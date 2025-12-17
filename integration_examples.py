"""
QuantAgent Integration Examples
How to integrate QuantAgent signals with popular trading platforms
"""

from trading_graph import TradingGraph
import pandas as pd

# ====================================================================
# Example 1: Binance (Crypto)
# ====================================================================
def binance_integration_example():
    """
    Integrate QuantAgent with Binance for crypto trading
    Requires: pip install python-binance
    """
    from binance.client import Client

    # Initialize Binance client
    api_key = "your_binance_api_key"
    api_secret = "your_binance_secret"
    client = Client(api_key, api_secret)

    # Initialize QuantAgent
    trading_graph = TradingGraph()

    # Get BTC data
    klines = client.get_klines(symbol='BTCUSDT', interval=Client.KLINE_INTERVAL_1HOUR, limit=100)
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                       'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                                       'taker_buy_quote', 'ignore'])

    # Prepare data for QuantAgent
    initial_state = {
        "kline_data": {
            "open": df['open'].astype(float).tolist(),
            "high": df['high'].astype(float).tolist(),
            "low": df['low'].astype(float).tolist(),
            "close": df['close'].astype(float).tolist(),
            "volume": df['volume'].astype(float).tolist(),
        },
        "time_frame": "1hour",
        "stock_name": "BTC"
    }

    # Get QuantAgent signal
    result = trading_graph.graph.invoke(initial_state)
    decision = result.get("final_trade_decision", "")

    # Parse decision
    if "LONG" in decision:
        # Place BUY order on Binance
        order = client.order_market_buy(
            symbol='BTCUSDT',
            quantity=0.01  # Adjust based on your risk
        )
        print(f"✅ Placed LONG order: {order}")

    elif "SHORT" in decision:
        # Place SELL order on Binance
        order = client.order_market_sell(
            symbol='BTCUSDT',
            quantity=0.01
        )
        print(f"✅ Placed SHORT order: {order}")


# ====================================================================
# Example 2: Interactive Brokers (Stocks/Futures)
# ====================================================================
def interactive_brokers_example():
    """
    Integrate with Interactive Brokers using ib_insync
    Requires: pip install ib_insync
    """
    from ib_insync import IB, Stock, MarketOrder

    # Connect to Interactive Brokers
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=1)  # TWS/Gateway

    # Initialize QuantAgent
    trading_graph = TradingGraph()

    # Get SPX data from your source
    # ... prepare kline_data ...

    initial_state = {
        "kline_data": your_data,
        "time_frame": "1hour",
        "stock_name": "SPX"
    }

    result = trading_graph.graph.invoke(initial_state)
    decision = result.get("final_trade_decision", "")

    # Define contract
    contract = Stock('SPY', 'SMART', 'USD')  # SPY as SPX proxy

    if "LONG" in decision:
        order = MarketOrder('BUY', 100)  # 100 shares
        trade = ib.placeOrder(contract, order)
        print(f"✅ Placed LONG: {trade}")

    elif "SHORT" in decision:
        order = MarketOrder('SELL', 100)
        trade = ib.placeOrder(contract, order)
        print(f"✅ Placed SHORT: {trade}")


# ====================================================================
# Example 3: Alpaca (Commission-free Stock Trading)
# ====================================================================
def alpaca_integration_example():
    """
    Integrate with Alpaca trading API
    Requires: pip install alpaca-trade-api
    """
    import alpaca_trade_api as tradeapi

    # Initialize Alpaca
    api = tradeapi.REST(
        'your_api_key',
        'your_secret_key',
        'https://paper-api.alpaca.markets'  # Paper trading
    )

    # Initialize QuantAgent
    trading_graph = TradingGraph()

    # ... get data and run analysis ...
    initial_state = {
        "kline_data": your_data,
        "time_frame": "1hour",
        "stock_name": "AAPL"
    }

    result = trading_graph.graph.invoke(initial_state)
    decision = result.get("final_trade_decision", "")

    if "LONG" in decision:
        api.submit_order(
            symbol='AAPL',
            qty=10,
            side='buy',
            type='market',
            time_in_force='gtc'
        )
        print("✅ Placed LONG order")

    elif "SHORT" in decision:
        api.submit_order(
            symbol='AAPL',
            qty=10,
            side='sell',
            type='market',
            time_in_force='gtc'
        )
        print("✅ Placed SHORT order")


# ====================================================================
# Example 4: MetaTrader 5 (Forex/CFD)
# ====================================================================
def metatrader5_example():
    """
    Integrate with MetaTrader 5
    Requires: pip install MetaTrader5
    """
    import MetaTrader5 as mt5

    # Initialize MT5
    if not mt5.initialize():
        print("MT5 initialization failed")
        return

    # Initialize QuantAgent
    trading_graph = TradingGraph()

    # ... get data and analyze ...

    result = trading_graph.graph.invoke(initial_state)
    decision = result.get("final_trade_decision", "")

    symbol = "EURUSD"
    lot = 0.1

    if "LONG" in decision:
        # Place BUY order
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY,
            "price": mt5.symbol_info_tick(symbol).ask,
            "deviation": 20,
            "magic": 234000,
            "comment": "QuantAgent LONG",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        print(f"✅ LONG order: {result}")

    elif "SHORT" in decision:
        # Place SELL order
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_SELL,
            "price": mt5.symbol_info_tick(symbol).bid,
            "deviation": 20,
            "magic": 234000,
            "comment": "QuantAgent SHORT",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        print(f"✅ SHORT order: {result}")


# ====================================================================
# Example 5: TradingView Webhook (Universal)
# ====================================================================
def tradingview_webhook_server():
    """
    Create a Flask webhook server to receive TradingView alerts
    and use QuantAgent for confirmation
    """
    from flask import Flask, request, jsonify

    app = Flask(__name__)
    trading_graph = TradingGraph()

    @app.route('/webhook', methods=['POST'])
    def webhook():
        data = request.json

        # TradingView sends alert data
        symbol = data.get('ticker')
        timeframe = data.get('interval')

        # Run QuantAgent analysis
        # ... fetch data and analyze ...

        result = trading_graph.graph.invoke(initial_state)
        decision = result.get("final_trade_decision", "")

        # Confirm or reject TradingView signal
        if "LONG" in decision:
            # Execute trade on your broker via API
            return jsonify({"status": "LONG confirmed", "action": "BUY"})
        elif "SHORT" in decision:
            return jsonify({"status": "SHORT confirmed", "action": "SELL"})
        else:
            return jsonify({"status": "No signal"})

    app.run(port=8000)


# ====================================================================
# Example 6: Scheduled Bot (Cron/Scheduler)
# ====================================================================
def automated_trading_bot():
    """
    Run QuantAgent on a schedule (e.g., every hour)
    """
    import schedule
    import time

    def run_analysis():
        trading_graph = TradingGraph()

        # Fetch latest data (yfinance, Binance, etc.)
        import yfinance as yf
        data = yf.download("BTC-USD", period="5d", interval="1h")

        initial_state = {
            "kline_data": {
                "open": data['Open'].tolist(),
                "high": data['High'].tolist(),
                "low": data['Low'].tolist(),
                "close": data['Close'].tolist(),
                "volume": data['Volume'].tolist(),
            },
            "time_frame": "1hour",
            "stock_name": "BTC"
        }

        result = trading_graph.graph.invoke(initial_state)
        decision = result.get("final_trade_decision", "")

        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Decision: {decision}")

        # Execute trade based on decision
        # ... your broker API call here ...

    # Schedule to run every hour
    schedule.every().hour.at(":00").do(run_analysis)

    print("🤖 Trading bot started...")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    print("""
    QuantAgent Trading Integration Examples
    ========================================

    Choose a platform to integrate:
    1. Binance (Crypto)
    2. Interactive Brokers (Stocks/Futures)
    3. Alpaca (Commission-free stocks)
    4. MetaTrader 5 (Forex/CFD)
    5. TradingView Webhook
    6. Automated Bot (Scheduled)

    ⚠️  DISCLAIMER: This is educational code.
    Always test with paper trading first!
    """)
