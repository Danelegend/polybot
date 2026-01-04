from sdk import *

class TestStrategy(Strategy):
    def on_trade(self) -> list[Order]:
        return []

    def on_order_book_change(self) -> list[Order]:
        return []

register_strategy(TestStrategy, ["0x1234567890123456789012345678901234567890"], [InstrumentLimit(
    instrument_id="0x1234567890123456789012345678901234567890",
    max_position_bid=100,
    max_position_ask=100,
    max_nominal_position_bid=100,
    max_nominal_position_ask=100,
)])

