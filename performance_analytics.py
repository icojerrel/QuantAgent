"""
Performance Analytics Module
============================

Calculates comprehensive trading performance metrics.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from database import get_database


class PerformanceAnalytics:
    """Calculate and track trading performance metrics"""

    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.db = get_database()

    def calculate_all_metrics(self) -> Dict:
        """Calculate all performance metrics"""
        trades = self.db.get_trade_history(limit=10000, status='closed')

        if not trades:
            return self._empty_metrics()

        return {
            'basic': self._calculate_basic_metrics(trades),
            'advanced': self._calculate_advanced_metrics(trades),
            'risk': self._calculate_risk_metrics(trades),
            'timing': self._calculate_timing_metrics(trades),
            'equity_curve': self._calculate_equity_curve(trades)
        }

    def _empty_metrics(self) -> Dict:
        """Return empty metrics structure"""
        return {
            'basic': {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_return_pct': 0
            },
            'advanced': {
                'profit_factor': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'largest_win': 0,
                'largest_loss': 0,
                'avg_win_pct': 0,
                'avg_loss_pct': 0
            },
            'risk': {
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'calmar_ratio': 0,
                'max_drawdown': 0,
                'max_drawdown_pct': 0,
                'recovery_factor': 0
            },
            'timing': {
                'avg_trade_duration_hours': 0,
                'avg_winning_trade_duration': 0,
                'avg_losing_trade_duration': 0
            },
            'equity_curve': []
        }

    def _calculate_basic_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate basic trading metrics"""
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) <= 0]

        total_pnl = sum(t.get('pnl', 0) for t in trades)
        total_return_pct = (total_pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0

        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0,
            'total_pnl': total_pnl,
            'total_return_pct': total_return_pct,
            'current_equity': self.initial_capital + total_pnl
        }

    def _calculate_advanced_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate advanced trading metrics"""
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) <= 0]

        # Profit factor
        gross_profit = sum(t.get('pnl', 0) for t in winning_trades)
        gross_loss = abs(sum(t.get('pnl', 0) for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # Average wins/losses
        avg_win = np.mean([t.get('pnl', 0) for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.get('pnl', 0) for t in losing_trades]) if losing_trades else 0

        # Percentage wins/losses
        avg_win_pct = np.mean([t.get('pnl_pct', 0) for t in winning_trades]) if winning_trades else 0
        avg_loss_pct = np.mean([t.get('pnl_pct', 0) for t in losing_trades]) if losing_trades else 0

        # Largest wins/losses
        largest_win = max([t.get('pnl', 0) for t in trades]) if trades else 0
        largest_loss = min([t.get('pnl', 0) for t in trades]) if trades else 0

        # Payoff ratio
        payoff_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0

        # Expectancy
        win_rate = len(winning_trades) / len(trades) if trades else 0
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))

        return {
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'avg_win_pct': avg_win_pct,
            'avg_loss_pct': avg_loss_pct,
            'payoff_ratio': payoff_ratio,
            'expectancy': expectancy,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss
        }

    def _calculate_risk_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate risk-adjusted metrics"""
        # Build equity curve
        equity_curve = self._calculate_equity_curve(trades)

        if len(equity_curve) < 2:
            return {
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'calmar_ratio': 0,
                'max_drawdown': 0,
                'max_drawdown_pct': 0,
                'recovery_factor': 0
            }

        equities = [point['equity'] for point in equity_curve]
        returns = np.diff(equities) / equities[:-1]

        # Sharpe Ratio
        if len(returns) > 1 and np.std(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)  # Annualized
        else:
            sharpe_ratio = 0

        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and np.std(downside_returns) > 0:
            sortino_ratio = np.mean(returns) / np.std(downside_returns) * np.sqrt(252)
        else:
            sortino_ratio = 0

        # Max Drawdown
        peak = equities[0]
        max_dd = 0
        max_dd_pct = 0

        for equity in equities:
            if equity > peak:
                peak = equity
            dd = peak - equity
            dd_pct = (dd / peak * 100) if peak > 0 else 0

            if dd > max_dd:
                max_dd = dd
                max_dd_pct = dd_pct

        # Calmar Ratio (return / max drawdown)
        total_return = equities[-1] - equities[0]
        calmar_ratio = (total_return / max_dd) if max_dd > 0 else 0

        # Recovery Factor
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        recovery_factor = total_pnl / max_dd if max_dd > 0 else 0

        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'max_drawdown': max_dd,
            'max_drawdown_pct': max_dd_pct,
            'recovery_factor': recovery_factor
        }

    def _calculate_timing_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate trade timing metrics"""
        durations = []
        winning_durations = []
        losing_durations = []

        for trade in trades:
            if trade.get('entry_time') and trade.get('exit_time'):
                entry = datetime.fromisoformat(str(trade['entry_time']))
                exit = datetime.fromisoformat(str(trade['exit_time']))
                duration_hours = (exit - entry).total_seconds() / 3600

                durations.append(duration_hours)

                if trade.get('pnl', 0) > 0:
                    winning_durations.append(duration_hours)
                else:
                    losing_durations.append(duration_hours)

        return {
            'avg_trade_duration_hours': np.mean(durations) if durations else 0,
            'avg_winning_trade_duration': np.mean(winning_durations) if winning_durations else 0,
            'avg_losing_trade_duration': np.mean(losing_durations) if losing_durations else 0,
            'median_trade_duration': np.median(durations) if durations else 0
        }

    def _calculate_equity_curve(self, trades: List[Dict]) -> List[Dict]:
        """Calculate equity curve over time"""
        equity_curve = [{'timestamp': datetime.now(), 'equity': self.initial_capital, 'pnl': 0}]

        running_equity = self.initial_capital

        # Sort trades by exit time
        sorted_trades = sorted(
            [t for t in trades if t.get('exit_time')],
            key=lambda x: x['exit_time']
        )

        for trade in sorted_trades:
            running_equity += trade.get('pnl', 0)
            equity_curve.append({
                'timestamp': trade['exit_time'],
                'equity': running_equity,
                'pnl': trade.get('pnl', 0),
                'trade_id': trade.get('id')
            })

        return equity_curve

    def get_daily_pnl(self, days: int = 30) -> List[Dict]:
        """Calculate daily P&L"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        trades = self.db.get_trade_history(limit=10000, status='closed')

        # Group by day
        daily_pnl = {}

        for trade in trades:
            if not trade.get('exit_time'):
                continue

            exit_time = datetime.fromisoformat(str(trade['exit_time']))

            if exit_time < start_date:
                continue

            date_key = exit_time.date().isoformat()

            if date_key not in daily_pnl:
                daily_pnl[date_key] = {
                    'date': date_key,
                    'pnl': 0,
                    'trades': 0,
                    'wins': 0,
                    'losses': 0
                }

            daily_pnl[date_key]['pnl'] += trade.get('pnl', 0)
            daily_pnl[date_key]['trades'] += 1

            if trade.get('pnl', 0) > 0:
                daily_pnl[date_key]['wins'] += 1
            else:
                daily_pnl[date_key]['losses'] += 1

        # Convert to list and sort
        result = list(daily_pnl.values())
        result.sort(key=lambda x: x['date'])

        return result

    def get_performance_summary(self) -> Dict:
        """Get high-level performance summary"""
        metrics = self.calculate_all_metrics()

        return {
            'total_trades': metrics['basic']['total_trades'],
            'win_rate': metrics['basic']['win_rate'],
            'total_return_pct': metrics['basic']['total_return_pct'],
            'sharpe_ratio': metrics['risk']['sharpe_ratio'],
            'max_drawdown_pct': metrics['risk']['max_drawdown_pct'],
            'profit_factor': metrics['advanced']['profit_factor'],
            'current_equity': metrics['basic'].get('current_equity', self.initial_capital)
        }

    def calculate_streak_stats(self, trades: List[Dict]) -> Dict:
        """Calculate winning/losing streak statistics"""
        if not trades:
            return {
                'current_streak': 0,
                'longest_winning_streak': 0,
                'longest_losing_streak': 0
            }

        # Sort by exit time
        sorted_trades = sorted(
            [t for t in trades if t.get('exit_time')],
            key=lambda x: x['exit_time']
        )

        current_streak = 0
        longest_winning_streak = 0
        longest_losing_streak = 0
        current_winning_streak = 0
        current_losing_streak = 0

        for trade in sorted_trades:
            pnl = trade.get('pnl', 0)

            if pnl > 0:
                current_winning_streak += 1
                current_losing_streak = 0
                current_streak = current_winning_streak
                longest_winning_streak = max(longest_winning_streak, current_winning_streak)
            else:
                current_losing_streak += 1
                current_winning_streak = 0
                current_streak = -current_losing_streak
                longest_losing_streak = max(longest_losing_streak, current_losing_streak)

        return {
            'current_streak': current_streak,
            'longest_winning_streak': longest_winning_streak,
            'longest_losing_streak': longest_losing_streak
        }


# Singleton instance
_analytics_instance = None

def get_analytics(initial_capital: float = 10000.0) -> PerformanceAnalytics:
    """Get analytics singleton"""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = PerformanceAnalytics(initial_capital)
    return _analytics_instance
