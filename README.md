Goal: Provide a simple platform for developers to make bots. Abstract away the complexity of infrastructure and risk tracking

User's should only care about creating the strategy. 

Design:
User's provide a python file + configuration file. The python file has the Strategy interface implemented.

Polymarket has a websocket.
<->
Websocket outputs to the polymarket information link.
<->
Information Link outputs to the 
<->
