"""
Integration tests for the Polymarket trading system.

These tests verify the complete data flow from exchange messages through to
strategy order generation. They use mock components to simulate the exchange
and capture outgoing orders.
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import pytest

from polybot.app import AppInterface, build_app
from polybot.common.enums import Venue, Side as CoreSide
from polybot.common.types import Order, INSTRUMENT_ID
from polybot.ids.interface import IInstrumentDefintionStore
from polybot.limits.limit_store import ILimitStore
from polybot.limits.limit import Limit
from polybot.polymarket import PolymarketIml
from polybot.polymarket.interfaces import PolymarketMessageHandler
from polybot.polymarket.polymarket_ws import IPolymarketWebsocket
from polybot.polymarket.types.messages import (
    OrderBookSummaryEvent,
    LastTradePriceEvent,
    OrderSummary,
)
from polybot.strategy import StrategyRegistry

from sdk.base_strategy import Strategy
from sdk.registration import register_strategy
from sdk.types import Order as SDKOrder, InstrumentLimit, TradeData, OrderBook
from sdk.enums import Side


# -----------------------------------------------------------------------------
# Mock Components
# -----------------------------------------------------------------------------

class MockPolymarketWebsocket(IPolymarketWebsocket):
    """
    A mock websocket that allows injection of messages into the IML.
    
    Instead of connecting to a real websocket, this mock allows tests to
    directly inject market data events as if they came from the exchange.
    """
    
    def __init__(self):
        self._handler: Optional[PolymarketMessageHandler] = None
        self._subscribed_markets: set[str] = set()
    
    def set_handler(self, handler: PolymarketMessageHandler):
        """Set the message handler (typically the IML)"""
        self._handler = handler
    
    def subscribe_to_market(self, token_id: str):
        """Track subscription requests"""
        self._subscribed_markets.add(token_id)
    
    @property
    def subscribed_markets(self) -> set[str]:
        return self._subscribed_markets
    
    # Message injection methods for testing
    def inject_orderbook_snapshot(
        self,
        token_id: str,
        bids: list[tuple[float, float]],
        asks: list[tuple[float, float]],
        timestamp: Optional[datetime] = None,
    ):
        """
        Inject an orderbook snapshot message.
        
        Args:
            token_id: The token/instrument ID
            bids: List of (price, size) tuples for bid levels
            asks: List of (price, size) tuples for ask levels
            timestamp: Optional timestamp, defaults to now
        """
        if self._handler is None:
            raise RuntimeError("Handler not set. Call set_handler first.")
        
        event = OrderBookSummaryEvent(
            event_type="book",
            asset_id=token_id,
            timestamp=timestamp or datetime.now(timezone.utc),
            bids=[OrderSummary(price=p, size=s) for p, s in bids],
            asks=[OrderSummary(price=p, size=s) for p, s in asks],
        )
        self._handler.handle_order_book_summary_event(event)
    
    def inject_trade(
        self,
        token_id: str,
        price: float,
        size: float,
        side: str,  # "BUY" or "SELL"
        condition_id: str = "0x" + "0" * 64,
        fee_rate_bps: float = 0.0,
        timestamp: Optional[datetime] = None,
    ):
        """
        Inject a trade message.
        
        Args:
            token_id: The token/instrument ID
            price: Trade price
            size: Trade size
            side: "BUY" or "SELL" - the taker side
            condition_id: Market condition ID (can use default for testing)
            fee_rate_bps: Fee rate in basis points
            timestamp: Optional timestamp, defaults to now
        """
        if self._handler is None:
            raise RuntimeError("Handler not set. Call set_handler first.")
        
        event = LastTradePriceEvent(
            event_type="last_trade_price",
            asset_id=token_id,
            price=price,
            size=size,
            side=side,
            market=condition_id,
            fee_rate_bps=fee_rate_bps,
            timestamp=timestamp or datetime.now(timezone.utc),
        )
        self._handler.handle_last_trade_price_event(event)


class MockInstrumentDefinitionStore(IInstrumentDefintionStore):
    """Simple mock that returns instrument IDs as-is"""
    
    def __init__(self):
        self._instruments: dict[str, INSTRUMENT_ID] = {}
    
    def register_instrument(self, venue: Venue, exchange_id: str, instrument_id: INSTRUMENT_ID):
        """Register an instrument mapping"""
        self._instruments[f"{venue.value}:{exchange_id}"] = instrument_id
    
    def get_instrument_id(self, venue: Venue, exchange_id: str) -> INSTRUMENT_ID:
        return self._instruments.get(f"{venue.value}:{exchange_id}", exchange_id)
    
    def get_exchange_id(self, venue: Venue, instrument_id: INSTRUMENT_ID) -> str:
        for key, iid in self._instruments.items():
            if iid == instrument_id:
                return key.split(":")[1]
        return str(instrument_id)


class MockLimitStore(ILimitStore):
    """Simple mock limit store that allows all orders"""
    
    def __init__(self):
        self._limits: dict[INSTRUMENT_ID, Limit] = {}
    
    def set_limit(self, instrument_id: INSTRUMENT_ID, limit: Limit):
        self._limits[instrument_id] = limit
    
    def try_reserve_capacity(self, instrument_id: INSTRUMENT_ID, side: CoreSide, volume: float, price: float):
        from polybot.limits.limit import LimitCheckResult
        return LimitCheckResult(allowed=True)
    
    def release_reserved_capacity(self, instrument_id: INSTRUMENT_ID, side: CoreSide, volume: float, price: float):
        pass
    
    def apply_fill(self, instrument_id: str, side: CoreSide, 
                   reserved_price: float, reserved_volume: float,
                   fill_price: float, fill_volume: float):
        pass


class OrderCapture:
    """Captures orders generated by strategies for test assertions"""
    
    def __init__(self):
        self.orders: list[Order] = []
    
    def capture(self, order: Order):
        """Called by the channel when an order is generated"""
        self.orders.append(order)
    
    def clear(self):
        """Clear captured orders"""
        self.orders.clear()
    
    def get_orders(self) -> list[Order]:
        return self.orders.copy()


# -----------------------------------------------------------------------------
# Test Harness
# -----------------------------------------------------------------------------

class IntegrationTestHarness:
    """
    A test harness that wires up all components for integration testing.
    
    This harness:
    - Creates a mock websocket for injecting market data
    - Creates mock stores for IDS and limits
    - Captures outgoing orders for assertions
    - Provides a complete App instance for testing
    """
    
    def __init__(self):
        self.mock_ws = MockPolymarketWebsocket()
        self.mock_ids = MockInstrumentDefinitionStore()
        self.mock_limit_store = MockLimitStore()
        self.order_capture = OrderCapture()
        
        # Create IML with mock websocket
        self.iml = PolymarketIml(ws=self.mock_ws)
        # Wire up the handler
        self.mock_ws.set_handler(self.iml)
        
        self.app: Optional[AppInterface] = None
    
    def build_app(self) -> AppInterface:
        """Build the app with all mocked components"""
        self.app = build_app(
            ids=self.mock_ids,
            iml=self.iml,
            limit_store=self.mock_limit_store,
            order_handler=self.order_capture.capture,
        )
        return self.app
    
    def initialize_and_run(self):
        """Initialize and run the app"""
        if self.app is None:
            self.build_app()
        self.app.initialize()
        self.app.run()
    
    def stop(self):
        """Stop the app"""
        if self.app:
            self.app.stop()
    
    def inject_orderbook(
        self,
        token_id: str,
        bids: list[tuple[float, float]],
        asks: list[tuple[float, float]],
    ):
        """Inject an orderbook snapshot"""
        self.mock_ws.inject_orderbook_snapshot(token_id, bids, asks)
    
    def inject_trade(
        self,
        token_id: str,
        price: float,
        size: float,
        side: str,
    ):
        """Inject a trade event"""
        self.mock_ws.inject_trade(token_id, price, size, side)
    
    def get_captured_orders(self) -> list[Order]:
        """Get all captured orders"""
        return self.order_capture.get_orders()
    
    def clear_orders(self):
        """Clear captured orders"""
        self.order_capture.clear()


# -----------------------------------------------------------------------------
# Test Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def harness():
    """Create a test harness for each test"""
    # Reset the strategy registry before each test
    StrategyRegistry.reset()
    
    h = IntegrationTestHarness()
    yield h
    h.stop()


# -----------------------------------------------------------------------------
# Test Strategies
# -----------------------------------------------------------------------------

class TradeFollowingStrategy(Strategy):
    """
    A simple strategy that places a BUY order at the trade price
    whenever a trade occurs.
    
    This is used to test the complete data flow from trade event to order.
    """
    
    def on_trade(self, instrument_id: str, trade: TradeData, orderbook: OrderBook) -> list[SDKOrder]:
        # Place a buy order at the trade price for 10 units
        return [
            SDKOrder(
                instrument_id=instrument_id,
                side=Side.BUY,
                price=trade.price,
                volume=Decimal("10"),
            )
        ]
    
    def on_order_book_change(self, instrument_id: str, orderbook: OrderBook) -> list[SDKOrder]:
        return []


# -----------------------------------------------------------------------------
# Integration Tests
# -----------------------------------------------------------------------------

def test_trade_following_strategy_sends_order_at_trade_price(harness: IntegrationTestHarness):
    """
    Test the complete flow:
    1. Subscribe to an instrument
    2. Receive an orderbook snapshot
    3. Receive a trade
    4. Strategy generates an order at the trade price
    
    This verifies the entire data path from exchange message to strategy order.
    """
    # Define test instrument
    test_token_id = "test_token_123"
    
    # Register the strategy
    register_strategy(
        strat_class=TradeFollowingStrategy,
        instrument_ids=[test_token_id],
        limits=[
            InstrumentLimit(
                instrument_id=test_token_id,
                max_position_bid=Decimal("1000"),
                max_position_ask=Decimal("1000"),
                max_nominal_position_bid=Decimal("100000"),
                max_nominal_position_ask=Decimal("100000"),
            )
        ],
        name="TradeFollower",
    )
    
    # Build and initialize the app
    harness.build_app()
    harness.initialize_and_run()
    
    # Inject an orderbook snapshot
    harness.inject_orderbook(
        token_id=test_token_id,
        bids=[(0.50, 100.0), (0.49, 200.0), (0.48, 300.0)],
        asks=[(0.51, 100.0), (0.52, 200.0), (0.53, 300.0)],
    )
    
    # Clear any orders from the snapshot phase
    harness.clear_orders()
    
    # Inject a trade at price 0.505
    trade_price = 0.505
    trade_size = 50.0
    harness.inject_trade(
        token_id=test_token_id,
        price=trade_price,
        size=trade_size,
        side="BUY",
    )
    
    # Get captured orders
    orders = harness.get_captured_orders()
    
    # Assert we got exactly one order
    assert len(orders) == 1, f"Expected 1 order, got {len(orders)}"
    
    order = orders[0]
    
    # Assert order properties
    assert order.instrument_id == test_token_id
    assert order.side == CoreSide.BUY
    assert float(order.price) == pytest.approx(trade_price, rel=1e-6)
    assert float(order.quantity) == 10.0


def test_multiple_trades_generate_multiple_orders(harness: IntegrationTestHarness):
    """Test that multiple trades generate multiple orders"""
    test_token_id = "multi_trade_token"
    
    register_strategy(
        strat_class=TradeFollowingStrategy,
        instrument_ids=[test_token_id],
        limits=[
            InstrumentLimit(
                instrument_id=test_token_id,
                max_position_bid=Decimal("1000"),
                max_position_ask=Decimal("1000"),
                max_nominal_position_bid=Decimal("100000"),
                max_nominal_position_ask=Decimal("100000"),
            )
        ],
        name="MultiTradeFollower",
    )
    
    harness.build_app()
    harness.initialize_and_run()
    
    # Inject orderbook
    harness.inject_orderbook(
        token_id=test_token_id,
        bids=[(0.50, 100.0)],
        asks=[(0.51, 100.0)],
    )
    harness.clear_orders()
    
    # Inject multiple trades
    trade_prices = [0.51, 0.52, 0.53]
    for price in trade_prices:
        harness.inject_trade(
            token_id=test_token_id,
            price=price,
            size=10.0,
            side="BUY",
        )
    
    orders = harness.get_captured_orders()
    
    assert len(orders) == 3
    for i, order in enumerate(orders):
        assert float(order.price) == pytest.approx(trade_prices[i], rel=1e-6)


def test_orderbook_is_populated_before_strategy_receives_trade(harness: IntegrationTestHarness):
    """
    Test that when a strategy receives a trade, it can also access
    the current orderbook state.
    """
    test_token_id = "orderbook_test_token"
    
    # Track what orderbook state the strategy sees
    orderbook_states = []
    
    class OrderbookTrackingStrategy(Strategy):
        def on_trade(self, instrument_id: str, trade: TradeData, orderbook: OrderBook) -> list[SDKOrder]:
            # Capture the orderbook state when trade is received
            orderbook_states.append({
                "best_bid": orderbook.best_bid().price if orderbook.best_bid() else None,
                "best_ask": orderbook.best_ask().price if orderbook.best_ask() else None,
            })
            return []
        
        def on_order_book_change(self, instrument_id: str, orderbook: OrderBook) -> list[SDKOrder]:
            return []
    
    register_strategy(
        strat_class=OrderbookTrackingStrategy,
        instrument_ids=[test_token_id],
        limits=[
            InstrumentLimit(
                instrument_id=test_token_id,
                max_position_bid=Decimal("1000"),
                max_position_ask=Decimal("1000"),
                max_nominal_position_bid=Decimal("100000"),
                max_nominal_position_ask=Decimal("100000"),
            )
        ],
        name="OrderbookTracker",
    )
    
    harness.build_app()
    harness.initialize_and_run()
    
    # Inject orderbook with known bid/ask
    harness.inject_orderbook(
        token_id=test_token_id,
        bids=[(0.45, 100.0)],
        asks=[(0.55, 100.0)],
    )
    
    # Inject a trade
    harness.inject_trade(
        token_id=test_token_id,
        price=0.50,
        size=10.0,
        side="BUY",
    )
    
    # Verify the strategy saw the correct orderbook state
    assert len(orderbook_states) == 1
    assert orderbook_states[0]["best_bid"] == pytest.approx(0.45, rel=1e-6)
    assert orderbook_states[0]["best_ask"] == pytest.approx(0.55, rel=1e-6)
