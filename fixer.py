# test_hybrid_router.py
"""
Hybrid Router test script - Tam versiyon
"""
import sys
sys.path.append('C:/Projects/Personal/AI/financeNew')

from handler_registry import HandlerRegistry
from hybrid_smart_router import HybridSmartRouter
import time

def initialize_test_router(use_sbert=False, debug=False):
    """Test için router'ı initialize et"""
    
    print("🚀 Test Router başlatılıyor...")
    
    # Registry oluştur
    registry = HandlerRegistry()
    
    # Handler'ları import et ve register et
    handlers_to_register = [
        ('performance_analysis', 'PerformanceAnalyzerMain', 'performance_analyzer'),
        ('technical_analysis', 'TechnicalAnalysis', 'technical_analyzer'),
        ('currency_inflation_analyzer', 'CurrencyInflationAnalyzer', 'currency_inflation_analyzer'),
        ('scenario_analysis', 'ScenarioAnalyzer', 'scenario_analyzer'),
        ('personal_finance_analyzer', 'PersonalFinanceAnalyzer', 'personal_finance_analyzer'),
        ('mathematical_calculations', 'MathematicalCalculator', 'mathematical_calculator'),
        ('portfolio_company_analysis', 'EnhancedPortfolioCompanyAnalyzer', 'portfolio_company_analyzer'),
        ('time_based_analyzer', 'TimeBasedAnalyzer', 'time_based_analyzer'),
        ('macroeconomic_analyzer', 'MacroeconomicAnalyzer', 'macroeconomic_analyzer'),
        ('advanced_metrics_analyzer', 'AdvancedMetricsAnalyzer', 'advanced_metrics_analyzer'),
        ('thematic_fund_analyzer', 'ThematicFundAnalyzer', 'thematic_analyzer'),
        ('fundamental_analysis', 'FundamentalAnalysisEnhancement', 'fundamental_analyzer')
    ]
    
    for module_name, class_name, handler_name in handlers_to_register:
        try:
            # Dinamik import
            module = __import__(module_name, fromlist=[class_name])
            handler_class = getattr(module, class_name)
            registry.register(handler_class, handler_name)
            print(f"✅ {handler_name} registered")
        except Exception as e:
            print(f"❌ {handler_name}: {e}")
    
    print(f"\n📊 Toplam {len(registry.registry)} handler registered")
    
    # Router oluştur
    router = HybridSmartRouter(registry, ai_provider=None, use_sbert=use_sbert)
    
    return router, registry

def run_test_suite():
    """Ana test suite"""
    
    print("🧪 Hybrid Router Test Suite")
    print("="*60)
    
    # Router'ı initialize et
    router, registry = initialize_test_router(use_sbert=False)
    
    # Test case'leri tanımla
    test_cases = [
        # (Soru, Beklenen Handler, Beklenen Method veya None)
        ("En güvenli 5 fon hangileri?", "performance_analyzer", "handle_safest_funds_sql_fast"),
        ("Beta katsayısı 1'den düşük fonlar", "advanced_metrics_analyzer", "handle_beta_analysis"),
        ("İş Portföy fonları nasıl performans gösteriyor?", "portfolio_company_analyzer", "analyze_company_comprehensive"),
        ("100000 TL'yi 3 fona nasıl dağıtmalıyım?", "mathematical_calculator", "handle_portfolio_distribution"),
        ("MACD sinyali pozitif olan fonlar", "technical_analyzer", "handle_macd_signals_sql"),
        ("Emekliliğe 10 yıl kala nasıl yatırım yapmalıyım?", "personal_finance_analyzer", "handle_retirement_planning"),
        ("Dolar fonlarının bu ayki performansı", "currency_inflation_analyzer", None),
        ("Enflasyon %50 olursa hangi fonlara yatırım yapmalıyım?", "scenario_analyzer", "analyze_inflation_scenario"),
        ("Bugün en çok kazanan fonlar", "time_based_analyzer", None),
        ("RSI 30'un altında olan fonlar", "technical_analyzer", "handle_rsi_signals_sql"),
        ("Faiz artışı fonları nasıl etkiler?", "macroeconomic_analyzer", "analyze_interest_rate_impact"),
        ("Teknoloji sektörü fonları", "thematic_analyzer", "analyze_thematic_question"),
        ("En büyük 10 fon hangileri?", "fundamental_analyzer", "handle_largest_funds_questions"),
        ("Sharpe oranı 0.5'ten yüksek fonlar", "advanced_metrics_analyzer", "handle_sharpe_ratio_analysis"),
        ("Son 30 gün en iyi performans gösteren fonlar", "performance_analyzer", "handle_top_gainers"),
    ]
    
    # İstatistikler
    success_count = 0
    failed_tests = []
    start_time = time.time()
    
    # Test döngüsü
    for i, (question, expected_handler, expected_method) in enumerate(test_cases, 1):
        print(f"\n[Test {i}/{len(test_cases)}]")
        print(f"❓ Soru: {question}")
        
        try:
            # Route bul
            route = router.route(question, threshold=0.3)
            
            if route:
                # Handler kontrolü
                handler_correct = route.handler == expected_handler
                
                # Method kontrolü (None ise herhangi bir method kabul edilir)
                method_correct = expected_method is None or route.method == expected_method
                
                if handler_correct and method_correct:
                    print(f"✅ BAŞARILI!")
                    print(f"   Handler: {route.handler}.{route.method}")
                    print(f"   Confidence: {route.confidence:.2f}")
                    print(f"   Match Type: {route.match_type}")
                    print(f"   Reasoning: {route.reasoning}")
                    success_count += 1
                else:
                    print(f"❌ BAŞARISIZ!")
                    print(f"   Beklenen: {expected_handler}.{expected_method or '*'}")
                    print(f"   Bulunan: {route.handler}.{route.method}")
                    failed_tests.append((i, question, expected_handler, route.handler))
            else:
                print(f"❌ Route bulunamadı!")
                failed_tests.append((i, question, expected_handler, "None"))
                
        except Exception as e:
            print(f"❌ HATA: {str(e)}")
            import traceback
            traceback.print_exc()
            failed_tests.append((i, question, expected_handler, f"Error: {str(e)}"))
        
        print("-"*60)
    
    # Test süresi
    end_time = time.time()
    total_time = end_time - start_time
    
    # Sonuç raporu
    print(f"\n{'='*60}")
    print(f"📊 TEST SONUÇLARI")
    print(f"{'='*60}")
    print(f"✅ Başarılı: {success_count}/{len(test_cases)}")
    print(f"❌ Başarısız: {len(failed_tests)}/{len(test_cases)}")
    print(f"🎯 Başarı Oranı: %{(success_count/len(test_cases)*100):.1f}")
    print(f"⏱️ Toplam Süre: {total_time:.1f} saniye")
    print(f"⚡ Ortalama: {(total_time/len(test_cases)*1000):.0f} ms/sorgu")
    
    # Başarısız testlerin detayları
    if failed_tests:
        print(f"\n❌ BAŞARISIZ TESTLER:")
        for test_no, question, expected, actual in failed_tests:
            print(f"   Test {test_no}: {question[:50]}...")
            print(f"      Beklenen: {expected}")
            print(f"      Bulunan: {actual}")
    
    return success_count, failed_tests, test_cases

def test_sbert_improvement():
    """SBERT ile iyileştirme testi"""
    print(f"\n\n🧠 SBERT İLE TEST:")
    print("="*60)
    
    try:
        # SBERT açık router
        router_sbert, _ = initialize_test_router(use_sbert=True)
        print("✅ SBERT başarıyla yüklendi")
        
        # Örnek sorular için test
        test_questions = [
            "Dolar fonlarının bu ayki performansı",
            "Bugün en çok kazanan fonlar",
            "Son 30 gün en iyi performans gösteren fonlar",
            "En güvenilir yatırım araçları",  # "güvenli" yerine "güvenilir"
            "Hangi fonlar daha az riskli?",   # Farklı ifade
        ]
        
        print("\n📊 SBERT Benzerlik Testleri:")
        for question in test_questions:
            route = router_sbert.route(question, threshold=0.3)
            if route:
                print(f"\n❓ '{question}'")
                print(f"   → {route.handler}.{route.method}")
                print(f"   Score: {route.confidence:.2f} ({route.match_type})")
    
    except Exception as e:
        print(f"❌ SBERT test edilemedi: {e}")

def test_edge_cases():
    """Edge case testleri"""
    print(f"\n\n🔍 EDGE CASE TESTLERİ:")
    print("="*60)
    
    router, _ = initialize_test_router(use_sbert=False)
    
    edge_cases = [
        # Çok kısa sorular
        "AKB",
        "Dolar?",
        
        # Yazım hataları
        "En güvenli fonalr",
        "Sharpe orani yüksek fonlar",
        
        # Karmaşık sorular
        "Hem güvenli hem de yüksek getirili dolar bazlı teknoloji fonları",
        "2025 yılı için emekliliğe 10 yıl kala beta katsayısı düşük fonlar",
        
        # Anlamsız/ilgisiz sorular
        "Merhaba",
        "Test test 123",
        "asdfgh"
    ]
    
    for question in edge_cases:
        print(f"\n❓ '{question}'")
        route = router.route(question, threshold=0.2)  # Düşük threshold
        if route:
            print(f"   → {route.handler}.{route.method} (Score: {route.confidence:.2f})")
        else:
            print(f"   → Route bulunamadı")

def main():
    """Ana test fonksiyonu"""
    # Ana test suite
    success_count, failed_tests, test_cases = run_test_suite()
    
    # SBERT testi (opsiyonel)
    test_sbert_improvement()
    
    # Edge case testi
    test_edge_cases()
    
    # Özet
    print(f"\n\n📊 GENEL ÖZET:")
    print(f"{'='*60}")
    print(f"✅ Toplam başarı: {success_count}/{len(test_cases)} (%{(success_count/len(test_cases)*100):.1f})")
    
    if success_count == len(test_cases):
        print("🎉 TÜM TESTLER BAŞARILI!")
    else:
        print(f"⚠️ {len(failed_tests)} test başarısız.")
        print("\nÖneriler:")
        print("1. Başarısız testler için handler pattern'lerini kontrol edin")
        print("2. Pattern score'larını ayarlayın")
        print("3. SBERT kullanımını değerlendirin")

if __name__ == "__main__":
    main()