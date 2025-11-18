"""
Safe patch application with unified diffs, backups, and syntax validation.

Never modifies files until user explicitly approves changes.
"""
import os
import shutil
import subprocess
import tempfile
import difflib
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger("llmobserve.patcher")


class SafePatcher:
    """Applies patches safely with validation and rollback."""
    
    def __init__(self, root_path: str, cache_dir: str = ".llmobserve"):
        self.root_path = Path(root_path).resolve()
        self.cache_dir = self.root_path / cache_dir
        self.backup_dir = self.cache_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.patches_dir = self.cache_dir / "patches"
        self.applied_patches: List[Dict] = []
    
    def generate_unified_diff(self, file_path: str, old_content: str, new_content: str) -> str:
        """
        Generate unified diff between old and new content.
        
        Args:
            file_path: Relative file path
            old_content: Original content
            new_content: Modified content
            
        Returns:
            Unified diff string
        """
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=''
        )
        
        return ''.join(diff)
    
    def show_diff(self, patches: List[str] = None) -> str:
        """
        Show unified diff for all patches or specific patches.
        
        Args:
            patches: List of patch files to show. If None, shows all.
            
        Returns:
            Combined unified diff string
        """
        if patches is None:
            patches = list(self.patches_dir.glob("*.patch"))
        else:
            patches = [self.patches_dir / p if not str(p).endswith('.patch') else self.patches_dir / f"{p}.patch" for p in patches]
        
        combined_diff = []
        
        for patch_file in patches:
            if patch_file.exists():
                with open(patch_file, 'r') as f:
                    combined_diff.append(f.read())
        
        return '\n'.join(combined_diff)
    
    def apply_patches(
        self,
        patches: List[str] = None,
        dry_run: bool = False,
        skip_validation: bool = False
    ) -> Dict:
        """
        Apply patches with backup and validation.
        
        Args:
            patches: List of patch files. If None, applies all.
            dry_run: If True, don't actually modify files
            skip_validation: Skip syntax validation
            
        Returns:
            Dict with results: {"success": bool, "applied": [...], "failed": [...]}
        """
        if patches is None:
            patch_files = list(self.patches_dir.glob("*.patch"))
        else:
            patch_files = [
                self.patches_dir / (p if p.endswith('.patch') else f"{p}.patch")
                for p in patches
            ]
        
        results = {
            "success": True,
            "applied": [],
            "failed": [],
            "backed_up": []
        }
        
        # Load patch metadata
        metadata_file = self.cache_dir / "scan.json"
        if not metadata_file.exists():
            raise RuntimeError("No scan results found. Run 'llmobserve scan' first.")
        
        with open(metadata_file, 'r') as f:
            scan_results = json.load(f)
        
        # Create backup timestamp
        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_subdir = self.backup_dir / backup_timestamp
        backup_subdir.mkdir(exist_ok=True)
        
        logger.info(f"[patcher] Applying {len(patch_files)} patches")
        
        for patch_file in patch_files:
            file_path = self._patch_file_to_source(patch_file)
            
            if not file_path:
                logger.warning(f"[patcher] Could not determine source file for {patch_file}")
                continue
            
            try:
                # Create backup
                if not dry_run:
                    self._backup_file(file_path, backup_subdir)
                    results["backed_up"].append(str(file_path))
                
                # Apply patch
                if self._apply_single_patch(file_path, patch_file, dry_run):
                    results["applied"].append(str(file_path))
                    
                    # Validate syntax
                    if not skip_validation and not dry_run:
                        if not self._validate_syntax(file_path):
                            # Restore backup
                            self._restore_backup(file_path, backup_subdir)
                            results["applied"].remove(str(file_path))
                            results["failed"].append({
                                "file": str(file_path),
                                "reason": "Syntax validation failed"
                            })
                            results["success"] = False
                            logger.error(f"[patcher] Syntax validation failed for {file_path}, restored backup")
                else:
                    results["failed"].append({
                        "file": str(file_path),
                        "reason": "Patch application failed"
                    })
                    results["success"] = False
                    
            except Exception as e:
                logger.error(f"[patcher] Failed to apply patch for {file_path}: {e}")
                results["failed"].append({
                    "file": str(file_path),
                    "reason": str(e)
                })
                results["success"] = False
        
        # Save apply record
        if not dry_run and results["applied"]:
            self._save_apply_record(backup_timestamp, results)
        
        return results
    
    def _apply_single_patch(self, file_path: Path, patch_file: Path, dry_run: bool) -> bool:
        """Apply a single patch file."""
        try:
            with open(patch_file, 'r') as f:
                patch_content = f.read()
            
            if not patch_content.strip():
                logger.info(f"[patcher] No changes for {file_path}")
                return True
            
            if dry_run:
                logger.info(f"[patcher] [DRY RUN] Would apply patch to {file_path}")
                return True
            
            # Use patch command
            result = subprocess.run(
                ['patch', '-p1', str(file_path)],
                input=patch_content,
                capture_output=True,
                text=True,
                cwd=self.root_path
            )
            
            if result.returncode != 0:
                logger.error(f"[patcher] Patch command failed: {result.stderr}")
                return False
            
            logger.info(f"[patcher] Applied patch to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"[patcher] Error applying patch: {e}")
            return False
    
    def _backup_file(self, file_path: Path, backup_subdir: Path):
        """Create backup of file."""
        relative_path = file_path.relative_to(self.root_path)
        backup_path = backup_subdir / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(file_path, backup_path)
        logger.debug(f"[patcher] Backed up {file_path} to {backup_path}")
    
    def _restore_backup(self, file_path: Path, backup_subdir: Path):
        """Restore file from backup."""
        relative_path = file_path.relative_to(self.root_path)
        backup_path = backup_subdir / relative_path
        
        if backup_path.exists():
            shutil.copy2(backup_path, file_path)
            logger.info(f"[patcher] Restored {file_path} from backup")
    
    def _validate_syntax(self, file_path: Path) -> bool:
        """Validate file syntax after modification."""
        if file_path.suffix == ".py":
            return self._validate_python(file_path)
        elif file_path.suffix in [".js", ".jsx", ".ts", ".tsx"]:
            return self._validate_javascript(file_path)
        return True  # Skip validation for unknown types
    
    def _validate_python(self, file_path: Path) -> bool:
        """Validate Python syntax."""
        try:
            result = subprocess.run(
                ['python', '-m', 'py_compile', str(file_path)],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"[patcher] Python validation failed: {e}")
            return False
    
    def _validate_javascript(self, file_path: Path) -> bool:
        """Validate JS/TS syntax using node or tsc."""
        # Try tsc first for TypeScript
        if file_path.suffix in [".ts", ".tsx"]:
            try:
                result = subprocess.run(
                    ['tsc', '--noEmit', str(file_path)],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            except FileNotFoundError:
                logger.warning("[patcher] tsc not found, skipping TS validation")
        
        # Try node syntax check
        try:
            result = subprocess.run(
                ['node', '--check', str(file_path)],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            logger.warning("[patcher] node not found, skipping JS validation")
            return True  # Skip if no validator available
    
    def _patch_file_to_source(self, patch_file: Path) -> Optional[Path]:
        """Convert patch filename back to source file path."""
        # Patch files are named: path_to_file.py.patch
        filename = patch_file.stem  # Remove .patch
        source_path = filename.replace('_', '/')
        
        full_path = self.root_path / source_path
        if full_path.exists():
            return full_path
        
        return None
    
    def _save_apply_record(self, backup_timestamp: str, results: Dict):
        """Save record of applied patches."""
        record_file = self.cache_dir / "apply_history.json"
        
        records = []
        if record_file.exists():
            with open(record_file, 'r') as f:
                records = json.load(f)
        
        records.append({
            "timestamp": backup_timestamp,
            "backup_dir": str(self.backup_dir / backup_timestamp),
            "results": results
        })
        
        with open(record_file, 'w') as f:
            json.dump(records, f, indent=2)
    
    def rollback(self, backup_timestamp: str = None) -> bool:
        """
        Rollback to a previous backup.
        
        Args:
            backup_timestamp: Specific backup to restore. If None, uses latest.
            
        Returns:
            True if successful
        """
        # Load apply history
        record_file = self.cache_dir / "apply_history.json"
        if not record_file.exists():
            logger.error("[patcher] No apply history found")
            return False
        
        with open(record_file, 'r') as f:
            records = json.load(f)
        
        if not records:
            logger.error("[patcher] No backups found")
            return False
        
        # Get backup to restore
        if backup_timestamp:
            record = next((r for r in records if r["timestamp"] == backup_timestamp), None)
            if not record:
                logger.error(f"[patcher] Backup {backup_timestamp} not found")
                return False
        else:
            record = records[-1]  # Latest
        
        backup_subdir = Path(record["backup_dir"])
        if not backup_subdir.exists():
            logger.error(f"[patcher] Backup directory not found: {backup_subdir}")
            return False
        
        # Restore all files
        logger.info(f"[patcher] Rolling back to {record['timestamp']}")
        
        for file_path in record["results"]["applied"]:
            full_path = self.root_path / file_path
            self._restore_backup(full_path, backup_subdir)
        
        logger.info("[patcher] Rollback complete")
        return True

