"""
Database Module for QuantAgent
==============================

Persistent storage for trades, performance metrics, and system state.

Uses SQLite for simplicity and portability.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class QuantAgentDatabase:
    """Database manager for QuantAgent"""

    def __init__(self, db_path: str = "data/quantagent.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_time TIMESTAMP NOT NULL,
                    exit_time TIMESTAMP,
                    symbol VARCHAR(20) NOT NULL,
                    direction VARCHAR(10) NOT NULL,
                    entry_price DECIMAL(20, 8) NOT NULL,
                    exit_price DECIMAL(20, 8),
                    size DECIMAL(20, 8) NOT NULL,
                    leverage DECIMAL(5, 2) DEFAULT 1.0,
                    pnl DECIMAL(20, 8),
                    pnl_pct DECIMAL(10, 4),
                    exit_reason VARCHAR(100),
                    status VARCHAR(20) DEFAULT 'open',
                    stop_loss DECIMAL(20, 8),
                    take_profit DECIMAL(20, 8),
                    commission DECIMAL(20, 8),
                    notes TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Performance snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    total_equity DECIMAL(20, 2) NOT NULL,
                    cash_balance DECIMAL(20, 2) NOT NULL,
                    open_positions_value DECIMAL(20, 2),
                    daily_pnl DECIMAL(20, 2),
                    total_pnl DECIMAL(20, 2),
                    total_trades INTEGER,
                    winning_trades INTEGER,
                    losing_trades INTEGER,
                    win_rate DECIMAL(5, 2),
                    sharpe_ratio DECIMAL(10, 4),
                    max_drawdown_pct DECIMAL(10, 4),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # System state table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_state (
                    key VARCHAR(100) PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Signals table (for manual trading mode)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    symbol VARCHAR(20) NOT NULL,
                    signal VARCHAR(10) NOT NULL,
                    confidence DECIMAL(5, 4),
                    signal_strength VARCHAR(20),
                    recommended_leverage DECIMAL(5, 2),
                    stop_loss DECIMAL(20, 8),
                    take_profit DECIMAL(20, 8),
                    position_size_pct DECIMAL(10, 4),
                    status VARCHAR(20) DEFAULT 'pending',
                    reasoning TEXT,
                    metadata TEXT,
                    approved_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    alert_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    is_read BOOLEAN DEFAULT 0,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_snapshots(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_is_read ON alerts(is_read)")

            logger.info("Database initialized successfully")

    # ========================================================================
    # Trade Management
    # ========================================================================

    def insert_trade(self, trade_data: Dict) -> int:
        """Insert a new trade"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Serialize metadata if present
            metadata = trade_data.get('metadata')
            if metadata and isinstance(metadata, dict):
                metadata = json.dumps(metadata)

            cursor.execute("""
                INSERT INTO trades (
                    entry_time, symbol, direction, entry_price, size, leverage,
                    stop_loss, take_profit, status, notes, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_data.get('entry_time', datetime.now()),
                trade_data['symbol'],
                trade_data['direction'],
                trade_data['entry_price'],
                trade_data['size'],
                trade_data.get('leverage', 1.0),
                trade_data.get('stop_loss'),
                trade_data.get('take_profit'),
                trade_data.get('status', 'open'),
                trade_data.get('notes'),
                metadata
            ))

            trade_id = cursor.lastrowid
            logger.info(f"Inserted trade {trade_id}: {trade_data['direction']} {trade_data['symbol']}")
            return trade_id

    def update_trade(self, trade_id: int, updates: Dict):
        """Update an existing trade"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Serialize metadata if present
            if 'metadata' in updates and isinstance(updates['metadata'], dict):
                updates['metadata'] = json.dumps(updates['metadata'])

            # Build SET clause
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [trade_id]

            cursor.execute(f"""
                UPDATE trades SET {set_clause} WHERE id = ?
            """, values)

            logger.info(f"Updated trade {trade_id}")

    def close_trade(self, trade_id: int, exit_price: float, exit_reason: str,
                    pnl: float, pnl_pct: float, commission: float = 0):
        """Close a trade"""
        self.update_trade(trade_id, {
            'exit_time': datetime.now(),
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'commission': commission,
            'status': 'closed'
        })

    def get_trade(self, trade_id: int) -> Optional[Dict]:
        """Get a single trade by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
            row = cursor.fetchone()

            if row:
                trade = dict(row)
                if trade.get('metadata'):
                    try:
                        trade['metadata'] = json.loads(trade['metadata'])
                    except:
                        pass
                return trade
            return None

    def get_open_trades(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open trades"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if symbol:
                cursor.execute("""
                    SELECT * FROM trades
                    WHERE status = 'open' AND symbol = ?
                    ORDER BY entry_time DESC
                """, (symbol,))
            else:
                cursor.execute("""
                    SELECT * FROM trades
                    WHERE status = 'open'
                    ORDER BY entry_time DESC
                """)

            trades = []
            for row in cursor.fetchall():
                trade = dict(row)
                if trade.get('metadata'):
                    try:
                        trade['metadata'] = json.loads(trade['metadata'])
                    except:
                        pass
                trades.append(trade)

            return trades

    def get_trade_history(self, limit: int = 100, offset: int = 0,
                         symbol: Optional[str] = None,
                         status: Optional[str] = None) -> List[Dict]:
        """Get trade history with pagination"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM trades WHERE 1=1"
            params = []

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY entry_time DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)

            trades = []
            for row in cursor.fetchall():
                trade = dict(row)
                if trade.get('metadata'):
                    try:
                        trade['metadata'] = json.loads(trade['metadata'])
                    except:
                        pass
                trades.append(trade)

            return trades

    def get_trades_count(self, symbol: Optional[str] = None,
                        status: Optional[str] = None) -> int:
        """Get total count of trades"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT COUNT(*) as count FROM trades WHERE 1=1"
            params = []

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

            if status:
                query += " AND status = ?"
                params.append(status)

            cursor.execute(query, params)
            return cursor.fetchone()['count']

    # ========================================================================
    # Performance Tracking
    # ========================================================================

    def insert_performance_snapshot(self, snapshot: Dict):
        """Insert a performance snapshot"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO performance_snapshots (
                    timestamp, total_equity, cash_balance, open_positions_value,
                    daily_pnl, total_pnl, total_trades, winning_trades, losing_trades,
                    win_rate, sharpe_ratio, max_drawdown_pct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.get('timestamp', datetime.now()),
                snapshot['total_equity'],
                snapshot['cash_balance'],
                snapshot.get('open_positions_value', 0),
                snapshot.get('daily_pnl', 0),
                snapshot.get('total_pnl', 0),
                snapshot.get('total_trades', 0),
                snapshot.get('winning_trades', 0),
                snapshot.get('losing_trades', 0),
                snapshot.get('win_rate', 0),
                snapshot.get('sharpe_ratio', 0),
                snapshot.get('max_drawdown_pct', 0)
            ))

    def get_performance_history(self, days: int = 30) -> List[Dict]:
        """Get performance history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM performance_snapshots
                WHERE timestamp >= datetime('now', '-' || ? || ' days')
                ORDER BY timestamp ASC
            """, (days,))

            return [dict(row) for row in cursor.fetchall()]

    def get_latest_performance(self) -> Optional[Dict]:
        """Get latest performance snapshot"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM performance_snapshots
                ORDER BY timestamp DESC
                LIMIT 1
            """)

            row = cursor.fetchone()
            return dict(row) if row else None

    # ========================================================================
    # System State
    # ========================================================================

    def set_state(self, key: str, value: any):
        """Set system state"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if not isinstance(value, str):
                value = json.dumps(value)

            cursor.execute("""
                INSERT OR REPLACE INTO system_state (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))

    def get_state(self, key: str, default=None) -> any:
        """Get system state"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT value FROM system_state WHERE key = ?", (key,))
            row = cursor.fetchone()

            if row:
                try:
                    return json.loads(row['value'])
                except:
                    return row['value']
            return default

    # ========================================================================
    # Signals (for manual trading mode)
    # ========================================================================

    def insert_signal(self, signal_data: Dict) -> int:
        """Insert a new signal"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            metadata = signal_data.get('metadata')
            if metadata and isinstance(metadata, dict):
                metadata = json.dumps(metadata)

            cursor.execute("""
                INSERT INTO signals (
                    timestamp, symbol, signal, confidence, signal_strength,
                    recommended_leverage, stop_loss, take_profit, position_size_pct,
                    reasoning, metadata, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_data.get('timestamp', datetime.now()),
                signal_data['symbol'],
                signal_data['signal'],
                signal_data.get('confidence'),
                signal_data.get('signal_strength'),
                signal_data.get('recommended_leverage'),
                signal_data.get('stop_loss'),
                signal_data.get('take_profit'),
                signal_data.get('position_size_pct'),
                signal_data.get('reasoning'),
                metadata,
                signal_data.get('status', 'pending')
            ))

            return cursor.lastrowid

    def get_pending_signals(self, limit: int = 10) -> List[Dict]:
        """Get pending signals for approval"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM signals
                WHERE status = 'pending'
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            signals = []
            for row in cursor.fetchall():
                signal = dict(row)
                if signal.get('metadata'):
                    try:
                        signal['metadata'] = json.loads(signal['metadata'])
                    except:
                        pass
                signals.append(signal)

            return signals

    def approve_signal(self, signal_id: int):
        """Approve a signal"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE signals
                SET status = 'approved', approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (signal_id,))

    def reject_signal(self, signal_id: int):
        """Reject a signal"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE signals SET status = 'rejected' WHERE id = ?
            """, (signal_id,))

    # ========================================================================
    # Alerts
    # ========================================================================

    def insert_alert(self, alert_type: str, severity: str, message: str,
                    metadata: Optional[Dict] = None):
        """Insert an alert"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if metadata:
                metadata = json.dumps(metadata)

            cursor.execute("""
                INSERT INTO alerts (timestamp, alert_type, severity, message, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (datetime.now(), alert_type, severity, message, metadata))

    def get_unread_alerts(self) -> List[Dict]:
        """Get unread alerts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM alerts
                WHERE is_read = 0
                ORDER BY timestamp DESC
            """)

            alerts = []
            for row in cursor.fetchall():
                alert = dict(row)
                if alert.get('metadata'):
                    try:
                        alert['metadata'] = json.loads(alert['metadata'])
                    except:
                        pass
                alerts.append(alert)

            return alerts

    def mark_alert_read(self, alert_id: int):
        """Mark alert as read"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE alerts SET is_read = 1 WHERE id = ?", (alert_id,))


# Singleton instance
_db_instance = None

def get_database() -> QuantAgentDatabase:
    """Get database singleton instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = QuantAgentDatabase()
    return _db_instance
