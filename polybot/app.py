"""
App - The central orchestrator that owns and composes all trading system components.

The App class is a minimal wrapper that focuses on ownership and composition.
It uses dependency injection via the AppBuilder to allow easy testing with mocks.

Usage:
    # Production
    app = AppBuilder().with_polymarket_credentials(creds).build()
    
    # Testing with mocks
    app = AppBuilder() \
        .with_ids(mock_ids) \
        .with_iml(mock_iml) \
        .build()
"""

from dataclasses import dataclass
from typing import Callable, Optional, Protocol, Type

from polybot.channel import ChannelInterface, Channel
from polybot.common.context_provider import ContextBuilder
from polybot.common.types import OrderRequest
from polybot.eml import ExecLink
from polybot.ids import IInstrumentDefintionStore
from polybot.iml import MarketDataProvider
from polybot.limits import ILimitStore, LimitStore
from polybot.state import IOrderManager, IOrderReader, IPositionReader, OrderManager, PositionManager
from polybot.strategy import create_strategy, StrategyRegistry

# Type alias for order handler callback
OrderHandler = Callable[[OrderRequest], None]


class AppInterface(Protocol):
    """Protocol defining the public interface of the App."""
    
    def initialize(self) -> None:
        """Initialize the application by loading all registered strategies."""
        ...

    def run(self) -> None:
        """Start the trading engine."""
        ...

    def stop(self) -> None:
        """Stop the trading engine gracefully."""
        ...


@dataclass
class AppDependencies:
    """
    Container for all App dependencies.
    
    This dataclass groups all the components that App needs, making it easy
    to pass around and inspect dependencies during testing.
    """
    ids: IInstrumentDefintionStore
    iml: MarketDataProvider
    eml: ExecLink
    limit_store: ILimitStore
    order_manager: IOrderManager
    order_reader: IOrderReader
    position_reader: IPositionReader
    registry: StrategyRegistry


class App(AppInterface):
    """
    Central orchestrator that owns and composes all trading system components.
    
    App is designed to be a minimal wrapper that:
    1. Owns all core components (IDS, IML, EML, state managers)
    2. Composes them together via the Channel
    3. Manages the lifecycle of the trading system
    
    All dependencies are injected via the constructor, making it easy to
    test with mocks. Use AppBuilder for convenient construction.
    """
    
    def __init__(self, deps: AppDependencies):
        """
        Initialize App with all dependencies.
        
        Args:
            deps: Container with all required dependencies
        """
        self._deps = deps
        
        # Build derived components
        self._context_builder = ContextBuilder(
            position_reader=deps.position_reader,
            order_reader=deps.order_reader,
        )
        
        self._channel: ChannelInterface = Channel(
            ids=deps.ids,
            iml=deps.iml,
            eml=deps.eml,
            context_builder=self._context_builder,
        )
    
    @property
    def deps(self) -> AppDependencies:
        """Access to dependencies for testing/inspection."""
        return self._deps
    
    @property
    def channel(self) -> ChannelInterface:
        """Access to the channel for testing/inspection."""
        return self._channel

    def initialize(self) -> None:
        """
        Initialize the application by loading all registered strategies.
        
        This method discovers strategies from the registry, applies their
        limits to the limit store, and creates strategy instances.
        """
        self._load_strategies_from_registry()

    def _load_strategies_from_registry(self) -> None:
        """
        Load all registered strategies from the strategy registry.
        
        For each registered strategy:
        1. Apply its limits to the limit store
        2. Create a strategy instance via the factory
        3. Store the instance for lifecycle management
        """
        for entry in self._deps.registry.get_all():
            # Register limits for each instrument
            for limit in entry.limits:
                self._deps.limit_store.set_limit(limit.instrument_id, limit)
            
            # Create the strategy instance
            config = entry.to_strategy_config(enabled=True)
            strategy = create_strategy(config)

            # Add the strategy to the channel
            self._channel.add_strategy(strategy)

    def run(self) -> None:
        """Start the trading engine."""
        self._channel.run()

    def stop(self) -> None:
        """Stop the trading engine gracefully."""
        self._channel.stop()


class AppBuilder:
    """
    Builder for constructing App instances with dependency injection.
    
    The builder pattern allows:
    1. Sensible defaults for production use
    2. Easy swapping of any component for testing
    3. Clear, fluent API for configuration
    
    Example:
        # Production with all defaults
        app = AppBuilder() \\
            .with_ids(my_ids) \\
            .with_iml(my_iml) \\
            .with_eml(my_eml) \\
            .build()
        
        # Testing with mocks
        app = AppBuilder() \\
            .with_ids(mock_ids) \\
            .with_iml(mock_iml) \\
            .with_eml(mock_eml) \\
            .with_limit_store(mock_limit_store) \\
            .build()
    """
    
    def __init__(self):
        """Initialize builder with no components set."""
        self._ids: Optional[IInstrumentDefintionStore] = None
        self._iml: Optional[MarketDataProvider] = None
        self._eml: Optional[ExecLink] = None
        self._limit_store: Optional[ILimitStore] = None
        self._order_manager: Optional[IOrderManager] = None
        self._position_manager: Optional[PositionManager] = None
        self._registry: Optional[StrategyRegistry] = None
    
    def with_ids(self, ids: IInstrumentDefintionStore) -> "AppBuilder":
        """Set the instrument definition store."""
        self._ids = ids
        return self
    
    def with_iml(self, iml: MarketDataProvider) -> "AppBuilder":
        """Set the market data provider."""
        self._iml = iml
        return self
    
    def with_eml(self, eml: ExecLink) -> "AppBuilder":
        """Set the execution link."""
        self._eml = eml
        return self
    
    def with_limit_store(self, limit_store: ILimitStore) -> "AppBuilder":
        """Set the limit store."""
        self._limit_store = limit_store
        return self
    
    def with_order_manager(self, order_manager: IOrderManager) -> "AppBuilder":
        """Set the order manager (also provides IOrderReader)."""
        self._order_manager = order_manager
        return self
    
    def with_position_manager(self, position_manager: PositionManager) -> "AppBuilder":
        """Set the position manager."""
        self._position_manager = position_manager
        return self
    
    def with_registry(self, registry: StrategyRegistry) -> "AppBuilder":
        """Set the strategy registry."""
        self._registry = registry
        return self
    
    def build(self) -> App:
        """
        Build the App instance with configured or default dependencies.
        
        Returns:
            Configured App instance
            
        Raises:
            ValueError: If required dependencies (ids, iml, eml) are not set
        """
        # Validate required dependencies
        if self._ids is None:
            raise ValueError("IDS (Instrument Definition Store) is required. Use with_ids().")
        if self._iml is None:
            raise ValueError("IML (Market Data Provider) is required. Use with_iml().")
        if self._eml is None:
            raise ValueError("EML (Execution Link) is required. Use with_eml().")
        
        # Use defaults for optional dependencies
        limit_store = self._limit_store or LimitStore()
        order_manager = self._order_manager or OrderManager()
        position_manager = self._position_manager or PositionManager()
        registry = self._registry or StrategyRegistry.get_instance()
        
        deps = AppDependencies(
            ids=self._ids,
            iml=self._iml,
            eml=self._eml,
            limit_store=limit_store,
            order_manager=order_manager,
            order_reader=order_manager,  # OrderManager implements both interfaces
            position_reader=position_manager,
            registry=registry,
        )
        
        return App(deps)


def create_test_app_builder() -> AppBuilder:
    """
    Factory function for creating an AppBuilder pre-configured for testing.
    
    This creates a builder with fresh instances of all state components,
    isolated from the global singleton registry.
    
    Returns:
        AppBuilder with isolated registry and fresh state managers
    """
    return AppBuilder().with_registry(StrategyRegistry())
