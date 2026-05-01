"""
AI Job Agent - Scheduler
Runs the pipeline automatically every day at your configured time.
Keep this script running in the background (e.g. in a terminal or as a service).
"""

import logging
import sys
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config import SCHEDULE_HOUR, SCHEDULE_MINUTE
from main import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    scheduler = BlockingScheduler(timezone="local")

    scheduler.add_job(
        func=run_pipeline,
        trigger=CronTrigger(hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE),
        id="ai_job_agent",
        name="AI Job Agent Daily Run",
        max_instances=1,
        misfire_grace_time=3600,  # Allow up to 1h late start (e.g. if PC was asleep)
    )

    logger.info("=" * 60)
    logger.info("🤖 AI Job Agent Scheduler — Running")
    logger.info(f"   Next run: every day at {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d}")
    logger.info("   Press Ctrl+C to stop.")
    logger.info("=" * 60)

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")
        scheduler.shutdown()
        sys.exit(0)


if __name__ == "__main__":
    main()
