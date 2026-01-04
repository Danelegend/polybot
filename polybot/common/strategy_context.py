from dataclasses import dataclass

from polybot.channel.position_manager import IPositionReader
from polybot.common.types import INSTRUMENT_ID
from polybot.common.orderbook import OrderBook
from typing import Mapping

@dataclass
class StrategyContext:
	position_reader: IPositionReader
	orderbooks: Mapping[INSTRUMENT_ID, OrderBook]
