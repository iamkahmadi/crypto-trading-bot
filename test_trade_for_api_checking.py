
# BUY 
# import my_config as config, csv
# from binance.client import Client
# from binance.enums import *

# client = Client(config.API_KEY, config.API_SECRET)

# try:
#     order = client.order_market_buy(
#     symbol='TRBUSDT',
#     quantity=0.13)
    
#     print('Buy order placed:', order)
# except Exception as e:
#     print(e)


# SELL
import my_config as config
from binance.client import Client
from binance.enums import *

client = Client(config.API_KEY, config.API_SECRET)

try:
    # Get the available balance for TRB
    balance = client.get_asset_balance(asset='TRB')
    available_quantity = float(balance['free'])

    # Place a market sell order with the available quantity
    order = client.order_market_sell(
        symbol='TRBUSDT',
        quantity=available_quantity
    )

    print('Sell order placed:', order)
except Exception as e:
    print(e)
