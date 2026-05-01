"""
AI Job Agent - Main Orchestrator
Runs the full pipeline: scrape → read resume → rewrite → save → email → log to Excel.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


from config import (
    JOB_SEARCH_QUERIES,
    JOB_SITES,
    JOB_HOURS_OLD,
    RESUME_PDF_PATH,
    OUTPUT_DIR,
    OPENAI_API_KEY,
)
from scraper import scrape_jobs_all_sources, _format_salary
from resume_reader import read_resume_pdf
from ai_rewriter import rewrite_resume_for_job
from docx_writer import save_resume_as_docx
from emailer import send_digest_email
from excel_tracker import append_jobs_to_tracker

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("agent.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def validate_config() -> bool:
    """Check that all required config is present before running."""
    errors = []

    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is not set in .env")

    if not Path(RESUME_PDF_PATH).exists():
        errors.append(
            f"Resume PDF not found: '{RESUME_PDF_PATH}'. "
            f"Set RESUME_PDF_PATH in .env to point to your resume."
        )

    if errors:
        for err in errors:
            logger.error(f"  ✗ {err}")
        return False

    return True


def run_pipeline() -> None:
    """
    Execute the full AI Job Agent pipeline:
      1. Validate config
      2. Read resume from PDF
      3. Scrape fresh LinkedIn jobs
      4. For each job: rewrite resume with AI
      5. Save each tailored resume as .docx
      6. Send daily digest email
    """
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("🤖 AI Job Agent — Starting pipeline")
    logger.info(f"   Queries:  {', '.join(JOB_SEARCH_QUERIES)}")
    logger.info(f"   Sites:    {', '.join(JOB_SITES)}")
    logger.info(f"   Scope:    Worldwide Remote  |  Last {JOB_HOURS_OLD}h")
    logger.info("=" * 60)

    # ── Step 1: Validate ──────────────────────────────────────
    logger.info("\n[1/5] Validating configuration...")
    if not validate_config():
        logger.error("Aborting: fix the errors above and retry.")
        sys.exit(1)
    logger.info("  ✓ Configuration OK")

    # ── Step 2: Read resume ───────────────────────────────────
    logger.info("\n[2/5] Reading resume...")
    try:
        resume_text = read_resume_pdf(RESUME_PDF_PATH)
        logger.info(f"  ✓ Resume loaded ({len(resume_text)} characters)")
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"  ✗ {e}")
        sys.exit(1)

    # ── Step 3: Scrape jobs ───────────────────────────────────
    logger.info(f"\n[3/6] Scraping {', '.join(JOB_SITES)} for fresh remote Python jobs...")
    jobs = scrape_jobs_all_sources()

    if not jobs:
        logger.warning(
            "  ⚠ No jobs found. Try broadening your search query or increasing JOB_HOURS_OLD."
        )
        logger.info("Pipeline completed — nothing to do.")
        return

    logger.info(f"  ✓ Found {len(jobs)} job(s)")

    # ── Step 4 & 5: Rewrite + Save ────────────────────────────
    logger.info(f"\n[4-5/6] Rewriting resumes and saving as DOCX...")
    results = []

    for i, job in enumerate(jobs, start=1):
        source_tag = f"[{job.get('source', '?').upper()}]"
        logger.info(f"\n  Job {i}/{len(jobs)} {source_tag}: {job['title']} @ {job['company']}")

        try:
            # Rewrite with AI
            tailored_resume = rewrite_resume_for_job(resume_text, job)

            # Save as DOCX
            docx_path = save_resume_as_docx(tailored_resume, job, OUTPUT_DIR)

            results.append({
                "job":          job,
                "resume_path":  docx_path,
                "job_type":     job.get("job_type", "Full-time"),
                "salary_range": _format_salary(job),
                "source":       job.get("source", ""),
            })

        except Exception as e:
            logger.error(f"  ✗ Failed for {job['title']} @ {job['company']}: {e}")
            # Continue with remaining jobs even if one fails
            continue

    if not results:
        logger.error("All jobs failed processing. Check your OpenAI API key.")
        sys.exit(1)

    # ── Step 6: Email ─────────────────────────────────────────
    logger.info(f"\n[5/6] Sending digest email...")
    email_sent = send_digest_email(results, attach_resumes=True)

    if not email_sent:
        logger.warning(
            "  ⚠ Email not sent (check email config). "
            f"Your tailored resumes are still saved in: {Path(OUTPUT_DIR).resolve()}"
        )

    # ── Step 7: Excel tracker ─────────────────────────────────
    logger.info(f"\n[6/6] Updating Excel job tracker...")
    try:
        rows_added = append_jobs_to_tracker(results)
        logger.info(f"  ✓ Tracker updated: {rows_added} rows added to job_tracker.xlsx")
    except Exception as e:
        logger.error(f"  ✗ Failed to update tracker: {e}")

    # ── Summary ───────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).seconds
    logger.info("\n" + "=" * 60)
    logger.info(f"✅ Pipeline complete in {elapsed}s")
    logger.info(f"   Jobs processed: {len(results)}/{len(jobs)}")
    logger.info(f"   Resumes saved:  {Path(OUTPUT_DIR).resolve()}")
    logger.info(f"   Excel tracker:  job_tracker.xlsx")
    logger.info(f"   Email sent:     {'Yes' if email_sent else 'No (check config)'}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_pipeline()
