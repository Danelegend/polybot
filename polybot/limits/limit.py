from pydantic import BaseModel

from polybot.common.types import INSTRUMENT_ID

class Limit(BaseModel):
    instrument_id: INSTRUMENT_ID

    max_position_size: float # Total volume of the instrument that can be held
    max_nominal_position_size: float # Total value of the instrument that can be held


class LimitCheckResult(BaseModel):
    allowed: bool
    reason: str = ""