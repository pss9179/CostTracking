"""
Claude-based code refinement and patch generation.

Sends candidate files to Claude API in batches, gets labeling suggestions,
and generates safe patches.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger("llmobserve.refiner")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


@dataclass
class PatchSuggestion:
    """Represents a suggested patch for a file."""
    file_path: str
    label: str
    patch_type: str  # "decorator", "context_manager", "wrap_tools"
    line_number: int
    function_name: Optional[str]
    code_before: str
    code_after: str
    reason: str
    confidence: float


@dataclass
class RefinementResult:
    """Result from Claude refinement."""
    file_path: str
    suggestions: List[PatchSuggestion]
    unified_patch: str  # Unified diff format
    needs_review: bool
    claude_reasoning: str


class CodeRefiner:
    """Refines code using Claude API."""
    
    def __init__(
        self,
        api_endpoint: str = None,
        api_key: str = None,
        cache_dir: str = ".llmobserve",
        custom_instructions: str = None
    ):
        """
        Initialize refiner.
        
        Args:
            api_endpoint: LLMObserve backend endpoint (uses backend's Claude key)
            api_key: User's LLMObserve API key
            cache_dir: Cache directory
            custom_instructions: User's plain English instructions
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests package required. Install with: pip install requests")
        
        self.api_endpoint = api_endpoint or os.getenv("LLMOBSERVE_COLLECTOR_URL", "https://llmobserve.com")
        self.api_key = api_key or os.getenv("LLMOBSERVE_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "LLMObserve API key required. "
                "Set LLMOBSERVE_API_KEY env var or pass api_key parameter."
            )
        
        self.cache_dir = Path(cache_dir)
        self.custom_instructions = custom_instructions
        
        self.results: List[RefinementResult] = []
    
    def refine_batch(self, candidates: List[Dict], batch_size: int = 3) -> List[RefinementResult]:
        """
        Refine candidates in batches using Claude.
        
        Args:
            candidates: List of FileCandidate dicts
            batch_size: Number of files to send to Claude at once
            
        Returns:
            List of RefinementResult objects
        """
        logger.info(f"[refiner] Refining {len(candidates)} candidates in batches of {batch_size}")
        
        # Sort by confidence (highest first)
        sorted_candidates = sorted(candidates, key=lambda c: c.get("confidence", 0), reverse=True)
        
        # Process in batches
        for i in range(0, len(sorted_candidates), batch_size):
            batch = sorted_candidates[i:i+batch_size]
            logger.info(f"[refiner] Processing batch {i//batch_size + 1}/{(len(sorted_candidates) + batch_size - 1)//batch_size}")
            
            try:
                results = self._refine_batch_claude(batch)
                self.results.extend(results)
            except Exception as e:
                logger.error(f"[refiner] Batch failed: {e}")
                # Continue with next batch
        
        # Save results
        self._save_results()
        
        logger.info(f"[refiner] Completed refinement: {len(self.results)} files")
        return self.results
    
    def _refine_batch_claude(self, batch: List[Dict]) -> List[RefinementResult]:
        """Send a batch of files to Claude for refinement."""
        # Build prompt
        prompt = self._build_batch_prompt(batch)
        
        # Call backend API (which calls Claude)
        endpoint = f"{self.api_endpoint.rstrip('/')}/api/ai-instrument-batch"
        
        response = requests.post(
            endpoint,
            json={
                "files": batch,
                "custom_instructions": self.custom_instructions
            },
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=120  # 2 minute timeout for batch
        )
        
        if response.status_code == 401:
            raise ValueError("Invalid API key")
        
        if not response.ok:
            raise RuntimeError(f"API error: {response.status_code} - {response.text}")
        
        data = response.json()
        
        # Parse results
        results = []
        for file_result in data.get("results", []):
            suggestions = [
                PatchSuggestion(**s) for s in file_result.get("suggestions", [])
            ]
            
            result = RefinementResult(
                file_path=file_result["file_path"],
                suggestions=suggestions,
                unified_patch=file_result.get("unified_patch", ""),
                needs_review=file_result.get("needs_review", len(suggestions) > 0),
                claude_reasoning=file_result.get("reasoning", "")
            )
            results.append(result)
        
        return results
    
    def _build_batch_prompt(self, batch: List[Dict]) -> str:
        """Build Claude prompt for a batch of files."""
        custom_note = f"\n\n**User Instructions:**\n{self.custom_instructions}\n" if self.custom_instructions else ""
        
        files_desc = "\n\n".join([
            f"**File {i+1}: {c['file_path']}**\n"
            f"Language: {c['language']}\n"
            f"Confidence: {c['confidence']:.2f}\n"
            f"Reasons: {', '.join(c['reasons'])}\n"
            f"LLM calls detected: {len(c.get('llm_calls', []))}\n"
            f"Agent patterns: {len(c.get('agent_patterns', []))}\n"
            for i, c in enumerate(batch)
        ])
        
        return f"""You are analyzing a codebase to suggest LLMObserve instrumentation.

{custom_note}

Analyze these files and suggest minimal, safe patches:

{files_desc}

For each file, return:
1. suggested_label: meaningful agent/tool name
2. patch_type: "decorator", "context_manager", or "wrap_tools"
3. exact line numbers and code changes
4. confidence score (0.0-1.0)

Be conservative. Only suggest changes where you're highly confident.
Return JSON with strict structure.
"""
    
    def _save_results(self):
        """Save refinement results to disk."""
        scan_file = self.cache_dir / "scan.json"
        patches_dir = self.cache_dir / "patches"
        patches_dir.mkdir(exist_ok=True)
        
        # Save scan results
        with open(scan_file, 'w') as f:
            json.dump([asdict(r) for r in self.results], f, indent=2)
        
        # Save individual patches
        for result in self.results:
            if result.unified_patch:
                patch_file = patches_dir / f"{result.file_path.replace('/', '_')}.patch"
                with open(patch_file, 'w') as f:
                    f.write(result.unified_patch)
        
        logger.info(f"[refiner] Saved results to {scan_file}")
    
    @classmethod
    def load_results(cls, cache_dir: str = ".llmobserve") -> List[RefinementResult]:
        """Load refinement results from disk."""
        scan_file = Path(cache_dir) / "scan.json"
        if not scan_file.exists():
            return []
        
        with open(scan_file, 'r') as f:
            data = json.load(f)
        
        results = []
        for item in data:
            suggestions = [PatchSuggestion(**s) for s in item["suggestions"]]
            result = RefinementResult(
                file_path=item["file_path"],
                suggestions=suggestions,
                unified_patch=item["unified_patch"],
                needs_review=item["needs_review"],
                claude_reasoning=item["claude_reasoning"]
            )
            results.append(result)
        
        return results

