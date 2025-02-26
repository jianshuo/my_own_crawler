class LinkAnalyzer:
    def __init__(self, link_structure):
        self.link_structure = link_structure
    
    def analyze_page_rank(self):
        """Calculate a simplified PageRank for each page."""
        total_pages = len(self.link_structure)
        scores = {url: 1.0 / total_pages for url in self.link_structure}
        
        # Perform iterations (simplified PageRank)
        damping_factor = 0.85
        iterations = 10
        
        for _ in range(iterations):
            new_scores = {url: (1.0 - damping_factor) / total_pages for url in self.link_structure}
            
            for source_url, links in self.link_structure.items():
                unique_links = set(links)
                if not unique_links:
                    continue
                
                outbound_weight = scores[source_url] * damping_factor / len(unique_links)
                
                for target_url in unique_links:
                    if target_url in new_scores:
                        new_scores[target_url] += outbound_weight
                    else:
                        new_scores[target_url] = outbound_weight
            
            scores = new_scores
        
        return scores
    
    def find_orphaned_pages(self):
        """Find pages that aren't linked to by any other page."""
        incoming_links = {url: 0 for url in self.link_structure}
        
        # Count incoming links
        for _, links in self.link_structure.items():
            for link in links:
                if link in incoming_links:
                    incoming_links[link] += 1
        
        # Return pages with no incoming links
        return [url for url, count in incoming_links.items() if count == 0]
    
    def find_hubs(self):
        """Find pages with many outgoing links (hub pages)."""
        if not self.link_structure:
            return []
            
        outgoing_counts = [len(links) for links in self.link_structure.values()]
        avg_outgoing_links = sum(outgoing_counts) / len(self.link_structure)
        threshold = max(avg_outgoing_links * 2, 10)
        
        return [url for url, links in self.link_structure.items() if len(links) > threshold]
    
    def find_authorities(self):
        """Find pages with many incoming links (authority pages)."""
        incoming_links = {url: 0 for url in self.link_structure}
        
        # Count incoming links
        for _, links in self.link_structure.items():
            for link in links:
                if link in incoming_links:
                    incoming_links[link] += 1
        
        if not incoming_links:
            return []
            
        avg_incoming_links = sum(incoming_links.values()) / len(incoming_links)
        threshold = max(avg_incoming_links * 2, 5)
        
        return [url for url, count in incoming_links.items() if count > threshold]
    
    def print_analysis(self):
        """Print a detailed analysis of the link structure."""
        print("\n📊 LINK STRUCTURE ANALYSIS")
        print("==========================")
        
        # Basic statistics
        print("\n📌 Basic Statistics:")
        print(f"Total pages: {len(self.link_structure)}")
        
        total_links = sum(len(links) for links in self.link_structure.values())
        print(f"Total links: {total_links}")
        print(f"Average links per page: {total_links / len(self.link_structure) if self.link_structure else 0}")
        
        # Orphaned pages
        orphaned_pages = self.find_orphaned_pages()
        print(f"\n📌 Orphaned Pages ({len(orphaned_pages)}):")
        for page in orphaned_pages[:5]:
            print(f"- {page}")
        if len(orphaned_pages) > 5:
            print(f"... and {len(orphaned_pages) - 5} more")
        
        # Hub pages
        hub_pages = self.find_hubs()
        print(f"\n📌 Hub Pages ({len(hub_pages)}):")
        for page in hub_pages[:5]:
            print(f"- {page} ({len(self.link_structure.get(page, []))} outgoing links)")
        if len(hub_pages) > 5:
            print(f"... and {len(hub_pages) - 5} more")
        
        # Authority pages
        authority_pages = self.find_authorities()
        print(f"\n📌 Authority Pages ({len(authority_pages)}):")
        for page in authority_pages[:5]:
            print(f"- {page}")
        if len(authority_pages) > 5:
            print(f"... and {len(authority_pages) - 5} more")
        
        # PageRank
        page_ranks = self.analyze_page_rank()
        top_pages = sorted(page_ranks.items(), key=lambda x: x[1], reverse=True)[:5]
        
        print("\n📌 Top Pages by PageRank:")
        for page, score in top_pages:
            print(f"- {page} (Score: {score:.4f})") 