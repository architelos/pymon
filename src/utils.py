from typing import Any

from loguru import logger


def get_attribute(obj: Any, name: str) -> Any | None:
    try:
        return getattr(obj, name)

    except AttributeError:
        return None


class Stdout:
    def write(self, message: str) -> None:
        if message == "\n":  # Account for sys.stdout.write()
            return

        logger.debug(message)

    def flush(self) -> None:
        pass
