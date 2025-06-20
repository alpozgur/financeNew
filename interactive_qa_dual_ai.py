# interactive_qa_dual_ai.py
"""
TEFAS Analysis System - OpenAI 
"""
import numbers
import re
import sys
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from config.config import Config
from analysis.coordinator import AnalysisCoordinator
from analysis.hybrid_fund_selector import HybridFundSelector, HighPerformanceFundAnalyzer
from ai_smart_question_router import AISmartQuestionRouter, AIRouteMatch
# from analysis.performance import batch_analyze_funds_by_details
# Mevcut import'ların altına ekleyin:
from advanced_metrics_analyzer import AdvancedMetricsAnalyzer
from thematic_fund_analyzer import ThematicFundAnalyzer
from utils import normalize_turkish_text
from technical_analysis import TechnicalAnalysis
from performance_analysis import PerformanceAnalyzerMain
from fundamental_analysis import FundamentalAnalysisEnhancement
from portfolio_company_analysis import EnhancedPortfolioCompanyAnalyzer
from currency_inflation_analyzer import CurrencyInflationAnalyzer
from time_based_analyzer import TimeBasedAnalyzer
from scenario_analysis import ScenarioAnalyzer
from personal_finance_analyzer import PersonalFinanceAnalyzer
from mathematical_calculations import MathematicalCalculator
from macroeconomic_analyzer import MacroeconomicAnalyzer
from response_merger import ResponseMerger
from ai_provider import AIProvider
from predictive_scenario_analyzer import PredictiveScenarioAnalyzer
from semantic_router import SemanticRouter
@dataclass
class RouteMatch:
    """Route eşleşme sonucu"""
    handler: str
    method: str
    score: float
    context: Dict[str, Any]
    matched_pattern: Optional[str] = None
    route_name: Optional[str] = None
class DualAITefasQA:
    """TEFAS Soru-Cevap Sistemi - OpenAI Destekli"""
    
    def __init__(self):
        print("🚀 TEFAS Analysis Dual AI Q&A System Loading...")
        self.config = Config()
        self.coordinator = AnalysisCoordinator(self.config)

        # Aktif fonları yükle
        print("📊 Loading active funds...")
        self.active_funds = self._load_active_funds()
        print(f"✅ Loaded {len(self.active_funds)} active funds")
        # YENİ: AI Provider
        self.ai_provider = AIProvider(self.coordinator)
      #  self.ai_status = self._check_ai_availability()
         # ESKİ: self.ai_status = self._check_ai_availability()
        # YENİ: Compatibility için ai_status'u tut ama ai_provider'dan al
        self.ai_status = {
            'openai': self.ai_provider.get_status()['openai_status']
        }
        # Modüllere ai_status yerine ai_provider geçebiliriz ama şimdilik uyumluluk için böyle
        self.advanced_metrics_analyzer = AdvancedMetricsAnalyzer(self.coordinator, self.active_funds, self.ai_status)
        self.technical_analyzer = TechnicalAnalysis(
            self.coordinator, 
            self.active_funds,
            self.ai_provider  # YENİ - ai_provider'ı geç
        )
        self.fundamental_analyzer = FundamentalAnalysisEnhancement(self.coordinator, self.active_funds)
        self.portfolio_analyzer = EnhancedPortfolioCompanyAnalyzer(self.coordinator)
        self.thematic_analyzer = ThematicFundAnalyzer(self.coordinator.db, self.config)
        self.performanceMain = PerformanceAnalyzerMain(self.coordinator, self.active_funds, self.ai_status)
        self.currency_analyzer = CurrencyInflationAnalyzer(self.coordinator.db, self.config)
        self.personal_analyzer = PersonalFinanceAnalyzer(self.coordinator, self.active_funds)
        self.time_analyzer = TimeBasedAnalyzer(self.coordinator, self.active_funds)
        self.scenario_analyzer = ScenarioAnalyzer(self.coordinator, self.active_funds)
        self.math_calculator = MathematicalCalculator(self.coordinator, self.active_funds)
        self.macro_analyzer = MacroeconomicAnalyzer(self.coordinator.db, self.config,self.coordinator)
        self.response_merger = ResponseMerger()
        self.enable_multi_handler = True  # Feature flag
        from ai_personalized_advisor import AIPersonalizedAdvisor
        self.ai_router = AISmartQuestionRouter(self.ai_provider)
        self.routing_enabled = True  # Routing'i tamamen kapatmak için
        self.ai_advisor = AIPersonalizedAdvisor(self.coordinator, self.ai_provider)        
        # Feature flags
        self.enable_multi_handler = True
        self.predictive_analyzer = PredictiveScenarioAnalyzer(
            self.coordinator,
            self.scenario_analyzer
        )        
        # --- SEMANTIC ROUTER ENTEGRASYONU ---
        self.semantic_router = SemanticRouter(
            model_name='all-MiniLM-L6-v2',
            similarity_threshold=0.85,
            max_matches=5
        )
        # Handler'ları semantic router'a ekle
        self._register_semantic_handlers()

    def _register_semantic_handlers(self):
        # Her handler için açıklama, methodlar ve örnek sorular
        self.semantic_router.add_handler(
            handler='performance_analyzer',
            description='Fon performans analizi, getiri analizi, en çok kazandıran/kaybettiren fonlar, performans karşılaştırması.',
            methods={
                'handle_safest_funds_sql_fast': 'En güvenli fonları listeler',
                'handle_riskiest_funds_list': 'En riskli fonları listeler',
                'handle_top_gainers': 'En çok kazandıran fonları listeler',
                'handle_worst_funds_list': 'En çok kaybettiren fonları listeler',
                'handle_analysis_question_dual': 'Genel fon performans analizi yapar',
            },
            examples=[
                'En çok kazandıran fonlar hangileri?',
                'Son 1 yılın en çok kazandıran fonları',
                'En çok kaybettiren fonlar nelerdir?',
                'En iyi performans gösteren fonlar',
                'En yüksek getirili fonlar',
                'En çok kazandıran 10 fon',
                'Son 3 ayın en iyi fonları',
                'En yüksek performanslı fonlar'
            ],
            execution_order=5  # Daha yüksek öncelik
        )
        self.semantic_router.add_handler(
            handler='scenario_analyzer',
            description='Senaryo bazlı fon analizi ve tahminler.',
            methods={
                'analyze_scenario_question': 'Senaryo bazlı analiz',
            },
            examples=[
                'Enflasyon artarsa hangi fonlar etkilenir?',
                'Dolar yükselirse fonlar ne olur?',
                'Faiz düşerse hangi fonlar avantajlı olur?'
            ],
            execution_order=20
        )
        self.semantic_router.add_handler(
            handler='personal_finance_analyzer',
            description='Kişisel finans ve yatırım danışmanlığı.',
            methods={
                'analyze_personal_finance_question': 'Kişisel finans sorularını yanıtlar',
            },
            examples=[
                'Birikimimi hangi fona yatırmalıyım?',
                'Emeklilik için en uygun fon hangisi?',
                'Kısa vadede kazançlı fon önerisi'
            ],
            execution_order=30
        )
        self.semantic_router.add_handler(
            handler='technical_analyzer',
            description='Fonlar için teknik analiz ve sinyal üretimi.',
            methods={
                'handle_ai_pattern_analysis': 'AI tabanlı teknik analiz',
                'handle_technical_analysis_questions_full_db': 'Teknik analiz sorularını yanıtlar',
            },
            examples=[
                'MACD sinyali veren fonlar',
                'RSI değeri yüksek fonlar',
                'Teknik analiz ile alım sinyali',
                'AI teknik analiz önerisi'
            ],
            execution_order=40
        )
        self.semantic_router.add_handler(
            handler='currency_inflation_analyzer',
            description='Döviz ve enflasyon etkisi analizi.',
            methods={
                'analyze_currency_funds': 'Döviz bazlı fon analizi',
            },
            examples=[
                'Dolar bazında en iyi fonlar',
                'Enflasyona karşı koruyan fonlar',
                'Euro bazında fon performansı'
            ],
            execution_order=50
        )
        self.semantic_router.add_handler(
            handler='portfolio_company_analyzer',
            description='Portföy şirketleri ve karşılaştırmalı analiz.',
            methods={
                'analyze_company_comprehensive': 'Şirket bazlı analiz',
                'find_best_portfolio_company_unlimited': 'En iyi portföy şirketini bulur',
            },
            examples=[
                'İş Portföy analizi',
                'Ak Portföy vs Garanti Portföy karşılaştırması',
                'En başarılı portföy şirketi hangisi?'
            ],
            execution_order=60
        )
        self.semantic_router.add_handler(
            handler='advanced_metrics_analyzer',
            description='Fonlar için gelişmiş metrik analizleri.',
            methods={
                'handle_beta_analysis': 'Beta katsayısı analizi',
                'handle_alpha_analysis': 'Alpha analizi',
                'handle_tracking_error_analysis': 'Tracking error analizi',
                'handle_information_ratio_analysis': 'Bilgi oranı analizi',
            },
            examples=[
                'Beta katsayısı düşük fonlar',
                'Alpha değeri yüksek fonlar',
                'Tracking error düşük fonlar',
                'Bilgi oranı yüksek fonlar'
            ],
            execution_order=70
        )
        self.semantic_router.add_handler(
            handler='thematic_analyzer',
            description='Tematik fonlar ve sektör bazlı analiz.',
            methods={
                'analyze_thematic_question': 'Tematik fon analizi',
            },
            examples=[
                'Teknoloji temalı fonlar',
                'Sağlık sektörü fonları',
                'Yeşil enerji fonları'
            ],
            execution_order=80
        )
        self.semantic_router.add_handler(
            handler='fundamental_analyzer',
            description='Fonların temel analizleri ve büyüklük, yaş, kategori gibi bilgiler.',
            methods={
                'handle_capacity_questions': 'Fon kapasite ve büyüklük analizi',
                'handle_investor_count_questions': 'Yatırımcı sayısı analizi',
                'handle_new_funds_questions': 'Yeni fonlar',
                'handle_largest_funds_questions': 'En büyük fonlar',
                'handle_fund_age_questions': 'Fon yaşı',
                'handle_fund_category_questions': 'Fon kategorisi',
            },
            examples=[
                'En büyük fonlar hangileri?',
                'Yatırımcı sayısı en fazla olan fonlar',
                'Yeni kurulan fonlar',
                'Fon kategorileri nelerdir?'
            ],
            execution_order=90
        )
        self.semantic_router.add_handler(
            handler='math_calculator',
            description='Matematiksel finans hesaplamaları.',
            methods={
                'analyze_mathematical_question': 'Matematiksel soru analizleri',
            },
            examples=[
                'Fon getirisi nasıl hesaplanır?',
                'Sharpe oranı nasıl bulunur?',
                'Risk/ödül oranı nedir?'
            ],
            execution_order=100
        )
        self.semantic_router.add_handler(
            handler='time_based_analyzer',
            description='Zaman bazlı fon analizleri.',
            methods={
                'analyze_time_based_question': 'Zaman bazlı analiz',
            },
            examples=[
                'Son 1 ayın en iyi fonları',
                'Geçen yılın performansı',
                'Son 6 ayda en çok kazandıran fonlar'
            ],
            execution_order=110
        )
        self.semantic_router.add_handler(
            handler='macroeconomic_analyzer',
            description='Makroekonomik gelişmelerin fonlara etkisi.',
            methods={
                'analyze_macroeconomic_impact': 'Makroekonomik etki analizi',
            },
            examples=[
                'Faiz artışı fonları nasıl etkiler?',
                'Enflasyonun fonlara etkisi',
                'Döviz kuru değişimi ve fonlar'
            ],
            execution_order=120
        )

    def _load_active_funds(self, max_funds=None, mode="comprehensive"):
        """
        Gelişmiş fon yükleme sistemi
        mode: "hybrid" (1-2 dk), "comprehensive" (5-10 dk), "fast" (30 sn)
        """
        
        if mode == "hybrid":
            print("🎯 Hibrit mod: Akıllı örnekleme + Büyük fonlar")
            selector = HybridFundSelector(self.coordinator.db, self.config)
            active_funds, analysis_funds = selector.load_funds_hybrid(
                quick_sample=150,    # 150 temsili fon
                detailed_analysis=30, # 30 detaylı analiz
                include_top=True     # Büyük fonları dahil et
            )
            return analysis_funds
            
        elif mode == "comprehensive":
            print("🚀 Kapsamlı mod: TÜM FONLAR (5-10 dakika)")
            analyzer = HighPerformanceFundAnalyzer(self.coordinator.db, self.config)
            all_results = analyzer.analyze_all_funds_optimized(
                batch_size=100,
                max_workers=8,
                use_bulk_queries=True
            )
            # En iyi 50 fonu döndür
            return all_results.head(50)['fcode'].tolist()
            
        else:  # fast
            print("⚡ Hızlı mod: İlk 50 fon")
            all_funds = self.coordinator.db.get_all_fund_codes()
            return all_funds[:50]
        
    def _check_ai_availability(self):
        """AI sistemlerinin durumunu kontrol et"""
        # AI Provider'dan status al
        provider_status = self.ai_provider.get_status()
        
        print(f"\n🤖 AI SİSTEMİ DURUMU:")
        print(f"   📋 Provider: {provider_status['provider_type'].upper()}")
        print(f"   ✅ Durum: {'Hazır' if provider_status['is_available'] else 'Mevcut değil'}")
        
        # Legacy uyumluluk için eski formatı döndür
        ai_status = {
            'openai': provider_status['openai_status']
        }
        
        print(f"   📱 OpenAI: {'✅ Hazır' if ai_status['openai'] else '❌ Mevcut değil'}")
        
        if provider_status['provider_type'] == 'dual' and ai_status['openai']:
            print("   🎯 Dual mode aktif - Karşılaştırmalı analiz mevcut!")
        elif ai_status['openai']:
            print("   🎯 Sadece OpenAI aktif")
        else:
            print("   ⚠️ Hiçbir AI sistemi aktif değil")
        
        return ai_status
    

    def answer_question(self, question):
        """AI-powered multi-handler routing ile soru cevaplama"""
        question_lower = normalize_turkish_text(question)
        
        # Routing aktif mi?
        if not self.routing_enabled:
            # Direkt legacy routing kullan
            numbers = re.findall(r'(\d+)', question)
            requested_count = int(numbers[0]) if numbers else 1
            return self._legacy_routing(question, question_lower, requested_count)
        
        try:
            # --- SEMANTIC ROUTER KULLANIMI ---
            routes = self.semantic_router.route(question)
            if routes:
                print(f"🎯 Semantic Routing: {len(routes)} handler bulundu")
                for i, route in enumerate(routes, 1):
                    print(f"  {i}. {route.handler}.{route.method} (güven: {route.confidence:.2f})")
                    print(f"     Sebep: {route.reasoning}")
                
                # Multi-handler mı?
                if len(routes) > 1 and any(r.is_multi_handler for r in routes):
                    # Multi-handler execution
                    responses = self._execute_multi_handlers_ai(routes, question)
                    if responses:
                        return self.response_merger.merge_responses(responses, question)
                else:
                    # Single handler execution
                    response = self._execute_single_handler_ai(routes[0], question)
                    if response:
                        return response
            
        except Exception as e:
            print(f"❌ Semantic routing hatası: {e}")
            import traceback
            traceback.print_exc()
        
        # Fallback: Legacy routing
        print("⚠️ Fallback: Legacy routing kullanılıyor")
        numbers = re.findall(r'(\d+)', question)
        requested_count = int(numbers[0]) if numbers else 1
        return self._legacy_routing(question, question_lower, requested_count)

    # 4. YENİ METODLAR EKLE
    def _execute_single_handler_ai(self, route: AIRouteMatch, question: str) -> Optional[str]:
        """Tek handler'ı çalıştır - DÜZELTME"""
        handler_name = route.handler
        method_name = route.method
        
        # Handler'ı bul
        handler = self._get_handler_instance(handler_name)
        if not handler:
            print(f"❌ Handler bulunamadı: {handler_name}")
            return None
        
        # Method'u bul
        method = getattr(handler, method_name, None)
        if not method:
            print(f"❌ Method bulunamadı: {handler_name}.{method_name}")
            return None
        
        try:
            # Parametreleri hazırla
            import inspect
            sig = inspect.signature(method)
            params = {}
            
            # Her method için özel parametre mapping
            if method_name == 'handle_safest_funds_sql_fast':
                if 'count' in sig.parameters:
                    # 'X' veya string değerleri kontrol et
                    count = route.context.get('requested_count', 10)
                    if isinstance(count, str) and not count.isdigit():
                        count = 10  # Default değer
                    else:
                        count = int(count) if isinstance(count, str) else count
                    params['count'] = count                    
            elif method_name == 'handle_top_gainers':
                if 'question' in sig.parameters:
                    params['question'] = question
                if 'count' in sig.parameters:
                    params['count'] = route.context.get('requested_count', 10)
                if 'risk_context' in sig.parameters:
                    params['risk_context'] = False
                    
            elif method_name == 'analyze_inflation_scenario':
                if 'question' in sig.parameters:
                    params['question'] = question
                    
            elif method_name == 'handle_combined_metrics_analysis':
                if 'question' in sig.parameters:
                    params['question'] = question
                    
            elif method_name == 'handle_ai_pattern_analysis':
                if 'question' in sig.parameters:
                    # Fund code varsa ekle
                    fund_code = route.context.get('fund_code')
                    if fund_code:
                        params['question'] = f"{fund_code} {question}"
                    else:
                        params['question'] = question                    
            elif method_name == 'handle_beta_analysis':
                if 'question' in sig.parameters:
                    params['question'] = question
                    
            elif method_name == 'handle_analysis_question_dual':
                if 'question' in sig.parameters:
                    # Fund code'u question'a ekle
                    fund_code = route.context.get('fund_code')
                    if fund_code and fund_code not in question:
                        params['question'] = f"{fund_code} {question}"
                    else:
                        params['question'] = question
                        
            elif method_name == 'analyze_currency_funds':
                # Bu method currency_type parametresi istiyor
                if 'currency_type' in sig.parameters:
                    params['currency_type'] = route.context.get('currency', 'USD')
                if 'top_n' in sig.parameters:
                    params['top_n'] = route.context.get('requested_count', 10)
                    
            else:
                # Genel durum
                if 'question' in sig.parameters:
                    params['question'] = question
            
            print(f"✅ Executing: {handler_name}.{method_name}")
            print(f"   Parameters: {list(params.keys())}")
            
            # Handler'ı çalıştır
            result = method(**params)
            return result
            
        except Exception as e:
            print(f"❌ Handler execution hatası: {e}")
            import traceback
            traceback.print_exc()
            return None
    def _execute_multi_handlers_ai(self, routes: List[AIRouteMatch], question: str) -> List[Dict]:
        """Multi handler execution - AI routing için"""
        responses = []
        executed_handlers = set()
        
        # Execution order'a göre sırala
        routes.sort(key=lambda x: x.execution_order)
        
        for route in routes:
            # Aynı handler'ı tekrar çalıştırma (multi-handler değilse)
            if route.handler in executed_handlers and not route.is_multi_handler:
                continue
            
            handler = self._get_handler_instance(route.handler)
            if not handler:
                continue
            
            try:
                method = getattr(handler, route.method, None)
                if not method:
                    continue
                
                # Parametreleri hazırla
                params = self._prepare_method_params_ai(method, route.context, question)
                
                print(f"✅ Multi-executing: {route.handler}.{route.method}")
                
                result = method(**params)
                
                if result:
                    responses.append({
                        'handler': route.handler,
                        'method': route.method,
                        'response': result,
                        'score': route.confidence,
                        'context': route.context,
                        'reasoning': route.reasoning
                    })
                    executed_handlers.add(route.handler)
                    
            except Exception as e:
                print(f"❌ Multi-handler execution hatası ({route.handler}): {e}")
                continue
        
        return responses

    def _prepare_method_params_ai(self, method, context: Dict, question: str) -> Dict:
        """AI context'ten method parametrelerini hazırla"""
        import inspect
        
        sig = inspect.signature(method)
        params = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            # Question her zaman var
            if param_name == 'question':
                params['question'] = question
            
            # Context'ten al
            elif param_name in context:
                params[param_name] = context[param_name]
            
            # Özel mapping'ler
            elif param_name == 'count' and 'requested_count' in context:
                params['count'] = context['requested_count']
            
            elif param_name == 'requested_count' and 'count' in context:
                params['requested_count'] = context['count']
            
            # Default değer varsa kullan
            elif param.default != inspect.Parameter.empty:
                params[param_name] = param.default
            
            # Özel durumlar
            elif param_name == 'days' and param.default == inspect.Parameter.empty:
                params['days'] = context.get('days', 30)
            
            elif param_name == 'count' and param.default == inspect.Parameter.empty:
                params['count'] = context.get('requested_count', 10)
        
        return params

    def _get_handler_instance(self, handler_name: str):
        """Handler instance'ını döndür"""
        handler_map = {
            'performance_analyzer': self.performanceMain,
            'scenario_analyzer': self.scenario_analyzer,
            'personal_finance_analyzer': self.personal_analyzer,
            'technical_analyzer': self.technical_analyzer,
            'currency_inflation_analyzer': self.currency_analyzer,
            'portfolio_company_analyzer': self.portfolio_analyzer,
            'mathematical_calculator': self.math_calculator,
            'time_based_analyzer': self.time_analyzer,
            'macroeconomic_analyzer': self.macro_analyzer,
            'advanced_metrics_analyzer': self.advanced_metrics_analyzer,
            'thematic_analyzer': self.thematic_analyzer,
            'fundamental_analyzer': self.fundamental_analyzer,
            'predictive_analyzer': self.predictive_analyzer,
            'ai_advisor': self.ai_advisor
        }
        handler = handler_map.get(handler_name)
        if not handler:
            print(f"⚠️ Handler bulunamadı: {handler_name}")
        return handler

    def _legacy_single_handler(self, question: str, question_lower: str) -> str:
        """Eski tek handler sistemi (fallback)"""
        # Mevcut _legacy_routing metodunuzu buraya taşıyın
        numbers_in_question = re.findall(r'(\d+)', question)
        requested_count = int(numbers_in_question[0]) if numbers_in_question else 1
        
        return self._legacy_routing(question, question_lower, requested_count)

    

    def _legacy_routing(self, question, question_lower, requested_count):
        """Mevcut if-else routing mantığınız - TAM OLARAK AYNI"""
        
        # 🔮 PREDİKTİF SENARYO SORULARI - EN BAŞA TAŞI
        if any(word in question_lower for word in ['sonra', 'tahmin', 'gelecek', 'olacak', 'beklenti', 'vadede']):
            if any(word in question_lower for word in ['enflasyon', 'dolar', 'faiz', 'borsa', 'ay', 'gün', 'hafta']):
                print("🔮 Legacy routing: Prediktif senaryo tespit edildi")
                return self.predictive_analyzer.analyze_predictive_scenario(question)
        
        # 🤖 AI PATTERN RECOGNITION
        if any(word in question_lower for word in ['ai teknik', 'ai pattern', 'ai sinyal']):
            return self.technical_analyzer.handle_ai_pattern_analysis(question)
            
        # 🎲 SENARYO ANALİZİ SORULARI
        if self.scenario_analyzer.is_scenario_question(question):
            # "sonra" içeriyorsa predictive'e yönlendir
            if any(word in question_lower for word in ['sonra', 'tahmin', 'gelecek']):
                return self.predictive_analyzer.analyze_predictive_scenario(question)
            return self.scenario_analyzer.analyze_scenario_question(question)
            
        # Makroekonomik sorular - HATA AYIKLAMA İÇİN TRY-EXCEPT EKLE
        try:
            if hasattr(self, 'macro_analyzer') and self.macro_analyzer.is_macroeconomic_question(question):
                return self.macro_analyzer.analyze_macroeconomic_impact(question)
        except Exception as e:
            import traceback
            print(f"Makro analiz hatası detayı:")
            traceback.print_exc()
            return f"❌ Makroekonomik analiz hatası: {str(e)}\n\nLütfen soruyu farklı şekilde sorun."

        if MathematicalCalculator.is_mathematical_question(question):
            return self.math_calculator.analyze_mathematical_question(question)
            
        # KİŞİSEL FİNANS SORULARI
        if self.personal_analyzer.is_personal_finance_question(question):
            return self.personal_analyzer.analyze_personal_finance_question(question)
            
        # ZAMAN BAZLI ANALİZLER - YENİ
        if TimeBasedAnalyzer.is_time_based_question(question):
            time_result = self.time_analyzer.analyze_time_based_question(question)
            if time_result:
                return time_result
                
        # GÜVENLİ FONLAR - ÇOKLU LİSTE DESTEĞİ
        if any(word in question_lower for word in ['en güvenli', 'en az riskli', 'güvenli fonlar']):
            # Eğer sayı belirtilmişse (örn: "en güvenli 10 fon") -> liste ver
            if requested_count > 1 or 'fonlar' in question_lower:
                return self.performanceMain.handle_safest_funds_sql_fast(requested_count)
            else:
                # Tek fon istiyorsa -> eski metodu kullan
                return self.performanceMain.handle_safest_fund()
        
        # RİSKLİ FONLAR - ÇOKLU LİSTE DESTEĞİ  
        if "en riskli" in question_lower:
            if requested_count > 1 or 'fonlar' in question_lower:
                return self.performanceMain.handle_riskiest_funds_list(requested_count)
            else:
                return self.performanceMain.handle_most_risky_fund()
        
        # EN ÇOK KAYBETTİREN - ÇOKLU LİSTE DESTEĞİ
        if any(word in question_lower for word in ['en çok kaybettiren', 'en çok düşen']):
            if requested_count > 1 or 'fonlar' in question_lower:
                return self.performanceMain.handle_worst_funds_list(requested_count)
            else:
                return self.performanceMain.handle_worst_fund()
                     # Özel risk sorusu yakalama
        if "en riskli" in question_lower:
             return self.performanceMain.handle_most_risky_fund()
        if "en güvenli" in question_lower or "en az riskli" in question_lower:
             return self.performanceMain.handle_safest_fund()
        if "en çok kaybettiren" in question_lower or "en çok düşen" in question_lower:
             return self.performanceMain.handle_worst_fund()
        if any(word in question_lower for word in ['portföy', 'portfolio']):
           
            # Belirli şirket kapsamlı analizi
             if any(word in question_lower for word in ['iş portföy', 'is portfoy', 'işbank portföy']):
                 return self.portfolio_analyzer.analyze_company_comprehensive('İş Portföy')
            
             elif any(word in question_lower for word in ['ak portföy', 'akbank portföy']):
                 return self.portfolio_analyzer.analyze_company_comprehensive('Ak Portföy')
            
             elif any(word in question_lower for word in ['garanti portföy', 'garantibank portföy']):
                 return self.portfolio_analyzer.analyze_company_comprehensive('Garanti Portföy')
            
             elif any(word in question_lower for word in ['ata portföy']):
                 return self.portfolio_analyzer.analyze_company_comprehensive('Ata Portföy')
            
             elif any(word in question_lower for word in ['qnb portföy']):
                 return self.portfolio_analyzer.analyze_company_comprehensive('QNB Portföy')
            
             elif any(word in question_lower for word in ['fiba portföy', 'fibabank portföy']):
                 return self.portfolio_analyzer.analyze_company_comprehensive('Fiba Portföy')
            
             # Şirket karşılaştırması
             elif any(word in question_lower for word in ['vs', 'karşı', 'karşılaştır', 'compare']):
                 return self._handle_company_comparison_enhanced(question)
            
             # En başarılı şirket
             elif any(word in question_lower for word in ['en başarılı', 'en iyi', 'best', 'most successful']):
                 return self.portfolio_analyzer.find_best_portfolio_company_unlimited()
            
             else:
                 return self._handle_portfolio_companies_overview(question)     
            
        elif any(word in question_lower for word in ['beta katsayısı', 'beta değeri', 'beta 1', 
                                                         'beta düşük', 'beta yüksek', 'beta altında','beta katsayisi', 'beta degeri', 'beta coefficient', 
                                             'beta 1', 'beta dusuk', 'beta yuksek', 'beta altinda',
                                             'beta less than', 'beta greater than']):
             return self.advanced_metrics_analyzer.handle_beta_analysis(question)
            
        elif any(word in question_lower for word in ['alpha değeri', 'alpha pozitif', 'jensen alpha', 
                                                         'alpha negatif', 'alfa değeri', 'alfa pozitif']):
             return self.advanced_metrics_analyzer.handle_alpha_analysis(question)
            
        elif any(word in question_lower for word in ['tracking error', 'takip hatası', 'index fon tracking',
                                                         'endeks fon tracking', 'tracking error düşük']):
             return self.advanced_metrics_analyzer.handle_tracking_error_analysis(question)
            
        elif any(word in question_lower for word in ['information ratio', 'bilgi oranı', 'ir yüksek',
                                                         'information ratio yüksek', 'aktif fon ir']):
             return self.advanced_metrics_analyzer.handle_information_ratio_analysis(question)
       
         # 📈 TEMATİK FON SORULARI - TÜM VERİTABANI 
        if self.thematic_analyzer.is_thematic_question(question):
             return self.thematic_analyzer.analyze_thematic_question(question)
                # FUNDAMENTAL ANALİZ SORULARI 🆕
        if any(word in question_lower for word in ['kapasite', 'büyüklük', 'büyük fon']):
             return self.fundamental_analyzer.handle_capacity_questions(question)
        
        if any(word in question_lower for word in ['yatırımcı sayısı', 'popüler fon']):
             return self.fundamental_analyzer.handle_investor_count_questions(question)
        
        if any(word in question_lower for word in ['yeni fon', 'yeni kurulan']):
             return self.fundamental_analyzer.handle_new_funds_questions(question)
        
        if any(word in question_lower for word in ['en büyük', 'largest']):
             return self.fundamental_analyzer.handle_largest_funds_questions(question)
        
        if any(word in question_lower for word in ['en eski', 'köklü']):
             return self.fundamental_analyzer.handle_fund_age_questions(question)
        
        if any(word in question_lower for word in ['kategori', 'tür']):
             return self.fundamental_analyzer.handle_fund_category_questions(question)        
         # --- Gelişmiş anahtar kelime tabanlı analizler ---
        if any(word in question_lower for word in ['yatırım dağılımı', 'varlık dağılımı', 'kompozisyon', 'içerik', 'portföy içerik']):
             return self._handle_fund_allocation_question(question)
        if 'fon kategorisi' in question_lower or 'fon türü' in question_lower:
             return self._handle_fund_category_question(question)
        if any(word in question_lower for word in ['kazanç', 'getiri', 'son 1 yıl', 'son 12 ay', 'geçtiğimiz yıl', 'son yıl']):
             return self.performanceMain.handle_fund_past_performance_question(question)
        if any(word in question_lower for word in ['en çok kazandıran', 'en çok getiri']):
             return self.performanceMain.handle_top_gainer_fund_question(question)
        if 'en çok kazandıran' in question_lower or 'en çok getiri' in question_lower:
             return self.performanceMain.handle_top_gainer_fund_question(question)
        if 'düşüşte olan fonlar' in question_lower or 'en çok kaybettiren' in question_lower:
             return self.performanceMain.handle_top_loser_fund_question(question)
        if 'sharpe oranı en yüksek' in question_lower:
             return self.performanceMain.handle_top_sharpe_funds_question(question)
        if 'volatilite' in question_lower and 'altında' in question_lower:
             return self.performanceMain.handle_low_volatility_funds_question(question)
         # --- mevcut kalan kodun ---
        if any(word in question_lower for word in ['2025', 'öneri', 'öner', 'recommend', 'suggest']):
             return self.performanceMain.handle_2025_recommendation_dual(question)
        elif any(word in question_lower for word in ['analiz', 'analyze', 'performance']):
             return self.performanceMain.handle_analysis_question_dual(question)
        elif any(word in question_lower for word in ['karşılaştır', 'compare', 'vs']):
             return self.performanceMain.handle_comparison_question(question)
        elif any(word in question_lower for word in ['risk', 'güvenli', 'safe']):
             return self._handle_risk_question(question)
        elif any(word in question_lower for word in ['piyasa', 'market', 'durum']):
             return self._handle_market_question_dual(question)

        elif any(word in question_lower for word in ['macd', 'bollinger', 'rsi', 'hareketli ortalama', 
                                                     'moving average', 'sma', 'ema', 'teknik sinyal',
                                                     'alım sinyali', 'satım sinyali', 'aşırı satım',
                                                     'aşırı alım', 'golden cross', 'death cross']):
             technical_result = self._handle_technical_analysis_questions_full_db(question)
             if technical_result:
                 return technical_result
             else:
                 return self._handle_general_question(question)

        elif any(word in question_lower for word in ['ai', 'yapay zeka', 'test']):
            return self._handle_ai_test_question(question)
        else:
             return self._handle_general_question(question)






    # def answer_question(self, question):
    #     """Soruya her iki AI ile de cevap ver"""
    #     question_lower =normalize_turkish_text(question)
    #     print(f"DEBUG - Question lower: {question_lower}")
    #     print(f"DEBUG - Alpha check: {any(word in question_lower for word in ['alpha degeri', 'alpha pozitif'])}")
    #     print(f"DEBUG - Tracking check: {any(word in question_lower for word in ['tracking error', 'takip hatasi'])}")
    #     # Sayısal değer parsing (10 fon, 5 fon vs.)
    #     numbers_in_question = re.findall(r'(\d+)', question)
    #     requested_count = int(numbers_in_question[0]) if numbers_in_question else 1
    # # 🎲 SENARYO ANALİZİ SORULARI - YENİ
    #     if self.scenario_analyzer.is_scenario_question(question):
    #         return self.scenario_analyzer.analyze_scenario_question(question)
    #     if CurrencyInflationAnalyzer.is_currency_inflation_question(question):
    #         return self.currency_analyzer.analyze_currency_inflation_question(question)
    #     # Makroekonomik sorular - HATA AYIKLAMA İÇİN TRY-EXCEPT EKLE
    #     try:
    #         if hasattr(self, 'macro_analyzer') and self.macro_analyzer.is_macroeconomic_question(question):
    #             return self.macro_analyzer.analyze_macroeconomic_impact(question)
    #     except Exception as e:
    #         import traceback
    #         print(f"Makro analiz hatası detayı:")
    #         traceback.print_exc()
    #         return f"❌ Makroekonomik analiz hatası: {str(e)}\n\nLütfen soruyu farklı şekilde sorun."


    #     if MathematicalCalculator.is_mathematical_question(question):
    #         return self.math_calculator.analyze_mathematical_question(question)
    #     # KİŞİSEL FİNANS SORULARI
    #     if self.personal_analyzer.is_personal_finance_question(question):
    #         return self.personal_analyzer.analyze_personal_finance_question(question)
    #     # ZAMAN BAZLI ANALİZLER - YENİ
    #     if TimeBasedAnalyzer.is_time_based_question(question):
    #         time_result = self.time_analyzer.analyze_time_based_question(question)
    #         if time_result:
    #             return time_result        
    #     # GÜVENLİ FONLAR - ÇOKLU LİSTE DESTEĞİ
    #     if any(word in question_lower for word in ['en güvenli', 'en az riskli', 'güvenli fonlar']):
    #         # Eğer sayı belirtilmişse (örn: "en güvenli 10 fon") -> liste ver
    #         if requested_count > 1 or 'fonlar' in question_lower:
    #             return self.performanceMain.handle_safest_funds_sql_fast(requested_count)
    #         else:
    #             # Tek fon istiyorsa -> eski metodu kullan
    #             return self.performanceMain.handle_safest_fund()
        
    #     # RİSKLİ FONLAR - ÇOKLU LİSTE DESTEĞİ  
    #     if "en riskli" in question_lower:

    def _handle_portfolio_companies_overview(self, question):
        """Genel portföy şirketleri genel bakış"""
        print("🏢 Portföy şirketleri genel analizi...")
        
        response = f"\n🏢 PORTFÖY YÖNETİM ŞİRKETLERİ GENEL BAKIŞ\n"
        response += f"{'='*50}\n\n"
        
        # Desteklenen şirketleri listele
        response += f"📊 DESTEKLENEN ŞİRKETLER:\n\n"
        
        for i, company in enumerate(self.portfolio_analyzer.company_keywords.keys(), 1):
            response += f"{i:2d}. {company}\n"
        
        response += f"\n💡 KULLANIM ÖRNEKLERİ:\n"
        response += f"   • 'İş Portföy analizi'\n"
        response += f"   • 'Ak Portföy vs Garanti Portföy karşılaştırması'\n"
        response += f"   • 'En başarılı portföy şirketi hangisi?'\n"
        response += f"   • 'QNB Portföy fonları nasıl?'\n\n"
        
        response += f"🎯 ÖZELLİKLER:\n"
        response += f"   ✅ Şirket bazında tüm fonları analiz\n"
        response += f"   ✅ Performans karşılaştırması\n"
        response += f"   ✅ Risk-getiri analizi\n"
        response += f"   ✅ Sharpe oranı hesaplama\n"
        response += f"   ✅ Kapsamlı raporlama\n\n"
        
        response += f"📈 EN BAŞARILI ŞİRKET İÇİN:\n"
        response += f"   'En başarılı portföy şirketi' sorusunu sorun!\n"
        
        return response

    def _handle_company_comparison_enhanced(self, question):
        """Gelişmiş şirket karşılaştırması"""
        # Sorudan şirket isimlerini çıkar
        companies = []
        question_upper = question.upper()
        
        for company, keywords in self.portfolio_analyzer.company_keywords.items():
            for keyword in keywords:
                if keyword in question_upper:
                    companies.append(company)
                    break
        
        # Tekrarları kaldır ve ilk 2'sini al
        companies = list(dict.fromkeys(companies))[:2]
        
        if len(companies) < 2:
            return f"❌ Karşılaştırma için 2 şirket gerekli. Örnek: 'İş Portföy vs Ak Portföy karşılaştırması'"
        
        return self.portfolio_analyzer.compare_companies_unlimited(companies[0], companies[1])

    def handle_company_comparison_enhanced(self, question):
        """Gelişmiş şirket karşılaştırması"""
        # Sorudan şirket isimlerini çıkar
        companies = []
        question_upper = question.upper()
        
        for company, keywords in self.portfolio_analyzer.company_keywords.items():
            for keyword in keywords:
                if keyword in question_upper:
                    companies.append(company)
                    break
        
        # Tekrarları kaldır ve ilk 2'sini al
        companies = list(dict.fromkeys(companies))[:2]
        
        if len(companies) < 2:
            return f"❌ Karşılaştırma için 2 şirket gerekli. Örnek: 'İş Portföy vs Ak Portföy karşılaştırması'"
        
        return self.portfolio_analyzer.compare_companies_unlimited(companies[0], companies[1])

    def _handle_technical_analysis_questions_full_db(self, question):
        """SQL tabanlı teknik analiz - Tüm veritabanını kullanır"""
        question_lower = question.lower()
        
        # MACD sinyali soruları
        if any(word in question_lower for word in ['macd', 'macd sinyali', 'macd pozitif', 'macd negatif']):
            return self.technical_analyzer.handle_macd_signals_sql(question)
        
        # Bollinger Bands soruları
        elif any(word in question_lower for word in ['bollinger', 'bollinger bantları', 'alt banda', 'üst banda']):
            return self.technical_analyzer.handle_bollinger_signals_sql(question)
        
        # RSI soruları
        elif any(word in question_lower for word in ['rsi', 'rsi düşük', 'rsi yüksek', 'aşırı satım', 'aşırı alım']):
            return self.technical_analyzer.handle_rsi_signals_sql(question)
        
        # Moving Average soruları
        elif any(word in question_lower for word in ['hareketli ortalama', 'moving average', 'sma', 'ema', 'golden cross', 'death cross']):
            return self.technical_analyzer.handle_moving_average_signals_sql(question)
        
        # Genel teknik sinyal soruları
        elif any(word in question_lower for word in ['teknik sinyal', 'alım sinyali', 'satım sinyali']):
            return self.technical_analyzer.handle_general_technical_signals_sql(question)
        
        else:
            return None

    def _handle_fund_category_question(self, question):
        words = question.upper().split()
        fund_code = None
        for word in words:
            if len(word) == 3 and word.isalpha():
                if word.upper() in [x.upper() for x in self.active_funds]:
                    fund_code = word.upper()
                    break
        if not fund_code:
            return "❌ Geçerli bir fon kodu tespit edilemedi."
        details = self.coordinator.db.get_fund_details(fund_code)
        if not details:
            return "❌ Fon detayı bulunamadı."
        category = details.get('fund_category', 'Bilinmiyor')
        fund_type = details.get('fund_type', 'Bilinmiyor')
        response = f"\n📑 {fund_code} FONU KATEGORİ BİLGİLERİ\n{'='*40}\n"
        response += f"Kategori: {category}\n"
        response += f"Tür: {fund_type}\n"
        return response

    def _handle_fund_allocation_question(self, question):
        # Soru içindeki fon kodunu bul
        import re
        words = question.upper().split()
        print("Kullanıcıdan gelen kelimeler:", words)
        print("Aktif fonlar:", self.active_funds)
        fund_code = None
        for word in words:
            if len(word) == 3 and word.isalpha():
                if word.upper() in [x.upper() for x in self.active_funds]:
                    fund_code = word.upper()
                    break
        # Eğer aktiflerde bulamazsan, tüm fon kodlarında dene
        if not fund_code:
            all_funds = [x.upper() for x in self.coordinator.db.get_all_fund_codes()]
            for word in words:
                if len(word) == 3 and word.isalpha():
                    if word.upper() in all_funds:
                        fund_code = word.upper()
                        break
        if not fund_code:
            return "❌ Geçerli bir fon kodu tespit edilemedi."
        details = self.coordinator.db.get_fund_details(fund_code)
        if not details:
            return "❌ Fon detayı bulunamadı."
        
        # --- Kolon anahtarlarının Türkçesi (dilersen ekle/güncelle) ---
        turkish_map = {
            "reverserepo": "Ters Repo",
            "foreignprivatesectordebtinstruments": "Yabancı Özel Sektör Borçlanması",
            "foreigninvestmentfundparticipationshares": "Yabancı Yatırım Fonu Katılma Payı",
            "governmentbondsandbillsfx": "Döviz Cinsi DİBS",
            "privatesectorforeigndebtinstruments": "Yabancı Özel Sektör Borçlanma Araçları",
            "stock": "Hisse Senedi",
            "governmentbond": "Devlet Tahvili",
            "precious_metals": "Kıymetli Madenler"
            # ... Diğerlerini ekleyebilirsin
        }

        # Öncelikle eski klasik yöntemle dene:
        allocation_keys = [
            'stock', 'governmentbond', 'eurobonds', 'bankbills', 'fxpayablebills',
            'commercialpaper', 'fundparticipationcertificate', 'realestateinvestmentfundparticipation', 'precious_metals',
            'reverserepo', 'foreignprivatesectordebtinstruments', 'foreigninvestmentfundparticipationshares',
            'governmentbondsandbillsfx', 'privatesectorforeigndebtinstruments'
        ]
        allocation = []
        for key in allocation_keys:
            val = details.get(key, 0)
            if isinstance(val, (int, float)) and val > 0:
                allocation.append((key, val))
            elif isinstance(val, str) and val.replace('.', '', 1).isdigit() and float(val) > 0:
                allocation.append((key, float(val)))
        # Eğer hala boşsa, otomatik tarama:
        if not allocation:
            allocation = []
            for k, v in details.items():
                if isinstance(v, (int, float)) and v > 0 and k not in ["idtefasfunddetails", "fcode", "fdate"]:
                    allocation.append((k, v))
                elif isinstance(v, str) and v.replace('.', '', 1).isdigit() and float(v) > 0 and k not in ["idtefasfunddetails", "fcode", "fdate"]:
                    allocation.append((k, float(v)))
        if not allocation:
            return f"❌ {fund_code} fonunun yatırım dağılımı verisi bulunamadı."
        
        # Yüzdelik tablo yap
        response = f"\n📊 {fund_code} FONU YATIRIM DAĞILIMI\n{'='*40}\n"
        response += "Varlık Türü                          | Yüzde (%)\n"
        response += "------------------------------------|-----------\n"
        for k, v in allocation:
            turkish = turkish_map.get(k, k)
            response += f"{turkish:<36} | {v:.2f}\n"
        response += "\nNot: Değerler doğrudan TEFAS veritabanından alınmıştır."
        return response
   
    def _handle_market_question_dual(self, question):
        """Piyasa durumu - Her iki AI ile"""
        print("📊 Dual AI piyasa durumu analiz ediliyor...")
        
        try:
            # Son 10 günün verilerini analiz et
            market_data = []
            
            for fcode in self.active_funds[:20]:
                try:
                    data = self.coordinator.db.get_fund_price_history(fcode, 10)
                    if not data.empty:
                        prices = data['price']
                        recent_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                        market_data.append(recent_return)
                except:
                    continue
            
            if market_data:
                avg_return = np.mean(market_data)
                positive_funds = sum(1 for r in market_data if r > 0)
                total_funds = len(market_data)
                
                response = f"\n📈 DUAL AI PİYASA DURUMU RAPORU\n"
                response += f"{'='*35}\n\n"
                
                response += f"📊 SON 10 GÜN VERİLERİ:\n"
                response += f"   Analiz Edilen Fon: {total_funds}\n"
                response += f"   Ortalama Getiri: %{avg_return:.2f}\n"
                response += f"   Pozitif Performans: {positive_funds}/{total_funds} (%{positive_funds/total_funds*100:.1f})\n\n"
                
                # Piyasa durumu
                if avg_return > 2:
                    mood = "🟢 ÇOK POZİTİF"
                elif avg_return > 0:
                    mood = "🟡 POZİTİF"
                elif avg_return > -2:
                    mood = "🟠 NÖTR"
                else:
                    mood = "🔴 NEGATİF"
                
                response += f"🌡️ PİYASA DUYARLILIĞI: {mood}\n\n"
                
                # AI yorumları
                market_prompt = f"""
                TEFAS piyasa durumu:
                
                Son 10 gün ortalama getiri: %{avg_return:.2f}
                Pozitif performans oranı: %{positive_funds/total_funds*100:.1f}
                Analiz edilen fon sayısı: {total_funds}
                Piyasa durumu: {mood}
                
                Bu verilere dayanarak piyasa durumu ve yatırımcı önerileri hakkında kısa yorum yap.
                """
                                # YENİ KOD:
                response += f"\n🤖 AI PİYASA YORUMU:\n"
                response += f"{'='*30}\n"

                try:
                    ai_market_analysis = self.ai_provider.query(
                        market_prompt,
                        "Sen piyasa analisti uzmanısın."
                    )
                    response += ai_market_analysis
                    return response
                except Exception as e:
                    response += "❌ AI piyasa analizi alınamadı\n"                

        except Exception as e:
            return f"❌ Piyasa analizi hatası: {e}"
    
    def _handle_ai_test_question(self, question):
        """AI test soruları"""
        response = f"\n🧪 AI SİSTEMLERİ TEST RAPORU\n"
        response += f"{'='*30}\n\n"
        
        # Provider status
        status = self.ai_provider.get_status()
        
        response += f"📊 DURUM RAPORU:\n"
        response += f"   📋 Provider Tipi: {status['provider_type'].upper()}\n"
        response += f"   ✅ Hazır: {'Evet' if status['is_available'] else 'Hayır'}\n"
        response += f"   🔄 Fallback: {'Aktif' if status['fallback_enabled'] else 'Kapalı'}\n\n"
        
        # Test prompt'u
        test_prompt = "TEFAS fonları hakkında 2 cümlelik kısa bilgi ver."
        
        response += f"🧪 TEST SONUCU:\n"
        
        try:
            test_result = self.ai_provider.query(test_prompt)
            response += f"✅ AI Testi Başarılı\n"
            response += f"Yanıt: {test_result[:100]}...\n"
        except Exception as e:
            response += f"❌ AI Testi Başarısız: {str(e)[:50]}\n"
        
        return response        
    
    def _handle_risk_question(self, question):
        """Risk soruları (önceki kodla aynı)"""
        response = f"\n🛡️ RİSK ANALİZİ VE GÜVENLİ YATIRIM\n"
        response += f"{'='*35}\n\n"
        
        # Düşük riskli fonları bul
        low_risk_funds = []
        
        for fcode in self.active_funds[:15]:
            try:
                data = self.coordinator.db.get_fund_price_history(fcode, 60)
                if not data.empty:
                    returns = data['price'].pct_change().dropna()
                    volatility = returns.std() * 100
                    
                    if volatility < 15:  # %15'ten düşük volatilite
                        low_risk_funds.append({
                            'fund': fcode,
                            'volatility': volatility,
                            'return': (data['price'].iloc[-1] / data['price'].iloc[0] - 1) * 100
                        })
            except:
                continue
        
        if low_risk_funds:
            df = pd.DataFrame(low_risk_funds).sort_values('volatility')
            
            response += f"🛡️ DÜŞÜK RİSKLİ FONLAR:\n"
            for _, fund in df.head(5).iterrows():
                response += f"   {fund['fund']}: Risk %{fund['volatility']:.1f}, Getiri %{fund['return']:.1f}\n"
        
        response += f"\n📋 RİSK YÖNETİMİ PRİNSİPLERİ:\n"
        response += f"   • Portföyünüzü diversifiye edin\n"
        response += f"   • Risk toleransınızı bilin\n"
        response += f"   • Acil fon ayırın (6-12 aylık gider)\n"
        response += f"   • Düzenli olarak rebalancing yapın\n"
        response += f"   • Uzun vadeli düşünün\n"
        
        return response
    
    def _handle_general_question(self, question):
        """Genel sorular"""
        response = f"\n❓ DUAL AI TEFAS ANALİZ SİSTEMİ\n"
        response += f"{'='*35}\n\n"
        
        response += f"🤖 SİSTEM DURUMU:\n"
        response += f"   📱 OpenAI: {'✅ Aktif' if self.ai_status['openai'] else '❌ İnaktif'}\n"
        response += f"   📊 Aktif Fonlar: {len(self.active_funds)}\n"
        response += f"   🗄️ Veritabanı: ✅ Bağlı\n\n"
        
        response += f"📋 AI SORU TİPLERİ:\n"
        response += f"   • '2025 için hangi fonları önerirsin?'\n"
        response += f"   • 'AKB fonunu analiz et'\n"
        response += f"   • 'Piyasa durumu nasıl?' \n"
        response += f"   • 'AI test' (AI sistemlerini test et)\n"
        response += f"   • 'AKB ve YAS karşılaştır'\n"
        response += f"   • 'Güvenli fonlar neler?'\n\n"
        
        response += f"\n🔬 İLERİ ANALİZ SORULARI:\n"
        response += f"   • 'Beta katsayısı 1'den düşük fonlar'\n"
        response += f"   • 'Alpha değeri pozitif olan fonlar'\n"
        response += f"   • 'Tracking error en düşük index fonlar'\n"
        response += f"   • 'Information ratio en yüksek aktif fonlar'\n"        
        return response

    def run_interactive_session(self):
        """İnteraktif AI oturumu"""
        print("\n" + "="*60)
        print("🤖 TEFAS AI ANALYSIS SYSTEM")
        print("="*60)
        print("🎯 Özellik:  AI OpenAI yanıt verir!")
        print("\n💡 Örnek sorular:")
        print("   • '2025 için 100000 TL ile hangi fonları önerirsin?'")
        print("   • 'AKB fonunu analiz et'")
        print("   • 'Piyasa durumu nasıl?'")
        print("   • 'AI test' (AI sistemlerini test et)")
        print("   • 'AKB ve YAS karşılaştır'")
        print("\n💬 Sorunuzu yazın (çıkmak için 'exit' yazın):")
        print("-" * 60)
        
        while True:
            try:
                question = input("\n🔍 Dual AI Soru: ").strip()
                
                if question.lower() in ['exit', 'çıkış', 'quit', 'q']:
                    print("\n👋 Dual AI Session sona erdi!")
                    break
                
                if not question:
                    continue
                
                print(f"\n🔄 Dual AI işleniyor...")
                answer = self.answer_question(question)
                print(answer)
                
                print("\n" + "-" * 60)
                
            except KeyboardInterrupt:
                print("\n\n👋 Dual AI Session sona erdi!")
                break
            except Exception as e:
                print(f"\n❌ Hata oluştu: {e}")
                continue



def main():
    """Ana fonksiyon"""
    try:
        # Dual AI Q&A sistemini başlat
        qa_system = DualAITefasQA()
        
        # Test modunu kontrol et
        if len(sys.argv) > 1:
            if sys.argv[1] == "--test":
                # AI test modu
                print(qa_system._handle_ai_test_question("AI test"))
            elif sys.argv[1] == "--demo":
                # Demo sorular
                demo_questions = [
                    "2025 için 50000 TL ile hangi fonları önerirsin?",
                    "AI test",
                    "Piyasa durumu nasıl?"
                ]
                
                for i, question in enumerate(demo_questions, 1):
                    print(f"\n[DEMO {i}] {question}")
                    print("-" * 40)
                    answer = qa_system.answer_question(question)
                    # İlk 500 karakter göster
                    preview = answer[:500] + "..." if len(answer) > 500 else answer
                    print(preview)
                    if i < len(demo_questions):
                        input("\nDevam etmek için Enter'a basın...")
            else:
                # Tek soru modu
                question = " ".join(sys.argv[1:])
                answer = qa_system.answer_question(question)
                print(answer)
        else:
            # İnteraktif mod
            qa_system.run_interactive_session()
            
    except Exception as e:
        print(f"❌ Dual AI sistem başlatma hatası: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()