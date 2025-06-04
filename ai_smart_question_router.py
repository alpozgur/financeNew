# ai_smart_question_router.py
"""
AI-Powered Smart Question Router
NLP destekli akıllı soru yönlendirme sistemi
"""

import json
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

@dataclass
class AIRouteMatch:
    """AI destekli route eşleşme sonucu"""
    handler: str
    method: str
    score: float
    context: Dict[str, any]
    reasoning: str  # AI'nın neden bu handler'ı seçtiğini açıklama
    confidence: float  # AI'nın güven skoru

class AISmartQuestionRouter:
    """NLP destekli akıllı soru yönlendirici"""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        self.logger = logging.getLogger(__name__)
        
        # Modül tanımlamaları - AI'ya context sağlamak için
        self.module_descriptions = {
            'performance_analyzer': {
                'description': 'Fon performansı, getiri, kayıp, risk analizleri',
                'keywords': ['getiri', 'kazanç', 'performans', 'en iyi', 'en kötü', 'güvenli', 'riskli'],
                'methods': {
                    'handle_top_gainers': 'En çok kazandıran fonları bulur',
                    'handle_safest_funds_sql_fast': 'En güvenli fonları listeler',
                    'handle_worst_funds_list': 'En çok kaybettiren fonları bulur',
                    'handle_2025_recommendation_dual': '2025 yılı için fon önerileri',
                    'handle_analysis_question_dual': 'Tek fon detaylı analizi'
                }
            },
            'technical_analyzer': {
                'description': 'Teknik analiz, MACD, RSI, Bollinger, hareketli ortalamalar',
                'keywords': ['macd', 'rsi', 'bollinger', 'teknik', 'sinyal', 'alım', 'satım'],
                'methods': {
                    'handle_macd_signals_sql': 'MACD sinyallerini analiz eder',
                    'handle_rsi_signals_sql': 'RSI aşırı alım/satım sinyalleri',
                    'handle_bollinger_signals_sql': 'Bollinger band sinyalleri'
                }
            },
            'currency_inflation_analyzer': {
                'description': 'Döviz, enflasyon, dolar, euro fonları analizi',
                'keywords': ['dolar', 'euro', 'döviz', 'enflasyon', 'kur', 'usd', 'eur'],
                'methods': {
                    'analyze_currency_funds': 'Döviz fonlarını analiz eder',
                    'analyze_inflation_funds_mv': 'Enflasyon korumalı fonları bulur'
                }
            },
            'scenario_analyzer': {
                'description': 'What-if senaryoları, kriz, enflasyon durumları',
                'keywords': ['eğer', 'olursa', 'senaryo', 'kriz', 'durumunda'],
                'methods': {
                    'analyze_inflation_scenario': 'Enflasyon senaryosu analizi',
                    'analyze_stock_crash_scenario': 'Borsa çöküşü senaryosu'
                }
            },
            'personal_finance_analyzer': {
                'description': 'Emeklilik, eğitim, ev alma, kişisel finans planlaması',
                'keywords': ['emeklilik', 'eğitim', 'ev', 'birikim', 'çocuk'],
                'methods': {
                    'handle_retirement_planning': 'Emeklilik planlaması',
                    'handle_education_planning': 'Eğitim birikimleri'
                }
            },
            'mathematical_calculator': {
                'description': 'Matematiksel hesaplamalar, compound faiz, portföy dağılımı',
                'keywords': ['hesapla', 'ne kadar', 'birikim', 'faiz', 'yıllık'],
                'methods': {
                    'handle_monthly_investment_calculation': 'Aylık yatırım hesaplaması',
                    'handle_portfolio_distribution': 'Portföy dağıtımı'
                }
            },
            'portfolio_company_analyzer': {
                'description': 'Portföy yönetim şirketleri analizi',
                'keywords': ['portföy', 'iş portföy', 'ak portföy', 'garanti portföy'],
                'methods': {
                    'analyze_company_comprehensive': 'Şirket detaylı analizi',
                    'compare_companies_unlimited': 'Şirket karşılaştırması'
                }
            },
            'time_based_analyzer': {
                'description': 'Zaman bazlı analizler, haftalık, aylık trendler',
                'keywords': ['bugün', 'bu hafta', 'bu ay', 'yıl başından', 'ytd'],
                'methods': {
                    'analyze_today_performance': 'Bugünkü performans',
                    'analyze_weekly_trends': 'Haftalık trend analizi'
                }
            },
            'macroeconomic_analyzer': {
                'description': 'Makroekonomik etkiler, faiz, TCMB, jeopolitik',
                'keywords': ['faiz', 'tcmb', 'fed', 'enflasyon', 'makro'],
                'methods': {
                    'analyze_interest_rate_impact': 'Faiz etkisi analizi',
                    'analyze_tcmb_decisions': 'TCMB karar etkileri'
                }
            },
            'advanced_metrics_analyzer': {
                'description': 'Beta, Alpha, Sharpe, Information Ratio gibi ileri metrikler',
                'keywords': ['beta', 'alpha', 'sharpe', 'information ratio', 'tracking error'],
                'methods': {
                    'handle_beta_analysis': 'Beta katsayısı analizi',
                    'handle_alpha_analysis': 'Alpha değeri analizi'
                }
            },
            'thematic_analyzer': {
                'description': 'Sektörel ve tematik fon analizleri',
                'keywords': ['teknoloji', 'sağlık', 'enerji', 'sektör', 'tema'],
                'methods': {
                    'analyze_thematic_question': 'Tematik fon analizi'
                }
            }
        }
        
        # Fallback için legacy router (opsiyonel)
        self.legacy_patterns = self._load_legacy_patterns()
        
    def route_question(self, question: str) -> AIRouteMatch:
        """Tek bir en uygun handler döndürür"""
        routes = self.route_question_multi(question)
        return routes[0] if routes else None
    
    def route_question_multi(self, question: str, max_handlers: int = 3) -> List[AIRouteMatch]:
        """AI destekli çoklu handler yönlendirmesi"""
        
        # Önce AI'dan routing önerisi al
        ai_routes = self._get_ai_routing(question)
        
        if ai_routes:
            # AI önerilerini AIRouteMatch formatına çevir
            return self._convert_ai_routes_to_matches(ai_routes, question)
        else:
            # Fallback: Legacy pattern matching
            self.logger.warning("AI routing başarısız, legacy routing kullanılıyor")
            return self._legacy_route(question)
    
    def _get_ai_routing(self, question: str) -> Optional[Dict]:
        """AI'dan routing önerisi al"""
        
        # Modül bilgilerini formatla
        modules_info = json.dumps(self.module_descriptions, indent=2, ensure_ascii=False)
        
        prompt = f"""
        Kullanıcı sorusu: "{question}"
        
        Mevcut modüller ve yetenekleri:
        {modules_info}
        
        Bu soruyu en iyi cevaplayabilecek modül(leri) ve metod(ları) belirle.
        Multi-handler mümkün - birden fazla modül gerekebilir.
        
        Önemli kurallar:
        1. Sadece yukarıdaki modüllerden ve metodlardan seç
        2. En spesifik ve uygun olanı tercih et
        3. Confidence score 0-1 arası olmalı
        4. Context'e sayısal değerleri ekle (varsa)
        
        JSON formatında döndür:
        {{
            "routes": [
                {{
                    "handler": "module_name",
                    "method": "method_name",
                    "confidence": 0.95,
                    "reasoning": "Neden bu modül/metod seçildi",
                    "context": {{
                        "requested_count": 5,  // eğer sayı varsa
                        "days": 30,  // eğer zaman aralığı varsa
                        "currency": "usd"  // eğer döviz varsa
                    }}
                }}
            ],
            "requires_multi_handler": false,
            "explanation": "Genel açıklama"
        }}
        """
        
        try:
            response = self.ai_provider.query(
                prompt,
                "Sen bir NLP routing uzmanısın. Soruları analiz edip doğru modüllere yönlendiriyorsun."
            )
            
            # JSON parse et
            return self._parse_ai_response(response)
            
        except Exception as e:
            self.logger.error(f"AI routing hatası: {e}")
            return None
    
    def _parse_ai_response(self, response: str) -> Optional[Dict]:
        """AI yanıtını parse et"""
        try:
            # JSON bloğunu bul
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Basit text parsing
                return self._parse_text_response(response)
        except Exception as e:
            self.logger.error(f"AI response parsing hatası: {e}")
            return None
    
    def _convert_ai_routes_to_matches(self, ai_routes: Dict, question: str) -> List[AIRouteMatch]:
        """AI route önerilerini AIRouteMatch objesine çevir"""
        matches = []
        
        for route in ai_routes.get('routes', []):
            # Context'i zenginleştir
            context = route.get('context', {})
            
            # Sayıları otomatik detect et (AI yapmamışsa)
            if 'requested_count' not in context:
                numbers = re.findall(r'(\d+)', question)
                if numbers:
                    context['requested_count'] = int(numbers[0])
            
            match = AIRouteMatch(
                handler=route['handler'],
                method=route['method'],
                score=route['confidence'],
                context=context,
                reasoning=route.get('reasoning', ''),
                confidence=route['confidence']
            )
            matches.append(match)
        
        # Confidence'a göre sırala
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        return matches
    
    def _legacy_route(self, question: str) -> List[AIRouteMatch]:
        """Fallback: Eski pattern matching sistemi"""
        # Basit keyword matching
        question_lower = question.lower()
        matches = []
        
        for module, info in self.module_descriptions.items():
            keywords = info.get('keywords', [])
            
            # Keyword match score
            match_score = sum(1 for kw in keywords if kw in question_lower) / len(keywords) if keywords else 0
            
            if match_score > 0:
                # En uygun metodu tahmin et
                method = self._guess_method(question_lower, info.get('methods', {}))
                
                if method:
                    matches.append(AIRouteMatch(
                        handler=module,
                        method=method,
                        score=match_score,
                        context={},
                        reasoning="Legacy keyword matching",
                        confidence=match_score
                    ))
        
        return sorted(matches, key=lambda x: x.score, reverse=True)[:3]
    
    def _guess_method(self, question_lower: str, methods: Dict[str, str]) -> Optional[str]:
        """Metodları keyword'lere göre tahmin et"""
        # Basit heuristic
        for method_name, description in methods.items():
            desc_lower = description.lower()
            
            # Method ismi veya açıklamasında geçen kelimeler
            if any(word in question_lower for word in desc_lower.split()):
                return method_name
        
        # Default: ilk metod
        return list(methods.keys())[0] if methods else None
    
    def _load_legacy_patterns(self) -> Dict:
        """Legacy pattern'leri yükle (opsiyonel)"""
        # Mevcut smart_question_router.py'den pattern'leri import edebilirsiniz
        return {}
    
    def _parse_text_response(self, response: str) -> Optional[Dict]:
        """Basit text parsing fallback"""
        # AI bazen düz metin olarak yanıt verebilir
        # Basit regex ile module ve method isimlerini bul
        
        routes = []
        
        # Module isimlerini ara
        for module in self.module_descriptions.keys():
            if module in response.lower():
                # Method ara
                methods = self.module_descriptions[module].get('methods', {})
                for method in methods.keys():
                    if method in response.lower():
                        routes.append({
                            'handler': module,
                            'method': method,
                            'confidence': 0.7,
                            'reasoning': 'Text parsing',
                            'context': {}
                        })
                        break
        
        return {'routes': routes} if routes else None