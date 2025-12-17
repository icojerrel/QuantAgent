# 📊 QuantAgent Trading Strategy Guide

Een complete, production-ready trading strategie met risk management, position sizing en automatische executie.

---

## 🎯 Strategie Overzicht

### Wat doet deze strategie?

```
1. Haalt real-time marktdata op (Bitcoin, stocks, etc.)
   ↓
2. QuantAgent analyseert met 4 AI agents
   ↓
3. Genereert LONG/SHORT signaal + confidence score
   ↓
4. Risk management: berekent position size, stop loss, take profit
   ↓
5. Voert trade uit (simulatie of live via API)
   ↓
6. Monitort positie en sluit bij SL/TP
   ↓
7. Herhaalt elk uur (of custom interval)
```

---

## 🏗️ Strategie Componenten

### 1. **Signal Generation** (QuantAgent)
- Gebruikt alle 4 agents (Indicator, Pattern, Trend, Decision)
- Genereert LONG/SHORT/HOLD signaal
- Berekent confidence score op basis van agent agreement

### 2. **Risk Management**
- **Position Sizing**: Riskeert 2% van capital per trade
- **Stop Loss**: 2% beneden entry
- **Take Profit**: 4% boven entry (2:1 risk/reward)
- **Max Daily Loss**: 5% van initial capital
- **Max Positions**: 3 concurrent trades

### 3. **Trade Execution**
- Automatische order placement
- Real-time stop loss monitoring
- Take profit executie
- Commission tracking

### 4. **Portfolio Management**
- Capital tracking
- P&L berekening
- Win rate statistics
- Daily performance limits

---

## 🚀 Hoe te Gebruiken

### Optie 1: Simulatie Mode (Aanbevolen om te starten)

```bash
# Start de strategie in simulatie mode
python trading_strategy.py
```

Dit draait de strategie **zonder echte trades te plaatsen**.

**Output:**
```
🚀 Starting QuantAgent Strategy (Live Mode)
Symbol: BTC-USD | Timeframe: 1h
Capital: $10000.00
--------------------------------------------------------------------------------

✅ Opened LONG position: BTC-USD @ $42,350.00
   Size: 0.2356 | SL: $41,503.00 | TP: $44,044.00

💼 PORTFOLIO STATUS
Capital: $9,990.12
Total Equity: $10,045.30
Daily P&L: $55.18
Total Trades: 1

📊 OPEN POSITIONS (1):
  BTC-USD: LONG | Entry: $42,350.00 | Unrealized P&L: $55.18

⏰ Waiting 3600s until next check...
```

---

### Optie 2: Live Trading (met Binance API)

**⚠️ WAARSCHUWING: Dit plaatst ECHTE orders!**

```python
# binance_live_strategy.py
from trading_strategy import QuantAgentStrategy, StrategyConfig
from binance.client import Client

# Configureer
config = StrategyConfig(
    symbol="BTC-USD",
    timeframe="1h",
    initial_capital=1000.0,  # Start met $1000
    position_size_pct=0.02,
    stop_loss_pct=0.02,
    take_profit_pct=0.04
)

# Initialiseer Binance
binance_client = Client("your_api_key", "your_secret")

# Start strategie
strategy = QuantAgentStrategy(config)

# Override de open_position method voor live execution
def live_open_position(symbol, signal, price):
    position = strategy.open_position(symbol, signal, price)

    if position and signal.value == "LONG":
        # Plaats echte BUY order op Binance
        order = binance_client.order_market_buy(
            symbol='BTCUSDT',
            quantity=position.size
        )
        print(f"✅ Live order placed: {order}")

    return position

# Run
strategy.open_position = live_open_position
strategy.run_live(interval_seconds=3600)
```

---

### Optie 3: Backtest Mode

```python
# backtest.py
from trading_strategy import QuantAgentStrategy, StrategyConfig
import pandas as pd

config = StrategyConfig(
    symbol="BTC-USD",
    timeframe="4h",
    initial_capital=10000.0
)

strategy = QuantAgentStrategy(config)

# Run backtest over historical data
for i in range(100):  # 100 iterations
    strategy.run_iteration()

# Print results
strategy.print_final_report()
strategy.save_results("backtest_results.json")
```

---

## ⚙️ Configuratie Parameters

### Trading Parameters

```python
StrategyConfig(
    symbol="BTC-USD",              # Asset to trade
    timeframe="1h",                # Candlestick timeframe
    position_size_pct=0.02,        # Risk 2% per trade
    max_position_size_pct=0.10,    # Max 10% in one asset
)
```

### Risk Management

```python
StrategyConfig(
    stop_loss_pct=0.02,            # 2% stop loss
    take_profit_pct=0.04,          # 4% take profit (2:1 R/R)
    max_daily_loss_pct=0.05,       # Max 5% daily loss
    max_positions=3,               # Max 3 concurrent positions
)
```

### Signal Filtering

```python
StrategyConfig(
    min_confidence_score=0.7,           # Min confidence to trade
    require_all_agents_agree=False,     # All 3 agents must agree
    use_trend_filter=True,              # Only trade with trend
)
```

---

## 📈 Performance Metrics

De strategie tracked automatisch:

- **Win Rate**: % winning trades
- **Total Return**: % portfolio groei
- **Sharpe Ratio**: Risk-adjusted return
- **Max Drawdown**: Grootste verlies van peak
- **Profit Factor**: Gross profit / gross loss

**Voorbeeld output:**

```
📈 FINAL PERFORMANCE REPORT
================================================================================
Initial Capital: $10000.00
Final Equity: $12,450.00
Total Return: +24.50%
Total Trades: 45
Winning Trades: 28
Losing Trades: 17
Win Rate: 62.2%
================================================================================
```

---

## 🎓 Strategie Details

### Entry Conditions

Een trade wordt geopend wanneer:

1. ✅ QuantAgent geeft LONG of SHORT signaal
2. ✅ Confidence score > 0.65 (default)
3. ✅ Geen bestaande positie in hetzelfde asset
4. ✅ Max positions niet bereikt (< 3)
5. ✅ Daily loss limit niet bereikt
6. ✅ Voldoende capital beschikbaar

### Exit Conditions

Een positie wordt gesloten wanneer:

1. 🎯 **Take Profit bereikt** (+4% voor LONG, -4% voor SHORT)
2. 🛑 **Stop Loss geraakt** (-2% voor LONG, +2% voor SHORT)
3. 🔄 **Signaal reversal** (LONG → SHORT of omgekeerd)
4. ⏹️ **Handmatig gestopt** (Ctrl+C)

### Position Sizing Formula

```python
# Fixed percentage risk
risk_per_trade = capital * 0.02  # 2%

# Calculate units
risk_per_unit = abs(entry_price - stop_loss_price)
position_size = risk_per_trade / risk_per_unit

# Apply max position constraint
max_size = (capital * 0.10) / entry_price
position_size = min(position_size, max_size)
```

**Voorbeeld:**
- Capital: $10,000
- Risk per trade: $200 (2%)
- Entry: $50,000
- Stop loss: $49,000 (2% below)
- Risk per unit: $1,000
- **Position size**: $200 / $1,000 = 0.2 BTC

---

## 🔧 Aanpassingen & Optimalisatie

### Custom Timeframes

```python
# Voor day trading
config = StrategyConfig(
    timeframe="15m",
    stop_loss_pct=0.01,  # Tighter stops
    take_profit_pct=0.02
)

# Voor swing trading
config = StrategyConfig(
    timeframe="4h",
    stop_loss_pct=0.05,  # Wider stops
    take_profit_pct=0.10
)
```

### Multiple Assets

```python
# Trade meerdere assets tegelijk
symbols = ["BTC-USD", "ETH-USD", "SPY"]

for symbol in symbols:
    config = StrategyConfig(symbol=symbol)
    strategy = QuantAgentStrategy(config)
    strategy.run_iteration()
```

### Aggressive vs Conservative

```python
# Aggressive (higher risk, higher reward)
config_aggressive = StrategyConfig(
    position_size_pct=0.05,      # 5% risk per trade
    max_positions=5,
    min_confidence_score=0.60
)

# Conservative (lower risk)
config_conservative = StrategyConfig(
    position_size_pct=0.01,      # 1% risk per trade
    max_positions=2,
    min_confidence_score=0.80,
    require_all_agents_agree=True
)
```

---

## 📊 Monitoring & Logging

### Log Files

De strategie schrijft naar:
- **Console**: Real-time updates
- **quantagent_strategy.log**: Volledige trade log

**Log voorbeeld:**
```
2025-12-17 14:30:00 [INFO] QuantAgent Signal for BTC-USD: LONG
2025-12-17 14:30:01 [INFO] Signal: LONG | Confidence: 0.78
2025-12-17 14:30:02 [INFO] ✅ Opened LONG position: BTC-USD @ $42,350.00
2025-12-17 15:45:00 [INFO] 🔄 Closed LONG position: BTC-USD @ $43,100.00
                            | P&L: $176.85 (+1.77%) | Reason: Take Profit
```

### JSON Export

```python
strategy.save_results("my_results.json")
```

**Output:**
```json
{
  "config": {...},
  "final_capital": 12450.00,
  "total_return_pct": 24.5,
  "total_trades": 45,
  "winning_trades": 28,
  "trades": [
    {
      "entry_time": "2025-12-17T14:30:00",
      "entry_price": 42350.00,
      "direction": "LONG",
      "exit_price": 43100.00,
      "pnl": 176.85,
      "pnl_pct": 1.77,
      "exit_reason": "Take Profit"
    },
    ...
  ]
}
```

---

## ⚠️ Risk Disclaimers

### Belangrijk om te Weten

1. **Geen Gegarandeerde Winst**
   - Trading is inherent risicovol
   - Verleden resultaten ≠ toekomstige resultaten
   - Je kunt je hele capital verliezen

2. **Test Altijd Eerst**
   - Start met paper trading (simulatie)
   - Test minstens 1-2 weken voor live
   - Begin met kleine bedragen

3. **Market Conditions**
   - Strategie presteert verschillend in bull/bear/sideways markets
   - Pas parameters aan voor verschillende condities
   - Monitor performance regelmatig

4. **Technical Risks**
   - API downtime
   - Network latency
   - Slippage op orders
   - LLM API rate limits

### Best Practices

✅ **DO:**
- Start met simulatie mode
- Gebruik stop losses ALTIJD
- Monitor daily losses
- Keep logs van alle trades
- Backtest before live trading
- Start klein en scale gradual

❌ **DON'T:**
- Trade met geld dat je niet kunt missen
- Ignore risk management
- Over-leverage positions
- Panic bij losses
- Wijzig strategie tijdens drawdown
- Trade zonder testing

---

## 🔍 Troubleshooting

### Strategie geeft geen signalen

```python
# Check confidence threshold
config.min_confidence_score = 0.50  # Lower threshold

# Check logs
tail -f quantagent_strategy.log
```

### Te veel losing trades

```python
# Tighten confidence
config.min_confidence_score = 0.75

# Use trend filter
config.use_trend_filter = True

# Reduce position size
config.position_size_pct = 0.01
```

### API errors

```python
# Add retry logic
import time

def safe_api_call(func, retries=3):
    for i in range(retries):
        try:
            return func()
        except Exception as e:
            if i == retries - 1:
                raise
            time.sleep(2 ** i)  # Exponential backoff
```

---

## 📚 Volgende Stappen

1. **Run Simulatie**
   ```bash
   python trading_strategy.py
   ```

2. **Analyseer Results**
   - Check win rate (target: >55%)
   - Check max drawdown (target: <15%)
   - Optimaliseer parameters

3. **Paper Trading**
   - Integreer met broker demo account
   - Run 2 weken real-time
   - Verify performance

4. **Go Live**
   - Start met 10% van intended capital
   - Scale up als performance blijft goed
   - Monitor dagelijks

---

## 🤝 Support

Vragen? Check:
- [DEPLOYMENT.md](DEPLOYMENT.md) - Setup instructies
- [integration_examples.py](integration_examples.py) - API voorbeelden
- [Discord Community](https://discord.gg/t9nQ6VXQ)

Happy trading! 🚀📈
