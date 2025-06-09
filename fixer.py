# test_fixed_routing.py - Düzeltmeleri test et

from interactive_qa_dual_ai import DualAITefasQA

def test_fixed_routing():
    """Düzeltilmiş routing'i test et"""
    qa = DualAITefasQA()
    
    # Sorunlu test case'leri
    test_cases = [
        "AKB fonunu analiz et",  # Fund analysis
        "TYH AI pattern analizi",  # AI pattern
        "Beta katsayısı 1'den düşük fonlar",  # Beta analysis
    ]
    
    for question in test_cases:
        print(f"\n{'='*80}")
        print(f"TEST: {question}")
        print(f"{'='*80}")
        
        # Manuel routing test
        routes = qa.ai_router.route_question_multi(question)
        if routes:
            print("ROUTING SONUCU:")
            for r in routes:
                print(f"  ✓ {r.handler}.{r.method}")
                print(f"    Context: {r.context}")
                print(f"    Reasoning: {r.reasoning}")
        else:
            print("❌ Routing başarısız!")
        
        # Gerçek cevap
        try:
            answer = qa.answer_question(question)
            print(f"\nCEVAP (ilk 300 karakter):")
            print(answer[:300] + "..." if len(answer) > 300 else answer)
        except Exception as e:
            print(f"❌ HATA: {e}")

if __name__ == "__main__":
    test_fixed_routing()