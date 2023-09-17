import sys
from time import sleep

from click import Path, command, option
from loguru import logger

from exc import ChangeDetected, UnsafeExit
from pymon import Pymon
from utils import Stdout


@command()
@option("--file", type=Path(exists=True), help="File path to monitor")
@option("--tb_limit", type=int, default=3, help="Exception traceback limit (default 3)")
@option("--retries", type=int, default=5, help="Retry limit before exiting (default 5)")
@option("--retry-delay", type=int, default=5, help="Delay between retries (default 5)")
@option(
    "--rate",
    type=int,
    default=2,
    help="Rate to poll for changes in seconds (default 2)",
)
def cli(file: str, tb_limit: int, retries: int, retry_delay: int, rate: int) -> None:
    if not "--help" in sys.argv:
        sys.stdout = Stdout()

    sys.tracebacklimit = tb_limit
    current_retries = 0

    logger.info(f"monitoring {file}\n")

    while current_retries <= retries:
        try:
            Pymon(file, rate).start_monitor()

        except Exception as exc:
            if not exc.__cause__:  # Sometimes a blank error is thrown
                continue

            if isinstance(exc.__cause__, ChangeDetected):
                logger.info("change detected in file, restarting\n")

                continue

            current_retries += 1

            logger.opt(exception=exc.__cause__).error(
                "exception raised during execution"
            )

            if isinstance(exc, UnsafeExit):
                logger.warning(str(exc) + "\n")

            else:
                logger.info(str(exc) + "\n")

            sleep(retry_delay)

    logger.warning("reached max retries, exiting")


if __name__ == "__main__":
    if not sys.version_info >= (3, 8):
        logger.error("requires python >= 3.8")

    else:
        cli()
