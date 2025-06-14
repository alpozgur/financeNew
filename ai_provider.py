# ai_provider.py
"""
Unified AI Provider - OpenAI desteği
Production-ready with fallback support
"""

import os
from typing import Optional, Dict, Any
import logging

class AIProvider:
    """Tek bir interface üzerinden OpenAI provider'ı yönet"""
    
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.logger = logging.getLogger(__name__)
        
        # Config'den provider tipini al
        self.provider_type = 'openai'
        self.fallback_enabled = os.getenv('AI_FALLBACK', 'true').lower() == 'true'
        
        # Mevcut AI analyzer'ı kullan
        self.ai_analyzer = coordinator.ai_analyzer if hasattr(coordinator, 'ai_analyzer') else None
        
        self._log_configuration()
    
    def _log_configuration(self):
        """AI konfigürasyonunu logla"""
        self.logger.info(f"AI Provider initialized: {self.provider_type}")
        self.logger.info(f"Fallback enabled: {self.fallback_enabled}")
        self.logger.info("Using OpenAI API")
    
    def query(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Ana query metodu - OpenAI provider
        
        Args:
            prompt: Kullanıcı promptu
            system_prompt: Sistem promptu (opsiyonel)
            **kwargs: Provider-specific parametreler
            
        Returns:
            AI yanıtı (string)
        """
        try:
            return self._query_openai(prompt, system_prompt, **kwargs)
        except Exception as e:
            self.logger.error(f"AI query failed: {e}")
            return self._get_fallback_response()
    
    def _query_openai(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """OpenAI query wrapper"""
        if not self.ai_analyzer:
            raise ValueError("AI Analyzer not initialized")
        
        # Mevcut metodu kullan
        return self.ai_analyzer.query_openai(prompt, system_prompt)
    
    def _get_fallback_response(self) -> str:
        """AI kullanılamadığında fallback yanıt"""
        return """
        AI analizi şu anda kullanılamıyor. 
        Lütfen veritabanı sonuçlarına göre değerlendirme yapın.
        """
    
    def is_available(self) -> bool:
        """AI servisinin kullanılabilir olup olmadığını kontrol et"""
        return self.ai_analyzer and self.ai_analyzer.openai_available
    
    def get_status(self) -> Dict[str, Any]:
        """AI provider durumunu döndür"""
        return {
            'provider_type': self.provider_type,
            'fallback_enabled': self.fallback_enabled,
            'is_available': self.is_available(),
            'openai_status': self.ai_analyzer.openai_available if self.ai_analyzer else False
        }