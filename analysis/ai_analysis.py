# analysis/ai_analysis.py
"""
AI Analysis Module - OpenAI 1.0+ Compatible
TEFAS fonları için AI destekli analiz ve yorumlama
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from datetime import datetime
from database.connection import DatabaseManager
from config.config import Config

class AIAnalyzer:
    """AI destekli analiz sistemi - OpenAI 1.0+ destekli"""
    
    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.db = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # OpenAI kurulumu (yeni versiyon)
        self.openai_client = None
        self.openai_available = False
        self._setup_openai()
        
        self.logger.info("AI Analyzer initialized")
    
    def _setup_openai(self):
        """OpenAI client'ı kur"""
        try:
            if self.config.ai.openai_api_key:
                # OpenAI 1.0+ import
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.config.ai.openai_api_key)
                self.openai_available = True
                self.logger.info("OpenAI client initialized successfully")
            else:
                self.logger.warning("OpenAI API key not found")
        except ImportError:
            self.logger.warning("OpenAI library not installed or version incompatible")
        except Exception as e:
            self.logger.error(f"OpenAI setup error: {e}")
    
    def query_openai(self, prompt: str, system_message: str = None, model: str = "gpt-3.5-turbo") -> str:
        """OpenAI API ile analiz yap (yeni versiyon)"""
        if not self.openai_available:
            return "OpenAI API kullanılamıyor - API key eksik veya yanlış"
        
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            return f"OpenAI analizi başarısız: {str(e)[:100]}"
    
    def analyze_fund_with_ai(self, 
                           fcode: str, 
                           performance_data: Dict = None, 
                           technical_data: Dict = None,
                           risk_data: Dict = None) -> Dict:
        """Fon analizi yap"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'fund_code': fcode,
            'analysis': {}
        }
        
        # Prompt oluştur
        prompt = self._create_analysis_prompt(fcode, performance_data, technical_data, risk_data)
        system_message = self._get_system_prompt()
        
        # OpenAI analizi
        try:
            openai_analysis = self.query_openai(prompt, system_message)
            results['analysis'] = openai_analysis
            self.logger.info(f"OpenAI analysis completed for {fcode}")
        except Exception as e:
            results['analysis'] = f"AI analizi başarısız: {e}"
            self.logger.error(f"AI analysis failed for {fcode}: {e}")
        
        return results
    
    def get_ai_status(self) -> Dict:
        """AI sistemlerinin durumunu döndür"""
        return {
            'openai': {
                'available': self.openai_available,
                'status': 'Ready' if self.openai_available else 'Not configured'
            }
        }