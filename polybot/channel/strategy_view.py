from polybot.common.orderbook import OrderBook
from polybot.common.types import INSTRUMENT_ID
from polybot.strategy import StrategyBase, StrategyInterface, TradeData
from polybot.common.types import OrderRequest
from polybot.common.context_provider import ContextProvider

class StrategyView(StrategyInterface):
    def __init__(self, strategy: StrategyBase):
        self._strategy = strategy
        # Store by ID for lookups, but the value is the reference
        self._books_map: dict[INSTRUMENT_ID, OrderBook] = {}
        # Store as a list for fast iteration in the hot loop
        self._books_list: list[OrderBook] = []

    def add_orderbook(self, instrument_id: INSTRUMENT_ID, orderbook: OrderBook):
        """Adds the book reference to both the map and the list."""
        if instrument_id not in self._books_map:
            self._books_map[instrument_id] = orderbook
            self._books_list.append(orderbook)

    @property
    def books(self) -> list[OrderBook]:
        """The strategy can iterate this list very quickly."""
        return self._books_list

    def get_book(self, instrument_id: INSTRUMENT_ID) -> OrderBook:
        """The strategy can grab a specific book by ID."""
        return self._books_map[instrument_id]

    def on_trade(self, instrument_id: INSTRUMENT_ID, trade_data: TradeData, orderbook: OrderBook, context: ContextProvider) -> list[OrderRequest]:
        return self._strategy.on_trade(
            instrument_id, 
            trade_data, 
            orderbook,
            self._to_strategy_context(context)
        )

    def on_order_book_change(self, instrument_id: INSTRUMENT_ID, orderbook: OrderBook, context: ContextProvider) -> list[OrderRequest]:
        return self._strategy.on_order_book_change(
            instrument_id, 
            orderbook,
            self._to_strategy_context(context)
        )


    def _to_strategy_context(self, context: ContextProvider) -> ContextProvider:
        context.orderbooks = self._books_map
        return context