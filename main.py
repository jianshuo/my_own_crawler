#!/usr/bin/env python3
import sys
import argparse
from WebCrawler import WebCrawler
from LinkAnalyzer import LinkAnalyzer


def main():
    parser = argparse.ArgumentParser(
        description="Web crawler to analyze link structure"
    )
    parser.add_argument("url", help="URL to start crawling from")
    parser.add_argument(
        "--max-depth", type=int, default=3, help="Maximum crawling depth (default: 3)"
    )
    parser.add_argument(
        "--restrict-domain",
        type=bool,
        default=True,
        help="Restrict crawling to the same domain (default: True)",
    )
    parser.add_argument(
        "--save-path",
        type=str,
        default=None,
        help="Directory to save crawled pages (default: None)",
    )
    parser.add_argument(
        "--threads", type=int, default=10, help="Number of worker threads (default: 10)"
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=0.1,
        help="Time delay between requests to same domain in seconds (default: 0.1)",
    )

    args = parser.parse_args()

    print("Starting crawler with:")
    print(f"URL: {args.url}")
    print(f"Max Depth: {args.max_depth}")
    print(f"Restrict to Domain: {args.restrict_domain}")
    print(f"Threads: {args.threads}")
    print(f"Rate Limit: {args.rate_limit} seconds")
    if args.save_path:
        print(f"Saving pages to: {args.save_path}")

    try:
        crawler = WebCrawler(
            args.url,
            args.max_depth,
            args.restrict_domain,
            args.save_path,
            args.threads,
            args.rate_limit,
        )
        link_structure = crawler.crawl()

        # Print basic link structure
        crawler.print_link_structure()

        # Add detailed analysis
        analyzer = LinkAnalyzer(link_structure)
        analyzer.print_analysis()

    except Exception as e:
        print(f"Crawling failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
