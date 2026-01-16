"""
Dashboard API Endpoints
=======================

Flask routes for the performance dashboard that expose trade data,
performance metrics, equity curves, and real-time analytics.

Author: QuantAgent Enhanced
"""

from flask import jsonify, request
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

from database import get_database
from performance_analytics import get_analytics


def add_dashboard_routes(app):
    """
    Add dashboard API routes to Flask app

    Call this function from web_interface.py after initializing the app

    Args:
        app: Flask application instance
    """

    db = get_database()
    analytics = get_analytics()


    @app.route("/api/dashboard/metrics", methods=["GET"])
    def get_performance_metrics():
        """
        Get comprehensive performance metrics

        Returns:
        {
            "success": true,
            "data": {
                "basic": {...},
                "advanced": {...},
                "risk": {...},
                "timing": {...}
            },
            "timestamp": "2024-01-15T10:30:00"
        }
        """
        try:
            metrics = analytics.calculate_all_metrics()

            # Remove equity_curve from this endpoint (separate endpoint for that)
            metrics.pop('equity_curve', None)

            return jsonify({
                "success": True,
                "data": metrics,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error calculating metrics: {str(e)}"
            }), 500


    @app.route("/api/dashboard/summary", methods=["GET"])
    def get_performance_summary():
        """
        Get high-level performance summary for quick overview

        Returns:
        {
            "success": true,
            "data": {
                "total_trades": 150,
                "win_rate": 65.5,
                "total_return_pct": 23.4,
                "sharpe_ratio": 1.8,
                "max_drawdown_pct": 8.5,
                "profit_factor": 2.1,
                "current_equity": 12340.50
            }
        }
        """
        try:
            summary = analytics.get_performance_summary()

            return jsonify({
                "success": True,
                "data": summary
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error getting summary: {str(e)}"
            }), 500


    @app.route("/api/dashboard/equity-curve", methods=["GET"])
    def get_equity_curve():
        """
        Get equity curve data for charting

        Query params:
            start_date (optional): ISO format date
            end_date (optional): ISO format date

        Returns:
        {
            "success": true,
            "data": [
                {
                    "timestamp": "2024-01-15T10:30:00",
                    "equity": 10500.50,
                    "pnl": 150.25,
                    "trade_id": 123
                },
                ...
            ]
        }
        """
        try:
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')

            # Get all metrics including equity curve
            metrics = analytics.calculate_all_metrics()
            equity_curve = metrics.get('equity_curve', [])

            # Filter by date range if provided
            if start_date or end_date:
                filtered_curve = []

                for point in equity_curve:
                    timestamp = point['timestamp']
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp)

                    if start_date:
                        start = datetime.fromisoformat(start_date)
                        if timestamp < start:
                            continue

                    if end_date:
                        end = datetime.fromisoformat(end_date)
                        if timestamp > end:
                            continue

                    filtered_curve.append(point)

                equity_curve = filtered_curve

            # Convert datetime objects to ISO strings for JSON serialization
            for point in equity_curve:
                if isinstance(point['timestamp'], datetime):
                    point['timestamp'] = point['timestamp'].isoformat()

            return jsonify({
                "success": True,
                "data": equity_curve
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error getting equity curve: {str(e)}"
            }), 500


    @app.route("/api/dashboard/trades", methods=["GET"])
    def get_trade_history():
        """
        Get paginated trade history with filters

        Query params:
            limit (int): Number of trades to return (default: 50, max: 500)
            offset (int): Offset for pagination (default: 0)
            status (str): Filter by status: 'open', 'closed', 'all' (default: 'all')
            symbol (str): Filter by trading symbol (optional)
            side (str): Filter by side: 'LONG', 'SHORT' (optional)
            start_date (str): ISO format date (optional)
            end_date (str): ISO format date (optional)

        Returns:
        {
            "success": true,
            "data": {
                "trades": [...],
                "total_count": 150,
                "returned_count": 50,
                "offset": 0,
                "has_more": true
            }
        }
        """
        try:
            # Parse query parameters
            limit = min(int(request.args.get('limit', 50)), 500)
            offset = int(request.args.get('offset', 0))
            status = request.args.get('status', 'all')
            symbol = request.args.get('symbol')
            side = request.args.get('side')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')

            # Build filters
            filters = {}
            if status != 'all':
                filters['status'] = status
            if symbol:
                filters['symbol'] = symbol
            if side:
                filters['side'] = side

            # Get trades from database
            trades = db.get_trade_history(
                limit=limit + 1,  # Get one extra to check if there's more
                offset=offset,
                status=status if status != 'all' else None
            )

            # Apply additional filters
            if symbol:
                trades = [t for t in trades if t.get('symbol') == symbol]
            if side:
                trades = [t for t in trades if t.get('side') == side]
            if start_date:
                start = datetime.fromisoformat(start_date)
                trades = [t for t in trades if datetime.fromisoformat(str(t.get('entry_time', ''))) >= start]
            if end_date:
                end = datetime.fromisoformat(end_date)
                trades = [t for t in trades if datetime.fromisoformat(str(t.get('entry_time', ''))) <= end]

            # Check if there are more results
            has_more = len(trades) > limit
            if has_more:
                trades = trades[:limit]

            # Convert datetime objects to strings
            for trade in trades:
                for field in ['entry_time', 'exit_time', 'created_at', 'updated_at']:
                    if field in trade and trade[field]:
                        if isinstance(trade[field], datetime):
                            trade[field] = trade[field].isoformat()

                # Parse metadata JSON if it's a string
                if 'metadata' in trade and isinstance(trade['metadata'], str):
                    try:
                        trade['metadata'] = json.loads(trade['metadata'])
                    except:
                        pass

            return jsonify({
                "success": True,
                "data": {
                    "trades": trades,
                    "returned_count": len(trades),
                    "offset": offset,
                    "has_more": has_more
                }
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error getting trade history: {str(e)}"
            }), 500


    @app.route("/api/dashboard/daily-pnl", methods=["GET"])
    def get_daily_pnl():
        """
        Get daily P&L aggregation

        Query params:
            days (int): Number of days to return (default: 30, max: 365)

        Returns:
        {
            "success": true,
            "data": [
                {
                    "date": "2024-01-15",
                    "pnl": 250.50,
                    "trades": 5,
                    "wins": 3,
                    "losses": 2
                },
                ...
            ]
        }
        """
        try:
            days = min(int(request.args.get('days', 30)), 365)

            daily_pnl = analytics.get_daily_pnl(days=days)

            return jsonify({
                "success": True,
                "data": daily_pnl
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error getting daily P&L: {str(e)}"
            }), 500


    @app.route("/api/dashboard/open-positions", methods=["GET"])
    def get_open_positions():
        """
        Get all currently open positions

        Returns:
        {
            "success": true,
            "data": {
                "positions": [...],
                "total_count": 3,
                "total_unrealized_pnl": 150.25
            }
        }
        """
        try:
            positions = db.get_open_trades()

            # Calculate total unrealized P&L
            total_unrealized = sum(p.get('unrealized_pnl', 0) for p in positions)

            # Convert datetime objects
            for pos in positions:
                for field in ['entry_time', 'created_at', 'updated_at']:
                    if field in pos and pos[field]:
                        if isinstance(pos[field], datetime):
                            pos[field] = pos[field].isoformat()

                # Parse metadata
                if 'metadata' in pos and isinstance(pos['metadata'], str):
                    try:
                        pos['metadata'] = json.loads(pos['metadata'])
                    except:
                        pass

            return jsonify({
                "success": True,
                "data": {
                    "positions": positions,
                    "total_count": len(positions),
                    "total_unrealized_pnl": total_unrealized
                }
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error getting open positions: {str(e)}"
            }), 500


    @app.route("/api/dashboard/trade/<int:trade_id>", methods=["GET"])
    def get_trade_detail(trade_id: int):
        """
        Get detailed information about a specific trade

        Returns:
        {
            "success": true,
            "data": {
                "trade": {...},
                "performance": {
                    "pnl_pct": 2.5,
                    "duration_hours": 24.5,
                    "risk_reward_ratio": 2.0
                }
            }
        }
        """
        try:
            trade = db.get_trade_by_id(trade_id)

            if not trade:
                return jsonify({
                    "success": False,
                    "error": "Trade not found"
                }), 404

            # Convert datetime objects
            for field in ['entry_time', 'exit_time', 'created_at', 'updated_at']:
                if field in trade and trade[field]:
                    if isinstance(trade[field], datetime):
                        trade[field] = trade[field].isoformat()

            # Parse metadata
            if 'metadata' in trade and isinstance(trade['metadata'], str):
                try:
                    trade['metadata'] = json.loads(trade['metadata'])
                except:
                    pass

            # Calculate additional performance metrics
            performance = {}

            if trade.get('pnl') is not None and trade.get('position_size'):
                performance['pnl_pct'] = (trade['pnl'] / (trade['entry_price'] * trade['position_size'])) * 100

            if trade.get('entry_time') and trade.get('exit_time'):
                entry = datetime.fromisoformat(str(trade['entry_time']))
                exit = datetime.fromisoformat(str(trade['exit_time']))
                performance['duration_hours'] = (exit - entry).total_seconds() / 3600

            if trade.get('stop_loss') and trade.get('take_profit') and trade.get('entry_price'):
                risk = abs(trade['entry_price'] - trade['stop_loss'])
                reward = abs(trade['take_profit'] - trade['entry_price'])
                if risk > 0:
                    performance['risk_reward_ratio'] = reward / risk

            return jsonify({
                "success": True,
                "data": {
                    "trade": trade,
                    "performance": performance
                }
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error getting trade detail: {str(e)}"
            }), 500


    @app.route("/api/dashboard/streaks", methods=["GET"])
    def get_streak_stats():
        """
        Get winning/losing streak statistics

        Returns:
        {
            "success": true,
            "data": {
                "current_streak": 5,
                "longest_winning_streak": 8,
                "longest_losing_streak": 3
            }
        }
        """
        try:
            trades = db.get_trade_history(limit=10000, status='closed')
            streaks = analytics.calculate_streak_stats(trades)

            return jsonify({
                "success": True,
                "data": streaks
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error calculating streaks: {str(e)}"
            }), 500


    @app.route("/api/dashboard/recent-alerts", methods=["GET"])
    def get_recent_alerts():
        """
        Get recent system alerts

        Query params:
            limit (int): Number of alerts (default: 20, max: 100)
            severity (str): Filter by severity: 'info', 'warning', 'error' (optional)

        Returns:
        {
            "success": true,
            "data": [
                {
                    "id": 1,
                    "alert_type": "risk_limit",
                    "severity": "warning",
                    "message": "Daily loss limit approaching",
                    "timestamp": "2024-01-15T10:30:00"
                },
                ...
            ]
        }
        """
        try:
            limit = min(int(request.args.get('limit', 20)), 100)
            severity = request.args.get('severity')

            alerts = db.get_recent_alerts(limit=limit)

            # Filter by severity if provided
            if severity:
                alerts = [a for a in alerts if a.get('severity') == severity]

            # Convert timestamps
            for alert in alerts:
                if 'timestamp' in alert and isinstance(alert['timestamp'], datetime):
                    alert['timestamp'] = alert['timestamp'].isoformat()

                # Parse metadata
                if 'metadata' in alert and isinstance(alert['metadata'], str):
                    try:
                        alert['metadata'] = json.loads(alert['metadata'])
                    except:
                        pass

            return jsonify({
                "success": True,
                "data": alerts
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error getting alerts: {str(e)}"
            }), 500


    @app.route("/api/dashboard/stats-by-symbol", methods=["GET"])
    def get_stats_by_symbol():
        """
        Get performance statistics grouped by symbol

        Returns:
        {
            "success": true,
            "data": {
                "BTC/USD": {
                    "total_trades": 50,
                    "win_rate": 68.0,
                    "total_pnl": 1250.50,
                    "avg_pnl": 25.01
                },
                ...
            }
        }
        """
        try:
            trades = db.get_trade_history(limit=10000, status='closed')

            stats_by_symbol = {}

            for trade in trades:
                symbol = trade.get('symbol', 'UNKNOWN')

                if symbol not in stats_by_symbol:
                    stats_by_symbol[symbol] = {
                        'total_trades': 0,
                        'wins': 0,
                        'losses': 0,
                        'total_pnl': 0,
                        'pnls': []
                    }

                stats = stats_by_symbol[symbol]
                pnl = trade.get('pnl', 0)

                stats['total_trades'] += 1
                stats['total_pnl'] += pnl
                stats['pnls'].append(pnl)

                if pnl > 0:
                    stats['wins'] += 1
                else:
                    stats['losses'] += 1

            # Calculate derived metrics
            for symbol, stats in stats_by_symbol.items():
                total = stats['total_trades']
                stats['win_rate'] = (stats['wins'] / total * 100) if total > 0 else 0
                stats['avg_pnl'] = stats['total_pnl'] / total if total > 0 else 0

                # Remove temporary pnls list
                del stats['pnls']

            return jsonify({
                "success": True,
                "data": stats_by_symbol
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error calculating stats by symbol: {str(e)}"
            }), 500


    @app.route("/api/dashboard/stats-by-timeframe", methods=["GET"])
    def get_stats_by_timeframe():
        """
        Get performance statistics grouped by timeframe

        Returns:
        {
            "success": true,
            "data": {
                "1h": {
                    "total_trades": 100,
                    "win_rate": 62.0,
                    "total_pnl": 850.25
                },
                "4h": {...}
            }
        }
        """
        try:
            trades = db.get_trade_history(limit=10000, status='closed')

            stats_by_tf = {}

            for trade in trades:
                # Extract timeframe from metadata
                timeframe = 'UNKNOWN'
                if 'metadata' in trade:
                    metadata = trade['metadata']
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}

                    timeframe = metadata.get('timeframe', 'UNKNOWN')

                if timeframe not in stats_by_tf:
                    stats_by_tf[timeframe] = {
                        'total_trades': 0,
                        'wins': 0,
                        'total_pnl': 0
                    }

                stats = stats_by_tf[timeframe]
                pnl = trade.get('pnl', 0)

                stats['total_trades'] += 1
                stats['total_pnl'] += pnl

                if pnl > 0:
                    stats['wins'] += 1

            # Calculate win rates
            for tf, stats in stats_by_tf.items():
                total = stats['total_trades']
                stats['win_rate'] = (stats['wins'] / total * 100) if total > 0 else 0

            return jsonify({
                "success": True,
                "data": stats_by_tf
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error calculating stats by timeframe: {str(e)}"
            }), 500


# Export for use in main web_interface.py
__all__ = ['add_dashboard_routes']
