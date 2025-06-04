# handler_registry.py
"""
Merkezi Handler Registry - Tüm handler'ların pattern ve keyword bilgilerini tutar
"""
from typing import Dict, List, Tuple, Optional
import inspect

class HandlerRegistry:
    """Handler'ları ve pattern bilgilerini merkezi olarak yöneten sınıf"""
    
    def __init__(self):
        self.registry = {}
        self._initialize_patterns()
    
    def register(self, handler_class, name: str):
        """Handler'ı registry'ye kaydet"""
        handler_info = {
            "class": handler_class,
            "examples": [],
            "keywords": [],
            "patterns": [],
            "methods": {}
        }
        
        # Handler'ın pattern metodlarını çağır
        if hasattr(handler_class, "get_examples"):
            handler_info["examples"] = handler_class.get_examples()
        
        if hasattr(handler_class, "get_keywords"):
            handler_info["keywords"] = handler_class.get_keywords()
            
        if hasattr(handler_class, "get_patterns"):
            handler_info["patterns"] = handler_class.get_patterns()
        
        # Method mapping bilgilerini al
        if hasattr(handler_class, "get_method_patterns"):
            handler_info["methods"] = handler_class.get_method_patterns()
            
        self.registry[name] = handler_info
    
    def _initialize_patterns(self):
        """Özel pattern'leri initialize et (şirket isimleri, temalar vs.)"""
        
        # Şirket pattern'leri
        self.company_patterns = {
            'iş portföy': 'portfolio_company_analyzer',
            'is portfoy': 'portfolio_company_analyzer',
            'işbank portföy': 'portfolio_company_analyzer',
            'ak portföy': 'portfolio_company_analyzer',
            'garanti portföy': 'portfolio_company_analyzer',
            'ata portföy': 'portfolio_company_analyzer',
            'qnb portföy': 'portfolio_company_analyzer',
            'fiba portföy': 'portfolio_company_analyzer'
        }
        
        # Tema pattern'leri
        self.thematic_patterns = {
            'teknoloji': 'thematic_analyzer',
            'sağlık': 'thematic_analyzer',
            'enerji': 'thematic_analyzer',
            'bankacılık': 'thematic_analyzer',
            'gıda': 'thematic_analyzer',
            'sektör': 'thematic_analyzer'
        }
        
        # Teknik analiz pattern'leri
        self.technical_patterns = {
            'macd': 'technical_analyzer',
            'rsi': 'technical_analyzer',
            'bollinger': 'technical_analyzer',
            'sma': 'technical_analyzer',
            'ema': 'technical_analyzer',
            'golden cross': 'technical_analyzer',
            'death cross': 'technical_analyzer'
        }
    
    def get_handler_for_pattern(self, text: str) -> Optional[Tuple[str, str, float]]:
        """
        Text için en uygun handler'ı bul
        Returns: (handler_name, method_name, confidence_score)
        """
        text_lower = text.lower()
        
        # 1. Öncelikli pattern kontrolü (şirket, tema, teknik)
        for pattern, handler in self.company_patterns.items():
            if pattern in text_lower:
                return (handler, 'analyze_company_comprehensive', 1.0)
        
        for pattern, handler in self.thematic_patterns.items():
            if pattern in text_lower:
                return (handler, 'analyze_thematic_question', 0.95)
        
        for pattern, handler in self.technical_patterns.items():
            if pattern in text_lower:
                method = self._get_technical_method(pattern)
                return ('technical_analyzer', method, 0.95)
        
        # 2. ÖNCELİKLİ KONTROLLER - Çakışan pattern'ler için
        # "Dolar fonlarının" -> currency_inflation_analyzer öncelikli
        if any(word in text_lower for word in ['dolar', 'euro', 'usd', 'eur']) and 'fon' in text_lower:
            # currency_inflation_analyzer'ı zorla
            for name, info in self.registry.items():
                if name == 'currency_inflation_analyzer':
                    method = self._find_best_method(text_lower, info['methods'])
                    return (name, method, 0.98)
        
        # "Bugün" -> time_based_analyzer öncelikli
        if any(word in text_lower for word in ['bugün', 'dün', 'bu hafta', 'bu ay', 'bu yıl']):
            for name, info in self.registry.items():
                if name == 'time_based_analyzer':
                    method = self._find_best_method(text_lower, info['methods'])
                    return (name, method, 0.98)
        
        # 3. Handler pattern kontrolü - SCORING İLE
        candidates = []
        
        for name, info in self.registry.items():
            # Pattern matching
            pattern_score = self._calculate_pattern_score(text_lower, info['patterns'])
            if pattern_score > 0:
                method = self._find_best_method(text_lower, info['methods'])
                candidates.append((name, method, pattern_score, 'pattern'))
            
            # Keyword matching
            keyword_score = self._calculate_keyword_score(text_lower, info['keywords'])
            if keyword_score > 0:
                method = self._find_best_method(text_lower, info['methods'])
                # Keyword score'u biraz düşür pattern'e göre
                candidates.append((name, method, keyword_score * 0.9, 'keyword'))
            
            # Example matching
            example_score = self._calculate_example_score(text_lower, info['examples'])
            if example_score > 0:
                method = self._find_best_method(text_lower, info['methods'])
                # Example score'u daha da düşür
                candidates.append((name, method, example_score * 0.8, 'example'))
        
        # En yüksek score'lu candidate'i seç
        if candidates:
            # Score'a göre sırala
            candidates.sort(key=lambda x: x[2], reverse=True)
            
            # Debug için
            if len(candidates) > 1:
                # print(f"[DEBUG] Top candidates for '{text[:50]}...':")
                for c in candidates[:3]:
                    print(f"  - {c[0]}: {c[2]:.2f} ({c[3]})")
            
            best = candidates[0]
            return (best[0], best[1], best[2])
        
        return None
    
    def _calculate_keyword_score(self, text: str, keywords: List[str]) -> float:
        """Keyword eşleşme skoru hesapla"""
        if not keywords:
            return 0.0
        
        matches = sum(1 for kw in keywords if kw.lower() in text)
        return min(matches / len(keywords) + (matches * 0.2), 1.0)
    
    def _calculate_pattern_score(self, text: str, patterns: List[Dict]) -> float:
        """Pattern eşleşme skoru hesapla"""
        if not patterns:
            return 0.0
        
        for pattern in patterns:
            if pattern.get('type') == 'regex':
                import re
                if re.search(pattern['pattern'], text):
                    return pattern.get('score', 0.8)
            elif pattern.get('type') == 'contains_all':
                words = pattern.get('words', [])
                if all(word in text for word in words):
                    return pattern.get('score', 0.9)
        
        return 0.0
    
    def _calculate_example_score(self, text: str, examples: List[str]) -> float:
        """Örnek eşleşme skoru hesapla"""
        if not examples:
            return 0.0
        
        # Basit yaklaşım: kelime benzerliği
        text_words = set(text.split())
        best_score = 0
        
        for example in examples:
            example_words = set(example.lower().split())
            common_words = text_words.intersection(example_words)
            
            if len(example_words) > 0:
                score = len(common_words) / len(example_words)
                best_score = max(best_score, score)
        
        return best_score
    
    def _find_best_method(self, text: str, methods: Dict[str, List[str]]) -> str:
        """Handler için en uygun method'u bul"""
        if not methods:
            return 'analyze'  # Default method
        
        for method_name, patterns in methods.items():
            for pattern in patterns:
                if pattern.lower() in text:
                    return method_name
        
        # Default olarak ilk method'u döndür
        return list(methods.keys())[0] if methods else 'analyze'
    
    def _get_technical_method(self, indicator: str) -> str:
        """Teknik indikatör için uygun method'u döndür"""
        method_map = {
            'macd': 'handle_macd_signals_sql',
            'rsi': 'handle_rsi_signals_sql',
            'bollinger': 'handle_bollinger_signals_sql',
            'sma': 'handle_moving_average_signals_sql',
            'ema': 'handle_moving_average_signals_sql',
            'golden cross': 'handle_moving_average_signals_sql',
            'death cross': 'handle_moving_average_signals_sql'
        }
        return method_map.get(indicator, 'handle_general_technical_signals_sql')
    
    def get_all_patterns(self) -> List[Tuple[str, str]]:
        """Tüm pattern'leri döndür (debugging için)"""
        patterns = []
        
        for name, info in self.registry.items():
            for example in info['examples']:
                patterns.append((name, example))
            for keyword in info['keywords']:
                patterns.append((name, keyword))
        
        return patterns