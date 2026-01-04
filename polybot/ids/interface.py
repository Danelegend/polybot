from polybot.common.enums import Venue
from polybot.common.types import INSTRUMENT_ID

class IInstrumentDefintionStore:
	def get_instrument_id(self, venue: Venue, exchange_id: str) -> INSTRUMENT_ID:
		...

	def get_exchange_id(self, venue: Venue, instrument_id: INSTRUMENT_ID) -> str:
		...

	