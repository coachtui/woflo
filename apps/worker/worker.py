import logging
import os
import time

from apps.worker.app.core.logging import configure_logging


configure_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    worker_id = os.getenv("WORKER_ID", "worker")
    poll_interval = float(os.getenv("POLL_INTERVAL_SECONDS", "2"))

    logger.info("worker_starting", extra={"worker_id": worker_id})

    # MVP scaffold: job queue + DB access will be implemented in Milestone B.
    while True:
        logger.info("worker_heartbeat", extra={"worker_id": worker_id})
        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
