"""
SDK Registry Utilities

This module provides conversion functions for translating SDK types
to core types when registering strategies.
"""

from polybot.limits import Limit
from sdk.types import InstrumentLimit


def convert_sdk_limit_to_core_limit(sdk_limit: InstrumentLimit) -> Limit:
	"""
	Convert an SDK InstrumentLimit to a core Limit.
	
	The SDK exposes bid/ask limits separately, while the core uses
	combined max values. We take the maximum of bid/ask for position limits.
	"""
	return Limit(
		instrument_id=sdk_limit.instrument_id,
		max_position_size=float(max(
			sdk_limit.max_position_bid,
			sdk_limit.max_position_ask
		)),
		max_nominal_position_size=float(max(
			sdk_limit.max_nominal_position_bid,
			sdk_limit.max_nominal_position_ask
		)),
	)
