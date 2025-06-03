# interactive_qa_dual_ai.py
"""
TEFAS Analysis System - Dual AI Q&A (OpenAI vs Ollama)
Her iki AI'ın da yanıt vermesi için güncellenmiş versiyon
"""
import re
import sys
import pandas as pd
import numpy as np
from config.config import Config
from analysis.coordinator import AnalysisCoordinator
from analysis.hybrid_fund_selector import HybridFundSelector, HighPerformanceFundAnalyzer
from analysis.performance import batch_analyze_funds_by_details
# Mevcut import'ların altına ekleyin:
from thematic_fund_analyzer import ThematicFundAnalyzer
from utils import normalize_turkish_text
from technical_analysis import TechnicalAnalysis
from performance_analysis import PerformanceAnalyzerMain
from fundamental_analysis import FundamentalAnalysisEnhancement
from portfolio_company_analysis import EnhancedPortfolioCompanyAnalyzer
class DualAITefasQA:
    """TEFAS Soru-Cevap Sistemi - OpenAI ve Ollama karşılaştırmalı"""
    
    def __init__(self):
        print("🚀 TEFAS Analysis Dual AI Q&A System Loading...")
        self.config = Config()
        self.coordinator = AnalysisCoordinator(self.config)

        # Aktif fonları yükle
        print("📊 Loading active funds...")
        self.active_funds = self._load_active_funds()
        print(f"✅ Loaded {len(self.active_funds)} active funds")
        self.ai_status = self._check_ai_availability()
        self.technical_analyzer = TechnicalAnalysis(self.coordinator, self.active_funds)
        self.fundamental_analyzer = FundamentalAnalysisEnhancement(self.coordinator, self.active_funds)
        self.portfolio_analyzer = EnhancedPortfolioCompanyAnalyzer(self.coordinator)
        self.thematic_analyzer = ThematicFundAnalyzer(self.coordinator.db, self.config)
        self.performanceMain = PerformanceAnalyzerMain(self.coordinator, self.active_funds, self.ai_status)
        # AI durumunu kontrol et
        
    def _load_active_funds(self, max_funds=None, mode="comprehensive"):
        """
        Gelişmiş fon yükleme sistemi
        mode: "hybrid" (1-2 dk), "comprehensive" (5-10 dk), "fast" (30 sn)
        """
        
        if mode == "hybrid":
            print("🎯 Hibrit mod: Akıllı örnekleme + Büyük fonlar")
            selector = HybridFundSelector(self.coordinator.db, self.config)
            active_funds, analysis_funds = selector.load_funds_hybrid(
                quick_sample=150,    # 150 temsili fon
                detailed_analysis=30, # 30 detaylı analiz
                include_top=True     # Büyük fonları dahil et
            )
            return analysis_funds
            
        elif mode == "comprehensive":
            print("🚀 Kapsamlı mod: TÜM FONLAR (5-10 dakika)")
            analyzer = HighPerformanceFundAnalyzer(self.coordinator.db, self.config)
            all_results = analyzer.analyze_all_funds_optimized(
                batch_size=100,
                max_workers=8,
                use_bulk_queries=True
            )
            # En iyi 50 fonu döndür
            return all_results.head(50)['fcode'].tolist()
            
        else:  # fast
            print("⚡ Hızlı mod: İlk 50 fon")
            all_funds = self.coordinator.db.get_all_fund_codes()
            return all_funds[:50]
        
    def _check_ai_availability(self):
        """AI sistemlerinin durumunu kontrol et"""
        ai_status = {
            'openai': self.coordinator.ai_analyzer.openai_available,
            'ollama': self.coordinator.ai_analyzer.ollama_available
        }
        
        print(f"\n🤖 AI SİSTEMLERİ DURUMU:")
        print(f"   📱 OpenAI: {'✅ Hazır' if ai_status['openai'] else '❌ Mevcut değil'}")
        print(f"   🦙 Ollama: {'✅ Hazır' if ai_status['ollama'] else '❌ Mevcut değil'}")
        
        if ai_status['openai'] and ai_status['ollama']:
            print("   🎯 Her iki AI de aktif - Karşılaştırmalı analiz mevcut!")
        elif ai_status['openai']:
            print("   🎯 Sadece OpenAI aktif")
        elif ai_status['ollama']:
            print("   🎯 Sadece Ollama aktif")
        else:
            print("   ⚠️ Hiçbir AI sistemi aktif değil")
            
        return ai_status
    
    def answer_question(self, question):
        """Soruya her iki AI ile de cevap ver"""
        question_lower =normalize_turkish_text(question)

        # Sayısal değer parsing (10 fon, 5 fon vs.)
        numbers_in_question = re.findall(r'(\d+)', question)
        requested_count = int(numbers_in_question[0]) if numbers_in_question else 1
        
        # GÜVENLİ FONLAR - ÇOKLU LİSTE DESTEĞİ
        if any(word in question_lower for word in ['en güvenli', 'en az riskli', 'güvenli fonlar']):
            # Eğer sayı belirtilmişse (örn: "en güvenli 10 fon") -> liste ver
            if requested_count > 1 or 'fonlar' in question_lower:
                return self.performanceMain.handle_safest_funds_sql_fast(requested_count)
            else:
                # Tek fon istiyorsa -> eski metodu kullan
                return self.performanceMain.handle_safest_fund()
        
        # RİSKLİ FONLAR - ÇOKLU LİSTE DESTEĞİ  
        if "en riskli" in question_lower:
            if requested_count > 1 or 'fonlar' in question_lower:
                return self.performanceMain.handle_riskiest_funds_list(requested_count)
            else:
                return self.performanceMain.handle_most_risky_fund()
        
        # EN ÇOK KAYBETTİREN - ÇOKLU LİSTE DESTEĞİ
        if any(word in question_lower for word in ['en çok kaybettiren', 'en çok düşen']):
            if requested_count > 1 or 'fonlar' in question_lower:
                return self.performanceMain.handle_worst_funds_list(requested_count)
            else:
                return self.performanceMain.handle_worst_fund()        
        # Özel risk sorusu yakalama
        if "en riskli" in question_lower:
            return self.performanceMain.handle_most_risky_fund()
        if "en güvenli" in question_lower or "en az riskli" in question_lower:
            return self.performanceMain.handle_safest_fund()
        if "en çok kaybettiren" in question_lower or "en çok düşen" in question_lower:
            return self.performanceMain.handle_worst_fund()

        if any(word in question_lower for word in ['portföy', 'portfolio']):
            
            # Belirli şirket kapsamlı analizi
            if any(word in question_lower for word in ['iş portföy', 'is portfoy', 'işbank portföy']):
                return self.portfolio_analyzer.analyze_company_comprehensive('İş Portföy')
            
            elif any(word in question_lower for word in ['ak portföy', 'akbank portföy']):
                return self.portfolio_analyzer.analyze_company_comprehensive('Ak Portföy')
            
            elif any(word in question_lower for word in ['garanti portföy', 'garantibank portföy']):
                return self.portfolio_analyzer.analyze_company_comprehensive('Garanti Portföy')
            
            elif any(word in question_lower for word in ['ata portföy']):
                return self.portfolio_analyzer.analyze_company_comprehensive('Ata Portföy')
            
            elif any(word in question_lower for word in ['qnb portföy']):
                return self.portfolio_analyzer.analyze_company_comprehensive('QNB Portföy')
            
            elif any(word in question_lower for word in ['fiba portföy', 'fibabank portföy']):
                return self.portfolio_analyzer.analyze_company_comprehensive('Fiba Portföy')
            
            # Şirket karşılaştırması
            elif any(word in question_lower for word in ['vs', 'karşı', 'karşılaştır', 'compare']):
                return self._handle_company_comparison_enhanced(question)
            
            # En başarılı şirket
            elif any(word in question_lower for word in ['en başarılı', 'en iyi', 'best', 'most successful']):
                return self.portfolio_analyzer.find_best_portfolio_company_unlimited()
            
            else:
                return self._handle_portfolio_companies_overview(question)            
        # 📈 TEMATİK FON SORULARI - TÜM VERİTABANI 
        if self.thematic_analyzer.is_thematic_question(question):
            return self.thematic_analyzer.analyze_thematic_question(question)
               # FUNDAMENTAL ANALİZ SORULARI 🆕
        if any(word in question_lower for word in ['kapasite', 'büyüklük', 'büyük fon']):
            return self.fundamental_analyzer.handle_capacity_questions(question)
        
        if any(word in question_lower for word in ['yatırımcı sayısı', 'popüler fon']):
            return self.fundamental_analyzer.handle_investor_count_questions(question)
        
        if any(word in question_lower for word in ['yeni fon', 'yeni kurulan']):
            return self.fundamental_analyzer.handle_new_funds_questions(question)
        
        if any(word in question_lower for word in ['en büyük', 'largest']):
            return self.fundamental_analyzer.handle_largest_funds_questions(question)
        
        if any(word in question_lower for word in ['en eski', 'köklü']):
            return self.fundamental_analyzer.handle_fund_age_questions(question)
        
        if any(word in question_lower for word in ['kategori', 'tür']):
            return self.fundamental_analyzer.handle_fund_category_questions(question)        
        # --- Gelişmiş anahtar kelime tabanlı analizler ---
        if any(word in question_lower for word in ['yatırım dağılımı', 'varlık dağılımı', 'kompozisyon', 'içerik', 'portföy içerik']):
            return self._handle_fund_allocation_question(question)
        if 'fon kategorisi' in question_lower or 'fon türü' in question_lower:
            return self._handle_fund_category_question(question)
        if any(word in question_lower for word in ['kazanç', 'getiri', 'son 1 yıl', 'son 12 ay', 'geçtiğimiz yıl', 'son yıl']):
            return self.performanceMain.handle_fund_past_performance_question(question)
        if 'en çok kazandıran' in question_lower or 'en çok getiri' in question_lower:
            return self.performanceMain.handle_top_gainer_fund_question(question)
        if 'düşüşte olan fonlar' in question_lower or 'en çok kaybettiren' in question_lower:
            return self.performanceMain.handle_top_loser_fund_question(question)
        if 'sharpe oranı en yüksek' in question_lower:
            return self.performanceMain.handle_top_sharpe_funds_question(question)
        if 'volatilite' in question_lower and 'altında' in question_lower:
            return self.performanceMain.handle_low_volatility_funds_question(question)
        # --- mevcut kalan kodun ---
        if any(word in question_lower for word in ['2025', 'öneri', 'öner', 'recommend', 'suggest']):
            return self.performanceMain.handle_2025_recommendation_dual(question)
        elif any(word in question_lower for word in ['analiz', 'analyze', 'performance']):
            return self.performanceMain.handle_analysis_question_dual(question)
        elif any(word in question_lower for word in ['karşılaştır', 'compare', 'vs']):
            return self.performanceMain.handle_comparison_question(question)
        elif any(word in question_lower for word in ['risk', 'güvenli', 'safe']):
            return self._handle_risk_question(question)
        elif any(word in question_lower for word in ['piyasa', 'market', 'durum']):
            return self._handle_market_question_dual(question)
        elif any(word in question_lower for word in ['macd', 'bollinger', 'rsi', 'hareketli ortalama', 
                                                    'moving average', 'sma', 'ema', 'teknik sinyal',
                                                    'alım sinyali', 'satım sinyali', 'aşırı satım',
                                                    'aşırı alım', 'golden cross', 'death cross']):
            technical_result = self._handle_technical_analysis_questions_full_db(question)
            if technical_result:
                return technical_result
            else:
                return self._handle_general_question(question)
        elif any(word in question_lower for word in ['ai', 'yapay zeka', 'test']):
            return self._handle_ai_test_question(question)
        else:
            return self._handle_general_question(question)

    def _handle_portfolio_companies_overview(self, question):
        """Genel portföy şirketleri genel bakış"""
        print("🏢 Portföy şirketleri genel analizi...")
        
        response = f"\n🏢 PORTFÖY YÖNETİM ŞİRKETLERİ GENEL BAKIŞ\n"
        response += f"{'='*50}\n\n"
        
        # Desteklenen şirketleri listele
        response += f"📊 DESTEKLENEN ŞİRKETLER:\n\n"
        
        for i, company in enumerate(self.portfolio_analyzer.company_keywords.keys(), 1):
            response += f"{i:2d}. {company}\n"
        
        response += f"\n💡 KULLANIM ÖRNEKLERİ:\n"
        response += f"   • 'İş Portföy analizi'\n"
        response += f"   • 'Ak Portföy vs Garanti Portföy karşılaştırması'\n"
        response += f"   • 'En başarılı portföy şirketi hangisi?'\n"
        response += f"   • 'QNB Portföy fonları nasıl?'\n\n"
        
        response += f"🎯 ÖZELLİKLER:\n"
        response += f"   ✅ Şirket bazında tüm fonları analiz\n"
        response += f"   ✅ Performans karşılaştırması\n"
        response += f"   ✅ Risk-getiri analizi\n"
        response += f"   ✅ Sharpe oranı hesaplama\n"
        response += f"   ✅ Kapsamlı raporlama\n\n"
        
        response += f"📈 EN BAŞARILI ŞİRKET İÇİN:\n"
        response += f"   'En başarılı portföy şirketi' sorusunu sorun!\n"
        
        return response

    def _handle_company_comparison_enhanced(self, question):
        """Gelişmiş şirket karşılaştırması"""
        # Sorudan şirket isimlerini çıkar
        companies = []
        question_upper = question.upper()
        
        for company, keywords in self.portfolio_analyzer.company_keywords.items():
            for keyword in keywords:
                if keyword in question_upper:
                    companies.append(company)
                    break
        
        # Tekrarları kaldır ve ilk 2'sini al
        companies = list(dict.fromkeys(companies))[:2]
        
        if len(companies) < 2:
            return f"❌ Karşılaştırma için 2 şirket gerekli. Örnek: 'İş Portföy vs Ak Portföy karşılaştırması'"
        
        return self.portfolio_analyzer.compare_companies_unlimited(companies[0], companies[1])

    def handle_company_comparison_enhanced(self, question):
        """Gelişmiş şirket karşılaştırması"""
        # Sorudan şirket isimlerini çıkar
        companies = []
        question_upper = question.upper()
        
        for company, keywords in self.portfolio_analyzer.company_keywords.items():
            for keyword in keywords:
                if keyword in question_upper:
                    companies.append(company)
                    break
        
        # Tekrarları kaldır ve ilk 2'sini al
        companies = list(dict.fromkeys(companies))[:2]
        
        if len(companies) < 2:
            return f"❌ Karşılaştırma için 2 şirket gerekli. Örnek: 'İş Portföy vs Ak Portföy karşılaştırması'"
        
        return self.portfolio_analyzer.compare_companies_unlimited(companies[0], companies[1])

    def _handle_technical_analysis_questions_full_db(self, question):
        """SQL tabanlı teknik analiz - Tüm veritabanını kullanır"""
        question_lower = question.lower()
        
        # MACD sinyali soruları
        if any(word in question_lower for word in ['macd', 'macd sinyali', 'macd pozitif', 'macd negatif']):
            return self.technical_analyzer.handle_macd_signals_sql(question)
        
        # Bollinger Bands soruları
        elif any(word in question_lower for word in ['bollinger', 'bollinger bantları', 'alt banda', 'üst banda']):
            return self.technical_analyzer.handle_bollinger_signals_sql(question)
        
        # RSI soruları
        elif any(word in question_lower for word in ['rsi', 'rsi düşük', 'rsi yüksek', 'aşırı satım', 'aşırı alım']):
            return self.technical_analyzer.handle_rsi_signals_sql(question)
        
        # Moving Average soruları
        elif any(word in question_lower for word in ['hareketli ortalama', 'moving average', 'sma', 'ema', 'golden cross', 'death cross']):
            return self.technical_analyzer.handle_moving_average_signals_sql(question)
        
        # Genel teknik sinyal soruları
        elif any(word in question_lower for word in ['teknik sinyal', 'alım sinyali', 'satım sinyali']):
            return self.technical_analyzer.handle_general_technical_signals_sql(question)
        
        else:
            return None

    def _handle_fund_category_question(self, question):
        words = question.upper().split()
        fund_code = None
        for word in words:
            if len(word) == 3 and word.isalpha():
                if word.upper() in [x.upper() for x in self.active_funds]:
                    fund_code = word.upper()
                    break
        if not fund_code:
            return "❌ Geçerli bir fon kodu tespit edilemedi."
        details = self.coordinator.db.get_fund_details(fund_code)
        if not details:
            return "❌ Fon detayı bulunamadı."
        category = details.get('fund_category', 'Bilinmiyor')
        fund_type = details.get('fund_type', 'Bilinmiyor')
        response = f"\n📑 {fund_code} FONU KATEGORİ BİLGİLERİ\n{'='*40}\n"
        response += f"Kategori: {category}\n"
        response += f"Tür: {fund_type}\n"
        return response

    def _handle_fund_allocation_question(self, question):
        # Soru içindeki fon kodunu bul
        import re
        words = question.upper().split()
        print("Kullanıcıdan gelen kelimeler:", words)
        print("Aktif fonlar:", self.active_funds)
        fund_code = None
        for word in words:
            if len(word) == 3 and word.isalpha():
                if word.upper() in [x.upper() for x in self.active_funds]:
                    fund_code = word.upper()
                    break
        # Eğer aktiflerde bulamazsan, tüm fon kodlarında dene
        if not fund_code:
            all_funds = [x.upper() for x in self.coordinator.db.get_all_fund_codes()]
            for word in words:
                if len(word) == 3 and word.isalpha():
                    if word.upper() in all_funds:
                        fund_code = word.upper()
                        break
        if not fund_code:
            return "❌ Geçerli bir fon kodu tespit edilemedi."
        details = self.coordinator.db.get_fund_details(fund_code)
        if not details:
            return "❌ Fon detayı bulunamadı."
        
        # --- Kolon anahtarlarının Türkçesi (dilersen ekle/güncelle) ---
        turkish_map = {
            "reverserepo": "Ters Repo",
            "foreignprivatesectordebtinstruments": "Yabancı Özel Sektör Borçlanması",
            "foreigninvestmentfundparticipationshares": "Yabancı Yatırım Fonu Katılma Payı",
            "governmentbondsandbillsfx": "Döviz Cinsi DİBS",
            "privatesectorforeigndebtinstruments": "Yabancı Özel Sektör Borçlanma Araçları",
            "stock": "Hisse Senedi",
            "governmentbond": "Devlet Tahvili",
            "precious_metals": "Kıymetli Madenler"
            # ... Diğerlerini ekleyebilirsin
        }

        # Öncelikle eski klasik yöntemle dene:
        allocation_keys = [
            'stock', 'governmentbond', 'eurobonds', 'bankbills', 'fxpayablebills',
            'commercialpaper', 'fundparticipationcertificate', 'realestateinvestmentfundparticipation', 'precious_metals',
            'reverserepo', 'foreignprivatesectordebtinstruments', 'foreigninvestmentfundparticipationshares',
            'governmentbondsandbillsfx', 'privatesectorforeigndebtinstruments'
        ]
        allocation = []
        for key in allocation_keys:
            val = details.get(key, 0)
            if isinstance(val, (int, float)) and val > 0:
                allocation.append((key, val))
            elif isinstance(val, str) and val.replace('.', '', 1).isdigit() and float(val) > 0:
                allocation.append((key, float(val)))
        # Eğer hala boşsa, otomatik tarama:
        if not allocation:
            allocation = []
            for k, v in details.items():
                if isinstance(v, (int, float)) and v > 0 and k not in ["idtefasfunddetails", "fcode", "fdate"]:
                    allocation.append((k, v))
                elif isinstance(v, str) and v.replace('.', '', 1).isdigit() and float(v) > 0 and k not in ["idtefasfunddetails", "fcode", "fdate"]:
                    allocation.append((k, float(v)))
        if not allocation:
            return f"❌ {fund_code} fonunun yatırım dağılımı verisi bulunamadı."
        
        # Yüzdelik tablo yap
        response = f"\n📊 {fund_code} FONU YATIRIM DAĞILIMI\n{'='*40}\n"
        response += "Varlık Türü                          | Yüzde (%)\n"
        response += "------------------------------------|-----------\n"
        for k, v in allocation:
            turkish = turkish_map.get(k, k)
            response += f"{turkish:<36} | {v:.2f}\n"
        response += "\nNot: Değerler doğrudan TEFAS veritabanından alınmıştır."
        return response
   
    def _handle_market_question_dual(self, question):
        """Piyasa durumu - Her iki AI ile"""
        print("📊 Dual AI piyasa durumu analiz ediliyor...")
        
        try:
            # Son 10 günün verilerini analiz et
            market_data = []
            
            for fcode in self.active_funds[:20]:
                try:
                    data = self.coordinator.db.get_fund_price_history(fcode, 10)
                    if not data.empty:
                        prices = data['price']
                        recent_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                        market_data.append(recent_return)
                except:
                    continue
            
            if market_data:
                avg_return = np.mean(market_data)
                positive_funds = sum(1 for r in market_data if r > 0)
                total_funds = len(market_data)
                
                response = f"\n📈 DUAL AI PİYASA DURUMU RAPORU\n"
                response += f"{'='*35}\n\n"
                
                response += f"📊 SON 10 GÜN VERİLERİ:\n"
                response += f"   Analiz Edilen Fon: {total_funds}\n"
                response += f"   Ortalama Getiri: %{avg_return:.2f}\n"
                response += f"   Pozitif Performans: {positive_funds}/{total_funds} (%{positive_funds/total_funds*100:.1f})\n\n"
                
                # Piyasa durumu
                if avg_return > 2:
                    mood = "🟢 ÇOK POZİTİF"
                elif avg_return > 0:
                    mood = "🟡 POZİTİF"
                elif avg_return > -2:
                    mood = "🟠 NÖTR"
                else:
                    mood = "🔴 NEGATİF"
                
                response += f"🌡️ PİYASA DUYARLILIĞI: {mood}\n\n"
                
                # AI yorumları
                market_prompt = f"""
                TEFAS piyasa durumu:
                
                Son 10 gün ortalama getiri: %{avg_return:.2f}
                Pozitif performans oranı: %{positive_funds/total_funds*100:.1f}
                Analiz edilen fon sayısı: {total_funds}
                Piyasa durumu: {mood}
                
                Bu verilere dayanarak piyasa durumu ve yatırımcı önerileri hakkında kısa yorum yap.
                """
                
                response += f"🤖 DUAL AI PİYASA YORUMLARI:\n"
                response += f"{'='*30}\n"
                
                # OpenAI yorumu
                if self.ai_status['openai']:
                    try:
                        openai_market = self.coordinator.ai_analyzer.query_openai(
                            market_prompt,
                            "Sen piyasa analisti uzmanısın."
                        )
                        response += f"\n📱 OpenAI Piyasa Yorumu:\n{openai_market}\n"
                    except Exception as e:
                        response += f"\n📱 OpenAI: ❌ Piyasa analizi alınamadı\n"
                
                # Ollama yorumu
                if self.ai_status['ollama']:
                    try:
                        ollama_market = self.coordinator.ai_analyzer.query_ollama(
                            market_prompt,
                            "Sen piyasa analisti uzmanısın."
                        )
                        response += f"\n🦙 Ollama Piyasa Yorumu:\n{ollama_market}\n"
                    except Exception as e:
                        response += f"\n🦙 Ollama: ❌ Piyasa analizi alınamadı\n"
                
                return response
            else:
                return "❌ Piyasa analizi için yeterli veri bulunamadı"
                
        except Exception as e:
            return f"❌ Piyasa analizi hatası: {e}"
    
    def _handle_ai_test_question(self, question):
        """AI test soruları"""
        response = f"\n🧪 AI SİSTEMLERİ TEST RAPORU\n"
        response += f"{'='*30}\n\n"
        
        response += f"📊 DURUM RAPORU:\n"
        response += f"   📱 OpenAI: {'✅ Aktif' if self.ai_status['openai'] else '❌ İnaktif'}\n"
        response += f"   🦙 Ollama: {'✅ Aktif' if self.ai_status['ollama'] else '❌ İnaktif'}\n\n"
        
        # Test prompt'u
        test_prompt = "TEFAS fonları hakkında 2 cümlelik kısa bilgi ver."
        
        response += f"🧪 TEST SONUÇLARI:\n"
        
        # OpenAI test
        if self.ai_status['openai']:
            try:
                openai_test = self.coordinator.ai_analyzer.query_openai(test_prompt)
                response += f"\n📱 OpenAI Test:\n   ✅ Çalışıyor\n   Yanıt: {openai_test[:100]}...\n"
            except Exception as e:
                response += f"\n📱 OpenAI Test:\n   ❌ Hata: {str(e)[:50]}\n"
        else:
            response += f"\n📱 OpenAI Test:\n   ❌ Kullanılamıyor\n"
        
        # Ollama test
        if self.ai_status['ollama']:
            try:
                ollama_test = self.coordinator.ai_analyzer.query_ollama(test_prompt)
                response += f"\n🦙 Ollama Test:\n   ✅ Çalışıyor\n   Yanıt: {ollama_test[:100]}...\n"
            except Exception as e:
                response += f"\n🦙 Ollama Test:\n   ❌ Hata: {str(e)[:50]}\n"
        else:
            response += f"\n🦙 Ollama Test:\n   ❌ Kullanılamıyor\n"
        
        return response
        
    def _handle_risk_question(self, question):
        """Risk soruları (önceki kodla aynı)"""
        response = f"\n🛡️ RİSK ANALİZİ VE GÜVENLİ YATIRIM\n"
        response += f"{'='*35}\n\n"
        
        # Düşük riskli fonları bul
        low_risk_funds = []
        
        for fcode in self.active_funds[:15]:
            try:
                data = self.coordinator.db.get_fund_price_history(fcode, 60)
                if not data.empty:
                    returns = data['price'].pct_change().dropna()
                    volatility = returns.std() * 100
                    
                    if volatility < 15:  # %15'ten düşük volatilite
                        low_risk_funds.append({
                            'fund': fcode,
                            'volatility': volatility,
                            'return': (data['price'].iloc[-1] / data['price'].iloc[0] - 1) * 100
                        })
            except:
                continue
        
        if low_risk_funds:
            df = pd.DataFrame(low_risk_funds).sort_values('volatility')
            
            response += f"🛡️ DÜŞÜK RİSKLİ FONLAR:\n"
            for _, fund in df.head(5).iterrows():
                response += f"   {fund['fund']}: Risk %{fund['volatility']:.1f}, Getiri %{fund['return']:.1f}\n"
        
        response += f"\n📋 RİSK YÖNETİMİ PRİNSİPLERİ:\n"
        response += f"   • Portföyünüzü diversifiye edin\n"
        response += f"   • Risk toleransınızı bilin\n"
        response += f"   • Acil fon ayırın (6-12 aylık gider)\n"
        response += f"   • Düzenli olarak rebalancing yapın\n"
        response += f"   • Uzun vadeli düşünün\n"
        
        return response
    
    def _handle_general_question(self, question):
        """Genel sorular"""
        response = f"\n❓ DUAL AI TEFAS ANALİZ SİSTEMİ\n"
        response += f"{'='*35}\n\n"
        
        response += f"🤖 SİSTEM DURUMU:\n"
        response += f"   📱 OpenAI: {'✅ Aktif' if self.ai_status['openai'] else '❌ İnaktif'}\n"
        response += f"   🦙 Ollama: {'✅ Aktif' if self.ai_status['ollama'] else '❌ İnaktif'}\n"
        response += f"   📊 Aktif Fonlar: {len(self.active_funds)}\n"
        response += f"   🗄️ Veritabanı: ✅ Bağlı\n\n"
        
        response += f"📋 DUAL AI SORU TİPLERİ:\n"
        response += f"   • '2025 için hangi fonları önerirsin?' (Her iki AI de yanıt verir)\n"
        response += f"   • 'AKB fonunu analiz et' (Dual AI değerlendirme)\n"
        response += f"   • 'Piyasa durumu nasıl?' (İkili AI yorumu)\n"
        response += f"   • 'AI test' (AI sistemlerini test et)\n"
        response += f"   • 'AKB ve YAS karşılaştır'\n"
        response += f"   • 'Güvenli fonlar neler?'\n\n"
        
        response += f"🎯 DUAL AI AVANTAJLARI:\n"
        response += f"   • OpenAI ve Ollama karşılaştırması\n"
        response += f"   • Farklı AI perspektifleri\n"
        response += f"   • Daha kapsamlı analiz\n"
        response += f"   • AI performans değerlendirmesi\n"
        
        return response

    def run_interactive_session(self):
        """İnteraktif dual AI oturumu"""
        print("\n" + "="*60)
        print("🤖 TEFAS DUAL AI ANALYSIS SYSTEM")
        print("="*60)
        print("🎯 Özellik: Her iki AI (OpenAI + Ollama) aynı anda yanıt verir!")
        print("\n💡 Örnek sorular:")
        print("   • '2025 için 100000 TL ile hangi fonları önerirsin?'")
        print("   • 'AKB fonunu analiz et'")
        print("   • 'Piyasa durumu nasıl?'")
        print("   • 'AI test' (AI sistemlerini test et)")
        print("   • 'AKB ve YAS karşılaştır'")
        print("\n💬 Sorunuzu yazın (çıkmak için 'exit' yazın):")
        print("-" * 60)
        
        while True:
            try:
                question = input("\n🔍 Dual AI Soru: ").strip()
                
                if question.lower() in ['exit', 'çıkış', 'quit', 'q']:
                    print("\n👋 Dual AI Session sona erdi!")
                    break
                
                if not question:
                    continue
                
                print(f"\n🔄 Dual AI işleniyor...")
                answer = self.answer_question(question)
                print(answer)
                
                print("\n" + "-" * 60)
                
            except KeyboardInterrupt:
                print("\n\n👋 Dual AI Session sona erdi!")
                break
            except Exception as e:
                print(f"\n❌ Hata oluştu: {e}")
                continue



def main():
    """Ana fonksiyon"""
    try:
        # Dual AI Q&A sistemini başlat
        qa_system = DualAITefasQA()
        
        # Test modunu kontrol et
        if len(sys.argv) > 1:
            if sys.argv[1] == "--test":
                # AI test modu
                print(qa_system._handle_ai_test_question("AI test"))
            elif sys.argv[1] == "--demo":
                # Demo sorular
                demo_questions = [
                    "2025 için 50000 TL ile hangi fonları önerirsin?",
                    "AI test",
                    "Piyasa durumu nasıl?"
                ]
                
                for i, question in enumerate(demo_questions, 1):
                    print(f"\n[DEMO {i}] {question}")
                    print("-" * 40)
                    answer = qa_system.answer_question(question)
                    # İlk 500 karakter göster
                    preview = answer[:500] + "..." if len(answer) > 500 else answer
                    print(preview)
                    if i < len(demo_questions):
                        input("\nDevam etmek için Enter'a basın...")
            else:
                # Tek soru modu
                question = " ".join(sys.argv[1:])
                answer = qa_system.answer_question(question)
                print(answer)
        else:
            # İnteraktif mod
            qa_system.run_interactive_session()
            
    except Exception as e:
        print(f"❌ Dual AI sistem başlatma hatası: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()