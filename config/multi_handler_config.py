# config/multi_handler_config.py

MULTI_HANDLER_CONFIG = {
    'enable_multi_handler': True,
    'max_handlers_per_question': 4,
    'min_score_threshold': 3,
    'merge_strategy': 'sequential',  # veya 'parallel', 'hierarchical'
    
    'handler_limits': {
        'scenario_analyzer': 2000,  # Max karakter sayısı
        'performance_analyzer': 1500,
        'technical_analyzer': 1000,
        'default': 1500
    },
    
    'execution_timeout': 10,  # saniye
    
    'priority_overrides': {
        # Belirli kombinasyonlar için öncelik
        ('scenario_analyzer', 'personal_finance_analyzer'): 10,
        ('time_based_analyzer', 'performance_analyzer'): 8
    }
}