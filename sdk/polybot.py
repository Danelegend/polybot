"""
Polybot SDK - User-facing entry point for the trading framework.

Each Polybot instance corresponds to exactly one App instance. The Polybot class
provides a user-friendly API for registering strategies and managing the trading
engine, while the App handles the internal orchestration.

Usage:
    # Production
    polybot = PolybotBuilder() \\
        .with_credentials(credentials) \\
        .build()
    polybot.register_strategy(MyStrategy, ["0x123"], [limits])
    polybot.start()
    
    # Testing with mocks
    polybot = PolybotBuilder() \\
        .with_app(mock_app) \\
        .with_registry(mock_registry) \\
        .build()
"""

from typing import Type, Optional

from sdk.credentials import Credentials
from sdk.base_strategy import Strategy
from sdk.types import InstrumentLimit
from sdk.internal.strategy_wrapper import StrategyWrapper
from sdk.internal.registry import convert_sdk_limit_to_core_limit

# Import from core
from polybot.app import App, AppBuilder, AppInterface, AppDependencies
from polybot.eml import ExecLink
from polybot.ids import IInstrumentDefintionStore, InstrumentDefinitionStore
from polybot.iml import MarketDataProvider
from polybot.limits import LimitStore
from polybot.polymarket import PolymarketIml
from polybot.strategy import StrategyRegistry, RegistrationEntry


class Polybot:
    """
    Main entry point for the Polybot SDK.
    
    Each Polybot instance corresponds to exactly one App instance. Users create 
    a Polybot with credentials, register strategies, and then start the trading 
    engine.
    
    For testing, use PolybotBuilder to inject mock dependencies.
    
    Example:
        polybot = Polybot(credentials)
        polybot.register_strategy(MyStrategy, ["0x123..."], [limits])
        polybot.start()
    """
    
    def __init__(
        self,
        app: AppInterface,
        registry: StrategyRegistry,
        credentials: Optional[Credentials] = None,
    ):
        """
        Initialize Polybot with injected dependencies.
        
        Args:
            app: The core App instance (1:1 relationship)
            registry: Strategy registry for this Polybot instance
            credentials: Optional trading credentials
        """
        self._app = app
        self._registry = registry
        self._credentials = credentials
    
    @property
    def app(self) -> AppInterface:
        """Access to the underlying App for testing/inspection."""
        return self._app
    
    @property
    def registry(self) -> StrategyRegistry:
        """Access to the strategy registry for testing/inspection."""
        return self._registry
    
    @property
    def credentials(self) -> Optional[Credentials]:
        """Access to credentials."""
        return self._credentials
    
    def register_strategy(
        self,
        strat_class: Type[Strategy],
        instrument_ids: list[str],
        limits: list[InstrumentLimit],
        name: str = "",
    ) -> RegistrationEntry:
        """
        Register a strategy class with this Polybot instance.
        
        Args:
            strat_class: The strategy class to register. Must inherit from Strategy.
            instrument_ids: List of instrument IDs this strategy will trade.
            limits: List of position limits for each instrument.
            name: Optional name for this strategy. Defaults to the class name.
        
        Returns:
            The RegistrationEntry that was created and registered.
        
        Raises:
            ValueError: If a strategy with the same name is already registered.
            ValueError: If instrument_ids is empty.
            ValueError: If limits don't cover all instrument_ids.
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
        wrapper_cls = self._create_wrapper_class(strat_class, strategy_name)
        
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
        
        # Register with the registry
        self._registry.register(entry)
        
        return entry
    
    def _create_wrapper_class(
        self,
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
    
    def start(self) -> None:
        """
        Initialize and start the trading engine.
        
        This will:
        1. Load all registered strategies
        2. Apply their limits
        3. Start the trading engine
        """
        self._app.initialize()
        self._app.run()
    
    def stop(self) -> None:
        """Stop the trading engine gracefully."""
        self._app.stop()


class PolybotBuilder:
    """
    Builder for constructing Polybot instances with dependency injection.
    
    The builder pattern allows:
    1. Easy production setup with just credentials
    2. Full control over dependencies for testing
    3. Clear, fluent API for configuration
    
    Example:
        # Production - uses real implementations
        polybot = PolybotBuilder() \\
            .with_credentials(credentials) \\
            .build()
        
        # Testing - inject mocks at any level
        polybot = PolybotBuilder() \\
            .with_app(mock_app) \\
            .build()
        
        # Testing - inject specific components into App
        polybot = PolybotBuilder() \\
            .with_ids(mock_ids) \\
            .with_iml(mock_iml) \\
            .with_eml(mock_eml) \\
            .build()
    """
    
    def __init__(self):
        """Initialize builder with no components set."""
        self._credentials: Optional[Credentials] = None
        self._app: Optional[AppInterface] = None
        self._registry: Optional[StrategyRegistry] = None
        
        # Components for building App (if app not provided directly)
        self._ids: Optional[IInstrumentDefintionStore] = None
        self._iml: Optional[MarketDataProvider] = None
        self._eml: Optional[ExecLink] = None
    
    def with_credentials(self, credentials: Credentials) -> "PolybotBuilder":
        """Set trading credentials."""
        self._credentials = credentials
        return self
    
    def with_app(self, app: AppInterface) -> "PolybotBuilder":
        """
        Set a pre-built App instance.
        
        Use this for testing when you want full control over the App.
        """
        self._app = app
        return self
    
    def with_registry(self, registry: StrategyRegistry) -> "PolybotBuilder":
        """
        Set a custom strategy registry.
        
        Use this for testing to isolate strategy registrations.
        """
        self._registry = registry
        return self
    
    def with_ids(self, ids: IInstrumentDefintionStore) -> "PolybotBuilder":
        """Set the instrument definition store (used when building App)."""
        self._ids = ids
        return self
    
    def with_iml(self, iml: MarketDataProvider) -> "PolybotBuilder":
        """Set the market data provider (used when building App)."""
        self._iml = iml
        return self
    
    def with_eml(self, eml: ExecLink) -> "PolybotBuilder":
        """Set the execution link (used when building App)."""
        self._eml = eml
        return self
    
    def _build_default_components(self) -> tuple[IInstrumentDefintionStore, MarketDataProvider, ExecLink]:
        """
        Build default components for production use.
        
        This creates real implementations when specific mocks aren't provided.
        """
        ids = self._ids or InstrumentDefinitionStore()
        iml = self._iml or PolymarketIml()
        
        # EML requires credentials - for now use a placeholder
        # In production, this would be built from credentials
        if self._eml is None:
            raise ValueError(
                "EML (Execution Link) is required. Either provide an App via with_app(), "
                "or provide an EML via with_eml()."
            )
        
        return ids, iml, self._eml
    
    def build(self) -> Polybot:
        """
        Build the Polybot instance with configured or default dependencies.
        
        Returns:
            Configured Polybot instance
            
        Raises:
            ValueError: If required dependencies cannot be resolved
        """
        # Use provided registry or create a new isolated one
        registry = self._registry or StrategyRegistry()
        
        # Build or use provided App
        if self._app is not None:
            app = self._app
        else:
            ids, iml, eml = self._build_default_components()
            
            app = AppBuilder() \
                .with_ids(ids) \
                .with_iml(iml) \
                .with_eml(eml) \
                .with_registry(registry) \
                .build()
        
        return Polybot(
            app=app,
            registry=registry,
            credentials=self._credentials,
        )


def create_polybot(credentials: Credentials, eml: ExecLink) -> Polybot:
    """
    Factory function for creating a production Polybot instance.
    
    This is the simplest way to create a fully configured Polybot
    for production use.
    
    Args:
        credentials: Trading credentials
        eml: Execution link for sending orders
    
    Returns:
        Configured Polybot ready for strategy registration
    """
    return PolybotBuilder() \
        .with_credentials(credentials) \
        .with_eml(eml) \
        .build()


def create_test_polybot(
    ids: Optional[IInstrumentDefintionStore] = None,
    iml: Optional[MarketDataProvider] = None,
    eml: Optional[ExecLink] = None,
) -> Polybot:
    """
    Factory function for creating a test Polybot instance with mock-friendly defaults.
    
    This creates a Polybot with an isolated registry and allows injecting
    mock components at any level.
    
    Args:
        ids: Optional mock instrument definition store
        iml: Optional mock market data provider  
        eml: Optional mock execution link (required if not providing app)
    
    Returns:
        Polybot configured for testing
        
    Raises:
        ValueError: If eml is not provided
    """
    builder = PolybotBuilder()
    
    if ids is not None:
        builder.with_ids(ids)
    if iml is not None:
        builder.with_iml(iml)
    if eml is not None:
        builder.with_eml(eml)
    
    return builder.build()
