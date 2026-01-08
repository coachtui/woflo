import asyncio
import logging
import os
import signal
import sys

from app.core.logging import configure_logging
from app.db.session import close_pool, get_pool
from app.queue_processor import process_job


configure_logging()
logger = logging.getLogger(__name__)


# Global shutdown flag
_shutdown = False


def handle_shutdown_signal(signum: int, frame: object) -> None:
    """Handle shutdown signals gracefully."""
    global _shutdown
    logger.info("shutdown_signal_received", extra={"signal": signum})
    _shutdown = True


async def worker_loop(worker_id: str, poll_interval: float) -> None:
    """
    Main worker loop.
    
    Continuously polls for jobs and processes them.
    Uses FOR UPDATE SKIP LOCKED for safe concurrent processing.
    """
    global _shutdown
    
    pool = await get_pool()
    logger.info("worker_started", extra={"worker_id": worker_id})
    
    try:
        while not _shutdown:
            try:
                # Try to process a job
                processed = await process_job(pool, worker_id)
                
                if processed:
                    # Job was processed, check for more immediately
                    continue
                else:
                    # No jobs available, wait before polling again
                    await asyncio.sleep(poll_interval)
                    
            except Exception as e:
                logger.error(
                    "worker_loop_error",
                    extra={"worker_id": worker_id, "error": str(e)},
                    exc_info=True,
                )
                # Wait before retrying to avoid tight error loops
                await asyncio.sleep(poll_interval)
    
    finally:
        logger.info("worker_shutting_down", extra={"worker_id": worker_id})
        await close_pool()
        logger.info("worker_stopped", extra={"worker_id": worker_id})


def main() -> None:
    """Entry point for worker."""
    worker_id = os.getenv("WORKER_ID", "worker-1")
    poll_interval = float(os.getenv("POLL_INTERVAL_SECONDS", "2"))
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    
    try:
        asyncio.run(worker_loop(worker_id, poll_interval))
    except KeyboardInterrupt:
        logger.info("worker_interrupted")
    except Exception as e:
        logger.error("worker_fatal_error", extra={"error": str(e)}, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
