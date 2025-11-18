"""
LLMObserve CLI - Command-line tools for instrumentation and debugging.
"""
import sys
import argparse
import logging
from pathlib import Path


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LLMObserve CLI - Auto-instrument code for cost tracking"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # 'instrument' command
    instrument_parser = subparsers.add_parser(
        'instrument',
        help='Auto-instrument Python files with AI'
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
    
    # 'preview' command
    preview_parser = subparsers.add_parser(
        'preview',
        help='Preview AI-suggested instrumentation without applying'
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
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Execute command
    if args.command == 'instrument':
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
            print(f"\n❌ Error: {e}", file=sys.stderr)
            if hasattr(args, 'verbose') and args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    elif args.command == 'preview':
        from llmobserve.ai_instrument import preview_instrumentation
        
        try:
            preview_instrumentation(
                args.file, 
                collector_url=args.collector_url,
                api_key=args.api_key
            )
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}", file=sys.stderr)
            if hasattr(args, 'verbose') and args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

