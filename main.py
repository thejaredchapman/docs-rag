"""CLI: python main.py "your question"."""
import argparse
import sys

import query


def main():
    parser = argparse.ArgumentParser(description="Ask a question about your docs.")
    parser.add_argument("question", help="The question to ask")
    parser.add_argument("--top-k", type=int, default=None, help="Override TOP_K")
    parser.add_argument("--no-cache", action="store_true", help="Skip the similarity cache")
    args = parser.parse_args()

    try:
        result = query.ask(args.question, top_k=args.top_k, use_cache=not args.no_cache)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(result["answer"])
    if result["sources"]:
        print("\nSources:")
        for source in result["sources"]:
            print(f"  - {source}")


if __name__ == "__main__":
    main()
