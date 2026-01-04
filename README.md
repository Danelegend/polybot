# Polymarket Trading Bot Framework (Pre-Beta)

> Production-grade infrastructure for building algorithmic trading bots on Polymarket. Focus on strategy, not plumbing.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Polybot is an open-source framework providing the core **commodity functionality** needed for prediction market trading bots. Commodity functionality refers to components that almost all trading bots require with only minor variations between implementations.

Rather than rebuilding information links, execution links, orderbooks, order management, position management, and limit checking for every bot, Polybot provides battle-tested implementations of these components bundled into a fast tick-to-trade pipeline. **You simply implement your strategy and focus on where the alpha is.**

### Key Benefits

- **Fast Development** - Go from idea to live trading in minutes, not days
- **Low Latency** - Optimized hot loop for fast tick-to-trade execution
- **Risk Management** - Built-in position and notional limits to prevent runaway losses
- **Real-time State** - Live tracking of orderbooks, positions, and active orders
- **Event-Driven** - React to trades and orderbook changes as they happen

### Rationale

After building numerous trading bots, I noticed that 80% of the code was repetitive infrastructure. This framework extracts that common functionality, allowing developers to focus on what actually generates returns: **strategy logic**.

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/polybot.git
cd polybot

# Install dependencies with uv (recommended)
uv sync

# Or with pip
pip install -r requirements.txt
```

## Quick Start

Here's a complete example of a simple market-making strategy:

```python
from sdk import Strategy, Order, InstrumentLimit, Side, register_strategy, start

class SimpleMarketMaker(Strategy):
    def on_trade(self, instrument_id: str, trade, orderbook):
        """React to trades by placing orders around the mid price"""
        orders = []
        
        mid_price = (orderbook.best_bid + orderbook.best_ask) / 2
        spread = 0.02  # 2% spread
        
        # Place bid and ask orders
        orders.append(Order(
            instrument_id=instrument_id,
            side=Side.BUY,
            price=mid_price * (1 - spread/2),
            volume=10
        ))
        orders.append(Order(
            instrument_id=instrument_id,
            side=Side.SELL,
            price=mid_price * (1 + spread/2),
            volume=10
        ))
        
        return orders
    
    def on_order_book_change(self, instrument_id: str, orderbook):
        """React to orderbook changes"""
        # Could implement similar logic or different strategy
        return []

# Register strategy with instrument IDs and limits
register_strategy(
    strategy=SimpleMarketMaker,
    instrument_ids=["0x1234567890123456789012345678901234567890"],
    limits=[InstrumentLimit(
        instrument_id="0x1234567890123456789012345678901234567890",
        max_position_bid=100,
        max_position_ask=100,
        max_nominal_position_bid=1000,
        max_nominal_position_ask=1000,
    )]
)

# Start the trading bot
start()
```

## How It Works

### Architecture

Polybot uses an event-driven architecture:

1. **Information Link** - WebSocket connection receives real-time market data from Polymarket
2. **Event Processing** - Trades and orderbook updates are parsed and routed to registered strategies
3. **Strategy Execution** - Your strategy logic processes events and returns desired orders
4. **Risk Checks** - Orders are validated against position and notional limits
5. **Execution Link** - Valid orders are sent to Polymarket (coming soon)
6. **State Updates** - Internal state is updated to reflect positions and active orders

### Creating a Strategy

Implement the `Strategy` base class:

```python
from sdk import Strategy, Order, OrderBook, TradeData

class MyStrategy(Strategy):
    def on_trade(self, instrument_id: str, trade: TradeData, orderbook: OrderBook) -> list[Order]:
        """
        Called when a trade occurs on a subscribed instrument.
        
        Args:
            instrument_id: The instrument that traded
            trade: Trade details (price, size, side)
            orderbook: Current orderbook state
            
        Returns:
            List of orders to place (can be empty)
        """
        return []
    
    def on_order_book_change(self, instrument_id: str, orderbook: OrderBook) -> list[Order]:
        """
        Called when the orderbook changes for a subscribed instrument.
        
        Args:
            instrument_id: The instrument that changed
            orderbook: Updated orderbook state
            
        Returns:
            List of orders to place (can be empty)
        """
        return []
```

### Registering Strategies

Use `register_strategy()` to connect your strategy to specific instruments:

```python
from sdk import register_strategy, InstrumentLimit

register_strategy(
    strategy=MyStrategy,
    instrument_ids=[
        "0x1234...",  # List all instruments to subscribe to
        "0x5678...",
    ],
    limits=[
        InstrumentLimit(
            instrument_id="0x1234...",
            max_position_bid=100,        # Max units on bid side
            max_position_ask=100,        # Max units on ask side
            max_nominal_position_bid=1000,   # Max $ on bid side
            max_nominal_position_ask=1000,   # Max $ on ask side
        ),
        # Add limits for each instrument
    ]
)
```

### Setting Risk Limits

Risk limits prevent strategies from accumulating excessive exposure:

- **Position Limits** - Maximum number of units (contracts) you can hold
- **Notional Limits** - Maximum dollar value of positions (price × volume)

Limits are checked **before** every order placement. Orders that would violate limits are rejected.

## Features

### ✅ Currently Available

- **Polymarket Information Link** - Real-time WebSocket connection with automatic reconnection
- **Orderbook Management** - Efficient orderbook data structures with fast updates
- **Strategy Routing** - Event routing to registered strategies based on instrument subscriptions
- **Position Tracking** - Real-time position monitoring across all instruments
- **Limit Enforcement** - Pre-trade risk checks for position and notional limits
- **Type Safety** - Full type hints and Pydantic validation

### 🚧 Coming Soon

- **Execution Link** - Order placement and cancellation via wallet integration
- **Order State Tracking** - Monitor in-flight and filled orders
- **Advanced Limits** - Max PnL, max volume, price collars, circuit breakers
- **Custom Data Sources** - Integrate external data feeds into trading decisions
- **Multi-Venue Support** - Expand to Kalshi and other prediction markets

## Use Cases

### ✅ Great For

- **Market Making** - Provide liquidity and capture spread
- **Statistical Arbitrage** - Exploit statistical relationships between markets
- **Mispricing Detection** - Trade on pricing inefficiencies
- **Momentum/Trend Following** - Ride market trends
- **Strategies requiring low-medium latency** - Fast but not ultra-high-frequency

### ❌ Not Suitable For

- **Ultra-low latency strategies** - If you need to be first by milliseconds
- **Competitive arbitrage** - Strategies that require skipping safety checks for speed

## API Reference

### Strategy Class

The base class for all strategies:

| Method | Arguments | Returns | Description |
|--------|-----------|---------|-------------|
| `on_trade` | `instrument_id: str`<br>`trade: TradeData`<br>`orderbook: OrderBook` | `list[Order]` | Called when a trade occurs |
| `on_order_book_change` | `instrument_id: str`<br>`orderbook: OrderBook` | `list[Order]` | Called when orderbook updates |

### Order Class

```python
Order(
    instrument_id: str,  # Instrument to trade
    side: Side,          # Side.BUY or Side.SELL
    price: Decimal,      # Limit price (must be > 0)
    volume: Decimal      # Order size (must be > 0)
)
```

### InstrumentLimit Class

```python
InstrumentLimit(
    instrument_id: str,              # Instrument to limit
    max_position_bid: Decimal,       # Max units on bid side
    max_position_ask: Decimal,       # Max units on ask side
    max_nominal_position_bid: Decimal,   # Max $ value on bid side
    max_nominal_position_ask: Decimal    # Max $ value on ask side
)
```

### Functions

- `register_strategy(strategy, instrument_ids, limits)` - Register a strategy with instruments and limits
- `start()` - Start the trading bot (blocking call)

## Project Status

**Current Version**: Pre-Beta v0.0.1

This project is in active development. Core infrastructure is functional, but execution capabilities are still being implemented. Use in production at your own risk.

### Roadmap

- [ ] Complete execution link with wallet integration
- [ ] Order state tracking and management
- [ ] Historical data replay for backtesting
- [ ] Enhanced risk management tools
- [ ] Performance monitoring and metrics
- [ ] Multi-venue support (Kalshi, etc.)
- [ ] Documentation and examples
- [ ] Comprehensive test coverage

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

### Development Setup

```bash
# Clone and install in development mode
git clone https://github.com/yourusername/polybot.git
cd polybot
uv sync

# Run tests
pytest tests/
```

## Support & Feedback

Have questions or suggestions? I'd love to hear from you:

- Open an [issue](https://github.com/yourusername/polybot/issues)
- Start a [discussion](https://github.com/yourusername/polybot/discussions)
- Contribute via [pull request](https://github.com/yourusername/polybot/pulls)

## License

MIT License - see LICENSE file for details.

## Disclaimer

This software is provided for educational purposes. Trading involves substantial risk of loss. Use at your own risk.