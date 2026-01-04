_app = None

def get_app_instance():
	global _app
	if _app is None:
		from .app import build_app
		from polybot.ids import InstrumentDefinitionStore
		from polybot.polymarket import PolymarketIml
		from polybot.limits import LimitStore
		_app = build_app(InstrumentDefinitionStore(), PolymarketIml(), LimitStore())
	return _app
