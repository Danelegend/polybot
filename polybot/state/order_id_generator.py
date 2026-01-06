from polybot.common.types import ORDER_ID

order_id_generator: ORDER_ID = 0

def generate_order_id() -> ORDER_ID:
	"""
	Internal to the system. This order id does not persist across restarts.
	It just has to be unique across the lifetime of the program.
	"""
	global order_id_generator
	order_id_generator += 1
	return order_id_generator
