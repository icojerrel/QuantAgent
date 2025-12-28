"""
Strategy Comparison Framework
==============================

Compares QuantAgent's 4-agent system vs Alpha Arena's single-LLM approach
on the same market data and evaluates performance metrics.

Author: Strategy Comparison Framework
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import yfinance as yf
import logging

# Import QuantAgent
from trading_graph import TradingGraph

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ComparisonMetrics:
    """Performance metrics for comparison"""
    system_name: str
    total_return_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown_pct: float
    avg_hold_time_hours: float
    total_fees: float
    net_profit: float


@dataclass
class Trade:
    """Individual trade record"""
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    direction: str  # LONG or SHORT
    size: float
    pnl: float
    pnl_pct: float
    reason: str
    system: str


# ============================================================================
# QuantAgent Wrapper
# ============================================================================

class QuantAgentBacktest:
    """Wrapper for QuantAgent 4-agent system"""

    def __init__(self, initial_capital: float = 10000):
        self.trading_graph = TradingGraph()
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = []
        self.trades: List[Trade] = []
        self.current_position = None

    def get_signal(self, data: pd.DataFrame, symbol: str, timeframe: str) -> Tuple[str, Dict]:
        """
        Get trading signal from QuantAgent

        Returns:
            (signal, analysis) where signal is 'LONG', 'SHORT', or 'HOLD'
        """
        try:
            # Prepare data for QuantAgent
            initial_state = {
                "kline_data": {
                    "open": data['Open'].tolist(),
                    "high": data['High'].tolist(),
                    "low": data['Low'].tolist(),
                    "close": data['Close'].tolist(),
                    "volume": data['Volume'].tolist(),
                },
                "time_frame": timeframe,
                "stock_name": symbol.replace("-USD", "")
            }

            # Run QuantAgent analysis
            result = self.trading_graph.graph.invoke(initial_state)

            # Extract decision
            decision_text = result.get("final_trade_decision", "")

            # Parse signal
            if "LONG" in decision_text.upper():
                signal = "LONG"
            elif "SHORT" in decision_text.upper():
                signal = "SHORT"
            else:
                signal = "HOLD"

            analysis = {
                "decision": decision_text,
                "indicator_report": result.get("indicator_report", ""),
                "pattern_report": result.get("pattern_report", ""),
                "trend_report": result.get("trend_report", ""),
            }

            return signal, analysis

        except Exception as e:
            logger.error(f"Error getting QuantAgent signal: {e}")
            return "HOLD", {}

    def execute_trade(self, signal: str, current_price: float, timestamp: datetime):
        """Execute trade based on signal"""

        # Close existing position if signal changes
        if self.current_position and self.current_position['direction'] != signal:
            self._close_position(current_price, timestamp, "Signal Reversal")

        # Open new position
        if signal in ['LONG', 'SHORT'] and not self.current_position:
            self._open_position(signal, current_price, timestamp)

    def _open_position(self, direction: str, entry_price: float, timestamp: datetime):
        """Open new position"""
        # Risk 2% per trade
        risk_amount = self.capital * 0.02
        stop_loss_pct = 0.02

        # Calculate position size
        risk_per_unit = entry_price * stop_loss_pct
        size = risk_amount / risk_per_unit if risk_per_unit > 0 else 0

        if size > 0:
            self.current_position = {
                'direction': direction,
                'entry_price': entry_price,
                'entry_time': timestamp,
                'size': size,
                'stop_loss': entry_price * (1 - stop_loss_pct) if direction == 'LONG' else entry_price * (1 + stop_loss_pct),
                'take_profit': entry_price * (1 + 0.04) if direction == 'LONG' else entry_price * (1 - 0.04)
            }

            # Deduct cost from capital
            cost = size * entry_price
            commission = cost * 0.001
            self.capital -= (cost + commission)

            logger.info(f"[QuantAgent] Opened {direction} @ ${entry_price:.2f}, size={size:.4f}")

    def _close_position(self, exit_price: float, timestamp: datetime, reason: str):
        """Close current position"""
        if not self.current_position:
            return

        pos = self.current_position

        # Calculate P&L
        if pos['direction'] == 'LONG':
            pnl = (exit_price - pos['entry_price']) * pos['size']
        else:  # SHORT
            pnl = (pos['entry_price'] - exit_price) * pos['size']

        # Deduct commission
        exit_value = pos['size'] * exit_price
        commission = exit_value * 0.001
        pnl -= commission

        pnl_pct = (pnl / (pos['entry_price'] * pos['size'])) * 100

        # Return capital
        self.capital += (exit_value + pnl)

        # Record trade
        trade = Trade(
            entry_time=pos['entry_time'],
            entry_price=pos['entry_price'],
            exit_time=timestamp,
            exit_price=exit_price,
            direction=pos['direction'],
            size=pos['size'],
            pnl=pnl,
            pnl_pct=pnl_pct,
            reason=reason,
            system="QuantAgent"
        )
        self.trades.append(trade)

        logger.info(f"[QuantAgent] Closed {pos['direction']} @ ${exit_price:.2f}, P&L=${pnl:.2f} ({pnl_pct:+.2f}%), Reason={reason}")

        self.current_position = None

    def check_stop_loss_take_profit(self, high: float, low: float, timestamp: datetime):
        """Check if SL or TP was hit"""
        if not self.current_position:
            return

        pos = self.current_position

        if pos['direction'] == 'LONG':
            # Check stop loss
            if low <= pos['stop_loss']:
                self._close_position(pos['stop_loss'], timestamp, "Stop Loss")
            # Check take profit
            elif high >= pos['take_profit']:
                self._close_position(pos['take_profit'], timestamp, "Take Profit")

        else:  # SHORT
            # Check stop loss
            if high >= pos['stop_loss']:
                self._close_position(pos['stop_loss'], timestamp, "Stop Loss")
            # Check take profit
            elif low <= pos['take_profit']:
                self._close_position(pos['take_profit'], timestamp, "Take Profit")


# ============================================================================
# Alpha Arena Simulator
# ============================================================================

class AlphaArenaSimulator:
    """
    Simulates Alpha Arena's single-LLM approach

    Note: This is a simplified simulation since we don't have the actual
    Alpha Arena LLM integration. We'll use a heuristic that mimics its
    multi-timeframe hysteresis approach.
    """

    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.trades: List[Trade] = []
        self.current_position = None
        self.last_trade_time = None
        self.cooldown_bars = 0

    def get_signal(self, data_5m: pd.DataFrame, data_4h: pd.DataFrame, symbol: str) -> str:
        """
        Simulate Alpha Arena's multi-timeframe decision logic

        Uses 5m for intraday confirmation, 4h for structure
        """
        try:
            # Calculate indicators for 4h timeframe (structure)
            ema20_4h = data_4h['Close'].ewm(span=20).mean()
            ema50_4h = data_4h['Close'].ewm(span=50).mean()
            macd_4h = self._calculate_macd(data_4h['Close'])

            # Calculate indicators for 5m timeframe (intraday)
            rsi_5m = self._calculate_rsi(data_5m['Close'], 14)
            macd_5m = self._calculate_macd(data_5m['Close'])
            ema20_5m = data_5m['Close'].ewm(span=20).mean()

            # Get latest values
            current_price = data_5m['Close'].iloc[-1]

            # 4h structure assessment
            structure_bullish = (ema20_4h.iloc[-1] > ema50_4h.iloc[-1] and
                                macd_4h['histogram'].iloc[-1] > 0)
            structure_bearish = (ema20_4h.iloc[-1] < ema50_4h.iloc[-1] and
                                macd_4h['histogram'].iloc[-1] < 0)

            # 5m momentum assessment
            momentum_bullish = (rsi_5m.iloc[-1] > 50 and
                               macd_5m['histogram'].iloc[-1] > 0 and
                               current_price > ema20_5m.iloc[-1])
            momentum_bearish = (rsi_5m.iloc[-1] < 50 and
                               macd_5m['histogram'].iloc[-1] < 0 and
                               current_price < ema20_5m.iloc[-1])

            # Hysteresis logic: require both timeframes to agree
            if structure_bullish and momentum_bullish:
                signal = "LONG"
            elif structure_bearish and momentum_bearish:
                signal = "SHORT"
            else:
                signal = "HOLD"

            # Cooldown enforcement (3-bar minimum)
            if self.cooldown_bars > 0:
                signal = "HOLD"
                self.cooldown_bars -= 1

            return signal

        except Exception as e:
            logger.error(f"Error calculating Alpha Arena signal: {e}")
            return "HOLD"

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(self, prices: pd.Series) -> Dict:
        """Calculate MACD"""
        ema12 = prices.ewm(span=12).mean()
        ema26 = prices.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal
        return {'macd': macd, 'signal': signal, 'histogram': histogram}

    def execute_trade(self, signal: str, current_price: float, timestamp: datetime):
        """Execute trade with 3-10x leverage"""

        # Close existing position if signal changes
        if self.current_position and self.current_position['direction'] != signal:
            self._close_position(current_price, timestamp, "Signal Flip")
            self.cooldown_bars = 3  # 3-bar cooldown

        # Open new position
        if signal in ['LONG', 'SHORT'] and not self.current_position:
            self._open_position(signal, current_price, timestamp)

    def _open_position(self, direction: str, entry_price: float, timestamp: datetime):
        """Open leveraged position (5x leverage)"""
        leverage = 5.0
        allocation = self.capital * 0.1  # 10% of capital
        notional = allocation * leverage
        size = notional / entry_price

        # Stop loss at 2%, take profit at 4%
        stop_loss_pct = 0.02
        take_profit_pct = 0.04

        self.current_position = {
            'direction': direction,
            'entry_price': entry_price,
            'entry_time': timestamp,
            'size': size,
            'leverage': leverage,
            'margin': allocation,
            'stop_loss': entry_price * (1 - stop_loss_pct) if direction == 'LONG' else entry_price * (1 + stop_loss_pct),
            'take_profit': entry_price * (1 + take_profit_pct) if direction == 'LONG' else entry_price * (1 - take_profit_pct)
        }

        # Deduct margin from capital
        commission = notional * 0.001
        self.capital -= (allocation + commission)

        logger.info(f"[AlphaArena] Opened {direction} @ ${entry_price:.2f}, size={size:.4f}, leverage={leverage}x")

    def _close_position(self, exit_price: float, timestamp: datetime, reason: str):
        """Close leveraged position"""
        if not self.current_position:
            return

        pos = self.current_position

        # Calculate P&L (leverage amplifies gains/losses)
        if pos['direction'] == 'LONG':
            price_change_pct = (exit_price - pos['entry_price']) / pos['entry_price']
        else:  # SHORT
            price_change_pct = (pos['entry_price'] - exit_price) / pos['entry_price']

        # P&L on margin (leverage multiplies return)
        pnl = pos['margin'] * price_change_pct * pos['leverage']

        # Deduct exit commission
        notional_exit = pos['size'] * exit_price
        commission = notional_exit * 0.001
        pnl -= commission

        pnl_pct = (pnl / pos['margin']) * 100

        # Return margin + P&L
        self.capital += (pos['margin'] + pnl)

        # Record trade
        trade = Trade(
            entry_time=pos['entry_time'],
            entry_price=pos['entry_price'],
            exit_time=timestamp,
            exit_price=exit_price,
            direction=pos['direction'],
            size=pos['size'],
            pnl=pnl,
            pnl_pct=pnl_pct,
            reason=reason,
            system="AlphaArena"
        )
        self.trades.append(trade)

        logger.info(f"[AlphaArena] Closed {pos['direction']} @ ${exit_price:.2f}, P&L=${pnl:.2f} ({pnl_pct:+.2f}%), Reason={reason}")

        self.current_position = None

    def check_stop_loss_take_profit(self, high: float, low: float, timestamp: datetime):
        """Check SL/TP"""
        if not self.current_position:
            return

        pos = self.current_position

        if pos['direction'] == 'LONG':
            if low <= pos['stop_loss']:
                self._close_position(pos['stop_loss'], timestamp, "Stop Loss")
            elif high >= pos['take_profit']:
                self._close_position(pos['take_profit'], timestamp, "Take Profit")
        else:  # SHORT
            if high >= pos['stop_loss']:
                self._close_position(pos['stop_loss'], timestamp, "Stop Loss")
            elif low <= pos['take_profit']:
                self._close_position(pos['take_profit'], timestamp, "Take Profit")


# ============================================================================
# Comparison Engine
# ============================================================================

class StrategyComparison:
    """Main comparison engine"""

    def __init__(self, symbol: str = "BTC-USD", start_date: str = "2024-01-01",
                 end_date: str = "2024-12-01", initial_capital: float = 10000):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital

        # Initialize both systems
        self.quantagent = QuantAgentBacktest(initial_capital)
        self.alphaarena = AlphaArenaSimulator(initial_capital)

        logger.info(f"Initialized comparison: {symbol} from {start_date} to {end_date}")

    def fetch_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Fetch market data for both timeframes"""
        logger.info("Fetching market data...")

        # Fetch 1h data for QuantAgent
        data_1h = yf.download(self.symbol, start=self.start_date, end=self.end_date,
                              interval="1h", progress=False)

        # Fetch 4h data for Alpha Arena
        data_4h = yf.download(self.symbol, start=self.start_date, end=self.end_date,
                              interval="4h", progress=False)

        # Fetch 5m data for Alpha Arena intraday
        # Note: yfinance limits 5m data to ~60 days, so we'll use 1h as proxy
        data_5m = data_1h.copy()  # Use 1h as proxy for 5m

        logger.info(f"Fetched {len(data_1h)} bars (1h), {len(data_4h)} bars (4h)")

        return data_1h, data_4h

    def run_backtest(self):
        """Run backtest on both systems"""
        logger.info("\n" + "="*80)
        logger.info("STARTING BACKTEST")
        logger.info("="*80 + "\n")

        # Fetch data
        data_1h, data_4h = self.fetch_data()

        # Run backtest bar by bar
        for i in range(100, len(data_1h)):  # Start after 100 bars for indicators
            bar = data_1h.iloc[i]
            timestamp = bar.name

            # Get last 100 bars for analysis
            hist_1h = data_1h.iloc[i-100:i]
            hist_4h = data_4h[data_4h.index <= timestamp].tail(100)

            # QuantAgent signal
            qa_signal, qa_analysis = self.quantagent.get_signal(hist_1h, self.symbol, "1hour")
            self.quantagent.execute_trade(qa_signal, bar['Close'], timestamp)
            self.quantagent.check_stop_loss_take_profit(bar['High'], bar['Low'], timestamp)

            # Alpha Arena signal
            aa_signal = self.alphaarena.get_signal(hist_1h, hist_4h, self.symbol)
            self.alphaarena.execute_trade(aa_signal, bar['Close'], timestamp)
            self.alphaarena.check_stop_loss_take_profit(bar['High'], bar['Low'], timestamp)

            # Progress logging
            if i % 100 == 0:
                logger.info(f"Progress: {i}/{len(data_1h)} bars processed")

        # Close any open positions
        final_price = data_1h['Close'].iloc[-1]
        final_time = data_1h.index[-1]

        if self.quantagent.current_position:
            self.quantagent._close_position(final_price, final_time, "Backtest End")

        if self.alphaarena.current_position:
            self.alphaarena._close_position(final_price, final_time, "Backtest End")

        logger.info("\n" + "="*80)
        logger.info("BACKTEST COMPLETE")
        logger.info("="*80 + "\n")

    def calculate_metrics(self) -> Tuple[ComparisonMetrics, ComparisonMetrics]:
        """Calculate performance metrics for both systems"""

        def calc_metrics(system_name: str, trades: List[Trade],
                        final_capital: float, initial_capital: float) -> ComparisonMetrics:

            if len(trades) == 0:
                return ComparisonMetrics(
                    system_name=system_name,
                    total_return_pct=0,
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0,
                    win_rate=0,
                    avg_win=0,
                    avg_loss=0,
                    profit_factor=0,
                    sharpe_ratio=0,
                    max_drawdown_pct=0,
                    avg_hold_time_hours=0,
                    total_fees=0,
                    net_profit=final_capital - initial_capital
                )

            winning = [t for t in trades if t.pnl > 0]
            losing = [t for t in trades if t.pnl <= 0]

            total_return = ((final_capital - initial_capital) / initial_capital) * 100
            win_rate = (len(winning) / len(trades)) * 100 if trades else 0
            avg_win = np.mean([t.pnl for t in winning]) if winning else 0
            avg_loss = np.mean([t.pnl for t in losing]) if losing else 0

            gross_profit = sum([t.pnl for t in winning])
            gross_loss = abs(sum([t.pnl for t in losing]))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

            # Sharpe ratio
            returns = [t.pnl_pct for t in trades]
            sharpe = (np.mean(returns) / np.std(returns)) if len(returns) > 1 and np.std(returns) > 0 else 0

            # Max drawdown
            equity_curve = [initial_capital]
            for t in trades:
                equity_curve.append(equity_curve[-1] + t.pnl)

            peak = equity_curve[0]
            max_dd = 0
            for eq in equity_curve:
                if eq > peak:
                    peak = eq
                dd = ((peak - eq) / peak) * 100
                if dd > max_dd:
                    max_dd = dd

            # Avg hold time
            hold_times = [(t.exit_time - t.entry_time).total_seconds() / 3600 for t in trades]
            avg_hold_time = np.mean(hold_times) if hold_times else 0

            return ComparisonMetrics(
                system_name=system_name,
                total_return_pct=total_return,
                total_trades=len(trades),
                winning_trades=len(winning),
                losing_trades=len(losing),
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=avg_loss,
                profit_factor=profit_factor,
                sharpe_ratio=sharpe,
                max_drawdown_pct=max_dd,
                avg_hold_time_hours=avg_hold_time,
                total_fees=0,  # Simplified
                net_profit=final_capital - initial_capital
            )

        qa_metrics = calc_metrics("QuantAgent (4-Agent)", self.quantagent.trades,
                                 self.quantagent.capital, self.initial_capital)
        aa_metrics = calc_metrics("Alpha Arena (Single-LLM)", self.alphaarena.trades,
                                 self.alphaarena.capital, self.initial_capital)

        return qa_metrics, aa_metrics

    def generate_report(self):
        """Generate comparison report"""
        qa_metrics, aa_metrics = self.calculate_metrics()

        print("\n" + "="*100)
        print("STRATEGY COMPARISON REPORT")
        print("="*100)
        print(f"\nSymbol: {self.symbol}")
        print(f"Period: {self.start_date} to {self.end_date}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print("\n" + "-"*100)

        # Comparison table
        print(f"\n{'METRIC':<30} {'QuantAgent':<25} {'Alpha Arena':<25} {'Winner':<15}")
        print("-"*100)

        metrics_to_compare = [
            ("Total Return %", "total_return_pct", "higher"),
            ("Total Trades", "total_trades", "neutral"),
            ("Win Rate %", "win_rate", "higher"),
            ("Avg Win $", "avg_win", "higher"),
            ("Avg Loss $", "avg_loss", "higher"),  # Less negative is better
            ("Profit Factor", "profit_factor", "higher"),
            ("Sharpe Ratio", "sharpe_ratio", "higher"),
            ("Max Drawdown %", "max_drawdown_pct", "lower"),
            ("Avg Hold Time (hrs)", "avg_hold_time_hours", "neutral"),
            ("Net Profit $", "net_profit", "higher"),
        ]

        for metric_name, attr, comparison in metrics_to_compare:
            qa_val = getattr(qa_metrics, attr)
            aa_val = getattr(aa_metrics, attr)

            if comparison == "higher":
                winner = "QuantAgent ✓" if qa_val > aa_val else "Alpha Arena ✓" if aa_val > qa_val else "Tie"
            elif comparison == "lower":
                winner = "QuantAgent ✓" if qa_val < aa_val else "Alpha Arena ✓" if aa_val < qa_val else "Tie"
            else:
                winner = "-"

            # Format values
            if "%" in metric_name or "ratio" in metric_name.lower():
                qa_str = f"{qa_val:.2f}%"
                aa_str = f"{aa_val:.2f}%"
            elif "$" in metric_name:
                qa_str = f"${qa_val:.2f}"
                aa_str = f"${aa_val:.2f}"
            else:
                qa_str = f"{qa_val:.2f}"
                aa_str = f"{aa_val:.2f}"

            print(f"{metric_name:<30} {qa_str:<25} {aa_str:<25} {winner:<15}")

        print("\n" + "="*100)

        # Trade analysis
        print("\nTRADE BREAKDOWN")
        print("-"*100)
        print(f"{'System':<30} {'Wins':<10} {'Losses':<10} {'Win Rate':<15} {'P&L':<20}")
        print("-"*100)
        print(f"{'QuantAgent':<30} {qa_metrics.winning_trades:<10} {qa_metrics.losing_trades:<10} "
              f"{qa_metrics.win_rate:<14.2f}% ${qa_metrics.net_profit:<19,.2f}")
        print(f"{'Alpha Arena':<30} {aa_metrics.winning_trades:<10} {aa_metrics.losing_trades:<10} "
              f"{aa_metrics.win_rate:<14.2f}% ${aa_metrics.net_profit:<19,.2f}")
        print("="*100)

        # Save to JSON
        report = {
            "symbol": self.symbol,
            "period": f"{self.start_date} to {self.end_date}",
            "initial_capital": self.initial_capital,
            "quantagent": asdict(qa_metrics),
            "alphaarena": asdict(aa_metrics),
            "trades": {
                "quantagent": [asdict(t) for t in self.quantagent.trades],
                "alphaarena": [asdict(t) for t in self.alphaarena.trades]
            }
        }

        with open("strategy_comparison_results.json", "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info("\n✅ Report saved to strategy_comparison_results.json")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run strategy comparison"""

    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║           Strategy Comparison Framework                      ║
    ║           QuantAgent vs Alpha Arena                          ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

    # Initialize comparison
    comparison = StrategyComparison(
        symbol="BTC-USD",
        start_date="2024-01-01",
        end_date="2024-12-01",
        initial_capital=10000
    )

    # Run backtest
    comparison.run_backtest()

    # Generate report
    comparison.generate_report()

    print("\n🏁 Comparison complete!")


if __name__ == "__main__":
    main()
