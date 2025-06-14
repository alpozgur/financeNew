# config/config.py
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Dict, Any
import json

load_dotenv()

@dataclass
class DatabaseConfig:
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '5432'))
    database: str = os.getenv('DB_NAME', 'tefas_db')
    username: str = os.getenv('DB_USER', 'postgres')
    password: str = os.getenv('DB_PASSWORD', '')
    
    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class AIConfig:
    openai_api_key: str = os.getenv('OPENAI_API_KEY', '')

@dataclass
class AnalysisConfig:
    risk_free_rate: float = 0.15  # Turkey risk-free rate
    confidence_levels: list = None
    monte_carlo_simulations: int = 10000
    backtesting_period: int = 252  # 1 year
    technical_indicators: dict = None
    
    def __post_init__(self):
        if self.confidence_levels is None:
            self.confidence_levels = [0.95, 0.99]
        if self.technical_indicators is None:
            self.technical_indicators = {
                'sma_periods': [5, 10, 20, 50, 100, 200],
                'ema_periods': [12, 26],
                'rsi_period': 14,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'bollinger_period': 20,
                'bollinger_std': 2
            }

class Config:
    def __init__(self):
        self.database = DatabaseConfig()
        self.ai = AIConfig()
        self.analysis = AnalysisConfig()
        
    def save_to_json(self, filepath: str):
        """Konfigürasyonu JSON dosyasına kaydet"""
        config_dict = {
            'database': {
                'host': self.database.host,
                'port': self.database.port,
                'database': self.database.database,
                'username': self.database.username
            },
            'ai': {
                'openai_api_key': self.ai.openai_api_key
            },
            'analysis': {
                'risk_free_rate': self.analysis.risk_free_rate,
                'confidence_levels': self.analysis.confidence_levels,
                'monte_carlo_simulations': self.analysis.monte_carlo_simulations,
                'backtesting_period': self.analysis.backtesting_period,
                'technical_indicators': self.analysis.technical_indicators
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
