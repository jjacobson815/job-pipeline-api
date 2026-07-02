import logging
import re
import urllib.parse
import httpx
import json
from app.core.config import get_settings
from app.domains.llm_analysis.services import LLMAnalysisService

logger = logging.getLogger(__name__)

class JobSearchService:
    """Service to automatically discover relevant job posting URLs based on a candidate's resume."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def discover_jobs(self, resume_text: str) -> dict:
        """Analyze resume, generate search queries, scrape results, and return matching job URLs."""
        # 1. Extract search queries using Gemini
        queries = await self._generate_search_queries(resume_text)
        logger.info("Generated job search queries from resume: %s", queries)

        # 2. Run search queries on DuckDuckGo and collect URLs
        all_urls = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for query in queries:
                try:
                    urls = await self._search_duckduckgo(client, query)
                    all_urls.extend(urls)
                except Exception as e:
                    logger.exception("Failed to search DuckDuckGo for query '%s': %s", query, e)

        # Deduplicate URLs
        unique_urls = list(dict.fromkeys(all_urls))
        logger.info("Discovered %d unique job URLs", len(unique_urls))

        return {
            "status": "success",
            "queries": queries,
            "urls": unique_urls[:15]  # Cap at 15 most relevant job postings
        }

    async def _generate_search_queries(self, resume_text: str) -> list[str]:
        """Ask LLM to recommend optimized search queries based on the resume."""
        fallback_queries = [
            '".NET Core" "React" remote developer',
            '"Senior Full Stack Engineer" C# remote'
        ]
        
        api_key = self.settings.gemini_api_key or self.settings.openai_api_key
        # Check if keys are placeholders or not provided
        if not api_key or "your-" in api_key or "sk-your" in api_key:
            logger.warning("No valid API key found. Falling back to default search queries.")
            return fallback_queries

        # Construct payload for the OpenAI compatibility layer
        use_gemini = self.settings.gemini_api_key is not None
        base_url = (
            "https://generativelanguage.googleapis.com/v1beta/openai/"
            if use_gemini
            else "https://api.openai.com/v1/"
        )
        model = "gemini-2.5-flash" if use_gemini else "gpt-4o-mini"
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert recruiter. Given the candidate's résumé text below, "
                        "extract 2 distinct, highly targeted search query phrases (e.g. '\".NET Core\" \"React\" remote developer' "
                        "or '\"Senior Full Stack Engineer\" C# remote') that would find the most relevant jobs matching their technical skills. "
                        "Respond ONLY with a JSON object containing a single key \"queries\" which is a list of strings. Do not include markdown wrappers."
                    )
                },
                {"role": "user", "content": resume_text}
            ],
            "response_format": {"type": "json_object"}
        }

        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error("LLM query generation failed: HTTP %d - %s", resp.status_code, resp.text)
                    return fallback_queries
                
                raw_text = resp.json()["choices"][0]["message"]["content"]
                # Clean JSON text from markdown wrappers if present
                clean_text = self._clean_json_text(raw_text)
                data = json.loads(clean_text)
                return data.get("queries", fallback_queries)
        except Exception as e:
            logger.exception("Failed to generate queries via LLM: %s", e)
            return fallback_queries

    def _clean_json_text(self, text: str) -> str:
        """Strip markdown json wrappers."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```json"):
                lines = lines[1:]
            else:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text

    async def _search_duckduckgo(self, client: httpx.AsyncClient, query: str) -> list[str]:
        """Search DuckDuckGo and parse result URLs."""
        search_q = f'{query} (site:dice.com/job-detail OR site:remoterocketship.com/company OR site:turing.com/jobs OR site:linkedin.com/jobs/view OR site:weworkremotely.com/remote-jobs OR site:simplyhired.com/job OR site:ziprecruiter.com/jobs)'
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(search_q)}"
        
        logger.info("Scraping DDG search: %s", url)
        resp = await client.get(url, headers=self._headers, follow_redirects=True)
        if resp.status_code != 200:
            logger.error("DuckDuckGo search failed: HTTP %d", resp.status_code)
            return []

        # Parse links using regex
        pattern = re.compile(r'href="([^"]+)"')
        raw_links = pattern.findall(resp.text)
        
        links = []
        for href in raw_links:
            href = urllib.parse.unquote(href.replace('&amp;', '&'))
            
            # DuckDuckGo redirects through /l/?kh=...&uddg=URL
            if 'uddg=' in href:
                parsed = urllib.parse.urlparse(href)
                query_params = urllib.parse.parse_qs(parsed.query)
                if 'uddg' in query_params:
                    actual_url = query_params['uddg'][0]
                    links.append(actual_url)
            elif href.startswith('//'):
                links.append('https:' + href)
            elif href.startswith('http'):
                links.append(href)
                
        # Filter for actual job postings and discard duckduckgo search internal pages
        filtered_links = []
        for l in links:
            if 'duckduckgo.com' in l:
                continue
            # Keep links matching job posting structures
            if any(domain in l.lower() for domain in [
                'dice.com/job-detail', 'remoterocketship.com', 'turing.com/jobs', 
                'linkedin.com/jobs', 'weworkremotely.com', 'simplyhired.com/job', 
                'ziprecruiter.com/jobs', 'reactjobs.io', 'glassdoor.com/job', 
                'workingnomads.com', 'flexjobs.com', 'arbeitnow.com'
            ]):
                filtered_links.append(l)

        return filtered_links
