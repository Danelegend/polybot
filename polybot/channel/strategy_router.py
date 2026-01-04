from polybot.common.types import INSTRUMENT_ID
from polybot.strategy import StrategyInterface
from polybot.channel.strategy_view import StrategyView
from collections import defaultdict
from typing import Generator

"""
StrategyRouter is responsible for:
 - Add a strategy and the instruments it cares about
 - For a given instrument, return all strategies that care about it
"""

class StrategyRouter:
	def __init__(self):
		self.strategy_views: list[StrategyView] = []
		self.strategies: dict[INSTRUMENT_ID, list[int]] = defaultdict(list)

	def add_strategy(self, strategy: StrategyInterface) -> StrategyView:
		strategy_view = StrategyView(strategy)
		self.strategy_views.append(strategy_view)
		strategy_id = len(self.strategy_views) - 1
		for iid in strategy.get_metadata().instruments:
			self.strategies[iid].append(strategy_id)
		return strategy_view

	def get_strategies(self, iid: INSTRUMENT_ID) -> list[StrategyView]:
		return [self.strategy_views[strategy_id] for strategy_id in self.strategies[iid]]

	def get_strategies_to_run(self, iid: INSTRUMENT_ID) -> Generator[StrategyView, None, None]:
		for strategy_id in self.strategies[iid]:
			yield self.strategy_views[strategy_id]