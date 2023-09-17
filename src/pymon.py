from importlib.util import module_from_spec, spec_from_file_location
from inspect import ismethod
from os import stat
from threading import Thread
from time import sleep
from typing import Callable

from loguru import logger

from src.exc import (
    ChangeDetected,
    InvalidImplementation,
    SafeExit,
    ThreadException,
    UnsafeExit,
)
from src.utils import get_attribute


# https://stackoverflow.com/questions/6800984/how-to-pass-and-run-a-callback-method-in-python
class ThreadingManager:
    def __init__(self) -> None:
        self.exception = None
        self.finished = False

    def new_thread(self, target: Callable) -> "CallbackThread":
        self.finished = False

        return CallbackThread(parent=self, target=target)

    def thread_finished(self, exception: Exception = None) -> None:
        self.finished = True
        self.exception = exception


class CallbackThread(Thread):
    def __init__(self, parent: ThreadingManager, target: Callable) -> None:
        self.parent = parent

        super().__init__(target=target)

    def run(self) -> None:
        exception = None

        try:
            super().run()

        except Exception as exc:
            exception = exc

        self.parent.thread_finished(exception)


class Pymon:
    def __init__(self, file_name: str, rate: int) -> None:
        self.rate = rate
        self.file_name = file_name
        self.last_modify = stat(file_name).st_mtime

        spec = spec_from_file_location("pymon_support", file_name)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)

        self.module = module

    def start_monitor(self) -> None:
        if not get_attribute(self.module, "PymonSupport"):
            raise InvalidImplementation("PymonSupport")

        self.pymonSupport = self.module.PymonSupport
        self.pymonEntrypoint = get_attribute(self.pymonSupport, "pymon_entrypoint")
        if not ismethod(self.pymonEntrypoint):
            raise InvalidImplementation("pymon_entrypoint")

        self.pymonCleanup = get_attribute(self.pymonSupport, "pymon_cleanup")

        try:
            manager = ThreadingManager()

            thread = manager.new_thread(self.pymonEntrypoint)
            thread.daemon = True
            thread.start()

            printed_already = False

            while True:
                if manager.finished:
                    if manager.exception:
                        raise ThreadException from manager.exception

                    if not printed_already:
                        logger.info("finished execution, waiting for changes")

                        printed_already = True

                    last_modify = stat(self.file_name).st_mtime
                    if last_modify != self.last_modify:
                        printed_already = False

                        raise ChangeDetected

                    sleep(self.rate)

        except ThreadException as exc:
            if not self.pymonCleanup:
                raise UnsafeExit("retrying unsafely; no cleanup method") from exc

            self.pymonCleanup()
            raise SafeExit("retrying safely") from exc
