from typing import Protocol

from polybot.common.types import INSTRUMENT_ID
from polybot.common.types import Side

from .limit import Limit, LimitCheckResult

class ILimitStore(Protocol):
    def set_limit(self, instrument_id: INSTRUMENT_ID, limit: Limit):
        """Register a new limit for a given instrument"""
        ...

    def try_reserve_capacity(self, instrument_id: INSTRUMENT_ID, side: Side, volume: float, price: float) -> LimitCheckResult:
        """Checks if the order fits; if yes, updates 'in_flight' capacity immediately."""
        ...

    def release_reserved_capacity(self, instrument_id: INSTRUMENT_ID, side: Side, volume: float, price: float):
        """
        Rollback function. Called if an order fails to be sent or is cancelled 
        before any fill occurs.
        """
        ...
    
    def apply_fill(self, instrument_id: str, side: Side, 
                   reserved_price: float, reserved_volume: float,
                   fill_price: float, fill_volume: float):
        """
        Converts 'in_flight' reserved capacity into 'realized' position.
        Crucial for adjusting notional limits if the fill price differed from 
        the requested price.
        """
        ...

    

"""
LimitStore:
 -> Add limits for a given instrument
 -> Commit_And_Set_Limits: When we place an order, we commit and set the limits as to lock up the order volume.
 -> Release_Limits: When an order is cancelled, we release the limits.
 -> When an order is filled, we release the limits to 
"""

class LimitStore(ILimitStore):
    def __init__(self):
        self.limits: dict[INSTRUMENT_ID, Limit] = {}

    def get_limit(self, instrument_id: INSTRUMENT_ID) -> Limit:
        return self.limits[instrument_id]

    def set_limit(self, instrument_id: INSTRUMENT_ID, limit: Limit):
        self.limits[instrument_id] = limit
