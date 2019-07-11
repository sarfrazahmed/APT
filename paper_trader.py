# Import dependencies
import logging
from kiteconnect import KiteTicker
from kiteconnect import KiteConnect
import pandas as pd
import os
import webbrowser
import datetime

# Authentication
api_key= 'qgm5efx193o4wo87'
api_secret='4pp34eb3kvoz0cb8ihygxotnwcljb7g8'
kite = KiteConnect(api_key=api_key)
webbrowser.open_new(kite.login_url())
print(kite.login_url())

request_token='J3PcJkB1WyhVl3vm8JW6g2Pnq37riK5z'
KRT=kite.generate_session(request_token,api_secret)
kite.set_access_token(KRT['access_token'])
print(KRT)

tokens = [897537]

# Initialise
kws = KiteTicker(api_key, KRT['access_token'])

def on_ticks(ws, ticks):
    # Callback to receive ticks.
    print(ticks)

def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens
    ws.subscribe(tokens)

    # Set TITAN to tick in `full` mode.
    ws.set_mode(ws.MODE_LTP , tokens)

# def on_close(ws, code, reason):
#     # On connection close stop the main loop
#     # Reconnection will not happen after executing `ws.stop()`
#     ws.stop()

# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_connect = on_connect
# kws.on_close = on_close

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
kws.connect()