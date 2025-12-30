from .interface import MarketDataConsumer, MarketDataProvider
from .messages import MarketEvent, MarketEventType

from collections import defaultdict
from typing import Generator

class ImlBase(MarketDataProvider):
    def __init__(self):
        self.subscriptions: defaultdict[str, list[MarketDataConsumer]] = defaultdict(list)

    def subscribe(self, instrument_id: str, consumer: MarketDataConsumer):
        self.subscriptions[instrument_id].append(consumer)

    def get_consumers(self, instrument_id: str) -> Generator[MarketDataConsumer, None, None]:
        yield from self.subscriptions[instrument_id]

    def emit_message(self, event: MarketEvent):
        for consumer in self.get_consumers(event.instrument_id):
            emit_event_to_consumer(event, consumer)



def emit_event_to_consumer(event: MarketEvent, consumer: MarketDataConsumer):
    match event.event_type:
        case MarketEventType.PRICE_CHANGE:
            consumer.on_price_change_event(event)
        case MarketEventType.TRADE:
            consumer.on_trade_event(event)
        case MarketEventType.ORDERBOOK_SNAPSHOT:
            consumer.on_order_book_snapshot_event(event)
        case _:
            raise ValueError(f"Unknown event type: {event.event_type}")

