"""
Semantic Router Kullanım Örneği
"""

import logging
from semantic_router import SemanticRouter, RouteMatch
import time
from typing import Dict, Any, List

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Router'ı oluştur
    router = SemanticRouter(
        model_name='all-MiniLM-L6-v2',
        similarity_threshold=0.7,
        max_matches=3
    )
    
    # Handler'ları ekle
    router.add_handler(
        handler='fund_analyzer',
        description='Fon analizi ve performans değerlendirmesi yapar',
        methods={
            'GET': 'Fon bilgilerini getirir',
            'POST': 'Yeni fon analizi başlatır'
        },
        examples=[
            'Bu fonun performansı nasıl?',
            'Fonun getirisi nedir?'
        ]
    )
    
    # Test routing
    test_questions = [
        "Bu fonun performansı nasıl?",
        "Portföyümü optimize et",
        "Piyasa trendi nedir?"
    ]
    
    for question in test_questions:
        print(f"\nSoru: {question}")
        routes = router.route(question)
        for route in routes:
            print(f"Handler: {route.handler}")
            print(f"Method: {route.method}")
            print(f"Confidence: {route.confidence:.2f}")
            print(f"Reasoning: {route.reasoning}")
            print("---")

if __name__ == "__main__":
    main() 