import os
from typing import Callable, Optional, Protocol

from polybot.ids import IInstrumentDefintionStore
from polybot.iml import MarketDataProvider
from polybot.limits import ILimitStore
from polybot.channel import build_channel
from polybot.common.types import Order

from polybot.strategy import create_strategy, StrategyRegistry

# Type alias for order handler callback
OrderHandler = Callable[[Order], None]


class AppInterface(Protocol):
    def initialize(self):
        ...

    def run(self):
        ...

    def stop(self):
        ...


class App(AppInterface):
    def __init__(
        self,
        ids: IInstrumentDefintionStore,
        iml: MarketDataProvider,
        limit_store: ILimitStore,
        order_handler: Optional[OrderHandler] = None,
    ):
        self._ids = ids
        self._iml = iml
        self._limit_store = limit_store

        self._channel = build_channel(self._ids, self._iml, order_handler)

    def initialize(self):
        """
        Initialize the application by loading all registered strategies.
        
        This method discovers strategies from the registry, applies their
        limits to the limit store, and creates strategy instances.
        """
        self._load_strategies_from_registry()

    def _load_strategies_from_registry(self):
        """
        Load all registered strategies from the strategy registry.
        
        For each registered strategy:
        1. Apply its limits to the limit store
        2. Create a strategy instance via the factory
        3. Store the instance for lifecycle management
        """
        registry = StrategyRegistry.get_instance()
        
        for entry in registry.get_all():
            # Register limits for each instrument
            for limit in entry.limits:
                self._limit_store.set_limit(limit.instrument_id, limit)
            
            # Create the strategy instance
            config = entry.to_strategy_config(enabled=True)
            strategy = create_strategy(config)

            # Add the strategy to the channel
            self._channel.add_strategy(strategy)

    def run(self):
        self._channel.run()

    def stop(self):
        self._channel.stop()


def build_app(
	ids: IInstrumentDefintionStore,
	iml: MarketDataProvider,
	limit_store: ILimitStore,
	order_handler: Optional[OrderHandler] = None,
) -> AppInterface:
	return App(ids, iml, limit_store, order_handler)
