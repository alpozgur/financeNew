# analysis/ai_analysis.py
"""
AI Analysis Module - OpenAI 1.0+ Compatible
TEFAS fonları için AI destekli analiz ve yorumlama
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import logging
import json
import requests
from datetime import datetime, timedelta
from database.connection import DatabaseManager
from config.config import Config

class AIAnalyzer:
    """AI destekli analiz sistemi - OpenAI 1.0+ ve Ollama destekli"""
    
    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.db = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # OpenAI kurulumu (yeni versiyon)
        self.openai_client = None
        self.openai_available = False
        self._setup_openai()
        
        # Ollama kurulumu
        self.ollama_base_url = config.ai.ollama_base_url
        self.ollama_model = config.ai.ollama_model
        self.ollama_available = self._check_ollama_connection()
        
        self.logger.info("AI Analyzer initialized")
    
    def _setup_openai(self):
        """OpenAI client'ı kur"""
        try:
            if self.config.ai.openai_api_key:
                # OpenAI 1.0+ import
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.config.ai.openai_api_key)
                self.openai_available = True
                self.logger.info("OpenAI client initialized successfully")
            else:
                self.logger.warning("OpenAI API key not found")
        except ImportError:
            self.logger.warning("OpenAI library not installed or version incompatible")
        except Exception as e:
            self.logger.error(f"OpenAI setup error: {e}")
    
    def _check_ollama_connection(self) -> bool:
        """Ollama bağlantısını kontrol et"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.logger.info("Ollama connection successful")
                return True
            else:
                self.logger.warning(f"Ollama connection failed: {response.status_code}")
                return False
        except Exception as e:
            self.logger.warning(f"Ollama connection error: {e}")
            return False
    
    def query_openai(self, prompt: str, system_message: str = None, model: str = "gpt-3.5-turbo") -> str:
        """OpenAI API ile analiz yap (yeni versiyon)"""
        if not self.openai_available:
            return "OpenAI API kullanılamıyor - API key eksik veya yanlış"
        
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            return f"OpenAI analizi başarısız: {str(e)[:100]}"
    
    def query_ollama(self, prompt: str, system_message: str = None) -> str:
        """Ollama ile analiz yap"""
        if not self.ollama_available:
            return "Ollama kullanılamıyor - Bağlantı kurulamadı"
        
        try:
            full_prompt = prompt
            if system_message:
                full_prompt = f"{system_message}\n\nUser Question: {prompt}"
            
            payload = {
                "model": self.ollama_model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 1000
                }
            }
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'Yanıt alınamadı')
            else:
                return f"Ollama API error: {response.status_code}"
                
        except Exception as e:
            self.logger.error(f"Ollama API error: {e}")
            return f"Ollama analizi başarısız: {str(e)[:100]}"
    
    def analyze_fund_with_ai(self, 
                           fcode: str, 
                           performance_data: Dict = None, 
                           technical_data: Dict = None,
                           risk_data: Dict = None,
                           use_openai: bool = True,
                           use_ollama: bool = True) -> Dict:
        """Fon verilerini AI ile analiz et"""
        
        # Analiz için veri özeti hazırla
        data_summary = self._prepare_fund_summary(fcode, performance_data, technical_data, risk_data)
        
        # System message (AI'a rolü tanımla)
        system_message = """
        Sen uzman bir finansal analist ve yatırım danışmanısın. Türk yatırım fonları (TEFAS) konusunda derin bilgin var.
        Verilen fon analiz verilerini yorumlayarak:
        1. Fonun genel durumu hakkında objektif değerlendirme
        2. Güçlü ve zayıf yönleri
        3. Risk seviyesi değerlendirmesi
        4. Yatırım önerisi (Al/Sat/Bekle)
        5. Teknik analiz yorumu
        6. Gelecek beklentileri
        
        Türkçe yanıt ver, maksimum 500 kelime kullan.
        """
        
        # Analiz prompt'u
        prompt = f"""
        {fcode} kodlu TEFAS fonu için analiz verilerini yorumla:

        {data_summary}

        Bu verilere dayanarak kısa ve özlü bir analiz raporu hazırla.
        """
        
        results = {
            'fcode': fcode,
            'analysis_timestamp': datetime.now(),
            'data_summary': data_summary
        }
        
        # OpenAI analizi
        if use_openai and self.openai_available:
            try:
                openai_analysis = self.query_openai(prompt, system_message)
                results['openai_analysis'] = openai_analysis
                self.logger.info(f"OpenAI analysis completed for {fcode}")
            except Exception as e:
                results['openai_analysis'] = f"OpenAI analizi başarısız: {e}"
                self.logger.error(f"OpenAI analysis failed for {fcode}: {e}")
        
        # Ollama analizi
        if use_ollama and self.ollama_available:
            try:
                ollama_analysis = self.query_ollama(prompt, system_message)
                results['ollama_analysis'] = ollama_analysis
                self.logger.info(f"Ollama analysis completed for {fcode}")
            except Exception as e:
                results['ollama_analysis'] = f"Ollama analizi başarısız: {e}"
                self.logger.error(f"Ollama analysis failed for {fcode}: {e}")
        
        # Konsensüs analizi (her iki AI'dan gelen önerileri karşılaştır)
        if 'openai_analysis' in results and 'ollama_analysis' in results:
            consensus = self._create_consensus_analysis(results['openai_analysis'], results['ollama_analysis'])
            results['consensus_analysis'] = consensus
        elif 'openai_analysis' in results:
            results['consensus_analysis'] = results['openai_analysis']
        elif 'ollama_analysis' in results:
            results['consensus_analysis'] = results['ollama_analysis']
        else:
            results['consensus_analysis'] = "AI analizi mevcut değil"
        
        return results
    
    def _prepare_fund_summary(self, 
                            fcode: str, 
                            performance_data: Dict = None, 
                            technical_data: Dict = None, 
                            risk_data: Dict = None) -> str:
        """AI analizi için fon verileri özetini hazırla"""
        
        summary_parts = [f"Fon Kodu: {fcode}"]
        
        # Performans verileri
        if performance_data and isinstance(performance_data, dict) and 'basic_metrics' in performance_data:
            basic = performance_data['basic_metrics']
            summary_parts.extend([
                "\nPERFORMANS VERİLERİ:",
                f"- Yıllık Getiri: %{basic.get('annual_return', 0) * 100:.2f}",
                f"- Yıllık Volatilite: %{basic.get('annual_volatility', 0) * 100:.2f}",
                f"- Sharpe Oranı: {basic.get('sharpe_ratio', 0):.3f}",
                f"- Kazanma Oranı: %{basic.get('win_rate', 0) * 100:.1f}"
            ])
            
            if 'drawdown_analysis' in performance_data:
                dd = performance_data['drawdown_analysis']
                summary_parts.append(f"- Maksimum Düşüş: %{dd.get('max_drawdown', 0) * 100:.2f}")
        
        # Teknik analiz verileri
        if technical_data and isinstance(technical_data, dict) and 'latest_values' in technical_data:
            latest = technical_data['latest_values']
            summary_parts.extend([
                "\nTEKNİK ANALİZ VERİLERİ:",
                f"- Güncel Fiyat: {latest.get('price', 0):.4f} TL",
                f"- RSI: {latest.get('rsi', 0):.1f}",
                f"- Sinyal Gücü: {latest.get('signal_strength', 0):.2f}"
            ])
            
            if 'trend_analysis' in technical_data:
                trend = technical_data['trend_analysis']
                summary_parts.append(f"- Genel Trend: {trend.get('overall_trend', 'Belirsiz')}")
        
        # Risk analizi verileri
        if risk_data and isinstance(risk_data, dict) and 'risk_score' in risk_data:
            risk_score = risk_data['risk_score']
            summary_parts.extend([
                "\nRİSK ANALİZİ VERİLERİ:",
                f"- Risk Kategorisi: {risk_score.get('risk_category', 'Belirsiz')}",
                f"- Risk Skoru: {risk_score.get('total_risk_score', 0):.1f}/100"
            ])
        
        return "\n".join(summary_parts)
    
    def _create_consensus_analysis(self, openai_response: str, ollama_response: str) -> str:
        """İki AI yanıtından konsensüs analizi oluştur"""
        
        # Basit konsensüs - her iki yanıt varsa OpenAI'ı öncelikle
        if len(openai_response) > 50 and "başarısız" not in openai_response.lower():
            return openai_response
        elif len(ollama_response) > 50 and "başarısız" not in ollama_response.lower():
            return ollama_response
        else:
            return "Güvenilir AI analizi oluşturulamadı"
    
    def generate_market_sentiment(self, fund_codes: List[str]) -> Dict:
        """Piyasa duyarlılığı analizi"""
        
        if len(fund_codes) == 0:
            return {'error': 'Analiz için fon bulunamadı'}
        
        # Son 30 günlük verileri topla
        market_data = []
        
        for fcode in fund_codes[:20]:  # İlk 20 fonu analiz et
            try:
                data = self.db.get_fund_price_history(fcode, 30)
                if not data.empty:
                    prices = data.set_index('pdate')['price'].sort_index()
                    returns = prices.pct_change().dropna()
                    
                    total_return = (prices.iloc[-1] / prices.iloc[0]) - 1
                    volatility = returns.std()
                    positive_days_ratio = (returns > 0).sum() / len(returns)
                    
                    market_data.append({
                        'fcode': fcode,
                        'total_return': total_return,
                        'volatility': volatility,
                        'positive_days': positive_days_ratio
                    })
            except Exception as e:
                self.logger.warning(f"Market sentiment error for {fcode}: {e}")
                continue
        
        if not market_data:
            return {'error': 'Market sentiment için veri bulunamadı'}
        
        market_df = pd.DataFrame(market_data)
        
        # Piyasa metrikleri
        avg_return = market_df['total_return'].mean()
        positive_funds_ratio = (market_df['total_return'] > 0).sum() / len(market_df)
        avg_volatility = market_df['volatility'].mean()
        
        # Duyarlılık skoru hesapla (0-100)
        sentiment_score = (
            (positive_funds_ratio * 40) +  # Pozitif fon oranı
            (min(max(avg_return * 100 + 10, 0), 30)) +  # Ortalama getiri
            (max(30 - avg_volatility * 1000, 0))  # Düşük volatilite bonusu
        )
        
        # Piyasa durumu
        if sentiment_score > 70:
            market_mood = "Çok Pozitif"
        elif sentiment_score > 50:
            market_mood = "Pozitif"
        elif sentiment_score > 30:
            market_mood = "Nötr"
        else:
            market_mood = "Negatif"
        
        # AI yorumu iste
        sentiment_summary = f"""
        Son 30 günlük TEFAS piyasa analizi:
        - Analiz edilen fon sayısı: {len(market_df)}
        - Ortalama getiri: %{avg_return * 100:.2f}
        - Pozitif performans oranı: %{positive_funds_ratio * 100:.1f}
        - Ortalama volatilite: %{avg_volatility * 100:.2f}
        - Duyarlılık skoru: {sentiment_score:.1f}/100
        - Piyasa durumu: {market_mood}
        
        Bu verilere dayanarak TEFAS piyasasının genel durumu ve yatırımcı önerileri hakkında kısa yorum yap.
        """
        
        ai_commentary = {}
        
        # AI yorumları al
        if self.openai_available:
            try:
                ai_commentary['openai'] = self.query_openai(
                    sentiment_summary,
                    "Sen TEFAS piyasası uzmanı bir analistsin."
                )
            except Exception as e:
                ai_commentary['openai'] = f"OpenAI market analizi başarısız: {e}"
        
        if self.ollama_available:
            try:
                ai_commentary['ollama'] = self.query_ollama(
                    sentiment_summary,
                    "Sen TEFAS piyasası uzmanı bir analistsin."
                )
            except Exception as e:
                ai_commentary['ollama'] = f"Ollama market analizi başarısız: {e}"
        
        return {
            'sentiment_score': sentiment_score,
            'market_mood': market_mood,
            'market_statistics': {
                'funds_analyzed': len(market_df),
                'average_return': avg_return,
                'positive_funds_ratio': positive_funds_ratio,
                'average_volatility': avg_volatility
            },
            'top_performers': market_df.nlargest(3, 'total_return')['fcode'].tolist(),
            'worst_performers': market_df.nsmallest(3, 'total_return')['fcode'].tolist(),
            'ai_commentary': ai_commentary,
            'analysis_date': datetime.now(),
            'raw_data': market_df.to_dict('records')
        }
    
    def predict_fund_performance(self, 
                               fcode: str, 
                               days_ahead: int = 30,
                               use_ai: bool = True) -> Dict:
        """AI destekli fon performans tahmini"""
        
        try:
            # Geçmiş verileri al
            historical_data = self.db.get_fund_price_history(fcode, 252)
            if historical_data.empty:
                return {'error': f'{fcode} için veri bulunamadı'}
            
            prices = historical_data.set_index('pdate')['price'].sort_index()
            returns = prices.pct_change().dropna()
            
            # İstatistiksel özellikler
            current_price = prices.iloc[-1]
            mean_return = returns.mean()
            volatility = returns.std()
            
            # Trend analizi
            recent_trend = (prices.iloc[-5:].iloc[-1] / prices.iloc[-5:].iloc[0]) - 1
            
            # Basit tahmin modelleri
            predictions = {
                'current_price': current_price,
                'random_walk_estimate': current_price * (1 + mean_return) ** days_ahead,
                'trend_based_estimate': current_price * (1 + recent_trend / 5) ** days_ahead,
                'conservative_estimate': current_price * (1 + mean_return * 0.5) ** days_ahead
            }
            
            # Monte Carlo simülasyonu
            n_simulations = 1000
            mc_returns = np.random.normal(mean_return, volatility, (n_simulations, days_ahead))
            mc_prices = current_price * np.cumprod(1 + mc_returns, axis=1)
            final_prices = mc_prices[:, -1]
            
            monte_carlo_analysis = {
                'expected_price': np.mean(final_prices),
                'price_std': np.std(final_prices),
                'confidence_intervals': {
                    '68%': [np.percentile(final_prices, 16), np.percentile(final_prices, 84)],
                    '95%': [np.percentile(final_prices, 2.5), np.percentile(final_prices, 97.5)]
                },
                'probability_gain': np.mean(final_prices > current_price),
                'probability_loss_10': np.mean((final_prices / current_price - 1) < -0.10)
            }
            
            result = {
                'fcode': fcode,
                'prediction_horizon_days': days_ahead,
                'current_price': current_price,
                'statistical_predictions': predictions,
                'monte_carlo_analysis': monte_carlo_analysis,
                'historical_metrics': {
                    'mean_daily_return': mean_return,
                    'daily_volatility': volatility,
                    'recent_trend': recent_trend
                },
                'prediction_date': datetime.now()
            }
            
            # AI tabanlı tahmin
            if use_ai and (self.openai_available or self.ollama_available):
                prediction_prompt = f"""
                {fcode} fonu tahmin analizi:
                
                Mevcut Fiyat: {current_price:.4f} TL
                Ortalama günlük getiri: %{mean_return * 100:.3f}
                Volatilite: %{volatility * 100:.2f}
                Son trend: %{recent_trend * 100:.2f}
                Monte Carlo beklenen fiyat: {monte_carlo_analysis['expected_price']:.4f} TL
                Kazanç olasılığı: %{monte_carlo_analysis['probability_gain'] * 100:.1f}
                
                {days_ahead} gün için fiyat yönü ve risk değerlendirmesi yap.
                """
                
                ai_predictions = {}
                
                if self.openai_available:
                    try:
                        ai_predictions['openai'] = self.query_openai(
                            prediction_prompt,
                            "Sen finansal tahmin uzmanısın."
                        )
                    except Exception as e:
                        ai_predictions['openai'] = f"OpenAI tahmin analizi başarısız: {e}"
                
                if self.ollama_available:
                    try:
                        ai_predictions['ollama'] = self.query_ollama(
                            prediction_prompt,
                            "Sen finansal tahmin uzmanısın."
                        )
                    except Exception as e:
                        ai_predictions['ollama'] = f"Ollama tahmin analizi başarısız: {e}"
                
                result['ai_predictions'] = ai_predictions
            
            return result
            
        except Exception as e:
            self.logger.error(f"Prediction error for {fcode}: {e}")
            return {'error': str(e)}
    
    def get_ai_status(self) -> Dict:
        """AI sistemlerinin durumunu döndür"""
        return {
            'openai': {
                'available': self.openai_available,
                'status': 'Ready' if self.openai_available else 'Not configured'
            },
            'ollama': {
                'available': self.ollama_available,
                'status': 'Ready' if self.ollama_available else 'Not connected',
                'base_url': self.ollama_base_url,
                'model': self.ollama_model
            }
        }