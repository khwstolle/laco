import enum
import typing


# Internal keys for lazy calls
@typing.final
class LazyKey(enum.StrEnum):
    CALL = "_target_"
    ARGS = "_args_"
    PARTIAL = "_partial_"


LAZY_CALL: typing.Final[str] = LazyKey.CALL.value
LAZY_ARGS: typing.Final[str] = LazyKey.ARGS.value
LAZY_PART: typing.Final[str] = LazyKey.PARTIAL.value

# Configuration root keys
CONFIG_VERSION: typing.Final[str] = "VERSION"
CONFIG_NAME: typing.Final[str] = "NAME"
