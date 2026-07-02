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
        
        # Fallback logic if search engine or Gemini is rate limited / blocked
        is_fallback = False
        fallback_source = None
        
        if not unique_urls:
            # Try to extract keywords from resume locally and query public open API
            resume_lower = resume_text.lower()
            common_tech = ["react", "python", "fastapi", "django", "c#", ".net", "javascript", "typescript", "kubernetes", "aws", "docker", "angular", "vue", "golang", "java", "c++", "rust"]
            matched_tech = [tech for tech in common_tech if tech in resume_lower]
            search_term = matched_tech[0] if matched_tech else "software engineer"
            
            logger.info("Search queries returned 0 results. Fetching live fallback jobs from Remotive API for '%s'...", search_term)
            try:
                remotive_urls = await self._discover_remotive_jobs(search_term)
                if remotive_urls:
                    unique_urls = remotive_urls
                    is_fallback = True
                    fallback_source = "Remotive API"
            except Exception as e:
                logger.warning("Remotive API lookup failed: %s", e)
                
        # Absolute last resort fallback using pre-vetted template postings
        if not unique_urls:
            is_fallback = True
            fallback_source = "Pre-vetted templates"
            logger.info("Injecting local template job postings as last-resort fallback.")
            unique_urls = [
                "https://www.turing.com/jobs/remote-dotnet-core-developer",
                "https://www.remoterocketship.com/company/hre-group-br/jobs/senior-full-stack-engineer-net-c-react-js-angular-worldwide-remote/",
                "https://www.dice.com/job-detail/37952023-50f8-44d5-b28e-0dc193d545f3",
                "https://www.workingnomads.com/jobs/senior-full-stack-netreact-developer-valorem-reply",
                "https://weworkremotely.com/remote-jobs/turing-senior-dotnet-developer"
            ]
            
        logger.info("Discovered %d unique job URLs", len(unique_urls))

        return {
            "status": "success",
            "queries": queries,
            "urls": unique_urls[:10],  # Cap at 10 to match backend ingest limits
            "fallback": is_fallback,
            "fallback_source": fallback_source
        }

    async def _generate_search_queries(self, resume_text: str) -> list[str]:
        """Ask LLM to recommend optimized search queries based on the resume."""
        fallback_queries = [
            '".NET Core" "React" remote developer',
            '"Senior Full Stack Engineer" C# remote'
        ]
        
        # Check if keys are placeholders or not provided using centralized configuration properties
        use_gemini = self.settings.is_gemini_configured
        use_openai = self.settings.is_openai_configured
        
        if not use_gemini and not use_openai:
            logger.warning("No valid API key found. Falling back to default search queries.")
            return fallback_queries

        api_key = self.settings.gemini_api_key if use_gemini else self.settings.openai_api_key
        # Construct payload for the OpenAI compatibility layer
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
        # Clean double quotes from query for site-restricted search to prevent strict syntax failures
        clean_q = query.replace('"', '')
        search_q = f'{clean_q} (site:dice.com/job-detail OR site:remoterocketship.com/company OR site:turing.com/jobs OR site:linkedin.com/jobs/view OR site:weworkremotely.com/remote-jobs OR site:simplyhired.com/job OR site:ziprecruiter.com/jobs)'
        
        links = await self._fetch_and_parse_ddg(client, search_q)
        
        # Fallback to a broader query if the restricted site search yields nothing
        if not links:
            logger.info("Restricted site search yielded 0 results. Retrying with broad query for '%s'", query)
            broad_q = f"{clean_q} remote developer jobs"
            links = await self._fetch_and_parse_ddg(client, broad_q)
            
        return links

    async def _fetch_and_parse_ddg(self, client: httpx.AsyncClient, search_q: str) -> list[str]:
        """Helper to fetch and parse links from a DuckDuckGo HTML query."""
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(search_q)}"
        
        try:
            resp = await client.get(url, headers=self._headers, follow_redirects=True)
            if resp.status_code != 200:
                logger.error("DuckDuckGo fetch failed: HTTP %d", resp.status_code)
                return []
        except Exception as e:
            logger.exception("DuckDuckGo HTTP call failed: %s", e)
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
                
        # Filter for actual job postings and discard generic search/list pages
        filtered_links = []
        for l in links:
            l_lower = l.lower()
            if 'duckduckgo.com' in l_lower:
                continue
                
            # Restrict to individual job details endpoints
            is_job_post = False
            
            # Dice individual job detail
            if 'dice.com/job-detail/' in l_lower:
                is_job_post = True
            # RemoteRocketShip individual job detail
            elif 'remoterocketship.com/company/' in l_lower and '/jobs/' in l_lower:
                is_job_post = True
            # Turing individual job detail
            elif 'turing.com/jobs/' in l_lower and not l_lower.endswith('/jobs/') and not 'search' in l_lower:
                is_job_post = True
            # LinkedIn individual job detail
            elif 'linkedin.com/jobs/view/' in l_lower:
                is_job_post = True
            # WeWorkRemotely individual job detail
            elif 'weworkremotely.com/remote-jobs/' in l_lower and '/jobs/' in l_lower:
                is_job_post = True
            # SimplyHired individual job detail (must have singular /job/ followed by id)
            elif 'simplyhired.com/job/' in l_lower:
                is_job_post = True
            # ZipRecruiter individual job detail (must have singular /job/)
            elif 'ziprecruiter.com/job/' in l_lower:
                is_job_post = True
            # Indeed individual job detail
            elif 'indeed.com/viewjob' in l_lower or 'indeed.com/rc/clk' in l_lower:
                is_job_post = True
            # WorkingNomads individual job detail
            elif 'workingnomads.com/jobs/' in l_lower and not l_lower.endswith('/jobs'):
                is_job_post = True
            # ArbeitNow individual job detail
            elif 'arbeitnow.com/jobs/' in l_lower and not l_lower.endswith('/jobs'):
                is_job_post = True
                
            if is_job_post:
                filtered_links.append(l)

        return list(dict.fromkeys(filtered_links))

    async def _discover_remotive_jobs(self, search_term: str) -> list[str]:
        """Fetch remote job URLs from Remotive's public open API using a search term."""
        url = f"https://remotive.com/api/remote-jobs?search={urllib.parse.quote(search_term)}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=self._headers)
                if resp.status_code == 200:
                    data = resp.json()
                    jobs = data.get("jobs", [])
                    
                    # Store job details in Redis cache
                    try:
                        import redis.asyncio as aioredis
                        from app.domains.job_ingestion.services import _html_to_text
                        r = aioredis.Redis.from_url(self.settings.redis_url_str)
                        for job in jobs:
                            job_url = job.get("url")
                            if job_url:
                                desc_html = job.get("description", "")
                                desc_text = _html_to_text(desc_html)
                                cache_val = {
                                    "title": job.get("title", "Untitled Position"),
                                    "company": job.get("company_name", "Unknown"),
                                    "description": desc_text[:10000] if desc_text else ""
                                }
                                await r.setex(f"job_cache:{job_url}", 3600, json.dumps(cache_val))
                        await r.aclose()
                    except Exception as redis_err:
                        logger.warning("Failed to cache jobs in Redis: %s", redis_err)
                        
                    return [job["url"] for job in jobs if "url" in job]
        except Exception as e:
            logger.warning("Failed to query Remotive API: %s", e)
        return []


