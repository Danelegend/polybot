from polybot.common.enums import Venue

class IInstrumentDefintionStore:
    def get_instrument_id(self, venue: Venue, exchange_id: str) -> int:
        ...

    def get_exchange_id(self, venue: Venue, instrument_id: int) -> str:
        ...

    