# analysis/coordinator.py
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
import json
from pathlib import Path

from database.connection import DatabaseManager
from config.config import Config
from analysis.performance import PerformanceAnalyzer
from analysis.technical import TechnicalAnalyzer
from analysis.monte_carlo import MonteCarloAnalyzer, RiskAnalyzer
from analysis.ai_analysis import AIAnalyzer
from analysis.portfolio_optimization import PortfolioOptimizer

class AnalysisCoordinator:
    """Tüm analiz modüllerini koordine eden ana sınıf"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Database connection
        self.db = DatabaseManager(config)
        
        # Analysis modules
        self.performance_analyzer = PerformanceAnalyzer(self.db, config)
        self.technical_analyzer = TechnicalAnalyzer(self.db, config)
        self.monte_carlo_analyzer = MonteCarloAnalyzer(self.db, config)
        self.risk_analyzer = RiskAnalyzer(self.db, config)
        self.ai_analyzer = AIAnalyzer(self.db, config)
        self.portfolio_optimizer = PortfolioOptimizer(self.db, config)
        
        self.logger.info("Analysis Coordinator başlatıldı")
    
    def comprehensive_fund_analysis(self, fcode: str, days: int = 252) -> Dict:
        """Tek fon için kapsamlı analiz"""
        self.logger.info(f"Fon {fcode} için kapsamlı analiz başlatılıyor...")
        
        analysis_results = {
            'fcode': fcode,
            'analysis_date': datetime.now(),
            'analysis_period_days': days
        }
        
        try:
            # 1. Performance Analysis
            self.logger.info(f"{fcode}: Performans analizi...")
            performance_data = self.performance_analyzer.analyze_fund_performance(fcode, days)
            analysis_results['performance_analysis'] = performance_data
            
            # 2. Technical Analysis
            self.logger.info(f"{fcode}: Teknik analiz...")
            technical_data = self.technical_analyzer.analyze_fund_technical(fcode, days)
            analysis_results['technical_analysis'] = technical_data
            
            # 3. Risk Analysis
            self.logger.info(f"{fcode}: Risk analizi...")
            risk_data = self.risk_analyzer.comprehensive_risk_analysis(fcode)
            analysis_results['risk_analysis'] = risk_data
            
            # 4. AI Analysis
            self.logger.info(f"{fcode}: AI analizi...")
            ai_data = self.ai_analyzer.analyze_fund_with_ai(
                fcode, performance_data, technical_data, risk_data
            )
            analysis_results['ai_analysis'] = ai_data
            
            # 5. Investment Score
            investment_score = self._calculate_investment_score(
                performance_data, technical_data, risk_data, ai_data
            )
            analysis_results['investment_score'] = investment_score
            
            self.logger.info(f"Fon {fcode} analizi tamamlandı")
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Fon {fcode} analiz hatası: {e}")
            analysis_results['error'] = str(e)
            return analysis_results
    
    def multi_fund_comparison(self, fund_codes: List[str], days: int = 252) -> Dict:
        """Çoklu fon karşılaştırması"""
        self.logger.info(f"{len(fund_codes)} fon için karşılaştırmalı analiz başlatılıyor...")
        
        comparison_results = {
            'fund_codes': fund_codes,
            'analysis_date': datetime.now(),
            'individual_analyses': {},
            'comparative_analysis': {}
        }
        
        # Her fon için bireysel analiz
        for fcode in fund_codes:
            try:
                individual_analysis = self.comprehensive_fund_analysis(fcode, days)
                comparison_results['individual_analyses'][fcode] = individual_analysis
                self.logger.info(f"Fon {fcode} analizi tamamlandı")
            except Exception as e:
                self.logger.error(f"Fon {fcode} analiz hatası: {e}")
                comparison_results['individual_analyses'][fcode] = {'error': str(e)}
        
        # Karşılaştırmalı analizler
        try:
            # Performance comparison
            performance_comparison = self.performance_analyzer.compare_funds_performance(fund_codes, days)
            comparison_results['comparative_analysis']['performance'] = performance_comparison
            
            # Technical analysis summary
            technical_batch = self.technical_analyzer.batch_technical_analysis(fund_codes, days)
            comparison_results['comparative_analysis']['technical'] = technical_batch
            
            # Correlation analysis
            correlation_analysis = self.risk_analyzer.calculate_correlation_analysis(fund_codes)
            comparison_results['comparative_analysis']['correlation'] = correlation_analysis
            
            # Portfolio optimization
            portfolio_analysis = self.portfolio_optimizer.comprehensive_portfolio_analysis(fund_codes)
            comparison_results['comparative_analysis']['portfolio_optimization'] = portfolio_analysis
            
            # Market sentiment
            market_sentiment = self.ai_analyzer.generate_market_sentiment(fund_codes)
            comparison_results['comparative_analysis']['market_sentiment'] = market_sentiment
            
            # Overall rankings
            rankings = self._create_overall_rankings(comparison_results['individual_analyses'])
            comparison_results['overall_rankings'] = rankings
            
        except Exception as e:
            self.logger.error(f"Karşılaştırmalı analiz hatası: {e}")
            comparison_results['comparative_analysis']['error'] = str(e)
        
        return comparison_results
    
    def daily_market_analysis(self, top_n_funds: int = 50) -> Dict:
        """Günlük piyasa analizi"""
        self.logger.info("Günlük piyasa analizi başlatılıyor...")
        
        try:
            # En aktif fonları al
            all_funds = self.db.get_all_fund_codes()
            selected_funds = all_funds[:top_n_funds]  # İlk N fonu seç
            
            # Market sentiment
            market_sentiment = self.ai_analyzer.generate_market_sentiment(selected_funds)
            
            # Top performers
            performance_comparison = self.performance_analyzer.compare_funds_performance(
                selected_funds, days=30
            )
            
            # Technical signals
            technical_batch = self.technical_analyzer.batch_technical_analysis(
                selected_funds[:20], days=30  # İlk 20 fon için teknik analiz
            )
            
            daily_analysis = {
                'analysis_date': datetime.now(),
                'funds_analyzed': len(selected_funds),
                'market_sentiment': market_sentiment,
                'performance_summary': performance_comparison,
                'technical_summary': technical_batch,
                'daily_highlights': self._create_daily_highlights(
                    market_sentiment, performance_comparison, technical_batch
                )
            }
            
            return daily_analysis
            
        except Exception as e:
            self.logger.error(f"Günlük analiz hatası: {e}")
            return {'error': str(e)}
    
    def generate_investment_report(self, fund_codes: List[str], 
                                 investment_amount: float = 100000) -> Dict:
        """Yatırım raporu oluştur"""
        self.logger.info("Yatırım raporu oluşturuluyor...")
        
        # Kapsamlı analiz
        analysis_results = self.multi_fund_comparison(fund_codes)
        
        # Portföy önerileri
        portfolio_recommendations = self.portfolio_optimizer.comprehensive_portfolio_analysis(
            fund_codes, investment_amount
        )
        
        # AI destekli rapor
        ai_report = self._generate_ai_investment_report(analysis_results, portfolio_recommendations)
        
        investment_report = {
            'report_date': datetime.now(),
            'investment_amount': investment_amount,
            'fund_analysis': analysis_results,
            'portfolio_recommendations': portfolio_recommendations,
            'ai_insights': ai_report,
            'executive_summary': self._create_executive_summary(analysis_results, portfolio_recommendations),
            'risk_assessment': self._create_risk_assessment(analysis_results),
            'actionable_recommendations': self._create_actionable_recommendations(portfolio_recommendations)
        }
        
        return investment_report
    
    def _calculate_investment_score(self, performance_data: Dict, technical_data: Dict, 
                                  risk_data: Dict, ai_data: Dict) -> Dict:
        """Yatırım skoru hesaplama (0-100 arası)"""
        try:
            total_score = 0
            component_scores = {}
            
            # Performance Score (0-30)
            if performance_data and 'basic_metrics' in performance_data:
                basic = performance_data['basic_metrics']
                sharpe = basic.get('sharpe_ratio', 0)
                annual_return = basic.get('annual_return', 0)
                win_rate = basic.get('win_rate', 0)
                
                perf_score = min(
                    (sharpe * 10) + (annual_return * 50) + (win_rate * 20), 30
                )
                component_scores['performance'] = perf_score
                total_score += perf_score
            
            # Technical Score (0-25)
            if technical_data and 'latest_values' in technical_data:
                signal_strength = technical_data['latest_values'].get('signal_strength', 0)
                trend_analysis = technical_data.get('trend_analysis', {})
                trend_strength = trend_analysis.get('trend_strength', 0)
                
                tech_score = (abs(signal_strength) * 15) + (trend_strength * 10)
                tech_score = min(tech_score, 25)
                component_scores['technical'] = tech_score
                total_score += tech_score
            
            # Risk Score (0-25)
            if risk_data and 'risk_score' in risk_data:
                risk_score = risk_data['risk_score'].get('total_risk_score', 50)
                # Risk skoru ters çevrilir (düşük risk = yüksek puan)
                adjusted_risk_score = max(0, 25 - (risk_score * 0.25))
                component_scores['risk'] = adjusted_risk_score
                total_score += adjusted_risk_score
            
            # AI Score (0-20)
            if ai_data:
                ai_score = 10  # Base score
                
                # Pozitif AI yorumları için bonus
                consensus = ai_data.get('consensus_analysis', '').lower()
                if any(word in consensus for word in ['al', 'pozitif', 'fırsat']):
                    ai_score += 10
                elif any(word in consensus for word in ['sat', 'negatif', 'risk']):
                    ai_score -= 5
                
                ai_score = max(0, min(ai_score, 20))
                component_scores['ai'] = ai_score
                total_score += ai_score
            
            # Score kategorizasyonu
            if total_score >= 80:
                category = "Excellent"
                recommendation = "Strong Buy"
            elif total_score >= 65:
                category = "Good"
                recommendation = "Buy"
            elif total_score >= 50:
                category = "Fair"
                recommendation = "Hold"
            elif total_score >= 35:
                category = "Poor"
                recommendation = "Sell"
            else:
                category = "Very Poor"
                recommendation = "Strong Sell"
            
            return {
                'total_score': total_score,
                'category': category,
                'recommendation': recommendation,
                'component_scores': component_scores
            }
            
        except Exception as e:
            self.logger.error(f"Investment score hesaplama hatası: {e}")
            return {
                'total_score': 50,
                'category': "Unknown",
                'recommendation': "Hold",
                'component_scores': {}
            }
    
    def _create_overall_rankings(self, individual_analyses: Dict) -> Dict:
        """Genel sıralamalar oluştur"""
        rankings = {
            'by_investment_score': [],
            'by_sharpe_ratio': [],
            'by_annual_return': [],
            'by_risk_score': [],
            'by_technical_signal': []
        }
        
        ranking_data = []
        
        for fcode, analysis in individual_analyses.items():
            if 'error' in analysis:
                continue
                
            data_point = {'fcode': fcode}
            
            # Investment score
            investment_score = analysis.get('investment_score', {}).get('total_score', 0)
            data_point['investment_score'] = investment_score
            
            # Performance metrics
            perf = analysis.get('performance_analysis', {}).get('basic_metrics', {})
            data_point['sharpe_ratio'] = perf.get('sharpe_ratio', 0)
            data_point['annual_return'] = perf.get('annual_return', 0)
            
            # Risk score
            risk = analysis.get('risk_analysis', {}).get('risk_score', {})
            data_point['risk_score'] = risk.get('total_risk_score', 50)
            
            # Technical signal
            tech = analysis.get('technical_analysis', {}).get('latest_values', {})
            data_point['technical_signal'] = tech.get('signal_strength', 0)
            
            ranking_data.append(data_point)
        
        if ranking_data:
            df = pd.DataFrame(ranking_data)
            
            # Rankings
            rankings['by_investment_score'] = df.nlargest(10, 'investment_score')['fcode'].tolist()
            rankings['by_sharpe_ratio'] = df.nlargest(10, 'sharpe_ratio')['fcode'].tolist()
            rankings['by_annual_return'] = df.nlargest(10, 'annual_return')['fcode'].tolist()
            rankings['by_risk_score'] = df.nsmallest(10, 'risk_score')['fcode'].tolist()  # Düşük risk = iyi
            rankings['by_technical_signal'] = df.nlargest(10, 'technical_signal')['fcode'].tolist()
        
        return rankings
    
    def _create_daily_highlights(self, market_sentiment: Dict, 
                               performance_comparison: Dict, technical_batch: Dict) -> Dict:
        """Günlük öne çıkanlar"""
        highlights = {
            'top_performers': [],
            'worst_performers': [],
            'strong_buy_signals': [],
            'strong_sell_signals': [],
            'market_mood': 'Unknown'
        }
        
        try:
            # Market mood
            highlights['market_mood'] = market_sentiment.get('market_mood', 'Unknown')
            
            # Top performers
            if performance_comparison and 'summary_stats' in performance_comparison:
                highlights['top_performers'] = [
                    performance_comparison['summary_stats'].get('best_return'),
                    performance_comparison['summary_stats'].get('best_sharpe'),
                    performance_comparison['summary_stats'].get('lowest_volatility')
                ]
            
            # Technical signals
            if technical_batch and 'summary_report' in technical_batch:
                summary = technical_batch['summary_report']
                highlights['strong_buy_signals'] = summary.get('top_buy_candidates', [])[:3]
                highlights['strong_sell_signals'] = summary.get('top_sell_candidates', [])[:3]
            
        except Exception as e:
            self.logger.error(f"Daily highlights oluşturma hatası: {e}")
        
        return highlights
    
    def _generate_ai_investment_report(self, analysis_results: Dict, 
                                     portfolio_recommendations: Dict) -> str:
        """AI destekli yatırım raporu"""
        try:
            report_data = {
                'analyzed_funds': len(analysis_results.get('individual_analyses', {})),
                'top_fund': analysis_results.get('overall_rankings', {}).get('by_investment_score', [None])[0],
                'recommended_portfolio': portfolio_recommendations.get('recommended_portfolio', {}),
                'market_sentiment': analysis_results.get('comparative_analysis', {}).get('market_sentiment', {})
            }
            
            prompt = f"""
            TEFAS Yatırım Raporu Özeti:
            
            Analiz Edilen Fon Sayısı: {report_data['analyzed_funds']}
            En İyi Performans Gösteren Fon: {report_data['top_fund']}
            Önerilen Portföy Metodu: {report_data['recommended_portfolio'].get('method', 'Belirsiz')}
            Piyasa Durumu: {report_data['market_sentiment'].get('market_mood', 'Belirsiz')}
            
            Bu verilere dayanarak yatırımcılar için kapsamlı ve anlaşılır bir rapor hazırla.
            Türkçe yazınız ve objektif öneriler sunun.
            """
            
            return self.ai_analyzer.query_openai(
                prompt, 
                "Sen uzman bir portföy yöneticisisin. TEFAS yatırım fonları konusunda deneyimlisin."
            )
            
        except Exception as e:
            self.logger.error(f"AI rapor oluşturma hatası: {e}")
            return "AI raporu oluşturulamadı"
    
    def _create_executive_summary(self, analysis_results: Dict, 
                                portfolio_recommendations: Dict) -> Dict:
        """Yönetici özeti"""
        try:
            summary = {
                'key_findings': [],
                'recommended_action': 'Hold',
                'risk_level': 'Medium',
                'expected_return': 0,
                'confidence_level': 'Medium'
            }
            
            # Key findings
            top_funds = analysis_results.get('overall_rankings', {}).get('by_investment_score', [])
            if top_funds:
                summary['key_findings'].append(f"En yüksek skorlu fon: {top_funds[0]}")
            
            # Recommended portfolio
            recommended = portfolio_recommendations.get('recommended_portfolio', {})
            if recommended:
                method = recommended.get('method', 'Unknown')
                expected_return = recommended.get('metrics', {}).get('expected_return', 0)
                summary['key_findings'].append(f"Önerilen strateji: {method}")
                summary['expected_return'] = expected_return
                
                if expected_return > 0.15:
                    summary['recommended_action'] = 'Buy'
                elif expected_return < 0.05:
                    summary['recommended_action'] = 'Sell'
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Executive summary oluşturma hatası: {e}")
            return {'error': str(e)}
    
    def _create_risk_assessment(self, analysis_results: Dict) -> Dict:
        """Risk değerlendirmesi"""
        try:
            individual_analyses = analysis_results.get('individual_analyses', {})
            risk_scores = []
            
            for fcode, analysis in individual_analyses.items():
                if 'error' not in analysis:
                    risk_data = analysis.get('risk_analysis', {}).get('risk_score', {})
                    risk_score = risk_data.get('total_risk_score', 50)
                    risk_scores.append(risk_score)
            
            if risk_scores:
                avg_risk = np.mean(risk_scores)
                max_risk = np.max(risk_scores)
                min_risk = np.min(risk_scores)
                
                return {
                    'average_risk_score': avg_risk,
                    'highest_risk_score': max_risk,
                    'lowest_risk_score': min_risk,
                    'risk_distribution': {
                        'low_risk_funds': len([r for r in risk_scores if r < 30]),
                        'medium_risk_funds': len([r for r in risk_scores if 30 <= r < 70]),
                        'high_risk_funds': len([r for r in risk_scores if r >= 70])
                    }
                }
            else:
                return {'error': 'Risk verileri hesaplanamadı'}
                
        except Exception as e:
            self.logger.error(f"Risk assessment hatası: {e}")
            return {'error': str(e)}
    
    def _create_actionable_recommendations(self, portfolio_recommendations: Dict) -> List[Dict]:
        """Uygulanabilir öneriler"""
        recommendations = []
        
        try:
            recommended = portfolio_recommendations.get('recommended_portfolio', {})
            
            if recommended and 'weights' in recommended:
                weights = recommended['weights']
                method = recommended.get('method', 'Unknown')
                
                recommendations.append({
                    'action': 'Portfolio Allocation',
                    'description': f"{method} stratejisi ile portföy oluşturun",
                    'details': weights,
                    'priority': 'High'
                })
                
                # En yüksek ağırlıklı fonlar
                sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
                top_funds = sorted_weights[:3]
                
                for fund, weight in top_funds:
                    if weight > 0.1:  # %10'un üstündeki fonlar
                        recommendations.append({
                            'action': 'Individual Investment',
                            'description': f"{fund} fonuna %{weight*100:.1f} ağırlık verin",
                            'details': {'fund': fund, 'weight': weight},
                            'priority': 'Medium'
                        })
            
            # Genel öneriler
            recommendations.append({
                'action': 'Risk Management',
                'description': 'Portföyünüzü düzenli olarak gözden geçirin',
                'details': {'frequency': 'Aylık', 'focus': 'Risk metrikleri'},
                'priority': 'Low'
            })
            
        except Exception as e:
            self.logger.error(f"Actionable recommendations hatası: {e}")
        
        return recommendations
    
    def save_analysis_results(self, results: Dict, filepath: str):
        """Analiz sonuçlarını dosyaya kaydet"""
        try:
            # Datetime objeleri için custom serializer
            def json_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, pd.DataFrame):
                    return obj.to_dict()
                elif isinstance(obj, pd.Series):
                    return obj.to_dict()
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                else:
                    return str(obj)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, default=json_serializer, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Analiz sonuçları kaydedildi: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Sonuç kaydetme hatası: {e}")
