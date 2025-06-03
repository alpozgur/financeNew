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
        
        self.fundamental_analyzer = FundamentalAnalysisEnhancement(self.coordinator, self.active_funds)
        self.portfolio_analyzer = EnhancedPortfolioCompanyAnalyzer(self.coordinator)
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
        question_lower = question.lower()
        # Sayısal değer parsing (10 fon, 5 fon vs.)
        import re
        numbers_in_question = re.findall(r'(\d+)', question)
        requested_count = int(numbers_in_question[0]) if numbers_in_question else 1
        
        # GÜVENLİ FONLAR - ÇOKLU LİSTE DESTEĞİ
        if any(word in question_lower for word in ['en güvenli', 'en az riskli', 'güvenli fonlar']):
            # Eğer sayı belirtilmişse (örn: "en güvenli 10 fon") -> liste ver
            if requested_count > 1 or 'fonlar' in question_lower:
                return self._handle_safest_funds_sql_fast(requested_count)
            else:
                # Tek fon istiyorsa -> eski metodu kullan
                return self._handle_safest_fund()
        
        # RİSKLİ FONLAR - ÇOKLU LİSTE DESTEĞİ  
        if "en riskli" in question_lower:
            if requested_count > 1 or 'fonlar' in question_lower:
                return self._handle_riskiest_funds_list(requested_count)
            else:
                return self._handle_most_risky_fund()
        
        # EN ÇOK KAYBETTİREN - ÇOKLU LİSTE DESTEĞİ
        if any(word in question_lower for word in ['en çok kaybettiren', 'en çok düşen']):
            if requested_count > 1 or 'fonlar' in question_lower:
                return self._handle_worst_funds_list(requested_count)
            else:
                return self._handle_worst_fund()        
        # Özel risk sorusu yakalama
        if "en riskli" in question_lower:
            return self._handle_most_risky_fund()
        if "en güvenli" in question_lower or "en az riskli" in question_lower:
            return self._handle_safest_fund()
        if "en çok kaybettiren" in question_lower or "en çok düşen" in question_lower:
            return self._handle_worst_fund()

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
            return self._handle_fund_past_performance_question(question)
        if 'en çok kazandıran' in question_lower or 'en çok getiri' in question_lower:
            return self._handle_top_gainer_fund_question(question)
        if 'düşüşte olan fonlar' in question_lower or 'en çok kaybettiren' in question_lower:
            return self._handle_top_loser_fund_question(question)
        if 'sharpe oranı en yüksek' in question_lower:
            return self._handle_top_sharpe_funds_question(question)
        if 'volatilite' in question_lower and 'altında' in question_lower:
            return self._handle_low_volatility_funds_question(question)
        # --- mevcut kalan kodun ---
        if any(word in question_lower for word in ['2025', 'öneri', 'öner', 'recommend', 'suggest']):
            return self._handle_2025_recommendation_dual(question)
        elif any(word in question_lower for word in ['analiz', 'analyze', 'performance']):
            return self._handle_analysis_question_dual(question)
        elif any(word in question_lower for word in ['karşılaştır', 'compare', 'vs']):
            return self._handle_comparison_question(question)
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
    # def _handle_safest_funds_list(self, count=10, days=60):
    #     """En güvenli fonların listesi (volatilite bazlı)"""
    #     print(f"🛡️ En güvenli {count} fon analiz ediliyor...")
        
    #     safe_funds = []
        
    #     # SQL ile direkt en düşük volatilite fonları (benzersiz)
    #     try:
    #         # Her fon için en güncel verileri al ve volatilite hesapla
    #         query = f"""
    #         WITH latest_prices AS (
    #             SELECT fcode, price, pdate,
    #                 ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY pdate DESC) as rn
    #             FROM tefasfunds 
    #             WHERE pdate >= CURRENT_DATE - INTERVAL '{days} days'
    #             AND price > 0
    #         ),
    #         price_series AS (
    #             SELECT fcode, price, pdate
    #             FROM latest_prices 
    #             WHERE rn <= {days}  -- Son {days} günlük veri
    #         )
    #         SELECT fcode, COUNT(*) as data_points
    #         FROM price_series 
    #         GROUP BY fcode
    #         HAVING COUNT(*) >= 20  -- En az 20 gün veri
    #         ORDER BY fcode
    #         """
            
    #         fund_candidates = self.coordinator.db.execute_query(query)
    #         print(f"   📊 {len(fund_candidates)} fon adayı bulundu")
            
    #         # Her fon için volatilite hesapla
    #         for _, row in fund_candidates.iterrows():
    #             fcode = row['fcode']
                
    #             try:
    #                 # Fon verilerini al
    #                 data = self.coordinator.db.get_fund_price_history(fcode, days)
                    
    #                 if len(data) >= 20:
    #                     prices = data.set_index('pdate')['price'].sort_index()
    #                     returns = prices.pct_change().dropna()
                        
    #                     # Risk metrikleri
    #                     volatility = returns.std() * 100  # Günlük volatilite %
    #                     annual_vol = volatility * np.sqrt(252)  # Yıllık volatilite
                        
    #                     # Getiri metrikleri
    #                     total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                        
    #                     # Max drawdown
    #                     cumulative = (1 + returns).cumprod()
    #                     running_max = cumulative.expanding().max()
    #                     drawdown = (cumulative - running_max) / running_max
    #                     max_drawdown = abs(drawdown.min()) * 100
                        
    #                     # Fund details
    #                     details = self.coordinator.db.get_fund_details(fcode)
    #                     fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
    #                     fund_type = details.get('fund_type', 'N/A') if details else 'N/A'
                        
    #                     safe_funds.append({
    #                         'fcode': fcode,
    #                         'volatility': volatility,
    #                         'annual_volatility': annual_vol,
    #                         'total_return': total_return,
    #                         'max_drawdown': max_drawdown,
    #                         'current_price': prices.iloc[-1],
    #                         'fund_name': fund_name,
    #                         'fund_type': fund_type,
    #                         'data_points': len(prices)
    #                     })
                        
    #             except Exception:
    #                 continue
            
    #         # Volatiliteye göre sırala (en düşük = en güvenli)
    #         safe_funds.sort(key=lambda x: x['volatility'])
            
    #         if safe_funds:
    #             response = f"\n🛡️ EN GÜVENLİ {count} FON (Düşük Risk/Volatilite)\n"
    #             response += f"{'='*50}\n\n"
    #             response += f"📊 ANALİZ PARAMETRELERİ:\n"
    #             response += f"   • Analiz Periyodu: Son {days} gün\n"
    #             response += f"   • Bulunan Güvenli Fon: {len(safe_funds)}\n"
    #             response += f"   • Risk Metriği: Günlük volatilite\n\n"
                
    #             response += f"🛡️ EN GÜVENLİ FONLAR LİSTESİ:\n\n"
                
    #             for i, fund in enumerate(safe_funds[:count], 1):
    #                 # Risk kategorisi
    #                 if fund['volatility'] < 1:
    #                     risk_category = "🟢 ÇOK DÜŞÜK"
    #                 elif fund['volatility'] < 2:
    #                     risk_category = "🟡 DÜŞÜK"
    #                 elif fund['volatility'] < 5:
    #                     risk_category = "🟠 ORTA"
    #                 else:
    #                     risk_category = "🔴 YÜKSEK"
                    
    #                 response += f"{i:2d}. {fund['fcode']} - {risk_category} RİSK\n"
    #                 response += f"    📉 Günlük Volatilite: %{fund['volatility']:.2f}\n"
    #                 response += f"    📊 Yıllık Volatilite: %{fund['annual_volatility']:.1f}\n"
    #                 response += f"    📈 Getiri: %{fund['total_return']:+.2f}\n"
    #                 response += f"    📉 Max Düşüş: %{fund['max_drawdown']:.2f}\n"
    #                 response += f"    💲 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
    #                 response += f"    🏷️ Tür: {fund['fund_type']}\n"
    #                 if fund['fund_name'] != 'N/A':
    #                     response += f"    📝 Adı: {fund['fund_name'][:45]}...\n"
    #                 response += f"\n"
                
    #             # İstatistikler
    #             avg_volatility = sum(f['volatility'] for f in safe_funds[:count]) / min(count, len(safe_funds))
    #             avg_return = sum(f['total_return'] for f in safe_funds[:count]) / min(count, len(safe_funds))
                
    #             response += f"📊 GÜVENLİ FONLAR İSTATİSTİKLERİ:\n"
    #             response += f"   Ortalama Volatilite: %{avg_volatility:.2f}\n"
    #             response += f"   Ortalama Getiri: %{avg_return:+.2f}\n"
    #             response += f"   En Güvenli: {safe_funds[0]['fcode']} (%{safe_funds[0]['volatility']:.2f})\n"
                
    #             # Risk/Getiri analizi
    #             if avg_return > 0:
    #                 response += f"\n💡 ANALİZ: Bu güvenli fonlar ortalama %{avg_return:.1f} getiri sağladı\n"
    #             else:
    #                 response += f"\n⚠️ DİKKAT: Güvenli fonlar %{abs(avg_return):.1f} kayıp yaşadı\n"
                
    #             response += f"\n🎯 YATIRIM TAVSİYESİ:\n"
    #             response += f"   • Düşük risk toleransı için: İlk 3 fon\n"
    #             response += f"   • Dengeli yaklaşım için: İlk 5 fon karışımı\n"
    #             response += f"   • Güvenli portföy için: %70 güvenli + %30 büyüme\n"
                
    #             return response
            
    #         else:
    #             return f"❌ Son {days} günde analiz edilebilir güvenli fon bulunamadı."
                
    #     except Exception as e:
    #         return f"❌ Güvenli fon analizi hatası: {e}"

    def _handle_technical_analysis_questions_full_db(self, question):
        """SQL tabanlı teknik analiz - Tüm veritabanını kullanır"""
        question_lower = question.lower()
        
        # MACD sinyali soruları
        if any(word in question_lower for word in ['macd', 'macd sinyali', 'macd pozitif', 'macd negatif']):
            return self._handle_macd_signals_sql(question)
        
        # Bollinger Bands soruları
        elif any(word in question_lower for word in ['bollinger', 'bollinger bantları', 'alt banda', 'üst banda']):
            return self._handle_bollinger_signals_sql(question)
        
        # RSI soruları
        elif any(word in question_lower for word in ['rsi', 'rsi düşük', 'rsi yüksek', 'aşırı satım', 'aşırı alım']):
            return self._handle_rsi_signals_sql(question)
        
        # Moving Average soruları
        elif any(word in question_lower for word in ['hareketli ortalama', 'moving average', 'sma', 'ema', 'golden cross', 'death cross']):
            return self._handle_moving_average_signals_sql(question)
        
        # Genel teknik sinyal soruları
        elif any(word in question_lower for word in ['teknik sinyal', 'alım sinyali', 'satım sinyali']):
            return self._handle_general_technical_signals_sql(question)
        
        else:
            return None

    def _handle_macd_signals_sql(self, question):
        """SQL ile MACD analizi - TÜM FONLAR"""
        print("📊 SQL ile MACD sinyali analiz ediliyor (TÜM VERİTABANI)...")
        
        # Pozitif/negatif sinyali tespit et
        is_positive = any(word in question.lower() for word in ['pozitif', 'positive', 'alım', 'buy'])
        signal_type = "pozitif" if is_positive else "negatif"
        operator = ">" if is_positive else "<"
        
        try:
            # SQL ile MACD hesaplama ve filtreleme
            query = f"""
            WITH recent_prices AS (
                -- Her fon için son 30 günlük veriyi al
                SELECT fcode, price, pdate,
                    ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY pdate DESC) as rn
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '40 days'
                AND price > 0
                AND investorcount > 50  -- Minimum yatırımcı sayısı
            ),
            price_series AS (
                SELECT fcode, price, pdate
                FROM recent_prices 
                WHERE rn <= 30  -- Son 30 gün
            ),
            ema_calculations AS (
                SELECT fcode,
                    -- Basitleştirilmiş EMA hesaplaması
                    AVG(CASE WHEN rn <= 12 THEN price END) as ema_12_approx,
                    AVG(CASE WHEN rn <= 26 THEN price END) as ema_26_approx,
                    COUNT(*) as data_points
                FROM (
                    SELECT fcode, price,
                        ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY pdate DESC) as rn
                    FROM price_series
                ) ranked_prices
                GROUP BY fcode
                HAVING COUNT(*) >= 26  -- En az 26 gün veri
            ),
            macd_signals AS (
                SELECT fcode,
                    ema_12_approx,
                    ema_26_approx,
                    (ema_12_approx - ema_26_approx) as macd_line,
                    data_points
                FROM ema_calculations
                WHERE ema_12_approx IS NOT NULL AND ema_26_approx IS NOT NULL
            )
            SELECT ms.fcode, ms.macd_line, ms.ema_12_approx, ms.ema_26_approx, 
                ms.data_points, f.price as current_price, f.investorcount
            FROM macd_signals ms
            JOIN (
                SELECT DISTINCT ON (fcode) fcode, price, investorcount
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY fcode, pdate DESC
            ) f ON ms.fcode = f.fcode
            WHERE ms.macd_line {operator} 0
            ORDER BY ABS(ms.macd_line) DESC
            LIMIT 20
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return f"❌ {signal_type.upper()} MACD sinyali olan fon bulunamadı."
            
            print(f"   ✅ SQL analizi: {len(result)} fon bulundu")
            
            response = f"\n📊 MACD SİNYALİ {signal_type.upper()} - SQL ANALİZİ (TÜM VERİTABANI)\n"
            response += f"{'='*60}\n\n"
            response += f"🎯 Toplam {len(result)} fon {signal_type} MACD sinyali veriyor\n\n"
            
            # Fund details'leri toplu al
            fund_codes = result['fcode'].tolist()
            fund_details_dict = {}
            
            # Batch olarak fund details al
            try:
                details_df = self.coordinator.db.get_all_fund_details()
                for _, detail_row in details_df.iterrows():
                    if detail_row['fcode'] in fund_codes:
                        fund_details_dict[detail_row['fcode']] = {
                            'name': detail_row.get('fund_name', 'N/A'),
                            'type': detail_row.get('fund_type', 'N/A')
                        }
            except:
                pass
            
            for i, (_, row) in enumerate(result.head(15).iterrows(), 1):
                fcode = row['fcode']
                macd_value = float(row['macd_line'])
                current_price = float(row['current_price'])
                investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                
                # Fund details
                fund_info = fund_details_dict.get(fcode, {'name': 'N/A', 'type': 'N/A'})
                
                # Sinyal gücü
                if abs(macd_value) > 0.01:
                    strength = "🟢 GÜÇLÜ"
                elif abs(macd_value) > 0.005:
                    strength = "🟡 ORTA"
                else:
                    strength = "🟠 ZAYIF"
                
                response += f"{i:2d}. {fcode} - {strength}\n"
                response += f"    📊 MACD: {macd_value:+.6f}\n"
                response += f"    💲 Fiyat: {current_price:.4f} TL\n"
                response += f"    👥 Yatırımcı: {investors:,} kişi\n"
                response += f"    🏷️ Tür: {fund_info['type']}\n"
                if fund_info['name'] != 'N/A':
                    response += f"    📝 Adı: {fund_info['name'][:40]}...\n"
                response += f"\n"
            
            # İstatistikler
            avg_macd = result['macd_line'].mean()
            strongest_macd = result.iloc[0]
            
            response += f"📊 {signal_type.upper()} MACD İSTATİSTİKLERİ:\n"
            response += f"   Ortalama MACD: {avg_macd:+.6f}\n"
            response += f"   En Güçlü: {strongest_macd['fcode']} ({strongest_macd['macd_line']:+.6f})\n"
            response += f"   Toplam Bulunan: {len(result)} fon\n"
            
            return response
            
        except Exception as e:
            print(f"   ❌ SQL MACD analizi hatası: {e}")
            return f"❌ SQL MACD analizi hatası: {e}"

    def _handle_bollinger_signals_sql(self, question):
        """SQL ile Bollinger Bantları analizi - TÜM FONLAR"""
        print("📊 SQL ile Bollinger Bantları analiz ediliyor (TÜM VERİTABANI)...")
        
        # Alt/üst banda yakın tespit et
        is_lower_band = any(word in question.lower() for word in ['alt banda', 'lower band', 'alt', 'düşük'])
        band_type = "alt banda" if is_lower_band else "üst banda"
        bb_condition = "< 0.3" if is_lower_band else "> 0.7"
        
        try:
            query = f"""
            WITH recent_prices AS (
                SELECT fcode, price, pdate,
                    ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY pdate DESC) as rn
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '30 days'
                AND price > 0
                AND investorcount > 50
            ),
            price_series AS (
                SELECT fcode, price, pdate
                FROM recent_prices 
                WHERE rn <= 20  -- Son 20 gün (Bollinger için yeterli)
            ),
            bollinger_calc AS (
                SELECT fcode,
                    AVG(price) as sma_20,
                    STDDEV(price) as std_20,
                    COUNT(*) as data_points,
                    (SELECT price FROM recent_prices WHERE fcode = ps.fcode AND rn = 1) as current_price
                FROM price_series ps
                GROUP BY fcode
                HAVING COUNT(*) >= 15  -- En az 15 gün
            ),
            bollinger_bands AS (
                SELECT fcode,
                    current_price,
                    sma_20,
                    std_20,
                    (sma_20 + 2 * std_20) as upper_band,
                    (sma_20 - 2 * std_20) as lower_band,
                    CASE 
                        WHEN (sma_20 + 2 * std_20) - (sma_20 - 2 * std_20) = 0 THEN 0
                        ELSE (current_price - (sma_20 - 2 * std_20)) / 
                            ((sma_20 + 2 * std_20) - (sma_20 - 2 * std_20))
                    END as bb_percent
                FROM bollinger_calc
                WHERE std_20 > 0
            )
            SELECT bb.fcode, bb.current_price, bb.sma_20, bb.upper_band, bb.lower_band, 
                bb.bb_percent, f.investorcount
            FROM bollinger_bands bb
            JOIN (
                SELECT DISTINCT ON (fcode) fcode, investorcount
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY fcode, pdate DESC
            ) f ON bb.fcode = f.fcode
            WHERE bb.bb_percent {bb_condition}
            ORDER BY {'bb.bb_percent ASC' if is_lower_band else 'bb.bb_percent DESC'}
            LIMIT 20
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return f"❌ {band_type.upper()} yakın Bollinger sinyali olan fon bulunamadı."
            
            print(f"   ✅ SQL analizi: {len(result)} fon bulundu")
            
            response = f"\n📊 BOLLİNGER BANTLARI - {band_type.upper()} YAKIN FONLAR (SQL)\n"
            response += f"{'='*55}\n\n"
            response += f"🎯 {len(result)} fon {band_type} yakın pozisyonda\n\n"
            
            # Fund details'leri toplu al
            fund_codes = result['fcode'].tolist()
            fund_details_dict = {}
            
            try:
                details_df = self.coordinator.db.get_all_fund_details()
                for _, detail_row in details_df.iterrows():
                    if detail_row['fcode'] in fund_codes:
                        fund_details_dict[detail_row['fcode']] = {
                            'name': detail_row.get('fund_name', 'N/A'),
                            'type': detail_row.get('fund_type', 'N/A')
                        }
            except:
                pass
            
            for i, (_, row) in enumerate(result.head(15).iterrows(), 1):
                fcode = row['fcode']
                current_price = float(row['current_price'])
                bb_percent = float(row['bb_percent'])
                upper_band = float(row['upper_band'])
                lower_band = float(row['lower_band'])
                sma_20 = float(row['sma_20'])
                investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                
                fund_info = fund_details_dict.get(fcode, {'name': 'N/A', 'type': 'N/A'})
                
                # Pozisyon belirleme
                if bb_percent < 0.2:
                    position = "🔴 ALT BANT ÇOK YAKIN"
                elif bb_percent < 0.3:
                    position = "🟠 ALT BANT YAKIN"
                elif bb_percent > 0.8:
                    position = "🟢 ÜST BANT ÇOK YAKIN"
                elif bb_percent > 0.7:
                    position = "🟡 ÜST BANT YAKIN"
                else:
                    position = "⚪ ORTA BÖLGE"
                
                response += f"{i:2d}. {fcode} - {position}\n"
                response += f"    💲 Fiyat: {current_price:.4f} TL\n"
                response += f"    📊 BB%: {bb_percent:.3f} (%{bb_percent*100:.1f})\n"
                response += f"    📈 Üst Bant: {upper_band:.4f} TL\n"
                response += f"    📉 Alt Bant: {lower_band:.4f} TL\n"
                response += f"    📊 SMA(20): {sma_20:.4f} TL\n"
                response += f"    👥 Yatırımcı: {investors:,} kişi\n"
                response += f"    🏷️ Tür: {fund_info['type']}\n"
                response += f"\n"
            
            # İstatistikler
            avg_bb_percent = result['bb_percent'].mean()
            closest = result.iloc[0]
            
            response += f"📊 {band_type.upper()} BOLLİNGER İSTATİSTİKLERİ:\n"
            response += f"   Ortalama BB%: {avg_bb_percent:.3f}\n"
            response += f"   En Yakın: {closest['fcode']} ({closest['bb_percent']:.3f})\n"
            response += f"   Toplam Bulunan: {len(result)} fon\n"
            
            return response
            
        except Exception as e:
            print(f"   ❌ SQL Bollinger analizi hatası: {e}")
            return f"❌ SQL Bollinger analizi hatası: {e}"

    def _handle_rsi_signals_sql(self, question):
        """SQL ile RSI analizi - TÜM FONLAR"""
        print("📊 SQL ile RSI analiz ediliyor (TÜM VERİTABANI)...")
        
        # RSI seviyesini tespit et
        is_oversold = any(word in question.lower() for word in ['düşük', 'oversold', 'aşırı satım', '30', 'altında'])
        is_overbought = any(word in question.lower() for word in ['yüksek', 'overbought', 'aşırı alım', '70', 'üstünde'])
        
        if is_oversold:
            condition = "oversold"
            rsi_condition = "< 35"  # Biraz esneklik
            order_by = "rsi_approx ASC"
        elif is_overbought:
            condition = "overbought" 
            rsi_condition = "> 65"  # Biraz esneklik
            order_by = "rsi_approx DESC"
        else:
            condition = "neutral"
            rsi_condition = "BETWEEN 40 AND 60"
            order_by = "ABS(rsi_approx - 50) ASC"
        
        try:
            # Basitleştirilmiş RSI hesaplaması SQL'de
            query = f"""
            WITH recent_prices AS (
                SELECT fcode, price, pdate,
                    LAG(price) OVER (PARTITION BY fcode ORDER BY pdate) as prev_price,
                    ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY pdate DESC) as rn
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '25 days'
                AND price > 0
                AND investorcount > 50
            ),
            price_changes AS (
                SELECT fcode, price, pdate,
                    CASE WHEN price > prev_price THEN price - prev_price ELSE 0 END as gain,
                    CASE WHEN price < prev_price THEN prev_price - price ELSE 0 END as loss
                FROM recent_prices 
                WHERE prev_price IS NOT NULL
                AND rn <= 15  -- Son 15 gün değişim
            ),
            rsi_calc AS (
                SELECT fcode,
                    AVG(gain) as avg_gain,
                    AVG(loss) as avg_loss,
                    COUNT(*) as data_points,
                    (SELECT price FROM recent_prices WHERE fcode = pc.fcode AND rn = 1) as current_price
                FROM price_changes pc
                GROUP BY fcode
                HAVING COUNT(*) >= 10  -- En az 10 gün
            ),
            rsi_values AS (
                SELECT fcode, current_price,
                    CASE 
                        WHEN avg_loss = 0 THEN 100
                        WHEN avg_gain = 0 THEN 0
                        ELSE 100 - (100 / (1 + (avg_gain / avg_loss)))
                    END as rsi_approx
                FROM rsi_calc
                WHERE avg_gain IS NOT NULL AND avg_loss IS NOT NULL
            )
            SELECT rv.fcode, rv.current_price, rv.rsi_approx, f.investorcount
            FROM rsi_values rv
            JOIN (
                SELECT DISTINCT ON (fcode) fcode, investorcount
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY fcode, pdate DESC
            ) f ON rv.fcode = f.fcode
            WHERE rv.rsi_approx {rsi_condition}
            ORDER BY {order_by}
            LIMIT 20
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return f"❌ RSI {condition} seviyesinde fon bulunamadı."
            
            print(f"   ✅ SQL analizi: {len(result)} fon bulundu")
            
            response = f"\n📊 RSI ANALİZİ - {condition.upper()} SEVİYE (SQL)\n"
            response += f"{'='*40}\n\n"
            response += f"🎯 {len(result)} fon RSI {condition} seviyesinde\n\n"
            
            # Fund details'leri toplu al
            fund_codes = result['fcode'].tolist()
            fund_details_dict = {}
            
            try:
                details_df = self.coordinator.db.get_all_fund_details()
                for _, detail_row in details_df.iterrows():
                    if detail_row['fcode'] in fund_codes:
                        fund_details_dict[detail_row['fcode']] = {
                            'name': detail_row.get('fund_name', 'N/A'),
                            'type': detail_row.get('fund_type', 'N/A')
                        }
            except:
                pass
            
            for i, (_, row) in enumerate(result.head(15).iterrows(), 1):
                fcode = row['fcode']
                current_price = float(row['current_price'])
                rsi_value = float(row['rsi_approx'])
                investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                
                fund_info = fund_details_dict.get(fcode, {'name': 'N/A', 'type': 'N/A'})
                
                # RSI kategorisi
                if rsi_value < 30:
                    rsi_category = "🔴 AŞIRI SATIM"
                elif rsi_value < 50:
                    rsi_category = "🟡 DÜŞÜK"
                elif rsi_value > 70:
                    rsi_category = "🟢 AŞIRI ALIM"
                elif rsi_value > 50:
                    rsi_category = "🟠 YÜKSEK"
                else:
                    rsi_category = "⚪ NORMAL"
                
                response += f"{i:2d}. {fcode} - {rsi_category}\n"
                response += f"    📊 RSI: {rsi_value:.1f}\n"
                response += f"    💲 Fiyat: {current_price:.4f} TL\n"
                response += f"    👥 Yatırımcı: {investors:,} kişi\n"
                response += f"    🏷️ Tür: {fund_info['type']}\n"
                if fund_info['name'] != 'N/A':
                    response += f"    📝 Adı: {fund_info['name'][:35]}...\n"
                response += f"\n"
            
            # İstatistikler
            avg_rsi = result['rsi_approx'].mean()
            extreme = result.iloc[0]
            
            response += f"📊 RSI {condition.upper()} İSTATİSTİKLERİ:\n"
            response += f"   Ortalama RSI: {avg_rsi:.1f}\n"
            response += f"   En Ekstrem: {extreme['fcode']} ({extreme['rsi_approx']:.1f})\n"
            response += f"   Toplam Bulunan: {len(result)} fon\n"
            
            return response
            
        except Exception as e:
            print(f"   ❌ SQL RSI analizi hatası: {e}")
            return f"❌ SQL RSI analizi hatası: {e}"

    def _handle_moving_average_signals_sql(self, question):
        """SQL ile Hareketli Ortalama analizi - TÜM FONLAR"""
        print("📊 SQL ile Hareketli Ortalama analiz ediliyor (TÜM VERİTABANI)...")
        
        # Golden/Death Cross tespit et
        is_golden_cross = any(word in question.lower() for word in ['golden cross', 'alım sinyali', 'pozitif'])
        signal_type = "Golden Cross" if is_golden_cross else "Death Cross"
        ma_condition = ">" if is_golden_cross else "<"
        
        try:
            query = f"""
            WITH recent_prices AS (
                SELECT fcode, price, pdate,
                    ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY pdate DESC) as rn
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '60 days'
                AND price > 0
                AND investorcount > 50
            ),
            ma_calculations AS (
                SELECT fcode,
                    AVG(CASE WHEN rn <= 20 THEN price END) as sma_20,
                    AVG(CASE WHEN rn <= 50 THEN price END) as sma_50,
                    COUNT(*) as data_points,
                    (SELECT price FROM recent_prices WHERE fcode = rp.fcode AND rn = 1) as current_price
                FROM recent_prices rp
                GROUP BY fcode
                HAVING COUNT(*) >= 50  -- En az 50 gün veri gerekli
            ),
            ma_signals AS (
                SELECT fcode, current_price, sma_20, sma_50,
                    ((sma_20 / sma_50) - 1) * 100 as ma_spread,
                    CASE 
                        WHEN sma_20 > sma_50 THEN 'Golden Cross'
                        WHEN sma_20 < sma_50 THEN 'Death Cross'
                        ELSE 'Neutral'
                    END as signal_type
                FROM ma_calculations
                WHERE sma_20 IS NOT NULL AND sma_50 IS NOT NULL
            )
            SELECT ms.fcode, ms.current_price, ms.sma_20, ms.sma_50, 
                ms.ma_spread, ms.signal_type, f.investorcount
            FROM ma_signals ms
            JOIN (
                SELECT DISTINCT ON (fcode) fcode, investorcount
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY fcode, pdate DESC
            ) f ON ms.fcode = f.fcode
            WHERE ms.sma_20 {ma_condition} ms.sma_50
            ORDER BY ABS(ms.ma_spread) DESC
            LIMIT 25
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return f"❌ {signal_type} sinyali olan fon bulunamadı."
            
            print(f"   ✅ SQL analizi: {len(result)} fon bulundu")
            
            response = f"\n📊 HAREKETLİ ORTALAMA - {signal_type.upper()} SİNYALLERİ (SQL)\n"
            response += f"{'='*55}\n\n"
            response += f"🎯 {len(result)} fon {signal_type} sinyali veriyor\n\n"
            
            # Fund details'leri toplu al
            fund_codes = result['fcode'].tolist()
            fund_details_dict = {}
            
            try:
                details_df = self.coordinator.db.get_all_fund_details()
                for _, detail_row in details_df.iterrows():
                    if detail_row['fcode'] in fund_codes:
                        fund_details_dict[detail_row['fcode']] = {
                            'name': detail_row.get('fund_name', 'N/A'),
                            'type': detail_row.get('fund_type', 'N/A')
                        }
            except:
                pass
            
            for i, (_, row) in enumerate(result.head(15).iterrows(), 1):
                fcode = row['fcode']
                current_price = float(row['current_price'])
                sma_20 = float(row['sma_20'])
                sma_50 = float(row['sma_50'])
                ma_spread = float(row['ma_spread'])
                investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                
                fund_info = fund_details_dict.get(fcode, {'name': 'N/A', 'type': 'N/A'})
                
                # Sinyal gücü
                if abs(ma_spread) > 5:
                    strength = "🟢 ÇOK GÜÇLÜ"
                elif abs(ma_spread) > 2:
                    strength = "🟡 GÜÇLÜ"
                elif abs(ma_spread) > 1:
                    strength = "🟠 ORTA"
                else:
                    strength = "⚪ ZAYIF"
                
                signal_icon = "🚀" if is_golden_cross else "📉"
                
                response += f"{i:2d}. {fcode} - {strength} {signal_icon}\n"
                response += f"    💲 Fiyat: {current_price:.4f} TL\n"
                response += f"    📊 SMA20: {sma_20:.4f} TL\n"
                response += f"    📈 SMA50: {sma_50:.4f} TL\n"
                response += f"    📍 Fark: %{ma_spread:+.2f}\n"
                response += f"    👥 Yatırımcı: {investors:,} kişi\n"
                response += f"    🏷️ Tür: {fund_info['type']}\n"
                response += f"\n"
            
            # İstatistikler
            avg_spread = result['ma_spread'].mean()
            strongest = result.iloc[0]
            
            response += f"📊 {signal_type.upper()} İSTATİSTİKLERİ:\n"
            response += f"   Ortalama Fark: %{avg_spread:+.2f}\n"
            response += f"   En Güçlü: {strongest['fcode']} (%{strongest['ma_spread']:+.2f})\n"
            response += f"   Toplam Bulunan: {len(result)} fon\n"
            
            return response
            
        except Exception as e:
            print(f"   ❌ SQL Moving Average analizi hatası: {e}")
            return f"❌ SQL Moving Average analizi hatası: {e}"

    def _handle_general_technical_signals_sql(self, question):
        """SQL ile Genel Teknik Sinyal analizi - TÜM FONLAR"""
        print("📊 SQL ile Genel Teknik Sinyaller analiz ediliyor (TÜM VERİTABANI)...")
        
        try:
            # Kompleks SQL sorgusu - multiple technical indicators
            query = """
            WITH recent_data AS (
                SELECT fcode, price, pdate, investorcount,
                    LAG(price, 1) OVER (PARTITION BY fcode ORDER BY pdate) as price_1d_ago,
                    LAG(price, 5) OVER (PARTITION BY fcode ORDER BY pdate) as price_5d_ago,
                    LAG(price, 10) OVER (PARTITION BY fcode ORDER BY pdate) as price_10d_ago,
                    ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY pdate DESC) as rn
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '30 days'
                AND price > 0
                AND investorcount > 100  -- Minimum yatırımcı sayısı
            ),
            latest_prices AS (
                SELECT fcode, price as current_price, investorcount
                FROM recent_data 
                WHERE rn = 1
            ),
            momentum_calc AS (
                SELECT rd.fcode,
                    lp.current_price,
                    lp.investorcount,
                    AVG(rd.price) as avg_price_20d,
                    STDDEV(rd.price) as std_price_20d,
                    -- Momentum indicators
                    CASE WHEN rd.price_5d_ago > 0 THEN 
                        ((lp.current_price - rd.price_5d_ago) / rd.price_5d_ago) * 100 
                        ELSE 0 END as momentum_5d,
                    CASE WHEN rd.price_10d_ago > 0 THEN 
                        ((lp.current_price - rd.price_10d_ago) / rd.price_10d_ago) * 100 
                        ELSE 0 END as momentum_10d,
                    COUNT(*) as data_points
                FROM recent_data rd
                JOIN latest_prices lp ON rd.fcode = lp.fcode
                WHERE rd.rn <= 20  -- Son 20 gün
                GROUP BY rd.fcode, lp.current_price, lp.investorcount
                HAVING COUNT(*) >= 15
            ),
            technical_scores AS (
                SELECT fcode, current_price, investorcount,
                    momentum_5d, momentum_10d,
                    -- Bollinger position approximation
                    CASE 
                        WHEN std_price_20d = 0 THEN 0.5
                        ELSE (current_price - (avg_price_20d - 2 * std_price_20d)) / 
                            (4 * std_price_20d)
                    END as bb_position,
                    -- Price vs moving average
                    CASE 
                        WHEN avg_price_20d = 0 THEN 0
                        ELSE ((current_price / avg_price_20d) - 1) * 100
                    END as price_vs_ma,
                    -- Combined technical score
                    CASE 
                        WHEN momentum_5d > 5 THEN 2
                        WHEN momentum_5d > 0 THEN 1
                        WHEN momentum_5d < -5 THEN -2
                        WHEN momentum_5d < 0 THEN -1
                        ELSE 0
                    END +
                    CASE 
                        WHEN momentum_10d > 10 THEN 2
                        WHEN momentum_10d > 0 THEN 1
                        WHEN momentum_10d < -10 THEN -2
                        WHEN momentum_10d < 0 THEN -1
                        ELSE 0
                    END as momentum_score
                FROM momentum_calc
            )
            SELECT fcode, current_price, investorcount, momentum_5d, momentum_10d,
                bb_position, price_vs_ma, momentum_score
            FROM technical_scores
            WHERE ABS(momentum_score) >= 2  -- Sadece güçlü sinyaller
            ORDER BY momentum_score DESC, ABS(momentum_5d) DESC
            LIMIT 25
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return "❌ Güçlü teknik sinyal olan fon bulunamadı."
            
            print(f"   ✅ SQL analizi: {len(result)} fon bulundu")
            
            response = f"\n📊 GENEL TEKNİK SİNYAL ANALİZİ - SQL (TÜM VERİTABANI)\n"
            response += f"{'='*55}\n\n"
            response += f"🎯 {len(result)} fon güçlü teknik sinyal veriyor\n\n"
            
            # Alım ve satım sinyallerini ayır
            buy_signals = result[result['momentum_score'] > 0].copy()
            sell_signals = result[result['momentum_score'] < 0].copy()
            
            # Fund details'leri toplu al
            fund_codes = result['fcode'].tolist()
            fund_details_dict = {}
            
            try:
                details_df = self.coordinator.db.get_all_fund_details()
                for _, detail_row in details_df.iterrows():
                    if detail_row['fcode'] in fund_codes:
                        fund_details_dict[detail_row['fcode']] = {
                            'name': detail_row.get('fund_name', 'N/A'),
                            'type': detail_row.get('fund_type', 'N/A')
                        }
            except:
                pass
            
            # ALIM SİNYALLERİ
            if not buy_signals.empty:
                response += f"🟢 GÜÇLÜ ALIM SİNYALLERİ ({len(buy_signals)} fon):\n\n"
                
                for i, (_, row) in enumerate(buy_signals.head(8).iterrows(), 1):
                    fcode = row['fcode']
                    current_price = float(row['current_price'])
                    momentum_5d = float(row['momentum_5d'])
                    momentum_10d = float(row['momentum_10d'])
                    momentum_score = int(row['momentum_score'])
                    investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                    
                    fund_info = fund_details_dict.get(fcode, {'name': 'N/A', 'type': 'N/A'})
                    
                    # Sinyal gücü
                    if momentum_score >= 4:
                        strength = "🟢 ÇOK GÜÇLÜ"
                    elif momentum_score >= 3:
                        strength = "🟡 GÜÇLÜ"
                    else:
                        strength = "🟠 ORTA"
                    
                    response += f"{i}. {fcode} - {strength} 🚀\n"
                    response += f"   💲 Fiyat: {current_price:.4f} TL\n"
                    response += f"   📊 5-Gün Momentum: %{momentum_5d:+.2f}\n"
                    response += f"   📈 10-Gün Momentum: %{momentum_10d:+.2f}\n"
                    response += f"   ⚡ Teknik Skor: +{momentum_score}\n"
                    response += f"   👥 Yatırımcı: {investors:,} kişi\n"
                    response += f"   🏷️ Tür: {fund_info['type']}\n"
                    response += f"\n"
            
            # SATIM SİNYALLERİ
            if not sell_signals.empty:
                response += f"\n🔴 GÜÇLÜ SATIM SİNYALLERİ ({len(sell_signals)} fon):\n\n"
                
                for i, (_, row) in enumerate(sell_signals.head(5).iterrows(), 1):
                    fcode = row['fcode']
                    current_price = float(row['current_price'])
                    momentum_5d = float(row['momentum_5d'])
                    momentum_10d = float(row['momentum_10d'])
                    momentum_score = int(row['momentum_score'])
                    investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                    
                    fund_info = fund_details_dict.get(fcode, {'name': 'N/A', 'type': 'N/A'})
                    
                    # Sinyal gücü
                    if momentum_score <= -4:
                        strength = "🔴 ÇOK GÜÇLÜ"
                    elif momentum_score <= -3:
                        strength = "🟠 GÜÇLÜ"
                    else:
                        strength = "🟡 ORTA"
                    
                    response += f"{i}. {fcode} - {strength} 📉\n"
                    response += f"   💲 Fiyat: {current_price:.4f} TL\n"
                    response += f"   📊 5-Gün Momentum: %{momentum_5d:+.2f}\n"
                    response += f"   📈 10-Gün Momentum: %{momentum_10d:+.2f}\n"
                    response += f"   ⚡ Teknik Skor: {momentum_score}\n"
                    response += f"   👥 Yatırımcı: {investors:,} kişi\n"
                    response += f"   🏷️ Tür: {fund_info['type']}\n"
                    response += f"\n"
            
            # GENEL İSTATİSTİKLER
            total_buy = len(buy_signals)
            total_sell = len(sell_signals)
            avg_momentum_5d = result['momentum_5d'].mean()
            
            response += f"📊 GENEL TEKNİK SİNYAL İSTATİSTİKLERİ:\n"
            response += f"   🟢 Alım Sinyali: {total_buy} fon\n"
            response += f"   🔴 Satım Sinyali: {total_sell} fon\n"
            response += f"   📊 Ortalama 5-Gün Momentum: %{avg_momentum_5d:+.2f}\n"
            response += f"   🎯 Toplam Analiz Edilen: {len(result)} fon\n"
            
            if total_buy > total_sell:
                response += f"\n💡 PİYASA YORUMU: Teknik sinyaller ALIMdan yana (%{total_buy/(total_buy+total_sell)*100:.0f})\n"
            elif total_sell > total_buy:
                response += f"\n💡 PİYASA YORUMU: Teknik sinyaller SATIMdan yana (%{total_sell/(total_buy+total_sell)*100:.0f})\n"
            else:
                response += f"\n💡 PİYASA YORUMU: Teknik sinyaller DENGELİ görünüyor\n"
            
            return response
            
        except Exception as e:
            print(f"   ❌ SQL Genel Teknik analizi hatası: {e}")
            return f"❌ SQL Genel Teknik analizi hatası: {e}"






    def _handle_technical_analysis_questions(self, question):
        """Teknik analiz sorularını işler"""
        question_lower = question.lower()
        
        # MACD sinyali soruları
        if any(word in question_lower for word in ['macd', 'macd sinyali', 'macd pozitif', 'macd negatif']):
            return self._handle_macd_signals(question)
        
        # Bollinger Bands soruları
        elif any(word in question_lower for word in ['bollinger', 'bollinger bantları', 'alt banda', 'üst banda']):
            return self._handle_bollinger_signals(question)
        
        # RSI soruları
        elif any(word in question_lower for word in ['rsi', 'rsi düşük', 'rsi yüksek', 'aşırı satım', 'aşırı alım']):
            return self._handle_rsi_signals(question)
        
        # Moving Average soruları
        elif any(word in question_lower for word in ['hareketli ortalama', 'moving average', 'sma', 'ema']):
            return self._handle_moving_average_signals(question)
        
        # Genel teknik sinyal soruları
        elif any(word in question_lower for word in ['teknik sinyal', 'alım sinyali', 'satım sinyali']):
            return self._handle_general_technical_signals(question)
        
        else:
            return None

    def _handle_macd_signals(self, question):
        """MACD sinyali pozitif/negatif olan fonlar"""
        print("📊 MACD sinyali analiz ediliyor...")
        
        # Pozitif/negatif sinyali tespit et
        is_positive = any(word in question.lower() for word in ['pozitif', 'positive', 'alım', 'buy'])
        signal_type = "pozitif" if is_positive else "negatif"
        
        response = f"\n📊 MACD SİNYALİ {signal_type.upper()} OLAN FONLAR\n"
        response += f"{'='*45}\n\n"
        
        macd_funds = []
        
        for fcode in self.active_funds[:30]:
            try:
                # Fon verilerini al
                data = self.coordinator.db.get_fund_price_history(fcode, 60)
                
                if len(data) >= 30:
                    prices = data.set_index('pdate')['price'].sort_index()
                    
                    # MACD hesapla
                    ema_12 = prices.ewm(span=12).mean()
                    ema_26 = prices.ewm(span=26).mean()
                    macd_line = ema_12 - ema_26
                    signal_line = macd_line.ewm(span=9).mean()
                    
                    current_macd = macd_line.iloc[-1]
                    current_signal = signal_line.iloc[-1]
                    
                    # Sinyal yönü
                    macd_signal = current_macd - current_signal
                    
                    # Pozitif/negatif filtrele
                    if (is_positive and macd_signal > 0) or (not is_positive and macd_signal < 0):
                        # Fund details
                        details = self.coordinator.db.get_fund_details(fcode)
                        fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                        
                        macd_funds.append({
                            'fcode': fcode,
                            'macd_signal': macd_signal,
                            'current_macd': current_macd,
                            'current_signal': current_signal,
                            'current_price': prices.iloc[-1],
                            'fund_name': fund_name
                        })
                        
            except Exception as e:
                continue
        
        # Sinyal gücüne göre sırala
        macd_funds.sort(key=lambda x: abs(x['macd_signal']), reverse=True)
        
        if macd_funds:
            response += f"🎯 BULUNAN {signal_type.upper()} MACD SİNYALLERİ ({len(macd_funds)} fon):\n\n"
            
            for i, fund in enumerate(macd_funds[:10], 1):
                # Sinyal gücü
                signal_strength = abs(fund['macd_signal'])
                
                if signal_strength > 0.001:
                    strength_text = "🟢 GÜÇLÜ"
                elif signal_strength > 0.0005:
                    strength_text = "🟡 ORTA"
                else:
                    strength_text = "🟠 ZAYIF"
                
                response += f"{i:2d}. {fund['fcode']} - {strength_text}\n"
                response += f"    📊 MACD: {fund['current_macd']:.6f}\n"
                response += f"    📉 Sinyal: {fund['current_signal']:.6f}\n"
                response += f"    ⚡ Fark: {fund['macd_signal']:+.6f}\n"
                response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
                if fund['fund_name'] != 'N/A':
                    response += f"    📝 Adı: {fund['fund_name'][:35]}...\n"
                response += f"\n"
            
            # En güçlü sinyal
            strongest = macd_funds[0]
            response += f"🏆 EN GÜÇLÜ {signal_type.upper()} SİNYAL:\n"
            response += f"   {strongest['fcode']}: {strongest['macd_signal']:+.6f}\n"
            
        else:
            response += f"❌ {signal_type.upper()} MACD sinyali olan fon bulunamadı.\n"
            response += f"💡 Daha geniş veri aralığı veya farklı sinyal türü deneyin.\n"
        
        response += f"\n📋 MACD SİNYAL AÇIKLAMASI:\n"
        response += f"   • MACD > Sinyal Hattı = Pozitif (Alım sinyali)\n"
        response += f"   • MACD < Sinyal Hattı = Negatif (Satım sinyali)\n"
        response += f"   • Analiz periyodu: Son 60 gün\n"
        
        return response

    def _handle_bollinger_signals(self, question):
        """Bollinger Bantlarında alt/üst banda yakın fonlar"""
        print("📊 Bollinger Bantları analiz ediliyor...")
        
        # Alt/üst banda yakın tespit et
        is_lower_band = any(word in question.lower() for word in ['alt banda', 'lower band', 'alt', 'düşük'])
        band_type = "alt banda" if is_lower_band else "üst banda"
        
        response = f"\n📊 BOLLİNGER BANTLARI - {band_type.upper()} YAKIN FONLAR\n"
        response += f"{'='*55}\n\n"
        
        bollinger_funds = []
        
        for fcode in self.active_funds[:30]:
            try:
                data = self.coordinator.db.get_fund_price_history(fcode, 40)
                
                if len(data) >= 25:
                    prices = data.set_index('pdate')['price'].sort_index()
                    
                    # Bollinger Bantları hesapla
                    sma_20 = prices.rolling(window=20).mean()
                    std_20 = prices.rolling(window=20).std()
                    
                    upper_band = sma_20 + (2 * std_20)
                    lower_band = sma_20 - (2 * std_20)
                    
                    current_price = prices.iloc[-1]
                    current_upper = upper_band.iloc[-1]
                    current_lower = lower_band.iloc[-1]
                    current_sma = sma_20.iloc[-1]
                    
                    # Bollinger %B hesapla
                    bb_percent = (current_price - current_lower) / (current_upper - current_lower)
                    
                    # Alt banda yakın (BB%B < 0.2) veya üst banda yakın (BB%B > 0.8)
                    if is_lower_band and bb_percent < 0.3:
                        condition_met = True
                        distance_text = f"Alt banda uzaklık: %{(bb_percent * 100):.1f}"
                    elif not is_lower_band and bb_percent > 0.7:
                        condition_met = True
                        distance_text = f"Üst banda uzaklık: %{((1-bb_percent) * 100):.1f}"
                    else:
                        condition_met = False
                    
                    if condition_met:
                        details = self.coordinator.db.get_fund_details(fcode)
                        fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                        
                        bollinger_funds.append({
                            'fcode': fcode,
                            'bb_percent': bb_percent,
                            'current_price': current_price,
                            'upper_band': current_upper,
                            'lower_band': current_lower,
                            'sma_20': current_sma,
                            'distance_text': distance_text,
                            'fund_name': fund_name
                        })
                        
            except Exception:
                continue
        
        # BB% değerine göre sırala
        if is_lower_band:
            bollinger_funds.sort(key=lambda x: x['bb_percent'])  # En düşük önce
        else:
            bollinger_funds.sort(key=lambda x: x['bb_percent'], reverse=True)  # En yüksek önce
        
        if bollinger_funds:
            response += f"🎯 {band_type.upper()} YAKIN FONLAR ({len(bollinger_funds)} fon):\n\n"
            
            for i, fund in enumerate(bollinger_funds[:10], 1):
                # Pozisyon belirleme
                if fund['bb_percent'] < 0.2:
                    position = "🔴 ALT BANT YAKIN"
                elif fund['bb_percent'] > 0.8:
                    position = "🟢 ÜST BANT YAKIN"
                else:
                    position = "🟡 ORTA BÖLGE"
                
                response += f"{i:2d}. {fund['fcode']} - {position}\n"
                response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
                response += f"    📊 BB%: {fund['bb_percent']:.3f} (%{fund['bb_percent']*100:.1f})\n"
                response += f"    📈 Üst Bant: {fund['upper_band']:.4f} TL\n"
                response += f"    📉 Alt Bant: {fund['lower_band']:.4f} TL\n"
                response += f"    📊 SMA(20): {fund['sma_20']:.4f} TL\n"
                response += f"    📍 {fund['distance_text']}\n"
                if fund['fund_name'] != 'N/A':
                    response += f"    📝 Adı: {fund['fund_name'][:35]}...\n"
                response += f"\n"
            
            # En yakın fon
            closest = bollinger_funds[0]
            response += f"🏆 EN YAKIN FON:\n"
            response += f"   {closest['fcode']}: BB% = {closest['bb_percent']:.3f}\n"
            
        else:
            response += f"❌ {band_type.upper()} yakın fon bulunamadı.\n"
            response += f"💡 Daha geniş kriterler veya farklı zaman aralığı deneyin.\n"
        
        response += f"\n📋 BOLLİNGER BANTLARI AÇIKLAMASI:\n"
        response += f"   • BB% < 0.2: Alt banda yakın (Potansiyel alım)\n"
        response += f"   • BB% > 0.8: Üst banda yakın (Potansiyel satım)\n"
        response += f"   • BB% = 0.5: Tam ortada (20-günlük ortalama)\n"
        response += f"   • Bantlar: 20-günlük SMA ± 2 standart sapma\n"
        
        return response

    def _handle_rsi_signals(self, question):
        """RSI düşük/yüksek olan fonlar"""
        print("📊 RSI analiz ediliyor...")
        
        # RSI seviyesini tespit et
        is_oversold = any(word in question.lower() for word in ['düşük', 'oversold', 'aşırı satım', '30', 'altında'])
        is_overbought = any(word in question.lower() for word in ['yüksek', 'overbought', 'aşırı alım', '70', 'üstünde'])
        
        if is_oversold:
            condition = "oversold"
            threshold = 30
            comparison = "<"
        elif is_overbought:
            condition = "overbought" 
            threshold = 70
            comparison = ">"
        else:
            condition = "neutral"
            threshold = 50
            comparison = "around"
        
        response = f"\n📊 RSI ANALİZİ - {condition.upper()} SEVIYE\n"
        response += f"{'='*40}\n\n"
        
        rsi_funds = []
        
        for fcode in self.active_funds[:30]:
            try:
                data = self.coordinator.db.get_fund_price_history(fcode, 30)
                
                if len(data) >= 20:
                    prices = data.set_index('pdate')['price'].sort_index()
                    
                    # RSI hesapla
                    delta = prices.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    current_rsi = rsi.iloc[-1]
                    
                    # Koşulu kontrol et
                    condition_met = False
                    if is_oversold and current_rsi < threshold:
                        condition_met = True
                    elif is_overbought and current_rsi > threshold:
                        condition_met = True
                    elif not is_oversold and not is_overbought:  # Neutral zone
                        condition_met = 40 <= current_rsi <= 60
                    
                    if condition_met:
                        details = self.coordinator.db.get_fund_details(fcode)
                        fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                        
                        rsi_funds.append({
                            'fcode': fcode,
                            'rsi': current_rsi,
                            'current_price': prices.iloc[-1],
                            'fund_name': fund_name
                        })
                        
            except Exception:
                continue
        
        # RSI değerine göre sırala
        if is_oversold:
            rsi_funds.sort(key=lambda x: x['rsi'])  # En düşük önce
        else:
            rsi_funds.sort(key=lambda x: x['rsi'], reverse=True)  # En yüksek önce
        
        if rsi_funds:
            response += f"🎯 RSI {condition.upper()} FONLAR ({len(rsi_funds)} fon):\n\n"
            
            for i, fund in enumerate(rsi_funds[:10], 1):
                rsi_value = fund['rsi']
                
                # RSI kategorisi
                if rsi_value < 30:
                    rsi_category = "🔴 AŞIRI SATIM"
                elif rsi_value > 70:
                    rsi_category = "🟢 AŞIRI ALIM"
                elif 30 <= rsi_value <= 50:
                    rsi_category = "🟡 DÜŞÜK"
                elif 50 < rsi_value <= 70:
                    rsi_category = "🟠 YÜKSEK"
                else:
                    rsi_category = "⚪ NORMAL"
                
                response += f"{i:2d}. {fund['fcode']} - {rsi_category}\n"
                response += f"    📊 RSI: {rsi_value:.1f}\n"
                response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
                if fund['fund_name'] != 'N/A':
                    response += f"    📝 Adı: {fund['fund_name'][:35]}...\n"
                response += f"\n"
            
            # Ekstrem değer
            extreme = rsi_funds[0]
            response += f"🏆 EN EKSTREM DEĞER:\n"
            response += f"   {extreme['fcode']}: RSI = {extreme['rsi']:.1f}\n"
            
        else:
            response += f"❌ RSI {condition} seviyesinde fon bulunamadı.\n"
            response += f"💡 Farklı RSI eşiği veya zaman aralığı deneyin.\n"
        
        response += f"\n📋 RSI SEVİYE AÇIKLAMASI:\n"
        response += f"   • RSI < 30: Aşırı satım (Potansiyel alım fırsatı)\n"
        response += f"   • RSI > 70: Aşırı alım (Potansiyel satım sinyali)\n"
        response += f"   • 30-70: Normal işlem aralığı\n"
        response += f"   • Hesaplama: 14-günlük periyot\n"
        
        return response

    def _handle_moving_average_signals(self, question):
        """Hareketli ortalama sinyalleri"""
        print("📊 Hareketli ortalama sinyalleri analiz ediliyor...")
        
        response = f"\n📊 HAREKETLİ ORTALAMA SİNYALLERİ\n"
        response += f"{'='*40}\n\n"
        
        ma_funds = []
        
        for fcode in self.active_funds[:25]:
            try:
                data = self.coordinator.db.get_fund_price_history(fcode, 60)
                
                if len(data) >= 50:
                    prices = data.set_index('pdate')['price'].sort_index()
                    
                    # Hareketli ortalamaları hesapla
                    sma_20 = prices.rolling(window=20).mean()
                    sma_50 = prices.rolling(window=50).mean()
                    
                    current_price = prices.iloc[-1]
                    current_sma20 = sma_20.iloc[-1]
                    current_sma50 = sma_50.iloc[-1]
                    
                    # Golden Cross (SMA20 > SMA50) ve Death Cross (SMA20 < SMA50)
                    if current_sma20 > current_sma50:
                        signal = "Golden Cross"
                        signal_type = "🟢 ALIM"
                    elif current_sma20 < current_sma50:
                        signal = "Death Cross"
                        signal_type = "🔴 SATIM"
                    else:
                        signal = "Neutral"
                        signal_type = "🟡 NÖTR"
                    
                    # Fiyat pozisyonu
                    if current_price > current_sma20:
                        price_position = "SMA20 üstünde"
                    else:
                        price_position = "SMA20 altında"
                    
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                    
                    ma_funds.append({
                        'fcode': fcode,
                        'signal': signal,
                        'signal_type': signal_type,
                        'current_price': current_price,
                        'sma_20': current_sma20,
                        'sma_50': current_sma50,
                        'price_position': price_position,
                        'ma_spread': ((current_sma20 / current_sma50) - 1) * 100,
                        'fund_name': fund_name
                    })
                    
            except Exception:
                continue
        
        # Sinyale göre grupla
        golden_cross = [f for f in ma_funds if f['signal'] == 'Golden Cross']
        death_cross = [f for f in ma_funds if f['signal'] == 'Death Cross']
        
        response += f"🟢 GOLDEN CROSS SİNYALLERİ ({len(golden_cross)} fon):\n"
        
        for i, fund in enumerate(golden_cross[:5], 1):
            response += f"{i}. {fund['fcode']} - {fund['signal_type']}\n"
            response += f"   💲 Fiyat: {fund['current_price']:.4f} TL\n"
            response += f"   📊 SMA20: {fund['sma_20']:.4f} TL\n"
            response += f"   📈 SMA50: {fund['sma_50']:.4f} TL\n"
            response += f"   📍 Fark: %{fund['ma_spread']:+.2f}\n"
            response += f"\n"
        
        response += f"\n🔴 DEATH CROSS SİNYALLERİ ({len(death_cross)} fon):\n"
        
        for i, fund in enumerate(death_cross[:5], 1):
            response += f"{i}. {fund['fcode']} - {fund['signal_type']}\n"
            response += f"   💲 Fiyat: {fund['current_price']:.4f} TL\n"
            response += f"   📊 SMA20: {fund['sma_20']:.4f} TL\n"
            response += f"   📈 SMA50: {fund['sma_50']:.4f} TL\n"
            response += f"   📍 Fark: %{fund['ma_spread']:+.2f}\n"
            response += f"\n"
        
        response += f"\n📋 HAREKETLİ ORTALAMA AÇIKLAMASI:\n"
        response += f"   • Golden Cross: SMA20 > SMA50 (Alım sinyali)\n"
        response += f"   • Death Cross: SMA20 < SMA50 (Satım sinyali)\n"
        response += f"   • SMA20: 20-günlük basit hareketli ortalama\n"
        response += f"   • SMA50: 50-günlük basit hareketli ortalama\n"
        
        return response

    def _handle_general_technical_signals(self, question):
        """Genel teknik sinyal analizi"""
        print("📊 Genel teknik sinyaller analiz ediliyor...")
        
        response = f"\n📊 GENEL TEKNİK SİNYAL ANALİZİ\n"
        response += f"{'='*40}\n\n"
        
        signal_funds = []
        
        for fcode in self.active_funds[:20]:
            try:
                data = self.coordinator.db.get_fund_price_history(fcode, 50)
                
                if len(data) >= 30:
                    prices = data.set_index('pdate')['price'].sort_index()
                    
                    # RSI
                    delta = prices.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    current_rsi = rsi.iloc[-1]
                    
                    # MACD
                    ema_12 = prices.ewm(span=12).mean()
                    ema_26 = prices.ewm(span=26).mean()
                    macd_line = ema_12 - ema_26
                    signal_line = macd_line.ewm(span=9).mean()
                    macd_signal = macd_line.iloc[-1] - signal_line.iloc[-1]
                    
                    # SMA
                    sma_20 = prices.rolling(window=20).mean()
                    price_vs_sma = ((prices.iloc[-1] / sma_20.iloc[-1]) - 1) * 100
                    
                    # Kombine sinyal skoru
                    signal_score = 0
                    
                    # RSI katkısı
                    if current_rsi < 30:
                        signal_score += 2  # Güçlü alım
                    elif current_rsi < 50:
                        signal_score += 1  # Zayıf alım
                    elif current_rsi > 70:
                        signal_score -= 2  # Güçlü satım
                    elif current_rsi > 60:
                        signal_score -= 1  # Zayıf satım
                    
                    # MACD katkısı
                    if macd_signal > 0:
                        signal_score += 1
                    else:
                        signal_score -= 1
                    
                    # SMA katkısı
                    if price_vs_sma > 0:
                        signal_score += 1
                    else:
                        signal_score -= 1
                    
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                    
                    signal_funds.append({
                        'fcode': fcode,
                        'signal_score': signal_score,
                        'rsi': current_rsi,
                        'macd_signal': macd_signal,
                        'price_vs_sma': price_vs_sma,
                        'current_price': prices.iloc[-1],
                        'fund_name': fund_name
                    })
                    
            except Exception:
                continue
        
        # Sinyal skoruna göre sırala
        signal_funds.sort(key=lambda x: x['signal_score'], reverse=True)
        
        if signal_funds:
            response += f"🟢 EN GÜÇLÜ ALIM SİNYALLERİ:\n\n"
            
            buy_signals = [f for f in signal_funds if f['signal_score'] > 0]
            for i, fund in enumerate(buy_signals[:5], 1):
                response += f"{i}. {fund['fcode']} (Skor: +{fund['signal_score']})\n"
                response += f"   📊 RSI: {fund['rsi']:.1f}\n"
                response += f"   📈 MACD: {fund['macd_signal']:+.6f}\n"
                response += f"   📍 SMA20 vs Fiyat: %{fund['price_vs_sma']:+.2f}\n"
                response += f"   💲 Fiyat: {fund['current_price']:.4f} TL\n"
                response += f"\n"
            
            response += f"\n🔴 EN GÜÇLÜ SATIM SİNYALLERİ:\n\n"
            
            sell_signals = [f for f in signal_funds if f['signal_score'] < 0]
            for i, fund in enumerate(sell_signals[-5:], 1):
                response += f"{i}. {fund['fcode']} (Skor: {fund['signal_score']})\n"
                response += f"   📊 RSI: {fund['rsi']:.1f}\n"
                response += f"   📈 MACD: {fund['macd_signal']:+.6f}\n"
                response += f"   📍 SMA20 vs Fiyat: %{fund['price_vs_sma']:+.2f}\n"
                response += f"   💲 Fiyat: {fund['current_price']:.4f} TL\n"
                response += f"\n"
            
        else:
            response += f"❌ Teknik sinyal hesaplanamadı.\n"
        
        response += f"\n📋 SİNYAL SKORLAMA SİSTEMİ:\n"
        response += f"   • RSI < 30: +2 puan (Güçlü alım)\n"
        response += f"   • MACD > Signal: +1 puan\n"
        response += f"   • Fiyat > SMA20: +1 puan\n"
        response += f"   • Toplam: -4 ile +4 arası\n"
        
        return response





    def _handle_safest_funds_sql_fast(self, count=10):
        """SQL tabanlı süper hızlı güvenli fonlar - Kullanıcı sayısına göre"""
        print(f"🛡️ SQL ile en güvenli {count} fon analizi...")
        
        try:
            # SQL için biraz fazla çek
            sql_limit = count * 2
            
            query = f"""
            WITH recent_prices AS (
                SELECT fcode, price, pdate,
                    LAG(price) OVER (PARTITION BY fcode ORDER BY pdate) as prev_price
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '30 days'
                AND price > 0
            ),
            returns AS (
                SELECT fcode, 
                    (price - prev_price) / prev_price as daily_return
                FROM recent_prices 
                WHERE prev_price IS NOT NULL
            ),
            volatility_calc AS (
                SELECT fcode,
                    COUNT(*) as data_points,
                    AVG(daily_return) as avg_return,
                    STDDEV(daily_return) * 100 as volatility,
                    MIN(daily_return) as min_return,
                    MAX(daily_return) as max_return
                FROM returns
                GROUP BY fcode
                HAVING COUNT(*) >= 15  -- En az 15 gün veri
            )
            SELECT fcode, volatility, avg_return, data_points
            FROM volatility_calc
            WHERE volatility > 0
            ORDER BY volatility ASC
            LIMIT {sql_limit}
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return "❌ SQL analizi sonuç vermedi."
            
            # Kullanıcının istediği sayıda al
            top_results = result.head(count)
            
            print(f"   ⚡ SQL ile {len(result)} fon analiz edildi, {len(top_results)} gösteriliyor")
            
            # Fund details al (sadece gösterilecek fonlar için)
            fund_details = {}
            for _, row in top_results.iterrows():
                fcode = row['fcode']
                try:
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_details[fcode] = {
                        'name': details.get('fund_name', 'N/A') if details else 'N/A',
                        'type': details.get('fund_type', 'N/A') if details else 'N/A'
                    }
                except:
                    fund_details[fcode] = {'name': 'N/A', 'type': 'N/A'}
            
            # Sonuçları formatla
            response = f"\n🛡️ EN GÜVENLİ {count} FON (SQL Hızlı Analiz)\n"
            response += f"{'='*45}\n\n"
            response += f"📊 ANALİZ SONUCU:\n"
            response += f"   • İstenen Fon: {count}\n"
            response += f"   • SQL Analizi: {len(result)} fon\n"
            response += f"   • En Düşük Volatilite: %{top_results.iloc[0]['volatility']:.2f}\n\n"
            
            for i, (_, row) in enumerate(top_results.iterrows(), 1):
                fcode = row['fcode']
                volatility = float(row['volatility'])
                avg_return = float(row['avg_return']) * 100
                data_points = int(row['data_points'])
                
                # Risk kategorisi
                if volatility < 1:
                    risk = "🟢 ÇOK GÜVENLİ"
                elif volatility < 2:
                    risk = "🟡 GÜVENLİ"
                elif volatility < 4:
                    risk = "🟠 ORTA"
                else:
                    risk = "🔴 RİSKLİ"
                
                response += f"{i:2d}. {fcode} - {risk}\n"
                response += f"    📉 Volatilite: %{volatility:.2f}\n"
                response += f"    📊 Ortalama Getiri: %{avg_return:+.3f}\n"
                response += f"    📈 Veri Noktası: {data_points}\n"
                response += f"    🏷️ Tür: {fund_details[fcode]['type']}\n"
                if fund_details[fcode]['name'] != 'N/A':
                    response += f"    📝 Adı: {fund_details[fcode]['name'][:35]}...\n"
                response += f"\n"
            
            # İstatistikler
            avg_vol = top_results['volatility'].mean()
            avg_ret = top_results['avg_return'].mean() * 100
            
            response += f"📊 {count} FON ÖZET İSTATİSTİKLER:\n"
            response += f"   Ortalama Volatilite: %{avg_vol:.2f}\n"
            response += f"   Ortalama Getiri: %{avg_ret:+.2f}\n"
            response += f"   En Güvenli: {top_results.iloc[0]['fcode']}\n"
            
            return response
            
        except Exception as e:
            print(f"   ❌ SQL analizi hatası: {e}")
            # Fallback: Hızlı Python versiyonu
            return self._handle_safest_funds_list_fallback(count)

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

    def _handle_riskiest_funds_list(self, count=10, days=60):
        """En riskli fonların listesi (yüksek volatilite)"""
        print(f"📈 En riskli {count} fon analiz ediliyor...")
        
        risky_funds = []
        
        for fcode in self.active_funds[:50]:
            try:
                data = self.coordinator.db.get_fund_price_history(fcode, days)
                
                if len(data) >= 20:
                    prices = data.set_index('pdate')['price'].sort_index()
                    returns = prices.pct_change().dropna()
                    
                    volatility = returns.std() * 100
                    total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                    
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                    
                    risky_funds.append({
                        'fcode': fcode,
                        'volatility': volatility,
                        'total_return': total_return,
                        'current_price': prices.iloc[-1],
                        'fund_name': fund_name
                    })
                    
            except Exception:
                continue
        
        # Volatiliteye göre sırala (en yüksek = en riskli)
        risky_funds.sort(key=lambda x: x['volatility'], reverse=True)
        
        if risky_funds:
            response = f"\n📈 EN RİSKLİ {count} FON (Yüksek Volatilite)\n"
            response += f"{'='*45}\n\n"
            
            for i, fund in enumerate(risky_funds[:count], 1):
                response += f"{i:2d}. {fund['fcode']}\n"
                response += f"    📈 Risk (Volatilite): %{fund['volatility']:.2f}\n"
                response += f"    📊 Getiri: %{fund['total_return']:+.2f}\n"
                response += f"    💲 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
                if fund['fund_name'] != 'N/A':
                    response += f"    📝 Adı: {fund['fund_name'][:45]}...\n"
                response += f"\n"
            
            return response
        else:
            return f"❌ Riskli fon analizi yapılamadı."

    def _handle_worst_funds_list(self, count=10, days=60):
        """En çok kaybettiren fonların listesi"""
        print(f"🔻 En çok kaybettiren {count} fon analiz ediliyor...")
        
        worst_funds = []
        
        for fcode in self.active_funds[:50]:
            try:
                data = self.coordinator.db.get_fund_price_history(fcode, days)
                
                if len(data) >= 10:
                    prices = data['price']
                    total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                    
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                    
                    worst_funds.append({
                        'fcode': fcode,
                        'total_return': total_return,
                        'current_price': prices.iloc[-1],
                        'fund_name': fund_name
                    })
                    
            except Exception:
                continue
        
        # Getiriye göre sırala (en düşük = en kötü)
        worst_funds.sort(key=lambda x: x['total_return'])
        
        if worst_funds:
            response = f"\n🔻 EN ÇOK KAYBETTİREN {count} FON (Son {days} Gün)\n"
            response += f"{'='*55}\n\n"
            
            for i, fund in enumerate(worst_funds[:count], 1):
                response += f"{i:2d}. {fund['fcode']}\n"
                response += f"    📉 Kayıp: %{fund['total_return']:.2f}\n"
                response += f"    💲 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
                if fund['fund_name'] != 'N/A':
                    response += f"    📝 Adı: {fund['fund_name'][:45]}...\n"
                response += f"\n"
            
            return response
        else:
            return f"❌ Kayıp analizi yapılamadı."

    def _handle_low_volatility_funds_question(self, question):
        import re
        m = re.search(r'volatilite.*?(\d+)', question)
        threshold = 10  # default
        if m:
            threshold = float(m.group(1))
        results = []
        for fcode in self.active_funds:
            data = self.coordinator.db.get_fund_price_history(fcode, 60)
            if not data.empty:
                prices = data.set_index('pdate')['price'].sort_index()
                returns = prices.pct_change().dropna()
                volatility = returns.std() * 100
                if volatility < threshold:
                    results.append((fcode, volatility))
        if not results:
            return f"Volatilitesi {threshold}'in altında fon bulunamadı."
        response = f"\n📉 Volatilitesi {threshold}'in Altında Fonlar\n"
        for fcode, vol in results:
            response += f"{fcode}: Volatilite: %{vol:.2f}\n"
        return response
    def _handle_top_sharpe_funds_question(self, question):
        results = []
        for fcode in self.active_funds:
            data = self.coordinator.db.get_fund_price_history(fcode, 60)
            if not data.empty:
                prices = data.set_index('pdate')['price'].sort_index()
                returns = prices.pct_change().dropna()
                annual_return = (prices.iloc[-1] / prices.iloc[0] - 1) * (252 / len(prices)) * 100
                volatility = returns.std() * np.sqrt(252) * 100
                sharpe = (annual_return - 15) / volatility if volatility > 0 else 0
                results.append((fcode, sharpe))
        if not results:
            return "Sharpe oranı hesaplanamadı."
        results.sort(key=lambda x: x[1], reverse=True)
        response = "\n🏆 Sharpe Oranı En Yüksek 3 Fon\n"
        for fcode, sharpe in results[:3]:
            response += f"{fcode}: Sharpe Oranı: {sharpe:.2f}\n"
        return response
    def _handle_top_loser_fund_question(self, question):
        min_return = 999
        worst_fund = None
        for fcode in self.active_funds:
            data = self.coordinator.db.get_fund_price_history(fcode, 30)
            if not data.empty:
                prices = data['price']
                ret = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                if ret < min_return:
                    min_return = ret
                    worst_fund = fcode
        if worst_fund:
            return f"🔻 Son 30 günde en çok kaybettiren fon: {worst_fund}\nGetiri: %{min_return:.2f}"
        else:
            return "En çok kaybettiren fon bulunamadı."
    def _handle_top_gainer_fund_question(self, question):
        max_return = -999
        best_fund = None
        for fcode in self.active_funds:
            data = self.coordinator.db.get_fund_price_history(fcode, 30)
            if not data.empty:
                prices = data['price']
                ret = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                if ret > max_return:
                    max_return = ret
                    best_fund = fcode
        if best_fund:
            return f"🚀 Son 30 günde en çok kazandıran fon: {best_fund}\nGetiri: %{max_return:.2f}"
        else:
            return "En çok kazandıran fon bulunamadı."
    def _handle_fund_past_performance_question(self, question):
        words = question.upper().split()
        fund_code = None
        for word in words:
            if len(word) == 3 and word.isalpha():
                if word.upper() in [x.upper() for x in self.active_funds]:
                    fund_code = word.upper()
                    break
        if not fund_code:
            return "❌ Geçerli bir fon kodu tespit edilemedi."
        data = self.coordinator.db.get_fund_price_history(fund_code, 252)
        if data.empty:
            return f"❌ {fund_code} için 1 yıllık veri bulunamadı."
        prices = data.set_index('pdate')['price'].sort_index()
        total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
        response = f"\n📈 {fund_code} FONU SON 1 YIL PERFORMANSI\n{'='*40}\n"
        response += f"Başlangıç Fiyatı: {prices.iloc[0]:.4f} TL\n"
        response += f"Son Fiyat: {prices.iloc[-1]:.4f} TL\n"
        response += f"Toplam Getiri: %{total_return:.2f}\n"
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

    def _handle_most_risky_fund(self, days=60):
        """En riskli (volatilitesi en yüksek) fonu bulur"""
        max_risk_fund = None
        max_vol = -1
        for fcode in self.active_funds:
            data = self.coordinator.db.get_fund_price_history(fcode, days)
            if not data.empty:
                returns = data['price'].pct_change().dropna()
                volatility = returns.std() * 100
                if volatility > max_vol:
                    max_vol = volatility
                    max_risk_fund = fcode
        if max_risk_fund:
            return f"📈 Son {days} günde volatilitesi en yüksek fon: **{max_risk_fund}**\nRisk (Volatilite): %{max_vol:.2f}"
        else:
            return "En riskli fon tespit edilemedi."

    def _handle_safest_fund(self, days=60):
        """En güvenli (en düşük volatilite) fonu bulur"""
        min_risk_fund = None
        min_vol = 1e9
        for fcode in self.active_funds:
            data = self.coordinator.db.get_fund_price_history(fcode, days)
            if not data.empty:
                returns = data['price'].pct_change().dropna()
                volatility = returns.std() * 100
                if volatility < min_vol:
                    min_vol = volatility
                    min_risk_fund = fcode
        if min_risk_fund:
            return f"🛡️ Son {days} günde volatilitesi en düşük fon: **{min_risk_fund}**\nRisk (Volatilite): %{min_vol:.2f}"
        else:
            return "En güvenli fon tespit edilemedi."

    def _handle_worst_fund(self, days=60):
        """En çok kaybettiren fonu bulur"""
        min_return_fund = None
        min_return = 1e9
        for fcode in self.active_funds:
            data = self.coordinator.db.get_fund_price_history(fcode, days)
            if not data.empty:
                prices = data['price']
                ret = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                if ret < min_return:
                    min_return = ret
                    min_return_fund = fcode
        if min_return_fund:
            return f"🔻 Son {days} günde en çok kaybettiren fon: **{min_return_fund}**\nGetiri: %{min_return:.2f}"
        else:
            return "En çok kaybettiren fon tespit edilemedi."    
    def _handle_2025_recommendation_dual(self, question):
            """2025 fon önerisi - Her iki AI ile analiz"""
            print("🎯 2025 Fund Recommendation Analysis - Dual AI...")
            
            # Tutar parsing
            import re
            amounts = re.findall(r'\b(\d{5,})\b', question)
            investment_amount = 100000
            if amounts:
                try:
                    investment_amount = int(amounts[0])
                except:
                    pass
            
            # Risk toleransını tespit et
            risk_tolerance = "moderate"
            if any(word in question.lower() for word in ['güvenli', 'safe', 'conservative']):
                risk_tolerance = "conservative"
            elif any(word in question.lower() for word in ['agresif', 'aggressive', 'risk']):
                risk_tolerance = "aggressive"
            
            print(f"📊 Analysis Parameters:")
            print(f"   Risk Tolerance: {risk_tolerance}")
            print(f"   Investment Amount: {investment_amount:,.0f} TL")
            
            # Veritabanı analizi (önceki kodla aynı)
            analysis_results = []
            test_funds = self.active_funds[:10]
            
            print(f"\n🔍 Analyzing {len(test_funds)} funds...")
            
            for i, fcode in enumerate(test_funds):
                try:
                    print(f"   [{i+1}/{len(test_funds)}] {fcode}...", end='')
                    
                    data = self.coordinator.db.get_fund_price_history(fcode, 60)
                    
                    if len(data) >= 20:
                        prices = data.set_index('pdate')['price'].sort_index()
                        returns = prices.pct_change().dropna()
                        
                        # Basit metrikler
                        total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                        annual_return = total_return * (252 / len(prices))
                        volatility = returns.std() * np.sqrt(252) * 100
                        sharpe = (annual_return - 15) / volatility if volatility > 0 else 0
                        win_rate = (returns > 0).sum() / len(returns) * 100
                        
                        # 2025 skorunu hesapla
                        score = self._calculate_2025_score(annual_return, volatility, sharpe, win_rate, risk_tolerance)
                        
                        analysis_results.append({
                            'fund_code': fcode,
                            'annual_return': annual_return,
                            'volatility': volatility,
                            'sharpe_ratio': sharpe,
                            'win_rate': win_rate,
                            'score_2025': score,
                            'current_price': prices.iloc[-1]
                        })
                        
                        print(f" ✅ (Score: {score:.1f})")
                    else:
                        print(" ❌")
                        
                except Exception as e:
                    print(f" ❌")
                    continue
            
            if not analysis_results:
                return "❌ Analiz için yeterli veri bulunamadı."
            
            # Sonuçları sırala
            df = pd.DataFrame(analysis_results)
            df = df.sort_values('score_2025', ascending=False)
            
            # Raporu oluştur
            response = f"\n🎯 2025 YIL SONU FON ÖNERİSİ RAPORU (DUAL AI)\n"
            response += f"{'='*55}\n\n"
            
            response += f"📊 ANALİZ PARAMETRELERİ:\n"
            response += f"   • Risk Toleransı: {risk_tolerance.upper()}\n"
            response += f"   • Yatırım Tutarı: {investment_amount:,.0f} TL\n"
            response += f"   • Analiz Edilen Fon: {len(df)}\n\n"
            
            # VERİTABANI ANALİZİ SONUÇLARI
            response += f"📈 VERİTABANI ANALİZİ - EN İYİ 5 FON:\n"
            top_5 = df.head(5)
            
            for i, (_, fund) in enumerate(top_5.iterrows(), 1):
                response += f"\n{i}. {fund['fund_code']} (2025 Skoru: {fund['score_2025']:.1f}/100)\n"
                response += f"   📊 Beklenen Yıllık Getiri: %{fund['annual_return']:.1f}\n"
                response += f"   📉 Risk (Volatilite): %{fund['volatility']:.1f}\n"
                response += f"   ⚡ Sharpe Oranı: {fund['sharpe_ratio']:.3f}\n"
                response += f"   🎯 Kazanma Oranı: %{fund['win_rate']:.1f}\n"
                response += f"   💰 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
            
            # PORTFÖY ÖNERİSİ
            response += f"\n💼 2025 PORTFÖY ÖNERİSİ ({investment_amount:,.0f} TL):\n"
            
            if len(top_5) >= 3:
                # Risk toleransına göre ağırlık dağılımı
                if risk_tolerance == "conservative":
                    weights = [0.4, 0.3, 0.2, 0.1, 0.0][:len(top_5)]
                elif risk_tolerance == "aggressive":
                    weights = [0.35, 0.25, 0.2, 0.15, 0.05][:len(top_5)]
                else:  # moderate
                    weights = [0.35, 0.25, 0.2, 0.15, 0.05][:len(top_5)]
                
                # Normalize weights
                weights = weights[:len(top_5)]
                weights = [w/sum(weights) for w in weights]
                
                portfolio_return = 0
                
                for i, ((_, fund), weight) in enumerate(zip(top_5.iterrows(), weights)):
                    amount = investment_amount * weight
                    portfolio_return += fund['annual_return'] * weight
                    
                    response += f"   {fund['fund_code']}: %{weight*100:.0f} ({amount:,.0f} TL)\n"
                    response += f"      Beklenen Katkı: %{fund['annual_return']*weight:.1f}\n"
                
                response += f"\n📊 PORTFÖY BEKLENTİLERİ:\n"
                response += f"   📈 Beklenen Yıllık Getiri: %{portfolio_return:.1f}\n"
            
            # ÇİFT AI ANALİZİ - HER İKİSİNİ DE ÇALIŞTIR
            response += f"\n🤖 ÇİFT AI YORUMLARI:\n"
            response += f"{'='*25}\n"
            fund_descriptions = []
            for fund_code in top_5.head(3)['fund_code']:
                details = self.coordinator.db.get_fund_details(fund_code)
                if not details:
                    details = {}
                name = details.get('fund_name', '')
                category = details.get('fund_category', '')
                fund_type = details.get('fund_type', '')
                description = details.get('description', '')
                summary = f"{fund_code}: {name} - {category} - {fund_type}. {description}"
                fund_descriptions.append(summary)

            # AI prompt hazırla
            ai_prompt = f"""
            2025 yılı için TEFAS fon analizi sonuçları:
            
            En iyi 3 fon: {chr(10).join(fund_descriptions)}

            Ortalama beklenen getiri: %{top_5.head(3)['annual_return'].mean():.1f}
            Risk toleransı: {risk_tolerance}
            Yatırım tutarı: {investment_amount:,.0f} TL

            Yukarıdaki bilgilerle bu fonların yatırımcısı için risk/getiri profili ve stratejisi hakkında maksimum 300 kelimeyle değerlendirme ve öneri yap.
            """
            
            # OpenAI Analizi
            if self.ai_status['openai']:
                print("🤖 OpenAI analizi yapılıyor...")
                try:
                    openai_response = self.coordinator.ai_analyzer.query_openai(
                        ai_prompt, 
                        "Sen TEFAS uzmanı bir finansal analistsin."
                    )
                    response += f"\n📱 OpenAI (GPT) Değerlendirmesi:\n"
                    response += f"   {openai_response}\n"
                except Exception as e:
                    response += f"\n📱 OpenAI Değerlendirmesi:\n"
                    response += f"   ❌ Analiz alınamadı: {str(e)[:100]}\n"
            else:
                response += f"\n📱 OpenAI: ❌ Mevcut değil\n"
            
            # Ollama Analizi
            if self.ai_status['ollama']:
                print("🦙 Ollama analizi yapılıyor...")
                try:
                    ollama_response = self.coordinator.ai_analyzer.query_ollama(
                        ai_prompt,
                        "Sen TEFAS uzmanı bir finansal analistsin."
                    )
                    response += f"\n🦙 Ollama (Mistral) Değerlendirmesi:\n"
                    response += f"   {ollama_response}\n"
                except Exception as e:
                    response += f"\n🦙 Ollama Değerlendirmesi:\n"
                    response += f"   ❌ Analiz alınamadı: {str(e)[:100]}\n"
            else:
                response += f"\n🦙 Ollama: ❌ Mevcut değil\n"
            
            # AI Karşılaştırma Özeti
            if self.ai_status['openai'] and self.ai_status['ollama']:
                response += f"\n🎯 AI KARŞILAŞTIRMASI:\n"
                response += f"   Her iki AI de analiz tamamlandı. Yukarıdaki yorumları karşılaştırabilirsiniz.\n"
                response += f"   OpenAI genellikle daha detaylı, Ollama daha özlü yorumlar yapar.\n"
            
            # RİSK UYARILARI
            response += f"\n⚠️ 2025 RİSK UYARILARI:\n"
            response += f"   • Geçmiş performans gelecek getiriyi garanti etmez\n"
            response += f"   • Türkiye ekonomik göstergelerini takip edin\n"
            response += f"   • Portföyü çeyrek yıllık gözden geçirin\n"
            response += f"   • AI öneriler bilgilendirme amaçlıdır, yatırım tavsiyesi değildir\n"
            
            response += f"\n✅ Dual AI analizi tamamlandı: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            
            return response
    
    def _handle_analysis_question_dual(self, question):
        """Tek fon analizi - Her iki AI ile (fonun detayları AI prompt'una eklenir)"""
        words = question.upper().split()
        fund_code = None

        for word in words:
            if len(word) == 3 and word.isalpha():
                if word.upper() in [x.upper() for x in self.active_funds]:
                    fund_code = word.upper()
                    break
        # Eğer aktif fonlar içinde bulamazsan, tüm fonlarda ara
        if not fund_code:
            all_funds = [x.upper() for x in self.coordinator.db.get_all_fund_codes()]
            for word in words:
                if len(word) == 3 and word.isalpha():
                    if word.upper() in all_funds:
                        fund_code = word.upper()
                        break
        if not fund_code:
            return f"❌ Geçerli bir fon kodu bulunamadı. Örnek: 'AKB fonunu analiz et'\nMevcut fonlar: {', '.join(self.active_funds[:10])}..."

        try:
            print(f"🔍 {fund_code} fonu dual AI analizi...")

            # Veritabanı analizi
            data = self.coordinator.db.get_fund_price_history(fund_code, 100)

            if data.empty:
                return f"❌ {fund_code} için veri bulunamadı"

            prices = data.set_index('pdate')['price'].sort_index()
            returns = prices.pct_change().dropna()

            # Temel metrikler
            total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
            annual_return = total_return * (252 / len(prices))
            volatility = returns.std() * np.sqrt(252) * 100
            sharpe = (annual_return - 15) / volatility if volatility > 0 else 0
            win_rate = (returns > 0).sum() / len(returns) * 100

            # --- FON DETAYLARI ---
            details = self.coordinator.db.get_fund_details(fund_code) if hasattr(self.coordinator.db, 'get_fund_details') else {}
            name = details.get('fund_name', '')
            category = details.get('fund_category', '')
            fund_type = details.get('fund_type', '')
            description = details.get('description', '')
            details_text = f"{fund_code}: {name} - {category} - {fund_type}. {description}".strip()

            # Sonuçları formatla
            response = f"\n📊 {fund_code} FONU DUAL AI ANALİZ RAPORU\n"
            response += f"{'='*45}\n\n"

            response += f"💰 TEMEL VERİLER:\n"
            response += f"   Güncel Fiyat: {prices.iloc[-1]:.4f} TL\n"
            response += f"   Son {len(prices)} Gün Getiri: %{total_return:.2f}\n"
            response += f"   Yıllık Getiri (Tahmini): %{annual_return:.1f}\n"
            response += f"   Volatilite: %{volatility:.1f}\n"
            response += f"   Sharpe Oranı: {sharpe:.3f}\n"
            response += f"   Kazanma Oranı: %{win_rate:.1f}\n\n"

            # AI Analizleri
            ai_prompt = f"""
            {details_text}

            Analiz verileri:
            Güncel Fiyat: {prices.iloc[-1]:.4f} TL
            Yıllık Getiri: %{annual_return:.1f}
            Volatilite: %{volatility:.1f}
            Sharpe Oranı: {sharpe:.3f}
            Kazanma Oranı: %{win_rate:.1f}
            Veri Periyodu: {len(prices)} gün

            Yukarıdaki fon bilgileriyle, bu fonun risk ve getiri profilini, avantaj/dezavantajlarını ve hangi yatırımcıya uygun olabileceğini 150 kelimeyi aşmadan açıklayıp özetle.
            """

            response += f"🤖 DUAL AI DEĞERLENDİRMESİ:\n"
            response += f"{'='*30}\n"

            # OpenAI
            if self.ai_status['openai']:
                try:
                    openai_analysis = self.coordinator.ai_analyzer.query_openai(
                        ai_prompt,
                        "Sen TEFAS fonu uzmanısın."
                    )
                    response += f"\n📱 OpenAI Analizi:\n{openai_analysis}\n"
                except Exception as e:
                    response += f"\n📱 OpenAI: ❌ Analiz alınamadı\n"

            # Ollama
            if self.ai_status['ollama']:
                try:
                    ollama_analysis = self.coordinator.ai_analyzer.query_ollama(
                        ai_prompt,
                        "Sen TEFAS fonu uzmanısın."
                    )
                    response += f"\n🦙 Ollama Analizi:\n{ollama_analysis}\n"
                except Exception as e:
                    response += f"\n🦙 Ollama: ❌ Analiz alınamadı\n"

            response += f"\n✅ Analiz tamamlandı: {datetime.now().strftime('%H:%M:%S')}\n"

            return response

        except Exception as e:
            return f"❌ Analiz hatası: {e}"
    
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
    
    def _handle_comparison_question(self, question):
        """Fon karşılaştırması (önceki kodla aynı)"""
        words = question.upper().split()
        fund_codes = []
        
        for word in words:
            if len(word) == 3 and word.isalpha():
                if word in self.active_funds:
                    fund_codes.append(word)
        
        if len(fund_codes) < 2:
            return f"❌ Karşılaştırma için en az 2 fon kodu gerekli. Örnek: 'AKB ve YAS karşılaştır'"
        
        try:
            comparison_data = []
            
            for fcode in fund_codes:
                data = self.coordinator.db.get_fund_price_history(fcode, 30)
                if not data.empty:
                    prices = data['price']
                    return_30d = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                    
                    comparison_data.append({
                        'fund': fcode,
                        'return_30d': return_30d,
                        'current_price': prices.iloc[-1]
                    })
            
            if not comparison_data:
                return "❌ Karşılaştırma için veri bulunamadı"
            
            response = f"\n⚖️ FON KARŞILAŞTIRMASI\n"
            response += f"{'='*22}\n\n"
            
            for fund_data in comparison_data:
                response += f"📊 {fund_data['fund']}:\n"
                response += f"   30 Gün Getiri: %{fund_data['return_30d']:.2f}\n"
                response += f"   Güncel Fiyat: {fund_data['current_price']:.4f} TL\n\n"
            
            # Kazanan
            best = max(comparison_data, key=lambda x: x['return_30d'])
            response += f"🏆 En İyi Performans: {best['fund']} (%{best['return_30d']:.2f})\n"
            
            return response
            
        except Exception as e:
            return f"❌ Karşılaştırma hatası: {e}"
    
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
    # 1. ANSWER_QUESTION metoduna eklenecek elif blokları
    # =============================================================
    
    def add_to_answer_question(self, question):
        """Bu blokları mevcut answer_question metoduna ekleyin"""
        question_lower = question.lower()
        
        # FUNDAMENTAL ANALİZ SORULARI - HEMEN EKLENEBİLİR! 🎯
        
        # 1. FON KAPASİTESİ SORULARI
        if any(word in question_lower for word in ['kapasite', 'büyüklük', 'büyük fon', 'capacity']):
            return self._handle_capacity_questions(question)
        
        # 2. YATIRIMCI SAYISI SORULARI  
        if any(word in question_lower for word in ['yatırımcı sayısı', 'investor count', 'popüler fon']):
            return self._handle_investor_count_questions(question)
        
        # 3. YENİ FONLAR SORULARI
        if any(word in question_lower for word in ['yeni fon', 'yeni kurulan', 'fresh fund', 'new fund']):
            return self._handle_new_funds_questions(question)
        
        # 4. EN BÜYÜK FONLAR SORULARI
        if any(word in question_lower for word in ['en büyük', 'largest', 'biggest', 'dev fon']):
            return self._handle_largest_funds_questions(question)
        
        # 5. FON YAŞI SORULARI
        if any(word in question_lower for word in ['en eski', 'köklü', 'oldest', 'kuruluş']):
            return self._handle_fund_age_questions(question)
        
        # 6. FON TİPİ/KATEGORİ SORULARI
        if any(word in question_lower for word in ['kategori', 'tür', 'type', 'category']):
            return self._handle_fund_category_questions(question)
        
        # 7. FON ŞİRKETİ BAZLI SORULAR
        if any(word in question_lower for word in ['hangi şirket', 'which company', 'portföy şirketi']):
            return self._handle_fund_company_questions(question)

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

    # def _handle_largest_funds_questions(self, question):
    #     """En büyük fonlar analizi"""
    #     print("🏢 En büyük fonlar analiz ediliyor...")
        
    #     response = f"\n🏢 EN BÜYÜK FONLAR ANALİZİ\n"
    #     response += f"{'='*35}\n\n"
        
    #     fund_sizes = []
        
    #     for fcode in self.active_funds[:50]:
    #         try:
    #             # Fund details'den kapasite bilgisi
    #             details = self.coordinator.db.get_fund_details(fcode)
                
    #             if details:
    #                 # Farklı büyüklük kriterleri
    #                 capacity = 0
    #                 investor_count = 0
                    
    #                 # Kapasite bilgisi
    #                 if 'fcapacity' in details:
    #                     try:
    #                         capacity = float(details['fcapacity'])
    #                     except:
    #                         capacity = 0
                    
    #                 # Son fiyat ve yatırımcı sayısı
    #                 data = self.coordinator.db.get_fund_price_history(fcode, 3)
    #                 if not data.empty:
    #                     current_price = data['price'].iloc[-1]
    #                     if 'investorcount' in data.columns:
    #                         investor_count = data['investorcount'].iloc[-1]
                        
    #                     # Kombinasyon skoru (kapasite + yatırımcı sayısı)
    #                     size_score = capacity + (investor_count * current_price * 1000)
                        
    #                     fund_sizes.append({
    #                         'fcode': fcode,
    #                         'capacity': capacity,
    #                         'investor_count': investor_count,
    #                         'current_price': current_price,
    #                         'size_score': size_score,
    #                         'fund_name': details.get('fund_name', 'N/A'),
    #                         'fund_type': details.get('fund_type', 'N/A')
    #                     })
                        
    #         except Exception:
    #             continue
        
    #     # Büyüklük skoruna göre sırala
    #     fund_sizes.sort(key=lambda x: x['size_score'], reverse=True)
        
    #     if fund_sizes:
    #         response += f"🏆 EN BÜYÜK 10 FON (Kombinasyon Skoruna Göre):\n\n"
            
    #         for i, fund in enumerate(fund_sizes[:10], 1):
    #             response += f"{i:2d}. {fund['fcode']}\n"
    #             response += f"    💰 Kapasite: {fund['capacity']:,.0f} TL\n"
    #             response += f"    👥 Yatırımcı: {fund['investor_count']:,} kişi\n"
    #             response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
    #             response += f"    📊 Büyüklük Skoru: {fund['size_score']:,.0f}\n"
    #             response += f"    🏷️ Tür: {fund['fund_type']}\n"
    #             if fund['fund_name'] != 'N/A':
    #                 response += f"    📝 Adı: {fund['fund_name'][:35]}...\n"
    #             response += f"\n"
            
    #         # Kategorilere göre en büyük
    #         response += f"📋 KATEGORİ LİDERLERİ:\n"
    #         response += f"   💰 En Büyük Kapasite: {max(fund_sizes, key=lambda x: x['capacity'])['fcode']}\n"
    #         response += f"   👥 En Çok Yatırımcı: {max(fund_sizes, key=lambda x: x['investor_count'])['fcode']}\n"
            
    #     else:
    #         response += f"❌ Fon büyüklük verileri alınamadı.\n"
        
    #     return response

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