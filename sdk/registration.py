"""
Strategy Registration API

This module provides the public API for registering strategies with the
core trading system. Strategies call register_strategy() at import time
to make themselves available to the trading engine.

Example:
	from sdk import Strategy, register_strategy, InstrumentLimit, Side
	
	class MyStrategy(Strategy):
		def on_trade(self):
			return []
		
		def on_order_book_change(self):
			return []
	
	register_strategy(
		strat_class=MyStrategy,
		instrument_ids=["0x1234..."],
		limits=[
			InstrumentLimit(
				instrument_id="0x1234...",
				max_position_bid=100,
				max_position_ask=100,
				max_nominal_position_bid=10000,
				max_nominal_position_ask=10000,
			)
		],
		name="my_strategy",
	)
"""

from typing import Optional, Type

from .base_strategy import Strategy
from .types import InstrumentLimit
from .internal.strategy_wrapper import StrategyWrapper
from .internal.registry import convert_sdk_limit_to_core_limit

# Import from core - SDK depends on core, not the other way around
from polybot.strategy import StrategyRegistry, RegistrationEntry


def register_strategy(
	strat_class: Type[Strategy],
	instrument_ids: list[str],
	limits: list[InstrumentLimit],
	name: str = "",
	registry: Optional[StrategyRegistry] = None,
) -> RegistrationEntry:
	"""
	Register a strategy class with the core trading system.
	
	This function should be called at module level (import time) to register
	your strategy. The core system will discover all registered strategies
	and instantiate them based on configuration.
	
	Args:
		strat_class: The strategy class to register. Must inherit from Strategy.
		instrument_ids: List of instrument IDs this strategy will trade.
		limits: List of position limits for each instrument.
		name: Optional name for this strategy. Defaults to the class name.
		registry: Optional registry instance. Defaults to the global singleton.
			Use a custom registry for testing to isolate strategy registrations.
	
	Returns:
		The RegistrationEntry that was created and registered.
	
	Raises:
		ValueError: If a strategy with the same name is already registered.
		ValueError: If instrument_ids is empty.
		ValueError: If limits don't cover all instrument_ids.
	
	Example:
		# Production - uses global registry
		register_strategy(
			strat_class=MyStrategy,
			instrument_ids=["0x1234..."],
			limits=[InstrumentLimit(...)],
			name="my_strategy",
		)
		
		# Testing - uses isolated registry
		test_registry = StrategyRegistry()
		register_strategy(
			strat_class=MyStrategy,
			instrument_ids=["0x1234..."],
			limits=[InstrumentLimit(...)],
			name="my_strategy",
			registry=test_registry,
		)
	"""
	# Validate inputs
	if not instrument_ids:
		raise ValueError("instrument_ids cannot be empty")
	
	# Validate that all instruments have limits defined
	limit_instrument_ids = {limit.instrument_id for limit in limits}
	missing_limits = set(instrument_ids) - limit_instrument_ids
	if missing_limits:
		raise ValueError(
			f"Missing limits for instruments: {missing_limits}. "
			"Each instrument_id must have a corresponding limit."
		)
	
	# Use class name as default strategy name
	strategy_name = name or strat_class.__name__
	
	# Create the wrapper class that adapts SDK strategy to core interface
	wrapper_cls = _create_wrapper_class(strat_class, strategy_name)
	
	# Convert SDK limits to core limits
	core_limits = tuple(
		convert_sdk_limit_to_core_limit(limit)
		for limit in limits
	)
	
	# Create the registration entry
	entry = RegistrationEntry(
		name=strategy_name,
		wrapper_cls=wrapper_cls,
		instrument_ids=tuple(instrument_ids),
		limits=core_limits,
	)
	
	# Register with the provided registry or the global singleton
	target_registry = registry or StrategyRegistry.get_instance()
	target_registry.register(entry)
	
	return entry


def _create_wrapper_class(
	strat_class: Type[Strategy],
	name: str
) -> Type[StrategyWrapper]:
	"""
	Create a wrapper class for the given strategy.
	
	We create a new class for each registration to maintain proper
	class identity and allow for strategy-specific customization.
	"""
	# Create a new wrapper class bound to this specific strategy class
	class BoundStrategyWrapper(StrategyWrapper):
		_bound_strategy_class = strat_class
		
		def __init__(self):
			super().__init__(self._bound_strategy_class)
	
	# Give it a meaningful name for debugging
	BoundStrategyWrapper.__name__ = f"{name}Wrapper"
	BoundStrategyWrapper.__qualname__ = f"{name}Wrapper"
	
	return BoundStrategyWrapper
