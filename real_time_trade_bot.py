import json
import talib
import numpy as np
from binance import ThreadedWebsocketManager
import config
from binance.client import Client
import datetime as dt

SYMBOL = input("Enter the SYMBOL like [BTCUSDT]: ").upper()
CURRENCY_NAME = input("Enter the CURRENCY_NAME like [BTC OR BNB OR ETH]: ").upper()
QUANTITY = float(input("Enter BUY Quantity: "))
indicator = int(input("Enter the indicator (1 for EMA, 2 for RSI, 3 for Bollinger Bands): "))
INTERVAL = input("select one of these timeframes format: 1m [1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d,3d,1w,1M]: ")

if CURRENCY_NAME not in SYMBOL:
    print("Currency Name doesn't match with SYMBOL")
    exit()

# Binance API credentials
API_KEY = input("Enter API KEY: ")
API_SECRET = input("Enter API SECRET: ")

client = Client(API_KEY, API_SECRET)

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
    global historical_data, SELL_ORDERS, BUY_ORDERS, buy_price, sell_price, buy_date, sell_date, profit, prev_timestamp
    json_message = msg
    
   # Extract relevant data from the WebSocket message || this area differs in test and prod mode
    candle_data = json_message['k']
    close_price = float(candle_data['c'])
    timestamp = json_message['k']['t']
    date = dt.datetime.fromtimestamp(timestamp / 1000.0)

    
    if timestamp != prev_timestamp:
        # Append the close price to the data array
        historical_data.append(close_price)
        prev_timestamp = timestamp
        print(f"=====================================")
        print(f"Candle  | Timeframe Time: {date}")
        print(f"Close Price : {close_price}")
        print(f"=====================================")

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

                try:
                    # Place a buy order
                    order = client.order_market_buy(symbol=SYMBOL,quantity=QUANTITY)

                    print('Buy order placed:', order)
                    
                    BUY_ORDERS += 1
                    buy_price = order['fills'][0]['price']
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

                except Exception as e:
                    print("[ERROR] occured while placing order, error code and description is given below, copy and google it to know what exactly went wrong")
                    print(e)
                    check = input("Press any key and enter to exit [copy the error code and desc before exiting]: ")
                    exit()
                

            elif signal == 'SELL' and sell_price == 0 and buy_price != 0:
                try:
                    # Get the available balance for TRB
                    balance = client.get_asset_balance(asset=CURRENCY_NAME)
                    available_quantity = float(balance['free'])

                    # Place a market sell order with the available quantity
                    order = client.order_market_sell(
                        symbol=SYMBOL,
                        quantity=available_quantity
                    )

                    print('Sell order placed:', order)
                    
                    SELL_ORDERS += 1
                    sell_price = order['fills'][0]['price']
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

                except Exception as e:
                    print("[ERROR] occured while placing order, error code and description is given below, copy and google it to know what exactly went wrong")
                    print(e)
                    check = input("Press any key and enter to exit [copy the error code and desc before exiting]: ")
                    exit()

# Run the strategy
print("Subscribing to WebSocket stream")
twm = ThreadedWebsocketManager(api_key=API_KEY, api_secret=API_SECRET)
twm.start()
# twm.start_kline_socket(callback=process_message, symbol=SYMBOL)
twm.start_kline_socket(callback=process_message, symbol=SYMBOL, interval=INTERVAL)

while True:
    pass
twm.stop()
check = input("Press any key and enter to exit: ")















"""
MY BUY ORDER
{
    "symbol": "TRBUSDT",
    "orderId": 719457906,
    "orderListId": -1,
    "clientOrderId": "jBQeYUDHuDGxmRWlsmeSID",
    "transactTime": 1697118377654,
    "price": "0.00000000",
    "origQty": "0.13000000",
    "executedQty": "0.13000000",
    "cummulativeQuoteQty": "5.98910000",
    "status": "FILLED",
    "timeInForce": "GTC",
    "type": "MARKET",
    "side": "BUY",
    "workingTime": 1697118377654,
    "fills": [
        {
            "price": "46.07000000",
            "qty": "0.13000000",
            "commission": "0.00002188",
            "commissionAsset": "BNB",
            "tradeId": 33472552
        }
    ],
    "selfTradePreventionMode": "NONE"
}

MY SELL ORDER
{
    "symbol": "TRBUSDT",
    "orderId": 719473119,
    "orderListId": -1,
    "clientOrderId": "aLfyiFMxihEyOmS1c07Hic",
    "transactTime": 1697119485944,
    "price": "0.00000000",
    "origQty": "0.13000000",
    "executedQty": "0.13000000",
    "cummulativeQuoteQty": "6.01380000",
    "status": "FILLED",
    "timeInForce": "GTC",
    "type": "MARKET",
    "side": "SELL",
    "workingTime": 1697119485944,
    "fills": [
        {
            "price": "46.26000000",
            "qty": "0.13000000",
            "commission": "0.00002187",
            "commissionAsset": "BNB",
            "tradeId": 33472883
        }
    ],
    "selfTradePreventionMode": "NONE"
}

"""