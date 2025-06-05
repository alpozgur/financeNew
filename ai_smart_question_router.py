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
                'keywords': ['emeklilik', 'emekliliğe', 'retirement', 'birikim', 'yaş', 'kala', 'yıl kala'],
                'methods': {
                    'handle_retirement_planning': 'Emeklilik planlaması',
                    'handle_education_planning': 'Eğitim birikimleri',
                    'handle_house_planning': 'Ev alma planlaması'
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
            },
            'predictive_analyzer': {
                'description': 'Gelecek tahminleri, prediktif senaryo analizleri',
                'keywords': ['tahmin', 'sonra', 'gelecek', 'olacak', 'beklenti', 'öngörü', 'projeksiyon'],
                'methods': {
                    'analyze_predictive_scenario': 'Gelecek senaryolarını tahmin eder'
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

        KURALLAR:
        1. Birden fazla modül gerekiyorsa hepsini döndür
        2. requested_count sadece "kaç tane", "5 fon", "10 fon" gibi durumlar için
        3. Beta/threshold değerleri için "threshold" veya "value" kullan
        4. Multi-handler örnek: Dolar fonları hem currency_inflation_analyzer hem performance_analyzer kullanabilir

        Örnek multi-handler response:
        {{
            "routes": [
                {{
                    "handler": "currency_inflation_analyzer",
                    "method": "analyze_currency_funds",
                    "confidence": 0.90,
                    "reasoning": "Dolar fonlarını filtrelemek için"
                }},
                {{
                    "handler": "performance_analyzer",
                    "method": "handle_analysis_question_dual",
                    "confidence": 0.85,
                    "reasoning": "Performans analizi için"
                }}
            ],
            "requires_multi_handler": true
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
    
    def _extract_context(self, question: str) -> Dict:
        """Sorudan context bilgilerini çıkar"""
        context = {}
        
        # Sayılar
        numbers = re.findall(r'(\d+)', question)
        
        # "X fon", "X tane" pattern'i - SADECE bu durumda requested_count
        count_pattern = re.search(r'(\d+)\s*(fon|tane|adet)', question.lower())
        if count_pattern:
            context['requested_count'] = int(count_pattern.group(1))
        
        # Beta, alpha gibi threshold değerleri
        threshold_patterns = [
            (r'beta.*?(\d+\.?\d*)', 'beta_threshold'),
            (r'alpha.*?(\d+\.?\d*)', 'alpha_threshold'),
            (r'sharpe.*?(\d+\.?\d*)', 'sharpe_threshold'),
            (r'%\s*(\d+)', 'percentage'),  # %50 gibi
            (r'(\d+).*?den\s*(düşük|az|küçük)', 'max_threshold'),
            (r'(\d+).*?den\s*(yüksek|fazla|büyük)', 'min_threshold')
        ]
        
        for pattern, context_key in threshold_patterns:
            match = re.search(pattern, question.lower())
            if match:
                # Eğer "den düşük/yüksek" pattern'i ise
                if context_key in ['max_threshold', 'min_threshold']:
                    context[context_key] = float(match.group(1))
                else:
                    context[context_key] = float(match.group(1))
        
        # Para birimleri
        currency_patterns = {
            'dolar': 'usd',
            'usd': 'usd',
            'euro': 'eur',
            'eur': 'eur',
            'sterlin': 'gbp',
            'pound': 'gbp'
        }
        
        question_lower = question.lower()
        for currency_word, currency_code in currency_patterns.items():
            if currency_word in question_lower:
                context['currency'] = currency_code
                break
        
        # Zaman aralıkları
        time_patterns = [
            (r'bugün', {'period': 'today', 'days': 1}),
            (r'bu hafta', {'period': 'week', 'days': 7}),
            (r'bu ay', {'period': 'month', 'days': 30}),
            (r'bu yıl', {'period': 'year', 'days': 365}),
            (r'son\s*(\d+)\s*gün', lambda m: {'days': int(m.group(1))}),
            (r'son\s*(\d+)\s*ay', lambda m: {'days': int(m.group(1)) * 30}),
            (r'son\s*(\d+)\s*yıl', lambda m: {'days': int(m.group(1)) * 365})
        ]
        
        for pattern, value in time_patterns:
            match = re.search(pattern, question_lower)
            if match:
                if callable(value):
                    context.update(value(match))
                else:
                    context.update(value)
                break
        
        # YENİ: Sharpe için min_threshold da ekle
        if 'sharpe_threshold' in context and 'yüksek' in question_lower:
            context['min_threshold'] = context['sharpe_threshold']
        
        # Emeklilik pattern'i - DÜZELTME
        if 'emeklilik' in question_lower or 'emekliliğe' in question_lower:
            # "10 yıl kala", "10 yıl var", "10 yılım var" gibi pattern'ler
            years_patterns = [
                r'(\d+)\s*yıl.*?kala',
                r'(\d+)\s*yıl.*?var',
                r'(\d+)\s*yılım',
                r'(\d+)\s*sene',
                r'emekliliğe\s*(\d+)\s*yıl'  # Yeni pattern
            ]
            
            for pattern in years_patterns:
                match = re.search(pattern, question_lower)
                if match:
                    context['years_to_goal'] = int(match.group(1))
                    context['goal_type'] = 'retirement'  # Yeni context
                    break
        
        return context
    
    def _parse_ai_response(self, response: str) -> Optional[Dict]:
        """AI yanıtını parse et"""
        try:
            # JSON bloğunu bul
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                parsed = json.loads(json_match.group())
                
                # Context None kontrolü
                if 'routes' in parsed:
                    for route in parsed['routes']:
                        if 'context' not in route:
                            route['context'] = {}
                        elif route['context'] is None:
                            route['context'] = {}
                
                return parsed
            else:
                # Basit text parsing
                return self._parse_text_response(response)
        except Exception as e:
            self.logger.error(f"AI response parsing hatası: {e}")
            return None
    
    def _convert_ai_routes_to_matches_old(self, ai_routes: Dict, question: str) -> List[AIRouteMatch]:
        """AI route önerilerini AIRouteMatch objesine çevir - POST-PROCESSING EKLENDİ"""
        matches = []
        question_lower = question.lower()
        
        # Manuel context extraction
        extracted_context = self._extract_context(question)
        if extracted_context is None:
            extracted_context = {}
        
        for route in ai_routes.get('routes', []):
            handler = route['handler']
            method = route['method']
            
            # ÖZEL KURAL: "olursa" içeren enflasyon soruları
            if 'olursa' in question_lower and 'enflasyon' in question_lower:
                if handler == 'currency_inflation_analyzer':
                    # Scenario analyzer'a yönlendir
                    handler = 'scenario_analyzer'
                    method = 'analyze_inflation_scenario'
                    route['reasoning'] = "Enflasyon senaryosu tespit edildi"
            
            # Context birleştirme
            ai_context = route.get('context')
            if ai_context is None:
                ai_context = {}
            
            if not isinstance(ai_context, dict):
                ai_context = {}
            if not isinstance(extracted_context, dict):
                extracted_context = {}
            
            final_context = {**ai_context, **extracted_context}
            
            # Gereksiz requested_count temizleme
            if 'requested_count' in final_context:
                if not re.search(r'\d+\s*(fon|tane|adet)', question.lower()):
                    final_context.pop('requested_count', None)
            
            match = AIRouteMatch(
                handler=handler,
                method=method,
                score=route['confidence'],
                context=final_context,
                reasoning=route.get('reasoning', ''),
                confidence=route['confidence']
            )
            matches.append(match)
        
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches
    

    def _convert_ai_routes_to_matches(self, ai_routes: Dict, question: str) -> List[AIRouteMatch]:
        """AI route önerilerini AIRouteMatch objesine çevir - ÖNCE PATTERN MATCHING"""
        matches = []
        question_lower = question.lower()
        
        # Manuel context extraction
        extracted_context = self._extract_context(question)
        if extracted_context is None:
            extracted_context = {}
        
        # ÖNCELİKLİ PATTERN MATCHING - AI'dan önce kontrol
        priority_match = self._check_priority_patterns(question_lower, extracted_context)
        if priority_match:
            return [priority_match]
        
        # AI routes'u işle (normal flow)
        for route in ai_routes.get('routes', []):
            handler = route['handler']
            method = route['method']
            
            # Mevcut olursa kuralı
            if 'olursa' in question_lower and 'enflasyon' in question_lower:
                if handler == 'currency_inflation_analyzer':
                    handler = 'scenario_analyzer'
                    method = 'analyze_inflation_scenario'
                    route['reasoning'] = "Enflasyon senaryosu tespit edildi"
            
            # Context birleştirme
            ai_context = route.get('context')
            if ai_context is None:
                ai_context = {}
            
            if not isinstance(ai_context, dict):
                ai_context = {}
            
            final_context = {**ai_context, **extracted_context}
            
            # Gereksiz requested_count temizleme
            if 'requested_count' in final_context:
                if not re.search(r'\d+\s*(fon|tane|adet)', question.lower()):
                    final_context.pop('requested_count', None)
            
            match = AIRouteMatch(
                handler=handler,
                method=method,
                score=route['confidence'],
                context=final_context,
                reasoning=route.get('reasoning', ''),
                confidence=route['confidence']
            )
            matches.append(match)
        
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches

    def _check_priority_patterns(self, question_lower: str, context: Dict) -> Optional[AIRouteMatch]:
        """Öncelikli pattern kontrolü - AI'dan önce çalışır"""
        
    # EN BAŞA EKLE - YÜKSEK ÖNCELİK
    # 0. Prediktif tahmin patterns - EN YÜKSEK ÖNCELİK
        if any(word in question_lower for word in ['sonra', 'tahmin', 'gelecek', 'olacak', 'beklenti']):
            if any(word in question_lower for word in ['enflasyon', 'dolar', 'faiz', 'borsa', 'fon']):
                return AIRouteMatch(
                    handler='predictive_analyzer',
                    method='analyze_predictive_scenario',
                    score=1.0,
                    context=context,
                    reasoning="Predictive scenario pattern match",
                    confidence=1.0
                )
                    # 1. Beta/Alpha/Sharpe patterns
        if any(word in question_lower for word in ['beta katsayısı', 'beta değeri', 'beta 1']):
            return AIRouteMatch(
                handler='advanced_metrics_analyzer',
                method='handle_beta_analysis',
                score=1.0,
                context=context,
                reasoning="Beta pattern match",
                confidence=1.0
            )
        
        if 'sharpe oranı' in question_lower:
            return AIRouteMatch(
                handler='advanced_metrics_analyzer',
                method='handle_sharpe_ratio_analysis',
                score=1.0,
                context=context,
                reasoning="Sharpe pattern match",
                confidence=1.0
            )
        
        # 2. Technical indicators
        if any(word in question_lower for word in ['macd sinyali', 'macd pozitif']):
            return AIRouteMatch(
                handler='technical_analyzer',
                method='handle_macd_signals_sql',
                score=1.0,
                context=context,
                reasoning="MACD pattern match",
                confidence=1.0
            )
        
        if 'rsi' in question_lower and any(word in question_lower for word in ['altında', 'üstünde']):
            return AIRouteMatch(
                handler='technical_analyzer',
                method='handle_rsi_signals_sql',
                score=1.0,
                context=context,
                reasoning="RSI pattern match",
                confidence=1.0
            )
        
        # 3. Currency patterns
        if 'dolar' in question_lower or 'euro' in question_lower:
            if 'performans' in question_lower or 'getiri' in question_lower:
                return AIRouteMatch(
                    handler='currency_inflation_analyzer',
                    method='analyze_currency_funds',
                    score=1.0,
                    context=context,
                    reasoning="Currency performance pattern match",
                    confidence=1.0
                )

        # YENİ: AI Pattern Recognition öncelik kontrolü
        if any(word in question_lower for word in ['ai teknik', 'ai pattern', 'yapay zeka teknik', 
                                                    'ai sinyal', 'pattern analiz']):
            return AIRouteMatch(
                handler='technical_analyzer',
                method='handle_ai_pattern_analysis',
                score=1.0,
                context=context,
                reasoning="AI technical pattern match",
                confidence=1.0
            )


        # 4. Portfolio company patterns
        # 4. Portfolio company patterns - DÜZELTME
        company_patterns = [
            ('iş portföy', 'İş Portföy'),
            ('is portfoy', 'İş Portföy'),  # Türkçe karakter sorunu için
            ('ak portföy', 'Ak Portföy'),
            ('garanti portföy', 'Garanti Portföy'),
            ('qnb portföy', 'QNB Portföy')
        ]
        
        for pattern, company_name in company_patterns:
            if pattern in question_lower:
                return AIRouteMatch(
                    handler='portfolio_company_analyzer',
                    method='analyze_company_comprehensive',
                    score=1.0,
                    context={'company_name': company_name},
                    reasoning=f"{company_name} pattern match",
                    confidence=1.0
                )
        
        # 5. Time-based patterns
        if 'bugün' in question_lower and any(word in question_lower for word in ['kazanan', 'kaybeden', 'performans']):
            return AIRouteMatch(
                handler='time_based_analyzer',
                method='analyze_today_performance',
                score=1.0,
                context=context,
                reasoning="Today pattern match",
                confidence=1.0
            )
        
        # 6. Mathematical patterns - GENİŞLETİLMİŞ
        if any(word in question_lower for word in ['dağıt', 'böl', 'nasıl dağıtmalı', 'tl\'yi', 'tl yi']):
            if any(word in question_lower for word in ['fon', 'portföy']):
                return AIRouteMatch(
                    handler='mathematical_calculator',
                    method='handle_portfolio_distribution',
                    score=1.0,
                    context=context,
                    reasoning="Distribution pattern match",
                    confidence=1.0
                )
        
        # 7. Fundamental patterns
        if 'en büyük' in question_lower and 'fon' in question_lower:
            return AIRouteMatch(
                handler='fundamental_analyzer',
                method='handle_largest_funds_questions',
                score=1.0,
                context=context,
                reasoning="Largest funds pattern match",
                confidence=1.0
            )
        
        # No priority pattern found
        return None

    def _legacy_route(self, question: str) -> List[AIRouteMatch]:
        """Fallback: Eski pattern matching sistemi"""
        question_lower = question.lower()
        matches = []
        
        # Özel durumlar için öncelikli kontrol
        if 'emeklilik' in question_lower or 'emekliliğe' in question_lower:
            context = self._extract_context(question)
            matches.append(AIRouteMatch(
                handler='personal_finance_analyzer',
                method='handle_retirement_planning',
                score=0.9,
                context=context,
                reasoning="Emeklilik keyword match",
                confidence=0.9
            ))
        # YENİ: Sektör/tema kontrolü
        elif any(sector in question_lower for sector in ['teknoloji', 'sağlık', 'enerji', 'sektör']):
            matches.append(AIRouteMatch(
                handler='thematic_analyzer',
                method='analyze_thematic_question',
                score=0.9,
                context={},
                reasoning="Sektör/tema keyword match",
                confidence=0.9
            ))

        # YENİ: Faiz kontrolü
        elif 'faiz' in question_lower and any(word in question_lower for word in ['artış', 'etkile', 'nasıl']):
            matches.append(AIRouteMatch(
                handler='macroeconomic_analyzer',
                method='analyze_interest_rate_impact',
                score=0.9,
                context={},
                reasoning="Faiz etkisi keyword match",
                confidence=0.9
            ))
        
        # YENİ: Portföy dağıtımı kontrolü
        elif any(word in question_lower for word in ['dağıt', 'böl']) and 'fon' in question_lower:
            matches.append(AIRouteMatch(
                handler='mathematical_calculator',
                method='handle_portfolio_distribution',
                score=0.9,
                context=self._extract_context(question),
                reasoning="Portfolio distribution keyword match",
                confidence=0.9
            ))
        
        # Basit keyword matching (geri kalan kod aynı)
        else:
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