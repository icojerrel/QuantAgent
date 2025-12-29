"""
Hybrid Trading System
=====================

Combines QuantAgent's 4-agent deep analysis with Alpha Arena's
multi-timeframe validation for superior trading decisions.

Architecture:
    Layer 1: QuantAgent 4-Agent Analysis (Deep Reasoning)
    Layer 2: Multi-Timeframe Validation (Timing Confirmation)
    Layer 3: Unified Risk Management (Best of Both)
    Layer 4: Smart Execution (Dual Confirmation)

Author: Hybrid System Framework
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import pandas as pd
import numpy as np
import yfinance as yf

# Import QuantAgent
from trading_graph import TradingGraph

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('hybrid_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

class SignalStrength(Enum):
    """Signal strength levels"""
    VERY_STRONG = 5
    STRONG = 4
    MODERATE = 3
    WEAK = 2
    VERY_WEAK = 1


class TradingMode(Enum):
    """Trading mode configuration"""
    CONSERVATIVE = "conservative"  # QuantAgent-style, 1x leverage
    BALANCED = "balanced"          # Hybrid, 2-3x leverage
    AGGRESSIVE = "aggressive"      # Alpha Arena-style, 5x leverage


@dataclass
class AnalysisResult:
    """Combined analysis from both systems"""
    # QuantAgent outputs
    qa_signal: str  # LONG/SHORT/HOLD
    qa_confidence: float  # 0.0-1.0
    qa_indicator_report: str
    qa_pattern_report: str
    qa_trend_report: str
    qa_decision: str

    # Multi-timeframe validation
    structure_aligned: bool  # 4h structure confirms
    momentum_aligned: bool   # 5m momentum confirms
    timeframe_confidence: float  # 0.0-1.0

    # Combined decision
    final_signal: str  # LONG/SHORT/HOLD
    signal_strength: SignalStrength
    recommended_leverage: float  # 1x-5x
    confidence_score: float  # 0.0-1.0

    # Risk parameters
    suggested_stop_loss: float
    suggested_take_profit: float
    position_size_pct: float

    # Reasoning
    reasoning: str
    warnings: List[str]


@dataclass
class HybridConfig:
    """Hybrid system configuration"""

    # Trading mode
    mode: TradingMode = TradingMode.BALANCED

    # Confirmation requirements
    require_both_systems_agree: bool = True
    min_confidence_threshold: float = 0.65

    # Leverage settings
    max_leverage: float = 5.0
    base_leverage: float = 1.0
    confidence_leverage_scaling: bool = True

    # Position sizing
    base_position_size_pct: float = 0.02  # 2% base risk
    max_position_size_pct: float = 0.10   # 10% max

    # Risk management
    base_stop_loss_pct: float = 0.02  # 2%
    base_take_profit_pct: float = 0.04  # 4%
    dynamic_risk_adjustment: bool = True

    # Timeframe settings
    primary_timeframe: str = "1h"
    structure_timeframe: str = "4h"
    momentum_timeframe: str = "15m"

    # Cooldown
    enable_cooldown: bool = True
    cooldown_bars: int = 3


# ============================================================================
# Layer 1: QuantAgent Deep Analysis
# ============================================================================

class QuantAgentAnalyzer:
    """Wrapper for QuantAgent's 4-agent system"""

    def __init__(self):
        self.trading_graph = TradingGraph()
        logger.info("✅ QuantAgent Analyzer initialized")

    def analyze(self, data: pd.DataFrame, symbol: str, timeframe: str) -> Dict:
        """
        Run QuantAgent's 4-agent analysis

        Returns:
            {
                'signal': 'LONG'|'SHORT'|'HOLD',
                'confidence': 0.0-1.0,
                'reports': {...},
                'decision': '...'
            }
        """
        try:
            # Prepare data
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

            # Run 4-agent analysis
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

            # Calculate confidence based on agent agreement
            confidence = self._calculate_confidence(result)

            return {
                'signal': signal,
                'confidence': confidence,
                'indicator_report': result.get("indicator_report", ""),
                'pattern_report': result.get("pattern_report", ""),
                'trend_report': result.get("trend_report", ""),
                'decision': decision_text
            }

        except Exception as e:
            logger.error(f"❌ QuantAgent analysis error: {e}")
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'indicator_report': '',
                'pattern_report': '',
                'trend_report': '',
                'decision': f'Error: {str(e)}'
            }

    def _calculate_confidence(self, result: Dict) -> float:
        """Calculate confidence based on agent agreement"""
        score = 0.5  # Base score

        indicator_report = result.get("indicator_report", "").upper()
        pattern_report = result.get("pattern_report", "").upper()
        trend_report = result.get("trend_report", "").upper()
        decision = result.get("final_trade_decision", "").upper()

        # Determine signal direction
        if "LONG" in decision:
            # Check bullish signals
            if any(w in indicator_report for w in ["BULLISH", "BUY", "STRONG"]):
                score += 0.15
            if any(w in pattern_report for w in ["BULLISH", "UPWARD", "BREAKOUT"]):
                score += 0.15
            if any(w in trend_report for w in ["UPTREND", "SUPPORT", "RISING"]):
                score += 0.20

        elif "SHORT" in decision:
            # Check bearish signals
            if any(w in indicator_report for w in ["BEARISH", "SELL", "WEAK"]):
                score += 0.15
            if any(w in pattern_report for w in ["BEARISH", "DOWNWARD", "BREAKDOWN"]):
                score += 0.15
            if any(w in trend_report for w in ["DOWNTREND", "RESISTANCE", "FALLING"]):
                score += 0.20

        return min(score, 1.0)


# ============================================================================
# Layer 2: Multi-Timeframe Validator
# ============================================================================

class MultiTimeframeValidator:
    """Alpha Arena-style multi-timeframe validation"""

    def __init__(self):
        logger.info("✅ Multi-Timeframe Validator initialized")

    def validate(self, data_primary: pd.DataFrame, data_structure: pd.DataFrame,
                 qa_signal: str) -> Dict:
        """
        Validate QuantAgent signal with multi-timeframe analysis

        Args:
            data_primary: Primary timeframe data (e.g., 1h)
            data_structure: Structure timeframe data (e.g., 4h)
            qa_signal: QuantAgent's signal (LONG/SHORT/HOLD)

        Returns:
            {
                'structure_aligned': bool,
                'momentum_aligned': bool,
                'confidence': 0.0-1.0,
                'recommended_signal': 'LONG'|'SHORT'|'HOLD'
            }
        """
        try:
            # Check structure (4h)
            structure_bullish, structure_score = self._check_structure(data_structure)

            # Check momentum (primary timeframe as proxy for 5m/15m)
            momentum_bullish, momentum_score = self._check_momentum(data_primary)

            # Determine alignment
            if qa_signal == "LONG":
                structure_aligned = structure_bullish
                momentum_aligned = momentum_bullish
                confidence = (structure_score + momentum_score) / 2.0

            elif qa_signal == "SHORT":
                structure_aligned = not structure_bullish
                momentum_aligned = not momentum_bullish
                confidence = (structure_score + momentum_score) / 2.0

            else:  # HOLD
                structure_aligned = False
                momentum_aligned = False
                confidence = 0.0

            # Hysteresis logic: require BOTH to agree for confirmation
            if structure_aligned and momentum_aligned:
                recommended_signal = qa_signal
            else:
                recommended_signal = "HOLD"

            return {
                'structure_aligned': structure_aligned,
                'momentum_aligned': momentum_aligned,
                'confidence': confidence,
                'recommended_signal': recommended_signal
            }

        except Exception as e:
            logger.error(f"❌ Multi-timeframe validation error: {e}")
            return {
                'structure_aligned': False,
                'momentum_aligned': False,
                'confidence': 0.0,
                'recommended_signal': 'HOLD'
            }

    def _check_structure(self, data: pd.DataFrame) -> Tuple[bool, float]:
        """Check higher timeframe structure"""
        try:
            # Calculate EMAs
            ema20 = data['Close'].ewm(span=20).mean()
            ema50 = data['Close'].ewm(span=50).mean()

            # MACD
            ema12 = data['Close'].ewm(span=12).mean()
            ema26 = data['Close'].ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()
            histogram = macd - signal

            # Latest values
            ema20_now = ema20.iloc[-1]
            ema50_now = ema50.iloc[-1]
            macd_hist_now = histogram.iloc[-1]

            # Bullish structure: EMA20 > EMA50 and MACD > 0
            is_bullish = (ema20_now > ema50_now) and (macd_hist_now > 0)

            # Calculate confidence
            ema_spread = abs(ema20_now - ema50_now) / ema50_now
            macd_strength = abs(macd_hist_now) / data['Close'].iloc[-1]
            confidence = min(0.5 + ema_spread * 100 + macd_strength * 100, 1.0)

            return is_bullish, confidence

        except Exception as e:
            logger.error(f"Structure check error: {e}")
            return False, 0.0

    def _check_momentum(self, data: pd.DataFrame) -> Tuple[bool, float]:
        """Check momentum alignment"""
        try:
            # RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # EMA
            ema20 = data['Close'].ewm(span=20).mean()

            # MACD
            ema12 = data['Close'].ewm(span=12).mean()
            ema26 = data['Close'].ewm(span=26).mean()
            macd = ema12 - ema26
            signal_line = macd.ewm(span=9).mean()
            histogram = macd - signal_line

            # Latest values
            price_now = data['Close'].iloc[-1]
            rsi_now = rsi.iloc[-1]
            ema20_now = ema20.iloc[-1]
            macd_hist_now = histogram.iloc[-1]

            # Bullish momentum: RSI > 50, price > EMA20, MACD > 0
            is_bullish = (rsi_now > 50) and (price_now > ema20_now) and (macd_hist_now > 0)

            # Calculate confidence
            rsi_strength = abs(rsi_now - 50) / 50  # Distance from neutral
            price_ema_spread = abs(price_now - ema20_now) / ema20_now
            confidence = min(0.5 + rsi_strength + price_ema_spread * 10, 1.0)

            return is_bullish, confidence

        except Exception as e:
            logger.error(f"Momentum check error: {e}")
            return False, 0.0


# ============================================================================
# Layer 3: Unified Risk Manager
# ============================================================================

class UnifiedRiskManager:
    """Combined risk management from both systems"""

    def __init__(self, config: HybridConfig):
        self.config = config
        logger.info("✅ Unified Risk Manager initialized")

    def calculate_position_params(self, signal: str, confidence: float,
                                  current_price: float, capital: float,
                                  volatility: float = None) -> Dict:
        """
        Calculate position parameters based on confidence and mode

        Returns:
            {
                'leverage': float,
                'position_size_pct': float,
                'stop_loss': float,
                'take_profit': float,
                'risk_reward_ratio': float
            }
        """
        # Leverage scaling based on confidence
        if self.config.confidence_leverage_scaling:
            # High confidence → Higher leverage (up to max)
            # Low confidence → Lower leverage (base)
            leverage_range = self.config.max_leverage - self.config.base_leverage
            leverage = self.config.base_leverage + (confidence * leverage_range)
        else:
            leverage = self.config.base_leverage

        # Cap leverage based on mode
        if self.config.mode == TradingMode.CONSERVATIVE:
            leverage = min(leverage, 1.5)
        elif self.config.mode == TradingMode.BALANCED:
            leverage = min(leverage, 3.0)
        # AGGRESSIVE uses full range

        # Position sizing
        if self.config.dynamic_risk_adjustment and volatility:
            # Reduce size in high volatility
            volatility_factor = max(0.5, 1.0 - (volatility * 2))
            position_size_pct = self.config.base_position_size_pct * confidence * volatility_factor
        else:
            position_size_pct = self.config.base_position_size_pct * confidence

        position_size_pct = min(position_size_pct, self.config.max_position_size_pct)

        # Stop loss / Take profit
        # Wider stops in high volatility
        sl_multiplier = 1.5 if volatility and volatility > 0.03 else 1.0
        stop_loss_pct = self.config.base_stop_loss_pct * sl_multiplier
        take_profit_pct = self.config.base_take_profit_pct * (2.0 if confidence > 0.8 else 1.0)

        if signal == "LONG":
            stop_loss = current_price * (1 - stop_loss_pct)
            take_profit = current_price * (1 + take_profit_pct)
        elif signal == "SHORT":
            stop_loss = current_price * (1 + stop_loss_pct)
            take_profit = current_price * (1 - take_profit_pct)
        else:
            stop_loss = current_price
            take_profit = current_price

        risk_reward = take_profit_pct / stop_loss_pct

        return {
            'leverage': round(leverage, 2),
            'position_size_pct': position_size_pct,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward_ratio': risk_reward
        }


# ============================================================================
# Hybrid Trading System (Main)
# ============================================================================

class HybridTradingSystem:
    """
    Main hybrid system combining QuantAgent and Alpha Arena
    """

    def __init__(self, config: HybridConfig = None):
        self.config = config or HybridConfig()

        # Initialize components
        self.qa_analyzer = QuantAgentAnalyzer()
        self.mtf_validator = MultiTimeframeValidator()
        self.risk_manager = UnifiedRiskManager(self.config)

        # State
        self.last_trade_time = None
        self.cooldown_remaining = 0

        logger.info("="*80)
        logger.info("🤖 HYBRID TRADING SYSTEM INITIALIZED")
        logger.info(f"Mode: {self.config.mode.value.upper()}")
        logger.info(f"Max Leverage: {self.config.max_leverage}x")
        logger.info(f"Require Both Systems: {self.config.require_both_systems_agree}")
        logger.info("="*80)

    def analyze_market(self, symbol: str, data_primary: pd.DataFrame,
                      data_structure: pd.DataFrame = None) -> AnalysisResult:
        """
        Complete market analysis using both systems

        Args:
            symbol: Trading symbol (e.g., "BTC-USD")
            data_primary: Primary timeframe data (e.g., 1h)
            data_structure: Structure timeframe data (e.g., 4h), optional

        Returns:
            AnalysisResult with complete analysis and recommendations
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 ANALYZING {symbol}")
        logger.info(f"{'='*80}")

        warnings = []

        # Layer 1: QuantAgent Deep Analysis
        logger.info("\n📊 Layer 1: QuantAgent 4-Agent Analysis...")
        qa_result = self.qa_analyzer.analyze(
            data_primary, symbol, self.config.primary_timeframe
        )

        logger.info(f"   Signal: {qa_result['signal']}")
        logger.info(f"   Confidence: {qa_result['confidence']:.2f}")

        # Layer 2: Multi-Timeframe Validation
        logger.info("\n🕐 Layer 2: Multi-Timeframe Validation...")

        if data_structure is not None and len(data_structure) > 50:
            mtf_result = self.mtf_validator.validate(
                data_primary, data_structure, qa_result['signal']
            )
        else:
            logger.warning("   ⚠️  No structure data, skipping multi-timeframe validation")
            mtf_result = {
                'structure_aligned': True,  # Assume OK if no data
                'momentum_aligned': True,
                'confidence': qa_result['confidence'],
                'recommended_signal': qa_result['signal']
            }
            warnings.append("Multi-timeframe validation skipped (no data)")

        logger.info(f"   Structure Aligned: {mtf_result['structure_aligned']}")
        logger.info(f"   Momentum Aligned: {mtf_result['momentum_aligned']}")
        logger.info(f"   MTF Confidence: {mtf_result['confidence']:.2f}")

        # Combine confidences
        combined_confidence = (qa_result['confidence'] + mtf_result['confidence']) / 2.0

        # Final decision logic
        logger.info("\n🧠 Layer 3: Decision Synthesis...")

        if self.config.require_both_systems_agree:
            # STRICT: Both systems must agree
            if (qa_result['signal'] == mtf_result['recommended_signal'] and
                qa_result['signal'] != 'HOLD' and
                mtf_result['structure_aligned'] and
                mtf_result['momentum_aligned']):
                final_signal = qa_result['signal']
                logger.info(f"   ✅ Both systems agree: {final_signal}")
            else:
                final_signal = "HOLD"
                logger.info(f"   ⏸️  Systems disagree or weak signal: HOLD")
                if qa_result['signal'] != mtf_result['recommended_signal']:
                    warnings.append(f"QuantAgent says {qa_result['signal']}, MTF says {mtf_result['recommended_signal']}")
        else:
            # FLEXIBLE: Use QuantAgent if confidence is high enough
            if combined_confidence >= self.config.min_confidence_threshold:
                final_signal = qa_result['signal']
                logger.info(f"   ✅ Confidence above threshold: {final_signal}")
            else:
                final_signal = "HOLD"
                logger.info(f"   ⏸️  Confidence too low: HOLD")
                warnings.append(f"Combined confidence {combined_confidence:.2f} < {self.config.min_confidence_threshold}")

        # Check cooldown
        if self.config.enable_cooldown and self.cooldown_remaining > 0:
            logger.info(f"   ⏰ Cooldown active ({self.cooldown_remaining} bars remaining): HOLD")
            final_signal = "HOLD"
            warnings.append(f"Cooldown active: {self.cooldown_remaining} bars")

        # Determine signal strength
        if combined_confidence >= 0.85:
            strength = SignalStrength.VERY_STRONG
        elif combined_confidence >= 0.75:
            strength = SignalStrength.STRONG
        elif combined_confidence >= 0.65:
            strength = SignalStrength.MODERATE
        elif combined_confidence >= 0.55:
            strength = SignalStrength.WEAK
        else:
            strength = SignalStrength.VERY_WEAK

        logger.info(f"   Signal Strength: {strength.name}")

        # Layer 3: Risk Management
        logger.info("\n💰 Layer 4: Risk Management...")

        current_price = data_primary['Close'].iloc[-1]
        volatility = data_primary['Close'].pct_change().std()

        risk_params = self.risk_manager.calculate_position_params(
            final_signal, combined_confidence, current_price,
            capital=10000,  # Placeholder
            volatility=volatility
        )

        logger.info(f"   Leverage: {risk_params['leverage']}x")
        logger.info(f"   Position Size: {risk_params['position_size_pct']*100:.2f}%")
        logger.info(f"   Stop Loss: ${risk_params['stop_loss']:.2f}")
        logger.info(f"   Take Profit: ${risk_params['take_profit']:.2f}")
        logger.info(f"   R/R Ratio: {risk_params['risk_reward_ratio']:.2f}")

        # Build reasoning
        reasoning_parts = []
        reasoning_parts.append(f"QuantAgent Signal: {qa_result['signal']} (confidence {qa_result['confidence']:.2f})")
        reasoning_parts.append(f"Multi-Timeframe: Structure {'✓' if mtf_result['structure_aligned'] else '✗'}, Momentum {'✓' if mtf_result['momentum_aligned'] else '✗'}")
        reasoning_parts.append(f"Combined Confidence: {combined_confidence:.2f}")
        reasoning_parts.append(f"Final Decision: {final_signal} ({strength.name})")

        reasoning = " | ".join(reasoning_parts)

        # Create result
        result = AnalysisResult(
            qa_signal=qa_result['signal'],
            qa_confidence=qa_result['confidence'],
            qa_indicator_report=qa_result['indicator_report'],
            qa_pattern_report=qa_result['pattern_report'],
            qa_trend_report=qa_result['trend_report'],
            qa_decision=qa_result['decision'],
            structure_aligned=mtf_result['structure_aligned'],
            momentum_aligned=mtf_result['momentum_aligned'],
            timeframe_confidence=mtf_result['confidence'],
            final_signal=final_signal,
            signal_strength=strength,
            recommended_leverage=risk_params['leverage'],
            confidence_score=combined_confidence,
            suggested_stop_loss=risk_params['stop_loss'],
            suggested_take_profit=risk_params['take_profit'],
            position_size_pct=risk_params['position_size_pct'],
            reasoning=reasoning,
            warnings=warnings
        )

        logger.info(f"\n{'='*80}")
        logger.info(f"📝 FINAL RECOMMENDATION: {final_signal}")
        logger.info(f"{'='*80}\n")

        return result

    def update_cooldown(self, traded: bool = False):
        """Update cooldown counter"""
        if traded and self.config.enable_cooldown:
            self.cooldown_remaining = self.config.cooldown_bars
            logger.info(f"⏰ Cooldown activated: {self.cooldown_remaining} bars")
        elif self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Demo of hybrid system"""

    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║              HYBRID TRADING SYSTEM                           ║
    ║         QuantAgent + Alpha Arena Combined                    ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

    # Configure hybrid system
    config = HybridConfig(
        mode=TradingMode.BALANCED,
        require_both_systems_agree=True,
        min_confidence_threshold=0.70,
        max_leverage=5.0,
        confidence_leverage_scaling=True
    )

    # Initialize system
    system = HybridTradingSystem(config)

    # Fetch data
    symbol = "BTC-USD"
    logger.info(f"Fetching data for {symbol}...")

    data_1h = yf.download(symbol, period="60d", interval="1h", progress=False)
    data_4h = yf.download(symbol, period="60d", interval="4h", progress=False)

    # Analyze
    result = system.analyze_market(symbol, data_1h, data_4h)

    # Display results
    print("\n" + "="*80)
    print("HYBRID SYSTEM ANALYSIS RESULT")
    print("="*80)
    print(f"\nSymbol: {symbol}")
    print(f"Timestamp: {datetime.now()}")
    print(f"\n{'LAYER':<30} {'RESULT':<50}")
    print("-"*80)
    print(f"{'QuantAgent Signal':<30} {result.qa_signal} (confidence: {result.qa_confidence:.2f})")
    print(f"{'Multi-Timeframe':<30} Structure: {result.structure_aligned}, Momentum: {result.momentum_aligned}")
    print(f"{'Combined Confidence':<30} {result.confidence_score:.2f}")
    print(f"{'Signal Strength':<30} {result.signal_strength.name}")
    print(f"\n{'FINAL DECISION':<30} {result.final_signal}")
    print(f"{'Recommended Leverage':<30} {result.recommended_leverage}x")
    print(f"{'Position Size':<30} {result.position_size_pct*100:.2f}%")
    print(f"{'Stop Loss':<30} ${result.suggested_stop_loss:.2f}")
    print(f"{'Take Profit':<30} ${result.suggested_take_profit:.2f}")

    if result.warnings:
        print(f"\n⚠️  WARNINGS:")
        for warning in result.warnings:
            print(f"   - {warning}")

    print("\n" + "="*80)

    # Save result
    with open("hybrid_analysis_result.json", "w") as f:
        json.dump(asdict(result), f, indent=2, default=str)

    logger.info("✅ Result saved to hybrid_analysis_result.json")


if __name__ == "__main__":
    main()
