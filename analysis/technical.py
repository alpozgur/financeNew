# analysis/technical.py
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from ta import add_all_ta_features, trend, momentum, volatility, volume
from ta.utils import dropna
from database.connection import DatabaseManager
from config.config import Config

class TechnicalAnalyzer:
    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.db = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.indicators_config = config.analysis.technical_indicators
    
    def calculate_moving_averages(self, prices: pd.Series) -> pd.DataFrame:
        """Hareketli ortalamaları hesapla"""
        ma_data = pd.DataFrame(index=prices.index)
        ma_data['price'] = prices
        
        # Simple Moving Averages
        for period in self.indicators_config['sma_periods']:
            ma_data[f'SMA_{period}'] = prices.rolling(window=period).mean()
        
        # Exponential Moving Averages
        for period in self.indicators_config['ema_periods']:
            ma_data[f'EMA_{period}'] = prices.ewm(span=period).mean()
        
        return ma_data
    
    def calculate_rsi(self, prices: pd.Series, period: int = None) -> pd.Series:
        """RSI (Relative Strength Index) hesapla"""
        if period is None:
            period = self.indicators_config['rsi_period']
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(self, prices: pd.Series) -> pd.DataFrame:
        """MACD indikatörünü hesapla"""
        fast_period = self.indicators_config['macd_fast']
        slow_period = self.indicators_config['macd_slow']
        signal_period = self.indicators_config['macd_signal']
        
        ema_fast = prices.ewm(span=fast_period).mean()
        ema_slow = prices.ewm(span=slow_period).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period).mean()
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'MACD': macd_line,
            'MACD_Signal': signal_line,
            'MACD_Histogram': histogram
        }, index=prices.index)
    
    def calculate_bollinger_bands(self, prices: pd.Series) -> pd.DataFrame:
        """Bollinger Bantlarını hesapla"""
        period = self.indicators_config['bollinger_period']
        std_dev = self.indicators_config['bollinger_std']
        
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        # Bollinger Band Width ve %B
        bb_width = (upper_band - lower_band) / sma
        bb_percent = (prices - lower_band) / (upper_band - lower_band)
        
        return pd.DataFrame({
            'BB_Upper': upper_band,
            'BB_Middle': sma,
            'BB_Lower': lower_band,
            'BB_Width': bb_width,
            'BB_Percent': bb_percent
        }, index=prices.index)
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                           k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """Stochastic Oscillator hesapla"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return pd.DataFrame({
            'Stoch_K': k_percent,
            'Stoch_D': d_percent
        }, index=close.index)
    
    def calculate_ichimoku(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
        """Ichimoku Cloud indikatörlerini hesapla"""
        # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
        tenkan_sen = (high.rolling(window=9).max() + low.rolling(window=9).min()) / 2
        
        # Kijun-sen (Base Line): (26-period high + 26-period low)/2
        kijun_sen = (high.rolling(window=26).max() + low.rolling(window=26).min()) / 2
        
        # Senkou Span A (Leading Span A): (Tenkan-sen + Kijun-sen)/2, shifted 26 periods ahead
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
        
        # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2, shifted 26 periods ahead
        senkou_span_b = ((high.rolling(window=52).max() + low.rolling(window=52).min()) / 2).shift(26)
        
        # Chikou Span (Lagging Span): Close shifted 26 periods back
        chikou_span = close.shift(-26)
        
        return pd.DataFrame({
            'Tenkan_Sen': tenkan_sen,
            'Kijun_Sen': kijun_sen,
            'Senkou_Span_A': senkou_span_a,
            'Senkou_Span_B': senkou_span_b,
            'Chikou_Span': chikou_span
        }, index=close.index)
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range hesapla"""
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    def calculate_williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Williams %R hesapla"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        
        williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)
        
        return williams_r
    
    def calculate_cci(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """Commodity Channel Index hesapla"""
        typical_price = (high + low + close) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
        
        cci = (typical_price - sma_tp) / (0.015 * mad)
        
        return cci
    
    def detect_support_resistance(self, prices: pd.Series, window: int = 10, min_touches: int = 2) -> Dict:
        """Destek ve direnç seviyelerini tespit et"""
        # Local maxima ve minima bul
        highs = prices.rolling(window=window*2+1, center=True).max() == prices
        lows = prices.rolling(window=window*2+1, center=True).min() == prices
        
        # Direnç seviyeleri (local maxima)
        resistance_points = prices[highs].dropna()
        resistance_levels = []
        
        for level in resistance_points:
            touches = sum(abs(prices - level) / level < 0.02)  # %2 tolerans
            if touches >= min_touches:
                resistance_levels.append({
                    'level': level,
                    'touches': touches,
                    'strength': touches / len(prices) * 100
                })
        
        # Destek seviyeleri (local minima)
        support_points = prices[lows].dropna()
        support_levels = []
        
        for level in support_points:
            touches = sum(abs(prices - level) / level < 0.02)  # %2 tolerans
            if touches >= min_touches:
                support_levels.append({
                    'level': level,
                    'touches': touches,
                    'strength': touches / len(prices) * 100
                })
        
        # En güçlü seviyeleri sırala
        resistance_levels = sorted(resistance_levels, key=lambda x: x['strength'], reverse=True)[:5]
        support_levels = sorted(support_levels, key=lambda x: x['strength'], reverse=True)[:5]
        
        return {
            'resistance_levels': resistance_levels,
            'support_levels': support_levels,
            'current_price': prices.iloc[-1],
            'nearest_resistance': min(resistance_levels, key=lambda x: abs(x['level'] - prices.iloc[-1])) if resistance_levels else None,
            'nearest_support': min(support_levels, key=lambda x: abs(x['level'] - prices.iloc[-1])) if support_levels else None
        }
    
    def generate_trading_signals(self, technical_data: pd.DataFrame) -> pd.DataFrame:
        """Teknik analize dayalı alım-satım sinyalleri üret"""
        signals = pd.DataFrame(index=technical_data.index)
        
        # RSI sinyalleri
        signals['RSI_Signal'] = 0
        signals.loc[technical_data['RSI'] < 30, 'RSI_Signal'] = 1  # Alım
        signals.loc[technical_data['RSI'] > 70, 'RSI_Signal'] = -1  # Satım
        
        # MACD sinyalleri
        signals['MACD_Signal'] = 0
        macd_cross = (technical_data['MACD'] > technical_data['MACD_Signal']) & \
                     (technical_data['MACD'].shift(1) <= technical_data['MACD_Signal'].shift(1))
        signals.loc[macd_cross, 'MACD_Signal'] = 1  # Alım
        
        macd_cross_down = (technical_data['MACD'] < technical_data['MACD_Signal']) & \
                          (technical_data['MACD'].shift(1) >= technical_data['MACD_Signal'].shift(1))
        signals.loc[macd_cross_down, 'MACD_Signal'] = -1  # Satım
        
        # Bollinger Band sinyalleri
        signals['BB_Signal'] = 0
        signals.loc[technical_data['BB_Percent'] < 0, 'BB_Signal'] = 1  # Alt bantın altına düşme - Alım
        signals.loc[technical_data['BB_Percent'] > 1, 'BB_Signal'] = -1  # Üst bantın üstüne çıkma - Satım
        
        # Moving Average sinyalleri
        signals['MA_Signal'] = 0
        if 'SMA_20' in technical_data.columns and 'SMA_50' in technical_data.columns:
            golden_cross = (technical_data['SMA_20'] > technical_data['SMA_50']) & \
                          (technical_data['SMA_20'].shift(1) <= technical_data['SMA_50'].shift(1))
            signals.loc[golden_cross, 'MA_Signal'] = 1  # Alım
            
            death_cross = (technical_data['SMA_20'] < technical_data['SMA_50']) & \
                         (technical_data['SMA_20'].shift(1) >= technical_data['SMA_50'].shift(1))
            signals.loc[death_cross, 'MA_Signal'] = -1  # Satım
        
        # Kombine sinyal (ağırlıklı)
        signal_weights = {
            'RSI_Signal': 0.25,
            'MACD_Signal': 0.30,
            'BB_Signal': 0.25,
            'MA_Signal': 0.20
        }
        
        signals['Combined_Signal'] = 0
        for signal_col, weight in signal_weights.items():
            signals['Combined_Signal'] += signals[signal_col] * weight
        
        # Sinyal gücü (-1 ile 1 arası)
        signals['Signal_Strength'] = signals['Combined_Signal']
        
        # Kesin alım/satım kararları
        signals['Final_Signal'] = 0
        signals.loc[signals['Combined_Signal'] > 0.5, 'Final_Signal'] = 1  # Güçlü Alım
        signals.loc[signals['Combined_Signal'] < -0.5, 'Final_Signal'] = -1  # Güçlü Satım
        
        return signals
    
    def calculate_momentum_indicators(self, prices: pd.Series) -> pd.DataFrame:
        """Momentum indikatörlerini hesapla"""
        momentum_data = pd.DataFrame(index=prices.index)
        
        # Rate of Change (ROC)
        for period in [5, 10, 20]:
            momentum_data[f'ROC_{period}'] = ((prices / prices.shift(period)) - 1) * 100
        
        # Momentum
        for period in [5, 10, 20]:
            momentum_data[f'Momentum_{period}'] = prices - prices.shift(period)
        
        # Price Oscillator
        momentum_data['Price_Oscillator'] = ((prices.ewm(span=12).mean() - prices.ewm(span=26).mean()) / 
                                           prices.ewm(span=26).mean()) * 100
        
        return momentum_data
    
    def analyze_fund_technical(self, fcode: str, days: int = 252) -> Dict:
        """Tek fon için kapsamlı teknik analiz"""
        try:
            # Fon verilerini çek
            fund_data = self.db.get_fund_price_history(fcode, days)
            
            if fund_data.empty:
                self.logger.warning(f"Fon {fcode} için veri bulunamadı")
                return {}
            
            # Veriyi hazırla
            fund_data = fund_data.set_index('pdate').sort_index()
            prices = fund_data['price']
            
            # Yüksek, düşük, kapanış fiyatları (fon verileri için price kullanıyoruz)
            high = prices  # Fonlar için tek fiyat var
            low = prices
            close = prices
            
            # Teknik indikatörleri hesapla
            technical_indicators = pd.DataFrame(index=prices.index)
            
            # Moving Averages
            ma_data = self.calculate_moving_averages(prices)
            technical_indicators = technical_indicators.join(ma_data)
            
            # RSI
            technical_indicators['RSI'] = self.calculate_rsi(prices)
            
            # MACD
            macd_data = self.calculate_macd(prices)
            technical_indicators = technical_indicators.join(macd_data)
            
            # Bollinger Bands
            bb_data = self.calculate_bollinger_bands(prices)
            technical_indicators = technical_indicators.join(bb_data)
            
            # Stochastic
            stoch_data = self.calculate_stochastic(high, low, close)
            technical_indicators = technical_indicators.join(stoch_data)
            
            # Williams %R
            technical_indicators['Williams_R'] = self.calculate_williams_r(high, low, close)
            
            # CCI
            technical_indicators['CCI'] = self.calculate_cci(high, low, close)
            
            # ATR
            technical_indicators['ATR'] = self.calculate_atr(high, low, close)
            
            # Momentum Indicators
            momentum_data = self.calculate_momentum_indicators(prices)
            technical_indicators = technical_indicators.join(momentum_data)
            
            # Trading Signals
            trading_signals = self.generate_trading_signals(technical_indicators)
            
            # Support/Resistance Analysis
            support_resistance = self.detect_support_resistance(prices)
            
            # Trend Analysis
            current_trend = self._analyze_trend(technical_indicators)
            
            return {
                'fcode': fcode,
                'analysis_date': pd.Timestamp.now(),
                'technical_indicators': technical_indicators,
                'trading_signals': trading_signals,
                'support_resistance': support_resistance,
                'trend_analysis': current_trend,
                'latest_values': {
                    'price': prices.iloc[-1],
                    'rsi': technical_indicators['RSI'].iloc[-1],
                    'macd': technical_indicators['MACD'].iloc[-1],
                    'bb_position': technical_indicators['BB_Percent'].iloc[-1],
                    'signal_strength': trading_signals['Signal_Strength'].iloc[-1],
                    'final_signal': trading_signals['Final_Signal'].iloc[-1]
                }
            }
            
        except Exception as e:
            self.logger.error(f"Fon {fcode} teknik analiz hatası: {e}")
            return {}
    
    def _analyze_trend(self, technical_data: pd.DataFrame) -> Dict:
        """Trend analizi yap"""
        try:
            # Moving Average tabanlı trend
            if 'SMA_20' in technical_data.columns and 'SMA_50' in technical_data.columns:
                current_ma20 = technical_data['SMA_20'].iloc[-1]
                current_ma50 = technical_data['SMA_50'].iloc[-1]
                
                if current_ma20 > current_ma50:
                    ma_trend = "Yükseliş"
                elif current_ma20 < current_ma50:
                    ma_trend = "Düşüş"
                else:
                    ma_trend = "Yatay"
            else:
                ma_trend = "Belirsiz"
            
            # RSI tabanlı trend
            current_rsi = technical_data['RSI'].iloc[-1]
            if current_rsi > 50:
                rsi_trend = "Yükseliş"
            elif current_rsi < 50:
                rsi_trend = "Düşüş"
            else:
                rsi_trend = "Yatay"
            
            # MACD tabanlı trend
            current_macd = technical_data['MACD'].iloc[-1]
            current_signal = technical_data['MACD_Signal'].iloc[-1]
            
            if current_macd > current_signal:
                macd_trend = "Yükseliş"
            elif current_macd < current_signal:
                macd_trend = "Düşüş"
            else:
                macd_trend = "Yatay"
            
            # Genel trend değerlendirmesi
            trends = [ma_trend, rsi_trend, macd_trend]
            uptrend_count = trends.count("Yükseliş")
            downtrend_count = trends.count("Düşüş")
            
            if uptrend_count >= 2:
                overall_trend = "Yükseliş"
                trend_strength = uptrend_count / len(trends)
            elif downtrend_count >= 2:
                overall_trend = "Düşüş"
                trend_strength = downtrend_count / len(trends)
            else:
                overall_trend = "Yatay"
                trend_strength = 0.5
            
            return {
                'overall_trend': overall_trend,
                'trend_strength': trend_strength,
                'ma_trend': ma_trend,
                'rsi_trend': rsi_trend,
                'macd_trend': macd_trend,
                'analysis_details': {
                    'current_rsi': current_rsi,
                    'ma20_vs_ma50': f"{current_ma20:.4f} vs {current_ma50:.4f}" if 'SMA_20' in technical_data.columns else "N/A",
                    'macd_vs_signal': f"{current_macd:.4f} vs {current_signal:.4f}"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Trend analizi hatası: {e}")
            return {'overall_trend': 'Belirsiz', 'trend_strength': 0}
    
    def batch_technical_analysis(self, fund_codes: List[str], days: int = 252) -> Dict:
        """Çoklu fon teknik analizi"""
        results = {}
        
        for fcode in fund_codes:
            try:
                analysis = self.analyze_fund_technical(fcode, days)
                if analysis:
                    results[fcode] = analysis
                    self.logger.info(f"Fon {fcode} teknik analizi tamamlandı")
            except Exception as e:
                self.logger.error(f"Fon {fcode} teknik analiz hatası: {e}")
        
        # Özet rapor oluştur
        summary = self._create_technical_summary(results)
        
        return {
            'individual_analyses': results,
            'summary_report': summary,
            'analysis_date': pd.Timestamp.now(),
            'total_funds_analyzed': len(results)
        }
    
    def _create_technical_summary(self, analyses: Dict) -> Dict:
        """Teknik analiz özet raporu oluştur"""
        if not analyses:
            return {}
        
        summary_data = []
        for fcode, analysis in analyses.items():
            latest = analysis.get('latest_values', {})
            trend = analysis.get('trend_analysis', {})
            
            summary_data.append({
                'fcode': fcode,
                'current_price': latest.get('price', 0),
                'rsi': latest.get('rsi', 0),
                'signal_strength': latest.get('signal_strength', 0),
                'final_signal': latest.get('final_signal', 0),
                'trend': trend.get('overall_trend', 'Belirsiz'),
                'trend_strength': trend.get('trend_strength', 0)
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        # İstatistikler
        buy_signals = len(summary_df[summary_df['final_signal'] == 1])
        sell_signals = len(summary_df[summary_df['final_signal'] == -1])
        neutral_signals = len(summary_df[summary_df['final_signal'] == 0])
        
        uptrend_funds = len(summary_df[summary_df['trend'] == 'Yükseliş'])
        downtrend_funds = len(summary_df[summary_df['trend'] == 'Düşüş'])
        
        return {
            'signal_distribution': {
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'neutral_signals': neutral_signals
            },
            'trend_distribution': {
                'uptrend_funds': uptrend_funds,
                'downtrend_funds': downtrend_funds,
                'sideways_funds': len(summary_df) - uptrend_funds - downtrend_funds
            },
            'top_buy_candidates': summary_df.nlargest(5, 'signal_strength')['fcode'].tolist(),
            'top_sell_candidates': summary_df.nsmallest(5, 'signal_strength')['fcode'].tolist(),
            'strongest_uptrend': summary_df[summary_df['trend'] == 'Yükseliş'].nlargest(5, 'trend_strength')['fcode'].tolist(),
            'average_rsi': summary_df['rsi'].mean(),
            'summary_table': summary_df
        }