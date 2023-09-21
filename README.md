# Crypto Trading Bot

This is a simple cryptocurrency trading bot written in Python. It uses the TA-Lib library for technical analysis and the Binance API for executing trades.

## Installation

To install the required dependencies, follow these steps:

1. Clone the repository:

bash
git clone https://github.com/iamkahmadi/crypto-trading-bot.git
2. Install the required Python packages:

bash
pip install -r requirements.txt
3. Install TA-Lib from GitHub:

If you are getting an error while installing TA-Lib, you can try installing it from the official GitHub repository. Follow these steps:

- Download the TA-Lib source code from the GitHub repository: [https://github.com/mrjbq7/ta-lib](https://github.com/mrjbq7/ta-lib)

- Extract the downloaded archive and navigate to the extracted folder.

- Run the following commands to build and install TA-Lib:

bash
./configure --prefix=/usr
make
sudo make install
- After successfully installing TA-Lib, you can proceed with the rest of the installation steps.

## Usage

To use the trading bot, follow these steps:

1. Open the `config.py` file and enter your Binance API key and secret key.

2. Run the `real_time_trade_bot.py` script:

bash
python real_time_trade_bot.py
3. The bot will start monitoring the cryptocurrency market and execute trades based on the specified strategy.

## Testing

To test the trading bot, you can use the `test_trade_bot.py` script. This script simulates trades without actually executing them on the exchange. It can be useful for backtesting and evaluating different strategies.

bash
python test_trade_bot.py
## Disclaimer

Please note that cryptocurrency trading involves substantial risk and may not be suitable for everyone. The trading bot provided here is for educational purposes only and should not be considered as financial advice. Always do your own research and exercise caution when trading cryptocurrencies.