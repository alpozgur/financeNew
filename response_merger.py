# response_merger.py
from typing import List, Dict, Any

class ResponseMerger:
    """Birden fazla handler yanıtını birleştiren sınıf"""
    
# response_merger.py - YENİ ÖZELLİKLER EKLE

    def merge_responses(self, responses: List[Dict[str, Any]], question: str) -> str:
        """Gelişmiş response birleştirme"""
        
        if not responses:
            return "❌ Hiçbir handler yanıt üretemedi."
        
        if len(responses) == 1:
            return responses[0]['response']
        
        # Multi-handler response
        merged = f"\n🔄 ÇOKLU ANALİZ SONUÇLARI ({len(responses)} kaynak)\n"
        merged += f"{'='*60}\n\n"
        
        # AI reasoning varsa göster
        if any('reasoning' in r for r in responses):
            merged += f"🤖 AI ANALİZ SEBEPLERİ:\n"
            for r in responses:
                if 'reasoning' in r:
                    merged += f"• {r['handler']}: {r['reasoning']}\n"
            merged += f"\n"
        
        # Yanıtları birleştir
        for i, resp in enumerate(responses, 1):
            handler_name = resp['handler']
            method_name = resp.get('method', '')
            handler_display = self._get_handler_display_name(handler_name)
            
            merged += f"📊 {i}. {handler_display}"
            if method_name:
                merged += f" ({method_name})"
            merged += f"\n"
            merged += f"{'-'*50}\n"
            merged += resp['response']
            
            if i < len(responses):
                merged += f"\n\n{'='*60}\n\n"
        
        # Özet
        if len(responses) > 2:
            merged += f"\n\n💡 ÖZET: {len(responses)} farklı perspektiften analiz yapıldı.\n"
            
            # En yüksek güvenli analiz
            if any('score' in r for r in responses):
                best = max(responses, key=lambda x: x.get('score', 0))
                merged += f"En güvenilir analiz: {self._get_handler_display_name(best['handler'])}\n"
        
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