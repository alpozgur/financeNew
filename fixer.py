# comprehensive_router_test.py
from ai_smart_question_router import AISmartQuestionRouter
from config.config import Config
from analysis.coordinator import AnalysisCoordinator

# Setup
config = Config()
coordinator = AnalysisCoordinator(config)
router = AISmartQuestionRouter(coordinator.ai_provider)

# Test soruları ve beklenen context'ler
test_cases = [
    {
        "question": "En güvenli 5 fon hangileri?",
        "expected_context": {"requested_count": 5},
        "expected_handler": "performance_analyzer"
    },
    {
        "question": "Beta katsayısı 1'den düşük fonlar",
        "expected_context": {"beta_threshold": 1.0, "max_threshold": 1.0},
        "expected_handler": "advanced_metrics_analyzer"
    },
    {
        "question": "Enflasyon %50 olursa hangi fonlara yatırım yapmalıyım?",
        "expected_context": {"percentage": 50.0},
        "expected_handler": "scenario_analyzer"
    },
    {
        "question": "Son 30 gün en iyi performans gösteren fonlar",
        "expected_context": {"days": 30},
        "expected_handler": "performance_analyzer"
    },
    {
        "question": "Dolar fonlarının bu ayki performansı",
        "expected_context": {"currency": "usd", "period": "month", "days": 30},
        "expected_handler": "currency_inflation_analyzer"
    },
    {
        "question": "MACD sinyali pozitif olan fonlar",
        "expected_context": {},
        "expected_handler": "technical_analyzer"
    },
    {
        "question": "Emekliliğe 10 yıl kala nasıl yatırım yapmalıyım?",
        "expected_context": {"years_to_goal": 10},
        "expected_handler": "personal_finance_analyzer"
    },
    {
        "question": "Sharpe oranı 0.5'ten yüksek fonlar",
        "expected_context": {"sharpe_threshold": 0.5, "min_threshold": 0.5},
        "expected_handler": "advanced_metrics_analyzer"
    }
]

print("🧪 AI Smart Router Comprehensive Test")
print("="*60)

success_count = 0
total_count = len(test_cases)

for i, test in enumerate(test_cases, 1):
    question = test["question"]
    expected_context = test["expected_context"]
    expected_handler = test["expected_handler"]
    
    print(f"\n[Test {i}/{total_count}]")
    print(f"❓ Soru: {question}")
    
    # Context extraction
    extracted_context = router._extract_context(question)
    print(f"📊 Extracted Context: {extracted_context}")
    
    # Route bulma
    routes = router.route_question_multi(question)
    
    if routes:
        route = routes[0]
        print(f"✅ Handler: {route.handler}.{route.method}")
        print(f"   Confidence: {route.confidence:.2f}")
        print(f"   Final Context: {route.context}")
        
        # Başarı kontrolü
        handler_correct = route.handler == expected_handler
        context_matches = all(
            extracted_context.get(k) == v 
            for k, v in expected_context.items()
        )
        
        if handler_correct and context_matches:
            print("   🎯 TEST BAŞARILI!")
            success_count += 1
        else:
            print("   ❌ TEST BAŞARISIZ!")
            if not handler_correct:
                print(f"      Beklenen handler: {expected_handler}")
            if not context_matches:
                print(f"      Beklenen context: {expected_context}")
    else:
        print("❌ Route bulunamadı!")
    
    print("-" * 60)

# Özet
print(f"\n📊 TEST SONUCU: {success_count}/{total_count} başarılı")
print(f"🎯 Başarı Oranı: %{(success_count/total_count)*100:.1f}")

# Performans testi
import time
print("\n⚡ PERFORMANS TESTİ:")
start_time = time.time()
for _ in range(10):
    router.route_question_multi("En güvenli 5 fon hangileri?")
elapsed = time.time() - start_time
print(f"10 sorgu için toplam süre: {elapsed:.2f} saniye")
print(f"Ortalama süre: {(elapsed/10)*1000:.0f} ms/sorgu")