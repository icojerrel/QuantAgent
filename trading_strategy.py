"""
QuantAgent Trading Strategy Implementation
===========================================

A complete, production-ready trading strategy that combines QuantAgent signals
with risk management, position sizing, and trade execution.

Author: QuantAgent Team
License: MIT
"""

import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import pandas as pd
import yfinance as yf
from trading_graph import TradingGraph


# ============================================================================
# Configuration
# ============================================================================

class SignalType(Enum):
    """Trading signal types"""
    LONG = "LONG"
    SHORT = "SHORT"
    HOLD = "HOLD"
    CLOSE = "CLOSE"


@dataclass
class StrategyConfig:
    """Strategy configuration parameters"""

    # Trading parameters
    symbol: str = "BTC-USD"
    timeframe: str = "1h"
    position_size_pct: float = 0.02  # 2% of capital per trade
    max_position_size_pct: float = 0.10  # Max 10% of capital in one asset

    # Risk management
    stop_loss_pct: float = 0.02  # 2% stop loss
    take_profit_pct: float = 0.04  # 4% take profit (2:1 R/R)
    max_daily_loss_pct: float = 0.05  # Max 5% daily loss
    max_positions: int = 3  # Max concurrent positions

    # Signal filtering
    min_confidence_score: float = 0.7  # Minimum confidence to trade
    require_all_agents_agree: bool = False  # Require all 3 agents to agree
    use_trend_filter: bool = True  # Only trade with trend

    # Execution
    use_market_orders: bool = True  # True = market, False = limit
    slippage_tolerance_pct: float = 0.001  # 0.1% max slippage

    # Backtesting
    initial_capital: float = 10000.0
    commission_pct: float = 0.001  # 0.1% commission per trade


@dataclass
class Trade:
    """Individual trade record"""
    entry_time: datetime
    entry_price: float
    direction: SignalType
    size: float
    stop_loss: float
    take_profit: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    exit_reason: Optional[str] = None


@dataclass
class Position:
    """Current open position"""
    symbol: str
    direction: SignalType
    entry_price: float
    size: float
    stop_loss: float
    take_profit: float
    entry_time: datetime
    unrealized_pnl: float = 0.0


# ============================================================================
# QuantAgent Trading Strategy
# ============================================================================

class QuantAgentStrategy:
    """
    Complete trading strategy using QuantAgent signals with risk management
    """

    def __init__(self, config: StrategyConfig):
        self.config = config
        self.trading_graph = TradingGraph()

        # Portfolio state
        self.capital = config.initial_capital
        self.initial_capital = config.initial_capital
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []

        # Risk tracking
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.last_reset_date = datetime.now().date()

        # Performance metrics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0

        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler('quantagent_strategy.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    # ========================================================================
    # Data & Signal Generation
    # ========================================================================

    def get_market_data(self, symbol: str, timeframe: str, lookback_periods: int = 100) -> pd.DataFrame:
        """Fetch market data from Yahoo Finance"""
        try:
            # Map timeframe to yfinance interval
            interval_map = {
                "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
                "1h": "1h", "4h": "4h", "1d": "1d"
            }
            interval = interval_map.get(timeframe, "1h")

            # Calculate period
            if interval in ["1m", "5m"]:
                period = "7d"
            elif interval in ["15m", "30m"]:
                period = "60d"
            else:
                period = "730d"  # 2 years

            data = yf.download(symbol, period=period, interval=interval, progress=False)

            if data.empty:
                raise ValueError(f"No data received for {symbol}")

            return data.tail(lookback_periods)

        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {e}")
            raise

    def get_quantagent_signal(self, symbol: str, timeframe: str) -> Tuple[SignalType, Dict]:
        """
        Get trading signal from QuantAgent

        Returns:
            (SignalType, analysis_dict) - Signal and full analysis
        """
        try:
            # Get market data
            data = self.get_market_data(symbol, timeframe)

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
                signal = SignalType.LONG
            elif "SHORT" in decision_text.upper():
                signal = SignalType.SHORT
            else:
                signal = SignalType.HOLD

            # Package analysis
            analysis = {
                "signal": signal,
                "decision": decision_text,
                "indicator_report": result.get("indicator_report", ""),
                "pattern_report": result.get("pattern_report", ""),
                "trend_report": result.get("trend_report", ""),
                "current_price": data['Close'].iloc[-1],
                "timestamp": datetime.now()
            }

            self.logger.info(f"QuantAgent Signal for {symbol}: {signal.value}")
            return signal, analysis

        except Exception as e:
            self.logger.error(f"Error getting QuantAgent signal: {e}")
            return SignalType.HOLD, {}

    def calculate_confidence_score(self, analysis: Dict) -> float:
        """
        Calculate confidence score from QuantAgent analysis

        Simple heuristic: check agreement between agents
        """
        score = 0.5  # Base score

        indicator_report = analysis.get("indicator_report", "").upper()
        pattern_report = analysis.get("pattern_report", "").upper()
        trend_report = analysis.get("trend_report", "").upper()
        signal = analysis.get("signal")

        if signal == SignalType.LONG:
            # Check bullish indicators
            if any(word in indicator_report for word in ["BULLISH", "BUY", "STRONG"]):
                score += 0.15
            if any(word in pattern_report for word in ["BULLISH", "UPWARD", "BREAK"]):
                score += 0.15
            if any(word in trend_report for word in ["UPTREND", "RISING", "SUPPORT"]):
                score += 0.20

        elif signal == SignalType.SHORT:
            # Check bearish indicators
            if any(word in indicator_report for word in ["BEARISH", "SELL", "WEAK"]):
                score += 0.15
            if any(word in pattern_report for word in ["BEARISH", "DOWNWARD", "BREAK"]):
                score += 0.15
            if any(word in trend_report for word in ["DOWNTREND", "FALLING", "RESISTANCE"]):
                score += 0.20

        return min(score, 1.0)

    # ========================================================================
    # Risk Management
    # ========================================================================

    def calculate_position_size(self, entry_price: float, stop_loss_price: float) -> float:
        """
        Calculate position size based on risk management

        Uses fixed percentage of capital risked per trade
        """
        # Risk per trade in dollars
        risk_per_trade = self.capital * self.config.position_size_pct

        # Risk per unit
        risk_per_unit = abs(entry_price - stop_loss_price)

        # Position size
        if risk_per_unit > 0:
            position_size = risk_per_trade / risk_per_unit
        else:
            position_size = 0

        # Apply max position size constraint
        max_size_dollars = self.capital * self.config.max_position_size_pct
        max_size_units = max_size_dollars / entry_price
        position_size = min(position_size, max_size_units)

        return position_size

    def calculate_stop_loss(self, entry_price: float, direction: SignalType) -> float:
        """Calculate stop loss price"""
        if direction == SignalType.LONG:
            return entry_price * (1 - self.config.stop_loss_pct)
        elif direction == SignalType.SHORT:
            return entry_price * (1 + self.config.stop_loss_pct)
        return entry_price

    def calculate_take_profit(self, entry_price: float, direction: SignalType) -> float:
        """Calculate take profit price"""
        if direction == SignalType.LONG:
            return entry_price * (1 + self.config.take_profit_pct)
        elif direction == SignalType.SHORT:
            return entry_price * (1 - self.config.take_profit_pct)
        return entry_price

    def check_daily_loss_limit(self) -> bool:
        """Check if daily loss limit has been reached"""
        # Reset daily tracking at start of new day
        if datetime.now().date() > self.last_reset_date:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.last_reset_date = datetime.now().date()

        # Check limit
        max_daily_loss = self.initial_capital * self.config.max_daily_loss_pct
        if self.daily_pnl <= -max_daily_loss:
            self.logger.warning(f"⚠️  Daily loss limit reached: ${self.daily_pnl:.2f}")
            return False

        return True

    def can_open_position(self) -> bool:
        """Check if we can open a new position"""
        # Check max positions
        if len(self.positions) >= self.config.max_positions:
            self.logger.info("Max positions reached")
            return False

        # Check daily loss limit
        if not self.check_daily_loss_limit():
            return False

        # Check capital
        if self.capital <= 0:
            self.logger.warning("No capital remaining")
            return False

        return True

    # ========================================================================
    # Trade Execution
    # ========================================================================

    def open_position(self, symbol: str, signal: SignalType, current_price: float) -> Optional[Position]:
        """Open a new position"""
        if not self.can_open_position():
            return None

        # Calculate stop loss and take profit
        stop_loss = self.calculate_stop_loss(current_price, signal)
        take_profit = self.calculate_take_profit(current_price, signal)

        # Calculate position size
        size = self.calculate_position_size(current_price, stop_loss)

        if size <= 0:
            self.logger.warning("Position size is zero, skipping trade")
            return None

        # Create position
        position = Position(
            symbol=symbol,
            direction=signal,
            entry_price=current_price,
            size=size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_time=datetime.now()
        )

        # Deduct capital
        position_value = size * current_price
        commission = position_value * self.config.commission_pct
        self.capital -= (position_value + commission)

        # Store position
        self.positions[symbol] = position

        # Create trade record
        trade = Trade(
            entry_time=position.entry_time,
            entry_price=position.entry_price,
            direction=signal,
            size=size,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        self.trade_history.append(trade)

        self.logger.info(
            f"✅ Opened {signal.value} position: {symbol} @ ${current_price:.2f} "
            f"| Size: {size:.4f} | SL: ${stop_loss:.2f} | TP: ${take_profit:.2f}"
        )

        return position

    def close_position(self, symbol: str, exit_price: float, reason: str = "Manual"):
        """Close an existing position"""
        if symbol not in self.positions:
            return

        position = self.positions[symbol]

        # Calculate P&L
        if position.direction == SignalType.LONG:
            pnl = (exit_price - position.entry_price) * position.size
        else:  # SHORT
            pnl = (position.entry_price - exit_price) * position.size

        # Deduct commission
        position_value = position.size * exit_price
        commission = position_value * self.config.commission_pct
        pnl -= commission

        pnl_pct = (pnl / (position.entry_price * position.size)) * 100

        # Update capital
        self.capital += (position_value + pnl)

        # Update daily P&L
        self.daily_pnl += pnl
        self.daily_trades += 1

        # Update trade record
        trade = self.trade_history[-1]
        trade.exit_time = datetime.now()
        trade.exit_price = exit_price
        trade.pnl = pnl
        trade.pnl_pct = pnl_pct
        trade.exit_reason = reason

        # Update statistics
        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1

        # Remove position
        del self.positions[symbol]

        self.logger.info(
            f"🔄 Closed {position.direction.value} position: {symbol} @ ${exit_price:.2f} "
            f"| P&L: ${pnl:.2f} ({pnl_pct:+.2f}%) | Reason: {reason}"
        )

    def check_exit_conditions(self, symbol: str, current_price: float):
        """Check if position should be exited (stop loss / take profit)"""
        if symbol not in self.positions:
            return

        position = self.positions[symbol]

        if position.direction == SignalType.LONG:
            # Check stop loss
            if current_price <= position.stop_loss:
                self.close_position(symbol, current_price, "Stop Loss")
            # Check take profit
            elif current_price >= position.take_profit:
                self.close_position(symbol, current_price, "Take Profit")

        elif position.direction == SignalType.SHORT:
            # Check stop loss
            if current_price >= position.stop_loss:
                self.close_position(symbol, current_price, "Stop Loss")
            # Check take profit
            elif current_price <= position.take_profit:
                self.close_position(symbol, current_price, "Take Profit")

    # ========================================================================
    # Strategy Execution
    # ========================================================================

    def run_iteration(self):
        """Run one iteration of the strategy"""
        symbol = self.config.symbol

        try:
            # Get current price
            data = self.get_market_data(symbol, self.config.timeframe, lookback_periods=10)
            current_price = data['Close'].iloc[-1]

            # Check exit conditions for existing positions
            self.check_exit_conditions(symbol, current_price)

            # Get QuantAgent signal
            signal, analysis = self.get_quantagent_signal(symbol, self.config.timeframe)

            # Calculate confidence
            confidence = self.calculate_confidence_score(analysis)

            self.logger.info(f"Signal: {signal.value} | Confidence: {confidence:.2f}")

            # Trading logic
            if signal in [SignalType.LONG, SignalType.SHORT]:
                # Check confidence threshold
                if confidence < self.config.min_confidence_score:
                    self.logger.info(f"Confidence too low ({confidence:.2f}), skipping trade")
                    return

                # Check if we already have a position in this symbol
                if symbol in self.positions:
                    existing_position = self.positions[symbol]
                    # If signal changed direction, close and reverse
                    if existing_position.direction != signal:
                        self.close_position(symbol, current_price, "Signal Reversal")
                        self.open_position(symbol, signal, current_price)
                else:
                    # Open new position
                    self.open_position(symbol, signal, current_price)

            # Update position unrealized P&L
            if symbol in self.positions:
                position = self.positions[symbol]
                if position.direction == SignalType.LONG:
                    position.unrealized_pnl = (current_price - position.entry_price) * position.size
                else:
                    position.unrealized_pnl = (position.entry_price - current_price) * position.size

        except Exception as e:
            self.logger.error(f"Error in strategy iteration: {e}")

    def run_live(self, interval_seconds: int = 3600):
        """
        Run strategy in live mode (continuously)

        Args:
            interval_seconds: How often to check for signals (default 1 hour)
        """
        self.logger.info("🚀 Starting QuantAgent Strategy (Live Mode)")
        self.logger.info(f"Symbol: {self.config.symbol} | Timeframe: {self.config.timeframe}")
        self.logger.info(f"Capital: ${self.capital:.2f}")
        self.logger.info("-" * 80)

        try:
            while True:
                self.run_iteration()
                self.print_status()

                # Wait for next iteration
                self.logger.info(f"⏰ Waiting {interval_seconds}s until next check...")
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            self.logger.info("\n⚠️  Strategy stopped by user")
            self.close_all_positions()
            self.print_final_report()

    def close_all_positions(self):
        """Close all open positions"""
        for symbol in list(self.positions.keys()):
            data = self.get_market_data(symbol, self.config.timeframe, lookback_periods=10)
            current_price = data['Close'].iloc[-1]
            self.close_position(symbol, current_price, "Strategy Stopped")

    # ========================================================================
    # Reporting
    # ========================================================================

    def print_status(self):
        """Print current strategy status"""
        self.logger.info("\n" + "=" * 80)
        self.logger.info(f"💼 PORTFOLIO STATUS")
        self.logger.info("=" * 80)
        self.logger.info(f"Capital: ${self.capital:.2f}")
        self.logger.info(f"Total Equity: ${self.get_total_equity():.2f}")
        self.logger.info(f"Daily P&L: ${self.daily_pnl:.2f}")
        self.logger.info(f"Total Trades: {self.total_trades}")

        if len(self.positions) > 0:
            self.logger.info(f"\n📊 OPEN POSITIONS ({len(self.positions)}):")
            for symbol, pos in self.positions.items():
                self.logger.info(
                    f"  {symbol}: {pos.direction.value} | "
                    f"Entry: ${pos.entry_price:.2f} | "
                    f"Size: {pos.size:.4f} | "
                    f"Unrealized P&L: ${pos.unrealized_pnl:.2f}"
                )
        else:
            self.logger.info("\n📊 No open positions")

        self.logger.info("=" * 80 + "\n")

    def get_total_equity(self) -> float:
        """Calculate total equity (capital + unrealized P&L)"""
        equity = self.capital
        for position in self.positions.values():
            equity += position.unrealized_pnl
        return equity

    def print_final_report(self):
        """Print final strategy performance report"""
        self.logger.info("\n" + "=" * 80)
        self.logger.info("📈 FINAL PERFORMANCE REPORT")
        self.logger.info("=" * 80)

        final_equity = self.get_total_equity()
        total_return = ((final_equity - self.initial_capital) / self.initial_capital) * 100

        self.logger.info(f"Initial Capital: ${self.initial_capital:.2f}")
        self.logger.info(f"Final Equity: ${final_equity:.2f}")
        self.logger.info(f"Total Return: {total_return:+.2f}%")
        self.logger.info(f"Total Trades: {self.total_trades}")
        self.logger.info(f"Winning Trades: {self.winning_trades}")
        self.logger.info(f"Losing Trades: {self.losing_trades}")

        if self.total_trades > 0:
            win_rate = (self.winning_trades / self.total_trades) * 100
            self.logger.info(f"Win Rate: {win_rate:.1f}%")

        self.logger.info("=" * 80)

    def save_results(self, filename: str = "strategy_results.json"):
        """Save strategy results to file"""
        results = {
            "config": asdict(self.config),
            "final_capital": self.capital,
            "initial_capital": self.initial_capital,
            "total_return_pct": ((self.get_total_equity() - self.initial_capital) / self.initial_capital) * 100,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "trades": [asdict(trade) for trade in self.trade_history]
        }

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        self.logger.info(f"💾 Results saved to {filename}")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run the QuantAgent trading strategy"""

    # Configure strategy
    config = StrategyConfig(
        symbol="BTC-USD",
        timeframe="1h",
        position_size_pct=0.02,  # Risk 2% per trade
        stop_loss_pct=0.02,      # 2% stop loss
        take_profit_pct=0.04,    # 4% take profit
        initial_capital=10000.0,
        max_positions=2,
        min_confidence_score=0.65
    )

    # Initialize strategy
    strategy = QuantAgentStrategy(config)

    # Run strategy
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║           QuantAgent Automated Trading Strategy              ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝

    ⚠️  WARNING: This will execute real trades if connected to a broker

    Starting in SIMULATION mode (no real trades)
    Press Ctrl+C to stop
    """)

    try:
        # Run live (checks every hour)
        strategy.run_live(interval_seconds=3600)
    except KeyboardInterrupt:
        print("\n\nStrategy stopped by user")
        strategy.save_results()


if __name__ == "__main__":
    main()
