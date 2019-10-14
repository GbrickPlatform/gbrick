

class NotInputSeed(Exception):
    # password argument error
    pass


class ValidationError(Exception):
    # transaction, header, block, receipt ...
    pass


class CacheError(Exception):
    # state cache error
    pass


class RoundError(Exception):
    # consensus round error
    pass


class FinalizeError(Exception):
    # not safe finality
    pass


class SerializeError(Exception):
    # data structure error
    pass


class GenesisError(Exception):
    pass


class FeeLimitedError(Exception):
    pass


class StackOverFlow(Exception):
    pass


class MemoryOverFlow(Exception):
    pass


class MemoryReadError(Exception):
    pass

