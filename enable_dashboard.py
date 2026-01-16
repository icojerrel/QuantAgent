"""
Quick Integration Script for Performance Dashboard
===================================================

Run this to enable the Performance Dashboard in your web_interface.py

Usage:
    python enable_dashboard.py

This will add the dashboard routes and UI while keeping all existing functionality.
"""

import sys
from pathlib import Path


def integrate_dashboard():
    """Integrate performance dashboard into web_interface.py"""

    print("📊 QuantAgent Performance Dashboard Integration")
    print("=" * 60)
    print()

    # Check if files exist
    web_interface_path = Path("web_interface.py")
    if not web_interface_path.exists():
        print("❌ Error: web_interface.py not found!")
        print("   Make sure you're running this from the QuantAgent directory")
        return False

    dashboard_api_path = Path("dashboard_api.py")
    if not dashboard_api_path.exists():
        print("❌ Error: dashboard_api.py not found!")
        return False

    database_path = Path("database.py")
    if not database_path.exists():
        print("❌ Error: database.py not found!")
        return False

    performance_path = Path("performance_analytics.py")
    if not performance_path.exists():
        print("❌ Error: performance_analytics.py not found!")
        return False

    print("✅ Found required files")
    print()

    # Read current web_interface.py
    with open(web_interface_path, 'r') as f:
        content = f.read()

    # Check if already integrated
    if "add_dashboard_routes" in content:
        print("ℹ️  Performance Dashboard already integrated!")
        print()
        print("   Your web interface already has:")
        print("   ✅ Dashboard API endpoints")
        print("   ✅ Performance metrics")
        print("   ✅ Equity curve charts")
        print("   ✅ Trade history table")
        print()
        print("   Visit http://localhost:5000/dashboard to view")
        return True

    print("📝 Adding performance dashboard...")
    print()

    # Find the imports section (after Flask import)
    flask_import = "from flask import Flask, request, jsonify, render_template"
    if flask_import not in content:
        print("❌ Error: Could not find Flask import statement")
        return False

    # Add dashboard import
    dashboard_import = """from flask import Flask, request, jsonify, render_template
from dashboard_api import add_dashboard_routes
"""
    content = content.replace(flask_import, dashboard_import)

    # Find app initialization
    app_init = 'app = Flask(__name__)'
    if app_init not in content:
        print("❌ Error: Could not find app initialization")
        return False

    # Add dashboard routes registration after app creation
    # We need to add it after the analyzer is created
    analyzer_init = "analyzer = WebTradingAnalyzer()"

    if analyzer_init in content:
        # If standard analyzer exists
        dashboard_registration = """analyzer = WebTradingAnalyzer()

# Add Performance Dashboard routes
add_dashboard_routes(app)
"""
        content = content.replace(analyzer_init, dashboard_registration)

    elif "enhanced_analyzer = EnhancedWebTradingAnalyzer" in content:
        # If enhanced analyzer exists
        enhanced_init = "add_enhanced_routes(app, analyzer, enhanced_analyzer)"
        dashboard_registration = """add_enhanced_routes(app, analyzer, enhanced_analyzer)

# Add Performance Dashboard routes
add_dashboard_routes(app)
"""
        content = content.replace(enhanced_init, dashboard_registration)

    else:
        print("❌ Error: Could not find analyzer initialization")
        return False

    # Add dashboard route
    health_route = '@app.route("/health")'
    dashboard_route = '''@app.route("/dashboard")
def dashboard_page():
    """Performance dashboard page"""
    return render_template("dashboard.html")


@app.route("/health")'''
    content = content.replace(health_route, dashboard_route)

    # Write backup
    backup_path = Path("web_interface.py.backup")
    print(f"📦 Creating backup: {backup_path}")
    with open(backup_path, 'w') as f:
        with open(web_interface_path, 'r') as original:
            f.write(original.read())

    # Write updated content
    with open(web_interface_path, 'w') as f:
        f.write(content)

    print("✅ Integration complete!")
    print()
    print("=" * 60)
    print("🎉 Performance Dashboard Activated!")
    print("=" * 60)
    print()
    print("New Features Available:")
    print("  ✅ Real-time Performance Metrics")
    print("  ✅ Equity Curve Chart")
    print("  ✅ Daily P&L Visualization")
    print("  ✅ Trade History Table with Filters")
    print("  ✅ Open Positions Monitor")
    print("  ✅ Performance by Symbol & Timeframe")
    print("  ✅ Auto-refresh every 30 seconds")
    print()
    print("Next Steps:")
    print("  1. Start the server: python web_interface.py")
    print("  2. Visit http://localhost:5000/dashboard")
    print("  3. View your trading performance in real-time!")
    print()
    print("💡 Tip: The dashboard automatically refreshes every 30 seconds")
    print()

    return True


def main():
    """Main entry point"""
    success = integrate_dashboard()

    if not success:
        print()
        print("⚠️  Integration failed. Please check the errors above.")
        sys.exit(1)

    print("🚀 Ready to go! Start with: python web_interface.py")
    print()


if __name__ == "__main__":
    main()
