import websocket, pprint, json, numpy as np, pandas as pd, time
import config, RSI
from binance.client import Client
from binance.enums import *

SOCKET = "wss://stream.binance.com:9443/ws/btcusdt@kline_1m"

client = Client(config.API_KEY, config.API_SECRET)

def order(side, quantity, symbol, order_type = ORDER_TYPE_MARKET):
    try:
        print("Sending Order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
        return True, float(order['fills'][0]['price'])
    except Exception as e:
        print(e)
        return False

closes = []
in_position = False

RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
TRADE_SYMBOL = 'BTCUSDT'
TRADE_QUANTITY_BUY = 0.001
TRADE_QUANTITY_SELL = 0.001
PRICE = 0

def on_open(ws):
    print("opened connection")

def on_close(ws):
    print("closed connection")

def on_message(ws, message):
    global closes, in_position, PRICE
    json_message = json.loads(message)

    candle = json_message['k']
    is_candle_closed = candle['x']
    close = candle['c']
    
    if is_candle_closed:
        print("{} closed at {}".format(TRADE_SYMBOL, close))
        closes.append(float(close))
        #print(closes)

        if len(closes) > RSI_PERIOD:
            np_closes = np.array(closes)
            rsi = RSI.RSI(np_closes, RSI_PERIOD)
            # print("All RSI's calculated so far...")
            # print(rsi)
            last_rsi = rsi[-1]
            print("Current RSI is {}".format(last_rsi))

            if last_rsi > RSI_OVERBOUGHT:
                if rsi[-2] > rsi[-1] or last_rsi > 80:
                    if in_position and (np_closes[-1] > PRICE):
                        print("Sell! Sell! Sell!")
                        order_succeeded = order(SIDE_SELL, TRADE_QUANTITY_SELL, TRADE_SYMBOL)
                        if order_succeeded[0]:
                            in_position = False
                            PRICE = 0
                    else:
                        print("Overbought!!")

            if last_rsi < RSI_OVERSOLD:
                if rsi[-2] < rsi[-1] or last_rsi < 20:
                    if in_position:
                        print("Oversold")
                    else:
                        print("Buy! Buy! Buy!")
                        order_succeeded = order(SIDE_BUY, TRADE_QUANTITY_BUY, TRADE_SYMBOL)
                        if order_succeeded[0]:
                            in_position = True
                            PRICE = order_succeeded[1]

            print()

ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()