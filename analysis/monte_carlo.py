# analysis/monte_carlo.py
import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from scipy import stats
from database.connection import DatabaseManager
from config.config import Config

class MonteCarloAnalyzer:
    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.db = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.n_simulations = config.analysis.monte_carlo_simulations
        
    def simulate_price_paths(self, 
                           initial_price: float,
                           daily_return: float,
                           daily_volatility: float,
                           days: int,
                           n_simulations: int = None) -> np.ndarray:
        """Monte Carlo fiyat yolu simülasyonu"""
        if n_simulations is None:
            n_simulations = self.n_simulations
            
        # Rastgele sayı üretimi (normal dağılım)
        random_returns = np.random.normal(
            daily_return, 
            daily_volatility, 
            (n_simulations, days)
        )
        
        # Kümülatif getiriler
        cumulative_returns = np.cumprod(1 + random_returns, axis=1)
        
        # Fiyat yolları
        price_paths = initial_price * cumulative_returns
        
        return price_paths
    
    def geometric_brownian_motion(self,
                                S0: float,  # Başlangıç fiyatı
                                mu: float,  # Drift (günlük getiri)
                                sigma: float,  # Volatilite
                                T: float,  # Zaman (yıl)
                                dt: float = 1/252,  # Zaman adımı (günlük)
                                n_simulations: int = None) -> np.ndarray:
        """Geometrik Brownian Motion simülasyonu"""
        if n_simulations is None:
            n_simulations = self.n_simulations
            
        n_steps = int(T / dt)
        
        # Wiener process (Brownian motion)
        dW = np.random.normal(0, np.sqrt(dt), (n_simulations, n_steps))
        
        # GBM formula: dS = μS dt + σS dW
        # Solution: S(t) = S0 * exp((μ - σ²/2)t + σW(t))
        
        time_steps = np.arange(0, n_steps) * dt
        W = np.cumsum(dW, axis=1)  # Wiener process
        
        # GBM paths
        exponent = (mu - 0.5 * sigma**2) * time_steps + sigma * W
        paths = S0 * np.exp(exponent)
        
        return paths
    
    def calculate_var_cvar(self, 
                          returns: np.ndarray, 
                          confidence_levels: List[float] = None) -> Dict:
        """Value at Risk ve Conditional VaR hesaplama"""
        if confidence_levels is None:
            confidence_levels = self.config.analysis.confidence_levels
            
        results = {}
        
        for confidence in confidence_levels:
            alpha = 1 - confidence
            
            # Value at Risk
            var = np.percentile(returns, alpha * 100)
            
            # Conditional VaR (Expected Shortfall)
            cvar = np.mean(returns[returns <= var])
            
            results[f'var_{int(confidence*100)}'] = var
            results[f'cvar_{int(confidence*100)}'] = cvar
            
        return results
    
    def stress_testing(self, 
                      initial_price: float,
                      historical_returns: pd.Series,
                      scenarios: Dict = None) -> Dict:
        """Stres testi senaryoları"""
        if scenarios is None:
            scenarios = {
                'normal': {'return_shock': 0, 'volatility_multiplier': 1},
                'mild_stress': {'return_shock': -0.10, 'volatility_multiplier': 1.5},
                'moderate_stress': {'return_shock': -0.20, 'volatility_multiplier': 2.0},
                'severe_stress': {'return_shock': -0.35, 'volatility_multiplier': 2.5},
                'extreme_stress': {'return_shock': -0.50, 'volatility_multiplier': 3.0}
            }
        
        base_return = historical_returns.mean()
        base_volatility = historical_returns.std()
        
        stress_results = {}
        
        for scenario_name, scenario_params in scenarios.items():
            # Şoklu parametreler
            stressed_return = base_return + scenario_params['return_shock'] / 252  # Günlük bazda
            stressed_volatility = base_volatility * scenario_params['volatility_multiplier']
            
            # Simülasyon (30 gün)
            price_paths = self.simulate_price_paths(
                initial_price=initial_price,
                daily_return=stressed_return,
                daily_volatility=stressed_volatility,
                days=30,
                n_simulations=1000
            )
            
            # Final fiyatlar
            final_prices = price_paths[:, -1]
            returns = (final_prices / initial_price) - 1
            
            # İstatistikler
            stress_results[scenario_name] = {
                'mean_return': np.mean(returns),
                'std_return': np.std(returns),
                'min_return': np.min(returns),
                'max_return': np.max(returns),
                'var_95': np.percentile(returns, 5),
                'var_99': np.percentile(returns, 1),
                'probability_loss': np.mean(returns < 0),
                'probability_loss_10': np.mean(returns < -0.10),
                'probability_loss_20': np.mean(returns < -0.20),
                'final_prices': final_prices
            }
        
        return stress_results
    
    def portfolio_monte_carlo(self, 
                            fund_codes: List[str],
                            weights: List[float],
                            days: int = 30,
                            n_simulations: int = None) -> Dict:
        """Portföy Monte Carlo simülasyonu"""
        if n_simulations is None:
            n_simulations = self.n_simulations
            
        if len(fund_codes) != len(weights):
            raise ValueError("Fon sayısı ve ağırlık sayısı eşit olmalı")
        
        if abs(sum(weights) - 1.0) > 1e-6:
            raise ValueError("Ağırlıkların toplamı 1 olmalı")
        
        # Her fon için verileri çek
        fund_data = {}
        for fcode in fund_codes:
            data = self.db.get_fund_price_history(fcode, 252)  # 1 yıllık veri
            if not data.empty:
                prices = data.set_index('pdate')['price'].sort_index()
                returns = prices.pct_change().dropna()
                fund_data[fcode] = {
                    'current_price': prices.iloc[-1],
                    'mean_return': returns.mean(),
                    'volatility': returns.std(),
                    'returns': returns
                }
        
        if not fund_data:
            return {}
        
        # Korelasyon matrisi
        returns_matrix = pd.DataFrame({
            fcode: data['returns'] 
            for fcode, data in fund_data.items()
        }).dropna()
        
        correlation_matrix = returns_matrix.corr()
        
        # Çok değişkenli normal dağılım parametreleri
        mean_returns = np.array([fund_data[fcode]['mean_return'] for fcode in fund_codes])
        volatilities = np.array([fund_data[fcode]['volatility'] for fcode in fund_codes])
        
        # Kovaryans matrisi
        cov_matrix = np.outer(volatilities, volatilities) * correlation_matrix.values
        
        # Monte Carlo simülasyonu
        portfolio_returns = []
        
        for _ in range(n_simulations):
            # Rastgele getiriler (çok değişkenli normal)
            random_returns = np.random.multivariate_normal(mean_returns, cov_matrix, days)
            
            # Günlük portföy getirileri
            daily_portfolio_returns = np.dot(random_returns, weights)
            
            # Kümülatif getiri
            cumulative_return = np.prod(1 + daily_portfolio_returns) - 1
            portfolio_returns.append(cumulative_return)
        
        portfolio_returns = np.array(portfolio_returns)
        
        # VaR ve CVaR hesapla
        var_cvar = self.calculate_var_cvar(portfolio_returns)
        
        # İstatistikler
        results = {
            'fund_codes': fund_codes,
            'weights': weights,
            'simulation_days': days,
            'n_simulations': n_simulations,
            'portfolio_statistics': {
                'mean_return': np.mean(portfolio_returns),
                'std_return': np.std(portfolio_returns),
                'min_return': np.min(portfolio_returns),
                'max_return': np.max(portfolio_returns),
                'skewness': stats.skew(portfolio_returns),
                'kurtosis': stats.kurtosis(portfolio_returns)
            },
            'risk_metrics': var_cvar,
            'probability_metrics': {
                'prob_positive': np.mean(portfolio_returns > 0),
                'prob_loss_5': np.mean(portfolio_returns < -0.05),
                'prob_loss_10': np.mean(portfolio_returns < -0.10),
                'prob_loss_20': np.mean(portfolio_returns < -0.20)
            },
            'correlation_matrix': correlation_matrix,
            'individual_fund_data': fund_data,
            'simulated_returns': portfolio_returns
        }
        
        return results
    
    def efficient_frontier_monte_carlo(self, 
                                     fund_codes: List[str],
                                     n_portfolios: int = 10000,
                                     days: int = 30) -> Dict:
        """Monte Carlo ile etkin sınır analizi"""
        # Her fon için verileri çek
        fund_data = {}
        for fcode in fund_codes:
            data = self.db.get_fund_price_history(fcode, 252)
            if not data.empty:
                prices = data.set_index('pdate')['price'].sort_index()
                returns = prices.pct_change().dropna()
                fund_data[fcode] = returns
        
        if len(fund_data) < 2:
            return {}
        
        # Returns matrix
        returns_df = pd.DataFrame(fund_data).dropna()
        mean_returns = returns_df.mean() * 252  # Yıllık
        cov_matrix = returns_df.cov() * 252  # Yıllık
        
        n_assets = len(fund_codes)
        
        # Rastgele portföyler oluştur
        results = []
        
        for _ in range(n_portfolios):
            # Rastgele ağırlıklar
            weights = np.random.random(n_assets)
            weights /= np.sum(weights)  # Normalize et
            
            # Portföy metrikleri
            portfolio_return = np.sum(mean_returns * weights)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            sharpe_ratio = (portfolio_return - self.config.analysis.risk_free_rate) / portfolio_volatility
            
            results.append({
                'weights': weights,
                'return': portfolio_return,
                'volatility': portfolio_volatility,
                'sharpe_ratio': sharpe_ratio
            })
        
        results_df = pd.DataFrame(results)
        
        # En iyi portföyleri bul
        max_sharpe_idx = results_df['sharpe_ratio'].idxmax()
        min_vol_idx = results_df['volatility'].idxmin()
        
        return {
            'efficient_frontier_data': results_df,
            'max_sharpe_portfolio': {
                'weights': dict(zip(fund_codes, results_df.loc[max_sharpe_idx, 'weights'])),
                'expected_return': results_df.loc[max_sharpe_idx, 'return'],
                'volatility': results_df.loc[max_sharpe_idx, 'volatility'],
                'sharpe_ratio': results_df.loc[max_sharpe_idx, 'sharpe_ratio']
            },
            'min_volatility_portfolio': {
                'weights': dict(zip(fund_codes, results_df.loc[min_vol_idx, 'weights'])),
                'expected_return': results_df.loc[min_vol_idx, 'return'],
                'volatility': results_df.loc[min_vol_idx, 'volatility'],
                'sharpe_ratio': results_df.loc[min_vol_idx, 'sharpe_ratio']
            },
            'mean_returns': mean_returns,
            'covariance_matrix': cov_matrix,
            'fund_codes': fund_codes
        }
    
    def black_swan_analysis(self, 
                          initial_price: float,
                          historical_returns: pd.Series,
                          extreme_percentiles: List[float] = [0.1, 0.5, 1.0]) -> Dict:
        """Kara kuğu (black swan) olayları analizi"""
        
        # Geçmiş verideki aşırı olayları tespit et
        historical_extremes = {}
        for percentile in extreme_percentiles:
            lower_threshold = np.percentile(historical_returns, percentile)
            upper_threshold = np.percentile(historical_returns, 100 - percentile)
            
            extreme_negative = historical_returns[historical_returns <= lower_threshold]
            extreme_positive = historical_returns[historical_returns >= upper_threshold]
            
            historical_extremes[f'extreme_{percentile}'] = {
                'negative_events': len(extreme_negative),
                'positive_events': len(extreme_positive),
                'avg_negative_return': extreme_negative.mean() if len(extreme_negative) > 0 else 0,
                'avg_positive_return': extreme_positive.mean() if len(extreme_positive) > 0 else 0,
                'worst_day': extreme_negative.min() if len(extreme_negative) > 0 else 0,
                'best_day': extreme_positive.max() if len(extreme_positive) > 0 else 0
            }
        
        # Aşırı olay senaryoları simülasyonu
        base_return = historical_returns.mean()
        base_volatility = historical_returns.std()
        
        black_swan_scenarios = {
            'market_crash_2008': -0.50,  # %50 düşüş
            'flash_crash': -0.20,        # %20 ani düşüş
            'currency_crisis': -0.35,    # %35 düşüş
            'pandemic_shock': -0.40,     # %40 düşüş
            'extreme_volatility': 0      # Normal getiri ama 5x volatilite
        }
        
        scenario_results = {}
        
        for scenario_name, shock in black_swan_scenarios.items():
            if scenario_name == 'extreme_volatility':
                # Yüksek volatilite senaryosu
                shocked_return = base_return
                shocked_volatility = base_volatility * 5
            else:
                # Getiri şoku senaryosu
                shocked_return = shock / 30  # 30 gün içinde gerçekleşen şok
                shocked_volatility = base_volatility * 2
            
            # 30 günlük simülasyon
            paths = self.simulate_price_paths(
                initial_price=initial_price,
                daily_return=shocked_return,
                daily_volatility=shocked_volatility,
                days=30,
                n_simulations=1000
            )
            
            final_returns = (paths[:, -1] / initial_price) - 1
            
            scenario_results[scenario_name] = {
                'mean_return': np.mean(final_returns),
                'median_return': np.median(final_returns),
                'std_return': np.std(final_returns),
                'var_95': np.percentile(final_returns, 5),
                'var_99': np.percentile(final_returns, 1),
                'worst_case': np.min(final_returns),
                'prob_loss_50': np.mean(final_returns < -0.50),
                'recovery_probability': np.mean(final_returns > 0)
            }
        
        return {
            'historical_extremes': historical_extremes,
            'black_swan_scenarios': scenario_results,
            'analysis_summary': {
                'historical_worst_day': historical_returns.min(),
                'historical_best_day': historical_returns.max(),
                'historical_volatility': historical_returns.std(),
                'extreme_event_frequency': len(historical_returns[abs(historical_returns) > 3 * historical_returns.std()]) / len(historical_returns)
            }
        }
    
    def tail_risk_analysis(self, returns: pd.Series) -> Dict:
        """Kuyruk riski analizi"""
        
        # Extreme Value Theory (EVT) analizi
        def fit_gumbel_distribution(data):
            """Gumbel dağılımı parametrelerini tahmin et"""
            params = stats.gumbel_r.fit(data)
            return params
        
        def fit_weibull_distribution(data):
            """Weibull dağılımı parametrelerini tahmin et"""
            params = stats.weibull_min.fit(data, floc=0)
            return params
        
        # Negatif getiriler (kayıplar)
        losses = -returns[returns < 0]
        
        if len(losses) == 0:
            return {'error': 'Negatif getiri bulunamadı'}
        
        # Threshold aşan değerler (Peaks Over Threshold - POT)
        threshold_95 = np.percentile(losses, 95)
        exceedances = losses[losses > threshold_95] - threshold_95
        
        tail_analysis = {
            'basic_statistics': {
                'total_losses': len(losses),
                'loss_frequency': len(losses) / len(returns),
                'average_loss': losses.mean(),
                'max_loss': losses.max(),
                'loss_volatility': losses.std()
            },
            'extreme_value_analysis': {},
            'tail_estimators': {}
        }
        
        try:
            # Gumbel fit
            gumbel_params = fit_gumbel_distribution(losses.values)
            tail_analysis['extreme_value_analysis']['gumbel'] = {
                'parameters': gumbel_params,
                'var_99': stats.gumbel_r.ppf(0.99, *gumbel_params),
                'expected_shortfall_99': stats.gumbel_r.expect(lambda x: x, args=gumbel_params, lb=stats.gumbel_r.ppf(0.99, *gumbel_params))
            }
        except:
            pass
        
        try:
            # Weibull fit
            weibull_params = fit_weibull_distribution(losses.values)
            tail_analysis['extreme_value_analysis']['weibull'] = {
                'parameters': weibull_params,
                'var_99': stats.weibull_min.ppf(0.99, *weibull_params),
            }
        except:
            pass
        
        # Hill estimator (tail index)
        if len(exceedances) > 10:
            sorted_exceedances = np.sort(exceedances)[::-1]
            k = min(len(sorted_exceedances) - 1, 50)  # Sample size for Hill estimator
            
            if k > 0 and sorted_exceedances[k] > 0:
                hill_estimator = (1/k) * np.sum(np.log(sorted_exceedances[:k] / sorted_exceedances[k]))
                tail_analysis['tail_estimators']['hill_index'] = hill_estimator
                tail_analysis['tail_estimators']['tail_thickness'] = 'Heavy' if hill_estimator > 0.5 else 'Light'
        
        return tail_analysis

class RiskAnalyzer:
    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.db = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.monte_carlo = MonteCarloAnalyzer(db_manager, config)
    
    def calculate_correlation_analysis(self, fund_codes: List[str]) -> Dict:
        """Korelasyon analizi"""
        # Fon verilerini çek
        fund_returns = {}
        
        for fcode in fund_codes:
            data = self.db.get_fund_price_history(fcode, 252)
            if not data.empty:
                prices = data.set_index('pdate')['price'].sort_index()
                returns = prices.pct_change().dropna()
                fund_returns[fcode] = returns
        
        if len(fund_returns) < 2:
            return {}
        
        # Returns DataFrame
        returns_df = pd.DataFrame(fund_returns).dropna()
        
        # Korelasyon matrisi
        correlation_matrix = returns_df.corr()
        
        # Ortalama korelasyonlar
        avg_correlation = correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean()
        
        # En yüksek ve en düşük korelasyonlar
        corr_pairs = []
        for i, fund1 in enumerate(fund_codes):
            for j, fund2 in enumerate(fund_codes[i+1:], i+1):
                if fund1 in correlation_matrix.index and fund2 in correlation_matrix.columns:
                    corr_value = correlation_matrix.loc[fund1, fund2]
                    corr_pairs.append({
                        'fund1': fund1,
                        'fund2': fund2,
                        'correlation': corr_value
                    })
        
        corr_pairs_df = pd.DataFrame(corr_pairs)
        
        # Diversifikasyon analizi
        diversification_ratio = self._calculate_diversification_ratio(returns_df)
        
        return {
            'correlation_matrix': correlation_matrix,
            'average_correlation': avg_correlation,
            'highest_correlations': corr_pairs_df.nlargest(5, 'correlation').to_dict('records'),
            'lowest_correlations': corr_pairs_df.nsmallest(5, 'correlation').to_dict('records'),
            'diversification_ratio': diversification_ratio,
            'correlation_summary': {
                'max_correlation': corr_pairs_df['correlation'].max(),
                'min_correlation': corr_pairs_df['correlation'].min(),
                'correlation_std': corr_pairs_df['correlation'].std()
            }
        }
    
    def _calculate_diversification_ratio(self, returns_df: pd.DataFrame) -> float:
        """Diversifikasyon oranı hesaplama"""
        try:
            # Eşit ağırlıklı portföy varsayımı
            n_assets = len(returns_df.columns)
            weights = np.array([1/n_assets] * n_assets)
            
            # Individual volatilitelerin ağırlıklı ortalaması
            individual_vols = returns_df.std().values
            weighted_avg_vol = np.sum(weights * individual_vols)
            
            # Portföy volatilitesi
            cov_matrix = returns_df.cov().values
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            
            # Diversifikasyon oranı
            diversification_ratio = weighted_avg_vol / portfolio_vol
            
            return diversification_ratio
        except:
            return 1.0
    
    def comprehensive_risk_analysis(self, fcode: str) -> Dict:
        """Kapsamlı risk analizi"""
        try:
            # Fon verilerini çek
            fund_data = self.db.get_fund_price_history(fcode, 500)  # 2 yıllık veri
            
            if fund_data.empty:
                return {}
            
            prices = fund_data.set_index('pdate')['price'].sort_index()
            returns = prices.pct_change().dropna()
            current_price = prices.iloc[-1]
            
            # Monte Carlo simülasyonu
            mc_results = self.monte_carlo.simulate_price_paths(
                initial_price=current_price,
                daily_return=returns.mean(),
                daily_volatility=returns.std(),
                days=30
            )
            
            mc_returns = (mc_results[:, -1] / current_price) - 1
            var_cvar = self.monte_carlo.calculate_var_cvar(mc_returns)
            
            # Stres testi
            stress_results = self.monte_carlo.stress_testing(current_price, returns)
            
            # Kuyruk riski analizi
            tail_risk = self.monte_carlo.tail_risk_analysis(returns)
            
            # Kara kuğu analizi
            black_swan = self.monte_carlo.black_swan_analysis(current_price, returns)
            
            return {
                'fcode': fcode,
                'current_price': current_price,
                'historical_statistics': {
                    'mean_return': returns.mean(),
                    'volatility': returns.std(),
                    'skewness': stats.skew(returns),
                    'kurtosis': stats.kurtosis(returns),
                    'jarque_bera_test': stats.jarque_bera(returns)
                },
                'monte_carlo_results': {
                    'simulated_returns': mc_returns,
                    'var_cvar': var_cvar,
                    'probability_loss': np.mean(mc_returns < 0),
                    'expected_return': np.mean(mc_returns),
                    'worst_case_1_percent': np.percentile(mc_returns, 1)
                },
                'stress_test_results': stress_results,
                'tail_risk_analysis': tail_risk,
                'black_swan_analysis': black_swan,
                'risk_score': self._calculate_risk_score(returns, var_cvar)
            }
            
        except Exception as e:
            self.logger.error(f"Risk analizi hatası {fcode}: {e}")
            return {}
    
    def _calculate_risk_score(self, returns: pd.Series, var_cvar: Dict) -> Dict:
        """Risk skoru hesaplama (0-100 arası)"""
        try:
            # Volatilite skoru (0-30)
            annual_vol = returns.std() * np.sqrt(252)
            vol_score = min(annual_vol * 100, 30)
            
            # VaR skoru (0-30)
            var_95 = abs(var_cvar.get('var_95', 0))
            var_score = min(var_95 * 100, 30)
            
            # Kurtosis skoru (0-20)
            kurt = stats.kurtosis(returns)
            kurtosis_score = min(abs(kurt) * 5, 20)
            
            # Maksimum düşüş skoru (0-20)
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_dd = abs(drawdown.min())
            drawdown_score = min(max_dd * 100, 20)
            
            total_score = vol_score + var_score + kurtosis_score + drawdown_score
            
            return {
                'total_risk_score': total_score,
                'volatility_score': vol_score,
                'var_score': var_score,
                'kurtosis_score': kurtosis_score,
                'drawdown_score': drawdown_score,
                'risk_category': self._get_risk_category(total_score)
            }
        except:
            return {'total_risk_score': 50, 'risk_category': 'Orta'}
    
    def _get_risk_category(self, score: float) -> str:
        """Risk kategorisi belirleme"""
        if score < 20:
            return 'Düşük'
        elif score < 40:
            return 'Orta-Düşük'
        elif score < 60:
            return 'Orta'
        elif score < 80:
            return 'Orta-Yüksek'
        else:
            return 'Yüksek'