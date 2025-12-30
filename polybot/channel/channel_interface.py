from typing import Protocol

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

    def run_strategies(self, instrument_id: str):
        """
        Runs the strategies for the given instrument
        """
        ...