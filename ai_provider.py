# ai_provider.py
"""
Unified AI Provider - OpenAI, Ollama veya Dual mode desteği
Production-ready with fallback support
"""

import os
from typing import Optional, Dict, Any
import logging

class AIProvider:
    """Tek bir interface üzerinden farklı AI provider'ları yönet"""
    
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.logger = logging.getLogger(__name__)
        
        # Config'den provider tipini al
        self.provider_type = os.getenv('AI_PROVIDER', 'openai').lower()
        self.fallback_enabled = os.getenv('AI_FALLBACK', 'true').lower() == 'true'
        
        # Mevcut AI analyzer'ı kullan
        self.ai_analyzer = coordinator.ai_analyzer if hasattr(coordinator, 'ai_analyzer') else None
        
        self._log_configuration()
    
    def _log_configuration(self):
        """AI konfigürasyonunu logla"""
        self.logger.info(f"AI Provider initialized: {self.provider_type}")
        self.logger.info(f"Fallback enabled: {self.fallback_enabled}")
        
        if self.provider_type == 'openai':
            self.logger.info("Using OpenAI API")
        elif self.provider_type == 'ollama':
            self.logger.info("Using Ollama (local)")
        elif self.provider_type == 'dual':
            self.logger.info("Using Dual mode (OpenAI + Ollama)")
    
    def query(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Ana query metodu - provider agnostic
        
        Args:
            prompt: Kullanıcı promptu
            system_prompt: Sistem promptu (opsiyonel)
            **kwargs: Provider-specific parametreler
            
        Returns:
            AI yanıtı (string)
        """
        try:
            if self.provider_type == 'openai':
                return self._query_openai(prompt, system_prompt, **kwargs)
            
            elif self.provider_type == 'ollama':
                try:
                    return self._query_ollama(prompt, system_prompt, **kwargs)
                except Exception as e:
                    if self.fallback_enabled:
                        self.logger.warning(f"Ollama failed, falling back to OpenAI: {e}")
                        return self._query_openai(prompt, system_prompt, **kwargs)
                    raise
            
            elif self.provider_type == 'dual':
                return self._query_dual(prompt, system_prompt, **kwargs)
            
            else:
                raise ValueError(f"Unknown provider type: {self.provider_type}")
                
        except Exception as e:
            self.logger.error(f"AI query failed: {e}")
            return self._get_fallback_response()
    
    def _query_openai(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """OpenAI query wrapper"""
        if not self.ai_analyzer:
            raise ValueError("AI Analyzer not initialized")
        
        # Mevcut metodu kullan
        return self.ai_analyzer.query_openai(prompt, system_prompt)
    
    def _query_ollama(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Ollama query wrapper"""
        if not self.ai_analyzer:
            raise ValueError("AI Analyzer not initialized")
        
        # Mevcut metodu kullan
        return self.ai_analyzer.query_ollama(prompt, system_prompt)
    
    def _query_dual(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Dual mode - her iki AI'dan da yanıt al"""
        results = {}
        
        # OpenAI yanıtı
        try:
            results['openai'] = self._query_openai(prompt, system_prompt, **kwargs)
        except Exception as e:
            self.logger.error(f"OpenAI query failed in dual mode: {e}")
            results['openai'] = None
        
        # Ollama yanıtı
        try:
            results['ollama'] = self._query_ollama(prompt, system_prompt, **kwargs)
        except Exception as e:
            self.logger.error(f"Ollama query failed in dual mode: {e}")
            results['ollama'] = None
        
        return self._format_dual_response(results)
    
    def _format_dual_response(self, results: Dict[str, Optional[str]]) -> str:
        """Dual mode yanıtlarını formatla"""
        response = ""
        
        if results.get('openai'):
            response += f"📱 OpenAI Analizi:\n{results['openai']}\n"
        else:
            response += "📱 OpenAI: Yanıt alınamadı\n"
        
        if results.get('ollama'):
            response += f"\n🦙 Ollama Analizi:\n{results['ollama']}\n"
        else:
            response += "\n🦙 Ollama: Yanıt alınamadı\n"
        
        if not results.get('openai') and not results.get('ollama'):
            response = self._get_fallback_response()
        
        return response
    
    def _get_fallback_response(self) -> str:
        """AI kullanılamadığında fallback yanıt"""
        return """
        AI analizi şu anda kullanılamıyor. 
        Lütfen veritabanı sonuçlarına göre değerlendirme yapın.
        """
    
    def is_available(self) -> bool:
        """AI servisinin kullanılabilir olup olmadığını kontrol et"""
        if self.provider_type == 'openai':
            return self.ai_analyzer and self.ai_analyzer.openai_available
        elif self.provider_type == 'ollama':
            return self.ai_analyzer and self.ai_analyzer.ollama_available
        elif self.provider_type == 'dual':
            return self.ai_analyzer and (
                self.ai_analyzer.openai_available or 
                self.ai_analyzer.ollama_available
            )
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """AI provider durumunu döndür"""
        return {
            'provider_type': self.provider_type,
            'fallback_enabled': self.fallback_enabled,
            'is_available': self.is_available(),
            'openai_status': self.ai_analyzer.openai_available if self.ai_analyzer else False,
            'ollama_status': self.ai_analyzer.ollama_available if self.ai_analyzer else False
        }