import os
import urllib.request
import urllib.parse
import html as html_lib
import re
from typing import List, Dict
from tavily import TavilyClient
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

def ddg_fallback_search(query: str) -> List[Dict[str, str]]:
    """
    DuckDuckGo fallback search scraper. Used if Tavily API key is missing.
    Queries the DDG HTML search page and parses the top 3 results.
    """
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    )
    
    try:
        # Use urllib to fetch DDG HTML search results
        with urllib.request.urlopen(req, timeout=10) as response:
            html_content = response.read().decode('utf-8')
            
        results = []
        # Result items are split by 'class="result '
        result_blocks = html_content.split('class="result ')
        
        # Iterate over the first few blocks (skipping the first split element)
        for block in result_blocks[1:]:
            if len(results) >= 3:
                break
                
            # Extract URL
            url_match = re.search(r'href="([^"]+)"', block)
            # Extract Title
            title_match = re.search(r'class="result__title"[^>]*>\s*<a[^>]*>([^<]+)</a>', block, re.DOTALL)
            # Extract Snippet
            snippet_match = re.search(r'class="result__snippet"[^>]*>([^<]+)</a>', block, re.DOTALL)
            
            if url_match and title_match:
                raw_url = url_match.group(1)
                
                # Unquote URL (DuckDuckGo wraps links through a local redirect endpoint)
                url = raw_url
                if "/l/?" in raw_url:
                    parsed_query = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
                    if "uddg" in parsed_query:
                        url = parsed_query["uddg"][0]
                
                # Clean up formatting and HTML character entity references
                title = html_lib.unescape(title_match.group(1).strip())
                # Clean up inner tag remnants
                title = re.sub(r'<[^>]+>', '', title)
                
                snippet = ""
                if snippet_match:
                    snippet = html_lib.unescape(snippet_match.group(1).strip())
                    snippet = re.sub(r'<[^>]+>', '', snippet)
                
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet
                })
                
        if results:
            return results
            
    except Exception as e:
        print(f"[Warning] DuckDuckGo fallback search failed: {e}")
        
    # Return Mock fallback results so the multi-agent system doesn't crash if offline/blocked
    return [
        {
            "title": f"Mock Search Result for: {query}",
            "url": "https://example.com/mock-search",
            "snippet": f"This is a fallback mock search result for the query '{query}' because both Tavily and DuckDuckGo search failed."
        }
    ]

def web_search(query: str) -> List[Dict[str, str]]:
    """
    Search the web using Tavily API if TAVILY_API_KEY is configured.
    Otherwise, automatically falls back to DuckDuckGo HTML search.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    
    # Check if Tavily key is valid (not empty and not the placeholder)
    use_tavily = api_key and api_key.strip() and "your_tavily" not in api_key
    
    if use_tavily:
        try:
            client = TavilyClient(api_key=api_key)
            response = client.search(query=query, max_results=3)
            results = response.get("results", [])
            
            formatted_results = []
            for r in results:
                formatted_results.append({
                    "title": r.get("title", "No Title"),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "")
                })
            return formatted_results
        except Exception as e:
            print(f"[Warning] Tavily search failed: {e}. Falling back to DuckDuckGo.")
            
    # Fallback to DuckDuckGo search
    return ddg_fallback_search(query)
