import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from scipy import stats
import empyrical as ep
from database.connection import DatabaseManager
from config.config import Config

class PerformanceAnalyzer:
    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.db = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.risk_free_rate = config.analysis.risk_free_rate / 100  # Annual rate
    
    def calculate_returns(self, prices: pd.Series) -> pd.Series:
        return prices.pct_change().dropna()
    
    def calculate_cumulative_returns(self, returns: pd.Series) -> pd.Series:
        return (1 + returns).cumprod() - 1
    
    def calculate_basic_metrics(self, returns: pd.Series) -> Dict:
        if len(returns) == 0:
            return {}
        daily_return = returns.mean()
        daily_volatility = returns.std()
        annual_return = daily_return * 252
        annual_volatility = daily_volatility * np.sqrt(252)
        sharpe_ratio = (annual_return - self.risk_free_rate) / annual_volatility if annual_volatility != 0 else 0
        max_return = returns.max()
        min_return = returns.min()
        positive_days = (returns > 0).sum()
        negative_days = (returns < 0).sum()
        win_rate = positive_days / len(returns) if len(returns) > 0 else 0
        skewness = stats.skew(returns)
        kurtosis = stats.kurtosis(returns)
        return {
            'daily_return': daily_return,
            'annual_return': annual_return,
            'daily_volatility': daily_volatility,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_return': max_return,
            'min_return': min_return,
            'win_rate': win_rate,
            'positive_days': positive_days,
            'negative_days': negative_days,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'total_observations': len(returns)
        }
    
    def calculate_drawdown(self, prices: pd.Series) -> Dict:
        if len(prices) == 0:
            return {}
        cumulative = (1 + self.calculate_returns(prices)).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        max_dd_date = drawdown.idxmin()
        drawdown_periods = []
        in_drawdown = False
        start_date = None
        for date, dd in drawdown.items():
            if dd < -0.001 and not in_drawdown:
                in_drawdown = True
                start_date = date
            elif dd >= -0.001 and in_drawdown:
                in_drawdown = False
                if start_date:
                    drawdown_periods.append((start_date, date, (date - start_date).days))
        max_drawdown_duration = max([period[2] for period in drawdown_periods]) if drawdown_periods else 0
        return {
            'max_drawdown': max_drawdown,
            'max_drawdown_date': max_dd_date,
            'max_drawdown_duration_days': max_drawdown_duration,
            'drawdown_periods_count': len(drawdown_periods),
            'current_drawdown': drawdown.iloc[-1] if len(drawdown) > 0 else 0,
            'drawdown_series': drawdown
        }
    
    def calculate_var(self, returns: pd.Series, confidence_levels: List[float] = None) -> Dict:
        if confidence_levels is None:
            confidence_levels = self.config.analysis.confidence_levels
        if len(returns) == 0:
            return {}
        var_results = {}
        for confidence in confidence_levels:
            mean_return = returns.mean()
            std_return = returns.std()
            var_parametric = mean_return - stats.norm.ppf(confidence) * std_return
            var_historical = returns.quantile(1 - confidence)
            skew = stats.skew(returns)
            kurt = stats.kurtosis(returns)
            z_score = stats.norm.ppf(confidence)
            modified_z = (z_score + 
                         (z_score**2 - 1) * skew / 6 + 
                         (z_score**3 - 3*z_score) * kurt / 24 - 
                         (2*z_score**3 - 5*z_score) * skew**2 / 36)
            var_modified = mean_return - modified_z * std_return
            var_results[f'var_{int(confidence*100)}'] = {
                'parametric': var_parametric,
                'historical': var_historical,
                'modified': var_modified
            }
        return var_results
    
    def calculate_advanced_ratios(self, returns: pd.Series) -> Dict:
        if len(returns) == 0:
            return {}
        try:
            negative_returns = returns[returns < 0]
            downside_deviation = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
            annual_return = returns.mean() * 252
            sortino_ratio = (annual_return - self.risk_free_rate) / downside_deviation if downside_deviation != 0 else 0
            prices = (1 + returns).cumprod()
            drawdown_info = self.calculate_drawdown(prices)
            calmar_ratio = abs(annual_return / drawdown_info['max_drawdown']) if drawdown_info.get('max_drawdown', 0) != 0 else 0
            tracking_error = returns.std() * np.sqrt(252)
            information_ratio = annual_return / tracking_error if tracking_error != 0 else 0
            beta = 1.0
            treynor_ratio = (annual_return - self.risk_free_rate) / beta
            return {
                'sortino_ratio': sortino_ratio,
                'calmar_ratio': calmar_ratio,
                'information_ratio': information_ratio,
                'treynor_ratio': treynor_ratio,
                'downside_deviation': downside_deviation,
                'tracking_error': tracking_error
            }
        except Exception as e:
            self.logger.error(f"Gelişmiş oran hesaplama hatası: {e}")
            return {}
    
    def analyze_fund_performance(self, fcode: str, days: int = 252) -> Dict:
        try:
            fund_data = self.db.get_fund_price_history(fcode, days)
            if fund_data.empty:
                self.logger.warning(f"Fon {fcode} için veri bulunamadı")
                return {}
            fund_data = fund_data.set_index('pdate')['price'].sort_index()
            returns = self.calculate_returns(fund_data)
            basic_metrics = self.calculate_basic_metrics(returns)
            drawdown_analysis = self.calculate_drawdown(fund_data)
            var_analysis = self.calculate_var(returns)
            advanced_ratios = self.calculate_advanced_ratios(returns)
            cumulative_returns = self.calculate_cumulative_returns(returns)
            analysis_result = {
                'fcode': fcode,
                'analysis_date': datetime.now(),
                'data_period': {
                    'start_date': fund_data.index.min(),
                    'end_date': fund_data.index.max(),
                    'total_days': len(fund_data)
                },
                'basic_metrics': basic_metrics,
                'drawdown_analysis': drawdown_analysis,
                'var_analysis': var_analysis,
                'advanced_ratios': advanced_ratios,
                'final_cumulative_return': cumulative_returns.iloc[-1] if len(cumulative_returns) > 0 else 0,
                'price_data': fund_data,
                'returns_data': returns,
                'cumulative_returns_data': cumulative_returns
            }
            self.logger.info(f"Fon {fcode} performans analizi tamamlandı")
            return analysis_result
        except Exception as e:
            self.logger.error(f"Fon {fcode} performans analizi hatası: {e}")
            return {}

# --- TOPLU ANALİZ FONKSİYONU (dosyanın sonunda class DIŞINDA olacak!) ---
def batch_analyze_funds_by_details(
    db: DatabaseManager,
    fund_details_df: pd.DataFrame,
    days: int = 252,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Analyze multiple funds with their details (from tefasfunddetails DataFrame).
    Returns a DataFrame with all scores/metrics and fund metadata.
    """
    analyzer = PerformanceAnalyzer(db, db.config)
    results = []
    for idx, row in fund_details_df.iterrows():
        fcode = row["fcode"]
        fund_name = row.get("fund_name", "")
        fund_type = row.get("fund_type", "")
        fund_category = row.get("fund_category", "")
        perf = analyzer.analyze_fund_performance(fcode, days=days)
        basic = perf.get('basic_metrics', {})
        advanced = perf.get('advanced_ratios', {})
        drawdown = perf.get('drawdown_analysis', {})
        results.append({
            "fcode": fcode,
            "fund_name": fund_name,
            "fund_type": fund_type,
            "fund_category": fund_category,
            "annual_return": basic.get('annual_return', 0),
            "annual_volatility": basic.get('annual_volatility', 0),
            "sharpe_ratio": basic.get('sharpe_ratio', 0),
            "sortino_ratio": advanced.get('sortino_ratio', 0),
            "calmar_ratio": advanced.get('calmar_ratio', 0),
            "win_rate": basic.get('win_rate', 0),
            "max_drawdown": drawdown.get('max_drawdown', 0),
        })
        if verbose:
            print(f"{fcode:6} | {fund_type:10} | {fund_category:15} | Sharpe: {basic.get('sharpe_ratio', 0):.2f}")
    result_df = pd.DataFrame(results)
    return result_df.sort_values('sharpe_ratio', ascending=False)
