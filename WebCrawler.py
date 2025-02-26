import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import time
import os
import hashlib
from collections import deque
import concurrent.futures
import threading


class WebCrawler:
    def __init__(
        self,
        seed_url,
        max_depth=5,
        restrict_to_domain=True,
        save_path=None,
        max_workers=10,
        rate_limit=0.1,
    ):
        self.visited_urls = set()
        self.link_structure = {}
        self.max_depth = max_depth
        self.restrict_to_domain = restrict_to_domain
        parsed_url = urlparse(seed_url)
        self.base_domain = parsed_url.netloc
        self.save_path = save_path
        self.url_to_filename_map = {}  # Maps URLs to their filenames
        self.max_workers = max_workers  # Number of worker threads
        self.rate_limit = rate_limit  # Time delay between requests to same domain

        # Locks for thread safety
        self.visited_lock = threading.Lock()
        self.structure_lock = threading.Lock()
        self.file_lock = threading.Lock()

        # Domain access timestamps to implement rate limiting
        self.domain_timestamps = {}
        self.domain_lock = threading.Lock()

        # Create save directory if specified
        if self.save_path and not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

    def normalize_url(self, url):
        """Normalize a URL by removing fragments and standardizing format."""
        try:
            # Parse the URL
            parsed = urlparse(url)

            # Remove the fragment
            normalized = urlunparse(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    "",  # Empty fragment
                )
            )

            # Ensure path ends with / if it's empty
            if parsed.path == "":
                normalized = normalized + "/"

            return normalized
        except Exception:
            return url

    def crawl(self):
        """Crawl the website starting from seed_url and return the link structure."""
        seed_url = (
            f"https://{self.base_domain}"
            if not urlparse(self.base_domain).scheme
            else self.base_domain
        )

        # Normalize the seed URL
        seed_url = self.normalize_url(seed_url)

        # Initialize the work queue with the seed URL
        queue = deque([(seed_url, 1)])

        # Track URLs currently being processed to avoid duplicates
        processing = set()
        processing_lock = threading.Lock()

        # Process URLs in batches until no more work
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            while queue:
                # Get a batch of URLs to process
                batch = []
                with processing_lock:
                    while queue and len(batch) < self.max_workers:
                        url, depth = queue.popleft()

                        # Skip if already visited or being processed
                        if url in self.visited_urls or url in processing:
                            continue

                        # Skip if depth exceeds max_depth
                        if depth > self.max_depth:
                            continue

                        # Mark as being processed
                        processing.add(url)
                        batch.append((url, depth))

                if not batch:
                    break

                # Submit batch to thread pool
                future_to_url = {
                    executor.submit(self.process_url, url, depth): (url, depth)
                    for url, depth in batch
                }

                # Process completed futures and collect new URLs
                new_urls = []
                for future in concurrent.futures.as_completed(future_to_url):
                    url, depth = future_to_url[future]
                    with processing_lock:
                        processing.remove(url)

                    try:
                        # Get the results (new URLs to crawl)
                        result_urls = future.result()
                        if result_urls:
                            # Add new URLs to process
                            for new_url in result_urls:
                                new_urls.append((new_url, depth + 1))
                    except Exception as e:
                        print(f"Error processing {url}: {e}")

                # Add new URLs to the queue
                with processing_lock:
                    queue.extend(new_urls)

        return self.link_structure

    def process_url(self, url, depth):
        """Process a single URL and return new URLs to crawl."""
        # Normalize the URL (remove fragments)
        url = self.normalize_url(url)

        # Check if URL is valid
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return []

            # Check if already visited (double-check with lock)
            with self.visited_lock:
                if url in self.visited_urls:
                    return []
                self.visited_urls.add(url)

            # Initialize entry in link structure
            with self.structure_lock:
                self.link_structure[url] = []

            print(f"Crawling: {url} (depth: {depth})")

            # Apply rate limiting for the domain
            domain = parsed.netloc
            self.apply_rate_limit(domain)

            # Check for cached content
            cached_content = None
            if self.save_path:
                filename = self.get_filename_for_url(url)
                filepath = os.path.join(self.save_path, filename)

                # Use file lock when checking/reading cache
                with self.file_lock:
                    if os.path.exists(filepath):
                        print(f"Using cached version for: {url}")
                        try:
                            with open(filepath, "r", encoding="utf-8") as f:
                                cached_content = f.read()
                        except Exception as e:
                            print(f"Error reading cache for {url}: {e}")
                            cached_content = None

            # Fetch or use cached content
            if cached_content:
                links = self.extract_links_from_content(url, cached_content)
            else:
                links, content = self.fetch_links_and_content(url)

                # Save content if needed
                if self.save_path and content:
                    self.save_page(url, content)

            # Update link structure
            with self.structure_lock:
                self.link_structure[url] = links

            # Return new URLs to crawl (make sure they're normalized too)
            new_urls = []
            for link in links:
                # Normalize the link
                link = self.normalize_url(link)

                with self.visited_lock:
                    if link in self.visited_urls:
                        continue

                link_domain = urlparse(link).netloc
                if not self.restrict_to_domain or link_domain == self.base_domain:
                    new_urls.append(link)

            return new_urls

        except Exception as e:
            print(f"Error processing {url}: {e}")
            return []

    def apply_rate_limit(self, domain):
        """Apply rate limiting for requests to the same domain."""
        with self.domain_lock:
            current_time = time.time()
            if domain in self.domain_timestamps:
                # Calculate how long to wait
                last_access = self.domain_timestamps[domain]
                elapsed = current_time - last_access
                if elapsed < self.rate_limit:
                    time.sleep(self.rate_limit - elapsed)

            # Update timestamp
            self.domain_timestamps[domain] = time.time()

    def extract_links_from_content(self, url, content):
        """Extract links from HTML content."""
        soup = BeautifulSoup(content, "html.parser")
        links = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]

            # Skip empty hrefs, javascript links, and anchors
            if not href or href.startswith("javascript:") or href.startswith("#"):
                continue

            try:
                # Try to join to create an absolute URL
                absolute_url = urljoin(url, href)

                # Normalize the URL (remove fragments)
                absolute_url = self.normalize_url(absolute_url)

                # Validate URL has a scheme (http/https)
                parsed = urlparse(absolute_url)
                if not parsed.scheme or not parsed.netloc:
                    continue

                links.append(absolute_url)
            except Exception:
                # If URL parsing fails, skip this URL
                continue

        return links

    def fetch_links_and_content(self, url):
        """Fetch links and content from a URL."""
        headers = {"User-Agent": "PythonWebCrawler/1.0"}

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Store the content
        content = response.text

        # Parse links
        links = self.extract_links_from_content(url, content)

        return links, content

    def get_filename_for_url(self, url):
        """Generate a consistent filename for a URL."""
        # Normalize URL first to remove fragments
        url = self.normalize_url(url)

        if url in self.url_to_filename_map:
            return self.url_to_filename_map[url]

        # Create a unique filename from the URL
        parsed_url = urlparse(url)

        # Remove scheme and www if present
        domain = parsed_url.netloc.replace("www.", "")

        # Hash the path for unique filenames
        path_hash = hashlib.md5(parsed_url.path.encode()).hexdigest()[:8]

        # Create a sensible filename
        if parsed_url.path and parsed_url.path != "/":
            path = parsed_url.path.rstrip("/")
            filename = f"{domain}{path.replace('/', '_')}"
            if len(filename) > 100:  # Limit filename length
                filename = f"{domain}_{path_hash}"
        else:
            filename = f"{domain}_index"

        # Ensure filename is valid and add extension
        filename = "".join(c if c.isalnum() or c in "_-." else "_" for c in filename)
        filename = f"{filename}.html"

        # Store in map for consistency
        with self.file_lock:
            self.url_to_filename_map[url] = filename

        return filename

    def save_page(self, url, content):
        """Save the page content to a file."""
        filename = self.get_filename_for_url(url)
        file_path = os.path.join(self.save_path, filename)

        with self.file_lock:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

    def print_link_structure(self):
        """Print the discovered link structure."""
        print("\nWebsite Link Structure:")
        print("=======================")

        for url, links in sorted(self.link_structure.items(), key=lambda x: x[0]):
            print(f"\n📄 {url}")
            print(f"  Outgoing links ({len(links)}):")

            for link in sorted(links):
                print(f"   → {link}")

        print("\nSummary:")
        print(f"Total pages crawled: {len(self.visited_urls)}")
