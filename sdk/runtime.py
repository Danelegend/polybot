from polybot.app_context import get_app_instance

def start():
	app = get_app_instance()
	app.initialize()
	app.run()
