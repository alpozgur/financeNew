# conflict_resolver.py

class ConflictResolver:
    def __init__(self):
        self.conflict_rules = {
            'performance_analyzer': {
                'keywords': ['güvenli', 'risk'],
                'resolver': self._resolve_safety_conflict
            },
            'currency_inflation_analyzer': {
                'keywords': ['enflasyon'],
                'resolver': self._resolve_inflation_conflict
            },
            'portfolio_analyzer': {
                'keywords': ['portföy'],
                'resolver': self._resolve_portfolio_conflict
            }
        }

    def _resolve_safety_conflict(self, question: str) -> str:
        """Güvenlik sorusu çakışmasını çöz"""
        if 'senaryo' in question or 'olursa' in question:
            return 'scenario_analyzer'
        elif 'emeklilik' in question:
            return 'personal_finance_analyzer'
        elif 'sql' in question or 'hızlı' in question:
            return 'performance_sql'
        else:
            return 'performance_analyzer'
    
    def _resolve_inflation_conflict(self, question: str) -> str:
        """Enflasyon sorusu çakışmasını çöz"""
        if any(word in question for word in ['olursa', 'durumunda', 'senaryo']):
            return 'scenario_analyzer'
        elif 'makro' in question or 'ekonomi' in question:
            return 'macroeconomic_analyzer'
        else:
            return 'currency_inflation_analyzer'
    
    def _resolve_portfolio_conflict(self, question: str) -> str:
        """Portföy sorusu çakışmasını çöz"""
        question_lower = question.lower()
        
        # Matematiksel dağıtım mı?
        if any(word in question_lower for word in ['böl', 'dağıt', 'ayır', 'yüzde']):
            return 'mathematical_calculator'
        
        # Şirket analizi mi?
        company_keywords = ['iş portföy', 'ak portföy', 'garanti portföy']
        if any(company in question_lower for company in company_keywords):
            return 'portfolio_company_analyzer'
        
        # Kişisel finans mı?
        if any(word in question_lower for word in ['emeklilik', 'birikim', 'çocuk']):
            return 'personal_finance_analyzer'
        
        return 'portfolio_company_analyzer'  # Default