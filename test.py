class PymonSupport:
    @classmethod
    def pymon_entrypoint(cls) -> None:
        print("a")

    @classmethod
    def pymon_cleanup(cls) -> None:
        print("clean")
