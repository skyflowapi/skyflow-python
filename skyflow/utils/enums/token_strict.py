from enum import Enum

from skyflow.generated.rest import V1BYOT


class TokenStrict(Enum):
    DISABLE = V1BYOT.DISABLE
    ENABLE = V1BYOT.ENABLE
    ENABLE_STRICT = V1BYOT.ENABLE_STRICT