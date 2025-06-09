# smart_routing_orchestrator.py - YENİ DOSYA
"""
Akıllı Routing Orkestratörü
Question Analyzer'ı kullanarak doğru handler'ları belirler
RİSK ANALİZİ ENTEGRE EDİLMİŞ
"""

from typing import List, Dict, Optional, Tuple

import pandas as pd
from intelligent_question_analyzer import IntelligentQuestionAnalyzer, QuestionAnalysis
from risk_assessment import RiskAssessment

class SmartRoutingOrchestrator:
    """Akıllı routing orkestratörü - Risk analizi entegre"""
    
    def __init__(self, db_connection, ai_provider=None, enable_risk_check=True):
        self.analyzer = IntelligentQuestionAnalyzer(db_connection)
        self.ai_provider = ai_provider
        self.db = db_connection
        self.enable_risk_check = enable_risk_check  # Risk kontrolünü aç/kapa
        self._initialize_routing_rules()
    
    def _initialize_routing_rules(self):
        """Routing kurallarını tanımla"""
        
        # Intent -> Handler mapping
        self.intent_handlers = {
            'analyze': {
                'single_fund': [('performance_analyzer', 'handle_analysis_question_dual', 1.0)],
                'comparison': [('performance_analyzer', 'handle_comparison_question', 1.0)],
                'multi_fund': [('performance_analyzer', 'handle_top_gainers', 0.8)],
                'general': [('performance_analyzer', 'handle_general_question', 0.7)]
            },
            'compare': {
                'comparison': [('performance_analyzer', 'handle_comparison_question', 1.0)],
                'single_fund': [('performance_analyzer', 'handle_analysis_question_dual', 0.5)],
            },
            'list': {
                'general': [
                    ('performance_analyzer', 'handle_top_gainers', 0.8),
                    ('performance_analyzer', 'handle_safest_funds_sql_fast', 0.7)
                ],
                'multi_fund': [('performance_analyzer', 'handle_top_gainers', 0.9)]
            },
            'recommend': {
                'general': [('performance_analyzer', 'handle_2025_recommendation_dual', 0.9)],
                'single_fund': [('performance_analyzer', 'handle_analysis_question_dual', 0.7)]
            },
            'risk': {
                'general': [('performance_analyzer', 'handle_safest_funds_sql_fast', 0.9)],
                'single_fund': [('performance_analyzer', 'handle_analysis_question_dual', 0.8)]
            },
            'technical': {
                'single_fund': [('technical_analyzer', 'handle_ai_pattern_analysis', 0.9)],
                'general': [('technical_analyzer', 'handle_general_technical_signals_sql', 0.8)]
            },
            'scenario': {
                'general': [('scenario_analyzer', 'analyze_scenario_question', 1.0)]
            },
            'predict': {
                'single_fund': [('predictive_analyzer', 'analyze_predictive_scenario', 0.9)],
                'general': [('predictive_analyzer', 'analyze_predictive_scenario', 0.8)]
            }
        }
        
        # Keyword -> Additional handlers
        self.keyword_handlers = {
            'currency': [('currency_inflation_analyzer', 'analyze_currency_inflation_question', 0.8)],
            'gold': [('thematic_analyzer', 'analyze_thematic_question', 0.7)],
            'equity': [('thematic_analyzer', 'analyze_thematic_question', 0.7)],
            'time': [('time_based_analyzer', 'analyze_time_based_question', 0.8)]
        }
    
    def route_question(self, question: str) -> List[Dict]:
        """Soruyu analiz et ve uygun handler'ları belirle"""
        
        # 1. Soruyu analiz et
        analysis = self.analyzer.analyze_question(question)
        print(f"\n[ROUTING] Analiz sonucu:")
        print(f"  - Tip: {analysis.question_type}")
        print(f"  - Intent: {analysis.intent}")
        print(f"  - Fon kodları: {analysis.fund_codes}")
        print(f"  - Keywords: {analysis.keywords}")
        print(f"  - Parametreler: {analysis.parameters}")
        
        # 2. Ana handler'ları belirle
        routes = self._get_primary_routes(analysis)
        
        # 3. Ek handler'ları ekle (keyword bazlı)
        additional_routes = self._get_additional_routes(analysis)
        routes.extend(additional_routes)
        
        # 4. Özel durumları kontrol et
        routes = self._apply_special_rules(routes, analysis)
        
        # 5. Skorlara göre sırala ve döndür
        routes.sort(key=lambda x: x['confidence'], reverse=True)
        
        # 6. Context bilgilerini ekle
        for route in routes:
            route['context'] = self._prepare_context(analysis, route)
        
        print(f"\n[ROUTING] {len(routes)} route belirlendi:")
        for r in routes:
            print(f"  - {r['handler']}.{r['method']} (confidence: {r['confidence']:.2f})")
        
        return routes
    
    def _get_primary_routes(self, analysis: QuestionAnalysis) -> List[Dict]:
        """Ana handler'ları belirle"""
        routes = []
        
        # Intent ve question_type kombinasyonuna göre
        intent_map = self.intent_handlers.get(analysis.intent, {})
        handlers = intent_map.get(analysis.question_type, [])
        
        for handler, method, confidence in handlers:
            routes.append({
                'handler': handler,
                'method': method,
                'confidence': confidence,
                'reason': f"{analysis.intent}_{analysis.question_type}"
            })
        
        return routes
    
    def _get_additional_routes(self, analysis: QuestionAnalysis) -> List[Dict]:
        """Keyword bazlı ek handler'lar"""
        routes = []
        
        for category, keywords in analysis.keywords.items():
            if category in self.keyword_handlers:
                for handler, method, confidence in self.keyword_handlers[category]:
                    # Aynı handler tekrar eklenmemeli
                    if not any(r['handler'] == handler for r in routes):
                        routes.append({
                            'handler': handler,
                            'method': method,
                            'confidence': confidence * 0.8,  # Ek handler'lar biraz düşük skorlu
                            'reason': f"keyword_{category}"
                        })
        
        return routes
    
    def _apply_special_rules(self, routes: List[Dict], analysis: QuestionAnalysis) -> List[Dict]:
        """Özel durumlar için kurallar"""
        
        # KURAL 1: Tek fon analizi + para birimi kelimesi yoksa currency_inflation_analyzer'ı çıkar
        if analysis.question_type == 'single_fund':
            if 'currency' not in analysis.keywords:
                routes = [r for r in routes if r['handler'] != 'currency_inflation_analyzer']
        
        # KURAL 2: Karşılaştırma için sadece performance_analyzer
        if analysis.question_type == 'comparison':
            routes = [r for r in routes if r['handler'] == 'performance_analyzer']
        
        # KURAL 3: Portföy şirketi soruları
        portfoy_keywords = ['iş portföy', 'ak portföy', 'garanti portföy']
        if any(kw in analysis.normalized_question for kw in portfoy_keywords):
            routes.insert(0, {
                'handler': 'portfolio_company_analyzer',
                'method': 'analyze_company_comprehensive',
                'confidence': 0.95,
                'reason': 'portfolio_company_detected'
            })
        
        return routes
    
    def _prepare_context(self, analysis: QuestionAnalysis, route: Dict) -> Dict:
        """Handler için context hazırla - RİSK ANALİZİ DAHİL"""
        context = {}
        
        # Parametreleri kopyala
        context.update(analysis.parameters)
        
        # RİSK ANALİZİ - Fon kodları varsa risk kontrolü yap
        if analysis.fund_codes and self.enable_risk_check:
            risk_assessments = {}
            for fcode in analysis.fund_codes:
                is_safe, risk_data, risk_warning = self._check_fund_risk(fcode)
                risk_assessments[fcode] = {
                    'is_safe': is_safe,
                    'risk_data': risk_data,
                    'risk_warning': risk_warning,
                    'risk_level': risk_data['risk_level'] if risk_data else 'UNKNOWN'
                }
            
            context['risk_assessments'] = risk_assessments
            
            # Eğer EXTREME riskli fon varsa özel işlem
            extreme_risk_funds = [
                fcode for fcode, assessment in risk_assessments.items() 
                if assessment['risk_level'] == 'EXTREME'
            ]
            
            if extreme_risk_funds:
                context['has_extreme_risk'] = True
                context['extreme_risk_funds'] = extreme_risk_funds
        
        # Handler'a özel context
        if route['handler'] == 'performance_analyzer':
            if analysis.fund_codes:
                context['fund_codes'] = analysis.fund_codes
                if len(analysis.fund_codes) == 1:
                    context['fund_code'] = analysis.fund_codes[0]
        
        elif route['handler'] == 'currency_inflation_analyzer':
            # Currency type belirleme
            if 'currency' in analysis.keywords:
                currency_keywords = analysis.keywords['currency']
                if 'dolar' in currency_keywords or 'usd' in currency_keywords:
                    context['currency_type'] = 'usd'
                elif 'euro' in currency_keywords or 'eur' in currency_keywords:
                    context['currency_type'] = 'eur'
                else:
                    context['currency_type'] = 'all'
            else:
                context['currency_type'] = 'all'
        
        return context
    
    def _check_fund_risk(self, fcode: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Fon risk kontrolü - mevcut risk_assessment.py kullanarak"""
        try:
            # MV'den risk verilerini çek
            query = f"""
            SELECT 
                fcode,
                current_price,
                price_vs_sma20,
                rsi_14,
                stochastic_14,
                days_since_last_trade,
                investorcount
            FROM mv_fund_technical_indicators 
            WHERE fcode = '{fcode}'
            """
            
            result = self.db.execute_query(query)
            
            if result.empty:
                return True, None, ""  # Veri yoksa güvenli say
            
            row = result.iloc[0]
            
            risk_data = {
                'fcode': fcode,
                'price_vs_sma20': float(row['price_vs_sma20']) if pd.notna(row['price_vs_sma20']) else 0,
                'rsi_14': float(row['rsi_14']) if pd.notna(row['rsi_14']) else 50,
                'stochastic_14': float(row['stochastic_14']) if pd.notna(row['stochastic_14']) else 50,
                'days_since_last_trade': int(row['days_since_last_trade']) if pd.notna(row['days_since_last_trade']) else 0,
                'investorcount': int(row['investorcount']) if pd.notna(row['investorcount']) else 0
            }
            
            # Risk değerlendirmesi
            risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
            risk_warning = RiskAssessment.format_risk_warning(risk_assessment)
            
            # EXTREME risk fonları güvenli değil
            is_safe = risk_assessment['risk_level'] not in ['EXTREME']
            
            return is_safe, risk_assessment, risk_warning
            
        except Exception as e:
            print(f"Risk kontrolü hatası ({fcode}): {e}")
            return True, None, ""  # Hata durumunda güvenli say
    
    def _apply_special_rules(self, routes: List[Dict], analysis: QuestionAnalysis) -> List[Dict]:
        """Özel durumlar için kurallar - RİSK BAZLI KURALLAR DAHİL"""
        
        # KURAL 1: Tek fon analizi + para birimi kelimesi yoksa currency_inflation_analyzer'ı çıkar
        if analysis.question_type == 'single_fund':
            if 'currency' not in analysis.keywords:
                routes = [r for r in routes if r['handler'] != 'currency_inflation_analyzer']
        
        # KURAL 2: Karşılaştırma için sadece performance_analyzer
        if analysis.question_type == 'comparison':
            routes = [r for r in routes if r['handler'] == 'performance_analyzer']
        
        # KURAL 3: Portföy şirketi soruları
        portfoy_keywords = ['iş portföy', 'ak portföy', 'garanti portföy']
        if any(kw in analysis.normalized_question for kw in portfoy_keywords):
            routes.insert(0, {
                'handler': 'portfolio_company_analyzer',
                'method': 'analyze_company_comprehensive',
                'confidence': 0.95,
                'reason': 'portfolio_company_detected'
            })
        
        # KURAL 4: RİSK BAZLI ROUTING - YENİ
        if self.enable_risk_check and analysis.fund_codes:
            # Risk kontrolü yap
            high_risk_funds = []
            for fcode in analysis.fund_codes:
                is_safe, risk_data, _ = self._check_fund_risk(fcode)
                if not is_safe and risk_data and risk_data['risk_level'] in ['HIGH', 'EXTREME']:
                    high_risk_funds.append(fcode)
            
            # Yüksek riskli fonlar varsa risk handler'ı ekle
            if high_risk_funds:
                routes.insert(0, {
                    'handler': 'risk_analyzer',
                    'method': 'analyze_high_risk_funds',
                    'confidence': 0.99,
                    'reason': 'high_risk_funds_detected'
                })
        
        # KURAL 5: Güvenli fon soruları için risk kontrolü zorunlu
        safety_keywords = ['güvenli', 'risk', 'kayıp', 'volatilite']
        if any(kw in analysis.normalized_question for kw in safety_keywords):
            # Risk kontrolünü zorunlu yap
            for route in routes:
                route['require_risk_check'] = True
        
        return routes
