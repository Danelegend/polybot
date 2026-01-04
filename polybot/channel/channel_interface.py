from typing import Protocol

from polybot.strategy import StrategyBase

class ChannelInterface(Protocol):
	def run(self):
		"""
		Starts the channel
		"""
		...
	
	def stop(self):
		"""
		Stops the channel
		"""
		...

	def add_strategy(self, strategy: StrategyBase):
		"""
		Adds a strategy to the channel
		"""
		...

	