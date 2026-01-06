from pydantic import BaseModel

class Credentials(BaseModel):
	...


class PolymarketCredentials(Credentials):
	wallet_private_key: str
	wallet_address: str



