import json

from typing import Protocol

from polybot.connection.ws_connection_base import ConnectionBase

from .interfaces import PolymarketMessageHandler
from .types.messages import (
	MessageType,
	OrderBookSummaryEvent,
	PriceChangeEvent,
	TickSizeChangeEvent,
	LastTradePriceEvent,
)

import logging
import traceback

logger = logging.getLogger(__name__)

POLYMARKET_SOCKET_URL = "wss://ws-subscriptions-clob.polymarket.com"
MARKET_CHANNEL = "market"


def build_market_url() -> str:
	return POLYMARKET_SOCKET_URL + "/ws/" + MARKET_CHANNEL


def _process_market_event(handler: PolymarketMessageHandler, msg: dict):
	match msg["event_type"]:
		case MessageType.BOOK.value:
			handler.handle_order_book_summary_event(
				OrderBookSummaryEvent(**msg)
			)
		case MessageType.PRICE_CHANGE.value:
			handler.handle_price_change_event(
				PriceChangeEvent(**msg)
			)
		case MessageType.TICK_SIZE_CHANGE.value:
			handler.handle_tick_size_change_event(
				TickSizeChangeEvent(**msg)
			)
		case MessageType.LAST_TRADE_PRICE.value:
			handler.handle_last_trade_price_event(
				LastTradePriceEvent(**msg)
			)
		case _:
			raise ValueError("Invalid event type")


def _process_market_events(handler: PolymarketMessageHandler, msg: dict | list):
	if isinstance(msg, list):
		for item in msg:
			_process_market_event(handler, item)
	else:
		_process_market_event(handler, msg)	


class IPolymarketWebsocket(Protocol):
	def subscribe_to_market(self, token_id: str):
		...


class PolyMarketWebSocket(ConnectionBase, IPolymarketWebsocket):
	def __init__(self, handler: PolymarketMessageHandler):
		super().__init__(build_market_url())

		self.handler = handler
		self.subscribed_markets: set[str] = set()

	def subscribe_to_market(self, token_id: str):
		if token_id in self.subscribed_markets:
			return

		self.subscribed_markets.add(token_id)

	def on_message(self, ws, message):
		try:
			_process_market_events(
				self.handler,
				json.loads(message),
			)
		except Exception:
			logger.error(traceback.format_exc())

	def on_error(self, ws, error):
		logger.error(f"Websocket error -> {str(error)}")
		return

	def on_close(self, ws, close_status_code, close_msg):
		logger.info("WebSocket closed")
		return

	def on_open(self, ws):
		data = {
			"assets_ids": [str(x) for x in self.subscribed_markets],
			"type": MARKET_CHANNEL,
		}
		logger.info(f"Subscribing to markets: {data}")
		self.send_message(data)
