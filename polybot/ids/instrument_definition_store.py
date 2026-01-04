from .interface import IInstrumentDefintionStore

from polybot.common.datastructures import TwoWayDict
from polybot.common.enums import Venue
from polybot.common.types import INSTRUMENT_ID

class InstrumentDefinitionStore(IInstrumentDefintionStore):
	def __init__(self):
		# Venue -> (InstrumentID <-> ExchangeInstrumentID)
		self.venue_store: dict[Venue, TwoWayDict[INSTRUMENT_ID, str]] = {}

	def get_instrument_id(self, venue: Venue, exchange_id: str) -> INSTRUMENT_ID:
		id_mapping = self.venue_store.get(venue)

		return id_mapping[exchange_id]

	def get_exchange_id(self, venue: Venue, instrument_id: INSTRUMENT_ID) -> str:
		id_mapping = self.venue_store.get(venue)

		return id_mapping[instrument_id]

