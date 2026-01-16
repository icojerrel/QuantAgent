# Performance Dashboard

**Real-time trading performance visualization and analytics**

The QuantAgent Performance Dashboard provides comprehensive insights into your trading activity, from equity curves to trade-by-trade analysis.

## Features

### 📊 Key Metrics Cards
- **Current Equity**: Real-time account balance
- **Total Return**: Percentage gain/loss from initial capital
- **Win Rate**: Percentage of profitable trades
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest peak-to-trough decline
- **Profit Factor**: Ratio of gross profit to gross loss

### 📈 Equity Curve
Interactive chart showing your account equity over time:
- Visualize account growth/decline
- Identify periods of outperformance
- Spot drawdown periods
- Hover for detailed information

### 💰 Daily P&L
Bar chart showing daily profit/loss for the last 30 days:
- Green bars: Profitable days
- Red bars: Losing days
- Quick visual assessment of consistency

### 🎯 Performance by Symbol
See which trading pairs are most profitable:
- Win rate comparison across symbols
- Identify your strongest markets
- Optimize symbol selection

### 📍 Open Positions Monitor
Real-time view of active trades:
- Entry price, current price, unrealized P&L
- Stop loss and take profit levels
- Position size and leverage
- Total unrealized P&L across all positions

### 📜 Trade History Table
Comprehensive trade log with filters:
- Filter by status (open/closed/all)
- Filter by side (long/short)
- Adjustable result limit (25-200 trades)
- Click any trade for detailed view
- Sortable columns

## Installation

### Quick Setup (Recommended)

```bash
# One-command installation
python enable_dashboard.py
```

This script will:
1. ✅ Check for required files
2. ✅ Backup your current `web_interface.py`
3. ✅ Add dashboard routes and imports
4. ✅ Register the dashboard page

### Manual Setup

If you prefer manual integration:

1. **Import dashboard routes** in `web_interface.py`:
```python
from dashboard_api import add_dashboard_routes
```

2. **Register routes** after creating the Flask app:
```python
app = Flask(__name__)
analyzer = WebTradingAnalyzer()

# Add dashboard routes
add_dashboard_routes(app)
```

3. **Add dashboard page route**:
```python
@app.route("/dashboard")
def dashboard_page():
    """Performance dashboard page"""
    return render_template("dashboard.html")
```

## Usage

### Starting the Dashboard

```bash
# Start the web interface
python web_interface.py

# Visit in your browser
# http://localhost:5000/dashboard
```

### Navigating the Dashboard

1. **From Analysis Page**: Click "📊 Dashboard" in the header
2. **From Dashboard**: Click "🔙 Back to Analysis" to return
3. **Refresh**: Click "🔄 Refresh" to manually update all data

### Filtering Trade History

Use the filters to narrow down your view:

**Status Filter**:
- `All Trades`: Show both open and closed positions
- `Closed Only`: Show only completed trades (default)
- `Open Only`: Show only active positions

**Side Filter**:
- `All Sides`: Show both longs and shorts
- `Long Only`: Show only long positions
- `Short Only`: Show only short positions

**Limit**:
- Choose how many trades to display (25/50/100/200)

### Auto-Refresh

The dashboard automatically refreshes **every 30 seconds** to show the latest data without manual intervention.

## API Endpoints

The dashboard exposes several REST API endpoints you can use programmatically:

### Performance Metrics

```bash
GET /api/dashboard/metrics
```

Returns comprehensive performance statistics:
```json
{
  "success": true,
  "data": {
    "basic": {
      "total_trades": 150,
      "winning_trades": 98,
      "losing_trades": 52,
      "win_rate": 65.33,
      "total_pnl": 2340.50,
      "total_return_pct": 23.41,
      "current_equity": 12340.50
    },
    "advanced": {
      "profit_factor": 2.15,
      "avg_win": 45.20,
      "avg_loss": -21.30,
      "expectancy": 15.60
    },
    "risk": {
      "sharpe_ratio": 1.82,
      "sortino_ratio": 2.45,
      "max_drawdown_pct": 8.5
    }
  }
}
```

### Performance Summary

```bash
GET /api/dashboard/summary
```

Quick overview of key metrics:
```json
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
```

### Equity Curve

```bash
GET /api/dashboard/equity-curve
GET /api/dashboard/equity-curve?start_date=2024-01-01&end_date=2024-12-31
```

Returns equity curve data points:
```json
{
  "success": true,
  "data": [
    {
      "timestamp": "2024-01-15T10:30:00",
      "equity": 10500.50,
      "pnl": 150.25,
      "trade_id": 123
    }
  ]
}
```

### Trade History

```bash
GET /api/dashboard/trades?limit=50&status=closed&side=LONG
```

Parameters:
- `limit`: Number of trades (default: 50, max: 500)
- `offset`: Pagination offset (default: 0)
- `status`: `open`, `closed`, or `all` (default: all)
- `symbol`: Filter by trading pair (optional)
- `side`: `LONG` or `SHORT` (optional)
- `start_date`: ISO format date (optional)
- `end_date`: ISO format date (optional)

Returns:
```json
{
  "success": true,
  "data": {
    "trades": [...],
    "returned_count": 50,
    "offset": 0,
    "has_more": true
  }
}
```

### Daily P&L

```bash
GET /api/dashboard/daily-pnl?days=30
```

Returns daily aggregated P&L:
```json
{
  "success": true,
  "data": [
    {
      "date": "2024-01-15",
      "pnl": 250.50,
      "trades": 5,
      "wins": 3,
      "losses": 2
    }
  ]
}
```

### Open Positions

```bash
GET /api/dashboard/open-positions
```

Returns all currently active trades:
```json
{
  "success": true,
  "data": {
    "positions": [...],
    "total_count": 3,
    "total_unrealized_pnl": 150.25
  }
}
```

### Trade Detail

```bash
GET /api/dashboard/trade/<trade_id>
```

Get detailed information about a specific trade:
```json
{
  "success": true,
  "data": {
    "trade": {
      "id": 123,
      "symbol": "BTC/USD",
      "side": "LONG",
      "entry_price": 45000.00,
      "exit_price": 46500.00,
      "pnl": 300.00
    },
    "performance": {
      "pnl_pct": 3.33,
      "duration_hours": 24.5,
      "risk_reward_ratio": 2.0
    }
  }
}
```

### Additional Endpoints

**Streak Statistics**:
```bash
GET /api/dashboard/streaks
```

**Recent Alerts**:
```bash
GET /api/dashboard/recent-alerts?limit=20&severity=warning
```

**Performance by Symbol**:
```bash
GET /api/dashboard/stats-by-symbol
```

**Performance by Timeframe**:
```bash
GET /api/dashboard/stats-by-timeframe
```

## Database Schema

The dashboard uses SQLite for persistence. See `database.py` for the full schema.

### Key Tables

**trades**: All trade records
- `id`, `symbol`, `side`, `entry_price`, `exit_price`, `pnl`, `status`
- `position_size`, `leverage`, `stop_loss`, `take_profit`
- `entry_time`, `exit_time`, `metadata`

**performance_snapshots**: Periodic performance captures
- `equity`, `total_pnl`, `win_rate`, `sharpe_ratio`
- `max_drawdown_pct`, `total_trades`

**system_state**: Current system configuration
- `mode`, `active_settings`, `last_trade_time`

**signals**: Trading signal history (for manual mode)

**alerts**: System notifications and warnings

## Performance Metrics Explained

### Basic Metrics

**Win Rate**: Percentage of trades that were profitable
- Formula: `(winning_trades / total_trades) * 100`
- Good: >60%
- Excellent: >70%

**Total Return %**: Overall account growth/decline
- Formula: `(total_pnl / initial_capital) * 100`
- Measures absolute performance

**Current Equity**: Latest account balance
- Formula: `initial_capital + total_pnl`

### Advanced Metrics

**Profit Factor**: Ratio of gross profit to gross loss
- Formula: `gross_profit / abs(gross_loss)`
- >1.0: Profitable overall
- >2.0: Strong performance
- >3.0: Exceptional

**Expectancy**: Average expected profit per trade
- Formula: `(win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))`
- Positive: System has edge
- Higher is better

**Payoff Ratio**: Average win vs average loss size
- Formula: `avg_win / abs(avg_loss)`
- >1.0: Wins larger than losses
- >2.0: Strong risk/reward

### Risk Metrics

**Sharpe Ratio**: Risk-adjusted returns
- Measures return per unit of risk
- >1.0: Good
- >2.0: Very good
- >3.0: Excellent

**Sortino Ratio**: Downside-risk-adjusted returns
- Similar to Sharpe, but only penalizes downside volatility
- Generally higher than Sharpe

**Calmar Ratio**: Return vs max drawdown
- Formula: `total_return / max_drawdown`
- Higher is better
- Shows recovery efficiency

**Max Drawdown**: Largest peak-to-trough decline
- Critical risk metric
- <10%: Conservative
- 10-20%: Moderate
- >20%: Aggressive

**Recovery Factor**: Profit relative to max drawdown
- Formula: `total_pnl / max_drawdown`
- >2.0: Good recovery capability

### Timing Metrics

**Average Trade Duration**: Mean time in position
- Helps identify holding period patterns
- Compare winners vs losers for insights

## Troubleshooting

### Dashboard Not Loading

**Check server logs**:
```bash
python web_interface.py
```

Look for errors related to:
- Database connection
- Missing dependencies
- Port conflicts

### No Data Showing

**Verify database has trades**:
```python
from database import get_database
db = get_database()
trades = db.get_trade_history(limit=10)
print(f"Found {len(trades)} trades")
```

### Charts Not Rendering

**Ensure Chart.js is loading**:
- Check browser console for errors
- Verify internet connection (Chart.js loads from CDN)
- Try hard refresh: `Ctrl+F5` (Windows) or `Cmd+Shift+R` (Mac)

### API Errors

**Check endpoint responses**:
```bash
curl http://localhost:5000/api/dashboard/summary
```

If you get 500 errors, check server logs for details.

## Customization

### Changing Auto-Refresh Interval

Edit `templates/dashboard.html`:
```javascript
// Change from 30 seconds to 60 seconds
setInterval(refreshDashboard, 60000);  // 60000ms = 60s
```

### Adding Custom Metrics

1. Add calculation to `performance_analytics.py`
2. Expose via API in `dashboard_api.py`
3. Display in `templates/dashboard.html`

### Styling

All styles are in `<style>` tag in `dashboard.html`. Customize:
- Colors: Change gradient values
- Card layout: Modify `.metrics-grid`
- Chart height: Adjust `.chart-wrapper` height

## Integration with Trading Bots

The dashboard can track trades from automated strategies:

```python
from database import get_database

db = get_database()

# When opening a trade
trade_id = db.insert_trade({
    'symbol': 'BTC/USD',
    'side': 'LONG',
    'entry_price': 45000.00,
    'position_size': 0.1,
    'leverage': 2.0,
    'stop_loss': 44000.00,
    'take_profit': 47000.00,
    'metadata': {'strategy': 'momentum', 'timeframe': '1h'}
})

# When closing a trade
db.close_trade(
    trade_id=trade_id,
    exit_price=46500.00,
    pnl=150.00,
    pnl_pct=3.33
)
```

The dashboard will automatically show this trade!

## Best Practices

1. **Regular Monitoring**: Check dashboard daily to track performance
2. **Set Alerts**: Use the alerts system for important events
3. **Analyze Patterns**: Review symbol and timeframe statistics weekly
4. **Track Equity Curve**: Watch for changes in trajectory
5. **Monitor Drawdowns**: Act if drawdown exceeds your risk tolerance
6. **Review Losing Trades**: Learn from mistakes to improve strategy

## Next Steps

- [ ] Add **real-time position updates** via WebSocket
- [ ] Implement **strategy comparison** dashboard
- [ ] Add **Monte Carlo simulations** for risk analysis
- [ ] Create **PDF export** for performance reports
- [ ] Build **mobile-responsive** version
- [ ] Add **multi-account** support

## Support

For issues or questions:
1. Check this documentation
2. Review `database.py` and `dashboard_api.py` code
3. Open an issue on GitHub

---

**Built with ❤️ for QuantAgent traders**
