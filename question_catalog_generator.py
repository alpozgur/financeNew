# question_catalog_generator.py
"""
TEFAS Sistemi Soru Kataloğu Oluşturucu
Tüm modüllerdeki sorulabilecek soruları toplar
"""

import os
import re
import importlib
import inspect
from typing import List, Dict, Set

class QuestionCatalogGenerator:
    def __init__(self):
        self.catalog = {}
        self.all_examples = []
        self.all_patterns = []
        self.missing_modules = []
        
    def generate_catalog(self) -> Dict:
        """Ana metod - tüm kataloğu oluştur"""
        
        # 1. Handler'ları tara
        self._scan_handlers()
        
        # 2. Router pattern'lerini tara
        self._scan_router_patterns()
        
        # 3. AI Router pattern'lerini tara
        self._scan_ai_router_patterns()
        
        # 4. Doğrudan metodlardan örnekleri çıkar
        self._extract_from_methods()
        
        # 5. Kataloğu formatla
        return self._format_catalog()
    
    def _scan_handlers(self):
        """Tüm handler modüllerini tara"""
        
        handlers = [
            # (modül_adı, sınıf_adı, kategori)
            ('performance_analysis', 'PerformanceAnalyzerMain', 'Performans'),
            ('technical_analysis', 'TechnicalAnalysis', 'Teknik Analiz'),
            ('currency_inflation_analyzer', 'CurrencyInflationAnalyzer', 'Döviz/Enflasyon'),
            ('scenario_analysis', 'ScenarioAnalyzer', 'Senaryo'),
            ('personal_finance_analyzer', 'PersonalFinanceAnalyzer', 'Kişisel Finans'),
            ('mathematical_calculations', 'MathematicalCalculator', 'Matematik'),
            ('portfolio_company_analysis', 'EnhancedPortfolioCompanyAnalyzer', 'Portföy Şirketleri'),
            ('time_based_analyzer', 'TimeBasedAnalyzer', 'Zaman Bazlı'),
            ('macroeconomic_analyzer', 'MacroeconomicAnalyzer', 'Makroekonomi'),
            ('advanced_metrics_analyzer', 'AdvancedMetricsAnalyzer', 'İleri Metrikler'),
            ('thematic_fund_analyzer', 'ThematicFundAnalyzer', 'Tematik'),
            ('fundamental_analysis', 'FundamentalAnalysisEnhancement', 'Temel Analiz'),
            ('ai_personalized_advisor', 'AIPersonalizedAdvisor', 'AI Danışman')
        ]
        
        for module_name, class_name, category in handlers:
            try:
                # Modülü import et
                module = importlib.import_module(module_name)
                handler_class = getattr(module, class_name)
                
                # get_examples metodunu çağır
                if hasattr(handler_class, 'get_examples'):
                    examples = handler_class.get_examples()
                    self.catalog[category] = {
                        'module': module_name,
                        'class': class_name,
                        'examples': examples,
                        'keywords': handler_class.get_keywords() if hasattr(handler_class, 'get_keywords') else [],
                        'patterns': handler_class.get_patterns() if hasattr(handler_class, 'get_patterns') else []
                    }
                    self.all_examples.extend(examples)
                
            except ImportError:
                self.missing_modules.append(module_name)
            except Exception as e:
                print(f"Hata ({module_name}): {e}")
    
    def _scan_router_patterns(self):
        """smart_question_router.py'den pattern'leri çıkar"""
        try:
            from smart_question_router import SmartQuestionRouter
            router = SmartQuestionRouter()
            
            for route_name, config in router.routes.items():
                # Pattern'leri example'a çevir
                for pattern in config.get('patterns', []):
                    # Regex'i anlamlı örneğe çevir
                    example = self._regex_to_example(pattern)
                    if example:
                        self.all_examples.append(example)
                        self.all_patterns.append({
                            'pattern': pattern,
                            'handler': config['handler'],
                            'method': config['method'],
                            'example': example
                        })
                        
        except Exception as e:
            print(f"Router tarama hatası: {e}")
    
    def _scan_ai_router_patterns(self):
        """ai_smart_question_router.py'den pattern'leri çıkar"""
        try:
            from ai_smart_question_router import AISmartQuestionRouter
            # Module descriptions'dan örnekler çıkar
            ai_router = AISmartQuestionRouter(None)  # ai_provider gerekmiyor sadece pattern'ler için
            
            for module, desc in ai_router.module_descriptions.items():
                keywords = desc.get('keywords', [])
                for keyword in keywords:
                    self.all_examples.append(f"{keyword} fonları nelerdir?")
                    
        except Exception as e:
            print(f"AI Router tarama hatası: {e}")
    
    def _extract_from_methods(self):
        """Metodların docstring'lerinden örnekler çıkar"""
        # Örnek: handle_* metodlarının docstring'leri
        patterns_from_code = [
            # Performans
            "En çok kazandıran 10 fon",
            "En çok kaybettiren fonlar",
            "En güvenli 5 fon",
            "En riskli fonlar",
            "2025 için öneri",
            "AKB fonunu analiz et",
            
            # Teknik
            "MACD sinyali pozitif olan fonlar",
            "RSI 30 altında fonlar",
            "Bollinger alt bandında fonlar",
            "Golden cross veren fonlar",
            "AI pattern analizi yap",
            
            # Döviz/Enflasyon
            "Dolar fonlarının performansı",
            "Euro fonları analizi",
            "Enflasyon korumalı fonlar",
            
            # Senaryo
            "Faiz artarsa ne olur?",
            "Enflasyon %50 olursa hangi fonlar kazandırır?",
            "Dolar 40 TL olursa?",
            
            # Kişisel
            "Emekliliğe 10 yıl kala nasıl yatırım yapmalıyım?",
            "35 yaşındayım emeklilik planı",
            "Çocuğum için eğitim fonu",
            "Ev almak için birikim",
            
            # Matematik
            "100000 TL'yi 3 fona böl",
            "Aylık 5000 TL ile 10 yılda ne birikir?",
            "1 milyon için kaç yıl yatırım yapmalı?",
            
            # Portföy Şirketleri
            "İş Portföy analizi",
            "Ak Portföy vs Garanti Portföy",
            "En başarılı portföy şirketi",
            
            # Zaman
            "Bugün en çok kazanan fonlar",
            "Bu hafta en çok düşenler",
            "Son 30 gün performansı",
            
            # Makro
            "TCMB faiz kararının etkisi",
            "FED kararları fonları nasıl etkiler?",
            
            # İleri Metrikler
            "Beta katsayısı 1'den düşük fonlar",
            "Alpha değeri pozitif fonlar",
            "Sharpe oranı en yüksek fonlar",
            
            # Tematik
            "Teknoloji fonları",
            "Sağlık sektörü fonları",
            "Enerji temalı fonlar",
            
            # Temel
            "En büyük 10 fon",
            "En çok yatırımcısı olan fonlar",
            "Yeni kurulan fonlar"
        ]
        
        self.all_examples.extend(patterns_from_code)
    
    def _regex_to_example(self, pattern: str) -> str:
        """Regex pattern'i örnek soruya çevir"""
        # Basit dönüşümler
        replacements = {
            r'\\s*': ' ',
            r'\\s+': ' ',
            r'(?:': '',
            r')?': '',
            r'.*?': ' ',
            r'[^\s]+': 'ABC',
            r'\d+': '10',
            '|': ' veya '
        }
        
        example = pattern
        for old, new in replacements.items():
            example = example.replace(old, new)
        
        # Temizle
        example = re.sub(r'[()\\]', '', example)
        example = ' '.join(example.split())
        
        return example.strip() + "?" if example else None
    
    def _format_catalog(self) -> Dict:
        """Kataloğu kullanıcı dostu formata çevir"""
        
        # Tekilleştir
        unique_examples = list(set(self.all_examples))
        unique_examples.sort()
        
        # Kategorize et
        categorized = {
            'Performans Soruları': [],
            'Teknik Analiz Soruları': [],
            'Risk Analizi': [],
            'Portföy Yönetimi': [],
            'Kişisel Finans': [],
            'Matematik/Hesaplama': [],
            'Makroekonomi': [],
            'Zaman Bazlı': [],
            'Şirket Analizi': [],
            'Tematik/Sektörel': [],
            'AI Özel': []
        }
        
        # Sınıflandırma kuralları
        for example in unique_examples:
            example_lower = example.lower()
            
            if any(word in example_lower for word in ['kazandıran', 'kaybettiren', 'getiri', 'performans']):
                categorized['Performans Soruları'].append(example)
            elif any(word in example_lower for word in ['macd', 'rsi', 'bollinger', 'teknik', 'ai pattern']):
                categorized['Teknik Analiz Soruları'].append(example)
            elif any(word in example_lower for word in ['risk', 'güvenli', 'volatilite']):
                categorized['Risk Analizi'].append(example)
            elif any(word in example_lower for word in ['portföy', 'dağıt', 'böl']):
                categorized['Portföy Yönetimi'].append(example)
            elif any(word in example_lower for word in ['emeklilik', 'eğitim', 'ev alma', 'yaşında']):
                categorized['Kişisel Finans'].append(example)
            elif any(word in example_lower for word in ['hesapla', 'kaç', 'ne kadar', 'aylık']):
                categorized['Matematik/Hesaplama'].append(example)
            elif any(word in example_lower for word in ['faiz', 'tcmb', 'fed', 'enflasyon']):
                categorized['Makroekonomi'].append(example)
            elif any(word in example_lower for word in ['bugün', 'bu hafta', 'son', 'gün']):
                categorized['Zaman Bazlı'].append(example)
            elif any(word in example_lower for word in ['iş portföy', 'ak portföy', 'şirket']):
                categorized['Şirket Analizi'].append(example)
            elif any(word in example_lower for word in ['teknoloji', 'sağlık', 'enerji', 'sektör']):
                categorized['Tematik/Sektörel'].append(example)
            elif any(word in example_lower for word in ['ai', 'yapay zeka', 'kişiye özel']):
                categorized['AI Özel'].append(example)
        
        return {
            'total_questions': len(unique_examples),
            'categories': categorized,
            'missing_modules': self.missing_modules,
            'detailed_catalog': self.catalog
        }
    
    def generate_markdown_report(self) -> str:
        """Markdown formatında rapor oluştur"""
        catalog = self.generate_catalog()
        
        report = "# TEFAS Analiz Sistemi - Soru Kataloğu\n\n"
        report += f"Toplam {catalog['total_questions']} farklı soru tipi desteklenmektedir.\n\n"
        
        for category, questions in catalog['categories'].items():
            if questions:
                report += f"## {category} ({len(questions)} soru)\n\n"
                for q in sorted(questions)[:20]:  # Her kategoriden max 20
                    report += f"- {q}\n"
                if len(questions) > 20:
                    report += f"- ... ve {len(questions)-20} soru daha\n"
                report += "\n"
        
        if catalog['missing_modules']:
            report += "## Eksik Modüller\n\n"
            for module in catalog['missing_modules']:
                report += f"- {module}\n"
        
        return report

# Kullanım
if __name__ == "__main__":
    generator = QuestionCatalogGenerator()
    
    # Markdown raporu oluştur
    report = generator.generate_markdown_report()
    
    # Dosyaya kaydet
    with open('soru_katalogu.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("Soru kataloğu 'soru_katalogu.md' dosyasına kaydedildi!")
    
    # Eksik modülleri göster
    catalog = generator.generate_catalog()
    if catalog['missing_modules']:
        print(f"\nEksik modüller: {', '.join(catalog['missing_modules'])}")