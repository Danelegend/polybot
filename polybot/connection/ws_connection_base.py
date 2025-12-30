import json
import threading
import time

from abc import ABC, abstractmethod
from enum import Enum
from websocket import WebSocketApp

import traceback

class ConnectionState(Enum):
    INITIALIZED = 1
    CONNECTING = 2
    CONNECTED = 3
    DISCONNECTED = 4
    STOPPING = 5

class ConnectionBase(ABC):
    def __init__(self, connection_link: str):
        self.ws = WebSocketApp(
            connection_link,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )

        self.connection_state = ConnectionState.INITIALIZED
        self.num_messages_received = 0

    def _on_message(self, ws, message):
        if message == "PONG":
            return
        
        self.num_messages_received += 1
        
        try:
            self.on_message(ws, message)
        except Exception as e:
            print("Error in on_message: ", e, " message=", message)
            traceback.print_exc()
            raise e

    def _on_error(self, ws, error):
        self.on_error(ws, error)

    def _on_close(self, ws, close_status_code, close_msg):
        self.on_close(ws, close_status_code, close_msg)
        self.connection_state = ConnectionState.DISCONNECTED

    def _on_open(self, ws):
        self.connection_state = ConnectionState.CONNECTED
        self.on_open(ws)
        
        threading.Thread(target=_ping, args=(ws,)).start()

    @abstractmethod
    def on_message(self, ws, message):
        ...

    @abstractmethod
    def on_error(self, ws, error):
        ...

    @abstractmethod
    def on_close(self, ws, close_status_code, close_msg):
        ...

    @abstractmethod
    def on_open(self, ws):
        ...

    def send_message(self, message: dict):
        self.ws.send(json.dumps(message))

    def stop(self):
        self.connection_state = ConnectionState.STOPPING
        self.ws.close()

    def run(self):
        if self.connection_state not in [
            ConnectionState.INITIALIZED,
            ConnectionState.DISCONNECTED,
        ]:
            raise Exception("Connection not in a valid state to run")

        self.connection_state = ConnectionState.CONNECTING
        self.ws.run_forever()


def _ping(ws):
    while True:
        ws.send("PING")
        time.sleep(10)