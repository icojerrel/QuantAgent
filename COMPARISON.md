# 🏆 Strategy Comparison: QuantAgent vs Alpha Arena

Een uitgebreid vergelijkingsframework dat de twee trading systemen head-to-head test op dezelfde marktdata.

---

## 📊 Wat Wordt Vergeleken?

### **QuantAgent (4-Agent System)**
- **Architectuur**: 4 gespecialiseerde agents (Indicator, Pattern, Trend, Decision)
- **Approach**: Collaborative multi-agent reasoning
- **Risk**: Conservative (2% risk per trade, 2% SL, 4% TP)
- **Leverage**: 1x (no leverage)
- **Timeframe**: 1h primary

### **Alpha Arena (Single-LLM System)**
- **Architectuur**: Enkele krachtige LLM als "quantitative trader"
- **Approach**: Multi-timeframe hysteresis (5m + 4h)
- **Risk**: Aggressive (3-10x leverage encouraged)
- **Leverage**: 5x (simulated)
- **Timeframe**: 5m intraday + 4h structure

---

## 🎯 Vergelijkingspunten

Het framework vergelijkt:

### 1. **Returns**
- Total return %
- Net profit $
- Risk-adjusted returns (Sharpe ratio)

### 2. **Win Rate**
- % winning trades
- Average win size
- Average loss size
- Profit factor (gross profit / gross loss)

### 3. **Risk Management**
- Max drawdown %
- Stop loss effectiveness
- Position sizing quality

### 4. **Trading Behavior**
- Total number of trades
- Average hold time
- Entry/exit timing

### 5. **Robustness**
- Performance across different market conditions
- Adaptability to volatility changes

---

## 🚀 Hoe te Gebruiken

### Quick Start

```bash
# Installeer dependencies (als je dat nog niet hebt gedaan)
pip install -r requirements.txt

# Run de vergelijking
python strategy_comparison.py
```

### Customize Parameters

```python
from strategy_comparison import StrategyComparison

# Maak custom vergelijking
comparison = StrategyComparison(
    symbol="BTC-USD",           # Asset om te testen
    start_date="2024-01-01",    # Start datum
    end_date="2024-12-01",      # Eind datum
    initial_capital=10000       # Start capital
)

# Run backtest
comparison.run_backtest()

# Genereer rapport
comparison.generate_report()
```

---

## 📈 Output

### Console Output

```
================================================================================
STRATEGY COMPARISON REPORT
================================================================================

Symbol: BTC-USD
Period: 2024-01-01 to 2024-12-01
Initial Capital: $10,000.00

--------------------------------------------------------------------------------

METRIC                         QuantAgent                Alpha Arena               Winner
--------------------------------------------------------------------------------
Total Return %                 +24.50%                   +85.20%                   Alpha Arena ✓
Total Trades                   45                        67                        -
Win Rate %                     62.22%                    58.21%                    QuantAgent ✓
Avg Win $                      $156.30                   $312.50                   Alpha Arena ✓
Avg Loss $                     -$78.20                   -$145.80                  QuantAgent ✓
Profit Factor                  2.85                      3.12                      Alpha Arena ✓
Sharpe Ratio                   1.42                      1.68                      Alpha Arena ✓
Max Drawdown %                 8.50%                     15.30%                    QuantAgent ✓
Avg Hold Time (hrs)            18.5                      12.3                      -
Net Profit $                   $2,450.00                 $8,520.00                 Alpha Arena ✓

================================================================================

TRADE BREAKDOWN
--------------------------------------------------------------------------------
System                         Wins       Losses     Win Rate        P&L
--------------------------------------------------------------------------------
QuantAgent                     28         17         62.22%          $2,450.00
Alpha Arena                    39         28         58.21%          $8,520.00
================================================================================

✅ Report saved to strategy_comparison_results.json
```

### JSON Output

Volledige resultaten worden opgeslagen in `strategy_comparison_results.json`:

```json
{
  "symbol": "BTC-USD",
  "period": "2024-01-01 to 2024-12-01",
  "initial_capital": 10000,
  "quantagent": {
    "total_return_pct": 24.50,
    "total_trades": 45,
    "win_rate": 62.22,
    "sharpe_ratio": 1.42,
    ...
  },
  "alphaarena": {
    "total_return_pct": 85.20,
    "total_trades": 67,
    "win_rate": 58.21,
    "sharpe_ratio": 1.68,
    ...
  },
  "trades": {
    "quantagent": [...],
    "alphaarena": [...]
  }
}
```

---

## 🔍 Hoe Het Werkt

### Backtest Proces

```
1. Fetch historical data (1h + 4h bars)
   ↓
2. For each bar:
   │
   ├─→ QuantAgent:
   │   ├── Get signal from 4-agent system
   │   ├── Execute trade (if signal changed)
   │   └── Check SL/TP
   │
   └─→ Alpha Arena:
       ├── Calculate multi-timeframe indicators
       ├── Apply hysteresis logic
       ├── Execute leveraged trade
       └── Check SL/TP
   ↓
3. Calculate performance metrics
   ↓
4. Generate comparison report
```

### QuantAgent Implementation

```python
class QuantAgentBacktest:
    """Simulates QuantAgent 4-agent system"""

    def get_signal(data, symbol, timeframe):
        # Run full 4-agent analysis
        result = trading_graph.invoke(kline_data)

        # Parse LONG/SHORT/HOLD from final decision
        decision = result["final_trade_decision"]
        signal = parse_signal(decision)

        return signal

    def execute_trade(signal, price):
        # Risk 2% per trade
        # SL at 2%, TP at 4%
        # No leverage
        ...
```

### Alpha Arena Simulation

```python
class AlphaArenaSimulator:
    """Simulates Alpha Arena multi-timeframe approach"""

    def get_signal(data_5m, data_4h):
        # 4h structure check (EMA20 vs EMA50, MACD)
        structure_bullish = check_structure(data_4h)

        # 5m momentum check (RSI, MACD, EMA)
        momentum_bullish = check_momentum(data_5m)

        # Hysteresis: require BOTH to agree
        if structure_bullish and momentum_bullish:
            return "LONG"
        elif structure_bearish and momentum_bearish:
            return "SHORT"
        else:
            return "HOLD"  # No conflicting signals

    def execute_trade(signal, price):
        # 5x leverage
        # SL at 2%, TP at 4%
        # Cooldown: 3 bars minimum
        ...
```

---

## 📊 Belangrijke Verschillen

### Decision Making

| Aspect | QuantAgent | Alpha Arena |
|--------|-----------|-------------|
| **Process** | Multi-agent deliberation | Single-LLM holistic |
| **Indicator Agent** | Dedicated RSI/MACD analysis | Combined in LLM |
| **Pattern Agent** | Specialized chart patterns | LLM visual analysis |
| **Trend Agent** | Support/resistance detection | Multi-timeframe structure |
| **Decision Agent** | Synthesizes all agents | LLM makes final call |

### Risk Profile

| Aspect | QuantAgent | Alpha Arena |
|--------|-----------|-------------|
| **Leverage** | 1x (spot) | 3-10x (perpetual) |
| **Risk/Trade** | 2% of capital | 10% margin × 5x leverage |
| **Max Loss/Trade** | ~2% | ~10% (if SL hit) |
| **Approach** | Conservative | Aggressive |

### Execution Speed

| Aspect | QuantAgent | Alpha Arena |
|--------|-----------|-------------|
| **Analysis Time** | ~30-60s (4 agents sequential) | ~10-20s (single LLM) |
| **API Calls** | 4 LLM calls | 1 LLM call (+ optional tools) |
| **Latency** | Higher | Lower |

---

## 🎓 Interpretatie van Resultaten

### Als QuantAgent Wint:

**Betekent:**
- Multi-agent deliberation leidt tot betere beslissingen
- Conservative risk management presteert beter
- Lagere leverage = lagere drawdowns
- Specialized agents > generalist LLM

**Use Case:**
- Risk-averse traders
- Long-term investing
- High volatility markets
- Beginner-friendly

---

### Als Alpha Arena Wint:

**Betekent:**
- Single powerful LLM is effectiever dan multi-agent
- Leverage amplifies returns (with higher risk)
- Multi-timeframe hysteresis werkt goed
- Faster execution = better entries

**Use Case:**
- Aggressive traders
- Experienced risk takers
- Trending markets
- Scalpers/day traders

---

### Als Het Close Is:

**Betekent:**
- Beide approaches zijn valide
- Market conditions bepalen welke beter is
- Hybrid approach mogelijk beste optie
- Test beide in verschillende regimes

---

## 🔧 Aanpassingen

### Test Verschillende Assets

```python
# Test op ETH in plaats van BTC
comparison = StrategyComparison(
    symbol="ETH-USD",
    start_date="2024-01-01",
    end_date="2024-12-01"
)
```

### Wijzig Risk Parameters

```python
# In strategy_comparison.py

# QuantAgent: verhoog risk
risk_amount = self.capital * 0.05  # 5% instead of 2%

# Alpha Arena: verlaag leverage
leverage = 3.0  # 3x instead of 5x
```

### Test Verschillende Timeframes

```python
# Haal 4h data op voor QuantAgent
data_4h = yf.download(symbol, interval="4h", ...)

# Gebruik 15m voor Alpha Arena intraday
data_15m = yf.download(symbol, interval="15m", ...)
```

---

## ⚠️ Limitaties

### Simulatie Beperkingen

1. **Alpha Arena Simplificatie**
   - Geen echte LLM integratie
   - Gebruikt heuristic rules in plaats van GPT/Claude
   - Kan niet tool calling simuleren

2. **Data Beperkingen**
   - yfinance heeft max 60 dagen voor 5m data
   - Gebruikt 1h als proxy voor 5m
   - Mogelijk slippage niet gesimuleerd

3. **QuantAgent Vereenvoudiging**
   - Geen commissies per agent call
   - Rate limiting niet gesimuleerd
   - LLM kosten niet meegenomen

### Hoe Resultaten Interpreteren

✅ **DO:**
- Vergelijk relatieve performance
- Kijk naar risk-adjusted returns (Sharpe)
- Analyseer drawdown tolerantie
- Test op meerdere assets/periodes

❌ **DON'T:**
- Neem absolute returns als garantie
- Negeer max drawdown
- Extrapoleer naar alle marktcondities
- Trade live zonder verder testen

---

## 📚 Volgende Stappen

### 1. Run de Baseline

```bash
python strategy_comparison.py
```

### 2. Analyseer Resultaten

Bekijk:
- Welke heeft betere Sharpe ratio?
- Welke heeft lagere drawdown?
- Welke past bij jouw risk tolerance?

### 3. Optimaliseer de Winnaar

Als QuantAgent wint:
- Optimaliseer agent prompts
- Tune position sizing
- Test meer assets

Als Alpha Arena wint:
- Integreer echte LLM
- Fine-tune leverage
- Optimaliseer cooldown

### 4. Hybride Approach

Combineer het beste van beide:
- QuantAgent voor analyse
- Alpha Arena voor executie
- Dual-system validation

---

## 🤝 Bijdragen

Wil je de vergelijking verbeteren?

**Mogelijke toevoegingen:**
- Meerdere assets tegelijk testen
- Walk-forward optimization
- Monte Carlo simulatie
- Live paper trading vergelijking
- Kosten tracking (API calls, fees)
- Slippage simulatie
- Market regime detection

---

## 📧 Support

Voor vragen over het vergelijkingsframework:
1. Check deze guide
2. Review `strategy_comparison.py` code
3. Run met `--debug` voor verbose output
4. Open een issue met resultaten

---

**Happy Comparing!** 🏆📊

*Vergeet niet: Past performance ≠ Future results. Altijd test met paper trading eerst!*
