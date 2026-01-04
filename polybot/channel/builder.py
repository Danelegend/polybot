from typing import Optional

from .channel import Channel, OrderHandler
from .channel_interface import ChannelInterface

from polybot.ids.interface import IInstrumentDefintionStore
from polybot.iml.interface import MarketDataProvider

def build_channel(
	ids: IInstrumentDefintionStore,
	iml: MarketDataProvider,
	order_handler: Optional[OrderHandler] = None,
) -> ChannelInterface:
	return Channel(ids, iml, order_handler)
