import talib
import config
from binance.client import Client
import pandas as pd
import numpy as np
import datetime as dt
import json, requests

print("============== Loaded Libs =============")

URL = 'https://api.binance.com/api/v3/klines'

intervals_to_secs = {
    '1m':60,
    '3m':180,
    '5m':300,
    '15m':900,
    '30m':1800,
    '1h':3600,
    '2h':7200,
    '4h':14400,
    '6h':21600,
    '8h':28800,
    '12h':43200,
    '1d':86400,
    '3d':259200,
    '1w':604800,
    '1M':2592000
}

SYMBOL = input("Enter the SYMBOL like [BTCUSDT]: ").upper()
indicator = int(input("Enter the indicator (1 for EMA, 2 for RSI, 3 for Bollinger Bands): "))
INTERVAL = input("select one of these timeframes format: 1m [1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d,3d,1w,1M]: ")


# Backtest start/end date
start_input = input("Enter the start date (YYYY-MM-DD): ")
end_input = input("Enter the end date (YYYY-MM-DD) or 'now' for current time: ")

if end_input.lower() == 'now':
    END = dt.datetime.now()
else:
    END = dt.datetime.strptime(end_input, "%Y-%m-%d")

START = dt.datetime.strptime(start_input, "%Y-%m-%d")

# Binance API credentials
API_KEY = input("Enter API KEY: ")
API_SECRET = input("Enter API SECRET: ")

client = Client(config.API_KEY, config.API_SECRET)


######################################################### below code keeps changing #################################

current_time = dt.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
file_name = f"{current_time}-orders.txt"
ORDERS_FILE = open(file_name,'a')
indicator_names = ["", "EMA", "RSI", "Bollinger Bands"]
txtt = f"""
COIN: {SYMBOL}
INDICATOR: {indicator_names[indicator]}
START TIME: {current_time}
"""
ORDERS_FILE.write(txtt)


# Define the parameters for the indicators
ema_fast_period = 12
ema_slow_period = 26
rsi_period = 14
bbands_period = 20
bbands_std_dev = 2


# Initialize the historical data array
historical_data = []

# Initialize variables for tracking buy and sell prices and dates
buy_price = 0
sell_price = 0
buy_date = None
sell_date = None
profit = 0
prev_timestamp = 1
SELL_ORDERS = 0
BUY_ORDERS = 0

# Calculate EMA
def calculate_ema(data, period):
    close_prices = np.array(data)
    ema = talib.EMA(close_prices, timeperiod=period)
    return ema

# Calculate RSI
def calculate_rsi(data, period):
    close_prices = np.array(data)
    rsi = talib.RSI(close_prices, timeperiod=period)
    return rsi

# Calculate Bollinger Bands
def calculate_bbands(data, period, std_dev):
    close_prices = np.array(data)
    upper_band, middle_band, lower_band = talib.BBANDS(close_prices, 
                                                      timeperiod=period, 
                                                      nbdevup=std_dev, 
                                                      nbdevdn=std_dev)
    return upper_band, middle_band, lower_band


# Define the trading bot logic
def trading_bot(data, risk_level):
    if risk_level == 1:
        ema_fast = calculate_ema(data, ema_fast_period)
        ema_slow = calculate_ema(data, ema_slow_period)
        last_ema_fast = ema_fast[-1]
        last_ema_slow = ema_slow[-1]
        
        if last_ema_fast > last_ema_slow:
            return 'BUY'
        elif last_ema_fast < last_ema_slow:
            return 'SELL'
        else:
            return 'HOLD'
        
    elif risk_level == 2:
        rsi = calculate_rsi(data, rsi_period)
        last_rsi = rsi[-1]
        
        if last_rsi < 70:
            return 'BUY'
        elif last_rsi > 30:
            return 'SELL'
        else:
            return 'HOLD'

    elif risk_level == 3:
        upper_band, middle_band, lower_band = calculate_bbands(data, bbands_period, bbands_std_dev)
        last_close_price = data[-1]
        
        if last_close_price > upper_band[-1]:
            return 'SELL'
        elif last_close_price < lower_band[-1]:
            return 'BUY'
        else:
            return 'HOLD'
        
    else:
        return 'INVALID PARAMETER'

# Define the WebSocket callback function
def process_message(msg):
    global historical_data, SELL_ORDERS, BUY_ORDERS, buy_price, sell_price, buy_date, sell_date, profit
    json_message = msg
    
    # Extract relevant data from the WebSocket message
    close_price = float(json_message['close'])
    timestamp = json_message['time']
    date = dt.datetime.fromtimestamp(timestamp / 1000.0)
    
    # Append the close price to the data array
    historical_data.append(close_price)

    if indicator == 1:
        data_for_indicators = np.array(historical_data[-ema_slow_period:])
    if indicator == 2:
        data_for_indicators = np.array(historical_data[-rsi_period:])
    if indicator == 3:
        data_for_indicators = np.array(historical_data[-bbands_period:])


    if (indicator == 1 and len(historical_data) > ema_slow_period) or (indicator == 2 and len(historical_data) > rsi_period) or (indicator == 3 and len(historical_data) > bbands_period):

        signal = None

        if indicator == 1:
            signal = trading_bot(data_for_indicators, 1)
        if indicator == 2:
            signal = trading_bot(data_for_indicators, 2)
        if indicator == 3:
            signal = trading_bot(data_for_indicators, 3)
        
        print(f"========== : Indicator: [{indicator_names[indicator]}] : ==========")
        print(f"========== : Signal: [{signal}] : =========")

        if signal == 'BUY' and buy_price == 0:
            BUY_ORDERS += 1
            buy_price = close_price
            buy_date = date
            txt = f"""
============================================
BUY_ORDERS: {BUY_ORDERS}
Buy Price: {buy_price}
Buy Date: {buy_date}
============================================
            """
            print(txt)
            ORDERS_FILE.write(txt)
        elif signal == 'SELL' and sell_price == 0 and buy_price != 0:
            SELL_ORDERS += 1
            sell_price = close_price
            sell_date = date
            profit += sell_price - buy_price
            txt = f"""
============================================
SELL_ORDERS: {SELL_ORDERS}
Sell Price: {sell_price}
Sell Date: {sell_date}
Profit: {profit}
============================================
            """
            print(txt)
            ORDERS_FILE.write(txt)
            # Reset buy and sell prices and dates
            buy_price = 0
            sell_price = 0
            buy_date = None
            sell_date = None


def download_kline_data(start: dt.datetime, end: dt.datetime, symbol: str, interval: str) -> pd.DataFrame:
    start = int(start.timestamp() * 1000)
    end = int(end.timestamp() * 1000)
    full_data = pd.DataFrame()

    while start < end:
        par = {
            'symbol': symbol,
            'interval': interval,
            'startTime': str(start),
            'endTime': str(end),
            'limit': 1000
        }
        data = pd.DataFrame(json.loads(requests.get(URL, params=par).text))


        # data.index = [dt.datetime.fromtimestamp(x / 1000.0) for x in data.iloc[:, 0]]
        data = data.astype(float)
        full_data = pd.concat([full_data, data])

        start += intervals_to_secs[interval] * 1000 * 1000

    full_data.columns = ["time","open","high","low","close","volume","close_time","quote_asset_volume","number_of_trades","taker_buy_base_asset_volume","taker_buy_quote_asset_volume","ignore"]

    # Keep only the desired columns
    full_data = full_data[["time","open","high","low","close","volume","close_time"]]

    return full_data

pd_data = download_kline_data(START, END, SYMBOL, INTERVAL)

for index, row in pd_data.iterrows():
    msg = {
        'symbol': SYMBOL,
        'interval': INTERVAL,
        'time': row['time'],
        'open': row['open'],
        'high': row['high'],
        'low': row['low'],
        'close': row['close'],
        'volume': row['volume'],
        'close_time': row['close_time']
    }
    process_message(msg)


ORDERS_FILE.close()

check = input("Press any key and enter to exit: ")