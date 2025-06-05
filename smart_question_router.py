# smart_question_router.py

import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field

@dataclass
class RouteMatch:
    """Route eşleşme sonucu"""
    handler: str
    method: str
    score: float
    context: Dict[str, Any]
    matched_patterns: List[str] = field(default_factory=list)
    route_name: Optional[str] = None
    priority: Optional[int] = None
    execution_order: Optional[int] = None

class SmartQuestionRouter:
    def __init__(self):
        self.routes = {
            'performance_top_gainers': {
                'patterns': [
                    r'en\s*(?:çok\s*)?(?:kazandıran|karlı|getiri\s*(?:sağlayan|veren)?)',
                    r'(?:en\s*)?(?:yüksek|fazla|iyi)\s*(?:getiri|kazanç|performans)',
                    r'(?:hangi|hangileri).*?(?:kazandır|kar\s*et|getiri)',
                    r'top\s*(?:gainer|performer|fund)',
                ],
                'negative_patterns': ['kaybet', 'düş', 'zarar'],
                'multi_indicators': [r'\d+\s*fon', 'fonlar', 'hangileri', 'listele'],
                'handler': 'performance_analyzer',
                'method': 'handle_top_gainers',
                'priority': 8
            },
            
            'performance_losers': {
                'patterns': [
                    r'en\s*(?:çok\s*)?(?:kaybettiren|zarar|düşen)',
                    r'(?:en\s*)?(?:kötü|zayıf|düşük)\s*(?:performans|getiri)',
                    r'worst\s*(?:performer|fund)',
                ],
                'multi_indicators': [r'\d+\s*fon', 'fonlar', 'hangileri'],
                'handler': 'performance_analyzer',
                'method': 'handle_worst_funds',
                'priority': 8
            },
            
            'safety_analysis': {
                'patterns': [
                    r'(?:en\s*)?güvenli(?:\s*fon)?',
                    r'(?:en\s*)?(?:az|düşük)\s*risk',
                    r'(?:düşük|az)\s*volatilite',
                    r'safe(?:st)?\s*fund',
                ],
                'context_modifiers': {
                    'senaryo': 'scenario_analyzer',
                    'emeklilik': 'personal_finance_analyzer',
                    'sql': 'use_sql_version'
                },
                'handler': 'performance_analyzer',
                'method': 'handle_safest_funds',
                'priority': 9
            },
            
            'technical_macd': {
                'patterns': [
                    r'macd\s*(?:sinyali?)?(?:\s*pozitif|\s*negatif)?',
                    r'macd.*?(?:alım|satım)',
                ],
                'handler': 'technical_analyzer',
                'method': 'handle_macd_signals',
                'priority': 10
            },
            
            'inflation_protection': {
                'patterns': [
                    r'enflasyon(?:\s*korumalı)?',
                    r'inflation\s*protected',
                ],
                'context_modifiers': {
                    'senaryo|olursa': 'scenario_analyzer',
                    'fon|yatırım': 'currency_inflation_analyzer',
                },
                'handler': 'currency_inflation_analyzer',
                'method': 'analyze_inflation',
                'priority': 7
            },
            
            'portfolio_company': {
                'patterns': [
                    r'(?:iş|ak|garanti|qnb|fiba)\s*portföy',
                    r'portföy\s*(?:şirket|yönetim)',
                ],
                'negative_patterns': ['böl', 'dağıt', 'ayır'],
                'handler': 'portfolio_company_analyzer',
                'method': 'analyze_company',
                'priority': 9
            },
            
            'portfolio_distribution': {
                'patterns': [
                    r'(?:portföy|para).*?(?:böl|dağıt|ayır)',
                    r'\d+.*?(?:fona|fon\s*arasında)',
                    r'nasıl\s*dağıt',
                ],
                'handler': 'mathematical_calculator',
                'method': 'handle_portfolio_distribution',
                'priority': 8
            },
            
            'time_based': {
                'patterns': [
                    r'(?:bugün|bu\s*gün|today)',
                    r'(?:bu\s*hafta|this\s*week)',
                    r'(?:son|last)\s*\d+\s*(?:gün|ay|yıl|hafta)',
                    r'(?:ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)',
                ],
                'handler': 'time_based_analyzer',
                'method': 'analyze_time_based',
                'priority': 6
            },
            'personal_advisor': {
                'patterns': [
                    r'\d+\s*yaş',  # "35 yaşındayım"
                    r'kişisel\s*plan',  # "kişisel plan"
                    r'bana\s*özel',  # "bana özel"
                    r'emeklilik.*?plan',  # "emeklilik planı"
                ],
                'handler': 'personal_finance_analyzer',
                'method': 'handle_ai_personalized_planning',
                'priority': 10
            },
            'predictive_scenario': {
                'patterns': [
                    r'tahmin|gelecek\s*\d+\s*(ay|gün)',
                    r'\d+\s*(ay|gün)\s*sonra',
                    r'yıl\s*sonu.*?fon',
                    r'beklenti|öngörü|projeksiyon'
                ],
                'handler': 'predictive_analyzer',
                'method': 'analyze_predictive_scenario',
                'priority': 9
            }
        }
        
        self.confidence_threshold = 5
        self.min_score_threshold = 3
        
        # Multi-handler kuralları
        self.multi_handler_rules = {
            'enflasyon_ve_doviz': {
                'triggers': ['enflasyon', 'döviz'],
                'required_handlers': ['currency_inflation_analyzer', 'scenario_analyzer'],
                'optional_handlers': ['macroeconomic_analyzer']
            },
            'emeklilik_planlamasi': {
                'triggers': ['emeklilik', 'birikim'],
                'required_handlers': ['personal_finance_analyzer'],
                'optional_handlers': ['mathematical_calculator', 'scenario_analyzer']
            },
            'teknik_ve_temel': {
                'triggers': ['analiz', 'detaylı'],
                'required_handlers': ['technical_analyzer'],
                'optional_handlers': ['fundamental_analyzer', 'performance_analyzer']
            },
            'piyasa_genel_durum': {
                'triggers': ['piyasa', 'durum', 'genel'],
                'required_handlers': ['performance_analyzer'],
                'optional_handlers': ['technical_analyzer', 'macroeconomic_analyzer']
            },
            'yatirim_stratejisi': {
                'triggers': ['strateji', 'öneri', 'tavsiye'],
                'required_handlers': ['performance_analyzer'],
                'optional_handlers': ['scenario_analyzer', 'personal_finance_analyzer']
            }
        }
        
        # Handler default metodları ve execution order
        self.handler_configs = {
            'currency_inflation_analyzer': {
                'default_method': 'analyze_currency_inflation_question',
                'execution_order': 10
            },
            'scenario_analyzer': {
                'default_method': 'analyze_scenario_question',
                'execution_order': 20
            },
            'macroeconomic_analyzer': {
                'default_method': 'analyze_macroeconomic_impact',
                'execution_order': 30
            },
            'personal_finance_analyzer': {
                'default_method': 'analyze_personal_finance_question',
                'execution_order': 15
            },
            'mathematical_calculator': {
                'default_method': 'analyze_mathematical_question',
                'execution_order': 25
            },
            'technical_analyzer': {
                'default_method': 'handle_general_technical_signals_sql',
                'execution_order': 35
            },
            'fundamental_analyzer': {
                'default_method': 'handle_general_question',
                'execution_order': 40
            },
            'performance_analyzer': {
                'default_method': 'handle_general_question',
                'execution_order': 45
            },
            'time_based_analyzer': {
                'default_method': 'analyze_time_based_question',
                'execution_order': 50
            },
            'portfolio_company_analyzer': {
                'default_method': 'analyze_company_comprehensive',
                'execution_order': 55
            },
            'thematic_analyzer': {
                'default_method': 'analyze_thematic_question',
                'execution_order': 60
            },
            'advanced_metrics_analyzer': {
                'default_method': 'handle_general_metrics',
                'execution_order': 65
            },
            'predictive_analyzer': {
                'default_method': 'analyze_predictive_scenario',
                'execution_order': 25
            }
        }

    def route_question(self, question: str) -> Optional[Dict]:
        """Soruyu en uygun handler'a yönlendir (legacy single handler için)"""
        question_lower = question.lower()
        matches = []
        
        # SAYILARI ÇIKAR
        numbers = re.findall(r'\d+', question)
        requested_count = int(numbers[0]) if numbers else None
        
        for route_name, config in self.routes.items():
            score = 0
            matched_pattern = None
            
            # Pozitif pattern eşleşmesi
            for pattern in config['patterns']:
                if re.search(pattern, question_lower):
                    score += config['priority']
                    matched_pattern = pattern
                    break
            
            # Negatif pattern kontrolü
            if score > 0 and 'negative_patterns' in config:
                for neg_pattern in config['negative_patterns']:
                    if re.search(neg_pattern, question_lower):
                        score = 0  # Bu route'u iptal et
                        break
            
            # Context modifier kontrolü
            if score > 0 and 'context_modifiers' in config:
                for context_pattern, modifier_handler in config['context_modifiers'].items():
                    if re.search(context_pattern, question_lower):
                        # Handler'ı değiştir
                        config = config.copy()
                        config['handler'] = modifier_handler
                        score += 2  # Context bonus
                        break
            
            if score > 0:
                matches.append({
                    'route': route_name,
                    'score': score,
                    'config': config,
                    'matched_pattern': matched_pattern,
                    'is_multi': self._check_if_multi(question_lower, config)
                })
        
        # En yüksek skorlu route'u seç
        if matches:
            best_match = max(matches, key=lambda x: x['score'])
            
            # Sayı belirleme mantığı
            if requested_count:
                count = requested_count
            elif best_match['is_multi']:
                count = 10  # Default çoklu sonuç
            else:
                count = 1
            
            # Zaman bazlı analiz için gün sayısı
            days = None
            if best_match['route'] == 'time_based':
                # "son 30 gün" gibi ifadeleri parse et
                days_match = re.search(r'son\s*(\d+)\s*gün', question_lower)
                if days_match:
                    days = int(days_match.group(1))
            
            result = {
                'handler': best_match['config']['handler'],
                'method': best_match['config']['method'],
                'is_multi': best_match['is_multi'],
                'count': count,
                'matched_pattern': best_match['matched_pattern'],
                'route_name': best_match['route'],
                'score': best_match['score']
            }
            
            if days:
                result['days'] = days
                
            return result
        
        return None

    def route_question_multi(self, question: str) -> List[RouteMatch]:
        """Birden fazla route döndürebilen routing (multi-handler için)"""
        question_lower = question.lower()
        matches = []
        
    # Önce "X fon" pattern'ini ara
        fon_count_match = re.search(r'(\d+)\s*fon(?:lar)?', question_lower)
        if fon_count_match:
            requested_count = int(fon_count_match.group(1))
        else:
            # Tüm sayıları bul
            numbers = re.findall(r'\d+', question)
            if numbers:
                # 1'den büyük olanları tercih et (zaman ifadeleri genelde 1)
                big_numbers = [int(n) for n in numbers if int(n) > 1]
                requested_count = max(big_numbers) if big_numbers else int(numbers[-1])
            else:
                requested_count = None
        # 🤖 ÖNCELİKLİ AI PATTERN KONTROLÜ
        if any(word in question_lower for word in ['ai teknik', 'ai pattern', 'ai sinyal', 
                                                'yapay zeka teknik', 'pattern analiz']):
            # Direkt AI pattern handler'a yönlendir
            match = RouteMatch(
                handler='technical_analyzer',
                method='handle_ai_pattern_analysis',
                score=100,  # En yüksek skor
                context={'requested_count': requested_count if 'requested_count' in locals() else None},
                matched_patterns=['ai_pattern_priority'],
                route_name='ai_pattern_analysis',
                priority=100,
                execution_order=1
            )
            return [match]  # Sadece bunu döndür
        
        # DEBUG
        print(f"[ROUTER] Question: {question}")
       # print(f"[ROUTER] Numbers found: {numbers}")
        print(f"[ROUTER] Requested count: {requested_count}")
        
        for route_name, config in self.routes.items():
            score = 0
            matched_patterns = []
            
            # Pozitif pattern eşleşmesi
            for pattern in config['patterns']:
                if re.search(pattern, question_lower):
                    score += config.get('priority', 5)
                    matched_patterns.append(pattern)
                    break
            
            # Negatif pattern kontrolü
            if score > 0 and 'negative_patterns' in config:
                for neg_pattern in config['negative_patterns']:
                    if re.search(neg_pattern, question_lower):
                        score = 0
                        break
            
            # Context modifier kontrolü
            if score > 0 and 'context_modifiers' in config:
                for context_pattern, modifier_handler in config['context_modifiers'].items():
                    if re.search(context_pattern, question_lower):
                        config = config.copy()
                        config['handler'] = modifier_handler
                        score += 2
                        break
            
            if score > 0:
                # Context oluştur
                context = {
                    'requested_count': requested_count,
                    'is_multi': self._check_if_multi(question_lower, config)
                }
                print(f"[ROUTER] Route: {route_name}, Is Multi: {context['is_multi']}, Count: {context['requested_count']}")                
                # Zaman bazlı analiz için gün sayısı
                if route_name == 'time_based':
                    days_match = re.search(r'son\s*(\d+)\s*gün', question_lower)
                    if days_match:
                        context['days'] = int(days_match.group(1))
                
                # RouteMatch objesi oluştur
                match = RouteMatch(
                    handler=config['handler'],
                    method=config['method'],
                    score=score,
                    context=context,
                    matched_patterns=matched_patterns,
                    route_name=route_name,
                    priority=config.get('priority', 5),
                    execution_order=self.handler_configs.get(config['handler'], {}).get('execution_order', 50)
                )
                matches.append(match)
        
        # Multi-handler kurallarını uygula
        matches = self._apply_multi_handler_rules(question, matches)
        
        # Execution order'a göre sırala (düşük önce çalışır)
        matches.sort(key=lambda x: (x.execution_order or 50, -x.score))
        
        return matches

    def _apply_multi_handler_rules(self, question: str, matches: List[RouteMatch]) -> List[RouteMatch]:
        """Multi-handler kurallarını uygula"""
        question_lower = question.lower()
        applied_rules = []
        
        # Hangi kurallar tetiklendi?
        for rule_name, rule in self.multi_handler_rules.items():
            if all(trigger in question_lower for trigger in rule['triggers']):
                applied_rules.append(rule)
        
        # Mevcut handler'ları kontrol et
        existing_handlers = {m.handler for m in matches}
        
        # Gerekli handler'ları ekle
        for rule in applied_rules:
            for required_handler in rule['required_handlers']:
                if required_handler not in existing_handlers:
                    # Handler config'ini al
                    handler_config = self._get_handler_config(required_handler)
                    if handler_config:
                        # Context'i kopyala (ilk match'ten)
                        context = matches[0].context.copy() if matches else {}
                        
                        match = RouteMatch(
                            handler=required_handler,
                            method=handler_config['default_method'],
                            score=5,  # Orta skor
                            matched_patterns=['multi_handler_rule'],
                            context=context,
                            priority=5,
                            execution_order=handler_config.get('execution_order', 50)
                        )
                        matches.append(match)
                        existing_handlers.add(required_handler)
            
            # Optional handler'ları düşük skorla ekle
            for optional_handler in rule.get('optional_handlers', []):
                if optional_handler not in existing_handlers:
                    handler_config = self._get_handler_config(optional_handler)
                    if handler_config:
                        context = matches[0].context.copy() if matches else {}
                        
                        match = RouteMatch(
                            handler=optional_handler,
                            method=handler_config['default_method'],
                            score=3,  # Düşük skor
                            matched_patterns=['multi_handler_rule_optional'],
                            context=context,
                            priority=3,
                            execution_order=handler_config.get('execution_order', 50)
                        )
                        matches.append(match)
        
        return matches

    def _get_handler_config(self, handler_name: str) -> Optional[Dict[str, Any]]:
        """Handler config'ini döndür"""
        return self.handler_configs.get(handler_name)

    def _check_if_multi(self, question: str, config: Dict) -> bool:
        """Çoklu sonuç isteniyor mu kontrol et"""
        if 'multi_indicators' in config:
            for indicator in config['multi_indicators']:
                if re.search(indicator, question):
                    return True
        return False

    def route_question_with_confidence(self, question: str) -> Optional[Dict]:
        """Güven skoru ile routing"""
        result = self.route_question(question)
        
        if result and result.get('score', 0) >= self.confidence_threshold:
            result['confidence'] = 'high'
        elif result:
            result['confidence'] = 'low'
            # Düşük güven durumunda kullanıcıya sor
            result['alternatives'] = self._get_alternatives(question)
        
        return result
    
    def _get_alternatives(self, question: str) -> List[Dict]:
        """Alternatif route'ları bul"""
        alternatives = []
        question_lower = question.lower()
        
        for route_name, config in self.routes.items():
            for pattern in config['patterns']:
                if re.search(pattern, question_lower):
                    alternatives.append({
                        'route': route_name,
                        'handler': config['handler'],
                        'method': config['method']
                    })
        
        return alternatives[:3]  # En fazla 3 alternatif