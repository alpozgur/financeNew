# test_ai_routing.py
from interactive_qa_dual_ai import DualAITefasQA

def test_routing():
    qa = DualAITefasQA()
    
    test_cases = [
        # Basit sorular
        "En güvenli 10 fon",
        "MPP fonunu analiz et",
        
        # Multi-handler tetikleyiciler
        "MPP fonunun detaylı analizi",
        "Piyasa durumu hakkında kapsamlı bilgi",
        
        # Karmaşık sorular
        "35 yaşındayım, emekliliğe 25 yıl var, 100 bin TL ile nasıl yatırım yapmalıyım?",
        "Enflasyon %50 olursa hangi fonlar güvenli?",
        
        # Teknik
        "Beta katsayısı 1'den düşük ve Sharpe oranı 0.5'ten yüksek fonlar",
        "AI pattern analizi ile TYH fonunu incele"
    ]
    
    for question in test_cases:
        print(f"\n{'='*80}")
        print(f"SORU: {question}")
        print(f"{'='*80}")
        
        # Routing sonuçları
        routes = qa.ai_router.route_question_multi(question)
        print("\nROUTING:")
        for r in routes:
            print(f"  {r.handler}.{r.method} (güven: {r.confidence:.2f})")
            print(f"    Context: {r.context}")
            print(f"    Sebep: {r.reasoning}")
        
        # Cevap
        print("\nCEVAP:")
        answer = qa.answer_question(question)
        print(answer[:500] + "..." if len(answer) > 500 else answer)

if __name__ == "__main__":
    test_routing()