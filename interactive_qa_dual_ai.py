# interactive_qa_dual_ai.py
"""
TEFAS Analysis System - Dual AI Q&A (OpenAI vs Ollama)
Her iki AI'ın da yanıt vermesi için güncellenmiş versiyon
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
from smart_question_router import SmartQuestionRouter
from response_merger import ResponseMerger
from ai_provider import AIProvider
from ai_smart_question_router import AISmartQuestionRouter
from predictive_scenario_analyzer import PredictiveScenarioAnalyzer
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
    """TEFAS Soru-Cevap Sistemi - OpenAI ve Ollama karşılaştırmalı"""
    
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
            'openai': self.ai_provider.get_status()['openai_status'],
            'ollama': self.ai_provider.get_status()['ollama_status']
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
        self.router = SmartQuestionRouter()
        self.response_merger = ResponseMerger()
        self.enable_multi_handler = True  # Feature flag
        self.ai_router = AISmartQuestionRouter(self.ai_provider)
        self.use_ai_routing = True
        from initialize_hybrid_router import initialize_hybrid_router
        self.hybrid_router, self.handler_registry = initialize_hybrid_router(
            ai_provider=self.ai_provider,
            use_sbert=True  # SBERT'i etkinleştir
        )
        from ai_personalized_advisor import AIPersonalizedAdvisor
        self.ai_advisor = AIPersonalizedAdvisor(self.coordinator, self.ai_provider)        
        # Feature flags
        self.use_hybrid_routing = True  # Yeni routing sistemini kullan
        self.enable_multi_handler = True
        self.predictive_analyzer = PredictiveScenarioAnalyzer(
            self.coordinator,
            self.scenario_analyzer
        )        

                # Makroekonomik analyzer'ı oluştur - HATA KONTROLÜ İLE
        try:
            print("📊 Makroekonomik analyzer yükleniyor...")
            self.macro_analyzer = MacroeconomicAnalyzer(self.coordinator.db, self.config, self.coordinator)
            print("✅ Makroekonomik analyzer yüklendi")
        except Exception as e:
            print(f"❌ Makroekonomik analyzer yüklenemedi: {e}")
            self.macro_analyzer = None

        # AI durumunu kontrol et
        
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
            'openai': provider_status['openai_status'],
            'ollama': provider_status['ollama_status']
        }
        
        print(f"   📱 OpenAI: {'✅ Hazır' if ai_status['openai'] else '❌ Mevcut değil'}")
        print(f"   🦙 Ollama: {'✅ Hazır' if ai_status['ollama'] else '❌ Mevcut değil'}")
        
        if provider_status['provider_type'] == 'dual' and ai_status['openai'] and ai_status['ollama']:
            print("   🎯 Dual mode aktif - Karşılaştırmalı analiz mevcut!")
        elif ai_status['openai']:
            print("   🎯 Sadece OpenAI aktif")
        elif ai_status['ollama']:
            print("   🎯 Sadece Ollama aktif")
        else:
            print("   ⚠️ Hiçbir AI sistemi aktif değil")
        
        return ai_status
    

    def answer_question(self, question):
        """Multi-handler desteği ile soru cevaplama"""
        question_lower = normalize_turkish_text(question)
        # 🚀 ÖNCELİKLİ KONTROL - AI PATTERN
        if any(word in question_lower for word in ['ai pattern', 'ai teknik', 'pattern analiz', 
                                                'ai sinyal', 'yapay zeka teknik']):
            print("🎯 AI Pattern Analysis'e direkt yönlendiriliyor")
            return self.technical_analyzer.handle_ai_pattern_analysis(question)        
        if self.use_ai_routing:
            # AI destekli routing
            try:
                route_results = self.ai_router.route_question_multi(question)
                
                if route_results:
                    print(f"AI Routing: {len(route_results)} handler bulundu")
                    for route in route_results:
                        print(f"  - {route.handler}.{route.method} (confidence: {route.confidence:.2f})")
                    
                    # Multi-handler execution
                    responses = self._execute_multi_handlers(route_results, question, question_lower)
                    
                    if responses:
                        return self.response_merger.merge_responses(responses, question)
            
            except Exception as e:
                print(f"AI routing hatası, fallback kullanılıyor: {e}")
        
        if any(word in question_lower for word in ['kişisel plan', 'bana özel', 'profilime göre', 
                                                    'yaşındayım', 'gelirim', 'kişiye özel']):
            return self.ai_advisor.analyze_from_question(question)
       # Fallback: Legacy routing
        numbers_in_question = re.findall(r'(\d+)', question)
        requested_count = int(numbers_in_question[0]) if numbers else 1
        return self._legacy_routing(question, question_lower, requested_count)

    def _execute_multi_handlers(self, routes: List[RouteMatch], question: str, question_lower: str) -> List[Dict]:
        """Birden fazla handler'ı çalıştır"""
        responses = []
        executed_handlers = set()  # Aynı handler'ı iki kez çalıştırma

        print(f"[EXEC] Total routes: {len(routes)}")
        for route in routes:
            print(f"[EXEC] Route: {route.handler}.{route.method}, Context: {route.context}")
        for route in routes:
            handler_name = route.handler
            
            # Aynı handler'ı tekrar çalıştırma
            if handler_name in executed_handlers:
                continue
                
            # Handler'ı bul
            handler = self._get_handler_instance(handler_name)
            if not handler:
                continue
            
            try:
                # Method'u çalıştır
                method = getattr(handler, route.method, None)
                if method:
                    # Context'ten parametreleri hazırla
                    params = {'question': question}
                    
                    # Context'ten gelen parametreleri ekle
                    if route.context.get('requested_count'):
                        params['count'] = route.context['requested_count']

                    print(f"[EXEC] Calling {handler_name}.{route.method} with params: {params}")

                    if route.context.get('days'):
                        params['days'] = route.context['days']
                    
                    if route.context.get('currency'):
                        params['currency'] = route.context['currency']
                    
                    # Method signature kontrolü (basit versiyon)
                    import inspect
                    sig = inspect.signature(method)
                    valid_params = {}
                    for param_name, param_value in params.items():
                        if param_name in sig.parameters:
                            valid_params[param_name] = param_value
                    print(f"[EXEC] Valid params after signature check: {valid_params}")


                    # Handler'ı çalıştır
                    result = method(**valid_params)
                    
                    if result:
                        responses.append({
                            'handler': handler_name,
                            'response': result,
                            'score': route.score,
                            'context': route.context
                        })
                        executed_handlers.add(handler_name)
                        
            except Exception as e:
                print(f"[EXEC] Handler execution error ({handler_name}): {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return responses

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
            'predictive_analyzer': self.predictive_analyzer
        }
        return handler_map.get(handler_name)
    
    def _prepare_handler_params(self, route: RouteMatch, question: str, question_lower: str) -> Dict:
        """Handler için parametreleri hazırla"""
        params = {'question': question}
        
        # Context'ten parametreleri al
        if 'requested_count' in route.context:
            params['count'] = route.context['requested_count']
            params['requested_count'] = route.context['requested_count']
        
        if 'days' in route.context:
            params['days'] = route.context['days']
        
        if 'currency' in route.context:
            params['currency'] = route.context['currency']
        
        # Method signature'a göre filtrele
        # (Gerçek implementasyonda method signature kontrolü yapılmalı)
        
        return params

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
    #         if requested_count > 1 or 'fonlar' in question_lower:
    #             return self.performanceMain.handle_riskiest_funds_list(requested_count)
    #         else:
    #             return self.performanceMain.handle_most_risky_fund()
        
    #     # EN ÇOK KAYBETTİREN - ÇOKLU LİSTE DESTEĞİ
    #     if any(word in question_lower for word in ['en çok kaybettiren', 'en çok düşen']):
    #         if requested_count > 1 or 'fonlar' in question_lower:
    #             return self.performanceMain.handle_worst_funds_list(requested_count)
    #         else:
    #             return self.performanceMain.handle_worst_fund()        
    #     # Özel risk sorusu yakalama
    #     if "en riskli" in question_lower:
    #         return self.performanceMain.handle_most_risky_fund()
    #     if "en güvenli" in question_lower or "en az riskli" in question_lower:
    #         return self.performanceMain.handle_safest_fund()
    #     if "en çok kaybettiren" in question_lower or "en çok düşen" in question_lower:
    #         return self.performanceMain.handle_worst_fund()

    #     if any(word in question_lower for word in ['portföy', 'portfolio']):
            
    #         # Belirli şirket kapsamlı analizi
    #         if any(word in question_lower for word in ['iş portföy', 'is portfoy', 'işbank portföy']):
    #             return self.portfolio_analyzer.analyze_company_comprehensive('İş Portföy')
            
    #         elif any(word in question_lower for word in ['ak portföy', 'akbank portföy']):
    #             return self.portfolio_analyzer.analyze_company_comprehensive('Ak Portföy')
            
    #         elif any(word in question_lower for word in ['garanti portföy', 'garantibank portföy']):
    #             return self.portfolio_analyzer.analyze_company_comprehensive('Garanti Portföy')
            
    #         elif any(word in question_lower for word in ['ata portföy']):
    #             return self.portfolio_analyzer.analyze_company_comprehensive('Ata Portföy')
            
    #         elif any(word in question_lower for word in ['qnb portföy']):
    #             return self.portfolio_analyzer.analyze_company_comprehensive('QNB Portföy')
            
    #         elif any(word in question_lower for word in ['fiba portföy', 'fibabank portföy']):
    #             return self.portfolio_analyzer.analyze_company_comprehensive('Fiba Portföy')
            
    #         # Şirket karşılaştırması
    #         elif any(word in question_lower for word in ['vs', 'karşı', 'karşılaştır', 'compare']):
    #             return self._handle_company_comparison_enhanced(question)
            
    #         # En başarılı şirket
    #         elif any(word in question_lower for word in ['en başarılı', 'en iyi', 'best', 'most successful']):
    #             return self.portfolio_analyzer.find_best_portfolio_company_unlimited()
            
    #         else:
    #             return self._handle_portfolio_companies_overview(question)     
            
    #     elif any(word in question_lower for word in ['beta katsayısı', 'beta değeri', 'beta 1', 
    #                                                     'beta düşük', 'beta yüksek', 'beta altında','beta katsayisi', 'beta degeri', 'beta coefficient', 
    #                                         'beta 1', 'beta dusuk', 'beta yuksek', 'beta altinda',
    #                                         'beta less than', 'beta greater than']):
    #         return self.advanced_metrics_analyzer.handle_beta_analysis(question)
            
    #     elif any(word in question_lower for word in ['alpha değeri', 'alpha pozitif', 'jensen alpha', 
    #                                                     'alpha negatif', 'alfa değeri', 'alfa pozitif']):
    #         return self.advanced_metrics_analyzer.handle_alpha_analysis(question)
            
    #     elif any(word in question_lower for word in ['tracking error', 'takip hatası', 'index fon tracking',
    #                                                     'endeks fon tracking', 'tracking error düşük']):
    #         return self.advanced_metrics_analyzer.handle_tracking_error_analysis(question)
            
    #     elif any(word in question_lower for word in ['information ratio', 'bilgi oranı', 'ir yüksek',
    #                                                     'information ratio yüksek', 'aktif fon ir']):
    #         return self.advanced_metrics_analyzer.handle_information_ratio_analysis(question)
       
    #     # 📈 TEMATİK FON SORULARI - TÜM VERİTABANI 
    #     if self.thematic_analyzer.is_thematic_question(question):
    #         return self.thematic_analyzer.analyze_thematic_question(question)
    #            # FUNDAMENTAL ANALİZ SORULARI 🆕
    #     if any(word in question_lower for word in ['kapasite', 'büyüklük', 'büyük fon']):
    #         return self.fundamental_analyzer.handle_capacity_questions(question)
        
    #     if any(word in question_lower for word in ['yatırımcı sayısı', 'popüler fon']):
    #         return self.fundamental_analyzer.handle_investor_count_questions(question)
        
    #     if any(word in question_lower for word in ['yeni fon', 'yeni kurulan']):
    #         return self.fundamental_analyzer.handle_new_funds_questions(question)
        
    #     if any(word in question_lower for word in ['en büyük', 'largest']):
    #         return self.fundamental_analyzer.handle_largest_funds_questions(question)
        
    #     if any(word in question_lower for word in ['en eski', 'köklü']):
    #         return self.fundamental_analyzer.handle_fund_age_questions(question)
        
    #     if any(word in question_lower for word in ['kategori', 'tür']):
    #         return self.fundamental_analyzer.handle_fund_category_questions(question)        
    #     # --- Gelişmiş anahtar kelime tabanlı analizler ---
    #     if any(word in question_lower for word in ['yatırım dağılımı', 'varlık dağılımı', 'kompozisyon', 'içerik', 'portföy içerik']):
    #         return self._handle_fund_allocation_question(question)
    #     if 'fon kategorisi' in question_lower or 'fon türü' in question_lower:
    #         return self._handle_fund_category_question(question)
    #     if any(word in question_lower for word in ['kazanç', 'getiri', 'son 1 yıl', 'son 12 ay', 'geçtiğimiz yıl', 'son yıl']):
    #         return self.performanceMain.handle_fund_past_performance_question(question)
    #     if any(word in question_lower for word in ['en çok kazandıran', 'en çok getiri']):
    #         return self.performanceMain.handle_top_gainer_fund_question(question)
    #     if 'en çok kazandıran' in question_lower or 'en çok getiri' in question_lower:
    #         return self.performanceMain.handle_top_gainer_fund_question(question)
    #     if 'düşüşte olan fonlar' in question_lower or 'en çok kaybettiren' in question_lower:
    #         return self.performanceMain.handle_top_loser_fund_question(question)
    #     if 'sharpe oranı en yüksek' in question_lower:
    #         return self.performanceMain.handle_top_sharpe_funds_question(question)
    #     if 'volatilite' in question_lower and 'altında' in question_lower:
    #         return self.performanceMain.handle_low_volatility_funds_question(question)
    #     # --- mevcut kalan kodun ---
    #     if any(word in question_lower for word in ['2025', 'öneri', 'öner', 'recommend', 'suggest']):
    #         return self.performanceMain.handle_2025_recommendation_dual(question)
    #     elif any(word in question_lower for word in ['analiz', 'analyze', 'performance']):
    #         return self.performanceMain.handle_analysis_question_dual(question)
    #     elif any(word in question_lower for word in ['karşılaştır', 'compare', 'vs']):
    #         return self.performanceMain.handle_comparison_question(question)
    #     elif any(word in question_lower for word in ['risk', 'güvenli', 'safe']):
    #         return self._handle_risk_question(question)
    #     elif any(word in question_lower for word in ['piyasa', 'market', 'durum']):
    #         return self._handle_market_question_dual(question)
    #     elif any(word in question_lower for word in ['macd', 'bollinger', 'rsi', 'hareketli ortalama', 
    #                                                 'moving average', 'sma', 'ema', 'teknik sinyal',
    #                                                 'alım sinyali', 'satım sinyali', 'aşırı satım',
    #                                                 'aşırı alım', 'golden cross', 'death cross']):
    #         technical_result = self._handle_technical_analysis_questions_full_db(question)
    #         if technical_result:
    #             return technical_result
    #         else:
    #             return self._handle_general_question(question)
    #     elif any(word in question_lower for word in ['ai', 'yapay zeka', 'test']):
    #         return self._handle_ai_test_question(question)
    #     else:
    #         return self._handle_general_question(question)

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
        response += f"   🦙 Ollama: {'✅ Aktif' if self.ai_status['ollama'] else '❌ İnaktif'}\n"
        response += f"   📊 Aktif Fonlar: {len(self.active_funds)}\n"
        response += f"   🗄️ Veritabanı: ✅ Bağlı\n\n"
        
        response += f"📋 DUAL AI SORU TİPLERİ:\n"
        response += f"   • '2025 için hangi fonları önerirsin?' (Her iki AI de yanıt verir)\n"
        response += f"   • 'AKB fonunu analiz et' (Dual AI değerlendirme)\n"
        response += f"   • 'Piyasa durumu nasıl?' (İkili AI yorumu)\n"
        response += f"   • 'AI test' (AI sistemlerini test et)\n"
        response += f"   • 'AKB ve YAS karşılaştır'\n"
        response += f"   • 'Güvenli fonlar neler?'\n\n"
        
        response += f"🎯 DUAL AI AVANTAJLARI:\n"
        response += f"   • OpenAI ve Ollama karşılaştırması\n"
        response += f"   • Farklı AI perspektifleri\n"
        response += f"   • Daha kapsamlı analiz\n"
        response += f"   • AI performans değerlendirmesi\n"
        response += f"\n🔬 İLERİ ANALİZ SORULARI:\n"
        response += f"   • 'Beta katsayısı 1'den düşük fonlar'\n"
        response += f"   • 'Alpha değeri pozitif olan fonlar'\n"
        response += f"   • 'Tracking error en düşük index fonlar'\n"
        response += f"   • 'Information ratio en yüksek aktif fonlar'\n"        
        return response

    def run_interactive_session(self):
        """İnteraktif dual AI oturumu"""
        print("\n" + "="*60)
        print("🤖 TEFAS DUAL AI ANALYSIS SYSTEM")
        print("="*60)
        print("🎯 Özellik: Her iki AI (OpenAI + Ollama) aynı anda yanıt verir!")
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