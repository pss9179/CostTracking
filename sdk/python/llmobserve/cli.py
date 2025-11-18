"""
LLMObserve CLI - Command-line tools for instrumentation and debugging.
"""
import sys
import argparse
import logging
from pathlib import Path

logger = logging.getLogger("llmobserve")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LLMObserve CLI - Auto-instrument code for cost tracking",
        epilog="""
Examples:
  # Scan entire project
  llmobserve scan .
  
  # Review changes interactively
  llmobserve review
  
  # Show unified diff
  llmobserve diff
  
  # Apply all changes
  llmobserve apply
  
  # Rollback last changes
  llmobserve rollback
  
  # Legacy single-file mode
  llmobserve preview my_agent.py
  llmobserve instrument my_agent.py --auto-apply
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # NEW: 'scan' command - scan codebase
    scan_parser = subparsers.add_parser(
        'scan',
        help='Scan codebase for LLM-related code (does not modify files)'
    )
    scan_parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Directory to scan (default: current directory)'
    )
    scan_parser.add_argument(
        '--instruct',
        help='Custom instructions in plain English (e.g., "Don\'t touch utils/")'
    )
    scan_parser.add_argument(
        '--batch-size',
        type=int,
        default=3,
        help='Number of files to send to Claude at once (default: 3)'
    )
    scan_parser.add_argument(
        '--api-key',
        help='Your LLMObserve API key (or set LLMOBSERVE_API_KEY env var)'
    )
    scan_parser.add_argument(
        '--collector-url',
        help='LLMObserve collector URL (or set LLMOBSERVE_COLLECTOR_URL env var)'
    )
    scan_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # NEW: 'review' command - interactive review
    review_parser = subparsers.add_parser(
        'review',
        help='Interactively review and approve/reject suggested changes'
    )
    review_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # NEW: 'diff' command - show unified diff
    diff_parser = subparsers.add_parser(
        'diff',
        help='Show unified diff of all pending changes'
    )
    diff_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # NEW: 'apply' command - apply patches
    apply_parser = subparsers.add_parser(
        'apply',
        help='Apply all changes (creates backups and validates syntax)'
    )
    apply_parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip syntax validation (not recommended)'
    )
    apply_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # NEW: 'rollback' command - undo changes
    rollback_parser = subparsers.add_parser(
        'rollback',
        help='Rollback to previous version (restores from backup)'
    )
    rollback_parser.add_argument(
        '--timestamp',
        help='Specific backup timestamp to restore (default: latest)'
    )
    rollback_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # LEGACY: 'instrument' command (kept for backward compatibility)
    instrument_parser = subparsers.add_parser(
        'instrument',
        help='[LEGACY] Auto-instrument single file with AI'
    )
    instrument_parser.add_argument(
        'file',
        help='Python file to instrument'
    )
    instrument_parser.add_argument(
        '--auto-apply',
        action='store_true',
        help='Automatically apply suggested changes (creates .bak backup)'
    )
    instrument_parser.add_argument(
        '--api-key',
        help='Your LLMObserve API key (or set LLMOBSERVE_API_KEY env var)'
    )
    instrument_parser.add_argument(
        '--collector-url',
        help='LLMObserve collector URL (or set LLMOBSERVE_COLLECTOR_URL env var)'
    )
    instrument_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # LEGACY: 'preview' command
    preview_parser = subparsers.add_parser(
        'preview',
        help='[LEGACY] Preview AI-suggested instrumentation for single file'
    )
    preview_parser.add_argument(
        'file',
        help='Python file to analyze'
    )
    preview_parser.add_argument(
        '--api-key',
        help='Your LLMObserve API key (or set LLMOBSERVE_API_KEY env var)'
    )
    preview_parser.add_argument(
        '--collector-url',
        help='LLMObserve collector URL (or set LLMOBSERVE_COLLECTOR_URL env var)'
    )
    preview_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # Parse args
    args = parser.parse_args()
    
    # Set up logging
    if args.command and hasattr(args, 'verbose') and args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format='[%(levelname)s] %(message)s'
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s'
        )
    
    # Execute command
    if args.command == 'scan':
        _cmd_scan(args)
    
    elif args.command == 'review':
        _cmd_review(args)
    
    elif args.command == 'diff':
        _cmd_diff(args)
    
    elif args.command == 'apply':
        _cmd_apply(args)
    
    elif args.command == 'rollback':
        _cmd_rollback(args)
    
    elif args.command == 'instrument':
        _cmd_instrument_legacy(args)
    
    elif args.command == 'preview':
        _cmd_preview_legacy(args)
    
    else:
        parser.print_help()
        sys.exit(1)


def _cmd_scan(args):
    """Execute scan command."""
    from llmobserve.scanner import CodeScanner
    from llmobserve.refiner import CodeRefiner
    
    try:
        print(f"🔍 Scanning {args.path} for LLM-related code...")
        print()
        
        # Run scanner
        scanner = CodeScanner(args.path)
        candidates = scanner.scan()
        
        if not candidates:
            print("✅ No LLM-related code found.")
            sys.exit(0)
        
        print(f"📊 Found {len(candidates)} files with LLM code:")
        for i, candidate in enumerate(candidates, 1):
            print(f"  {i}. {candidate.file_path} (confidence: {candidate.confidence:.0%})")
            if args.verbose:
                print(f"     Reasons: {', '.join(candidate.reasons[:2])}")
        
        print()
        print(f"💾 Saved candidates to .llmobserve/candidates.json")
        print()
        
        # Ask to continue with refinement
        response = input("📤 Send to Claude for refinement? [y/N]: ")
        if response.lower() != 'y':
            print("Scan complete. Run 'llmobserve review' when ready.")
            sys.exit(0)
        
        # Run refiner
        print()
        print("🤖 Sending to Claude API for analysis...")
        
        refiner = CodeRefiner(
            api_endpoint=args.collector_url,
            api_key=args.api_key,
            custom_instructions=args.instruct
        )
        
        # Convert candidates to dicts
        candidate_dicts = [
            {
                "file_path": c.file_path,
                "language": c.language,
                "confidence": c.confidence,
                "reasons": c.reasons,
                "llm_calls": c.llm_calls,
                "agent_patterns": c.agent_patterns
            }
            for c in candidates
        ]
        
        results = refiner.refine_batch(candidate_dicts, batch_size=args.batch_size)
        
        total_suggestions = sum(len(r.suggestions) for r in results)
        
        print()
        print(f"✅ Analysis complete!")
        print(f"   {len(results)} files analyzed")
        print(f"   {total_suggestions} suggestions generated")
        print()
        print("📝 Next steps:")
        print("   llmobserve review   - Review changes interactively")
        print("   llmobserve diff     - Show unified diff")
        print("   llmobserve apply    - Apply all changes")
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _cmd_review(args):
    """Execute review command (interactive)."""
    from llmobserve.refiner import CodeRefiner
    from llmobserve.patcher import SafePatcher
    
    try:
        # Load scan results
        results = CodeRefiner.load_results()
        
        if not results:
            print("❌ No scan results found. Run 'llmobserve scan' first.")
            sys.exit(1)
        
        print("📋 Reviewing suggested changes...")
        print()
        
        approved = []
        rejected = []
        
        for i, result in enumerate(results, 1):
            if not result.suggestions:
                continue
            
            print(f"[{i}/{len(results)}] {result.file_path}")
            print(f"   Claude says: {result.claude_reasoning[:100]}...")
            print()
            
            for j, suggestion in enumerate(result.suggestions, 1):
                print(f"   Suggestion {j}: {suggestion.patch_type}")
                print(f"   Label: {suggestion.label}")
                print(f"   Line {suggestion.line_number}: {suggestion.reason}")
                print()
                print(f"   - {suggestion.code_before}")
                print(f"   + {suggestion.code_after}")
                print()
                
                response = input("   Apply this? [y/n/view/skip/quit]: ").lower()
                
                if response == 'y':
                    approved.append((result.file_path, j))
                    print("   ✅ Approved")
                elif response == 'n':
                    rejected.append((result.file_path, j))
                    print("   ❌ Rejected")
                elif response == 'view':
                    print(f"\n   Full context:\n{result.unified_patch}\n")
                    response = input("   Apply? [y/n]: ").lower()
                    if response == 'y':
                        approved.append((result.file_path, j))
                elif response == 'quit':
                    break
                else:
                    print("   ⏭️  Skipped")
                
                print()
        
        print(f"📊 Review complete:")
        print(f"   ✅ Approved: {len(approved)}")
        print(f"   ❌ Rejected: {len(rejected)}")
        print()
        
        if approved:
            print("Run 'llmobserve apply' to apply approved changes.")
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Review failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _cmd_diff(args):
    """Execute diff command."""
    from llmobserve.patcher import SafePatcher
    
    try:
        patcher = SafePatcher('.')
        diff = patcher.show_diff()
        
        if not diff:
            print("No pending changes to show.")
            sys.exit(0)
        
        print(diff)
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Diff failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _cmd_apply(args):
    """Execute apply command."""
    from llmobserve.patcher import SafePatcher
    
    try:
        patcher = SafePatcher('.')
        
        # Show diff first
        print("📝 Changes to be applied:")
        print()
        diff = patcher.show_diff()
        print(diff)
        print()
        
        # Confirm
        response = input("Apply all changes? [y/N]: ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
        
        # Apply
        print()
        print("🔧 Applying patches...")
        results = patcher.apply_patches(skip_validation=args.skip_validation)
        
        print()
        if results["success"]:
            print(f"✅ Successfully applied {len(results['applied'])} patches")
            print(f"   Backups saved to .llmobserve/backups/")
        else:
            print(f"⚠️  Applied {len(results['applied'])} patches with {len(results['failed'])} failures")
            for failure in results["failed"]:
                print(f"   ❌ {failure['file']}: {failure['reason']}")
        
        print()
        print("💡 To undo: llmobserve rollback")
        
        sys.exit(0 if results["success"] else 1)
        
    except Exception as e:
        logger.error(f"Apply failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _cmd_rollback(args):
    """Execute rollback command."""
    from llmobserve.patcher import SafePatcher
    
    try:
        patcher = SafePatcher('.')
        
        print("⏪ Rolling back changes...")
        success = patcher.rollback(backup_timestamp=args.timestamp)
        
        if success:
            print("✅ Rollback complete")
            sys.exit(0)
        else:
            print("❌ Rollback failed")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _cmd_instrument_legacy(args):
    """Execute legacy instrument command."""
    from llmobserve.ai_instrument import auto_instrument
    
    try:
        result = auto_instrument(
            args.file,
            auto_apply=args.auto_apply,
            collector_url=args.collector_url,
            api_key=args.api_key
        )
        
        if result['suggestions']:
            print(f"\n📊 Suggestions:")
            for i, suggestion in enumerate(result['suggestions'], 1):
                print(f"  {i}. {suggestion.get('type')} at line {suggestion.get('line_number')}")
                print(f"     → {suggestion.get('suggested_label')}")
        
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _cmd_preview_legacy(args):
    """Execute legacy preview command."""
    from llmobserve.ai_instrument import preview_instrumentation
    
    try:
        preview_instrumentation(
            args.file, 
            collector_url=args.collector_url,
            api_key=args.api_key
        )
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
