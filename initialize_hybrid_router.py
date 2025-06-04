# initialize_hybrid_router.py
"""
Production için Hybrid Router initialization
"""
from handler_registry import HandlerRegistry
from hybrid_smart_router import HybridSmartRouter

def initialize_hybrid_router(ai_provider=None, use_sbert=True):
    """Production router initialization"""
    
    # Registry oluştur
    registry = HandlerRegistry()
    
    # Handler'ları register et
    handlers = [
        ('performance_analysis', 'PerformanceAnalyzerMain', 'performance_analyzer'),
        ('technical_analysis', 'TechnicalAnalysis', 'technical_analyzer'),
        ('currency_inflation_analyzer', 'CurrencyInflationAnalyzer', 'currency_inflation_analyzer'),
        ('scenario_analysis', 'ScenarioAnalyzer', 'scenario_analyzer'),
        ('personal_finance_analyzer', 'PersonalFinanceAnalyzer', 'personal_finance_analyzer'),
        ('mathematical_calculations', 'MathematicalCalculator', 'mathematical_calculator'),
        ('portfolio_company_analysis', 'EnhancedPortfolioCompanyAnalyzer', 'portfolio_company_analyzer'),
        ('time_based_analyzer', 'TimeBasedAnalyzer', 'time_based_analyzer'),
        ('macroeconomic_analyzer', 'MacroeconomicAnalyzer', 'macroeconomic_analyzer'),
        ('advanced_metrics_analyzer', 'AdvancedMetricsAnalyzer', 'advanced_metrics_analyzer'),
        ('thematic_fund_analyzer', 'ThematicFundAnalyzer', 'thematic_analyzer'),
        ('fundamental_analysis', 'FundamentalAnalysisEnhancement', 'fundamental_analyzer')
    ]
    
    for module_name, class_name, handler_name in handlers:
        try:
            module = __import__(module_name, fromlist=[class_name])
            handler_class = getattr(module, class_name)
            registry.register(handler_class, handler_name)
        except Exception as e:
            print(f"Warning: Could not register {handler_name}: {e}")
    
    # Router oluştur
    router = HybridSmartRouter(registry, ai_provider, use_sbert)
    
    return router, registry