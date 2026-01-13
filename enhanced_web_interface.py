"""
Enhanced Web Interface with Hybrid Mode, Leverage, and Advanced Features
=========================================================================

Extends the base web_interface.py with:
- Hybrid Mode (QuantAgent + Multi-Timeframe Validation)
- Confidence-Based Leverage Scaling
- Signal Strength Classification
- Trade Cooldown Mechanism
- Performance Metrics Dashboard

Author: QuantAgent Enhanced
"""

import json
from pathlib import Path
from typing import Dict, Optional
from enum import Enum

from flask import jsonify
from hybrid_system import (
    HybridTradingSystem,
    HybridConfig,
    TradingMode,
    SignalStrength
)


class AnalysisMode(Enum):
    """Analysis mode selection"""
    STANDARD = "standard"  # Original 4-agent QuantAgent
    HYBRID = "hybrid"      # Hybrid with MTF validation


class EnhancedWebTradingAnalyzer:
    """
    Enhanced analyzer with hybrid mode support
    """

    def __init__(self, base_analyzer):
        """
        Initialize enhanced analyzer

        Args:
            base_analyzer: The original WebTradingAnalyzer instance
        """
        self.base_analyzer = base_analyzer
        self.settings_file = Path("data/enhanced_settings.json")

        # Default settings
        self.settings = {
            "analysis_mode": AnalysisMode.STANDARD.value,
            "trading_mode": TradingMode.BALANCED.value,
            "max_leverage": 3.0,
            "require_both_systems_agree": True,
            "min_confidence_threshold": 0.70,
            "enable_cooldown": True,
            "cooldown_bars": 3,
            "min_signal_strength": SignalStrength.MODERATE.value,
            "confidence_leverage_scaling": True,
            "base_position_size_pct": 0.02,
            "base_stop_loss_pct": 0.02,
            "base_take_profit_pct": 0.04,
        }

        # Load persisted settings
        self.load_settings()

        # Initialize hybrid system
        self.hybrid_system = None
        self._init_hybrid_system()

        # Cooldown state
        self.cooldown_remaining = 0
        self.last_trade_time = None

    def _init_hybrid_system(self):
        """Initialize hybrid trading system with current settings"""
        config = HybridConfig(
            mode=TradingMode(self.settings["trading_mode"]),
            require_both_systems_agree=self.settings["require_both_systems_agree"],
            min_confidence_threshold=self.settings["min_confidence_threshold"],
            max_leverage=self.settings["max_leverage"],
            base_leverage=1.0,
            confidence_leverage_scaling=self.settings["confidence_leverage_scaling"],
            base_position_size_pct=self.settings["base_position_size_pct"],
            base_stop_loss_pct=self.settings["base_stop_loss_pct"],
            base_take_profit_pct=self.settings["base_take_profit_pct"],
            enable_cooldown=self.settings["enable_cooldown"],
            cooldown_bars=self.settings["cooldown_bars"],
        )

        self.hybrid_system = HybridTradingSystem(config)

    def load_settings(self):
        """Load settings from file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
            except Exception as e:
                print(f"Warning: Could not load settings: {e}")

    def save_settings(self):
        """Save settings to file"""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def update_settings(self, new_settings: Dict) -> Dict:
        """
        Update enhanced settings

        Returns:
            {"success": bool, "message": str}
        """
        try:
            # Validate settings
            if "trading_mode" in new_settings:
                if new_settings["trading_mode"] not in [m.value for m in TradingMode]:
                    return {"success": False, "message": "Invalid trading mode"}

            if "analysis_mode" in new_settings:
                if new_settings["analysis_mode"] not in [m.value for m in AnalysisMode]:
                    return {"success": False, "message": "Invalid analysis mode"}

            if "max_leverage" in new_settings:
                if not (1.0 <= new_settings["max_leverage"] <= 10.0):
                    return {"success": False, "message": "Leverage must be between 1x and 10x"}

            if "min_confidence_threshold" in new_settings:
                if not (0.0 <= new_settings["min_confidence_threshold"] <= 1.0):
                    return {"success": False, "message": "Confidence threshold must be between 0 and 1"}

            # Update settings
            self.settings.update(new_settings)

            # Reinitialize hybrid system if needed
            if any(k in new_settings for k in [
                "trading_mode", "max_leverage", "require_both_systems_agree",
                "min_confidence_threshold", "confidence_leverage_scaling",
                "enable_cooldown", "cooldown_bars"
            ]):
                self._init_hybrid_system()

            # Save to disk
            self.save_settings()

            return {"success": True, "message": "Settings updated successfully"}

        except Exception as e:
            return {"success": False, "message": f"Error updating settings: {str(e)}"}

    def get_settings(self) -> Dict:
        """Get current settings"""
        return self.settings.copy()

    def run_enhanced_analysis(self, df_primary, df_structure, symbol: str, timeframe: str) -> Dict:
        """
        Run analysis with enhanced features

        Args:
            df_primary: Primary timeframe data (e.g., 1h)
            df_structure: Structure timeframe data (e.g., 4h)
            symbol: Trading symbol
            timeframe: Primary timeframe

        Returns:
            Enhanced analysis results with hybrid mode, leverage, signal strength, etc.
        """
        try:
            analysis_mode = AnalysisMode(self.settings["analysis_mode"])

            if analysis_mode == AnalysisMode.HYBRID:
                # Run hybrid analysis
                result = self.hybrid_system.analyze_market(symbol, df_primary, df_structure)

                # Check cooldown
                if self.settings["enable_cooldown"] and self.cooldown_remaining > 0:
                    result.final_signal = "HOLD"
                    result.warnings.append(f"Cooldown active: {self.cooldown_remaining} bars remaining")

                # Check minimum signal strength
                min_strength = SignalStrength(self.settings["min_signal_strength"])
                if result.signal_strength.value < min_strength.value:
                    result.final_signal = "HOLD"
                    result.warnings.append(
                        f"Signal strength {result.signal_strength.name} below minimum {min_strength.name}"
                    )

                # Format response
                return {
                    "success": True,
                    "mode": "hybrid",
                    "signal": result.final_signal,
                    "confidence": result.confidence_score,
                    "signal_strength": result.signal_strength.name,
                    "signal_strength_value": result.signal_strength.value,
                    "recommended_leverage": result.recommended_leverage,
                    "position_size_pct": result.position_size_pct * 100,
                    "stop_loss": result.suggested_stop_loss,
                    "take_profit": result.suggested_take_profit,
                    "reasoning": result.reasoning,
                    "warnings": result.warnings,
                    "qa_signal": result.qa_signal,
                    "qa_confidence": result.qa_confidence,
                    "structure_aligned": result.structure_aligned,
                    "momentum_aligned": result.momentum_aligned,
                    "timeframe_confidence": result.timeframe_confidence,
                    "indicator_report": result.qa_indicator_report,
                    "pattern_report": result.qa_pattern_report,
                    "trend_report": result.qa_trend_report,
                    "decision_text": result.qa_decision,
                    "cooldown_remaining": self.cooldown_remaining,
                }

            else:
                # Run standard QuantAgent analysis
                results = self.base_analyzer.run_analysis(df_primary, symbol, timeframe)
                formatted = self.base_analyzer.extract_analysis_results(results)

                # Add confidence calculation
                confidence = self._calculate_standard_confidence(results)

                # Determine signal
                decision_text = results.get("final_trade_decision", "")
                if "LONG" in decision_text.upper():
                    signal = "LONG"
                elif "SHORT" in decision_text.upper():
                    signal = "SHORT"
                else:
                    signal = "HOLD"

                # Apply leverage scaling
                leverage = self._calculate_leverage(confidence)

                # Signal strength
                signal_strength = self._confidence_to_strength(confidence)

                # Check cooldown
                if self.settings["enable_cooldown"] and self.cooldown_remaining > 0:
                    signal = "HOLD"
                    formatted["warnings"] = [f"Cooldown active: {self.cooldown_remaining} bars"]

                # Add enhanced fields to standard analysis
                formatted.update({
                    "mode": "standard",
                    "signal": signal,
                    "confidence": confidence,
                    "signal_strength": signal_strength.name,
                    "signal_strength_value": signal_strength.value,
                    "recommended_leverage": leverage,
                    "cooldown_remaining": self.cooldown_remaining,
                })

                return formatted

        except Exception as e:
            return {
                "success": False,
                "error": f"Enhanced analysis error: {str(e)}"
            }

    def _calculate_standard_confidence(self, results: Dict) -> float:
        """Calculate confidence from standard QuantAgent results"""
        score = 0.5

        indicator_report = results.get("indicator_report", "").upper()
        pattern_report = results.get("pattern_report", "").upper()
        trend_report = results.get("trend_report", "").upper()
        decision = results.get("final_trade_decision", "").upper()

        if "LONG" in decision:
            if any(w in indicator_report for w in ["BULLISH", "BUY", "STRONG"]):
                score += 0.15
            if any(w in pattern_report for w in ["BULLISH", "UPWARD", "BREAKOUT"]):
                score += 0.15
            if any(w in trend_report for w in ["UPTREND", "SUPPORT", "RISING"]):
                score += 0.20
        elif "SHORT" in decision:
            if any(w in indicator_report for w in ["BEARISH", "SELL", "WEAK"]):
                score += 0.15
            if any(w in pattern_report for w in ["BEARISH", "DOWNWARD", "BREAKDOWN"]):
                score += 0.15
            if any(w in trend_report for w in ["DOWNTREND", "RESISTANCE", "FALLING"]):
                score += 0.20

        return min(score, 1.0)

    def _calculate_leverage(self, confidence: float) -> float:
        """Calculate leverage based on confidence and settings"""
        if not self.settings["confidence_leverage_scaling"]:
            return 1.0

        max_lev = self.settings["max_leverage"]

        # Scale leverage: low confidence → 1x, high confidence → max
        leverage = 1.0 + (confidence * (max_lev - 1.0))

        return round(leverage, 2)

    def _confidence_to_strength(self, confidence: float) -> SignalStrength:
        """Convert confidence score to signal strength"""
        if confidence >= 0.85:
            return SignalStrength.VERY_STRONG
        elif confidence >= 0.75:
            return SignalStrength.STRONG
        elif confidence >= 0.65:
            return SignalStrength.MODERATE
        elif confidence >= 0.55:
            return SignalStrength.WEAK
        else:
            return SignalStrength.VERY_WEAK

    def update_cooldown(self, traded: bool = False):
        """Update cooldown counter"""
        if traded and self.settings["enable_cooldown"]:
            self.cooldown_remaining = self.settings["cooldown_bars"]
        elif self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1


# API Routes to add to main web_interface.py
# ===========================================

def add_enhanced_routes(app, analyzer, enhanced_analyzer):
    """
    Add enhanced API routes to Flask app

    Call this function from main web_interface.py after initializing the app
    """

    @app.route("/api/enhanced/settings", methods=["GET"])
    def get_enhanced_settings():
        """Get current enhanced settings"""
        try:
            return jsonify({
                "success": True,
                "settings": enhanced_analyzer.get_settings()
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})

    @app.route("/api/enhanced/settings", methods=["POST"])
    def update_enhanced_settings():
        """Update enhanced settings"""
        try:
            data = request.get_json()
            result = enhanced_analyzer.update_settings(data)
            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})

    @app.route("/api/enhanced/analyze", methods=["POST"])
    def enhanced_analyze():
        """
        Enhanced analysis endpoint with hybrid mode support

        Request:
        {
            "asset": "BTC",
            "timeframe": "1h",
            "start_date": "2024-01-01",
            "end_date": "2024-12-01",
            "structure_timeframe": "4h"  // Optional for hybrid mode
        }
        """
        try:
            data = request.get_json()
            asset = data.get("asset")
            timeframe = data.get("timeframe", "1h")
            start_date = data.get("start_date")
            end_date = data.get("end_date")
            structure_timeframe = data.get("structure_timeframe", "4h")

            # Fetch primary timeframe data
            df_primary = analyzer.fetch_yfinance_data(asset, timeframe, start_date, end_date)
            if df_primary.empty:
                return jsonify({"success": False, "error": "No data available for primary timeframe"})

            # Fetch structure timeframe data (for hybrid mode)
            df_structure = None
            if enhanced_analyzer.settings["analysis_mode"] == AnalysisMode.HYBRID.value:
                df_structure = analyzer.fetch_yfinance_data(asset, structure_timeframe, start_date, end_date)

            # Run enhanced analysis
            symbol = analyzer.yfinance_symbols.get(asset, asset)
            result = enhanced_analyzer.run_enhanced_analysis(
                df_primary, df_structure, symbol, timeframe
            )

            return jsonify(result)

        except Exception as e:
            return jsonify({"success": False, "error": str(e)})

    @app.route("/api/enhanced/modes", methods=["GET"])
    def get_available_modes():
        """Get available trading and analysis modes"""
        return jsonify({
            "success": True,
            "analysis_modes": [
                {"value": m.value, "name": m.name} for m in AnalysisMode
            ],
            "trading_modes": [
                {"value": m.value, "name": m.name, "description": _get_mode_description(m)}
                for m in TradingMode
            ],
            "signal_strengths": [
                {"value": s.value, "name": s.name} for s in SignalStrength
            ]
        })

    @app.route("/api/enhanced/cooldown", methods=["POST"])
    def update_cooldown():
        """Manually update cooldown (for testing or after manual trade)"""
        try:
            data = request.get_json()
            traded = data.get("traded", False)
            enhanced_analyzer.update_cooldown(traded)
            return jsonify({
                "success": True,
                "cooldown_remaining": enhanced_analyzer.cooldown_remaining
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})


def _get_mode_description(mode: TradingMode) -> str:
    """Get description for trading mode"""
    descriptions = {
        TradingMode.CONSERVATIVE: "Max 1.5x leverage, 1% risk per trade - Safest option",
        TradingMode.BALANCED: "Max 3x leverage, 2% risk per trade - Recommended for most traders",
        TradingMode.AGGRESSIVE: "Max 5x leverage, 5% risk per trade - High risk/reward"
    }
    return descriptions.get(mode, "")


# Export for use in main web_interface.py
__all__ = [
    'EnhancedWebTradingAnalyzer',
    'AnalysisMode',
    'add_enhanced_routes'
]
