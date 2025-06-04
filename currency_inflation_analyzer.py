# currency_inflation_analyzer.py
"""
TEFAS Döviz ve Enflasyon Analiz Sistemi
Dolar, Euro, TL bazlı fonlar ve enflasyon korumalı yatırım araçları analizi
"""

from datetime import datetime
import pandas as pd
import numpy as np
import logging
import time  
from database.connection import DatabaseManager
from config.config import Config

class CurrencyInflationAnalyzer:
    """Döviz ve Enflasyon analiz sistemi - TÜM VERİTABANI"""
    
    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.db = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 💱 DÖVIZ VE ENFLASYON KEYWORD MAPPING
        self.currency_keywords = {
            'usd': {
                'keywords': [
                    'DOLAR', 'DOLLAR', 'USD', 'ABD DOLARI', 'US DOLLAR',
                    'AMERİKAN DOLARI', 'DÖVİZ', 'FOREIGN CURRENCY',
                    'DOLAR CINSI', 'USD CINSI', '$'
                ],
                'description': 'Dolar bazlı ve dolar hedge fonları',
                'currency_code': 'USD',
                'portfolio_fields': ['foreigncurrencybills', 'foreigndebtinstruments', 'foreignexchangetradedfunds']
            },
            'eur': {
                'keywords': [
                    'EURO', 'EUR', 'AVRO', 'AVRUPA', 'EUROPEAN',
                    'EURO CINSI', 'EUR CINSI', '€', 'EUROZONE'
                ],
                'description': 'Euro bazlı ve euro hedge fonları',
                'currency_code': 'EUR',
                'portfolio_fields': ['foreigncurrencybills', 'foreigndebtinstruments', 'foreignexchangetradedfunds']
            },
            'tl_based': {
                'keywords': [
                    'TL', 'TÜRK LİRASI', 'TRY', 'TURKISH LIRA',
                    'TL CİNSİ', 'YERLİ PARA', 'LOKAL', 'LOCAL',
                    'TL BAZLI', 'TRY BASED'
                ],
                'description': 'TL bazlı güvenli fonlar',
                'currency_code': 'TRY',
                'portfolio_fields': ['governmentbond', 'treasurybill', 'termdeposittl', 'participationaccounttl']
            },
            'inflation_protected': {
                'keywords': [
                    'ENFLASYON', 'INFLATION', 'UFRS', 'CPI',
                    'ENFLASYON KORUMAL', 'INFLATION PROTECTED',
                    'REAL RETURN', 'REEL GETİRİ', 'İNDEXED',
                    'KIRA SERTIFIKASI', 'KIRA SERTIFIKAS',
                    'DEĞİŞKEN', 'VARIABLE', 'FLOATING'
                ],
                'description': 'Enflasyon korumalı ve değişken getirili fonlar',
                'currency_code': 'INFLATION',
                'portfolio_fields': ['governmentleasecertificates', 'privatesectorleasecertificates', 'governmentbond']
            },
            'hedge_funds': {
                'keywords': [
                    'HEDGE', 'KORUMA', 'KORUNMA', 'PROTECTED',
                    'DÖVİZ KORUMA', 'CURRENCY HEDGE', 'FORWARD',
                    'VADELI İŞLEM', 'DERIVATIVES', 'TÜREVLERİ',
                    'SWAP', 'OPTIONS', 'FUTURES'
                ],
                'description': 'Döviz hedge ve korunma fonları',
                'currency_code': 'HEDGE',
                'portfolio_fields': ['derivatives', 'futurescashcollateral']
            },
            'precious_metals': {
                'keywords': [
                    'ALTIN', 'GOLD', 'GÜMÜŞ', 'SILVER', 'PLATİN', 'PLATINUM',
                    'KIYMETLİ MADEN', 'PRECIOUS METALS', 'METAL',
                    'ALTIN FUND', 'GOLD FUND', 'ALTIN ETF'
                ],
                'description': 'Altın ve kıymetli maden fonları (enflasyon koruması)',
                'currency_code': 'GOLD',
                'portfolio_fields': ['preciousmetals', 'preciousmetalsbyf', 'preciousmetalskba', 'preciousmetalskks']
            }
        }
    
    @staticmethod
    def is_currency_inflation_question(question):
        """Döviz/enflasyon sorusu mu kontrol et"""
        question_lower = question.lower()
        
        # Ana keyword listesi
        currency_keywords = [
            'dolar', 'dollar', 'usd', 'euro', 'eur', 'avro',
            'döviz', 'currency', 'foreign', 'yabancı para',
            'enflasyon', 'inflation', 'hedge', 'koruma', 'korunma',
            'tl bazlı', 'tl cinsi', 'türk lirası', 'altin', 'gold',
            'kıymetli maden', 'precious metals'
        ]
        
        # Fon ile birlikte kullanım
        if any(word in question_lower for word in currency_keywords):
            if any(word in question_lower for word in ['fon', 'fund', 'yatırım']):
                return True
        
        # Özel kombinasyonlar
        special_combinations = [
            'dolar bazlı fonlar', 'euro fonları', 'enflasyon korumalı',
            'döviz hedge', 'tl en güvenli', 'altın fonları',
            'kıymetli maden fonları', 'yabancı para fonları'
        ]
        
        return any(combo in question_lower for combo in special_combinations)
    
    def analyze_currency_inflation_question(self, question):
        """Ana giriş noktası - MV versiyonunu kullan"""
        question_lower = question.lower()
        
        # Enflasyon korumalı fonlar sorusu
        if any(word in question_lower for word in ['enflasyon korumalı', 'enflasyona karşı', 'inflation protected']):
            # Önce MV versiyonunu dene
            return self.analyze_inflation_funds_mv()
        
        # Diğer durumlar için mevcut logic...
        return self._handle_general_inflation_question(question)


    def _handle_general_inflation_question(self, question):
        """Ana analiz fonksiyonu"""
        question_lower = question.lower()
        
        # Öncelik sırasına göre analiz
        if any(word in question_lower for word in ['dolar', 'dollar', 'usd']):
            return self.analyze_currency_funds('usd', question)
        elif any(word in question_lower for word in ['euro', 'eur', 'avro']):
            return self.analyze_currency_funds('eur', question)
        elif any(word in question_lower for word in ['enflasyon', 'inflation']):
            return self.analyze_currency_funds('inflation_protected', question)
        elif any(word in question_lower for word in ['hedge', 'koruma', 'korunma']):
            return self.analyze_currency_funds('hedge_funds', question)
        elif any(word in question_lower for word in ['altın', 'gold', 'kıymetli maden']):
            return self.analyze_currency_funds('precious_metals', question)
        elif any(word in question_lower for word in ['tl bazlı', 'tl cinsi', 'türk lirası']):
            return self.analyze_currency_funds('tl_based', question)
        elif any(word in question_lower for word in ['döviz', 'currency', 'foreign']):
            return self.analyze_all_foreign_currencies(question)
        else:
            return self._handle_general_currency_overview()
    
    def analyze_inflation_funds_mv(self):
        """Enflasyon korumalı fonları MV'den analiz et - ULTRA HIZLI"""
        print("⚡ Enflasyon korumalı fonlar MV'den yükleniyor...")


        
        try:
            # MV güncellik kontrolü
            freshness_check = """
            SELECT 
                EXTRACT(EPOCH FROM (NOW() - last_refresh))/3600 as hours_since_refresh
            FROM pg_matviews
            WHERE matviewname = 'mv_scenario_analysis_funds'
            """
            
            freshness = self.db.execute_query(freshness_check)
            if not freshness.empty and freshness.iloc[0]['hours_since_refresh'] > 24:
                print("   ⚠️ MV 24 saatten eski, güncelleniyor...")
                self.db.execute_query("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_scenario_analysis_funds")
            
            # Kategorilere göre grupla ve en iyileri al
            query = """
            WITH ranked_funds AS (
                SELECT 
                    *,
                    ROW_NUMBER() OVER (
                        PARTITION BY protection_category 
                        ORDER BY inflation_scenario_score DESC
                    ) as category_rank
                FROM mv_scenario_analysis_funds
                WHERE inflation_protection_score > 15
                AND investorcount > 100  -- Minimum yatırımcı filtresi
            ),
            category_stats AS (
                -- Her kategori için istatistikler
                SELECT 
                    protection_category,
                    COUNT(*) as category_count,
                    AVG(inflation_protection_score) as avg_score,
                    AVG(return_30d) as avg_return_30d,
                    AVG(volatility_30d) as avg_volatility
                FROM mv_scenario_analysis_funds
                WHERE inflation_protection_score > 15
                GROUP BY protection_category
            )
            SELECT 
                rf.*,
                cs.category_count,
                cs.avg_score as category_avg_score,
                cs.avg_return_30d as category_avg_return
            FROM ranked_funds rf
            JOIN category_stats cs ON rf.protection_category = cs.protection_category
            WHERE rf.category_rank <= 5  -- Her kategoriden en iyi 5
            ORDER BY rf.protection_category, rf.inflation_scenario_score DESC
            """
            
            start_time = datetime.now().timestamp()
            result = self.db.execute_query(query)
            elapsed = datetime.now().timestamp() - start_time
            
            if result.empty:
                print("   ❌ MV'de enflasyon korumalı fon bulunamadı, fallback kullanılıyor...")
                return self._analyze_inflation_funds_fallback()
            
            print(f"   ✅ {len(result)} fon {elapsed:.3f} saniyede yüklendi!")
            
            # Sonuçları formatla
            response = f"\n💹 ENFLASYON KORUMALI FONLAR ANALİZİ\n"
            response += f"{'='*60}\n\n"
            response += f"⚡ Süre: {elapsed:.3f} saniye (MV kullanıldı)\n"
            response += f"📊 Toplam: {len(result)} fon (kategorilere göre gruplu)\n\n"
            
            # İstatistikler için ek sorgu
            stats_query = """
            SELECT 
                protection_category,
                COUNT(*) as fund_count,
                AVG(inflation_protection_score) as avg_protection_score,
                AVG(return_30d) as avg_return_30d,
                AVG(return_90d) as avg_return_90d,
                AVG(volatility_30d) as avg_volatility,
                SUM(fcapacity) / 1e9 as total_capacity_billion,
                SUM(investorcount) as total_investors
            FROM mv_scenario_analysis_funds
            WHERE inflation_protection_score > 15
            GROUP BY protection_category
            ORDER BY avg_protection_score DESC
            """
            
            stats = self.db.execute_query(stats_query)
            
            # Genel istatistikler
            if not stats.empty:
                response += f"📊 GENEL İSTATİSTİKLER:\n"
                response += f"{'='*50}\n"
                
                total_funds = stats['fund_count'].sum()
                total_capacity = stats['total_capacity_billion'].sum()
                total_investors = stats['total_investors'].sum()
                
                response += f"   📈 Toplam Enflasyon Korumalı Fon: {int(total_funds)}\n"
                response += f"   💰 Toplam Varlık: {total_capacity:.1f} Milyar TL\n"
                response += f"   👥 Toplam Yatırımcı: {int(total_investors):,}\n\n"
            
            # Kategorilere göre göster
            current_category = None
            category_names = {
                'ALTIN_AGIRLIKLI': '🥇 ALTIN AĞIRLIKLI FONLAR',
                'HISSE_AGIRLIKLI': '📊 HİSSE AĞIRLIKLI FONLAR',
                'DOVIZ_AGIRLIKLI': '💱 DÖVİZ AĞIRLIKLI FONLAR',
                'KATILIM_FONU': '🌙 KATILIM FONLARI',
                'KARMA_KORUMA': '🔄 KARMA KORUMA FONLARI',
                'TAHVIL_AGIRLIKLI': '📋 TAHVİL AĞIRLIKLI FONLAR',
                'DIGER': '📌 DİĞER FONLAR'
            }
            
            for _, fund in result.iterrows():
                category = fund['protection_category']
                
                # Yeni kategori başlığı
                if category != current_category:
                    current_category = category
                    
                    # Kategori istatistikleri
                    cat_stats = stats[stats['protection_category'] == category]
                    if not cat_stats.empty:
                        cat_data = cat_stats.iloc[0]
                        
                        response += f"\n{category_names.get(category, category)}:\n"
                        response += f"{'-'*55}\n"
                        response += f"📊 Kategori İstatistikleri:\n"
                        response += f"   • Toplam Fon: {int(cat_data['fund_count'])}\n"
                        response += f"   • Ort. Koruma Skoru: {cat_data['avg_protection_score']:.1f}\n"
                        response += f"   • Ort. 30G Getiri: %{cat_data['avg_return_30d']:.2f}\n"
                        response += f"   • Ort. Volatilite: %{cat_data['avg_volatility']:.2f}\n\n"
                
                # Fon detayları
                fcode = fund['fcode']
                fname = (fund['fund_name'] or f'Fon {fcode}')[:40]
                rank = int(fund['category_rank'])
                
                # Performans emoji
                if fund['return_30d'] > 5:
                    perf_emoji = "🚀"
                elif fund['return_30d'] > 2:
                    perf_emoji = "📈"
                elif fund['return_30d'] > 0:
                    perf_emoji = "➕"
                else:
                    perf_emoji = "➖"
                
                response += f"{rank}. {fcode} - {fname}... {perf_emoji}\n"
                response += f"   🛡️ Enflasyon Koruma: {fund['inflation_protection_score']:.1f}/100\n"
                response += f"   📊 Senaryo Skoru: {fund['inflation_scenario_score']:.1f}\n"
                
                # Performans metrikleri
                if pd.notna(fund['return_30d']):
                    response += f"   📈 30 Gün: %{fund['return_30d']:+.2f}\n"
                if pd.notna(fund['return_90d']):
                    response += f"   📈 90 Gün: %{fund['return_90d']:+.2f}\n"
                if pd.notna(fund['volatility_30d']):
                    response += f"   📉 Risk: %{fund['volatility_30d']:.2f}\n"
                if pd.notna(fund['sharpe_ratio_approx']) and fund['sharpe_ratio_approx'] > 0:
                    response += f"   ⚡ Sharpe: {fund['sharpe_ratio_approx']:.2f}\n"
                
                response += f"   💰 Fiyat: {fund['current_price']:.4f} TL\n"
                response += f"   👥 Yatırımcı: {fund['investorcount']:,}\n"
                
                # Portföy kompozisyonu (önemli olanlar)
                if fund['gold_ratio'] > 10:
                    response += f"   🥇 Altın: %{fund['gold_ratio']:.1f}\n"
                if fund['equity_ratio'] > 10:
                    response += f"   📊 Hisse: %{fund['equity_ratio']:.1f}\n"
                if fund['fx_ratio'] > 10:
                    response += f"   💱 Döviz: %{fund['fx_ratio']:.1f}\n"
                
                response += "\n"
            
            # Öneriler
            response += self._get_inflation_recommendations()
            
            return response
            
        except Exception as e:
            print(f"❌ MV analizi hatası: {e}")
            import traceback
            traceback.print_exc()
            # Fallback
            return self._analyze_inflation_funds_fallback()

    def _get_inflation_recommendations(self):
        """Enflasyon koruması için genel öneriler"""
        return f"""
    💡 ENFLASYON KORUMA STRATEJİLERİ:
    {'='*40}
    1. 🥇 **Altın Fonları** - Klasik enflasyon koruması
    • Fiziki altın destekli fonları tercih edin
    • Uzun vadeli koruma sağlar

    2. 📊 **Hisse Fonları** - Uzun vadeli reel getiri
    • Büyük şirketlerin hisse fonları
    • Temettü getirisi olan fonlar

    3. 💱 **Döviz/Eurobond Fonları** - TL değer kaybına karşı
    • USD/EUR bazlı fonlar
    • Eurobond ağırlıklı fonlar

    4. 🌙 **Katılım Fonları** - Alternatif koruma
    • Kira sertifikaları
    • Altın katılım fonları

    5. 🔄 **Karma Fonlar** - Dengeli yaklaşım
    • Çeşitlendirilmiş portföy
    • Orta risk profili

    ⚠️ **ÖNEMLİ UYARILAR:**
    • Yatırım tavsiyesi değildir
    • Portföyünüzü çeşitlendirin
    • Düzenli gözden geçirin
    • Risk toleransınıza uygun seçim yapın
    """

    def _analyze_inflation_funds_fallback(self):
        """MV çalışmazsa kullanılacak fallback metod"""
        print("   🔄 Fallback: Standart SQL sorgusu kullanılıyor...")
        
        try:
            # Daha basit bir sorgu
            query = """
            SELECT DISTINCT ON (f.fcode)
                f.fcode,
                f.ftitle as fund_name,
                f.price as current_price,
                f.investorcount,
                -- Basit kategori tespiti
                CASE 
                    WHEN d.preciousmetals > 50 THEN 'ALTIN'
                    WHEN d.stock > 60 THEN 'HİSSE'
                    WHEN d.eurobonds > 30 THEN 'DÖVİZ'
                    ELSE 'DİĞER'
                END as category
            FROM tefasfunds f
            LEFT JOIN tefasfunddetails d ON f.fcode = d.fcode
            WHERE f.pdate >= CURRENT_DATE - INTERVAL '7 days'
            AND f.investorcount > 100
            AND (d.preciousmetals > 20 OR d.stock > 50 OR d.eurobonds > 20)
            ORDER BY f.fcode, f.pdate DESC
            LIMIT 30
            """
            
            result = self.db.execute_query(query)
            
            if result.empty:
                return "❌ Enflasyon korumalı fon bulunamadı."
            
            response = f"\n💹 ENFLASYON KORUMALI FONLAR (Basit Analiz)\n"
            response += f"{'='*50}\n\n"
            response += f"📊 {len(result)} fon bulundu\n\n"
            
            for _, fund in result.iterrows():
                response += f"• {fund['fcode']} - {fund['fund_name'][:40]}...\n"
                response += f"  Kategori: {fund['category']}\n"
                response += f"  Fiyat: {fund['current_price']:.4f} TL\n"
                response += f"  Yatırımcı: {fund['investorcount']:,}\n\n"
            
            return response
            
        except Exception as e:
            return f"❌ Enflasyon analizi hatası: {str(e)}"


    def analyze_currency_funds(self, currency_type, question):
        """Belirli döviz/enflasyon tipinde fonları analiz et"""
        print(f"💱 {currency_type.upper()} fonları analiz ediliyor...")
        
        start_time = datetime.now().timestamp()
        
        # 1. İlgili fonları bul
        currency_funds = self.find_currency_funds_sql(currency_type)
        
        if not currency_funds:
            currency_info = self.currency_keywords.get(currency_type, {})
            description = currency_info.get('description', currency_type)
            return f"❌ {description} kategorisinde fon bulunamadı."
        
        print(f"   📊 {len(currency_funds)} {currency_type} fonu bulundu")
        
        # 2. Performans analizi
        performance_results = self.analyze_currency_performance(currency_funds, currency_type)
        
        if not performance_results:
            return f"❌ {currency_type.upper()} fonları için performans verisi hesaplanamadı."
        
        elapsed = datetime.now().timestamp() - start_time
        print(f"   ⏱️ Analiz tamamlandı: {elapsed:.1f} saniye")
        
        # 3. Sonuçları formatla
        return self.format_currency_analysis_results(currency_type, performance_results, elapsed)
    
    def find_currency_funds_sql(self, currency_type):
        """SQL ile döviz/enflasyon fonlarını bul"""
        currency_data = self.currency_keywords.get(currency_type, {})
        keywords = currency_data.get('keywords', [])
        
        if not keywords:
            return []
        
        try:
            # SQL LIKE koşulları oluştur
            like_conditions = []
            for keyword in keywords:
                like_conditions.append(f"UPPER(f.ftitle) LIKE '%{keyword}%'")
            
            where_clause = " OR ".join(like_conditions)
            
            # Ana sorgu
            query = f"""
            WITH currency_funds AS (
                SELECT DISTINCT f.fcode, f.ftitle as fund_name, f.fcapacity, 
                    f.investorcount, f.price, f.pdate,
                    ROW_NUMBER() OVER (PARTITION BY f.fcode ORDER BY f.pdate DESC) as rn
                FROM tefasfunds f
                WHERE ({where_clause})
                AND f.pdate >= CURRENT_DATE - INTERVAL '30 days'
                AND f.price > 0
                AND f.investorcount > 25  -- Minimum yatırımcı filtresi
            )
            SELECT fcode, fund_name, fcapacity, investorcount, price
            FROM currency_funds 
            WHERE rn = 1
            ORDER BY fcapacity DESC NULLS LAST
            """
            
            result = self.db.execute_query(query)
            
            funds_list = []
            for _, row in result.iterrows():
                # Portföy analizi ile doğrulama
                portfolio_score = self.calculate_currency_portfolio_score(row['fcode'], currency_type)
                
                funds_list.append({
                    'fcode': row['fcode'],
                    'fund_name': row['fund_name'],
                    'capacity': float(row['fcapacity']) if pd.notna(row['fcapacity']) else 0,
                    'investors': int(row['investorcount']) if pd.notna(row['investorcount']) else 0,
                    'current_price': float(row['price']) if pd.notna(row['price']) else 0,
                    'portfolio_score': portfolio_score,
                    'currency_type': currency_type
                })
            
            # Portföy skoruna göre filtrele ve sırala
            filtered_funds = [f for f in funds_list if f['portfolio_score'] > 0.1]  # %10+ ilgili varlık
            filtered_funds.sort(key=lambda x: x['portfolio_score'], reverse=True)
            
            return filtered_funds
            
        except Exception as e:
            print(f"   ❌ SQL sorgu hatası: {e}")
            return []
    
    def calculate_currency_portfolio_score(self, fcode, currency_type):
        """Portföy dağılımından döviz/enflasyon skorunu hesapla"""
        try:
            query = f"""
            SELECT * FROM tefasfunddetails 
            WHERE fcode = '{fcode}' 
            ORDER BY fdate DESC 
            LIMIT 1
            """
            
            result = self.db.execute_query(query)
            if result.empty:
                return 0
            
            row = result.iloc[0]
            currency_data = self.currency_keywords.get(currency_type, {})
            portfolio_fields = currency_data.get('portfolio_fields', [])
            
            total_score = 0
            
            # İlgili portföy alanlarından skor hesapla
            for field in portfolio_fields:
                value = float(row.get(field, 0) or 0)
                total_score += value
            
            # Özel hesaplamalar
            if currency_type == 'usd':
                # Dolar için: yabancı varlıklar + EUR olmayan döviz
                foreign_equity = float(row.get('foreignequity', 0) or 0)
                foreign_debt = float(row.get('foreigndebtinstruments', 0) or 0)
                total_score += foreign_equity + foreign_debt
                
            elif currency_type == 'eur':
                # Euro için: Avrupa bölgesi varlıkları (şimdilik foreign ile aynı)
                foreign_equity = float(row.get('foreignequity', 0) or 0)
                total_score += foreign_equity * 0.3  # EUR payı tahmini
                
            elif currency_type == 'tl_based':
                # TL için: yerli borçlanma araçları
                gov_bond = float(row.get('governmentbond', 0) or 0)
                treasury_bill = float(row.get('treasurybill', 0) or 0)
                stock = float(row.get('stock', 0) or 0)  # Yerli hisse
                total_score += gov_bond + treasury_bill + stock
                
            elif currency_type == 'inflation_protected':
                # Enflasyon koruması için: kira sertifikaları + değişken faizli
                lease_certs = float(row.get('governmentleasecertificates', 0) or 0)
                private_lease = float(row.get('privatesectorleasecertificates', 0) or 0)
                total_score += lease_certs + private_lease
                
            elif currency_type == 'hedge_funds':
                # Hedge için: türev araçlar
                derivatives = float(row.get('derivatives', 0) or 0)
                futures_collateral = float(row.get('futurescashcollateral', 0) or 0)
                total_score += derivatives + futures_collateral
                
            elif currency_type == 'precious_metals':
                # Kıymetli madenler için: tüm altın alanları
                precious_total = 0
                precious_fields = ['preciousmetals', 'preciousmetalsbyf', 'preciousmetalskba', 'preciousmetalskks']
                for field in precious_fields:
                    precious_total += float(row.get(field, 0) or 0)
                total_score = precious_total
            
            return min(total_score / 100, 1.0)  # 0-1 arası normalize et
            
        except Exception as e:
            self.logger.warning(f"Portfolio score hesaplama hatası {fcode}: {e}")
            return 0
    
    def analyze_currency_performance(self, funds_list, currency_type, analysis_days=180):
        """Döviz/Enflasyon fonları performans analizi"""
        print(f"   📈 {len(funds_list)} fon için performans analizi...")
        
        performance_results = []
        successful = 0
        
        for i, fund_info in enumerate(funds_list, 1):
            fcode = fund_info['fcode']
            
            if i % 10 == 0:
                print(f"   [{i}/{len(funds_list)}] işlendi...")
            
            try:
                # Performans verilerini hesapla
                data = self.db.get_fund_price_history(fcode, analysis_days)
                
                if len(data) >= 30:  # En az 30 gün veri
                    prices = data.set_index('pdate')['price'].sort_index()
                    returns = prices.pct_change().dropna()
                    
                    # Temel metrikler
                    total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                    annual_return = total_return * (252 / len(prices))
                    volatility = returns.std() * np.sqrt(252) * 100
                    
                    # Sharpe ratio
                    if volatility > 0:
                        sharpe = (annual_return - 15) / volatility
                    else:
                        sharpe = 0
                    
                    win_rate = (returns > 0).sum() / len(returns) * 100
                    
                    # Max drawdown
                    cumulative = (1 + returns).cumprod()
                    running_max = cumulative.expanding().max()
                    drawdown = (cumulative - running_max) / running_max
                    max_drawdown = abs(drawdown.min()) * 100
                    
                    # Döviz/Enflasyon özel skor
                    currency_score = self.calculate_currency_score(
                        annual_return, volatility, sharpe, win_rate, currency_type, max_drawdown
                    )
                    
                    fund_result = {
                        'fcode': fcode,
                        'fund_name': fund_info['fund_name'],
                        'capacity': fund_info['capacity'],
                        'investors': fund_info['investors'],
                        'current_price': fund_info['current_price'],
                        'portfolio_score': fund_info['portfolio_score'],
                        'total_return': total_return,
                        'annual_return': annual_return,
                        'volatility': volatility,
                        'sharpe_ratio': sharpe,
                        'win_rate': win_rate,
                        'max_drawdown': max_drawdown,
                        'currency_score': currency_score,
                        'data_points': len(prices)
                    }
                    
                    performance_results.append(fund_result)
                    successful += 1
                    
            except Exception as e:
                continue
        
        print(f"   ✅ {successful}/{len(funds_list)} fon başarıyla analiz edildi")
        return performance_results
    
    def calculate_currency_score(self, annual_return, volatility, sharpe, win_rate, currency_type, max_drawdown):
        """Döviz/Enflasyon özel skor hesaplama"""
        base_score = 0
        
        # Temel skor (0-60)
        base_score += min(max(annual_return, 0) / 40 * 25, 25)  # Getiri
        base_score += min(max(sharpe, 0) * 15, 20)  # Sharpe
        base_score += min(win_rate / 10, 15)  # Kazanma oranı
        
        # Döviz/Enflasyon özel bonus (0-40)
        if currency_type == 'usd':
            # USD fonları için istikrar ve korelasyon bonusu
            if volatility < 20:
                base_score += 15
            if annual_return > 10:
                base_score += 15
            if sharpe > 0.4:
                base_score += 10
                
        elif currency_type == 'eur':
            # EUR fonları için
            if volatility < 18:
                base_score += 15
            if annual_return > 8:
                base_score += 15
            if sharpe > 0.3:
                base_score += 10
                
        elif currency_type == 'tl_based':
            # TL fonları için güvenlik bonusu
            if volatility < 10:
                base_score += 20
            if win_rate > 60:
                base_score += 10
            if annual_return > 15:  # Enflasyon üstü
                base_score += 10
                
        elif currency_type == 'inflation_protected':
            # Enflasyon koruması için
            if annual_return > 18:  # Enflasyon + reel getiri
                base_score += 20
            if volatility < 15:
                base_score += 15
            if sharpe > 0.5:
                base_score += 5
                
        elif currency_type == 'hedge_funds':
            # Hedge fonları için risk yönetimi bonusu
            if volatility < 25:
                base_score += 15
            if max_drawdown < 15:
                base_score += 15
            if sharpe > 0.3:
                base_score += 10
                
        elif currency_type == 'precious_metals':
            # Altın fonları için
            if annual_return > 12:
                base_score += 20
            if volatility < 30:
                base_score += 10
            if win_rate > 50:
                base_score += 10
        
        return min(max(base_score, 0), 100)
    
    def format_currency_analysis_results(self, currency_type, results, analysis_time):
        """Döviz/Enflasyon analiz sonuçlarını formatla"""
        
        # Currency skora göre sırala
        results.sort(key=lambda x: x['currency_score'], reverse=True)
        
        currency_data = self.currency_keywords.get(currency_type, {})
        description = currency_data.get('description', currency_type.upper())
        currency_code = currency_data.get('currency_code', currency_type.upper())
        
        response = f"\n💱 {description.upper()} ANALİZİ - TÜM VERİTABANI\n"
        response += f"{'='*60}\n\n"
        
        response += f"🎯 {description}\n"
        response += f"💰 Para Birimi/Tip: {currency_code}\n"
        response += f"🔍 Analiz Kapsamı: {len(results)} fon\n"
        response += f"⏱️ Analiz Süresi: {analysis_time:.1f} saniye\n\n"
        
        # GENEL İSTATİSTİKLER
        if results:
            total_capacity = sum(r['capacity'] for r in results)
            total_investors = sum(r['investors'] for r in results)
            avg_return = sum(r['annual_return'] for r in results) / len(results)
            avg_volatility = sum(r['volatility'] for r in results) / len(results)
            avg_score = sum(r['currency_score'] for r in results) / len(results)
            avg_portfolio_score = sum(r['portfolio_score'] for r in results) / len(results)
            
            response += f"📊 {currency_code} GENEL İSTATİSTİKLERİ:\n"
            response += f"   🔢 Toplam Fon: {len(results)}\n"
            response += f"   💰 Toplam Varlık: {total_capacity:,.0f} TL ({total_capacity/1000000000:.1f} milyar)\n"
            response += f"   👥 Toplam Yatırımcı: {total_investors:,} kişi\n"
            response += f"   📈 Ortalama Getiri: %{avg_return:+.2f}\n"
            response += f"   📊 Ortalama Risk: %{avg_volatility:.2f}\n"
            response += f"   🎯 Ortalama {currency_code} Skoru: {avg_score:.1f}/100\n"
            response += f"   💼 Ortalama Portföy Uyumu: %{avg_portfolio_score*100:.1f}\n\n"
        
        # EN İYİ 12 FON
        response += f"🏆 EN İYİ {min(12, len(results))} {currency_code} FONU ({currency_code} Skoruna Göre):\n\n"
        
        for i, fund in enumerate(results[:12], 1):
            # Skor kategorisi
            score = fund['currency_score']
            if score > 80:
                rating = "🌟 EFSANE"
            elif score > 70:
                rating = "⭐ MÜKEMMEL"
            elif score > 60:
                rating = "🔶 ÇOK İYİ"
            elif score > 50:
                rating = "🔸 İYİ"
            elif score > 40:
                rating = "🟡 ORTA"
            else:
                rating = "🔻 ZAYIF"
            
            # Risk seviyesi
            volatility = fund['volatility']
            if volatility < 10:
                risk_level = "🟢 DÜŞÜK"
            elif volatility < 20:
                risk_level = "🟡 ORTA"
            elif volatility < 30:
                risk_level = "🟠 YÜKSEK"
            else:
                risk_level = "🔴 ÇOK YÜKSEK"
            
            response += f"{i:2d}. {fund['fcode']} - {rating}\n"
            response += f"    🎯 {currency_code} Skoru: {score:.1f}/100\n"
            response += f"    📈 Yıllık Getiri: %{fund['annual_return']:+.2f}\n"
            response += f"    ⚡ Sharpe Oranı: {fund['sharpe_ratio']:.3f}\n"
            response += f"    📊 Risk Seviyesi: {risk_level} (%{volatility:.1f})\n"
            response += f"    🎯 Kazanma Oranı: %{fund['win_rate']:.1f}\n"
            response += f"    💼 Portföy Uyumu: %{fund['portfolio_score']*100:.1f}\n"
            response += f"    💰 Kapasite: {fund['capacity']:,.0f} TL\n"
            response += f"    👥 Yatırımcı: {fund['investors']:,} kişi\n"
            response += f"    💲 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
            response += f"    📝 Adı: {fund['fund_name'][:40]}...\n"
            response += f"\n"
        
        # KATEGORİ LİDERLERİ
        if results:
            best_return = max(results, key=lambda x: x['annual_return'])
            best_sharpe = max(results, key=lambda x: x['sharpe_ratio'])
            safest = min(results, key=lambda x: x['volatility'])
            biggest = max(results, key=lambda x: x['capacity'])
            most_relevant = max(results, key=lambda x: x['portfolio_score'])
            
            response += f"🏅 {currency_code} KATEGORİ LİDERLERİ:\n"
            response += f"   📈 En Yüksek Getiri: {best_return['fcode']} (%{best_return['annual_return']:+.1f})\n"
            response += f"   ⚡ En İyi Sharpe: {best_sharpe['fcode']} ({best_sharpe['sharpe_ratio']:.3f})\n"
            response += f"   🛡️ En Güvenli: {safest['fcode']} (%{safest['volatility']:.1f} risk)\n"
            response += f"   💰 En Büyük: {biggest['fcode']} ({biggest['capacity']/1000000:.0f}M TL)\n"
            response += f"   💼 En Uyumlu Portföy: {most_relevant['fcode']} (%{most_relevant['portfolio_score']*100:.1f})\n\n"
        
        # PERFORMANS DAĞILIMI
        if results:
            excellent = len([f for f in results if f['currency_score'] > 70])
            good = len([f for f in results if 50 < f['currency_score'] <= 70])
            average = len([f for f in results if 30 < f['currency_score'] <= 50])
            poor = len([f for f in results if f['currency_score'] <= 30])
            
            response += f"📊 {currency_code} PERFORMANS DAĞILIMI:\n"
            response += f"   🌟 Mükemmel (>70): {excellent} fon (%{excellent/len(results)*100:.1f})\n"
            response += f"   🔶 İyi (50-70): {good} fon (%{good/len(results)*100:.1f})\n"
            response += f"   🟡 Orta (30-50): {average} fon (%{average/len(results)*100:.1f})\n"
            response += f"   🔻 Zayıf (≤30): {poor} fon (%{poor/len(results)*100:.1f})\n\n"
        
        # ÖZEL TAVSİYELER
        response += f"💡 {currency_code} YATIRIM TAVSİYELERİ:\n"
        
        if currency_type == 'usd':
            response += f"   🇺🇸 Dolar güçlenme beklentisinde USD fonları tercih edilebilir\n"
            response += f"   ⚠️ TL/USD paritesindeki değişimleri takip edin\n"
            response += f"   💼 Portföyde maksimum %30 USD ağırlığı önerilir\n"
            
        elif currency_type == 'eur':
            response += f"   🇪🇺 Avrupa ekonomisindeki gelişmeleri izleyin\n"
            response += f"   📊 EUR/TRY paritesindeki hareketleri takip edin\n"
            response += f"   💼 Dolar karşısında hedge etkisi sağlayabilir\n"
            
        elif currency_type == 'tl_based':
            response += f"   🇹🇷 TL bazlı fonlar döviz riskinden korunma sağlar\n"
            response += f"   📈 Enflasyon oranının üstünde getiri hedefleyin\n"
            response += f"   🛡️ Konservatif yatırımcılar için uygun\n"
            
        elif currency_type == 'inflation_protected':
            response += f"   📊 Enflasyon verilerini yakından takip edin\n"
            response += f"   📈 Reel getiri odaklı yatırım stratejisi\n"
            response += f"   ⚖️ Portföyde enflasyon hedge aracı olarak kullanın\n"
            
        elif currency_type == 'hedge_funds':
            response += f"   🛡️ Döviz riskini minimize etmek için tercih edin\n"
            response += f"   📊 Türev araç maliyetlerini göz önünde bulundurun\n"
            response += f"   💡 Volatilite yüksek dönemlerde değerlendirin\n"
            
        elif currency_type == 'precious_metals':
            response += f"   💰 Altın enflasyon hedge aracı olarak kullanılabilir\n"
            response += f"   📊 Küresel belirsizlik dönemlerinde avantajlı\n"
            response += f"   ⚖️ Portföyde %5-15 ağırlık önerilir\n"
        
        # RİSK UYARILARI
        response += f"\n⚠️ {currency_code} RİSK UYARILARI:\n"
        response += f"   • Döviz kurlarındaki volatilite yüksek risk içerir\n"
        response += f"   • Küresel ekonomik gelişmeleri yakından izleyin\n"
        response += f"   • Merkez bankası politikalarındaki değişimlere dikkat\n"
        response += f"   • Portföy diversifikasyonunu ihmal etmeyin\n"
        
        if results:
            top_fund = results[0]
            response += f"\n🎯 ÖNERİLEN FON: {top_fund['fcode']}\n"
            response += f"   📊 Skor: {top_fund['currency_score']:.1f}/100\n"
            response += f"   📈 Beklenen Getiri: %{top_fund['annual_return']:+.1f}\n"
            response += f"   🛡️ Risk Seviyesi: %{top_fund['volatility']:.1f}\n"
        
        return response
    
    def analyze_all_foreign_currencies(self, question):
        """Tüm döviz fonlarını karşılaştırmalı analiz et"""
        print("💱 Tüm döviz fonları karşılaştırmalı analiz...")
        
        currency_types = ['usd', 'eur', 'hedge_funds']
        comparison_results = {}
        
        for currency_type in currency_types:
            print(f"   📊 {currency_type.upper()} analizi...")
            funds = self.find_currency_funds_sql(currency_type)
            if funds:
                performance = self.analyze_currency_performance(funds, currency_type, 120)
                if performance:
                    # Özet istatistikler
                    avg_return = sum(f['annual_return'] for f in performance) / len(performance)
                    avg_volatility = sum(f['volatility'] for f in performance) / len(performance)
                    avg_score = sum(f['currency_score'] for f in performance) / len(performance)
                    total_capacity = sum(f['capacity'] for f in performance)
                    
                    comparison_results[currency_type] = {
                        'fund_count': len(performance),
                        'avg_return': avg_return,
                        'avg_volatility': avg_volatility,
                        'avg_score': avg_score,
                        'total_capacity': total_capacity,
                        'best_fund': max(performance, key=lambda x: x['currency_score']),
                        'performance_data': performance
                    }
        
        if not comparison_results:
            return "❌ Döviz fonları karşılaştırması için yeterli veri bulunamadı."
        
        return self.format_currency_comparison_results(comparison_results)
    
    def format_currency_comparison_results(self, comparison_results):
        """Döviz karşılaştırma sonuçlarını formatla"""
        
        response = f"\n💱 DÖVİZ FONLARI KARŞILAŞTIRMALI ANALİZ\n"
        response += f"{'='*50}\n\n"
        
        response += f"📊 KARŞILAŞTIRILAN DÖVİZ TİPLERİ: {len(comparison_results)}\n\n"
        
        # KARŞILAŞTIRMA TABLOSU
        response += f"📈 DÖVİZ PERFORMANS KARŞILAŞTIRMASI:\n\n"
        response += f"{'Döviz':<10} | {'Fon':<4} | {'Getiri':<8} | {'Risk':<7} | {'Skor':<5} | {'Varlık':<8}\n"
        response += f"{'-'*10}|{'-'*5}|{'-'*9}|{'-'*8}|{'-'*6}|{'-'*8}\n"
        
        # Skor bazında sırala
        sorted_currencies = sorted(comparison_results.items(), key=lambda x: x[1]['avg_score'], reverse=True)
        
        currency_names = {
            'usd': 'USD',
            'eur': 'EUR', 
            'hedge_funds': 'HEDGE'
        }
        
        for currency_type, data in sorted_currencies:
            currency_name = currency_names.get(currency_type, currency_type.upper())
            varlık_milyar = data['total_capacity'] / 1000000000
            response += f"{currency_name:<10} | {data['fund_count']:<4} | %{data['avg_return']:+5.1f} | %{data['avg_volatility']:5.1f} | {data['avg_score']:4.1f} | {varlık_milyar:5.1f}B\n"
        
        # KAZANANLAR
        response += f"\n🏆 DÖVİZ KATEGORİ KAZANANLARI:\n"
        
        best_return_currency = max(comparison_results.items(), key=lambda x: x[1]['avg_return'])
        best_score_currency = max(comparison_results.items(), key=lambda x: x[1]['avg_score'])
        safest_currency = min(comparison_results.items(), key=lambda x: x[1]['avg_volatility'])
        biggest_currency = max(comparison_results.items(), key=lambda x: x[1]['total_capacity'])
        
        response += f"   📈 En Yüksek Getiri: {currency_names.get(best_return_currency[0], best_return_currency[0]).upper()} (%{best_return_currency[1]['avg_return']:+.1f})\n"
        response += f"   🎯 En Yüksek Skor: {currency_names.get(best_score_currency[0], best_score_currency[0]).upper()} ({best_score_currency[1]['avg_score']:.1f})\n"
        response += f"   🛡️ En Güvenli: {currency_names.get(safest_currency[0], safest_currency[0]).upper()} (%{safest_currency[1]['avg_volatility']:.1f} risk)\n"
        response += f"   💰 En Büyük Varlık: {currency_names.get(biggest_currency[0], biggest_currency[0]).upper()} ({biggest_currency[1]['total_capacity']/1000000000:.1f}B TL)\n"
        
        # HER DÖVİZDEN EN İYİ FON
        response += f"\n🌟 HER DÖVİZDEN EN İYİ FON:\n\n"
        
        for currency_type, data in sorted_currencies:
            currency_name = currency_names.get(currency_type, currency_type.upper())
            best_fund = data['best_fund']
            response += f"💱 {currency_name}:\n"
            response += f"   {best_fund['fcode']} - Skor: {best_fund['currency_score']:.1f}\n"
            response += f"   Getiri: %{best_fund['annual_return']:+.1f}, Risk: %{best_fund['volatility']:.1f}\n"
            response += f"   {best_fund['fund_name'][:35]}...\n\n"
        
        # PORTFÖY ÖNERİSİ
        response += f"💼 DÖVİZ PORTFÖY ÖNERİSİ:\n"
        winner = sorted_currencies[0]
        response += f"   🥇 Ana Döviz: {currency_names.get(winner[0], winner[0]).upper()}\n"
        response += f"   📊 Önerilen Ağırlık: %40-60\n"
        response += f"   🛡️ Hedge Fonları: %20-30\n"
        response += f"   ⚖️ Diversifikasyon: TL + Altın %20-40\n"
        
        return response
    
    def _handle_general_currency_overview(self):
        """Genel döviz/enflasyon fon genel bakış"""
        response = f"\n💱 DÖVİZ VE ENFLASYON FON ANALİZ SİSTEMİ\n"
        response += f"{'='*50}\n\n"
        
        response += f"📊 DESTEKLENEN DÖVİZ/ENFLASYON KATEGORİLERİ:\n\n"
        
        for i, (currency_type, data) in enumerate(self.currency_keywords.items(), 1):
            currency_code = data.get('currency_code', currency_type.upper())
            description = data.get('description', currency_type)
            response += f"{i:2d}. {currency_code:<8} - {description}\n"
        
        response += f"\n💡 KULLANIM ÖRNEKLERİ:\n"
        response += f"   • 'Dolar bazlı fonlar hangileri?'\n"
        response += f"   • 'Euro fonları performansı nasıl?'\n"
        response += f"   • 'Enflasyon korumalı fonlar analizi'\n"
        response += f"   • 'Döviz hedge fonları var mı?'\n"
        response += f"   • 'TL bazlı en güvenli fonlar'\n"
        response += f"   • 'Altın fonları karşılaştırması'\n\n"
        
        response += f"🎯 ANALİZ ÖZELLİKLERİ:\n"
        response += f"   ✅ TÜM veritabanı tarama (1700+ fon)\n"
        response += f"   ✅ Döviz özel skorlama sistemi\n"
        response += f"   ✅ Portföy uyumluluk analizi\n"
        response += f"   ✅ Risk-getiri optimizasyonu\n"
        response += f"   ✅ Enflasyon hedge analizi\n"
        response += f"   ✅ Döviz karşılaştırması\n"
        response += f"   ✅ Yatırım önerileri ve uyarılar\n\n"
        
        response += f"📈 HIZLI BAŞLANGIÇ:\n"
        response += f"   Döviz adı veya 'enflasyon' yazmanız yeterli!\n"
        response += f"   Örnek: 'dolar', 'euro', 'enflasyon', 'altın'\n\n"
        
        response += f"⚠️ ÖNEMLİ NOT:\n"
        response += f"   • Döviz yatırımları yüksek risk içerir\n"
        response += f"   • Kur hareketleri ani ve keskin olabilir\n"
        response += f"   • Portföy diversifikasyonu kritik önemde\n"
        response += f"   • Uzun vadeli yatırım stratejisi önerilir\n"
        
        return response

# =============================================================
# INTERACTIVE_QA_DUAL_AI.PY'YE ENTEGRASYON KODU
# =============================================================

def integrate_currency_inflation_to_qa():
    """
    Bu fonksiyonları interactive_qa_dual_ai.py dosyasına entegre edin:
    
    1. İMPORT bölümüne ekleyin:
    from currency_inflation_analyzer import CurrencyInflationAnalyzer
    
    2. DualAITefasQA.__init__ metodunda analyzer'ı başlatın:
    self.currency_analyzer = CurrencyInflationAnalyzer(self.coordinator.db, self.config)
    
    3. answer_question metoduna aşağıdaki elif bloğunu ekleyin:
    """
    
    integration_code = '''
    # DualAITefasQA.answer_question() metoduna eklenecek kod:
    
    def answer_question(self, question):
        question_lower = normalize_turkish_text(question)
        
        # ... mevcut kodlar ...
        
        # 💱 DÖVİZ VE ENFLASYON SORULARI - TÜM VERİTABANI
        if CurrencyInflationAnalyzer.is_currency_inflation_question(question):
            return self.currency_analyzer.analyze_currency_inflation_question(question)
        
        # ... kalan kodlar ...
    '''
    
    return integration_code

# =============================================================
# CURRENCY ANALYSIS CONFIGURATION
# =============================================================

CURRENCY_CONFIG = {
    'analysis_period_days': 180,        # 6 ay default
    'minimum_investors': 25,            # Minimum yatırımcı sayısı
    'minimum_portfolio_score': 0.1,     # Minimum portföy uyum skoru (%10)
    'minimum_data_points': 30,          # Minimum veri noktası
    'performance_threshold': 8,         # Performans eşiği %
    'max_funds_per_currency': 50,       # Para birimi başına maksimum fon
    'sql_timeout': 30,                  # SQL timeout saniye
    'volatility_thresholds': {          # Risk seviye eşikleri
        'low': 10,
        'medium': 20,
        'high': 30
    },
    'currency_benchmarks': {            # Para birimi benchmarkları
        'usd': {'expected_return': 12, 'max_volatility': 25},
        'eur': {'expected_return': 10, 'max_volatility': 22},
        'tl_based': {'expected_return': 18, 'max_volatility': 15},
        'inflation_protected': {'expected_return': 20, 'max_volatility': 18},
        'precious_metals': {'expected_return': 15, 'max_volatility': 35}
    }
}

# =============================================================
# PORTFOLIO ANALYSIS HELPERS
# =============================================================

def analyze_currency_portfolio_distribution(db_manager, fcode):
    """Detaylı portföy dağılım analizi"""
    try:
        query = f"""
        SELECT 
            stock, foreignequity, foreigndebtinstruments, foreigncurrencybills,
            governmentbond, treasurybill, termdeposittl, termdeposit,
            participationaccounttl, participationaccount,
            preciousmetals, preciousmetalsbyf, preciousmetalskba, preciousmetalskks,
            derivatives, futurescashcollateral,
            governmentleasecertificates, privatesectorleasecertificates,
            exchangetradedfund, fundparticipationcertificate,
            other, tmm, repo, reverserepo,
            fdate
        FROM tefasfunddetails 
        WHERE fcode = '{fcode}' 
        ORDER BY fdate DESC 
        LIMIT 1
        """
        
        result = db_manager.execute_query(query)
        if not result.empty:
            return result.iloc[0].to_dict()
        return {}
        
    except Exception as e:
        logging.getLogger(__name__).warning(f"Portfolio distribution error {fcode}: {e}")
        return {}

def calculate_currency_exposure(portfolio_data):
    """Portföy verilerinden döviz exposure hesapla"""
    
    # USD exposure
    usd_exposure = (
        float(portfolio_data.get('foreignequity', 0) or 0) +
        float(portfolio_data.get('foreigndebtinstruments', 0) or 0) +
        float(portfolio_data.get('foreigncurrencybills', 0) or 0) * 0.7  # USD payı tahmini
    )
    
    # EUR exposure
    eur_exposure = (
        float(portfolio_data.get('foreigncurrencybills', 0) or 0) * 0.3  # EUR payı tahmini
    )
    
    # TL exposure
    tl_exposure = (
        float(portfolio_data.get('stock', 0) or 0) +
        float(portfolio_data.get('governmentbond', 0) or 0) +
        float(portfolio_data.get('treasurybill', 0) or 0) +
        float(portfolio_data.get('termdeposittl', 0) or 0) +
        float(portfolio_data.get('participationaccounttl', 0) or 0)
    )
    
    # Precious metals (inflation hedge)
    precious_exposure = (
        float(portfolio_data.get('preciousmetals', 0) or 0) +
        float(portfolio_data.get('preciousmetalsbyf', 0) or 0) +
        float(portfolio_data.get('preciousmetalskba', 0) or 0) +
        float(portfolio_data.get('preciousmetalskks', 0) or 0)
    )
    
    # Hedge instruments
    hedge_exposure = (
        float(portfolio_data.get('derivatives', 0) or 0) +
        float(portfolio_data.get('futurescashcollateral', 0) or 0)
    )
    
    return {
        'usd_exposure': usd_exposure,
        'eur_exposure': eur_exposure,
        'tl_exposure': tl_exposure,
        'precious_metals_exposure': precious_exposure,
        'hedge_exposure': hedge_exposure,
        'total_foreign': usd_exposure + eur_exposure
    }

# =============================================================
# DEMO VE TEST FONKSİYONLARI
# =============================================================

def demo_currency_inflation_analysis():
    """Demo döviz/enflasyon analiz fonksiyonu"""
    from config.config import Config
    from database.connection import DatabaseManager
    
    config = Config()
    db = DatabaseManager(config)
    analyzer = CurrencyInflationAnalyzer(db, config)
    
    # Test soruları
    test_questions = [
        "Dolar bazlı fonlar hangileri?",
        "Euro fonları performansı",
        "Enflasyon korumalı fonlar",
        "Döviz hedge fonları var mı?",
        "TL bazlı en güvenli fonlar",
        "Altın fonları analizi"
    ]
    
    print("💱 DÖVİZ VE ENFLASYON ANALİZ SİSTEMİ DEMO")
    print("="*50)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[DEMO {i}/6] {question}")
        print("-" * 40)
        
        try:
            result = analyzer.analyze_currency_inflation_question(question)
            # İlk 300 karakteri göster
            preview = result[:300] + "..." if len(result) > 300 else result
            print(preview)
            print("✅ Demo başarılı")
            
            if i < len(test_questions):
                input("\nDevam etmek için Enter'a basın...")
                
        except Exception as e:
            print(f"❌ Demo hatası: {e}")
    
    print(f"\n🎉 Döviz/Enflasyon analiz demo tamamlandı!")

# =============================================================
# CURRENCY RISK MANAGEMENT
# =============================================================

class CurrencyRiskManager:
    """Döviz risk yönetimi yardımcı sınıfı"""
    
    @staticmethod
    def calculate_var_for_currency(returns, confidence_level=0.95):
        """Döviz fonu için VaR hesaplama"""
        if len(returns) < 30:
            return 0
        return np.percentile(returns, (1 - confidence_level) * 100)
    
    @staticmethod
    def assess_currency_correlation(fund_returns, currency_returns):
        """Fon ile döviz kuru korelasyonu"""
        if len(fund_returns) != len(currency_returns):
            return 0
        return np.corrcoef(fund_returns, currency_returns)[0, 1]
    
    @staticmethod
    def currency_diversification_score(portfolio_weights):
        """Döviz diversifikasyon skoru"""
        weights = np.array(list(portfolio_weights.values()))
        weights = weights / weights.sum()  # Normalize
        herfindahl_index = np.sum(weights ** 2)
        return 1 - herfindahl_index  # 0-1 arası, 1 = tam diversifiye

if __name__ == "__main__":
    # Integration code'u göster
    print(integrate_currency_inflation_to_qa())
    print("\n" + "="*50)
    # Demo çalıştır
    demo_currency_inflation_analysis()