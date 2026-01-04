from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, AliasChoices, field_serializer
from enum import Enum

from .common import Keccak256, TickSize


class MessageType(Enum):
	BOOK = "book"
	PRICE_CHANGE = "price_change"
	LAST_TRADE_PRICE = "last_trade_price"
	TICK_SIZE_CHANGE = "tick_size_change"


class OrderSummary(BaseModel):
	price: float
	size: float

class PriceChange(BaseModel):
	best_ask: float = Field(validation_alias=AliasChoices("ba", "best_ask"))
	best_bid: float = Field(validation_alias=AliasChoices("bb", "best_bid"))
	price: float = Field(validation_alias=AliasChoices("p", "price"))
	size: float = Field(validation_alias=AliasChoices("s", "size"))
	side: Literal["BUY", "SELL"] = Field(validation_alias=AliasChoices("si", "side"))
	token_id: str = Field(validation_alias=AliasChoices("a", "asset_id"))
	hash: str = Field(validation_alias=AliasChoices("h", "hash"))


class OrderBookSummary(BaseModel):
	condition_id: Optional[Keccak256] = Field(None, alias="market")
	token_id: Optional[str] = Field(None, alias="asset_id")
	timestamp: Optional[datetime] = None
	hash: Optional[str] = None
	bids: list[OrderSummary] = []
	asks: list[OrderSummary] = []

	@field_serializer("bids", "asks")
	def serialize_sizes(self, orders: list[OrderSummary]) -> list[dict]:
		return [
			{
				"price": f"{order.price:.3f}".rstrip("0").rstrip("."),
				"size": f"{order.size:.2f}".rstrip("0").rstrip("."),
			}
			for order in orders
		]

	@field_serializer("timestamp")
	def serialize_timestamp(self, ts: datetime) -> str:
		# Convert to millisecond timestamp string without decimal places
		return str(int(ts.timestamp() * 1000))


class PriceChanges(BaseModel):
	condition_id: Keccak256 = Field(validation_alias=AliasChoices("m", "market"))
	price_changes: list[PriceChange] = Field(
		validation_alias=AliasChoices("pc", "price_changes")
	)
	timestamp: datetime = Field(validation_alias=AliasChoices("t", "timestamp"))


class TickSizeChange(BaseModel):
	token_id: str = Field(alias="asset_id")
	condition_id: Keccak256 = Field(alias="market")
	old_tick_size: TickSize
	new_tick_size: TickSize


class LastTradePrice(BaseModel):
	price: float
	size: float
	side: Literal["BUY", "SELL"]
	token_id: str = Field(alias="asset_id")
	condition_id: Keccak256 = Field(alias="market")
	fee_rate_bps: float

class OrderBookSummaryEvent(OrderBookSummary):
	event_type: Literal["book"]


class PriceChangeEvent(PriceChanges):
	event_type: Literal["price_change"]


class TickSizeChangeEvent(TickSizeChange):
	side: Literal["BUY", "SELL"]
	timestamp: datetime
	event_type: Literal["tick_size_change"]


class LastTradePriceEvent(LastTradePrice):
	timestamp: datetime
	event_type: Literal["last_trade_price"]