import yaml

from dataclasses import dataclass

"""
A strategy config is a yaml file of the following format:

strategy_name: <strategy_name>    # The name of this instance of the strategy
strategy_type: <strategy_type>    # The type of strategy that should be run
instrument_ids:                   # The instrument ids that this instance should be run for
    - <instrument_id>
    - <instrument_id>
    ...

"""

@dataclass
class StrategyConfig:
    strategy_name: str
    strategy_type: str

    instrument_ids: list[str]

    @staticmethod
    def from_file(file_path: str):
        with open(file_path, "r") as f:
            config = yaml.safe_load(f)
            return StrategyConfig(**config)

