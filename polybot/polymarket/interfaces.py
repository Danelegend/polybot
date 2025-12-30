from typing import Protocol

from .types.messages import (
    OrderBookSummaryEvent,
    PriceChangeEvent,
    TickSizeChangeEvent,
    LastTradePriceEvent,
)


class PolymarketMessageHandler(Protocol):
    def handle_order_book_summary_event(self, event: OrderBookSummaryEvent):
        ...

    def handle_price_change_event(self, event: PriceChangeEvent):
        ...

    def handle_tick_size_change_event(self, event: TickSizeChangeEvent):
        ...

    def handle_last_trade_price_event(self, event: LastTradePriceEvent):
        ...

