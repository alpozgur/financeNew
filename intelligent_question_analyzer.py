"""
Akıllı Soru Analiz Sistemi
Kullanıcı girdilerini normalize eder ve doğru yönlendirme yapar
"""

import re
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
import unicodedata

@dataclass
class QuestionAnalysis:
    """Soru analiz sonucu"""
    original_question: str
    normalized_question: str
    fund_codes: List[str]
    question_type: str  # 'single_fund', 'comparison', 'multi_fund', 'general'
    keywords: Dict[str, List[str]]
    intent: str  # 'analyze', 'compare', 'list', 'recommend', etc.
    parameters: Dict[str, any]

class IntelligentQuestionAnalyzer:
    """Akıllı soru analiz sistemi"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._load_valid_fund_codes()
        self._initialize_patterns()
    
    def _load_valid_fund_codes(self):
        """Veritabanından geçerli fon kodlarını yükle"""
        try:
            # Tüm fon kodlarını yükle ve normalize et
            all_codes = self.db.get_all_fund_codes()
            self.valid_fund_codes = {code.upper() for code in all_codes}
            print(f"✅ {len(self.valid_fund_codes)} geçerli fon kodu yüklendi")
        except Exception as e:
            print(f"❌ Fon kodları yüklenemedi: {e}")
            self.valid_fund_codes = set()
    
    def _initialize_patterns(self):
        """Pattern ve keyword tanımlamaları"""
        
        # Intent patterns
        self.intent_patterns = {
            'analyze': ['analiz', 'incele', 'değerlendir', 'nasıl', 'durum', 'performans'],
            'compare': ['karşılaştır', 'compare', 'vs', 'karşı', 'fark', 'hangisi', 'mı yoksa'],
            'list': ['listele', 'göster', 'hangileri', 'neler', 'kaç tane', 'en iyi', 'en kötü'],
            'recommend': ['öner', 'tavsiye', 'recommend', 'suggest', 'hangisi iyi'],
            'predict': ['tahmin', 'gelecek', 'olur', 'beklenti', 'forecast'],
            'risk': ['risk', 'güvenli', 'riskli', 'volatilite', 'kayıp'],
            'technical': ['teknik', 'macd', 'rsi', 'bollinger', 'sinyal'],
            'scenario': ['olursa', 'durumunda', 'senaryosu', 'eğer', 'what if']
        }
        
        # Category patterns
        self.category_patterns = {
            'currency': ['dolar', 'euro', 'döviz', 'kur', 'usd', 'eur', 'fx'],
            'gold': ['altın', 'gold', 'kıymetli', 'maden'],
            'equity': ['hisse', 'borsa', 'pay', 'stock', 'equity'],
            'bond': ['tahvil', 'bono', 'bond', 'sabit getiri'],
            'money_market': ['para piyasası', 'likit', 'kısa vadeli', 'repo']
        }
        
        # Time patterns
        self.time_patterns = {
            'today': ['bugün', 'today'],
            'week': ['hafta', 'haftalık', 'week'],
            'month': ['ay', 'aylık', 'month'],
            'year': ['yıl', 'yıllık', 'senelik', 'year'],
            'days': [r'(\d+)\s*gün', r'son\s*(\d+)\s*gün'],
            'future': ['gelecek', 'sonra', 'future', 'önümüzdeki']
        }
    
    def analyze_question(self, question: str) -> QuestionAnalysis:
        """Soruyu detaylı analiz et"""
        
        # 1. Normalize et
        normalized = self._normalize_text(question)
        
        # 2. Fon kodlarını tespit et
        fund_codes = self._extract_fund_codes(question)
        
        # 3. Soru tipini belirle
        question_type = self._determine_question_type(fund_codes, normalized)
        
        # 4. Intent'i belirle
        intent = self._determine_intent(normalized)
        
        # 5. Keyword'leri çıkar
        keywords = self._extract_keywords(normalized)
        
        # 6. Parametreleri çıkar
        parameters = self._extract_parameters(normalized, fund_codes)
        
        return QuestionAnalysis(
            original_question=question,
            normalized_question=normalized,
            fund_codes=fund_codes,
            question_type=question_type,
            keywords=keywords,
            intent=intent,
            parameters=parameters
        )
    
    def _normalize_text(self, text: str) -> str:
        """Metni normalize et - Türkçe karakterler korunur"""
        # Küçük harfe çevir
        text = text.lower()
        
        # Fazla boşlukları temizle
        text = ' '.join(text.split())
        
        # Noktalama işaretlerini koru ama normalize et
        text = re.sub(r'\s+([?.!,])', r'\1', text)
        
        return text
    
    def _extract_fund_codes(self, question: str) -> List[str]:
        """Fon kodlarını akıllıca tespit et"""
        found_codes = []
        
        # Hem büyük hem küçük harf kombinasyonları için
        # Tüm 3 harfli kombinasyonları bul
        potential_codes = re.findall(r'\b[A-Za-z]{3}\b', question)
        
        for code in potential_codes:
            code_upper = code.upper()
            
            # Geçerli fon kodu mu kontrol et
            if code_upper in self.valid_fund_codes:
                if code_upper not in found_codes:
                    found_codes.append(code_upper)
            else:
                # Yakın eşleşme kontrolü (typo düzeltme)
                close_match = self._find_close_match(code_upper)
                if close_match and close_match not in found_codes:
                    found_codes.append(close_match)
        
        return found_codes
    
    def _find_close_match(self, code: str) -> Optional[str]:
        """Yakın fon kodu eşleşmesi bul (typo düzeltme)"""
        # Basit Levenshtein mesafesi
        for valid_code in self.valid_fund_codes:
            if self._levenshtein_distance(code, valid_code) <= 1:
                return valid_code
        return None
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """İki string arasındaki Levenshtein mesafesi"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _determine_question_type(self, fund_codes: List[str], normalized: str) -> str:
        """Soru tipini belirle"""
        num_funds = len(fund_codes)
        
        if num_funds == 0:
            return 'general'
        elif num_funds == 1:
            # Tek fon ama liste sorusu olabilir
            if any(word in normalized for word in ['fonlar', 'hangileri', 'listele']):
                return 'multi_fund'
            return 'single_fund'
        elif num_funds == 2:
            # İki fon - karşılaştırma mı yoksa ikisi hakkında ayrı bilgi mi?
            if any(word in normalized for word in ['karşılaştır', 'vs', 'karşı', 'fark']):
                return 'comparison'
            return 'multi_fund'
        else:
            return 'multi_fund'
    
    def _determine_intent(self, normalized: str) -> str:
        """Ana niyeti belirle"""
        max_score = 0
        best_intent = 'analyze'
        
        for intent, patterns in self.intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in normalized)
            if score > max_score:
                max_score = score
                best_intent = intent
        
        return best_intent
    
    def _extract_keywords(self, normalized: str) -> Dict[str, List[str]]:
        """Kategorilere göre keyword'leri çıkar"""
        keywords = {}
        
        for category, patterns in self.category_patterns.items():
            found = [p for p in patterns if p in normalized]
            if found:
                keywords[category] = found
        
        # Zaman keyword'leri
        time_keywords = []
        for time_type, patterns in self.time_patterns.items():
            if time_type == 'days':
                for pattern in patterns:
                    match = re.search(pattern, normalized)
                    if match:
                        time_keywords.append(f"{match.group(1)}_days")
            else:
                for pattern in patterns:
                    if pattern in normalized:
                        time_keywords.append(time_type)
                        break
        
        if time_keywords:
            keywords['time'] = time_keywords
        
        return keywords
    
    def _extract_parameters(self, normalized: str, fund_codes: List[str]) -> Dict[str, any]:
        """Parametreleri çıkar"""
        params = {}
        
        # Sayıları çıkar
        numbers = re.findall(r'\d+', normalized)
        if numbers:
            # "5 fon", "10 tane" gibi
            count_match = re.search(r'(\d+)\s*(fon|tane|adet)', normalized)
            if count_match:
                params['requested_count'] = int(count_match.group(1))
            
            # Yüzde değerleri
            percent_match = re.search(r'%\s*(\d+)|(\d+)\s*%', normalized)
            if percent_match:
                params['percentage'] = int(percent_match.group(1) or percent_match.group(2))
            
            # Para miktarı (50000, 100000 gibi)
            for num in numbers:
                if len(num) >= 5:  # En az 10000
                    params['amount'] = int(num)
                    break
        
        # Zaman parametreleri
        time_match = re.search(r'(\d+)\s*(gün|hafta|ay|yıl)', normalized)
        if time_match:
            value = int(time_match.group(1))
            unit = time_match.group(2)
            
            # Güne çevir
            if unit == 'hafta':
                params['days'] = value * 7
            elif unit == 'ay':
                params['days'] = value * 30
            elif unit == 'yıl':
                params['days'] = value * 365
            else:
                params['days'] = value
        
        # Fon kodları
        if fund_codes:
            params['fund_codes'] = fund_codes
        
        return params
