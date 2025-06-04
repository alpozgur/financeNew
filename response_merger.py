# response_merger.py
from typing import List, Dict, Any

class ResponseMerger:
    """Birden fazla handler yanıtını birleştiren sınıf"""
    
    def merge_responses(self, responses: List[Dict[str, Any]], question: str) -> str:
        """Birden fazla handler yanıtını birleştir"""
        
        if not responses:
            return "❌ Hiçbir handler yanıt üretemedi."
        
        if len(responses) == 1:
            # Tek yanıt varsa direkt döndür
            return responses[0]['response']
        
        # Birden fazla yanıt varsa birleştir
        merged = f"\n🔄 ÇOKLU ANALİZ SONUÇLARI ({len(responses)} kaynak)\n"
        merged += f"{'='*60}\n\n"
        
        # Yanıtları skorlarına göre sırala
        responses.sort(key=lambda x: x['score'], reverse=True)
        
        for i, resp in enumerate(responses, 1):
            handler_name = resp['handler']
            handler_display = self._get_handler_display_name(handler_name)
            
            merged += f"📊 {i}. {handler_display} (Skor: {resp['score']})\n"
            merged += f"{'-'*50}\n"
            merged += resp['response']
            
            if i < len(responses):
                merged += f"\n\n{'='*60}\n\n"
        
        # Özet ekle
        if len(responses) > 2:
            merged += f"\n\n💡 ÖZET: {len(responses)} farklı perspektiften analiz yapıldı.\n"
            merged += f"En yüksek skorlu analiz: {self._get_handler_display_name(responses[0]['handler'])}\n"
        
        return merged
    
    def _get_handler_display_name(self, handler_name: str) -> str:
        """Handler adını kullanıcı dostu formata çevir"""
        display_names = {
            'performance_analyzer': 'Performans Analizi',
            'scenario_analyzer': 'Senaryo Analizi',
            'technical_analyzer': 'Teknik Analiz',
            'currency_inflation_analyzer': 'Döviz/Enflasyon Analizi',
            'portfolio_company_analyzer': 'Portföy Şirket Analizi',
            'mathematical_calculator': 'Matematiksel Hesaplama',
            'time_based_analyzer': 'Zaman Bazlı Analiz',
            'macroeconomic_analyzer': 'Makroekonomik Analiz',
            'advanced_metrics_analyzer': 'İleri Metrik Analizi',
            'thematic_analyzer': 'Tematik Analiz',
            'fundamental_analyzer': 'Temel Analiz',
            'personal_finance_analyzer': 'Kişisel Finans Analizi'
        }
        return display_names.get(handler_name, handler_name.replace('_', ' ').title())