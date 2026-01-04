from polybot.iml import ImlBase, MarketDataConsumer
from polybot.iml import (
		OrderBookSnapshotEvent as ImlOrderBookSnapshotEvent,
		OrderBookUpdateEvent as ImlOrderBookUpdateEvent,
		TradeEvent as ImlTradeEvent,
		LevelDelta as ImlLevelDelta,
		Level as ImlLevel,
)
from polybot.common.enums import Venue
from polybot.common.enums import Side

from .interfaces import PolymarketMessageHandler
from .polymarket_ws import PolyMarketWebSocket, IPolymarketWebsocket
from .types.messages import (
	OrderBookSummaryEvent,
	PriceChangeEvent,
	TickSizeChangeEvent,
	LastTradePriceEvent,
)

from decimal import Decimal
from typing import Dict, Optional

"""
POLYMARKET API NOTES:
There are 3 messages that we care about:
 - book: a full snapshot of the order book at a point in time
 - price_change: when the price of a level changes
 - last_trade_price: when a trade occurs.

 Book will be given to us when we initially subscribe.

 Price change is given to us as users insert and cancel orders

 Last trade price is given to us when a trade occurs. This also results in
 a book update event being emitted.
"""

class DeltaCache:
	"""
	Tracks the last seen state of orderbook levels to calculate 
	the difference (delta) between market updates.
	"""
	def __init__(self):
		# Nested mapping: {instrument_id: {Side.BUY: {price: size}, Side.SELL: {price: size}}}
		self._cache: Dict[str, Dict[Side, Dict[Decimal, Decimal]]] = {}

	def get_last_size(self, instrument_id: str, side: Side, price: Decimal) -> Decimal:
		"""
		Retrieves the last known size for a specific price level.
		Returns 0 if the price level has never been seen or was previously cleared.
		"""
		try:
			return self._cache[instrument_id][side].get(price, Decimal("0"))
		except KeyError:
			# Initialize instrument/side maps if they don't exist
			if instrument_id not in self._cache:
				self._cache[instrument_id] = {Side.BUY: {}, Side.SELL: {}}
			return Decimal("0")

	def update_size(self, instrument_id: str, side: Side, price: Decimal, new_size: Decimal):
		"""
		Updates the cache with the newest size. 
		If the size is 0, it removes the price level to save memory.
		"""
		if instrument_id not in self._cache:
			self._cache[instrument_id] = {Side.BUY: {}, Side.SELL: {}}
			
		if new_size <= 0:
			# Level is exhausted/cancelled; pop it to keep the cache lean
			self._cache[instrument_id][side].pop(price, None)
		else:
			self._cache[instrument_id][side][price] = new_size

	def get_delta(self, instrument_id: str, side: Side, price: Decimal, new_size: Decimal) -> Decimal:
		"""
		Helper method to calculate the delta and update the cache in one go.
		Returns: (New Size - Old Size)
		"""
		old_size = self.get_last_size(instrument_id, side, price)
		delta = new_size - old_size
		self.update_size(instrument_id, side, price, new_size)
		return delta


class PolymarketIml(ImlBase, PolymarketMessageHandler):
	def __init__(self, ws: Optional[IPolymarketWebsocket] = None):
		super().__init__()

		self.ws: IPolymarketWebsocket = ws if ws is not None else PolyMarketWebSocket(self)
		self.delta_cache = DeltaCache()

	def subscribe(self, instrument_id: str, consumer: MarketDataConsumer):
		super().subscribe(instrument_id, consumer)

		self.ws.subscribe_to_market(instrument_id)
	
	def handle_order_book_summary_event(self, event: OrderBookSummaryEvent):
		for bid in event.bids:
			self.delta_cache.update_size(event.token_id, Side.BUY, Decimal(bid.price), Decimal(bid.size))
		for ask in event.asks:
			self.delta_cache.update_size(event.token_id, Side.SELL, Decimal(ask.price), Decimal(ask.size))
		
		self.emit_message(
			order_book_summary_event_to_market_event(
				event
			)
		)

	def handle_price_change_event(self, event: PriceChangeEvent):
		get_delta = self.delta_cache.get_delta
		timestamp_ms = _datetime_to_unix_ms(event.timestamp)

		token_groups: dict[str, list[ImlLevelDelta]] = {}

		for pc in event.price_changes:
			t_id = pc.token_id
			# Convert string side to enum
			side = Side.BUY if pc.side == "BUY" else Side.SELL

			delta = ImlLevelDelta(
				price=Decimal(pc.price),
				size_delta=get_delta(pc.token_id, side, Decimal(pc.price), Decimal(pc.size)),
				side=side,
			)

			if t_id not in token_groups:
				token_groups[t_id] = [delta]
			else:
				token_groups[t_id].append(delta)

		for token_id, deltas in token_groups.items():
			self.emit_message(
				ImlOrderBookUpdateEvent(
					venue=Venue.POLYMARKET,
					instrument_id=token_id,
					timestamp=timestamp_ms,
					deltas=deltas
				)
			)

	def handle_tick_size_change_event(self, event: TickSizeChangeEvent):
		return

	def handle_last_trade_price_event(self, event: LastTradePriceEvent):
		# Convert string side to enum
		side = Side.BUY if event.side == "BUY" else Side.SELL
		
		self.delta_cache.update_size(event.token_id, side, Decimal(event.price), Decimal(event.size))

		self.emit_message(
			ImlTradeEvent(
				venue=Venue.POLYMARKET,
				instrument_id=event.token_id,
				timestamp=_datetime_to_unix_ms(event.timestamp),
				price=Decimal(event.price),
				size=Decimal(event.size),
				side=side,
			)
		)


def _datetime_to_unix_ms(dt) -> int:
	"""Convert datetime to Unix timestamp in milliseconds"""
	if dt is None:
		return 0
	return int(dt.timestamp() * 1000)


def order_book_summary_event_to_market_event(event: OrderBookSummaryEvent) -> ImlOrderBookSnapshotEvent:
	return ImlOrderBookSnapshotEvent(
		venue=Venue.POLYMARKET,
		instrument_id=event.token_id,
		timestamp=_datetime_to_unix_ms(event.timestamp),
		bids=[
			ImlLevel(
				price=Decimal(bid.price),
				size=Decimal(bid.size),
			)
			for bid in event.bids
		],
		asks=[
			ImlLevel(
				price=Decimal(ask.price),
				size=Decimal(ask.size),
			)
			for ask in event.asks
		],
	)
