"""
Strategy Registry - Central registration point for all trading strategies.

This module provides a singleton registry that stores all registered strategies
and their associated metadata. External systems (like the SDK) register strategies
here, and the core trading system queries this registry to discover and 
instantiate strategies at runtime.
"""

from dataclasses import dataclass
from typing import Type

from polybot.strategy.strategy import StrategyBase
from polybot.strategy.config import StrategyConfig
from polybot.limits.limit import Limit


@dataclass(frozen=True)
class RegistrationEntry:
	"""
	Immutable record of a registered strategy.
	
	Contains all information needed by the core system to instantiate
	and configure a strategy instance.
	"""
	name: str
	wrapper_cls: Type[StrategyBase]
	instrument_ids: tuple[str, ...]
	limits: tuple[Limit, ...]

	def to_strategy_config(self, enabled: bool = True) -> StrategyConfig:
		"""Convert this registration entry to a StrategyConfig for the factory."""
		return StrategyConfig(
			name=self.name,
			instrument_ids=list(self.instrument_ids),
			cls=self.wrapper_cls,
			enabled=enabled,
		)


class StrategyRegistry:
	"""
	Singleton registry for all trading strategies.
	
	Strategies register themselves at import time via external registration
	functions (e.g., the SDK's register_strategy()). The core App queries 
	this registry to discover available strategies.
	
	Usage:
		# External system registers a strategy:
		registry = StrategyRegistry.get_instance()
		registry.register(entry)
		
		# Core App discovers strategies:
		for entry in StrategyRegistry.get_instance().get_all():
			strategy = create_strategy(entry.to_strategy_config())
	"""
	
	_instance: "StrategyRegistry | None" = None
	
	def __init__(self):
		self._entries: dict[str, RegistrationEntry] = {}
	
	@classmethod
	def get_instance(cls) -> "StrategyRegistry":
		"""Get the singleton registry instance."""
		if cls._instance is None:
			cls._instance = cls()
		return cls._instance
	
	@classmethod
	def reset(cls) -> None:
		"""Reset the registry. Useful for testing."""
		cls._instance = None
	
	def register(self, entry: RegistrationEntry) -> None:
		"""
		Register a strategy entry.
		
		Raises:
			ValueError: If a strategy with the same name is already registered.
		"""
		if entry.name in self._entries:
			raise ValueError(
				f"Strategy '{entry.name}' is already registered. "
				"Each strategy must have a unique name."
			)
		self._entries[entry.name] = entry
	
	def get_all(self) -> list[RegistrationEntry]:
		"""Get all registered strategies."""
		return list(self._entries.values())
	
	def __len__(self) -> int:
		return len(self._entries)
	
	def __iter__(self):
		return iter(self._entries.values())

