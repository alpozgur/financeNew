# interactive_qa_dual_ai.py
"""
TEFAS Analysis System - Dual AI Q&A (OpenAI vs Ollama)
Her iki AI'ın da yanıt vermesi için güncellenmiş versiyon
"""
import time
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config.config import Config
from analysis.coordinator import AnalysisCoordinator
from analysis.hybrid_fund_selector import HybridFundSelector, HighPerformanceFundAnalyzer
import pandas as pd
from analysis.performance import batch_analyze_funds_by_details
# Mevcut import'ların altına ekleyin:
from analysis.hybrid_fund_selector import HybridFundSelector, HighPerformanceFundAnalyzer
from thematic_fund_analyzer import ThematicFundAnalyzer
from utils import normalize_turkish_text, extract_company_from_fund_name
from technical_analysis import TechnicalAnalysis
from performance_analysis import PerformanceAnalyzer

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
        self.technical_analyzer = TechnicalAnalysis(self.coordinator, self.active_funds)
        self.fundamental_analyzer = FundamentalAnalysisEnhancement(self.coordinator, self.active_funds)
        self.portfolio_analyzer = EnhancedPortfolioCompanyAnalyzer(self.coordinator)
        self.thematic_analyzer = ThematicFundAnalyzer(self.coordinator.db, self.config)
        self.performance_analyzer = PerformanceAnalyzer(self.coordinator, self.active_funds)
        # AI durumunu kontrol et
        self.ai_status = self._check_ai_availability()
        
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
        import re
        numbers_in_question = re.findall(r'(\d+)', question)
        requested_count = int(numbers_in_question[0]) if numbers_in_question else 1
        
        # GÜVENLİ FONLAR - ÇOKLU LİSTE DESTEĞİ
        if any(word in question_lower for word in ['en güvenli', 'en az riskli', 'güvenli fonlar']):
            # Eğer sayı belirtilmişse (örn: "en güvenli 10 fon") -> liste ver
            if requested_count > 1 or 'fonlar' in question_lower:
                return self.performance_analyzer.handle_safest_funds_sql_fast(requested_count)
            else:
                # Tek fon istiyorsa -> eski metodu kullan
                return self.performance_analyzer.handle_safest_fund()
        
        # RİSKLİ FONLAR - ÇOKLU LİSTE DESTEĞİ  
        if "en riskli" in question_lower:
            if requested_count > 1 or 'fonlar' in question_lower:
                return self.performance_analyzer.handle_riskiest_funds_list(requested_count)
            else:
                return self.performance_analyzer.handle_most_risky_fund()
        
        # EN ÇOK KAYBETTİREN - ÇOKLU LİSTE DESTEĞİ
        if any(word in question_lower for word in ['en çok kaybettiren', 'en çok düşen']):
            if requested_count > 1 or 'fonlar' in question_lower:
                return self.performance_analyzer.handle_worst_funds_list(requested_count)
            else:
                return self.performance_analyzer.handle_worst_fund()        
        # Özel risk sorusu yakalama
        if "en riskli" in question_lower:
            return self.performance_analyzer.handle_most_risky_fund()
        if "en güvenli" in question_lower or "en az riskli" in question_lower:
            return self.performance_analyzer.handle_safest_fund()
        if "en çok kaybettiren" in question_lower or "en çok düşen" in question_lower:
            return self.performance_analyzer.handle_worst_fund()

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
            return self.fundamental_analyzer._handle_capacity_questions(question)
        
        if any(word in question_lower for word in ['yatırımcı sayısı', 'popüler fon']):
            return self.fundamental_analyzer._handle_investor_count_questions(question)
        
        if any(word in question_lower for word in ['yeni fon', 'yeni kurulan']):
            return self.fundamental_analyzer._handle_new_funds_questions(question)
        
        if any(word in question_lower for word in ['en büyük', 'largest']):
            return self.fundamental_analyzer._handle_largest_funds_questions(question)
        
        if any(word in question_lower for word in ['en eski', 'köklü']):
            return self.fundamental_analyzer._handle_fund_age_questions(question)
        
        if any(word in question_lower for word in ['kategori', 'tür']):
            return self.fundamental_analyzer._handle_fund_category_questions(question)        
        # --- Gelişmiş anahtar kelime tabanlı analizler ---
        if any(word in question_lower for word in ['yatırım dağılımı', 'varlık dağılımı', 'kompozisyon', 'içerik', 'portföy içerik']):
            return self._handle_fund_allocation_question(question)
        if 'fon kategorisi' in question_lower or 'fon türü' in question_lower:
            return self._handle_fund_category_question(question)
        if any(word in question_lower for word in ['kazanç', 'getiri', 'son 1 yıl', 'son 12 ay', 'geçtiğimiz yıl', 'son yıl']):
            return self.performance_analyzer.handle_fund_past_performance_question(question)
        if 'en çok kazandıran' in question_lower or 'en çok getiri' in question_lower:
            return self.performance_analyzer.handle_top_gainer_fund_question(question)
        if 'düşüşte olan fonlar' in question_lower or 'en çok kaybettiren' in question_lower:
            return self.performance_analyzer.handle_top_loser_fund_question(question)
        if 'sharpe oranı en yüksek' in question_lower:
            return self.performance_analyzer.handle_top_sharpe_funds_question(question)
        if 'volatilite' in question_lower and 'altında' in question_lower:
            return self.performance_analyzer.handle_low_volatility_funds_question(question)
        # --- mevcut kalan kodun ---
        if any(word in question_lower for word in ['2025', 'öneri', 'öner', 'recommend', 'suggest']):
            return self.performance_analyzer.handle_2025_recommendation_dual(question)
        elif any(word in question_lower for word in ['analiz', 'analyze', 'performance']):
            return self.performance_analyzer.handle_analysis_question_dual(question)
        elif any(word in question_lower for word in ['karşılaştır', 'compare', 'vs']):
            return self.performance_analyzer.handle_comparison_question(question)
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

    def _handle_safest_funds_list_fallback(self, count=10):
        """Fallback: Hızlı Python versiyonu"""
        print(f"🛡️ Python fallback: En güvenli {count} fon...")
        
        safe_funds = []
        start_time = time.time()
        
        for fcode in self.active_funds:  # 50 fon
            try:
                # Kısa veri çek (20 gün)
                data = self.coordinator.db.get_fund_price_history(fcode, 20)
                
                if len(data) >= 10:
                    prices = data.set_index('pdate')['price'].sort_index()
                    returns = prices.pct_change().dropna()
                    
                    volatility = returns.std() * 100
                    total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                    
                    safe_funds.append({
                        'fcode': fcode,
                        'volatility': volatility,
                        'total_return': total_return,
                        'current_price': prices.iloc[-1]
                    })
                    
            except Exception:
                continue
        
        elapsed = time.time() - start_time
        print(f"   ✅ {len(safe_funds)} fon analiz edildi ({elapsed:.1f} saniye)")
        
        if not safe_funds:
            return "❌ Analiz edilebilir güvenli fon bulunamadı."
        
        # Volatiliteye göre sırala
        safe_funds.sort(key=lambda x: x['volatility'])
        top_funds = safe_funds[:count]
        
        # Fund details al
        for fund in top_funds:
            try:
                details = self.coordinator.db.get_fund_details(fund['fcode'])
                fund['fund_name'] = details.get('fund_name', 'N/A') if details else 'N/A'
                fund['fund_type'] = details.get('fund_type', 'N/A') if details else 'N/A'
            except:
                fund['fund_name'] = 'N/A'
                fund['fund_type'] = 'N/A'
        
        # Response oluştur
        response = f"\n🛡️ EN GÜVENLİ {count} FON (Python Fallback)\n"
        response += f"{'='*45}\n\n"
        response += f"📊 ANALİZ SONUCU:\n"
        response += f"   • Analiz Süresi: {elapsed:.1f} saniye\n"
        response += f"   • En Düşük Volatilite: %{top_funds[0]['volatility']:.2f}\n\n"
        
        for i, fund in enumerate(top_funds, 1):
            # Risk seviyesi
            if fund['volatility'] < 1:
                risk_level = "🟢 ÇOK GÜVENLİ"
            elif fund['volatility'] < 2:
                risk_level = "🟡 GÜVENLİ"
            elif fund['volatility'] < 4:
                risk_level = "🟠 ORTA"
            else:
                risk_level = "🔴 RİSKLİ"
            
            response += f"{i:2d}. {fund['fcode']} - {risk_level}\n"
            response += f"    📉 Volatilite: %{fund['volatility']:.2f}\n"
            response += f"    📈 Getiri: %{fund['total_return']:+.2f}\n"
            response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
            response += f"    🏷️ Tür: {fund['fund_type']}\n"
            response += f"\n"
        
        return response

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
    
    def _calculate_2025_score(self, annual_return, volatility, sharpe, win_rate, risk_tolerance):
        """2025 için özel skorlama"""
        score = 0
        
        # Getiri skoru (0-30)
        return_score = min(max(annual_return, 0) / 30 * 30, 30)
        score += return_score
        
        # Sharpe skoru (0-25)
        sharpe_score = min(max(sharpe, 0) * 10, 25)
        score += sharpe_score
        
        # Risk skoru (0-25)
        if risk_tolerance == "conservative":
            risk_score = max(25 - volatility, 0)
        elif risk_tolerance == "aggressive":
            risk_score = min(volatility / 2, 25)
        else:  # moderate
            risk_score = max(20 - abs(volatility - 20) / 2, 0)
        score += risk_score
        
        # Konsistans skoru (0-20)
        consistency_score = win_rate / 5
        score += consistency_score
        
        return max(min(score, 100), 0)
    
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

    def analyze_filtered_funds_example(self, fund_type=None, fund_category=None, days=252, top_n=5):
        """
        Example: Analyze and print top N funds by type/category.
        """
        print(f"\n[Batch Analysis] Filtering funds by: type={fund_type}, category={fund_category}")
        fund_details_df = self.coordinator.db.get_funds_with_details(fund_type=fund_type, fund_category=fund_category)
        if fund_details_df.empty:
            print("No funds found for the given filter.")
            return

        # Toplu analiz & skorla
        result_df = batch_analyze_funds_by_details(self.coordinator.db, fund_details_df, days=days, verbose=False)
        print(f"\nTop {top_n} funds (sorted by Sharpe ratio):")
        print(result_df.head(top_n)[["fcode", "fund_name", "fund_type", "fund_category", "sharpe_ratio", "annual_return"]])

        # AI prompt için ilk 5 fonu metinle göster
        prompt = ""
        for i, row in result_df.head(top_n).iterrows():
            prompt += (
                f"{row['fund_name']} ({row['fcode']}), Type: {row['fund_type']}, "
                f"Category: {row['fund_category']}, Sharpe: {row['sharpe_ratio']:.2f}, Return: {row['annual_return']:.2%}\n"
            )
        print("\nAI Prompt Example:\n", prompt)

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

class FundamentalAnalysisEnhancement:
    """Fundamental Analiz eklentisi - interactive_qa_dual_ai.py'ye entegre edilecek"""
    
    def __init__(self, coordinator, active_funds):
        self.coordinator = coordinator
        self.active_funds = active_funds
    
    # =============================================================
    # 2. HANDLER METODLARI - Mevcut sistemi kullanır
    # =============================================================

    def _handle_capacity_questions(self, question):
        """Kapasite analizi - GÜNCEL KAYITLARLA"""
        import re
        
        print("💰 Fon kapasitesi analiz ediliyor...")
        
        numbers = re.findall(r'(\d+(?:\.\d+)?)\s*(milyon|milyar|million|billion)', question.lower())
        
        if numbers:
            amount = float(numbers[0][0])
            unit = numbers[0][1]
            
            if unit in ['milyon', 'million']:
                threshold = amount * 1000000
            else:
                threshold = amount * 1000000000
            
            response = f"\n💰 FON KAPASİTE ANALİZİ - {amount:,.0f} {unit.upper()}\n"
            response += f"{'='*55}\n\n"
            response += f"🎯 Aranılan Eşik: {threshold:,.0f} TL\n\n"
            
            large_funds = []
            
            try:
                # 🔧 DÜZELTME: Her fon için en güncel kaydı al
                query = f"""
                WITH latest_records AS (
                    SELECT fcode, fcapacity, investorcount, price, pdate,
                        ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY pdate DESC) as rn
                    FROM tefasfunds 
                    WHERE fcapacity > {threshold}
                    AND pdate >= CURRENT_DATE - INTERVAL '7 days'
                )
                SELECT fcode, fcapacity, investorcount, price
                FROM latest_records 
                WHERE rn = 1
                ORDER BY fcapacity DESC
                LIMIT 20
                """
                
                result = self.coordinator.db.execute_query(query)
                print(f"   📊 SQL sorgusu: {len(result)} BENZERSIZ büyük fon bulundu")
                
                for _, row in result.iterrows():
                    fcode = row['fcode']
                    capacity = float(row['fcapacity'])
                    price = float(row['price']) if pd.notna(row['price']) else 0
                    investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                    
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                    
                    large_funds.append({
                        'fcode': fcode,
                        'capacity': capacity,
                        'current_price': price,
                        'investors': investors,
                        'fund_name': fund_name
                    })
                    
            except Exception as e:
                print(f"   ❌ SQL sorgu hatası: {e}")
                return f"❌ Kapasite analizi başarısız: {e}"
            
            # Sonuçları sırala
            large_funds.sort(key=lambda x: x['capacity'], reverse=True)
            
            if large_funds:
                response += f"🏆 BÜYÜK KAPASİTELİ FONLAR (Benzersiz - En Güncel):\n\n"
                
                for i, fund in enumerate(large_funds[:15], 1):
                    response += f"{i:2d}. {fund['fcode']}\n"
                    response += f"    💰 Kapasite: {fund['capacity']:,.0f} TL\n"
                    response += f"    💲 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
                    if fund['investors'] > 0:
                        response += f"    👥 Yatırımcı: {fund['investors']:,} kişi\n"
                    if fund['fund_name'] != 'N/A':
                        response += f"    📝 Adı: {fund['fund_name'][:50]}...\n"
                    response += f"\n"
                
                response += f"💡 NOT: Her fon sadece 1 kez gösteriliyor (en güncel verilerle)\n"
                
            else:
                response += f"❌ {threshold:,.0f} TL üstü kapasiteli fon bulunamadı.\n"
            
            return response
        
        else:
            return "❌ Kapasite değeri belirtilmedi. Örnek: 'Kapasitesi 500 milyon TL üstü fonlar'"

    def _handle_investor_count_questions(self, question):
        """Yatırımcı sayısı analizi - GÜNCEL KAYITLARLA DÜZELTILMIŞ"""
        import re
        
        print("👥 Yatırımcı sayısı analiz ediliyor...")
        
        # Sayısal değer çıkar
        numbers = re.findall(r'(\d+)', question)
        min_investors = int(numbers[0]) if numbers else 1000
        
        response = f"\n👥 YATIRIMCI SAYISI ANALİZİ\n"
        response += f"{'='*40}\n\n"
        response += f"🎯 Minimum Yatırımcı: {min_investors:,}\n\n"
        
        popular_funds = []
        
        # 🔧 DÜZELTME: Her fon için EN GÜNCEL kaydı al
        try:
            # OPTION 1: Window Function ile (en güvenilir)
            query = f"""
            WITH latest_records AS (
                SELECT fcode, investorcount, price, fcapacity, pdate,
                    ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY pdate DESC) as rn
                FROM tefasfunds 
                WHERE investorcount > {min_investors}
                AND pdate >= CURRENT_DATE - INTERVAL '7 days'
            )
            SELECT fcode, investorcount, price, fcapacity
            FROM latest_records 
            WHERE rn = 1
            ORDER BY investorcount DESC
            LIMIT 20
            """
            
            result = self.coordinator.db.execute_query(query)
            
            print(f"   📊 SQL sorgusu: {len(result)} BENZERSIZ fon bulundu")
            
            for _, row in result.iterrows():
                fcode = row['fcode']
                investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                price = float(row['price']) if pd.notna(row['price']) else 0
                capacity = float(row['fcapacity']) if pd.notna(row['fcapacity']) else 0
                
                # Fund details'den isim al
                details = self.coordinator.db.get_fund_details(fcode)
                fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                fund_type = details.get('fund_type', 'N/A') if details else 'N/A'
                
                popular_funds.append({
                    'fcode': fcode,
                    'investors': investors,
                    'fund_name': fund_name,
                    'fund_type': fund_type,
                    'current_price': price,
                    'capacity': capacity
                })
                
        except Exception as e:
            print(f"   ❌ Window function hatası: {e}")
            
            # FALLBACK: Basit güncel tarih sorgusu
            try:
                fallback_query = f"""
                SELECT fcode, investorcount, price, fcapacity
                FROM tefasfunds 
                WHERE investorcount > {min_investors}
                AND pdate = (SELECT MAX(pdate) FROM tefasfunds)
                ORDER BY investorcount DESC
                LIMIT 20
                """
                
                result = self.coordinator.db.execute_query(fallback_query)
                print(f"   📊 Fallback sorgusu: {len(result)} fon bulundu")
                
                for _, row in result.iterrows():
                    fcode = row['fcode']
                    investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                    price = float(row['price']) if pd.notna(row['price']) else 0
                    capacity = float(row['fcapacity']) if pd.notna(row['fcapacity']) else 0
                    
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                    fund_type = details.get('fund_type', 'N/A') if details else 'N/A'
                    
                    popular_funds.append({
                        'fcode': fcode,
                        'investors': investors,
                        'fund_name': fund_name,
                        'fund_type': fund_type,
                        'current_price': price,
                        'capacity': capacity
                    })
                    
            except Exception as e2:
                print(f"   ❌ Fallback de başarısız: {e2}")
                return "❌ Yatırımcı sayısı analizi yapılamadı - veritabanı hatası"
        
        # Yatırımcı sayısına göre sırala (Python'da da kontrol et)
        popular_funds.sort(key=lambda x: x['investors'], reverse=True)
        
        if popular_funds:
            response += f"🏆 EN POPÜLER FONLAR (Benzersiz Fonlar - En Güncel Veriler):\n\n"
            
            for i, fund in enumerate(popular_funds[:15], 1):  # İlk 15'i göster
                response += f"{i:2d}. {fund['fcode']}\n"
                response += f"    👥 Yatırımcı: {fund['investors']:,} kişi\n"
                response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
                if fund['capacity'] > 0:
                    response += f"    💰 Kapasite: {fund['capacity']:,.0f} TL\n"
                response += f"    🏷️ Tür: {fund['fund_type']}\n"
                if fund['fund_name'] != 'N/A':
                    response += f"    📝 Adı: {fund['fund_name'][:40]}...\n"
                response += f"\n"
            
            # İstatistikler
            total_investors = sum(f['investors'] for f in popular_funds)
            avg_investors = total_investors / len(popular_funds)
            
            response += f"📊 İSTATİSTİKLER (Benzersiz Fonlar):\n"
            response += f"   Bulunan Fon Sayısı: {len(popular_funds)}\n"
            response += f"   Toplam Yatırımcı: {total_investors:,}\n"
            response += f"   Ortalama: {avg_investors:,.0f}\n"
            response += f"   En Popüler: {popular_funds[0]['fcode']} ({popular_funds[0]['investors']:,} kişi)\n"
            
            # En büyük 3'ün detayı
            response += f"\n🥇 TOP 3 BENZERSIZ FONLAR:\n"
            for i, fund in enumerate(popular_funds[:3], 1):
                response += f"   {i}. {fund['fcode']}: {fund['investors']:,} yatırımcı\n"
            
            # Duplicate uyarısı
            response += f"\n💡 NOT: Artık her fon sadece 1 kez gösteriliyor (en güncel verilerle)\n"
            
        else:
            response += f"❌ {min_investors:,} üstü yatırımcısı olan fon bulunamadı.\n"
            response += f"💡 Daha düşük bir eşik deneyin (örn: {min_investors//2:,}).\n"
        
        return response

    def _handle_safest_funds_list(self, count=10, days=60):
        """En güvenli fonların listesi - HIZLANDIRILAN VERSİYON"""
        print(f"🛡️ En güvenli {count} fon analiz ediliyor...")
        
        safe_funds = []
        
        # 🚀 HIZLANDIRMA 1: Sadece active_funds kullan (1753 değil, 50 fon)
        print(f"   ⚡ {len(self.active_funds)} aktif fonu analiz ediliyor...")
        
        start_time = time.time()
        processed = 0
        
        for fcode in self.active_funds:  # Zaten optimize edilmiş 50 fon
            try:
                processed += 1
                if processed % 10 == 0:
                    elapsed = time.time() - start_time
                    print(f"   📊 {processed}/{len(self.active_funds)} işlendi ({elapsed:.1f}s)")
                
                # 🚀 HIZLANDIRMA 2: Daha az veri çek (60 gün yerine 30)
                data = self.coordinator.db.get_fund_price_history(fcode, 30)
                
                if len(data) >= 15:  # 15 gün yeterli
                    prices = data.set_index('pdate')['price'].sort_index()
                    returns = prices.pct_change().dropna()
                    
                    # 🚀 HIZLANDIRMA 3: Sadece temel metrikler
                    volatility = returns.std() * 100
                    total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                    
                    # 🚀 HIZLANDIRMA 4: Fund details'i sonradan al
                    safe_funds.append({
                        'fcode': fcode,
                        'volatility': volatility,
                        'total_return': total_return,
                        'current_price': prices.iloc[-1],
                        'data_points': len(prices)
                    })
                    
            except Exception:
                continue
        
        elapsed = time.time() - start_time
        print(f"   ✅ {len(safe_funds)} fon analiz edildi ({elapsed:.1f} saniye)")
        
        if not safe_funds:
            return f"❌ Analiz edilebilir güvenli fon bulunamadı."
        
        # Volatiliteye göre sırala
        safe_funds.sort(key=lambda x: x['volatility'])
        
        # 🚀 HIZLANDIRMA 5: Sadece top fonlar için fund details al
        top_funds = safe_funds[:count]
        
        for fund in top_funds:
            try:
                details = self.coordinator.db.get_fund_details(fund['fcode'])
                fund['fund_name'] = details.get('fund_name', 'N/A') if details else 'N/A'
                fund['fund_type'] = details.get('fund_type', 'N/A') if details else 'N/A'
            except:
                fund['fund_name'] = 'N/A'
                fund['fund_type'] = 'N/A'
        
        # Response oluştur
        response = f"\n🛡️ EN GÜVENLİ {count} FON (Son 30 Gün Volatilite)\n"
        response += f"{'='*50}\n\n"
        response += f"📊 ANALİZ SONUCU:\n"
        response += f"   • Analiz Edilen: {len(safe_funds)} fon\n"
        response += f"   • Analiz Süresi: {elapsed:.1f} saniye\n"
        response += f"   • En Düşük Volatilite: %{safe_funds[0]['volatility']:.2f}\n\n"
        
        response += f"🛡️ EN GÜVENLİ FONLAR:\n\n"
        
        for i, fund in enumerate(top_funds, 1):
            # Risk seviyesi
            if fund['volatility'] < 1:
                risk_level = "🟢 ÇOK GÜVENLİ"
            elif fund['volatility'] < 2:
                risk_level = "🟡 GÜVENLİ"
            elif fund['volatility'] < 4:
                risk_level = "🟠 ORTA"
            else:
                risk_level = "🔴 RİSKLİ"
            
            response += f"{i:2d}. {fund['fcode']} - {risk_level}\n"
            response += f"    📉 Volatilite: %{fund['volatility']:.2f}\n"
            response += f"    📈 Getiri: %{fund['total_return']:+.2f}\n"
            response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
            response += f"    🏷️ Tür: {fund['fund_type']}\n"
            response += f"\n"
        
        # Hızlı istatistikler
        avg_vol = sum(f['volatility'] for f in top_funds) / len(top_funds)
        avg_return = sum(f['total_return'] for f in top_funds) / len(top_funds)
        
        response += f"📊 ÖZEİ:\n"
        response += f"   Ortalama Volatilite: %{avg_vol:.2f}\n"
        response += f"   Ortalama Getiri: %{avg_return:+.2f}\n"
        response += f"   En Güvenli: {top_funds[0]['fcode']} (%{top_funds[0]['volatility']:.2f})\n"
        
        return response

    def _handle_new_funds_questions(self, question):
        """Yeni kurulan fonlar analizi"""
        from datetime import datetime, timedelta
        
        print("🆕 Yeni fonlar analiz ediliyor...")
        
        # Son 1 yıl içinde kurulan fonları bul
        cutoff_date = datetime.now() - timedelta(days=365)
        
        response = f"\n🆕 YENİ KURULAN FONLAR ANALİZİ\n"
        response += f"{'='*45}\n\n"
        response += f"📅 Arama Periyodu: Son 1 yıl ({cutoff_date.strftime('%d.%m.%Y')} sonrası)\n\n"
        
        new_funds = []
        
        for fcode in self.active_funds[:40]:
            try:
                # Fonun geçmiş verilerini al
                data = self.coordinator.db.get_fund_price_history(fcode, 400)
                
                if not data.empty:
                    # İlk veri tarihi = kuruluş tarihi (yaklaşık)
                    first_date = pd.to_datetime(data['pdate'].min())
                    
                    if first_date >= cutoff_date:
                        # Fund details'den bilgi al
                        details = self.coordinator.db.get_fund_details(fcode)
                        fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                        fund_type = details.get('fund_type', 'N/A') if details else 'N/A'
                        
                        # Performans hesapla
                        current_price = data['price'].iloc[-1]
                        first_price = data['price'].iloc[0]
                        performance = (current_price / first_price - 1) * 100
                        
                        new_funds.append({
                            'fcode': fcode,
                            'start_date': first_date,
                            'fund_name': fund_name,
                            'fund_type': fund_type,
                            'performance': performance,
                            'days_old': (datetime.now() - first_date).days,
                            'current_price': current_price
                        })
                        
            except Exception:
                continue
        
        # Tarihe göre sırala (en yeni önce)
        new_funds.sort(key=lambda x: x['start_date'], reverse=True)
        
        if new_funds:
            response += f"🚀 BULUNAN YENİ FONLAR ({len(new_funds)} adet):\n\n"
            
            for i, fund in enumerate(new_funds[:8], 1):
                days_old = fund['days_old']
                months_old = days_old / 30
                
                response += f"{i}. {fund['fcode']}\n"
                response += f"   📅 Kuruluş: {fund['start_date'].strftime('%d.%m.%Y')}\n"
                response += f"   ⏰ Yaş: {months_old:.1f} ay ({days_old} gün)\n"
                response += f"   📊 Performans: %{fund['performance']:+.2f}\n"
                response += f"   🏷️ Tür: {fund['fund_type']}\n"
                response += f"   💲 Fiyat: {fund['current_price']:.4f} TL\n"
                if fund['fund_name'] != 'N/A':
                    response += f"   📝 Adı: {fund['fund_name'][:35]}...\n"
                response += f"\n"
            
            # En iyi performans
            best_performer = max(new_funds, key=lambda x: x['performance'])
            response += f"🏆 EN İYİ YENİ FON PERFORMANSI:\n"
            response += f"   {best_performer['fcode']}: %{best_performer['performance']:+.2f}\n"
            
        else:
            response += f"❌ Son 1 yılda kurulan fon bulunamadı.\n"
            response += f"💡 Tüm fonlar 1 yıldan eski görünüyor.\n"
        
        return response

    def _handle_largest_funds_questions(self, question, count=None):
        """En büyük fonlar analizi - Kullanıcının istediği sayıda"""
        print("🏢 En büyük fonlar SQL analizi...")
        
        # Kullanıcının istediği sayıyı tespit et
        import re
        numbers_in_question = re.findall(r'(\d+)', question)
        requested_count = int(numbers_in_question[0]) if numbers_in_question else 10
        
        # SQL için biraz fazla çek (filtering için)
        sql_limit = max(requested_count * 2, 20)
        
        try:
            # SQL ile en büyük fonları bul - JOIN ile her iki tablodan veri çek
            query = f'''
            WITH latest_data AS (
                SELECT f.fcode, f.fcapacity, f.investorcount, f.price, f.pdate,
                    f.ftitle as fund_name, null as fund_type,
                    ROW_NUMBER() OVER (PARTITION BY f.fcode ORDER BY f.pdate DESC) as rn
                FROM tefasfunds f
                LEFT JOIN tefasfunddetails d ON f.fcode = d.fcode
                WHERE f.fcapacity > 1000000  -- En az 1M TL
                AND f.investorcount > 100    -- En az 100 yatırımcı
                AND f.pdate >= CURRENT_DATE - INTERVAL '7 days'
            )
            SELECT fcode, fcapacity, investorcount, price, fund_name, fund_type
            FROM latest_data 
            WHERE rn = 1
            ORDER BY fcapacity DESC
            LIMIT {sql_limit}
            '''
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                # Fallback: Eşiği düşür
                print("   💡 Yüksek eşikle sonuç yok, eşik düşürülüyor...")
                
                fallback_query = f'''
                WITH latest_data AS (
                    SELECT f.fcode, f.fcapacity, f.investorcount, f.price,
                        f.ftitle as fund_name, null as fund_type,
                        ROW_NUMBER() OVER (PARTITION BY f.fcode ORDER BY f.pdate DESC) as rn
                    FROM tefasfunds f
                    LEFT JOIN tefasfunddetails d ON f.fcode = d.fcode
                    WHERE f.fcapacity > 100000   -- En az 100K TL
                    AND f.pdate >= CURRENT_DATE - INTERVAL '14 days'
                )
                SELECT fcode, fcapacity, investorcount, price, fund_name, fund_type
                FROM latest_data 
                WHERE rn = 1
                ORDER BY fcapacity DESC
                LIMIT {sql_limit}
                '''
                
                result = self.coordinator.db.execute_query(fallback_query)
                
            if result.empty:
                return f"❌ En büyük {requested_count} fon verisi bulunamadı - veritabanında kapasite bilgisi eksik olabilir."
            
            # Sadece kullanıcının istediği sayıda al
            result = result.head(requested_count)
            
            print(f"   ✅ {len(result)} büyük fon bulundu (istenen: {requested_count})")
            
            response = f"\n🏢 EN BÜYÜK {requested_count} FON (Kapasite Bazlı)\n"
            response += f"{'='*45}\n\n"
            response += f"📊 ANALİZ SONUCU:\n"
            response += f"   • İstenen Fon Sayısı: {requested_count}\n"
            response += f"   • Bulunan Fon: {len(result)}\n"
            response += f"   • En Büyük Kapasite: {result.iloc[0]['fcapacity']:,.0f} TL\n\n"
            
            for i, (_, row) in enumerate(result.iterrows(), 1):
                fcode = row['fcode']
                capacity = float(row['fcapacity'])
                investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                price = float(row['price']) if pd.notna(row['price']) else 0
                fund_name = row['fund_name'] if pd.notna(row['fund_name']) else 'N/A'
                fund_type = row['fund_type'] if pd.notna(row['fund_type']) else 'N/A'
                
                # Kapasiteyi okunabilir formatta göster
                if capacity >= 1000000000:  # 1 milyar+
                    capacity_text = f"{capacity/1000000000:.1f} milyar TL"
                elif capacity >= 1000000:  # 1 milyon+
                    capacity_text = f"{capacity/1000000:.0f} milyon TL"
                else:
                    capacity_text = f"{capacity:,.0f} TL"
                
                response += f"{i:2d}. {fcode}\n"
                response += f"    💰 Kapasite: {capacity_text}\n"
                response += f"    👥 Yatırımcı: {investors:,} kişi\n"
                response += f"    💲 Güncel Fiyat: {price:.4f} TL\n"
                response += f"    🏷️ Tür: {fund_type}\n"
                if fund_name != 'N/A':
                    response += f"    📝 Adı: {fund_name[:45]}...\n"
                response += f"\n"
            
            # En büyük 3'ün özeti (veya daha az varsa hepsini göster)
            top_count = min(3, len(result))
            response += f"🏆 TOP {top_count} ÖZET:\n"
            for i, (_, row) in enumerate(result.head(top_count).iterrows(), 1):
                capacity_billion = row['fcapacity'] / 1000000000
                if capacity_billion >= 1:
                    response += f"   {i}. {row['fcode']}: {capacity_billion:.1f} milyar TL\n"
                else:
                    response += f"   {i}. {row['fcode']}: {row['fcapacity']/1000000:.0f} milyon TL\n"
            
            # İstatistikler
            total_capacity = result['fcapacity'].sum()
            avg_capacity = result['fcapacity'].mean()
            total_investors = result['investorcount'].sum()
            
            response += f"\n📊 {requested_count} FON İSTATİSTİKLERİ:\n"
            response += f"   Toplam Kapasite: {total_capacity/1000000000:.1f} milyar TL\n"
            response += f"   Ortalama Kapasite: {avg_capacity/1000000:.0f} milyon TL\n"
            response += f"   Toplam Yatırımcı: {total_investors:,} kişi\n"
            
            return response
            
        except Exception as e:
            print(f"   ❌ SQL analizi hatası: {e}")
            return f"❌ SQL analizi hatası: {e}\n💡 Veritabanı şemasını kontrol edin - fcapacity kolonu mevcut mu?"
    
    def _handle_fund_age_questions(self, question):
        """Fon yaşı analizi"""
        print("⏰ Fon yaşları analiz ediliyor...")
        
        response = f"\n⏰ EN ESKİ/KÖKLÜ FONLAR ANALİZİ\n"
        response += f"{'='*40}\n\n"
        
        fund_ages = []
        
        for fcode in self.active_funds[:40]:
            try:
                # En eski veriyi bul
                data = self.coordinator.db.get_fund_price_history(fcode, 2000)  # Maksimum veri
                
                if not data.empty:
                    oldest_date = pd.to_datetime(data['pdate'].min())
                    newest_date = pd.to_datetime(data['pdate'].max())
                    
                    # Yaş hesapla
                    fund_age_days = (datetime.now() - oldest_date).days
                    fund_age_years = fund_age_days / 365.25
                    
                    # Fund details
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                    
                    # Performans (tüm zamanlar)
                    first_price = data['price'].iloc[0]
                    last_price = data['price'].iloc[-1]
                    total_performance = (last_price / first_price - 1) * 100
                    
                    fund_ages.append({
                        'fcode': fcode,
                        'start_date': oldest_date,
                        'age_years': fund_age_years,
                        'age_days': fund_age_days,
                        'fund_name': fund_name,
                        'total_performance': total_performance,
                        'current_price': last_price,
                        'data_points': len(data)
                    })
                    
            except Exception:
                continue
        
        # Yaşa göre sırala (en eski önce)
        fund_ages.sort(key=lambda x: x['age_years'], reverse=True)
        
        if fund_ages:
            response += f"🏛️ EN ESKİ/KÖKLÜ FONLAR:\n\n"
            
            for i, fund in enumerate(fund_ages[:8], 1):
                response += f"{i}. {fund['fcode']}\n"
                response += f"   📅 Kuruluş: {fund['start_date'].strftime('%d.%m.%Y')}\n"
                response += f"   ⏰ Yaş: {fund['age_years']:.1f} yıl ({fund['age_days']:,} gün)\n"
                response += f"   📊 Toplam Performans: %{fund['total_performance']:+.1f}\n"
                response += f"   📈 Veri Noktası: {fund['data_points']:,}\n"
                response += f"   💲 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
                if fund['fund_name'] != 'N/A':
                    response += f"   📝 Adı: {fund['fund_name'][:35]}...\n"
                response += f"\n"
            
            # İstatistikler
            avg_age = sum(f['age_years'] for f in fund_ages) / len(fund_ages)
            oldest_fund = fund_ages[0]
            
            response += f"📊 YAŞ İSTATİSTİKLERİ:\n"
            response += f"   Ortalama Yaş: {avg_age:.1f} yıl\n"
            response += f"   En Eski Fon: {oldest_fund['fcode']} ({oldest_fund['age_years']:.1f} yıl)\n"
            response += f"   En Başarılı Eski Fon: {max(fund_ages, key=lambda x: x['total_performance'])['fcode']}\n"
            
        else:
            response += f"❌ Fon yaşı verileri alınamadı.\n"
        
        return response

    def _handle_fund_category_questions(self, question):
        """Fon kategori/tür analizi"""
        print("🏷️ Fon kategorileri analiz ediliyor...")
        
        response = f"\n🏷️ FON KATEGORİ/TÜR ANALİZİ\n"
        response += f"{'='*40}\n\n"
        
        categories = {}
        fund_types = {}
        
        for fcode in self.active_funds[:50]:
            try:
                details = self.coordinator.db.get_fund_details(fcode)
                
                if details:
                    category = details.get('fund_category', 'Bilinmiyor')
                    fund_type = details.get('fund_type', 'Bilinmiyor')
                    
                    # Kategori sayımı
                    if category in categories:
                        categories[category].append(fcode)
                    else:
                        categories[category] = [fcode]
                    
                    # Tür sayımı
                    if fund_type in fund_types:
                        fund_types[fund_type].append(fcode)
                    else:
                        fund_types[fund_type] = [fcode]
                        
            except Exception:
                continue
        
        # Kategorileri sırala
        sorted_categories = sorted(categories.items(), key=lambda x: len(x[1]), reverse=True)
        sorted_types = sorted(fund_types.items(), key=lambda x: len(x[1]), reverse=True)
        
        response += f"📊 FON KATEGORİLERİ (En Popüler → En Az):\n\n"
        
        for i, (category, funds) in enumerate(sorted_categories[:8], 1):
            response += f"{i:2d}. {category}\n"
            response += f"    📊 Fon Sayısı: {len(funds)}\n"
            response += f"    📝 Örnek Fonlar: {', '.join(funds[:3])}\n"
            response += f"\n"
        
        response += f"🏷️ FON TÜRLERİ:\n\n"
        
        for i, (fund_type, funds) in enumerate(sorted_types[:6], 1):
            response += f"{i}. {fund_type}: {len(funds)} fon\n"
        
        response += f"\n📈 DAĞILIM İSTATİSTİKLERİ:\n"
        response += f"   Toplam Kategori: {len(categories)}\n"
        response += f"   Toplam Tür: {len(fund_types)}\n"
        response += f"   En Popüler Kategori: {sorted_categories[0][0]} ({len(sorted_categories[0][1])} fon)\n"
        
        return response

    def _capacity_help_message(self):
        """Kapasite sorusu için yardım mesajı"""
        return f"""
❌ Kapasite değeri belirtilmedi!

💡 ÖRNEK KULLANIM:
   • "Kapasitesi 500 milyon TL üstü fonlar"
   • "1 milyar TL üzerinde fon var mı?"
   • "Büyüklüğü 100 milyon üstü fonları listele"

📝 DESTEKLENENLER:
   • milyon/million
   • milyar/billion  
   • Sayısal değerler (100, 500, 1.5 vb.)
"""
class EnhancedPortfolioCompanyAnalyzer:
    """Gelişmiş Portföy Şirketi Analiz Sistemi"""
    
    def __init__(self, coordinator):
        self.coordinator = coordinator
        
        # 🎯 GELİŞTİRİLMİŞ Şirket keyword mapping
        self.company_keywords = {
            'İş Portföy': ['İŞ PORTFÖY', 'IS PORTFOY', 'ISBANK PORTFOY'],
            'Ak Portföy': ['AK PORTFÖY', 'AKBANK PORTFÖY', 'AKPORTFOY'],
            'Garanti Portföy': ['GARANTİ PORTFÖY', 'GARANTI PORTFOY', 'GARANTIBANK'],
            'Ata Portföy': ['ATA PORTFÖY', 'ATA PORTFOY'],
            'QNB Portföy': ['QNB PORTFÖY', 'QNB PORTFOY', 'FINANSBANK'],
            'Fiba Portföy': ['FİBA PORTFÖY', 'FIBA PORTFOY', 'FIBABANK'],
            'Yapı Kredi Portföy': ['YAPI KREDİ PORTFÖY', 'YKB PORTFÖY', 'YAPIKREDI'],
            'TEB Portföy': ['TEB PORTFÖY', 'TEB PORTFOY'],
            'Deniz Portföy': ['DENİZ PORTFÖY', 'DENIZ PORTFOY', 'DENIZBANK'],
            'Ziraat Portföy': ['ZİRAAT PORTFÖY', 'ZIRAAT PORTFOY', 'ZIRAATBANK'],
            'Halk Portföy': ['HALK PORTFÖY', 'HALK PORTFOY', 'HALKBANK'],
            'İstanbul Portföy': ['İSTANBUL PORTFÖY', 'ISTANBUL PORTFOY'],
            'Vakıf Portföy': ['VAKIF PORTFÖY', 'VAKIFBANK PORTFÖY'],
            'ICBC Turkey Portföy': ['ICBC', 'INDUSTRIAL'],
            'Bizim Portföy': ['BİZİM PORTFÖY', 'BIZIM PORTFOY'],
            'Tacirler Portföy': ['TACİRLER PORTFÖY', 'TACIRLER'],
            'Gedik Portföy': ['GEDİK PORTFÖY', 'GEDIK'],
            'Info Portföy': ['INFO PORTFÖY', 'INFORMATICS'],
            'Marmara Portföy': ['MARMARA PORTFÖY', 'MARMARA'],
            'Kare Portföy': ['KARE PORTFÖY', 'KARE'],
            'Strateji Portföy': ['STRATEJİ PORTFÖY', 'STRATEJI'],
            'Global Portföy': ['GLOBAL PORTFÖY', 'GLOBAL MD'],
            'Azimut Portföy': ['AZİMUT PORTFÖY', 'AZIMUT'],
            'ING Portföy': ['ING PORTFÖY', 'ING BANK']
        }
    
    def get_all_company_funds_unlimited(self, company_name):
        """Şirketin TÜM fonlarını bul - LİMİTSİZ"""
        print(f"🔍 {company_name} - TÜM fonları aranıyor (limitsiz)...")
        
        try:
            company_funds = []
            keywords = self.company_keywords.get(company_name, [])
            
            if not keywords:
                print(f"   ⚠️ {company_name} için keyword bulunamadı")
                return []
            
            for keyword in keywords:
                try:
                    # 🚀 LİMİTSİZ SORGU - Tüm fonları bul
                    query = f"""
                    WITH latest_data AS (
                        SELECT DISTINCT f.fcode, f.ftitle, f.fcapacity, f.investorcount, f.price, f.pdate,
                            ROW_NUMBER() OVER (PARTITION BY f.fcode ORDER BY f.pdate DESC) as rn
                        FROM tefasfunds f
                        WHERE UPPER(f.ftitle) LIKE '%{keyword}%'
                        AND f.pdate >= CURRENT_DATE - INTERVAL '30 days'
                        AND f.price > 0
                    )
                    SELECT fcode, ftitle as fund_name, fcapacity, investorcount, price
                    FROM latest_data 
                    WHERE rn = 1
                    ORDER BY fcapacity DESC NULLS LAST
                    """
                    
                    result = self.coordinator.db.execute_query(query)
                    
                    for _, row in result.iterrows():
                        fund_info = {
                            'fcode': row['fcode'],
                            'fund_name': row['fund_name'],
                            'capacity': float(row['fcapacity']) if pd.notna(row['fcapacity']) else 0,
                            'investors': int(row['investorcount']) if pd.notna(row['investorcount']) else 0,
                            'current_price': float(row['price']) if pd.notna(row['price']) else 0
                        }
                        
                        # Duplicate kontrolü
                        if not any(f['fcode'] == fund_info['fcode'] for f in company_funds):
                            company_funds.append(fund_info)
                            
                except Exception as e:
                    print(f"   ⚠️ Keyword '{keyword}' sorgu hatası: {e}")
                    continue
            
            print(f"   ✅ {len(company_funds)} FON BULUNDU")
            return company_funds
            
        except Exception as e:
            print(f"   ❌ Genel hata: {e}")
            return []

    def calculate_comprehensive_performance(self, fund_code, days=252):
        """Kapsamlı performans hesaplama - INF ve NaN hatalarını düzeltilmiş"""
        try:
            # Veri çekimi
            data = self.coordinator.db.get_fund_price_history(fund_code, days)
            
            if len(data) < 10:
                return None
            
            prices = data.set_index('pdate')['price'].sort_index()
            returns = prices.pct_change().dropna()
            
            # ❌ HATA KAYNAĞI: İlk veya son fiyat 0 veya NaN olabilir
            first_price = prices.iloc[0]
            last_price = prices.iloc[-1]
            
            # 🔧 DÜZELTİLMİŞ: Sıfır kontrolü ekle
            if first_price <= 0 or last_price <= 0 or pd.isna(first_price) or pd.isna(last_price):
                print(f"   ⚠️ {fund_code} geçersiz fiyat verisi: başlangıç={first_price}, son={last_price}")
                return None
            
            # Temel metrikler - güvenli hesaplama
            total_return = (last_price / first_price - 1) * 100
            
            # ❌ HATA KAYNAĞI: returns.std() NaN olabilir
            returns_std = returns.std()
            if pd.isna(returns_std) or returns_std == 0:
                print(f"   ⚠️ {fund_code} volatilite hesaplanamadı")
                return None
            
            annual_return = total_return * (252 / len(prices))
            volatility = returns_std * np.sqrt(252) * 100
            
            # 🔧 DÜZELTİLMİŞ: Sharpe ratio hesaplama
            if volatility > 0 and not pd.isna(volatility):
                sharpe = (annual_return - 15) / volatility
            else:
                sharpe = 0
            
            win_rate = (returns > 0).sum() / len(returns) * 100
            
            # Max drawdown hesaplama - güvenli
            try:
                cumulative = (1 + returns).cumprod()
                running_max = cumulative.expanding().max()
                drawdown = (cumulative - running_max) / running_max
                max_drawdown = abs(drawdown.min()) * 100
                
                # NaN kontrolü
                if pd.isna(max_drawdown):
                    max_drawdown = 0
                    
            except Exception:
                max_drawdown = 0
            
            # Calmar ratio - güvenli
            if max_drawdown > 0 and not pd.isna(max_drawdown):
                calmar = abs(annual_return / max_drawdown)
            else:
                calmar = 0
            
            # Sortino ratio - güvenli
            negative_returns = returns[returns < 0]
            if len(negative_returns) > 0:
                downside_std = negative_returns.std()
                if not pd.isna(downside_std) and downside_std > 0:
                    downside_deviation = downside_std * np.sqrt(252) * 100
                    sortino = (annual_return - 15) / downside_deviation
                else:
                    sortino = 0
            else:
                sortino = 0
            
            # 🔧 DÜZELTİLMİŞ: Tüm değerlerin geçerliliğini kontrol et
            result = {
                'total_return': total_return,
                'annual_return': annual_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe,
                'sortino_ratio': sortino,
                'calmar_ratio': calmar,
                'win_rate': win_rate,
                'max_drawdown': max_drawdown,
                'data_points': len(prices),
                'current_price': last_price
            }
            
            # Infinity ve NaN temizleme
            for key, value in result.items():
                if pd.isna(value) or np.isinf(value):
                    print(f"   ⚠️ {fund_code} {key} değeri geçersiz: {value}")
                    if key in ['sharpe_ratio', 'sortino_ratio', 'calmar_ratio']:
                        result[key] = 0
                    elif key in ['volatility', 'max_drawdown']:
                        result[key] = 0
                    else:
                        result[key] = 0
            
            return result
            
        except Exception as e:
            print(f"   ❌ {fund_code} performans hatası: {e}")
            return None
    
    def analyze_company_comprehensive(self, company_name, analysis_days=252):
        """Şirket kapsamlı analizi - TÜM FONLARLA"""
        print(f"\n🏢 {company_name.upper()} - KAPSAMLI ANALİZ BAŞLATIYOR...")
        print("="*60)
        
        start_time = time.time()
        
        # 1. TÜM FONLARI BUL
        company_funds = self.get_all_company_funds_unlimited(company_name)
        
        if not company_funds:
            return f"❌ {company_name} fonları bulunamadı."
        
        print(f"📊 BULUNAN FONLAR: {len(company_funds)}")
        print(f"📅 ANALİZ PERİYODU: {analysis_days} gün")
        
        # 2. HER FON İÇİN DETAYLI PERFORMANS ANALİZİ
        print(f"\n🔍 PERFORMANS ANALİZİ BAŞLATIYOR...")
        
        performance_results = []
        successful_analysis = 0
        
        for i, fund_info in enumerate(company_funds, 1):
            fcode = fund_info['fcode']
            print(f"   [{i}/{len(company_funds)}] {fcode}...", end='')
            
            perf = self.calculate_comprehensive_performance(fcode, analysis_days)
            
            if perf:
                fund_result = {
                    'fcode': fcode,
                    'fund_name': fund_info['fund_name'],
                    'capacity': fund_info['capacity'],
                    'investors': fund_info['investors'],
                    **perf  # Performans metriklerini ekle
                }
                performance_results.append(fund_result)
                successful_analysis += 1
                print(f" ✅ ({perf['annual_return']:+.1f}%)")
            else:
                print(f" ❌")
        
        elapsed = time.time() - start_time
        print(f"\n⏱️ ANALİZ TAMAMLANDI: {elapsed:.1f} saniye")
        print(f"✅ BAŞARILI: {successful_analysis}/{len(company_funds)} fon")
        
        if not performance_results:
            return f"❌ {company_name} için performans verisi hesaplanamadı."
        
        # 3. SONUÇLARI FORMATLA
        return self.format_company_analysis_results(company_name, performance_results, elapsed)

    def format_company_analysis_results(self, company_name, results, analysis_time):
        """Analiz sonuçlarını formatla - INF/NaN güvenli"""
        
        # Sonuçları Sharpe ratio'ya göre sırala
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        
        response = f"\n🏢 {company_name.upper()} - KAPSAMLI ANALİZ RAPORU\n"
        response += f"{'='*55}\n\n"
        
        # ÖZET İSTATİSTİKLER - güvenli hesaplama
        total_funds = len(results)
        total_capacity = sum(r['capacity'] for r in results)
        total_investors = sum(r['investors'] for r in results)
        
        # 🔧 DÜZELTİLMİŞ: INF ve NaN değerleri filtrele
        valid_returns = [r['annual_return'] for r in results if not (pd.isna(r['annual_return']) or np.isinf(r['annual_return']))]
        valid_sharpes = [r['sharpe_ratio'] for r in results if not (pd.isna(r['sharpe_ratio']) or np.isinf(r['sharpe_ratio']))]
        valid_volatilities = [r['volatility'] for r in results if not (pd.isna(r['volatility']) or np.isinf(r['volatility']))]
        
        avg_return = sum(valid_returns) / len(valid_returns) if valid_returns else 0
        avg_sharpe = sum(valid_sharpes) / len(valid_sharpes) if valid_sharpes else 0
        avg_volatility = sum(valid_volatilities) / len(valid_volatilities) if valid_volatilities else 0
        
        response += f"📊 ŞİRKET GENEL İSTATİSTİKLERİ:\n"
        response += f"   🔢 Toplam Fon Sayısı: {total_funds}\n"
        response += f"   💰 Toplam Varlık: {total_capacity:,.0f} TL ({total_capacity/1000000000:.1f} milyar)\n"
        response += f"   👥 Toplam Yatırımcı: {total_investors:,} kişi\n"
        response += f"   📈 Ortalama Yıllık Getiri: %{avg_return:+.2f}\n"
        response += f"   ⚡ Ortalama Sharpe Oranı: {avg_sharpe:.3f}\n"
        response += f"   📊 Ortalama Volatilite: %{avg_volatility:.2f}\n"
        response += f"   ⏱️ Analiz Süresi: {analysis_time:.1f} saniye\n"
        response += f"   📊 Geçerli Veri: {len(valid_returns)}/{total_funds} fon\n\n"
        
        # EN İYİ PERFORMANS FONLARI (TOP 10) - geçerli veriler
        valid_results = [r for r in results if not (pd.isna(r['sharpe_ratio']) or np.isinf(r['sharpe_ratio']))]
        
        response += f"🏆 EN İYİ PERFORMANS FONLARI (Sharpe Oranına Göre):\n\n"
        
        for i, fund in enumerate(valid_results[:10], 1):
            # Performance tier belirleme
            if fund['sharpe_ratio'] > 1.0:
                tier = "🌟 MÜKEMMEL"
            elif fund['sharpe_ratio'] > 0.5:
                tier = "⭐ ÇOK İYİ"
            elif fund['sharpe_ratio'] > 0:
                tier = "🔶 İYİ"
            elif fund['sharpe_ratio'] > -0.5:
                tier = "🔸 ORTA"
            else:
                tier = "🔻 ZAYIF"
            
            response += f"{i:2d}. {fund['fcode']} - {tier}\n"
            response += f"    📈 Yıllık Getiri: %{fund['annual_return']:+.2f}\n"
            response += f"    ⚡ Sharpe Oranı: {fund['sharpe_ratio']:.3f}\n"
            response += f"    📊 Volatilite: %{fund['volatility']:.2f}\n"
            response += f"    🎯 Kazanma Oranı: %{fund['win_rate']:.1f}\n"
            response += f"    📉 Max Düşüş: %{fund['max_drawdown']:.2f}\n"
            response += f"    💰 Kapasite: {fund['capacity']:,.0f} TL\n"
            response += f"    👥 Yatırımcı: {fund['investors']:,} kişi\n"
            response += f"    💲 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
            response += f"    📝 Adı: {fund['fund_name'][:45]}...\n"
            response += f"\n"
        
        # KATEGORİ LİDERLERİ - güvenli
        if valid_results:
            # En yüksek getiri - INF olmayan
            best_return_fund = max(valid_results, key=lambda x: x['annual_return'] if not np.isinf(x['annual_return']) else -999)
            best_sharpe_fund = max(valid_results, key=lambda x: x['sharpe_ratio'])
            lowest_vol_fund = min(valid_results, key=lambda x: x['volatility'] if x['volatility'] > 0 else 999)
            
            response += f"🏅 KATEGORİ LİDERLERİ:\n"
            response += f"   🥇 En Yüksek Getiri: {best_return_fund['fcode']} (%{best_return_fund['annual_return']:+.1f})\n"
            response += f"   🛡️ En Düşük Risk: {lowest_vol_fund['fcode']} (%{lowest_vol_fund['volatility']:.1f})\n"
            response += f"   ⚡ En Yüksek Sharpe: {best_sharpe_fund['fcode']} ({best_sharpe_fund['sharpe_ratio']:.3f})\n"
            response += f"   💰 En Büyük Fon: {max(results, key=lambda x: x['capacity'])['fcode']} ({max(results, key=lambda x: x['capacity'])['capacity']/1000000:.0f}M TL)\n"
            response += f"   👥 En Popüler: {max(results, key=lambda x: x['investors'])['fcode']} ({max(results, key=lambda x: x['investors'])['investors']:,} kişi)\n"
        
        # PERFORMANCE DAĞILIMI - geçerli verilerle
        if valid_results:
            excellent_funds = len([f for f in valid_results if f['sharpe_ratio'] > 1.0])
            good_funds = len([f for f in valid_results if 0.5 < f['sharpe_ratio'] <= 1.0])
            average_funds = len([f for f in valid_results if 0 < f['sharpe_ratio'] <= 0.5])
            poor_funds = len([f for f in valid_results if f['sharpe_ratio'] <= 0])
            
            response += f"\n📊 PERFORMANS DAĞILIMI:\n"
            response += f"   🌟 Mükemmel (Sharpe>1.0): {excellent_funds} fon (%{excellent_funds/len(valid_results)*100:.1f})\n"
            response += f"   ⭐ Çok İyi (0.5-1.0): {good_funds} fon (%{good_funds/len(valid_results)*100:.1f})\n"
            response += f"   🔶 İyi (0-0.5): {average_funds} fon (%{average_funds/len(valid_results)*100:.1f})\n"
            response += f"   🔻 Zayıf (≤0): {poor_funds} fon (%{poor_funds/len(valid_results)*100:.1f})\n"
        
        # GENEL DEĞERLENDİRME
        if avg_sharpe > 0.5:
            overall_rating = "🌟 MÜKEMMEL"
        elif avg_sharpe > 0.2:
            overall_rating = "⭐ ÇOK İYİ"
        elif avg_sharpe > 0:
            overall_rating = "🔶 İYİ"
        elif avg_sharpe > -0.2:
            overall_rating = "🔸 ORTA"
        else:
            overall_rating = "🔻 ZAYIF"
        
        response += f"\n🎯 GENEL DEĞERLENDİRME: {overall_rating}\n"
        response += f"   Ortalama Sharpe {avg_sharpe:.3f} ile {company_name} "
        
        if avg_sharpe > 0.3:
            response += "güçlü performans sergiliyor.\n"
        elif avg_sharpe > 0:
            response += "makul bir performans gösteriyor.\n"
        else:
            response += "performansını iyileştirmesi gerekiyor.\n"
        
        # VERİ KALİTESİ UYARISI
        invalid_count = total_funds - len(valid_results)
        if invalid_count > 0:
            response += f"\n⚠️ VERİ KALİTESİ NOTU:\n"
            response += f"   {invalid_count} fon geçersiz veri nedeniyle hariç tutuldu\n"
            response += f"   (INF, NaN veya sıfır değerler içeren fonlar)\n"
        
        return response

    def compare_companies_unlimited(self, company1, company2, analysis_days=252):
        """İki şirketi kapsamlı karşılaştır - LİMİTSİZ"""
        print(f"\n⚖️ {company1} vs {company2} - KAPSAMLI KARŞILAŞTIRMA")
        print("="*65)
        
        # Her iki şirket için analiz
        results1 = self.analyze_company_detailed_data(company1, analysis_days)
        results2 = self.analyze_company_detailed_data(company2, analysis_days)
        
        if not results1['success'] or not results2['success']:
            return f"❌ Karşılaştırma için yeterli veri yok."
        
        response = f"\n⚖️ {company1.upper()} vs {company2.upper()} - DETAYLI KARŞILAŞTIRMA\n"
        response += f"{'='*70}\n\n"
        
        # GENEL İSTATİSTİKLER KARŞILAŞTIRMASI
        metrics = [
            ('Fon Sayısı', 'total_funds', 'adet', 'higher'),
            ('Toplam Varlık', 'total_capacity', 'milyar TL', 'higher'), 
            ('Ortalama Getiri', 'avg_return', '%', 'higher'),
            ('Ortalama Sharpe', 'avg_sharpe', '', 'higher'),
            ('Ortalama Risk', 'avg_volatility', '%', 'lower'),
            ('Toplam Yatırımcı', 'total_investors', 'K kişi', 'higher')
        ]
        
        response += f"📊 GENEL KARŞILAŞTIRMA:\n\n"
        response += f"{'Metrik':<15} | {company1:<15} | {company2:<15} | Kazanan\n"
        response += f"{'-'*15}|{'-'*16}|{'-'*16}|{'-'*15}\n"
        
        score1 = 0
        score2 = 0
        
        for metric_name, key, unit, better in metrics:
            val1 = results1['stats'][key]
            val2 = results2['stats'][key]
            
            # Değer formatlama
            if 'milyar' in unit:
                val1_display = f"{val1/1000000000:.1f}"
                val2_display = f"{val2/1000000000:.1f}"
            elif 'K kişi' in unit:
                val1_display = f"{val1/1000:.0f}"
                val2_display = f"{val2/1000:.0f}"
            elif '%' in unit:
                val1_display = f"{val1:+.1f}"
                val2_display = f"{val2:+.1f}"
            else:
                val1_display = f"{val1:.2f}"
                val2_display = f"{val2:.2f}"
            
            # Kazanan belirleme
            if better == 'higher':
                winner = company1 if val1 > val2 else company2
                if val1 > val2:
                    score1 += 1
                else:
                    score2 += 1
            else:  # lower is better (risk)
                winner = company1 if val1 < val2 else company2
                if val1 < val2:
                    score1 += 1
                else:
                    score2 += 1
            
            response += f"{metric_name:<15} | {val1_display:<15} | {val2_display:<15} | 🏆 {winner}\n"
        
        # GENEL SKOR
        response += f"\n🏆 GENEL SKOR: {company1} {score1}-{score2} {company2}\n"
        
        if score1 > score2:
            overall_winner = company1
            response += f"🥇 KAZANAN: {company1}\n"
        elif score2 > score1:
            overall_winner = company2
            response += f"🥇 KAZANAN: {company2}\n"
        else:
            response += f"🤝 BERABERE\n"
        
        # EN İYİ FONLAR KARŞILAŞTIRMASI
        response += f"\n🌟 EN İYİ FONLAR KARŞILAŞTIRMASI:\n\n"
        
        response += f"🏢 {company1.upper()} EN İYİLERİ:\n"
        for i, fund in enumerate(results1['top_funds'][:3], 1):
            response += f"   {i}. {fund['fcode']}: Sharpe {fund['sharpe_ratio']:.3f}, Getiri %{fund['annual_return']:+.1f}\n"
        
        response += f"\n🏢 {company2.upper()} EN İYİLERİ:\n"
        for i, fund in enumerate(results2['top_funds'][:3], 1):
            response += f"   {i}. {fund['fcode']}: Sharpe {fund['sharpe_ratio']:.3f}, Getiri %{fund['annual_return']:+.1f}\n"
        
        # GÜÇLÜ/ZAYIF YÖNLER
        response += f"\n💪 GÜÇLÜ YÖNLER:\n"
        response += f"🏢 {company1}:\n"
        if results1['stats']['avg_sharpe'] > results2['stats']['avg_sharpe']:
            response += f"   ✅ Daha iyi risk-ayarlı getiri\n"
        if results1['stats']['total_capacity'] > results2['stats']['total_capacity']:
            response += f"   ✅ Daha büyük varlık yönetimi\n"
        if results1['stats']['total_funds'] > results2['stats']['total_funds']:
            response += f"   ✅ Daha geniş fon yelpazesi\n"
        
        response += f"\n🏢 {company2}:\n"
        if results2['stats']['avg_sharpe'] > results1['stats']['avg_sharpe']:
            response += f"   ✅ Daha iyi risk-ayarlı getiri\n"
        if results2['stats']['total_capacity'] > results1['stats']['total_capacity']:
            response += f"   ✅ Daha büyük varlık yönetimi\n"
        if results2['stats']['total_funds'] > results1['stats']['total_funds']:
            response += f"   ✅ Daha geniş fon yelpazesi\n"
        
        return response

    def analyze_company_detailed_data(self, company_name, analysis_days=252):
        """Şirket için detaylı veri analizi (karşılaştırma için)"""
        try:
            company_funds = self.get_all_company_funds_unlimited(company_name)
            
            if not company_funds:
                return {'success': False}
            
            performance_results = []
            
            for fund_info in company_funds:
                perf = self.calculate_comprehensive_performance(fund_info['fcode'], analysis_days)
                if perf:
                    fund_result = {
                        'fcode': fund_info['fcode'],
                        'fund_name': fund_info['fund_name'],
                        'capacity': fund_info['capacity'],
                        'investors': fund_info['investors'],
                        **perf
                    }
                    performance_results.append(fund_result)
            
            if not performance_results:
                return {'success': False}
            
            # İstatistikleri hesapla
            total_funds = len(performance_results)
            total_capacity = sum(r['capacity'] for r in performance_results)
            total_investors = sum(r['investors'] for r in performance_results)
            avg_return = sum(r['annual_return'] for r in performance_results) / total_funds
            avg_sharpe = sum(r['sharpe_ratio'] for r in performance_results) / total_funds
            avg_volatility = sum(r['volatility'] for r in performance_results) / total_funds
            
            # En iyi fonları bul
            performance_results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
            
            return {
                'success': True,
                'stats': {
                    'total_funds': total_funds,
                    'total_capacity': total_capacity,
                    'total_investors': total_investors,
                    'avg_return': avg_return,
                    'avg_sharpe': avg_sharpe,
                    'avg_volatility': avg_volatility
                },
                'top_funds': performance_results[:5],
                'all_funds': performance_results
            }
            
        except Exception as e:
            print(f"   ❌ {company_name} detaylı analiz hatası: {e}")
            return {'success': False}

    def find_best_portfolio_company_unlimited(self):
        """En başarılı portföy şirketini bul - TÜM ŞİRKETLER"""
        print(f"\n🏆 EN BAŞARILI PORTFÖY ŞİRKETİ ANALİZİ - TÜM ŞİRKETLER")
        print("="*65)
        
        company_results = []
        total_companies = len(self.company_keywords)
        
        for i, company_name in enumerate(self.company_keywords.keys(), 1):
            print(f"\n📊 [{i}/{total_companies}] {company_name} analizi...")
            
            try:
                result = self.analyze_company_detailed_data(company_name, analysis_days=180)  # 6 ay
                
                if result['success']:
                    stats = result['stats']
                    
                    # BAŞARI SKORU hesaplama (çok boyutlu)
                    success_score = (
                        stats['avg_sharpe'] * 40 +          # Risk-ayarlı getiri (en önemli)
                        (stats['avg_return'] / 100) * 30 +   # Mutlak getiri 
                        (stats['total_funds'] / 10) * 15 +   # Fon çeşitliliği
                        min(stats['total_capacity'] / 1000000000, 5) * 10 +  # Büyüklük (max 5 puan)
                        (stats['total_investors'] / 100000) * 5  # Popülerlik
                    )
                    
                    company_results.append({
                        'company': company_name,
                        'success_score': success_score,
                        **stats,
                        'best_fund': result['top_funds'][0] if result['top_funds'] else None
                    })
                    
                    print(f"   ✅ Başarı Skoru: {success_score:.2f}")
                else:
                    print(f"   ❌ Veri yetersiz")
                    
            except Exception as e:
                print(f"   ❌ Hata: {e}")
                continue
        
        if not company_results:
            return "❌ Hiçbir şirket analiz edilemedi."
        
        # Başarı skoruna göre sırala
        company_results.sort(key=lambda x: x['success_score'], reverse=True)
        
        return self.format_best_company_results(company_results)

    def format_best_company_results(self, results):
        """En başarılı şirket sonuçlarını formatla"""
        
        response = f"\n🏆 EN BAŞARILI PORTFÖY YÖNETİM ŞİRKETİ SIRALAMASI\n"
        response += f"{'='*60}\n\n"
        response += f"📊 {len(results)} şirket analiz edildi (TÜM FONLARLA)\n\n"
        
        # TOP 10 ŞİRKET
        response += f"🥇 EN BAŞARILI 10 ŞİRKET (Çok Boyutlu Skorlama):\n\n"
        
        for i, company in enumerate(results[:10], 1):
            # Başarı kategorisi
            score = company['success_score']
            if score > 15:
                rating = "🌟 EFSANE"
            elif score > 10:
                rating = "⭐ MÜKEMMEL"
            elif score > 7:
                rating = "🔶 ÇOK İYİ"
            elif score > 5:
                rating = "🔸 İYİ"
            elif score > 3:
                rating = "🟡 ORTA"
            else:
                rating = "🔻 ZAYIF"
            
            response += f"{i:2d}. {company['company']} - {rating}\n"
            response += f"    🎯 Başarı Skoru: {score:.2f}/25\n"
            response += f"    📊 Fon Sayısı: {company['total_funds']}\n"
            response += f"    📈 Ort. Getiri: %{company['avg_return']:+.2f}\n"
            response += f"    ⚡ Ort. Sharpe: {company['avg_sharpe']:.3f}\n"
            response += f"    💰 Varlık: {company['total_capacity']/1000000000:.1f} milyar TL\n"
            response += f"    👥 Yatırımcı: {company['total_investors']:,} kişi\n"
            
            if company['best_fund']:
                bf = company['best_fund']
                response += f"    🏆 En İyi Fon: {bf['fcode']} (Sharpe: {bf['sharpe_ratio']:.3f})\n"
            
            response += f"\n"
        
        # ŞAMPİYONLAR
        winner = results[0]
        response += f"🏆 GENEL ŞAMPİYON: {winner['company']}\n"
        response += f"   🎯 Toplam Skor: {winner['success_score']:.2f}\n"
        response += f"   📊 {winner['total_funds']} fon ile %{winner['avg_return']:+.1f} ortalama getiri\n"
        
        # KATEGORİ ŞAMPİYONLARI
        response += f"\n🏅 KATEGORİ ŞAMPİYONLARI:\n"
        
        # En yüksek getiri
        best_return = max(results, key=lambda x: x['avg_return'])
        response += f"   📈 En Yüksek Getiri: {best_return['company']} (%{best_return['avg_return']:+.1f})\n"
        
        # En iyi Sharpe
        best_sharpe = max(results, key=lambda x: x['avg_sharpe'])
        response += f"   ⚡ En İyi Sharpe: {best_sharpe['company']} ({best_sharpe['avg_sharpe']:.3f})\n"
        
        # En büyük varlık
        biggest_aum = max(results, key=lambda x: x['total_capacity'])
        response += f"   💰 En Büyük Varlık: {biggest_aum['company']} ({biggest_aum['total_capacity']/1000000000:.1f} milyar TL)\n"
        
        # En çok fon
        most_funds = max(results, key=lambda x: x['total_funds'])
        response += f"   📊 En Çok Fon: {most_funds['company']} ({most_funds['total_funds']} fon)\n"
        
        # En popüler
        most_popular = max(results, key=lambda x: x['total_investors'])
        response += f"   👥 En Popüler: {most_popular['company']} ({most_popular['total_investors']:,} yatırımcı)\n"
        
        # SEKTÖR ANALİZİ
        avg_sector_score = sum(r['success_score'] for r in results) / len(results)
        avg_sector_return = sum(r['avg_return'] for r in results) / len(results)
        avg_sector_sharpe = sum(r['avg_sharpe'] for r in results) / len(results)
        
        response += f"\n📊 SEKTÖR GENEL ANALİZİ:\n"
        response += f"   Ortalama Başarı Skoru: {avg_sector_score:.2f}\n"
        response += f"   Ortalama Getiri: %{avg_sector_return:+.2f}\n"
        response += f"   Ortalama Sharpe: {avg_sector_sharpe:.3f}\n"
        
        # PERFORMANS DAĞILIMI
        excellent = len([r for r in results if r['success_score'] > 10])
        good = len([r for r in results if 7 < r['success_score'] <= 10])
        average = len([r for r in results if 5 < r['success_score'] <= 7])
        poor = len([r for r in results if r['success_score'] <= 5])
        
        response += f"\n📈 PERFORMANS DAĞILIMI:\n"
        response += f"   🌟 Mükemmel (>10): {excellent} şirket\n"
        response += f"   ⭐ Çok İyi (7-10): {good} şirket\n"
        response += f"   🔶 İyi (5-7): {average} şirket\n"
        response += f"   🔻 Gelişmeli (≤5): {poor} şirket\n"
        
        return response


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