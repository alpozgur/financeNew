# ai_smart_question_router.py - GÜNCELLENECEK
"""
AI-Powered Smart Question Router - PRODUCTION VERSION
AI + Pattern Matching + Multi-Handler Support
"""

import json
import re
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import logging

@dataclass
class AIRouteMatch:
    """AI destekli route eşleşme sonucu"""
    handler: str
    method: str
    score: float
    context: Dict[str, Any]
    reasoning: str
    confidence: float
    is_multi_handler: bool = False
    execution_order: int = 50

class AISmartQuestionRouter:
    """Production-ready AI + Pattern hybrid router"""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        self.logger = logging.getLogger(__name__)
        
        # Fallback pattern'ler - AI başarısız olursa kullanılacak
        self.fallback_patterns = self._load_fallback_patterns()
        
        # Handler bilgileri - AI'ya context sağlamak için
        self.handler_descriptions = self._load_handler_descriptions()
        # YENİ: Method mapping patterns - AI'ya hangi pattern'de hangi method'u kullanacağını öğret
        self.method_mapping_patterns = {
            'performance_analyzer': {
                # Güvenli/Riskli fon listeleri
                r'en\s*(güvenli|az\s*riskli)\s*\d*\s*fon': 'handle_safest_funds_sql_fast',
                r'güvenli\s*fonlar': 'handle_safest_funds_sql_fast',
                r'en\s*riskli\s*\d*\s*fon': 'handle_riskiest_funds_list',
                r'riskli\s*fonlar': 'handle_riskiest_funds_list',
                
                # Kazandıran/Kaybettiren fonlar
                r'en\s*(çok\s*)?kazandıran\s*\d*\s*fon': 'handle_top_gainers',
                r'en\s*(iyi|yüksek)\s*performans': 'handle_top_gainers',
                r'en\s*(çok\s*)?kaybettiren\s*\d*\s*fon': 'handle_worst_funds_list',
                r'en\s*kötü\s*performans': 'handle_worst_funds_list',
                
                # Tek fon analizi - ÖNEMLİ
                r'^[A-Z]{3}$': 'handle_analysis_question_dual',  # Sadece fon kodu
                r'\b[A-Z]{3}\b.*?(analiz|incele|değerlendir|nasıl)': 'handle_analysis_question_dual',
                r'(analiz\s*et|incele|değerlendir).*?\b[A-Z]{3}\b': 'handle_analysis_question_dual',
                r'\b[A-Z]{3}\b\s+fonu': 'handle_analysis_question_dual',
                
                # Öneriler
                r'2025.*?(öneri|tavsiye)': 'handle_2025_recommendation_dual',
                r'öneri.*?2025': 'handle_2025_recommendation_dual',
                
                # Karşılaştırma
                r'\b[A-Z]{3}\b.*?vs.*?\b[A-Z]{3}\b': 'handle_comparison_question',
                r'karşılaştır': 'handle_comparison_question',
                
                # Sharpe/Volatilite
                r'sharpe\s*oranı.*?yüksek': 'handle_top_sharpe_funds_question',
                r'volatilite.*?düşük': 'handle_low_volatility_funds_question'
            },
            
            'technical_analyzer': {
                # MACD
                r'macd.*?(pozitif|negatif|sinyal)': 'handle_macd_signals_sql',
                r'macd\s*sinyali': 'handle_macd_signals_sql',
                
                # RSI
                r'rsi.*?(\d+).*?(altında|üstünde)': 'handle_rsi_signals_sql',
                r'aşırı\s*(satım|alım)': 'handle_rsi_signals_sql',
                
                # Bollinger
                r'bollinger.*?(alt|üst)\s*band': 'handle_bollinger_signals_sql',
                
                # AI Pattern - ÖNEMLİ
                r'ai\s*pattern.*?ile.*?[A-Z]{3}': 'handle_ai_pattern_analysis',
                r'[A-Z]{3}.*?ai\s*pattern': 'handle_ai_pattern_analysis',
                r'ai\s*teknik': 'handle_ai_pattern_analysis',
                r'pattern\s*analiz': 'handle_ai_pattern_analysis',
                
                # Genel teknik
                r'teknik\s*sinyal': 'handle_general_technical_signals_sql'
            },
            
            'currency_inflation_analyzer': {
                # Enflasyon
                r'enflasyon.*?korumalı': 'analyze_inflation_funds_mv',
                r'enflasyon.*?\d+.*?olursa': 'analyze_inflation_scenario',
                
                # Döviz
                r'dolar.*?fonları': 'analyze_currency_funds',
                r'euro.*?fonları': 'analyze_currency_funds'
            },
            
            'scenario_analyzer': {
                # Senaryolar
                r'enflasyon.*?\d+.*?olursa': 'analyze_inflation_scenario',
                r'enflasyon.*?güvenli': 'analyze_inflation_scenario',
                r'borsa.*?(düş|çök)': 'analyze_stock_crash_scenario',
                r'eğer.*?olursa': 'analyze_scenario_question'
            },
            
            'personal_finance_analyzer': {
                # Emeklilik
                r'emeklilik.*?plan': 'handle_retirement_planning',
                r'emekliliğe.*?\d+.*?yıl': 'handle_retirement_planning',
                r'\d+\s*yaşında.*?emeklilik': 'handle_ai_personalized_planning'
            },
            
            'mathematical_calculator': {
                # Portföy dağıtımı
                r'\d+.*?tl.*?dağıt': 'handle_portfolio_distribution',
                r'portföy.*?dağılım': 'handle_portfolio_distribution',
                r'\d+.*?fona\s*böl': 'handle_portfolio_distribution'
            },
            
            'portfolio_company_analyzer': {
                # Şirket analizi
                r'(iş|ak|garanti|qnb)\s*portföy': 'analyze_company_comprehensive',
                r'portföy\s*şirket.*?analiz': 'analyze_company_comprehensive'
            },
            
            'advanced_metrics_analyzer': {
                # Beta - öncelik sırası önemli!
                r'beta.*?\d.*?(düşük|altında).*?sharpe': 'handle_combined_metrics_analysis',
                r'sharpe.*?\d.*?(yüksek|üstünde).*?beta': 'handle_combined_metrics_analysis',
                r'beta.*?katsayısı.*?\d': 'handle_beta_analysis',
                r'beta.*?(düşük|altında)': 'handle_beta_analysis',
                
                # Sharpe
                r'sharpe.*?oranı.*?\d': 'handle_sharpe_ratio_analysis',
                r'sharpe.*?(yüksek|üstünde)': 'handle_sharpe_ratio_analysis',
                
                # Kombine Beta + Sharpe
                r'beta.*?sharpe': 'handle_combined_metrics_analysis',  # YENİ
                r'sharpe.*?beta': 'handle_combined_metrics_analysis'   # YENİ
            }
        }

        # Multi-handler kuralları
        self.multi_handler_rules = self._load_multi_handler_rules()
        
        # Cache for AI responses
        self.route_cache = {}
        
    def route_question(self, question: str) -> Optional[AIRouteMatch]:
        """Tek handler döndür"""
        routes = self.route_question_multi(question, max_handlers=1)
        return routes[0] if routes else None
    
    def route_question_multi(self, question: str, max_handlers: int = 5) -> List[AIRouteMatch]:
        """AI destekli çoklu handler routing"""
        
        # 1. Cache kontrolü
        cache_key = question.lower().strip()
        if cache_key in self.route_cache:
            self.logger.info(f"Cache hit for: {question[:50]}...")
            return self.route_cache[cache_key]
        
        # 2. AI routing denemesi
        ai_routes = self._get_ai_routing(question)
        
        if ai_routes:
            # AI başarılı - sonuçları işle
            routes = self._process_ai_routes(ai_routes, question)
            
            # Cache'e kaydet
            if routes:
                self.route_cache[cache_key] = routes[:max_handlers]
                
            return routes[:max_handlers]
        
        # 3. Fallback: Pattern matching
        self.logger.warning("AI routing failed, using pattern matching")
        return self._pattern_based_routing(question, max_handlers)
    
    def _get_ai_routing(self, question: str) -> Optional[Dict]:
        """AI'dan routing önerisi al"""
        
        # ÖNCE: Pattern matching ile kesin eşleşmeleri kontrol et
        pattern_matches = self._check_pattern_matches(question)
        if pattern_matches:
            self.logger.info(f"Pattern match found for: {question}")
            return {"routes": pattern_matches, "pattern_matched": True}
        
        # Handler bilgilerini JSON formatında hazırla
        handlers_info = json.dumps(self.handler_descriptions, indent=2, ensure_ascii=False)
        
        # Method mapping örnekleri
        mapping_examples = self._prepare_mapping_examples()
        
        prompt = f"""
        Kullanıcı sorusu: "{question}"

        Mevcut handler'lar ve yetenekleri:
        {handlers_info}
        
        Method mapping örnekleri:
        {mapping_examples}

        GÖREV:
        1. Soruyu analiz et ve en uygun handler(ları) belirle
        2. Her handler için spesifik method ve context bilgisi ver
        3. Multi-handler gerekiyorsa hepsini listele
        4. Güven skorunu belirt (0-1 arası)

        ÖZEL KURALLAR:
        - 3 harfli FON KODLARI (AKB, TYH vb) tespit et, "FON_KODU" placeholder kullanma
        - "En güvenli X fon" → handle_safest_funds_sql_fast
        - "[FON_KODU] analiz et" → handle_analysis_question_dual
        - "Enflasyon X olursa" → scenario_analyzer.analyze_inflation_scenario (ÖNEMLİ!)
        - "olursa" kelimesi geçen sorular genelde scenario_analyzer kullanır
        - Yukarıdaki method mapping örneklerine kesinlikle uy
        - "piyasa durumu" soruları için performance_analyzer.handle_top_gainers kullan
        - "kapsamlı" kelimesi varsa multi-handler olarak işaretle
        FORMAT:
        {{
            "routes": [
                {{
                    "handler": "performance_analyzer",
                    "method": "handle_safest_funds_sql_fast",
                    "confidence": 0.95,
                    "reasoning": "En güvenli 10 fon listesi isteniyor",
                    "context": {{"requested_count": 10}}
                }}
            ]
        }}
        """
        
        try:
            response = self.ai_provider.query(
                prompt,
                "Sen akıllı bir soru yönlendirme uzmanısın."
            )
            
            return self._parse_ai_response(response)
            
        except Exception as e:
            self.logger.error(f"AI routing error: {e}")
            return None    
    def _parse_ai_response(self, response: str) -> Optional[Dict]:
        """AI yanıtını parse et"""
        try:
            # JSON bloğunu bul
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                parsed = json.loads(json_match.group())
                
                # Validation
                if 'routes' in parsed and isinstance(parsed['routes'], list):
                    for route in parsed['routes']:
                        # Eksik alanları doldur
                        route.setdefault('context', {})
                        route.setdefault('confidence', 0.8)
                        route.setdefault('reasoning', 'AI recommendation')
                
                return parsed
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parse error: {e}")
        except Exception as e:
            self.logger.error(f"Parse error: {e}")
        
        return None
    
    def _process_ai_routes(self, ai_routes: Dict, question: str) -> List[AIRouteMatch]:
        """AI route'larını işle ve AIRouteMatch objesine dönüştür"""
        routes = []
        question_lower = question.lower()
        
        # Manuel context extraction - AI'nın kaçırdıklarını yakala
        manual_context = self._extract_context_from_question(question)
        
        # Multi-handler kontrolü
        is_multi = ai_routes.get('requires_multi_handler', False)
        if not is_multi:
            # Multi-handler trigger'ları kontrol et
            is_multi = self._check_multi_handler_triggers(question_lower)
        
        for route_data in ai_routes.get('routes', []):
            handler = route_data['handler']
            method = route_data['method']
            
            # Handler validation
            if handler not in self.handler_descriptions:
                self.logger.warning(f"Unknown handler: {handler}")
                continue
            
            # Method validation
            valid_methods = self.handler_descriptions[handler].get('methods', {})
            if method not in valid_methods:
                # En yakın method'u bul
                method = self._find_closest_method(method, valid_methods)
            
            # Context merge
            ai_context = route_data.get('context', {})
            final_context = {**manual_context, **ai_context}  # AI öncelikli
            
            # Execution order
            exec_order = self.handler_descriptions[handler].get('execution_order', 50)
            
            route = AIRouteMatch(
                handler=handler,
                method=method,
                score=route_data['confidence'],
                context=final_context,
                reasoning=route_data.get('reasoning', ''),
                confidence=route_data['confidence'],
                is_multi_handler=is_multi,
                execution_order=exec_order
            )
            
            routes.append(route)
        
        # Execution order'a göre sırala
        routes.sort(key=lambda x: (x.execution_order, -x.confidence))
        
        return routes
    
    def _pattern_based_routing(self, question: str, max_handlers: int) -> List[AIRouteMatch]:
        """Fallback: Pattern matching ile routing"""
        routes = []
        question_lower = question.lower()
        
        for pattern_group in self.fallback_patterns:
            for pattern in pattern_group['patterns']:
                if re.search(pattern, question_lower):
                    context = self._extract_context_from_question(question)
                    
                    route = AIRouteMatch(
                        handler=pattern_group['handler'],
                        method=pattern_group['method'],
                        score=pattern_group.get('priority', 0.5),
                        context=context,
                        reasoning=f"Pattern match: {pattern}",
                        confidence=0.6,  # Pattern matching daha düşük güven
                        is_multi_handler=self._check_multi_handler_triggers(question_lower)
                    )
                    
                    routes.append(route)
                    break  # Her grup için tek match
        
        # Skora göre sırala
        routes.sort(key=lambda x: x.score, reverse=True)
        
        return routes[:max_handlers]
    
    def _extract_context_from_question(self, question: str) -> Dict[str, Any]:
        """Sorudan context bilgilerini çıkar"""
        context = {}
        question_lower = question.lower()
        words = question.upper().split()
        
        # Fund code detection - SADECE gerçek fon kodları
        fund_code = None
        fund_code_matches = re.findall(r'\b[A-Z]{3}\b', question.upper())
        
        if fund_code_matches:
            # Genişletilmiş yaygın kelimeler listesi
            common_words = [
                # Türkçe yaygın kelimeler
                'BIR', 'IKI', 'UÇ', 'DÖR', 'BEŞ', 'ALT', 'YED', 'SEK', 'DOK', 'ON',
                'YIL', 'GUN', 'AY', 'VE', 'ILE', 'AMA', 'YOK', 'VAR', 'HER', 'BU', 
                'ŞU', 'O', 'NE', 'KIM', 'GEL', 'GIT', 'YAP', 'ET', 'AL', 'VER',
                'SAT', 'KOY', 'CEK', 'BAK', 'DUR', 'KAL', 'OL', 'BIL', 'IST',
                'DEN', 'TEN', 'DAN', 'TAN', 'BIN', 'YÜZ', 'MIL',
                # İngilizce yaygın kelimeler  
                'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'WHO',
                'CAN', 'HAS', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'NOW',
                'NEW', 'WAY', 'MAY', 'SAY', 'GET', 'HAS', 'HIM', 'HOW', 'ITS',
                'TWO', 'BOY', 'DID', 'CAR', 'LET', 'SUN', 'BIG', 'BED', 'BOX',
                # Para birimleri
                'TRY', 'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD',
                # Sayılar
                'BIN', 'YUZ', 'ELL', 'KIR', 'SEK', 'DOK',
                # Zaman
                'GUN', 'YIL', 'AY', 'DUN', 'BUG', 'YAR',
                # Diğer
                'FON', 'PAR', 'HIS', 'TAH', 'END', 'BOR', 'DÖV', 'ALT', 'ÜST'
            ]
            
            # Sadece yaygın olmayan kelimeleri al
            for code in fund_code_matches:
                if code not in common_words:
                    # Ek kontrol: Cümle içindeki pozisyona bak
                    # "... için TYH fonunu ..." gibi durumlarda TYH fon kodu
                    pattern = rf'\b{code}\b\s*(fonu?|fonlar|yatırım|hisse)'
                    if re.search(pattern, question, re.IGNORECASE):
                        fund_code = code
                        break
                    # Veya cümle başında/sonunda tek başına
                    elif re.search(rf'^{code}\b|\b{code}$', question):
                        fund_code = code
                        break
        
        if fund_code:
            context['fund_code'] = fund_code
            # Sayılar - DÜZELTME
        numbers = re.findall(r'(\d+)', question)
        if numbers:
            # "X fon" pattern
            count_pattern = re.search(r'(\d+)\s*(fon|tane|adet)', question.lower())
            if count_pattern:
                context['requested_count'] = int(count_pattern.group(1))        
            else:
                # En büyük sayıyı al
                context['requested_count'] = max(int(n) for n in numbers)
        
        # # 2. Fon kodu
        # fund_codes = re.findall(r'\b[A-Z]{3}\b', question)
        # if fund_codes:
        #     context['fund_code'] = fund_codes[0]
        # 3. Zaman periyodu
        time_patterns = [
            (r'son\s*(\d+)\s*gün', lambda m: {'days': int(m.group(1))}),
            (r'son\s*(\d+)\s*ay', lambda m: {'days': int(m.group(1)) * 30}),
            (r'son\s*(\d+)\s*yıl', lambda m: {'days': int(m.group(1)) * 365}),
            (r'bugün', {'period': 'today', 'days': 1}),
            (r'bu\s*hafta', {'period': 'week', 'days': 7}),
            (r'bu\s*ay', {'period': 'month', 'days': 30})
        ]
        
        for pattern, value in time_patterns:
            match = re.search(pattern, question_lower)
            if match:
                if callable(value):
                    context.update(value(match))
                else:
                    context.update(value)
                break
        
        # 4. Para miktarı
        amount_patterns = [
            (r'(\d+)\s*(?:bin|k)\s*(?:tl|lira)?', 1000),
            (r'(\d+)\s*milyon\s*(?:tl|lira)?', 1000000),
            (r'(\d+)\s*(?:tl|lira)', 1)
        ]
        
        for pattern, multiplier in amount_patterns:
            match = re.search(pattern, question_lower)
            if match:
                context['amount'] = int(match.group(1)) * multiplier
                break
        
        # 5. Yüzde
        percent_match = re.search(r'%\s*(\d+)', question_lower)
        if percent_match:
            context['percentage'] = int(percent_match.group(1))
        
        # 6. Para birimi
        currencies = {
            'dolar': 'USD', 'usd': 'USD',
            'euro': 'EUR', 'eur': 'EUR',
            'sterlin': 'GBP'
        }
        
        for currency, code in currencies.items():
            if currency in question_lower:
                context['currency'] = code
                break
        
        # 7. Emeklilik
        if 'emeklilik' in question_lower:
            years_match = re.search(r'(\d+)\s*yıl', question_lower)
            if years_match:
                context['years_to_goal'] = int(years_match.group(1))
                context['goal_type'] = 'retirement'
        
        # 8. Risk toleransı
        if any(word in question_lower for word in ['güvenli', 'düşük risk', 'az risk']):
            context['risk_tolerance'] = 'low'
        elif any(word in question_lower for word in ['yüksek risk', 'agresif']):
            context['risk_tolerance'] = 'high'
        
        # 9. Metrik threshold'ları
        # Beta
        beta_match = re.search(r'beta.*?(\d+\.?\d*)', question_lower)
        if beta_match:
            context['beta_threshold'] = float(beta_match.group(1))
            if 'düşük' in question_lower or 'altında' in question_lower:
                context['comparison'] = 'less_than'
            elif 'yüksek' in question_lower or 'üstünde' in question_lower:
                context['comparison'] = 'greater_than'
        
        # Sharpe
        sharpe_match = re.search(r'sharpe.*?(\d+\.?\d*)', question_lower)
        if sharpe_match:
            context['sharpe_threshold'] = float(sharpe_match.group(1))
        
        # 10. Şirket adı
        companies = {
            'iş portföy': 'İş Portföy',
            'ak portföy': 'Ak Portföy',
            'garanti portföy': 'Garanti Portföy',
            'qnb portföy': 'QNB Portföy'
        }
        
        for pattern, name in companies.items():
            if pattern in question_lower:
                context['company_name'] = name
                break
        
        return context
    
    def _check_multi_handler_triggers(self, question_lower: str) -> bool:
        """Multi-handler gerekiyor mu kontrol et"""
        triggers = [
            'detaylı', 'kapsamlı', 'tüm yönleri', 'her açıdan',
            'karşılaştırmalı', 'derinlemesine', 'analiz raporu'
        ]
        
        return any(trigger in question_lower for trigger in triggers)
    
    def _find_closest_method(self, suggested: str, valid_methods: Dict) -> str:
        """En yakın valid method'u bul"""
        suggested_lower = suggested.lower()
        
        # Exact match
        if suggested in valid_methods:
            return suggested
        
        # Partial match
        for method in valid_methods:
            if suggested_lower in method.lower() or method.lower() in suggested_lower:
                return method
        
        # Default
        return list(valid_methods.keys())[0] if valid_methods else 'analyze'
    
    def _load_handler_descriptions(self) -> Dict:
        """Handler tanımlamalarını yükle - DÜZELTME"""
        return {
            'performance_analyzer': {
                'description': 'Fon performansı, getiri, kayıp, risk analizleri ve TEK FON ANALİZİ',
                'keywords': ['performans', 'getiri', 'kazanç', 'kayıp', 'analiz et', 'incele', 'değerlendir'],
                'methods': {
                    'handle_top_gainers': 'En çok kazandıran fonları bulur',
                    'handle_safest_funds_sql_fast': 'En güvenli fonları listeler',
                    'handle_worst_funds_list': 'En çok kaybettiren fonları bulur',
                    'handle_riskiest_funds_list': 'En riskli fonları bulur',
                    'handle_2025_recommendation_dual': '2025 yılı için fon önerileri',
                    'handle_analysis_question_dual': 'TEK FON DETAYLI ANALİZİ - ÖNEMLİ',
                    'handle_comparison_question': 'İki fon karşılaştırması'
                },
                'execution_order': 10
            },
            'technical_analyzer': {
                'description': 'Teknik analiz, MACD, RSI, Bollinger, AI pattern analizi',
                'keywords': ['macd', 'rsi', 'bollinger', 'teknik', 'ai pattern', 'pattern'],
                'methods': {
                    'handle_macd_signals_sql': 'MACD sinyallerini analiz eder',
                    'handle_rsi_signals_sql': 'RSI aşırı alım/satım sinyalleri',
                    'handle_bollinger_signals_sql': 'Bollinger band sinyalleri',
                    'handle_moving_average_signals_sql': 'Hareketli ortalama sinyalleri',
                    'handle_ai_pattern_analysis': 'AI PATTERN ANALİZİ - FON KODU İLE'
                },
                'execution_order': 20
            },
            'currency_inflation_analyzer': {
                'description': 'Döviz, enflasyon, dolar, euro fonları analizi',
                'keywords': ['dolar', 'euro', 'döviz', 'enflasyon', 'kur', 'usd', 'eur'],
                'methods': {
                    'analyze_currency_funds': 'Döviz fonlarını analiz eder',
                    'analyze_inflation_funds_mv': 'Enflasyon korumalı fonları bulur',
                    'analyze_currency_inflation_question': 'Genel döviz/enflasyon sorusu analizi'
                },
                'execution_order': 30
            },
            'scenario_analyzer': {
                'description': 'What-if senaryoları, kriz, enflasyon durumları',
                'keywords': ['eğer', 'olursa', 'senaryo', 'kriz', 'durumunda', 'enflasyon olursa'],
                'methods': {
                    'analyze_stock_crash_scenario': 'Borsa çöküşü senaryosu',
                    'analyze_scenario_question': 'Genel senaryo analizi'
                },
                'execution_order': 40
            },
            'personal_finance_analyzer': {
                'description': 'Emeklilik, eğitim, ev alma, kişisel finans planlaması',
                'methods': {
                    'handle_retirement_planning': 'Emeklilik planlaması',
                    'handle_ai_personalized_planning': 'Kişiselleştirilmiş plan',
                    'analyze_personal_finance_question': 'Genel kişisel finans'
                },
                'execution_order': 50
            },
            'mathematical_calculator': {
                'description': 'Matematiksel hesaplamalar, compound faiz, portföy dağılımı',
                'methods': {
                    'handle_monthly_investment_calculation': 'Aylık yatırım hesaplaması',
                    'handle_portfolio_distribution': 'Portföy dağıtımı',
                    'analyze_mathematical_question': 'Genel matematik hesaplama'
                },
                'execution_order': 60
            },
            'portfolio_company_analyzer': {
                'description': 'Portföy yönetim şirketleri analizi',
                'methods': {
                    'analyze_company_comprehensive': 'Şirket detaylı analizi',
                    'compare_companies_unlimited': 'Şirket karşılaştırması',
                    'find_best_portfolio_company_unlimited': 'En iyi şirket'
                },
                'execution_order': 70
            },
            'time_based_analyzer': {
                'description': 'Zaman bazlı analizler, haftalık, aylık trendler',
                'methods': {
                    'analyze_today_performance': 'Bugünkü performans',
                    'analyze_time_based_question': 'Genel zaman bazlı analiz'
                },
                'execution_order': 80
            },
            'macroeconomic_analyzer': {
                'description': 'Makroekonomik etkiler, faiz, TCMB, jeopolitik',
                'methods': {
                    'analyze_macroeconomic_impact': 'Makro etki analizi',
                    'analyze_interest_rate_impact': 'Faiz etkisi'
                },
                'execution_order': 90
            },
            'advanced_metrics_analyzer': {
                'description': 'Beta, Alpha, Sharpe, Information Ratio gibi ileri metrikler',
                'methods': {
                    'handle_beta_analysis': 'Beta katsayısı analizi',
                    'handle_alpha_analysis': 'Alpha değeri analizi',
                    'handle_sharpe_ratio_analysis': 'Sharpe oranı analizi'
                },
                'execution_order': 100
            },
            'thematic_analyzer': {
                'description': 'Sektörel ve tematik fon analizleri',
                'methods': {
                    'analyze_thematic_question': 'Tematik fon analizi'
                },
                'execution_order': 110
            },
            'fundamental_analyzer': {
                'description': 'Fon büyüklüğü, yatırımcı sayısı, temel analizler',
                'methods': {
                    'handle_largest_funds_questions': 'En büyük fonlar',
                    'handle_investor_count_questions': 'Yatırımcı sayısı analizi',
                    'handle_fund_category_questions': 'Kategori analizi'
                },
                'execution_order': 120
            }
        }
    
    def _load_multi_handler_rules(self) -> Dict:
        """Multi-handler kuralları"""
        return {
            'comprehensive_analysis': {
                'triggers': ['detaylı', 'kapsamlı', 'tüm yönleri'],
                'required_handlers': ['performance_analyzer', 'technical_analyzer'],
                'optional_handlers': ['fundamental_analyzer']
            },
            'investment_decision': {
                'triggers': ['yatırım kararı', 'hangisine yatırım', 'seçim'],
                'required_handlers': ['performance_analyzer', 'risk_analyzer'],
                'optional_handlers': ['scenario_analyzer']
            },
            'market_overview': {
                'triggers': ['piyasa durumu', 'genel durum'],
                'required_handlers': ['time_based_analyzer', 'performance_analyzer'],
                'optional_handlers': ['macroeconomic_analyzer']
            }
        }
    
    def _load_fallback_patterns(self) -> List[Dict]:
        """Fallback pattern'ler"""
        return [
            {
                'handler': 'performance_analyzer',
                'method': 'handle_top_gainers',
                'patterns': [
                    r'en\s*(?:çok\s*)?kazandıran',
                    r'en\s*(?:iyi|yüksek)\s*(?:performans|getiri)'
                ],
                'priority': 0.9
            },
            {
                'handler': 'performance_analyzer',
                'method': 'handle_safest_funds_sql_fast',
                'patterns': [
                    r'en\s*güvenli',
                    r'en\s*az\s*riskli'
                ],
                'priority': 0.9
            },
            {
                'handler': 'technical_analyzer',
                'method': 'handle_ai_pattern_analysis',
                'patterns': [
                    r'ai\s*pattern',
                    r'ai\s*teknik',
                    r'pattern\s*analiz'
                ],
                'priority': 1.0
            },
            {
                'handler': 'scenario_analyzer',
                'method': 'analyze_scenario_question',
                'patterns': [
                    r'olursa',
                    r'durumunda',
                    r'senaryosu'
                ],
                'priority': 0.8
            },
            {
                'handler': 'personal_finance_analyzer',
                'method': 'handle_retirement_planning',
                'patterns': [
                    r'emeklilik',
                    r'emekliliğe.*?yıl'
                ],
                'priority': 0.8
            }
        ]
    
    def clear_cache(self):
        """Cache'i temizle"""
        self.route_cache.clear()
        self.logger.info("Route cache cleared")
    
    def get_stats(self) -> Dict:
        """İstatistikleri döndür"""
        return {
            'cache_size': len(self.route_cache),
            'handlers_count': len(self.handler_descriptions),
            'fallback_patterns_count': sum(len(p['patterns']) for p in self.fallback_patterns),
            'multi_handler_rules_count': len(self.multi_handler_rules)
        }
    
    def _check_pattern_matches(self, question: str) -> List[Dict]:
        """Pattern matching ile kesin eşleşmeleri kontrol et - ÖNCELİK SIRALI"""
        question_lower = question.lower()
        matches = []
        
        # ÖNCELİK 1: Özel pattern'ler (en spesifik)
        special_patterns = {
            r'piyasa.*?durum.*?kapsamlı|kapsamlı.*?piyasa': {
                'handler': 'performance_analyzer',
                'method': 'handle_top_gainers',
                'priority': 100,
                'is_multi_handler': True  # Multi-handler tetikle
            },
            # Kişisel finans - DAHA SPESIFIK
            r'\d+\s*yaşında.*?emeklilik': {
                'handler': 'personal_finance_analyzer',
                'method': 'handle_retirement_planning',
                'priority': 100
            },
            r'emekliliğe.*?\d+\s*yıl': {
                'handler': 'personal_finance_analyzer',
                'method': 'handle_retirement_planning',
                'priority': 100
            },
            # Enflasyon senaryosu - YENİ EKLEME
            r'enflasyon.*?\d+.*?olursa': {
                'handler': 'scenario_analyzer',
                'method': 'analyze_scenario_question',
                'priority': 100
            },
            # Beta + Sharpe kombinasyonu
            r'beta.*?sharpe|sharpe.*?beta': {
                'handler': 'advanced_metrics_analyzer',
                'method': 'handle_combined_metrics_analysis',
                'priority': 100
            },
            # AI pattern
            r'ai\s*pattern.*?[A-Z]{3}|pattern\s*analiz.*?[A-Z]{3}': {
                'handler': 'technical_analyzer',
                'method': 'handle_ai_pattern_analysis',
                'priority': 100
            },
            # Kişisel finans
            r'\d+\s*yaş.*?emeklilik.*?\d+\s*yıl': {
                'handler': 'personal_finance_analyzer',
                'method': 'handle_retirement_planning',
                'priority': 100
            }
        }
        
        # Önce özel pattern'leri kontrol et
        for pattern, config in special_patterns.items():
            if re.search(pattern, question_lower, re.IGNORECASE):
                context = self._extract_context_from_question(question)
                matches.append({
                    "handler": config['handler'],
                    "method": config['method'],
                    "confidence": 0.98,
                    "reasoning": f"Special pattern match: {pattern}",
                    "context": context
                })
                return matches  # İlk eşleşmede dur
        
        # ÖNCELİK 2: Normal pattern'ler
        for handler, patterns in self.method_mapping_patterns.items():
            for pattern, method in patterns.items():
                if re.search(pattern, question_lower, re.IGNORECASE):
                    context = self._extract_context_from_question(question)
                    
                    matches.append({
                        "handler": handler,
                        "method": method,
                        "confidence": 0.95,
                        "reasoning": f"Pattern match: {pattern}",
                        "context": context
                    })
                    return matches  # İlk eşleşmede dur
        
        return []
    def _prepare_mapping_examples(self) -> str:
        """AI için method mapping örnekleri hazırla"""
        examples = []
        
        # Her handler'dan birkaç örnek
        example_mappings = {
            '"En güvenli 10 fon"': 'performance_analyzer.handle_safest_funds_sql_fast',
            '"AKB fonunu analiz et"': 'performance_analyzer.handle_analysis_question_dual',
            '"En çok kazandıran fonlar"': 'performance_analyzer.handle_top_gainers',
            '"MACD sinyali pozitif fonlar"': 'technical_analyzer.handle_macd_signals_sql',
            '"AI pattern analizi TYH"': 'technical_analyzer.handle_ai_pattern_analysis',
            '"Enflasyon %50 olursa"': 'scenario_analyzer.analyze_inflation_scenario',
            '"Beta katsayısı 1 altında"': 'advanced_metrics_analyzer.handle_beta_analysis',
            '"İş Portföy analizi"': 'portfolio_company_analyzer.analyze_company_comprehensive',
            '"100000 TL nasıl dağıtmalı"': 'mathematical_calculator.handle_portfolio_distribution',
            '"Emekliliğe 25 yıl var"': 'personal_finance_analyzer.handle_retirement_planning',
            '"BHL vs AJE"': 'performance_analyzer.handle_comparison_question',
            '"FPH ve GFL karşılaştır"': 'performance_analyzer.handle_comparison_question',
            '"USD bazlı fonlar"': 'currency_inflation_analyzer.analyze_currency_funds',
            '"dolar fonları"': 'currency_inflation_analyzer.analyze_currency_funds',
            '"alpha değeri pozitif fonlar"': 'advanced_metrics_analyzer.handle_alpha_analysis',
            '"tracking error düşük index fonlar"': 'advanced_metrics_analyzer.handle_tracking_error_analysis',
            '"information ratio yüksek aktif fonlar"': 'advanced_metrics_analyzer.handle_information_ratio_analysis',
            '"50 günlük hareketli ortalama üstünde fonlar"': 'technical_analyzer.handle_moving_average_signals_sql',
            '"beta 0.5 düşük fonlar"': 'advanced_metrics_analyzer.handle_beta_analysis',

        }
        
        for example, mapping in example_mappings.items():
            examples.append(f'{example} → {mapping}')
        
        return '\n'.join(examples)