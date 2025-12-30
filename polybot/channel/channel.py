
from .channel_interface import ChannelInterface


class Channel(ChannelInterface):
    def __init__(self):
        ...

    def run(self):
        ...

    def stop(self):
        ...

    def run_strategies(self, instrument_id: str):
        ...
