# analysis/portfolio_optimization.py
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
from scipy.optimize import minimize
from scipy import stats
import cvxpy as cp
from database.connection import DatabaseManager
from config.config import Config

class PortfolioOptimizer:
    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.db = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.risk_free_rate = config.analysis.risk_free_rate / 100
    
    def get_fund_returns_matrix(self, fund_codes: List[str], days: int = 252) -> pd.DataFrame:
        """Fonların getiri matrisini oluştur"""
        returns_data = {}
        
        for fcode in fund_codes:
            try:
                data = self.db.get_fund_price_history(fcode, days)
                if not data.empty:
                    prices = data.set_index('pdate')['price'].sort_index()
                    returns = prices.pct_change().dropna()
                    returns_data[fcode] = returns
            except Exception as e:
                self.logger.warning(f"Fon {fcode} verisi alınamadı: {e}")
        
        # DataFrame oluştur ve eksik verileri temizle
        returns_df = pd.DataFrame(returns_data).dropna()
        
        if returns_df.empty:
            raise ValueError("Geçerli fon verisi bulunamadı")
        
        return returns_df
    
    def calculate_portfolio_metrics(self, weights: np.ndarray, returns_df: pd.DataFrame) -> Dict:
        """Portföy metriklerini hesapla"""
        # Ortalama getiriler (yıllık)
        mean_returns = returns_df.mean() * 252
        
        # Kovaryans matrisi (yıllık)
        cov_matrix = returns_df.cov() * 252
        
        # Portföy getirileri
        portfolio_return = np.sum(mean_returns * weights)
        
        # Portföy volatilitesi
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # Sharpe oranı
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        # Diğer metrikler
        portfolio_returns = returns_df.dot(weights)
        
        # Sortino oranı
        negative_returns = portfolio_returns[portfolio_returns < 0]
        downside_deviation = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
        sortino_ratio = (portfolio_return - self.risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
        
        # VaR hesaplaması
        var_95 = np.percentile(portfolio_returns, 5) * np.sqrt(252)
        var_99 = np.percentile(portfolio_returns, 1) * np.sqrt(252)
        
        return {
            'expected_return': portfolio_return,
            'volatility': portfolio_volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'var_95': var_95,
            'var_99': var_99,
            'skewness': stats.skew(portfolio_returns),
            'kurtosis': stats.kurtosis(portfolio_returns)
        }
    
    def optimize_max_sharpe(self, returns_df: pd.DataFrame, 
                           constraints: Dict = None) -> Dict:
        """Maksimum Sharpe oranı için optimizasyon"""
        
        n_assets = len(returns_df.columns)
        mean_returns = returns_df.mean() * 252
        cov_matrix = returns_df.cov() * 252
        
        # Objective function (negative Sharpe ratio)
        def negative_sharpe(weights):
            portfolio_return = np.sum(mean_returns * weights)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            return -(portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        # Constraints
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # Weights sum to 1
        ]
        
        # Ek kısıtlar
        if constraints:
            if 'max_weight' in constraints:
                for i in range(n_assets):
                    constraints_list.append({
                        'type': 'ineq', 
                        'fun': lambda x, i=i: constraints['max_weight'] - x[i]
                    })
            
            if 'min_weight' in constraints:
                for i in range(n_assets):
                    constraints_list.append({
                        'type': 'ineq', 
                        'fun': lambda x, i=i: x[i] - constraints['min_weight']
                    })
        
        # Bounds (0 <= weight <= 1)
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        # Initial guess (equal weights)
        initial_guess = np.array([1/n_assets] * n_assets)
        
        # Optimization
        result = minimize(
            negative_sharpe,
            initial_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list
        )
        
        if result.success:
            optimal_weights = result.x
            portfolio_metrics = self.calculate_portfolio_metrics(optimal_weights, returns_df)
            
            return {
                'success': True,
                'weights': dict(zip(returns_df.columns, optimal_weights)),
                'metrics': portfolio_metrics,
                'optimization_result': result
            }
        else:
            return {
                'success': False,
                'error': result.message
            }
    
    def optimize_min_volatility(self, returns_df: pd.DataFrame,
                               target_return: float = None,
                               constraints: Dict = None) -> Dict:
        """Minimum volatilite için optimizasyon"""
        
        n_assets = len(returns_df.columns)
        mean_returns = returns_df.mean() * 252
        cov_matrix = returns_df.cov() * 252
        
        # Objective function (portfolio variance)
        def portfolio_variance(weights):
            return np.dot(weights.T, np.dot(cov_matrix, weights))
        
        # Constraints
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # Weights sum to 1
        ]
        
        # Target return constraint
        if target_return:
            constraints_list.append({
                'type': 'eq',
                'fun': lambda x: np.sum(mean_returns * x) - target_return
            })
        
        # Additional constraints
        if constraints:
            if 'max_weight' in constraints:
                for i in range(n_assets):
                    constraints_list.append({
                        'type': 'ineq', 
                        'fun': lambda x, i=i: constraints['max_weight'] - x[i]
                    })
        
        bounds = tuple((0, 1) for _ in range(n_assets))
        initial_guess = np.array([1/n_assets] * n_assets)
        
        result = minimize(
            portfolio_variance,
            initial_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list
        )
        
        if result.success:
            optimal_weights = result.x
            portfolio_metrics = self.calculate_portfolio_metrics(optimal_weights, returns_df)
            
            return {
                'success': True,
                'weights': dict(zip(returns_df.columns, optimal_weights)),
                'metrics': portfolio_metrics,
                'optimization_result': result
            }
        else:
            return {
                'success': False,
                'error': result.message
            }
    
    def generate_efficient_frontier(self, returns_df: pd.DataFrame, 
                                  n_portfolios: int = 100) -> Dict:
        """Etkin sınır oluştur"""
        
        mean_returns = returns_df.mean() * 252
        min_return = mean_returns.min()
        max_return = mean_returns.max()
        
        # Target return aralığı
        target_returns = np.linspace(min_return, max_return, n_portfolios)
        
        efficient_portfolios = []
        
        for target_return in target_returns:
            try:
                result = self.optimize_min_volatility(returns_df, target_return)
                if result['success']:
                    efficient_portfolios.append({
                        'target_return': target_return,
                        'volatility': result['metrics']['volatility'],
                        'sharpe_ratio': result['metrics']['sharpe_ratio'],
                        'weights': result['weights']
                    })
            except Exception as e:
                self.logger.warning(f"Efficient frontier hesaplama hatası: {e}")
                continue
        
        if not efficient_portfolios:
            return {'success': False, 'error': 'Etkin sınır hesaplanamadı'}
        
        # En iyi portföyleri bul
        efficient_df = pd.DataFrame(efficient_portfolios)
        
        # Maximum Sharpe ratio portfolio
        max_sharpe_idx = efficient_df['sharpe_ratio'].idxmax()
        max_sharpe_portfolio = efficient_df.loc[max_sharpe_idx]
        
        # Minimum volatility portfolio
        min_vol_idx = efficient_df['volatility'].idxmin()
        min_vol_portfolio = efficient_df.loc[min_vol_idx]
        
        return {
            'success': True,
            'efficient_frontier': efficient_df,
            'max_sharpe_portfolio': max_sharpe_portfolio.to_dict(),
            'min_volatility_portfolio': min_vol_portfolio.to_dict(),
            'capital_allocation_line': self._calculate_cal(efficient_df)
        }
    
    def _calculate_cal(self, efficient_df: pd.DataFrame) -> Dict:
        """Capital Allocation Line hesapla"""
        try:
            max_sharpe_idx = efficient_df['sharpe_ratio'].idxmax()
            optimal_portfolio = efficient_df.loc[max_sharpe_idx]
            
            # CAL slope = Sharpe ratio
            cal_slope = optimal_portfolio['sharpe_ratio']
            
            return {
                'slope': cal_slope,
                'intercept': self.risk_free_rate,
                'optimal_portfolio_return': optimal_portfolio['target_return'],
                'optimal_portfolio_volatility': optimal_portfolio['volatility']
            }
        except:
            return {}
    
    def risk_parity_optimization(self, returns_df: pd.DataFrame) -> Dict:
        """Risk Parity optimizasyonu"""
        
        n_assets = len(returns_df.columns)
        cov_matrix = returns_df.cov() * 252
        
        def risk_parity_objective(weights):
            """Risk contributions'ın eşitliğini minimize et"""
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            marginal_contrib = np.dot(cov_matrix, weights)
            contrib = weights * marginal_contrib
            
            # Risk contributions'ın standart sapması
            target_contrib = portfolio_variance / n_assets
            return np.sum((contrib - target_contrib)**2)
        
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        ]
        
        bounds = tuple((0.01, 0.5) for _ in range(n_assets))  # Min %1, Max %50
        initial_guess = np.array([1/n_assets] * n_assets)
        
        result = minimize(
            risk_parity_objective,
            initial_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if result.success:
            optimal_weights = result.x
            portfolio_metrics = self.calculate_portfolio_metrics(optimal_weights, returns_df)
            
            # Risk contributions
            portfolio_variance = np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights))
            marginal_contrib = np.dot(cov_matrix, optimal_weights)
            risk_contrib = optimal_weights * marginal_contrib / portfolio_variance
            
            return {
                'success': True,
                'weights': dict(zip(returns_df.columns, optimal_weights)),
                'risk_contributions': dict(zip(returns_df.columns, risk_contrib)),
                'metrics': portfolio_metrics
            }
        else:
            return {
                'success': False,
                'error': result.message
            }
    
    def black_litterman_optimization(self, returns_df: pd.DataFrame,
                                   views: Dict = None,
                                   tau: float = 0.025) -> Dict:
        """Black-Litterman modeli ile optimizasyon"""
        
        n_assets = len(returns_df.columns)
        
        # Historical parameters
        mu_hist = returns_df.mean() * 252  # Historical returns
        sigma = returns_df.cov() * 252     # Covariance matrix
        
        # Market cap weights (equal weights varsayımı)
        w_market = np.array([1/n_assets] * n_assets)
        
        # Implied equilibrium returns
        risk_aversion = 3.0  # Typical risk aversion parameter
        pi = risk_aversion * np.dot(sigma, w_market)
        
        if views is None:
            # Views yoksa sadece equilibrium returns kullan
            mu_bl = pi
            sigma_bl = sigma
        else:
            # Views varsa Black-Litterman formülünü uygula
            P, Q, Omega = self._process_views(views, returns_df.columns, sigma)
            
            if P is not None:
                # Black-Litterman formülü
                tau_sigma = tau * sigma
                M1 = np.linalg.inv(tau_sigma)
                M2 = np.dot(P.T, np.dot(np.linalg.inv(Omega), P))
                M3 = np.dot(np.linalg.inv(tau_sigma), pi)
                M4 = np.dot(P.T, np.dot(np.linalg.inv(Omega), Q))
                
                mu_bl = np.dot(np.linalg.inv(M1 + M2), M3 + M4)
                sigma_bl = np.linalg.inv(M1 + M2)
            else:
                mu_bl = pi
                sigma_bl = sigma
        
        # Mean-variance optimization with Black-Litterman inputs
        def negative_sharpe_bl(weights):
            portfolio_return = np.sum(mu_bl * weights)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(sigma_bl, weights)))
            return -(portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        bounds = tuple((0, 1) for _ in range(n_assets))
        initial_guess = w_market
        
        result = minimize(
            negative_sharpe_bl,
            initial_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if result.success:
            optimal_weights = result.x
            portfolio_metrics = self.calculate_portfolio_metrics(optimal_weights, returns_df)
            
            return {
                'success': True,
                'weights': dict(zip(returns_df.columns, optimal_weights)),
                'metrics': portfolio_metrics,
                'equilibrium_returns': dict(zip(returns_df.columns, pi)),
                'bl_returns': dict(zip(returns_df.columns, mu_bl)),
                'views_applied': views is not None
            }
        else:
            return {
                'success': False,
                'error': result.message
            }
    
    def _process_views(self, views: Dict, fund_codes: List[str], sigma: np.ndarray) -> Tuple:
        """Views'ları Black-Litterman formatına çevir"""
        try:
            n_assets = len(fund_codes)
            fund_to_idx = {fund: idx for idx, fund in enumerate(fund_codes)}
            
            # Views listesi
            view_list = []
            for view_desc, view_data in views.items():
                if 'funds' in view_data and 'expected_return' in view_data:
                    view_vector = np.zeros(n_assets)
                    for fund, weight in view_data['funds'].items():
                        if fund in fund_to_idx:
                            view_vector[fund_to_idx[fund]] = weight
                    
                    view_list.append({
                        'vector': view_vector,
                        'return': view_data['expected_return'],
                        'confidence': view_data.get('confidence', 0.5)
                    })
            
            if not view_list:
                return None, None, None
            
            # P matrix (picking matrix)
            P = np.array([view['vector'] for view in view_list])
            
            # Q vector (expected returns for views)
            Q = np.array([view['return'] for view in view_list])
            
            # Omega matrix (uncertainty of views)
            Omega = np.diag([
                view['confidence'] * np.dot(view['vector'], np.dot(sigma, view['vector']))
                for view in view_list
            ])
            
            return P, Q, Omega
            
        except Exception as e:
            self.logger.error(f"Views işleme hatası: {e}")
            return None, None, None
    
    def cvar_optimization(self, returns_df: pd.DataFrame, 
                         alpha: float = 0.05,
                         target_return: float = None) -> Dict:
        """Conditional Value at Risk (CVaR) optimizasyonu"""
        
        n_assets = len(returns_df.columns)
        n_scenarios = len(returns_df)
        
        # CVaR optimization using cvxpy
        w = cp.Variable(n_assets)  # Portfolio weights
        z = cp.Variable(n_scenarios)  # Auxiliary variables for CVaR
        var = cp.Variable()  # Value at Risk
        
        # Scenario returns
        returns_matrix = returns_df.values
        
        # CVaR constraint
        cvar_constraint = [
            z[i] >= -(returns_matrix[i, :] @ w) - var
            for i in range(n_scenarios)
        ]
        cvar_constraint.extend([z >= 0])
        
        # CVaR objective (minimize)
        cvar = var + (1 / (alpha * n_scenarios)) * cp.sum(z)
        
        # Constraints
        constraints = [
            cp.sum(w) == 1,  # Weights sum to 1
            w >= 0,  # Long only
            w <= 0.5  # Maximum 50% in any asset
        ]
        constraints.extend(cvar_constraint)
        
        # Target return constraint
        if target_return:
            mean_returns = returns_df.mean().values * 252
            constraints.append(mean_returns @ w >= target_return)
        
        # Optimization problem
        problem = cp.Problem(cp.Minimize(cvar), constraints)
        
        try:
            problem.solve(solver=cp.ECOS)
            
            if problem.status == cp.OPTIMAL:
                optimal_weights = w.value
                portfolio_metrics = self.calculate_portfolio_metrics(optimal_weights, returns_df)
                
                return {
                    'success': True,
                    'weights': dict(zip(returns_df.columns, optimal_weights)),
                    'metrics': portfolio_metrics,
                    'cvar': cvar.value,
                    'var': var.value
                }
            else:
                return {
                    'success': False,
                    'error': f'Optimization failed: {problem.status}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'CVaR optimization error: {e}'
            }
    
    def robust_optimization(self, returns_df: pd.DataFrame,
                           uncertainty_level: float = 0.1) -> Dict:
        """Robust portföy optimizasyonu"""
        
        n_assets = len(returns_df.columns)
        mean_returns = returns_df.mean() * 252
        cov_matrix = returns_df.cov() * 252
        
        # Uncertainty set parameters
        gamma = uncertainty_level  # Uncertainty budget
        
        # Robust optimization using cvxpy
        w = cp.Variable(n_assets)
        
        # Robust objective: min w'Σw + γ||Σ^(1/2)w||_2
        portfolio_variance = cp.quad_form(w, cov_matrix.values)
        
        # Uncertainty term
        sigma_sqrt = np.linalg.cholesky(cov_matrix.values)
        uncertainty_term = gamma * cp.norm(sigma_sqrt.T @ w, 2)
        
        objective = portfolio_variance + uncertainty_term
        
        constraints = [
            cp.sum(w) == 1,
            w >= 0,
            w <= 0.4  # Maximum 40% in any asset
        ]
        
        problem = cp.Problem(cp.Minimize(objective), constraints)
        
        try:
            problem.solve()
            
            if problem.status == cp.OPTIMAL:
                optimal_weights = w.value
                portfolio_metrics = self.calculate_portfolio_metrics(optimal_weights, returns_df)
                
                return {
                    'success': True,
                    'weights': dict(zip(returns_df.columns, optimal_weights)),
                    'metrics': portfolio_metrics,
                    'uncertainty_level': uncertainty_level,
                    'robust_objective': objective.value
                }
            else:
                return {
                    'success': False,
                    'error': f'Robust optimization failed: {problem.status}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Robust optimization error: {e}'
            }
    
    def multi_objective_optimization(self, returns_df: pd.DataFrame,
                                   objectives: Dict = None) -> Dict:
        """Çok amaçlı optimizasyon"""
        
        if objectives is None:
            objectives = {
                'return': 0.4,      # Return weight
                'risk': 0.3,        # Risk (volatility) weight
                'diversification': 0.2,  # Diversification weight
                'esg': 0.1          # ESG weight (placeholder)
            }
        
        n_assets = len(returns_df.columns)
        mean_returns = returns_df.mean() * 252
        cov_matrix = returns_df.cov() * 252
        
        def multi_objective_function(weights):
            # Return component (maximize)
            portfolio_return = np.sum(mean_returns * weights)
            return_score = portfolio_return / mean_returns.max()
            
            # Risk component (minimize)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            risk_score = 1 - (portfolio_volatility / np.sqrt(np.diag(cov_matrix)).max())
            
            # Diversification component (maximize)
            # Herfindahl index (minimize concentration)
            diversification_score = 1 - np.sum(weights**2)
            
            # ESG component (placeholder - equal weights)
            esg_score = 0.5  # Would be based on actual ESG scores
            
            # Weighted combination
            total_score = (
                objectives['return'] * return_score +
                objectives['risk'] * risk_score +
                objectives['diversification'] * diversification_score +
                objectives['esg'] * esg_score
            )
            
            return -total_score  # Minimize negative score (maximize score)
        
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        ]
        
        bounds = tuple((0.01, 0.3) for _ in range(n_assets))  # Min 1%, Max 30%
        initial_guess = np.array([1/n_assets] * n_assets)
        
        result = minimize(
            multi_objective_function,
            initial_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if result.success:
            optimal_weights = result.x
            portfolio_metrics = self.calculate_portfolio_metrics(optimal_weights, returns_df)
            
            return {
                'success': True,
                'weights': dict(zip(returns_df.columns, optimal_weights)),
                'metrics': portfolio_metrics,
                'objectives': objectives,
                'total_score': -result.fun
            }
        else:
            return {
                'success': False,
                'error': result.message
            }
    
    def comprehensive_portfolio_analysis(self, fund_codes: List[str],
                                       investment_amount: float = 100000,
                                       optimization_methods: List[str] = None) -> Dict:
        """Kapsamlı portföy analizi"""
        
        if optimization_methods is None:
            optimization_methods = [
                'max_sharpe', 'min_volatility', 'risk_parity',
                'cvar', 'robust', 'multi_objective'
            ]
        
        try:
            # Returns matrix
            returns_df = self.get_fund_returns_matrix(fund_codes)
            
            if len(returns_df.columns) < 2:
                return {'error': 'En az 2 fon gerekli'}
            
            results = {
                'fund_codes': list(returns_df.columns),
                'analysis_period': f"{returns_df.index[0]} - {returns_df.index[-1]}",
                'investment_amount': investment_amount,
                'optimizations': {}
            }
            
            # Her optimizasyon metodunu çalıştır
            if 'max_sharpe' in optimization_methods:
                results['optimizations']['max_sharpe'] = self.optimize_max_sharpe(returns_df)
            
            if 'min_volatility' in optimization_methods:
                results['optimizations']['min_volatility'] = self.optimize_min_volatility(returns_df)
            
            if 'risk_parity' in optimization_methods:
                results['optimizations']['risk_parity'] = self.risk_parity_optimization(returns_df)
            
            if 'efficient_frontier' in optimization_methods:
                results['efficient_frontier'] = self.generate_efficient_frontier(returns_df)
            
            if 'cvar' in optimization_methods:
                results['optimizations']['cvar'] = self.cvar_optimization(returns_df)
            
            if 'robust' in optimization_methods:
                results['optimizations']['robust'] = self.robust_optimization(returns_df)
            
            if 'multi_objective' in optimization_methods:
                results['optimizations']['multi_objective'] = self.multi_objective_optimization(returns_df)
            
            # En iyi portföyü seç
            best_portfolio = self._select_best_portfolio(results['optimizations'])
            results['recommended_portfolio'] = best_portfolio
            
            # Yatırım önerileri
            if best_portfolio and 'weights' in best_portfolio:
                investment_allocation = {
                    fund: weight * investment_amount
                    for fund, weight in best_portfolio['weights'].items()
                }
                results['investment_allocation'] = investment_allocation
            
            return results
            
        except Exception as e:
            self.logger.error(f"Portföy analizi hatası: {e}")
            return {'error': str(e)}
    
    def _select_best_portfolio(self, optimizations: Dict) -> Dict:
        """En iyi portföyü seç"""
        best_portfolio = None
        best_score = -np.inf
        
        for method, result in optimizations.items():
            if result.get('success') and 'metrics' in result:
                metrics = result['metrics']
                
                # Scoring: Sharpe ratio + return/risk ratio
                score = (
                    metrics.get('sharpe_ratio', 0) * 0.6 +
                    (metrics.get('expected_return', 0) / max(metrics.get('volatility', 1), 0.01)) * 0.4
                )
                
                if score > best_score:
                    best_score = score
                    best_portfolio = {
                        'method': method,
                        'weights': result['weights'],
                        'metrics': metrics,
                        'score': score
                    }
        
        return best_portfolio