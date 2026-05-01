"""
AI Job Agent - Multi-Site Job Scraper
Searches LinkedIn, Indeed, and ZipRecruiter per query with site-specific
parameters (per jobspy docs), deduplicates, filters, and returns the
freshest remote Python backend roles worldwide.

Per-site parameter strategy (per jobspy docs):
  LinkedIn     — is_remote=True + hours_old  (both supported)
  ZipRecruiter — is_remote=True + hours_old  (both supported)
  Indeed       — hours_old only + "remote" keyword in query
                 (is_remote conflicts with hours_old on Indeed)
                 country_indeed="usa" (www.indeed.com = global facing domain)

jobspy DataFrame columns captured:
  site, job_url, job_url_direct, title, company, company_url,
  location, date_posted, job_type, interval, min_amount, max_amount,
  currency, is_remote, job_level, job_function, company_industry,
  emails, description
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd
from jobspy import scrape_jobs

from config import (
    JOB_SEARCH_QUERIES,
    JOB_SITES,
    JOB_MAX_RESULTS_PER_QUERY,
    JOB_HOURS_OLD,
    JOB_EXCLUDE_KEYWORDS,
)

logger = logging.getLogger(__name__)

RAW_EXPORT_FILE = "raw_jobs_latest.csv"   # raw jobspy output saved each run


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe(value, fallback="") -> str:
    """Return a clean string from any DataFrame cell value."""
    if value is None or (isinstance(value, float) and str(value) == "nan"):
        return fallback
    return str(value).strip()


def _format_salary(job: Dict) -> str:
    """Build a human-readable salary string from jobspy fields."""
    lo       = job.get("salary_min")
    hi       = job.get("salary_max")
    cur      = job.get("salary_currency", "USD")
    interval = job.get("salary_interval", "")   # yearly / hourly / monthly

    interval_map = {
        "yearly":  "/yr",
        "monthly": "/mo",
        "weekly":  "/wk",
        "daily":   "/day",
        "hourly":  "/hr",
    }
    suffix = interval_map.get(str(interval).lower(), "")

    try:
        if lo and hi:
            return f"{cur} {int(float(lo)):,} – {int(float(hi)):,}{suffix}"
        elif lo:
            return f"{cur} {int(float(lo)):,}+{suffix}"
        elif hi:
            return f"Up to {cur} {int(float(hi)):,}{suffix}"
    except (ValueError, TypeError):
        pass
    return "Not listed"


def _ingest(df: pd.DataFrame, all_jobs: Dict, label: str):
    """Filter a DataFrame and add passing jobs into all_jobs (dedup by url)."""
    df = df[df["description"].notna() & (df["description"].str.strip() != "")]
    new_count = 0
    for _, row in df.iterrows():
        url = _safe(row.get("job_url"))
        if not url or url in all_jobs:
            continue
        job = _row_to_job(row)
        if _passes_filters(job):
            all_jobs[url] = job
            new_count += 1
    logger.info(f"      {new_count} new unique jobs added (raw: {len(df)})")


def _passes_filters(job: Dict) -> bool:
    """Return False if the job hits any deal-breaker keyword."""
    haystack = f"{job.get('title', '')} {job.get('description', '')}".lower()
    for kw in JOB_EXCLUDE_KEYWORDS:
        if kw.lower() in haystack:
            logger.debug(f"  ✗ Excluded '{job['title']}' — keyword: '{kw}'")
            return False
    return True


def _row_to_job(row: pd.Series) -> Dict:
    """Convert a jobspy DataFrame row into a clean job dict with all rich fields."""
    return {
        # Core
        "title":             _safe(row.get("title"),           "Unknown Role"),
        "company":           _safe(row.get("company"),         "Unknown Company"),
        "company_url":       _safe(row.get("company_url")),
        "job_url":           _safe(row.get("job_url")),
        "job_url_direct":    _safe(row.get("job_url_direct")),
        "location":          _safe(row.get("location"),        "Remote"),
        "description":       _safe(row.get("description")),
        "date_posted":       _safe(row.get("date_posted"),     datetime.today().strftime("%Y-%m-%d")),
        # Job attributes
        "job_type":          _safe(row.get("job_type"),        "Full-time"),
        "job_level":         _safe(row.get("job_level")),       # e.g. Mid-Senior, Entry
        "job_function":      _safe(row.get("job_function")),    # e.g. Engineering
        "is_remote":         bool(row.get("is_remote", True)),
        # Company
        "company_industry":  _safe(row.get("company_industry")),
        "company_employees": _safe(row.get("company_num_employees")),
        # Salary
        "salary_min":        row.get("min_amount"),
        "salary_max":        row.get("max_amount"),
        "salary_currency":   _safe(row.get("currency"),        "USD"),
        "salary_interval":   _safe(row.get("interval")),
        # Contact
        "recruiter_emails":  _safe(row.get("emails")),
        # Source
        "source":            _safe(row.get("site")),
    }


# ── Site groupings ────────────────────────────────────────────────────────────
# Sites that support is_remote + hours_old together
SITES_WITH_REMOTE_FLAG = {"linkedin", "zip_recruiter"}
# Sites where is_remote conflicts with hours_old — use keyword instead
SITES_KEYWORD_REMOTE   = {"indeed"}


def _scrape_site_group(
    sites: List[str],
    query: str,
    use_remote_flag: bool,
) -> Optional[pd.DataFrame]:
    """
    Single scrape_jobs() call for a group of sites with appropriate parameters.

    LinkedIn / ZipRecruiter: is_remote=True + hours_old
    Indeed: no is_remote flag, "remote" keyword already in query, country_indeed="usa"
    """
    kwargs = dict(
        site_name=sites,
        search_term=query,
        results_wanted=JOB_MAX_RESULTS_PER_QUERY * 3,
        hours_old=JOB_HOURS_OLD,
        linkedin_fetch_description=True,
        verbose=0,
    )

    if use_remote_flag:
        kwargs["is_remote"] = True
    else:
        # Indeed: use country_indeed="usa" (www.indeed.com = global-facing domain)
        kwargs["country_indeed"] = "usa"

    return scrape_jobs(**kwargs)


# ── Main scraper ──────────────────────────────────────────────────────────────

def scrape_jobs_all_sources() -> List[Dict]:
    """
    Run every configured query with per-site parameter handling:
      - LinkedIn + ZipRecruiter: is_remote=True + hours_old
      - Indeed: hours_old + "remote" keyword in query + country_indeed="usa"

    Results are deduplicated by job_url, filtered, and sorted newest-first.
    """
    all_jobs: Dict[str, Dict] = {}
    all_raw_frames: List[pd.DataFrame] = []

    # Split configured sites into two groups
    remote_flag_sites = [s for s in JOB_SITES if s in SITES_WITH_REMOTE_FLAG]
    keyword_sites     = [s for s in JOB_SITES if s in SITES_KEYWORD_REMOTE]

    total = len(JOB_SEARCH_QUERIES)
    for i, query in enumerate(JOB_SEARCH_QUERIES, start=1):
        logger.info(f"  [{i}/{total}] Query: '{query}' | Last {JOB_HOURS_OLD}h")

        # ── Group A: LinkedIn + ZipRecruiter ─────────────────
        if remote_flag_sites:
            logger.info(f"    → [{', '.join(remote_flag_sites)}] is_remote=True")
            try:
                df_a = _scrape_site_group(remote_flag_sites, query, use_remote_flag=True)
                if df_a is not None and not df_a.empty:
                    all_raw_frames.append(df_a)
                    _ingest(df_a, all_jobs, label=f"{remote_flag_sites}")
            except Exception as e:
                logger.warning(f"    ⚠ {remote_flag_sites} failed: {e}")

        # ── Group B: Indeed ───────────────────────────────────
        if keyword_sites:
            indeed_query = f"{query} remote"   # bake "remote" into keyword
            logger.info(f"    → [{', '.join(keyword_sites)}] query='{indeed_query}' country_indeed='usa'")
            try:
                df_b = _scrape_site_group(keyword_sites, indeed_query, use_remote_flag=False)
                if df_b is not None and not df_b.empty:
                    all_raw_frames.append(df_b)
                    _ingest(df_b, all_jobs, label=f"{keyword_sites}")
            except Exception as e:
                logger.warning(f"    ⚠ {keyword_sites} failed: {e}")

    # ── Export raw CSV ────────────────────────────────────────
    if all_raw_frames:
        try:
            raw_df = pd.concat(all_raw_frames, ignore_index=True).drop_duplicates(subset="job_url")
            raw_df.to_csv(RAW_EXPORT_FILE, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
            logger.info(f"  📄 Raw data saved: {RAW_EXPORT_FILE} ({len(raw_df)} rows)")
        except Exception as e:
            logger.warning(f"  ⚠ Could not save raw CSV: {e}")

    if not all_jobs:
        logger.warning(
            "No jobs found. Tips: increase JOB_HOURS_OLD to 48 or 72, "
            "or broaden JOB_SEARCH_QUERIES in .env"
        )
        return []

    results = sorted(all_jobs.values(), key=lambda j: j["date_posted"], reverse=True)
    logger.info(f"\n  ✓ Total unique filtered jobs: {len(results)}")
    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )
    jobs = scrape_jobs_all_sources()
    print(f"\n{'='*70}")
    print(f"  {len(jobs)} jobs found")
    print(f"{'='*70}")
    for j in jobs:
        print(f"\n  [{j['source'].upper()}] {j['title']} @ {j['company']}")
        print(f"  Level: {j['job_level'] or '—'}  |  Industry: {j['company_industry'] or '—'}")
        print(f"  📍 {j['location']}  |  📅 {j['date_posted']}  |  💰 {_format_salary(j)}")
        print(f"  🔗 {j['job_url']}")
