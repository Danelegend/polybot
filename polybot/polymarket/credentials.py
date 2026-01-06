from pydantic import BaseModel

from py_clob_client import ClobClient

class PolymarketCredentials(BaseModel):
	wallet_private_key: str
	wallet_address: str


def to_clob_client(credentials: PolymarketCredentials) -> ClobClient:
	host = "https://clob.polymarket.com"
	chain_id = 137
	private_key = credentials.wallet_private_key
	funder = credentials.wallet_address

	return ClobClient(
		host=host,
		chain_id=chain_id,
		private_key=private_key,
		funder=funder,
	)

