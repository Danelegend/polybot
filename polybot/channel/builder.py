"""
Channel Builder - Factory for constructing Channel instances.

The builder provides a clean interface for creating Channel instances
with all required dependencies injected.
"""

from typing import Optional

from .channel import Channel
from .channel_interface import ChannelInterface

from polybot.common.context_provider import ContextBuilder
from polybot.eml import ExecLink
from polybot.ids.interface import IInstrumentDefintionStore
from polybot.iml.interface import MarketDataProvider


class ChannelBuilder:
    """
    Builder for constructing Channel instances with dependency injection.
    
    Example:
        channel = ChannelBuilder() \\
            .with_ids(ids) \\
            .with_iml(iml) \\
            .with_eml(eml) \\
            .with_context_builder(context_builder) \\
            .build()
    """
    
    def __init__(self):
        self._ids: Optional[IInstrumentDefintionStore] = None
        self._iml: Optional[MarketDataProvider] = None
        self._eml: Optional[ExecLink] = None
        self._context_builder: Optional[ContextBuilder] = None
    
    def with_ids(self, ids: IInstrumentDefintionStore) -> "ChannelBuilder":
        """Set the instrument definition store."""
        self._ids = ids
        return self
    
    def with_iml(self, iml: MarketDataProvider) -> "ChannelBuilder":
        """Set the market data provider."""
        self._iml = iml
        return self
    
    def with_eml(self, eml: ExecLink) -> "ChannelBuilder":
        """Set the execution link."""
        self._eml = eml
        return self
    
    def with_context_builder(self, context_builder: ContextBuilder) -> "ChannelBuilder":
        """Set the context builder."""
        self._context_builder = context_builder
        return self
    
    def build(self) -> ChannelInterface:
        """
        Build the Channel instance.
        
        Returns:
            Configured Channel instance
            
        Raises:
            ValueError: If required dependencies are not set
        """
        if self._ids is None:
            raise ValueError("IDS is required. Use with_ids().")
        if self._iml is None:
            raise ValueError("IML is required. Use with_iml().")
        if self._eml is None:
            raise ValueError("EML is required. Use with_eml().")
        if self._context_builder is None:
            raise ValueError("ContextBuilder is required. Use with_context_builder().")
        
        return Channel(
            ids=self._ids,
            iml=self._iml,
            eml=self._eml,
            context_builder=self._context_builder,
        )


def build_channel(
    ids: IInstrumentDefintionStore,
    iml: MarketDataProvider,
    eml: ExecLink,
    context_builder: ContextBuilder,
) -> ChannelInterface:
    """
    Factory function for building a Channel with all dependencies.
    
    This is a convenience function that wraps ChannelBuilder for
    simple use cases where all dependencies are known upfront.
    
    Args:
        ids: Instrument definition store
        iml: Market data provider
        eml: Execution link
        context_builder: Context builder for strategy execution
    
    Returns:
        Configured Channel instance
    """
    return ChannelBuilder() \
        .with_ids(ids) \
        .with_iml(iml) \
        .with_eml(eml) \
        .with_context_builder(context_builder) \
        .build()
