"""
Static code scanner for detecting LLM-related code.

Scans Python/JS/TS files, builds dependency graphs, and identifies candidates
for instrumentation without making any modifications.
"""
import os
import re
import ast
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger("llmobserve.scanner")


@dataclass
class FileCandidate:
    """Represents a file that potentially contains LLM code."""
    file_path: str
    language: str  # "python", "javascript", "typescript"
    confidence: float  # 0.0 to 1.0
    reasons: List[str]  # Why this file was flagged
    imports: List[str]  # Imported modules
    dependencies: List[str]  # Files that import this file
    content_hash: str  # SHA256 for caching
    llm_calls: List[Dict]  # Detected LLM API calls
    agent_patterns: List[Dict]  # Detected agent-like patterns
    line_count: int


class CodeScanner:
    """Scans codebase for LLM-related code."""
    
    # Known LLM-related imports
    LLM_IMPORTS = {
        "openai", "anthropic", "google.generativeai", "cohere",
        "langchain", "crewai", "autogen", "llama_index",
        "llmobserve", "guidance", "semantic_kernel"
    }
    
    # Agent-like function name patterns
    AGENT_PATTERNS = [
        r".*agent.*", r".*orchestrat.*", r".*workflow.*",
        r".*pipeline.*", r".*task.*", r".*run.*", r".*invoke.*",
        r".*execute.*", r".*process.*"
    ]
    
    # LLM API call patterns
    LLM_API_PATTERNS = [
        r"\.chat\.completions\.create",
        r"\.messages\.create",
        r"\.generate",
        r"\.invoke",
        r"\.run",
        r"ChatCompletion\.create",
        r"anthropic\.Anthropic",
        r"OpenAI\(",
        r"ChatOpenAI\(",
    ]
    
    def __init__(self, root_path: str, cache_dir: str = ".llmobserve"):
        self.root_path = Path(root_path).resolve()
        self.cache_dir = self.root_path / cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        
        self.candidates: List[FileCandidate] = []
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.file_hashes: Dict[str, str] = {}
        
    def scan(self) -> List[FileCandidate]:
        """
        Scan the codebase and return candidate files.
        
        Returns:
            List of FileCandidate objects
        """
        logger.info(f"[scanner] Scanning {self.root_path}")
        
        # Load cache if exists
        cache = self._load_cache()
        
        # Find all Python/JS/TS files
        files = self._find_code_files()
        logger.info(f"[scanner] Found {len(files)} code files")
        
        # Analyze each file
        for file_path in files:
            relative_path = str(file_path.relative_to(self.root_path))
            
            # Check cache
            file_hash = self._compute_hash(file_path)
            if relative_path in cache and cache[relative_path]["hash"] == file_hash:
                logger.debug(f"[scanner] Using cached analysis for {relative_path}")
                candidate = FileCandidate(**cache[relative_path]["candidate"])
                self.candidates.append(candidate)
                continue
            
            # Analyze file
            candidate = self._analyze_file(file_path)
            if candidate and candidate.confidence > 0.3:  # Minimum confidence threshold
                self.candidates.append(candidate)
        
        # Build dependency graph
        self._build_dependency_graph()
        
        # Update candidates with dependency info
        self._update_dependencies()
        
        # Save to cache and candidates.json
        self._save_candidates()
        
        logger.info(f"[scanner] Found {len(self.candidates)} candidates")
        return self.candidates
    
    def _find_code_files(self) -> List[Path]:
        """Find all Python/JS/TS files in the directory."""
        files = []
        
        # Directories to skip
        skip_dirs = {
            "node_modules", ".git", "__pycache__", ".venv", "venv",
            "env", "build", "dist", ".next", ".vercel", ".llmobserve"
        }
        
        for ext in [".py", ".js", ".ts", ".jsx", ".tsx"]:
            for file_path in self.root_path.rglob(f"*{ext}"):
                # Skip if in excluded directory
                if any(skip in file_path.parts for skip in skip_dirs):
                    continue
                files.append(file_path)
        
        return files
    
    def _analyze_file(self, file_path: Path) -> Optional[FileCandidate]:
        """Analyze a single file for LLM-related code."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            language = self._detect_language(file_path)
            relative_path = str(file_path.relative_to(self.root_path))
            
            if language == "python":
                return self._analyze_python(file_path, content, relative_path)
            elif language in ["javascript", "typescript"]:
                return self._analyze_javascript(file_path, content, relative_path)
            
            return None
            
        except Exception as e:
            logger.error(f"[scanner] Failed to analyze {file_path}: {e}")
            return None
    
    def _analyze_python(self, file_path: Path, content: str, relative_path: str) -> Optional[FileCandidate]:
        """Analyze Python file."""
        reasons = []
        imports = []
        llm_calls = []
        agent_patterns = []
        confidence = 0.0
        
        try:
            tree = ast.parse(content)
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                        if any(llm in alias.name for llm in self.LLM_IMPORTS):
                            reasons.append(f"Imports LLM library: {alias.name}")
                            confidence += 0.3
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                        if any(llm in node.module for llm in self.LLM_IMPORTS):
                            reasons.append(f"Imports from LLM library: {node.module}")
                            confidence += 0.3
                
                # Detect function definitions with agent-like names
                elif isinstance(node, ast.FunctionDef):
                    func_name = node.name.lower()
                    if any(re.match(pattern, func_name) for pattern in self.AGENT_PATTERNS):
                        agent_patterns.append({
                            "type": "function",
                            "name": node.name,
                            "line": node.lineno
                        })
                        reasons.append(f"Agent-like function: {node.name}")
                        confidence += 0.2
                
                # Detect class definitions
                elif isinstance(node, ast.ClassDef):
                    class_name = node.name.lower()
                    if any(re.match(pattern, class_name) for pattern in self.AGENT_PATTERNS):
                        agent_patterns.append({
                            "type": "class",
                            "name": node.name,
                            "line": node.lineno
                        })
                        reasons.append(f"Agent-like class: {node.name}")
                        confidence += 0.2
            
            # Detect LLM API calls in content
            for pattern in self.LLM_API_PATTERNS:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    llm_calls.append({
                        "pattern": pattern,
                        "line": line_num,
                        "snippet": content[max(0, match.start()-20):match.end()+20]
                    })
                    confidence += 0.4
                    reasons.append(f"LLM API call at line {line_num}")
            
            if confidence == 0.0:
                return None
            
            return FileCandidate(
                file_path=relative_path,
                language="python",
                confidence=min(confidence, 1.0),
                reasons=reasons,
                imports=imports,
                dependencies=[],
                content_hash=self._compute_hash(file_path),
                llm_calls=llm_calls,
                agent_patterns=agent_patterns,
                line_count=content.count('\n') + 1
            )
            
        except SyntaxError as e:
            logger.warning(f"[scanner] Syntax error in {relative_path}: {e}")
            return None
    
    def _analyze_javascript(self, file_path: Path, content: str, relative_path: str) -> Optional[FileCandidate]:
        """Analyze JavaScript/TypeScript file (basic regex-based)."""
        reasons = []
        imports = []
        llm_calls = []
        agent_patterns = []
        confidence = 0.0
        
        # Extract imports (basic regex)
        import_matches = re.finditer(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', content)
        for match in import_matches:
            module = match.group(1)
            imports.append(module)
            if any(llm in module for llm in self.LLM_IMPORTS):
                reasons.append(f"Imports LLM library: {module}")
                confidence += 0.3
        
        # Detect LLM API calls
        for pattern in self.LLM_API_PATTERNS:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                llm_calls.append({
                    "pattern": pattern,
                    "line": line_num
                })
                confidence += 0.4
                reasons.append(f"LLM API call at line {line_num}")
        
        # Detect agent-like function names
        func_matches = re.finditer(r'(?:function|const|let|var)\s+(\w+)\s*(?:=|\()', content)
        for match in matches:
            func_name = match.group(1).lower()
            if any(re.match(pattern, func_name) for pattern in self.AGENT_PATTERNS):
                line_num = content[:match.start()].count('\n') + 1
                agent_patterns.append({
                    "type": "function",
                    "name": match.group(1),
                    "line": line_num
                })
                reasons.append(f"Agent-like function: {match.group(1)}")
                confidence += 0.2
        
        if confidence == 0.0:
            return None
        
        return FileCandidate(
            file_path=relative_path,
            language="javascript" if file_path.suffix == ".js" else "typescript",
            confidence=min(confidence, 1.0),
            reasons=reasons,
            imports=imports,
            dependencies=[],
            content_hash=self._compute_hash(file_path),
            llm_calls=llm_calls,
            agent_patterns=agent_patterns,
            line_count=content.count('\n') + 1
        )
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        ext = file_path.suffix
        if ext == ".py":
            return "python"
        elif ext in [".js", ".jsx"]:
            return "javascript"
        elif ext in [".ts", ".tsx"]:
            return "typescript"
        return "unknown"
    
    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file content."""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def _build_dependency_graph(self):
        """Build import dependency graph."""
        # For Python, track which files import which modules
        for candidate in self.candidates:
            if candidate.language == "python":
                file_module = candidate.file_path.replace("/", ".").replace(".py", "")
                for other in self.candidates:
                    if other.file_path != candidate.file_path:
                        if file_module in other.imports:
                            if candidate.file_path not in self.dependency_graph:
                                self.dependency_graph[candidate.file_path] = set()
                            self.dependency_graph[candidate.file_path].add(other.file_path)
    
    def _update_dependencies(self):
        """Update candidates with dependency information."""
        for candidate in self.candidates:
            if candidate.file_path in self.dependency_graph:
                candidate.dependencies = list(self.dependency_graph[candidate.file_path])
    
    def _load_cache(self) -> Dict:
        """Load cached scan results."""
        cache_file = self.cache_dir / "cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"[scanner] Failed to load cache: {e}")
        return {}
    
    def _save_candidates(self):
        """Save candidates to disk."""
        candidates_file = self.cache_dir / "candidates.json"
        cache_file = self.cache_dir / "cache.json"
        
        # Save candidates
        with open(candidates_file, 'w') as f:
            json.dump([asdict(c) for c in self.candidates], f, indent=2)
        
        # Save cache
        cache = {}
        for candidate in self.candidates:
            cache[candidate.file_path] = {
                "hash": candidate.content_hash,
                "candidate": asdict(candidate)
            }
        with open(cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
        
        logger.info(f"[scanner] Saved {len(self.candidates)} candidates to {candidates_file}")

