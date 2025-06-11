# currency_inflation_analyzer.py
"""
TEFAS Döviz ve Enflasyon Analiz Sistemi - Risk Assessment ve MV Entegreli
Dolar, Euro, TL bazlı fonlar ve enflasyon korumalı yatırım araçları analizi
Risk değerlendirme sistemi ve Materialized View'lar ile güçlendirilmiş versiyon
"""

from datetime import datetime
import pandas as pd
import numpy as np
import logging
import time  
from database.connection import DatabaseManager
from config.config import Config
from risk_assessment import RiskAssessment

class CurrencyInflationAnalyzer:
    """Döviz ve Enflasyon analiz sistemi - MV + Risk Assessment"""
    
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
            # MV versiyonunu kullan
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
        """Enflasyon korumalı fonları MV'den analiz et - ULTRA HIZLI + Risk Assessment"""
        print("⚡ Enflasyon korumalı fonlar MV'den yükleniyor...")
        
        try:
            # MV güncellik kontrolü
            freshness_check = """
            SELECT 
                EXTRACT(EPOCH FROM (NOW() - last_refresh))/3600 as hours_since_refresh
            FROM pg_matviews
            WHERE matviewname = 'mv_scenario_analysis_funds'
            """
            
            try:
                freshness = self.db.execute_query(freshness_check)
                if not freshness.empty and freshness.iloc[0]['hours_since_refresh'] > 24:
                    print("   ⚠️ MV 24 saatten eski, güncelleniyor...")
                    self.db.execute_query("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_scenario_analysis_funds")
            except:
                # MV kontrolü başarısız olsa bile devam et
                pass
            
            # Kategorilere göre grupla ve en iyileri al
            query = """
            WITH ranked_funds AS (
                SELECT 
                    saf.*,
                    ti.rsi_14,
                    ti.stochastic_14,
                    ti.price_vs_sma20,
                    ti.days_since_last_trade,
                    lf.ftitle as fund_name,
                    ROW_NUMBER() OVER (
                        PARTITION BY saf.protection_category 
                        ORDER BY saf.inflation_scenario_score DESC
                    ) as category_rank
                FROM mv_scenario_analysis_funds saf
                JOIN mv_fund_technical_indicators ti ON saf.fcode = ti.fcode
                LEFT JOIN mv_latest_fund_data lf ON saf.fcode = lf.fcode
                WHERE saf.inflation_protection_score > 15
                AND saf.investorcount > 100
            ),
            category_stats AS (
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
            WHERE rf.category_rank <= 5
            ORDER BY rf.protection_category, rf.inflation_scenario_score DESC
            """
            
            start_time = datetime.now().timestamp()
            result = self.db.execute_query(query)
            elapsed = datetime.now().timestamp() - start_time
            
            if result.empty:
                print("   ❌ MV'de enflasyon korumalı fon bulunamadı, fallback kullanılıyor...")
                return self._analyze_inflation_funds_fallback()
            
            print(f"   ✅ {len(result)} fon {elapsed:.3f} saniyede yüklendi!")
            
            # RİSK DEĞERLENDİRMESİ - MV verilerinden
            print("   🛡️ Risk değerlendirmesi yapılıyor...")
            risk_assessed_funds = []
            high_risk_count = 0
            extreme_risk_count = 0
            
            for _, fund in result.iterrows():
                # Risk verileri hazırla
                risk_data = {
                    'fcode': fund['fcode'],
                    'price_vs_sma20': float(fund.get('price_vs_sma20', 0)),
                    'rsi_14': float(fund.get('rsi_14', 50)),
                    'stochastic_14': float(fund.get('stochastic_14', 50)),
                    'days_since_last_trade': int(fund.get('days_since_last_trade', 0)),
                    'investorcount': int(fund['investorcount'])
                }
                
                # Risk değerlendirmesi yap
                risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                
                # Risk istatistikleri
                if risk_assessment['risk_level'] == 'HIGH':
                    high_risk_count += 1
                elif risk_assessment['risk_level'] == 'EXTREME':
                    extreme_risk_count += 1
                
                # Fund verisine risk bilgilerini ekle
                fund_with_risk = fund.to_dict()
                fund_with_risk['risk_level'] = risk_assessment['risk_level']
                fund_with_risk['risk_score'] = risk_assessment['risk_score']
                fund_with_risk['risk_factors'] = risk_assessment['risk_factors']
                fund_with_risk['tradeable'] = risk_assessment.get('tradeable', True)
                fund_with_risk['requires_research'] = risk_assessment.get('requires_research', False)
                
                risk_assessed_funds.append(fund_with_risk)
            
            print(f"   📊 Risk Dağılımı: {extreme_risk_count} Ekstrem, {high_risk_count} Yüksek risk")
            
            # Sonuçları formatla - Risk Assessment dahil
            response = f"\n💹 ENFLASYON KORUMALI FONLAR ANALİZİ (MV + Risk Assessment)\n"
            response += f"{'='*70}\n\n"
            response += f"⚡ Süre: {elapsed:.3f} saniye (MV kullanıldı)\n"
            response += f"📊 Toplam: {len(result)} fon (kategorilere göre gruplu)\n"
            response += f"🛡️ Risk Taraması: ✅ Tamamlandı\n"
            response += f"   ⚠️ Yüksek Risk: {high_risk_count} fon\n"
            response += f"   ⛔ Ekstrem Risk: {extreme_risk_count} fon\n\n"
            
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
            
            # Kategorilere göre göster - Risk dahil
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
            
            for fund_data in risk_assessed_funds:
                category = fund_data['protection_category']
                
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
                
                # Risk göstergesi
                risk_indicators = {
                    'LOW': '🟢',
                    'MEDIUM': '🟡',
                    'HIGH': '🟠',
                    'EXTREME': '🔴'
                }
                risk_indicator = risk_indicators.get(fund_data['risk_level'], '⚪')
                
                # Fon detayları
                fcode = fund_data['fcode']
                fname = (fund_data.get('fund_name') or f'Fon {fcode}')[:40]
                rank = int(fund_data['category_rank'])
                
                # Performans emoji
                if pd.notna(fund_data.get('return_30d')):
                    if fund_data['return_30d'] > 5:
                        perf_emoji = "🚀"
                    elif fund_data['return_30d'] > 2:
                        perf_emoji = "📈"
                    elif fund_data['return_30d'] > 0:
                        perf_emoji = "➕"
                    else:
                        perf_emoji = "➖"
                else:
                    perf_emoji = ""
                
                # EXTREME risk uyarısı
                risk_warning = ""
                if fund_data['risk_level'] == 'EXTREME':
                    risk_warning = " ⛔ EXTREME RİSK"
                    if not fund_data.get('tradeable', True):
                        risk_warning += " - TRADE EDİLEMEZ"
                elif fund_data['risk_level'] == 'HIGH':
                    risk_warning = " ⚠️ YÜKSEK RİSK"
                
                response += f"{rank}. {fcode} - {fname}... {perf_emoji} {risk_indicator}{risk_warning}\n"
                response += f"   🛡️ Enflasyon Koruma: {fund_data['inflation_protection_score']:.1f}/100\n"
                response += f"   📊 Senaryo Skoru: {fund_data['inflation_scenario_score']:.1f}\n"
                response += f"   🎯 Risk Skoru: {fund_data['risk_score']:.1f}/100 ({fund_data['risk_level']})\n"
                
                # Performans metrikleri
                if pd.notna(fund_data.get('return_30d')):
                    response += f"   📈 30 Gün: %{fund_data['return_30d']:+.2f}\n"
                if pd.notna(fund_data.get('return_90d')):
                    response += f"   📈 90 Gün: %{fund_data['return_90d']:+.2f}\n"
                if pd.notna(fund_data.get('volatility_30d')):
                    response += f"   📉 Risk: %{fund_data['volatility_30d']:.2f}\n"
                if pd.notna(fund_data.get('sharpe_ratio_approx')) and fund_data['sharpe_ratio_approx'] > 0:
                    response += f"   ⚡ Sharpe: {fund_data['sharpe_ratio_approx']:.2f}\n"
                
                response += f"   💰 Fiyat: {fund_data['current_price']:.4f} TL\n"
                response += f"   👥 Yatırımcı: {fund_data['investorcount']:,}\n"
                
                # Risk faktörleri - Kritik olanları göster
                if fund_data['risk_factors']:
                    critical_factors = [f for f in fund_data['risk_factors'] if f['severity'] in ['CRITICAL', 'HIGH']]
                    if critical_factors:
                        response += f"   ⚠️ Risk Faktörleri: {critical_factors[0]['description']}\n"
                        if 'action' in critical_factors[0]:
                            response += f"   → {critical_factors[0]['action']}\n"
                
                # Portföy kompozisyonu (önemli olanlar)
                if fund_data.get('gold_ratio', 0) > 10:
                    response += f"   🥇 Altın: %{fund_data['gold_ratio']:.1f}\n"
                if fund_data.get('equity_ratio', 0) > 10:
                    response += f"   📊 Hisse: %{fund_data['equity_ratio']:.1f}\n"
                if fund_data.get('fx_ratio', 0) > 10:
                    response += f"   💱 Döviz: %{fund_data['fx_ratio']:.1f}\n"
                
                response += "\n"
            
            # Risk uyarıları ve öneriler
            response += self._get_inflation_recommendations_with_risk(extreme_risk_count, high_risk_count)
            
            return response
            
        except Exception as e:
            print(f"❌ MV analizi hatası: {e}")
            import traceback
            traceback.print_exc()
            # Fallback
            return self._analyze_inflation_funds_fallback()

    def _get_inflation_recommendations_with_risk(self, extreme_count, high_count):
        """Risk assessment dahil enflasyon koruması önerileri"""
        response = f"""
💡 ENFLASYON KORUMA STRATEJİLERİ (Risk Assessment Dahil):
{'='*60}
"""
        
        # Risk uyarısı
        if extreme_count > 0 or high_count > 0:
            response += f"⚠️ **RİSK UYARISI:**\n"
            if extreme_count > 0:
                response += f"   🔴 {extreme_count} fon EXTREME RİSK seviyesinde\n"
            if high_count > 0:
                response += f"   🟠 {high_count} fon YÜKSEK RİSK seviyesinde\n"
            response += f"   👀 Bu fonları tercih etmeden önce detaylı araştırma yapın!\n\n"
        
        response += f"""1. 🥇 **Altın Fonları** - Klasik enflasyon koruması
• Fiziki altın destekli fonları tercih edin
• Uzun vadeli koruma sağlar
• 🟢 Düşük risk seviyesindeki altın fonlarını seçin

2. 📊 **Hisse Fonları** - Uzun vadeli reel getiri
• Büyük şirketlerin hisse fonları
• Temettü getirisi olan fonlar
• ⚠️ Risk seviyesini mutlaka kontrol edin

3. 💱 **Döviz/Eurobond Fonları** - TL değer kaybına karşı
• USD/EUR bazlı fonlar
• Eurobond ağırlıklı fonlar
• 🛡️ Hedge fonları döviz riskini azaltır

4. 🌙 **Katılım Fonları** - Alternatif koruma
• Kira sertifikaları
• Altın katılım fonları
• 🟡 Risk seviyesi genelde orta

5. 🔄 **Karma Fonlar** - Dengeli yaklaşım
• Çeşitlendirilmiş portföy
• Orta risk profili
• 📊 Risk dağılımını kontrol edin

⚠️ **GÜNCEL RİSK UYARILARI:**
• {extreme_count + high_count} fon yüksek/ekstrem risk taşıyor
• 🔴 Extreme risk fonlarından kaçının
• 🟡 Orta risk fonları dengeyi sağlar
• 🟢 Düşük risk fonları konservatif yaklaşım
• Yatırım tavsiyesi değildir - kendi araştırmanızı yapın
• Portföyünüzü çeşitlendirin ve düzenli gözden geçirin
"""
        return response

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

    def analyze_currency_funds(self, currency_type='all', question=''):
        """Belirli döviz/enflasyon tipinde fonları analiz et - MV entegreli + Risk Assessment"""
        print(f"💱 {currency_type.upper()} fonları analiz ediliyor (MV kullanımı ile)...")
        
        start_time = datetime.now().timestamp()
        
        # 1. MV'den ilgili fonları bul
        currency_funds = self._find_currency_funds_mv(currency_type)
        
        if not currency_funds:
            # Fallback: SQL sorgusu
            print("   ⚠️ MV'de veri bulunamadı, SQL fallback kullanılıyor...")
            currency_funds = self.find_currency_funds_sql(currency_type)
        
        if not currency_funds:
            currency_info = self.currency_keywords.get(currency_type, {})
            description = currency_info.get('description', currency_type)
            return f"❌ {description} kategorisinde fon bulunamadı."
        
        print(f"   📊 {len(currency_funds)} {currency_type} fonu bulundu")
        
        # 2. Performans analizi (MV tabanlı)
        performance_results = self.analyze_currency_performance_mv(currency_type, currency_funds)
        
        if not performance_results:
            return f"❌ {currency_type.upper()} fonları için performans verisi hesaplanamadı."
        
        elapsed = datetime.now().timestamp() - start_time
        print(f"   ⏱️ Analiz tamamlandı: {elapsed:.1f} saniye")
        
        # 3. Sonuçları formatla
        return self.format_currency_analysis_results(currency_type, performance_results, elapsed)

    def _find_currency_funds_mv(self, currency_type):
        """MV'den döviz fonlarını bul"""
        try:
            currency_data = self.currency_keywords.get(currency_type, {})
            keywords = currency_data.get('keywords', [])
            
            if not keywords:
                return []
            
            # SQL LIKE koşulları oluştur
            like_conditions = []
            for keyword in keywords[:5]:  # İlk 5 keyword kullan
                like_conditions.append(f"UPPER(lf.ftitle) LIKE '%{keyword}%'")
            
            where_clause = " OR ".join(like_conditions)
            
            # MV sorgusu
            query = f"""
            WITH currency_funds AS (
                SELECT 
                    lf.fcode,
                    lf.ftitle as fund_name,
                    lf.fcapacity,
                    lf.investorcount,
                    lf.price as current_price,
                    pm.annual_return,
                    pm.annual_volatility,
                    pm.sharpe_ratio,
                    pm.win_rate,
                    ti.rsi_14,
                    ti.stochastic_14,
                    ti.price_vs_sma20,
                    ti.days_since_last_trade,
                    -- Portföy detayları
                    fd.eurobonds,
                    fd.foreigncurrencybills,
                    fd.foreigndebtinstruments,
                    fd.preciousmetals,
                    fd.stock,
                    fd.governmentbond,
                    fd.treasurybill,
                    fd.termdeposittl,
                    fd.governmentleasecertificates,
                    fd.derivatives
                FROM mv_latest_fund_data lf
                LEFT JOIN mv_fund_performance_metrics pm ON lf.fcode = pm.fcode
                LEFT JOIN mv_fund_technical_indicators ti ON lf.fcode = ti.fcode
                LEFT JOIN mv_fund_details_latest fd ON lf.fcode = fd.fcode
                WHERE ({where_clause})
                AND lf.investorcount > 50
            )
            SELECT * FROM currency_funds
            ORDER BY fcapacity DESC NULLS LAST
            LIMIT 50
            """
            
            result = self.db.execute_query(query)
            
            if result.empty:
                return []
            
            funds_list = []
            for _, row in result.iterrows():
                # Portföy skorunu hesapla
                portfolio_score = self._calculate_currency_portfolio_score_mv(row, currency_type)
                
                funds_list.append({
                    'fcode': row['fcode'],
                    'fund_name': row['fund_name'],
                    'capacity': float(row['fcapacity']) if pd.notna(row['fcapacity']) else 0,
                    'investors': int(row['investorcount']) if pd.notna(row['investorcount']) else 0,
                    'current_price': float(row['current_price']) if pd.notna(row['current_price']) else 0,
                    'portfolio_score': portfolio_score,
                    'currency_type': currency_type,
                    # MV'den gelen performans verileri
                    'annual_return': float(row['annual_return']) * 100 if pd.notna(row['annual_return']) else None,
                    'volatility': float(row['annual_volatility']) * 100 if pd.notna(row['annual_volatility']) else None,
                    'sharpe_ratio': float(row['sharpe_ratio']) if pd.notna(row['sharpe_ratio']) else None,
                    'win_rate': float(row['win_rate']) * 100 if pd.notna(row['win_rate']) else None,
                    # Risk verileri
                    'rsi_14': float(row['rsi_14']) if pd.notna(row['rsi_14']) else 50,
                    'stochastic_14': float(row['stochastic_14']) if pd.notna(row['stochastic_14']) else 50,
                    'price_vs_sma20': float(row['price_vs_sma20']) if pd.notna(row['price_vs_sma20']) else 0,
                    'days_since_last_trade': int(row['days_since_last_trade']) if pd.notna(row['days_since_last_trade']) else 0
                })
            
            # Portföy skoruna göre filtrele ve sırala
            filtered_funds = [f for f in funds_list if f['portfolio_score'] > 0.1]  # %10+ ilgili varlık
            filtered_funds.sort(key=lambda x: x['portfolio_score'], reverse=True)
            
            print(f"   ✅ MV'den {len(filtered_funds)} uygun fon yüklendi")
            return filtered_funds
            
        except Exception as e:
            print(f"   ❌ MV sorgu hatası: {e}")
            return []

    def _calculate_currency_portfolio_score_mv(self, row, currency_type):
        """MV verisinden portföy skoru hesapla"""
        try:
            currency_data = self.currency_keywords.get(currency_type, {})
            portfolio_fields = currency_data.get('portfolio_fields', [])
            
            total_score = 0
            
            # İlgili portföy alanlarından skor hesapla
            for field in portfolio_fields:
                if field in row and pd.notna(row[field]):
                    value = float(row[field])
                    total_score += value
            
            # Özel hesaplamalar
            if currency_type == 'usd' or currency_type == 'eur':
                # Dolar/Euro için: yabancı varlıklar
                foreign_assets = (
                    float(row.get('eurobonds', 0) or 0) +
                    float(row.get('foreigncurrencybills', 0) or 0) +
                    float(row.get('foreigndebtinstruments', 0) or 0)
                )
                total_score = max(total_score, foreign_assets)
                
            elif currency_type == 'tl_based':
                # TL için: yerli borçlanma araçları
                tl_assets = (
                    float(row.get('governmentbond', 0) or 0) +
                    float(row.get('treasurybill', 0) or 0) +
                    float(row.get('termdeposittl', 0) or 0)
                )
                total_score = max(total_score, tl_assets)
                
            elif currency_type == 'precious_metals':
                # Altın için
                total_score = float(row.get('preciousmetals', 0) or 0)
            
            return min(total_score / 100, 1.0)  # 0-1 arası normalize et
            
        except Exception as e:
            return 0

    def analyze_currency_performance_mv(self, currency_type, funds_list):
        """MV tabanlı performans analizi - Risk Assessment dahil"""
        print(f"   📈 {len(funds_list)} fon için performans + risk analizi (MV tabanlı)...")
        
        performance_results = []
        successful = 0
        high_risk_count = 0
        extreme_risk_count = 0
        
        for i, fund_info in enumerate(funds_list, 1):
            fcode = fund_info['fcode']
            
            if i % 10 == 0:
                print(f"   [{i}/{len(funds_list)}] işlendi...")
            
            try:
                # Risk değerlendirmesi
                risk_data = {
                    'fcode': fcode,
                    'price_vs_sma20': fund_info.get('price_vs_sma20', 0),
                    'rsi_14': fund_info.get('rsi_14', 50),
                    'stochastic_14': fund_info.get('stochastic_14', 50),
                    'days_since_last_trade': fund_info.get('days_since_last_trade', 0),
                    'investorcount': fund_info['investors']
                }
                
                risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                
                # Risk sayacları
                if risk_assessment['risk_level'] == 'HIGH':
                    high_risk_count += 1
                elif risk_assessment['risk_level'] == 'EXTREME':
                    extreme_risk_count += 1
                
                # MV'den gelen performans verilerini kullan
                if fund_info.get('annual_return') is not None:
                    # MV verileri mevcut
                    annual_return = fund_info['annual_return']
                    volatility = fund_info.get('volatility', 20)
                    sharpe = fund_info.get('sharpe_ratio', 0)
                    win_rate = fund_info.get('win_rate', 50)
                    
                    # Max drawdown tahmini (volatilite bazlı)
                    max_drawdown = min(volatility * 2, 50)
                    
                else:
                    # MV verileri yoksa hesapla
                    data = self.db.get_fund_price_history(fcode, 120)
                    
                    if len(data) < 30:
                        continue
                    
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
                    'total_return': annual_return / 2,  # 6 aylık tahmin
                    'annual_return': annual_return,
                    'volatility': volatility,
                    'sharpe_ratio': sharpe,
                    'win_rate': win_rate,
                    'max_drawdown': max_drawdown,
                    'currency_score': currency_score,
                    # Risk Assessment verileri
                    'risk_level': risk_assessment['risk_level'],
                    'risk_score': risk_assessment['risk_score'],
                    'risk_factors': risk_assessment['risk_factors'],
                    'tradeable': risk_assessment.get('tradeable', True),
                    'requires_research': risk_assessment.get('requires_research', False)
                }
                
                performance_results.append(fund_result)
                successful += 1
                
            except Exception as e:
                continue
        
        print(f"   ✅ {successful}/{len(funds_list)} fon başarıyla analiz edildi")
        print(f"   🛡️ Risk Dağılımı: {extreme_risk_count} Ekstrem, {high_risk_count} Yüksek")
        return performance_results

    def analyze_currency_performance(self, currency_type, funds_list, analysis_days=180):
        """Döviz/Enflasyon fonları performans analizi - Risk Assessment dahil (Fallback)"""
        print(f"   📈 {len(funds_list)} fon için performans + risk analizi...")
        
        performance_results = []
        successful = 0
        high_risk_count = 0
        extreme_risk_count = 0
        
        for i, fund_info in enumerate(funds_list, 1):
            fcode = fund_info['fcode']
            
            if i % 10 == 0:
                print(f"   [{i}/{len(funds_list)}] işlendi...")
            
            try:
                # MV'den risk verileri çek
                mv_query = f"SELECT * FROM mv_fund_technical_indicators WHERE fcode = '{fcode}'"
                mv_data = self.db.execute_query(mv_query)
                
                # Risk değerlendirmesi
                risk_data = {
                    'fcode': fcode,
                    'price_vs_sma20': 0,
                    'rsi_14': 50,
                    'stochastic_14': 50,
                    'days_since_last_trade': 0,
                    'investorcount': fund_info['investors']
                }
                
                if not mv_data.empty:
                    risk_data.update({
                        'price_vs_sma20': float(mv_data.iloc[0]['price_vs_sma20']),
                        'rsi_14': float(mv_data.iloc[0]['rsi_14']),
                        'stochastic_14': float(mv_data.iloc[0]['stochastic_14']),
                        'days_since_last_trade': int(mv_data.iloc[0]['days_since_last_trade'])
                    })
                
                risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                
                # Risk sayacları
                if risk_assessment['risk_level'] == 'HIGH':
                    high_risk_count += 1
                elif risk_assessment['risk_level'] == 'EXTREME':
                    extreme_risk_count += 1
                
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
                        'data_points': len(prices),
                        # Risk Assessment verileri
                        'risk_level': risk_assessment['risk_level'],
                        'risk_score': risk_assessment['risk_score'],
                        'risk_factors': risk_assessment['risk_factors'],
                        'tradeable': risk_assessment.get('tradeable', True),
                        'requires_research': risk_assessment.get('requires_research', False)
                    }
                    
                    performance_results.append(fund_result)
                    successful += 1
                    
            except Exception as e:
                continue
        
        print(f"   ✅ {successful}/{len(funds_list)} fon başarıyla analiz edildi")
        print(f"   🛡️ Risk Dağılımı: {extreme_risk_count} Ekstrem, {high_risk_count} Yüksek")
        return performance_results

    def _get_risk_indicator(self, risk_level):
        """Risk seviyesi göstergesi"""
        indicators = {
            'LOW': '🟢',
            'MEDIUM': '🟡',
            'HIGH': '🟠',
            'EXTREME': '🔴'
        }
        return indicators.get(risk_level, '')

    def find_currency_funds_sql(self, currency_type):
        """SQL ile döviz/enflasyon fonlarını bul (Fallback)"""
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
        """Döviz/Enflasyon analiz sonuçlarını formatla - Risk Assessment dahil"""
        
        # Currency skora göre sırala
        results.sort(key=lambda x: x['currency_score'], reverse=True)
        
        currency_data = self.currency_keywords.get(currency_type, {})
        description = currency_data.get('description', currency_type.upper())
        currency_code = currency_data.get('currency_code', currency_type.upper())
        
        # Risk istatistikleri hesapla
        extreme_risk_count = len([f for f in results if f['risk_level'] == 'EXTREME'])
        high_risk_count = len([f for f in results if f['risk_level'] == 'HIGH'])
        medium_risk_count = len([f for f in results if f['risk_level'] == 'MEDIUM'])
        low_risk_count = len([f for f in results if f['risk_level'] == 'LOW'])
        non_tradeable_count = len([f for f in results if not f.get('tradeable', True)])
        
        response = f"\n💱 {description.upper()} ANALİZİ - Risk Assessment Dahil\n"
        response += f"{'='*70}\n\n"
        
        response += f"🎯 {description}\n"
        response += f"💰 Para Birimi/Tip: {currency_code}\n"
        response += f"🔍 Analiz Kapsamı: {len(results)} fon\n"
        response += f"⏱️ Analiz Süresi: {analysis_time:.1f} saniye\n"
        response += f"🛡️ Risk Taraması: ✅ Tamamlandı\n\n"
        
        # RİSK DAĞILIMI
        response += f"📊 RİSK DAĞILIMI:\n"
        response += f"   🟢 Düşük Risk: {low_risk_count} fon (%{low_risk_count/len(results)*100:.1f})\n"
        response += f"   🟡 Orta Risk: {medium_risk_count} fon (%{medium_risk_count/len(results)*100:.1f})\n"
        response += f"   🟠 Yüksek Risk: {high_risk_count} fon (%{high_risk_count/len(results)*100:.1f})\n"
        response += f"   🔴 Ekstrem Risk: {extreme_risk_count} fon (%{extreme_risk_count/len(results)*100:.1f})\n"
        if non_tradeable_count > 0:
            response += f"   ⛔ Trade Edilemez: {non_tradeable_count} fon\n"
        response += f"\n"
        
        # Risk uyarısı
        if extreme_risk_count > 0 or non_tradeable_count > 0:
            response += f"⚠️ UYARI: "
            if extreme_risk_count > 0:
                response += f"{extreme_risk_count} fon EXTREME RİSK seviyesinde! "
            if non_tradeable_count > 0:
                response += f"{non_tradeable_count} fon TRADE EDİLEMEZ durumda!"
            response += f"\n\n"
        
        # GENEL İSTATİSTİKLER
        if results:
            total_capacity = sum(r['capacity'] for r in results)
            total_investors = sum(r['investors'] for r in results)
            avg_return = sum(r['annual_return'] for r in results) / len(results)
            avg_volatility = sum(r['volatility'] for r in results) / len(results)
            avg_score = sum(r['currency_score'] for r in results) / len(results)
            avg_portfolio_score = sum(r['portfolio_score'] for r in results) / len(results)
            avg_risk_score = sum(r['risk_score'] for r in results) / len(results)
            
            response += f"📊 {currency_code} GENEL İSTATİSTİKLERİ:\n"
            response += f"   🔢 Toplam Fon: {len(results)}\n"
            response += f"   💰 Toplam Varlık: {total_capacity:,.0f} TL ({total_capacity/1000000000:.1f} milyar)\n"
            response += f"   👥 Toplam Yatırımcı: {total_investors:,} kişi\n"
            response += f"   📈 Ortalama Getiri: %{avg_return:+.2f}\n"
            response += f"   📊 Ortalama Risk: %{avg_volatility:.2f}\n"
            response += f"   🎯 Ortalama {currency_code} Skoru: {avg_score:.1f}/100\n"
            response += f"   💼 Ortalama Portföy Uyumu: %{avg_portfolio_score*100:.1f}\n"
            response += f"   🛡️ Ortalama Risk Skoru: {avg_risk_score:.1f}/100\n\n"
        
        # EN İYİ 10 FON - Risk seviyesine göre filtrelenmiş
        safe_funds = [f for f in results if f['risk_level'] in ['LOW', 'MEDIUM'] and f.get('tradeable', True)]
        if safe_funds:
            response += f"🏆 EN İYİ {min(10, len(safe_funds))} GÜVENLİ {currency_code} FONU:\n\n"
            
            for i, fund in enumerate(safe_funds[:10], 1):
                # Risk göstergesi
                risk_indicator = self._get_risk_indicator(fund['risk_level'])
                
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
                
                response += f"{i:2d}. {fund['fcode']} - {rating} {risk_indicator}\n"
                response += f"    🎯 {currency_code} Skoru: {score:.1f}/100\n"
                response += f"    🛡️ Risk Skoru: {fund['risk_score']:.1f}/100 ({fund['risk_level']})\n"
                response += f"    📈 Yıllık Getiri: %{fund['annual_return']:+.2f}\n"
                response += f"    ⚡ Sharpe Oranı: {fund['sharpe_ratio']:.3f}\n"
                response += f"    📊 Risk Seviyesi: %{fund['volatility']:.1f}\n"
                response += f"    🎯 Kazanma Oranı: %{fund['win_rate']:.1f}\n"
                response += f"    💼 Portföy Uyumu: %{fund['portfolio_score']*100:.1f}\n"
                response += f"    💰 Kapasite: {fund['capacity']:,.0f} TL\n"
                response += f"    👥 Yatırımcı: {fund['investors']:,} kişi\n"
                response += f"    💲 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
                
                # Risk faktörleri varsa göster
                if fund['risk_factors']:
                    critical_factors = [f for f in fund['risk_factors'] if f['severity'] in ['CRITICAL', 'HIGH']]
                    if critical_factors:
                        response += f"    ⚠️ Risk: {critical_factors[0]['description']}\n"
                        if 'action' in critical_factors[0]:
                            response += f"    → {critical_factors[0]['action']}\n"
                
                response += f"    📝 Adı: {fund['fund_name'][:40]}...\n"
                response += f"\n"
        
        # RİSKLİ FONLAR UYARISI
        risky_funds = [f for f in results if f['risk_level'] in ['HIGH', 'EXTREME'] or not f.get('tradeable', True)]
        if risky_funds:
            response += f"⚠️ RİSKLİ FONLAR UYARISI ({len(risky_funds)} fon):\n\n"
            
            for i, fund in enumerate(risky_funds[:5], 1):
                risk_indicator = self._get_risk_indicator(fund['risk_level'])
                
                if not fund.get('tradeable', True):
                    risk_warning = "⛔ TRADE EDİLEMEZ"
                elif fund['risk_level'] == 'EXTREME':
                    risk_warning = "⛔ EXTREME RİSK"
                else:
                    risk_warning = "⚠️ YÜKSEK RİSK"
                
                response += f"{i}. {fund['fcode']} - {risk_warning} {risk_indicator}\n"
                response += f"   🛡️ Risk Skoru: {fund['risk_score']:.1f}/100\n"
                response += f"   📈 Getiri: %{fund['annual_return']:+.1f}\n"
                
                # Risk faktörleri
                if fund['risk_factors']:
                    critical_factors = [f for f in fund['risk_factors'] if f['severity'] in ['CRITICAL', 'HIGH']]
                    if critical_factors:
                        response += f"   🚨 Sebep: {critical_factors[0]['description']}\n"
                        if 'action' in critical_factors[0]:
                            response += f"   → {critical_factors[0]['action']}\n"
                
                response += "\n"
        
        # KATEGORİ LİDERLERİ - GÜVENLİ FONLARDAN
        if safe_funds:
            best_return = max(safe_funds, key=lambda x: x['annual_return'])
            best_sharpe = max(safe_funds, key=lambda x: x['sharpe_ratio'])
            safest = min(safe_funds, key=lambda x: x['volatility'])
            biggest = max(safe_funds, key=lambda x: x['capacity'])
            most_relevant = max(safe_funds, key=lambda x: x['portfolio_score'])
            
            response += f"🏅 GÜVENLİ {currency_code} KATEGORİ LİDERLERİ:\n"
            response += f"   📈 En Yüksek Getiri: {best_return['fcode']} (%{best_return['annual_return']:+.1f}) {self._get_risk_indicator(best_return['risk_level'])}\n"
            response += f"   ⚡ En İyi Sharpe: {best_sharpe['fcode']} ({best_sharpe['sharpe_ratio']:.3f}) {self._get_risk_indicator(best_sharpe['risk_level'])}\n"
            response += f"   🛡️ En Güvenli: {safest['fcode']} (%{safest['volatility']:.1f} risk) {self._get_risk_indicator(safest['risk_level'])}\n"
            response += f"   💰 En Büyük: {biggest['fcode']} ({biggest['capacity']/1000000:.0f}M TL) {self._get_risk_indicator(biggest['risk_level'])}\n"
            response += f"   💼 En Uyumlu: {most_relevant['fcode']} (%{most_relevant['portfolio_score']*100:.1f}) {self._get_risk_indicator(most_relevant['risk_level'])}\n\n"
        
        # ÖZEL TAVSİYELER
        response += f"💡 {currency_code} YATIRIM TAVSİYELERİ (Risk Assessment Dahil):\n"
        
        if currency_type == 'usd':
            response += f"   🇺🇸 Dolar güçlenme beklentisinde güvenli USD fonları tercih edilebilir\n"
            response += f"   🛡️ {low_risk_count} düşük riskli, {medium_risk_count} orta riskli USD fonu mevcut\n"
            response += f"   ⚠️ TL/USD paritesindeki değişimleri takip edin\n"
            response += f"   💼 Portföyde maksimum %30 USD ağırlığı önerilir\n"
            
        elif currency_type == 'eur':
            response += f"   🇪🇺 Avrupa ekonomisindeki gelişmeleri izleyin\n"
            response += f"   🛡️ Risk seviyesi: {low_risk_count} güvenli, {medium_risk_count} orta riskli EUR fonu\n"
            response += f"   📊 EUR/TRY paritesindeki hareketleri takip edin\n"
            response += f"   💼 Dolar karşısında hedge etkisi sağlayabilir\n"
            
        elif currency_type == 'tl_based':
            response += f"   🇹🇷 TL bazlı fonlar döviz riskinden korunma sağlar\n"
            response += f"   🛡️ Genelde düşük risk: {low_risk_count + medium_risk_count} güvenli TL fonu\n"
            response += f"   📈 Enflasyon oranının üstünde getiri hedefleyin\n"
            response += f"   🛡️ Konservatif yatırımcılar için uygun\n"
            
        elif currency_type == 'inflation_protected':
            response += f"   📊 Enflasyon verilerini yakından takip edin\n"
            response += f"   🛡️ Risk dağılımı: {low_risk_count} güvenli, {high_risk_count + extreme_risk_count} riskli\n"
            response += f"   📈 Reel getiri odaklı yatırım stratejisi\n"
            response += f"   ⚖️ Portföyde enflasyon hedge aracı olarak kullanın\n"
            
        elif currency_type == 'hedge_funds':
            response += f"   🛡️ Döviz riskini minimize etmek için tercih edin\n"
            response += f"   📊 Risk seviyesi: genelde orta-yüksek ({medium_risk_count + high_risk_count} fon)\n"
            response += f"   📊 Türev araç maliyetlerini göz önünde bulundurun\n"
            response += f"   💡 Volatilite yüksek dönemlerde değerlendirin\n"
            
        elif currency_type == 'precious_metals':
            response += f"   💰 Altın enflasyon hedge aracı olarak kullanılabilir\n"
            response += f"   🛡️ Risk dağılımı: {low_risk_count + medium_risk_count} güvenli altın fonu\n"
            response += f"   📊 Küresel belirsizlik dönemlerinde avantajlı\n"
            response += f"   ⚖️ Portföyde %5-15 ağırlık önerilir\n"
        
        # RİSK UYARILARI
        response += f"\n⚠️ {currency_code} RİSK UYARILARI:\n"
        
        if extreme_risk_count > 0:
            response += f"   🔴 {extreme_risk_count} EXTREME RİSK fonu tespit edildi - KAÇININ!\n"
        if non_tradeable_count > 0:
            response += f"   ⛔ {non_tradeable_count} fon TRADE EDİLEMEZ durumda!\n"
        if high_risk_count > 0:
            response += f"   🟠 {high_risk_count} YÜKSEK RİSK fonu - Dikkatli olun\n"
        
        response += f"   🟡 {medium_risk_count} ORTA RİSK fonu - Kabul edilebilir\n"
        response += f"   🟢 {low_risk_count} DÜŞÜK RİSK fonu - Güvenli seçenek\n"
        response += f"   • Döviz kurlarındaki volatilite yüksek risk içerir\n"
        response += f"   • Küresel ekonomik gelişmeleri yakından izleyin\n"
        response += f"   • Merkez bankası politikalarındaki değişimlere dikkat\n"
        response += f"   • Portföy diversifikasyonunu ihmal etmeyin\n"
        
        # ÖNERİLEN FON - Güvenli fonlardan en iyi
        if safe_funds:
            top_fund = safe_funds[0]
            risk_indicator = self._get_risk_indicator(top_fund['risk_level'])
            response += f"\n🎯 ÖNERİLEN GÜVENLİ FON: {top_fund['fcode']} {risk_indicator}\n"
            response += f"   📊 {currency_code} Skoru: {top_fund['currency_score']:.1f}/100\n"
            response += f"   🛡️ Risk Skoru: {top_fund['risk_score']:.1f}/100 ({top_fund['risk_level']})\n"
            response += f"   📈 Beklenen Getiri: %{top_fund['annual_return']:+.1f}\n"
            response += f"   🛡️ Risk Seviyesi: %{top_fund['volatility']:.1f}\n"
            
            if top_fund.get('requires_research'):
                response += f"   ⚠️ Yatırım öncesi detaylı araştırma önerilir\n"
        
        return response
    
    def analyze_all_foreign_currencies(self, question):
        """Tüm döviz fonlarını karşılaştırmalı analiz et - MV tabanlı + Risk Assessment"""
        print("💱 Tüm döviz fonları karşılaştırmalı analiz (MV tabanlı)...")
        
        currency_types = ['usd', 'eur', 'hedge_funds']
        comparison_results = {}
        
        for currency_type in currency_types:
            print(f"   📊 {currency_type.upper()} analizi...")
            
            # MV tabanlı arama
            funds = self._find_currency_funds_mv(currency_type)
            if not funds:
                # Fallback
                funds = self.find_currency_funds_sql(currency_type)
                
            if funds:
                # MV tabanlı performans analizi
                performance = self.analyze_currency_performance_mv(currency_type, funds[:30])
                
                if performance:
                    # Risk istatistikleri
                    extreme_risk = len([f for f in performance if f['risk_level'] == 'EXTREME'])
                    high_risk = len([f for f in performance if f['risk_level'] == 'HIGH'])
                    safe_funds = [f for f in performance if f['risk_level'] in ['LOW', 'MEDIUM']]
                    
                    # Özet istatistikler - sadece güvenli fonlardan
                    if safe_funds:
                        avg_return = sum(f['annual_return'] for f in safe_funds) / len(safe_funds)
                        avg_volatility = sum(f['volatility'] for f in safe_funds) / len(safe_funds)
                        avg_score = sum(f['currency_score'] for f in safe_funds) / len(safe_funds)
                        total_capacity = sum(f['capacity'] for f in safe_funds)
                        
                        comparison_results[currency_type] = {
                            'total_fund_count': len(performance),
                            'safe_fund_count': len(safe_funds),
                            'extreme_risk_count': extreme_risk,
                            'high_risk_count': high_risk,
                            'avg_return': avg_return,
                            'avg_volatility': avg_volatility,
                            'avg_score': avg_score,
                            'total_capacity': total_capacity,
                            'best_safe_fund': max(safe_funds, key=lambda x: x['currency_score']),
                            'performance_data': performance
                        }
        
        if not comparison_results:
            return "❌ Döviz fonları karşılaştırması için yeterli veri bulunamadı."
        
        return self.format_currency_comparison_results(comparison_results)
    
    def format_currency_comparison_results(self, comparison_results):
        """Döviz karşılaştırma sonuçlarını formatla - Risk Assessment dahil"""
        
        response = f"\n💱 DÖVİZ FONLARI KARŞILAŞTIRMALI ANALİZ (MV + Risk Assessment)\n"
        response += f"{'='*70}\n\n"
        
        response += f"📊 KARŞILAŞTIRILAN DÖVİZ TİPLERİ: {len(comparison_results)}\n"
        response += f"⚡ Materialized View kullanıldı\n\n"
        
        # KARŞILAŞTIRMA TABLOSU - Risk bilgileri dahil
        response += f"📈 DÖVİZ PERFORMANS & RİSK KARŞILAŞTIRMASI:\n\n"
        response += f"{'Döviz':<10} | {'Toplam':<6} | {'Güvenli':<7} | {'Riskli':<6} | {'Getiri':<8} | {'Risk':<7} | {'Skor':<5}\n"
        response += f"{'-'*10}|{'-'*7}|{'-'*8}|{'-'*7}|{'-'*9}|{'-'*8}|{'-'*5}\n"
        
        # Skor bazında sırala
        sorted_currencies = sorted(comparison_results.items(), key=lambda x: x[1]['avg_score'], reverse=True)
        
        currency_names = {
            'usd': 'USD',
            'eur': 'EUR', 
            'hedge_funds': 'HEDGE'
        }
        
        for currency_type, data in sorted_currencies:
            currency_name = currency_names.get(currency_type, currency_type.upper())
            risky_count = data['extreme_risk_count'] + data['high_risk_count']
            
            response += f"{currency_name:<10} | {data['total_fund_count']:<6} | "
            response += f"{data['safe_fund_count']:<7} | {risky_count:<6} | "
            response += f"%{data['avg_return']:+5.1f} | %{data['avg_volatility']:5.1f} | {data['avg_score']:4.1f}\n"
        
        # KAZANANLAR - GÜVENLİ FONLAR BAZINDA
        response += f"\n🏆 DÖVİZ KATEGORİ KAZANANLARI (Güvenli Fonlar):\n"
        
        best_return_currency = max(comparison_results.items(), key=lambda x: x[1]['avg_return'])
        best_score_currency = max(comparison_results.items(), key=lambda x: x[1]['avg_score'])
        safest_currency = min(comparison_results.items(), key=lambda x: x[1]['avg_volatility'])
        biggest_currency = max(comparison_results.items(), key=lambda x: x[1]['total_capacity'])
        most_safe_currency = max(comparison_results.items(), key=lambda x: x[1]['safe_fund_count'])
        
        response += f"   📈 En Yüksek Getiri: {currency_names.get(best_return_currency[0], best_return_currency[0]).upper()} (%{best_return_currency[1]['avg_return']:+.1f})\n"
        response += f"   🎯 En Yüksek Skor: {currency_names.get(best_score_currency[0], best_score_currency[0]).upper()} ({best_score_currency[1]['avg_score']:.1f})\n"
        response += f"   🛡️ En Güvenli: {currency_names.get(safest_currency[0], safest_currency[0]).upper()} (%{safest_currency[1]['avg_volatility']:.1f} risk)\n"
        response += f"   💰 En Büyük Varlık: {currency_names.get(biggest_currency[0], biggest_currency[0]).upper()} ({biggest_currency[1]['total_capacity']/1000000000:.1f}B TL)\n"
        response += f"   🟢 En Çok Güvenli Fon: {currency_names.get(most_safe_currency[0], most_safe_currency[0]).upper()} ({most_safe_currency[1]['safe_fund_count']} fon)\n"
        
        # RİSK UYARISI
        total_extreme = sum(data['extreme_risk_count'] for data in comparison_results.values())
        total_high = sum(data['high_risk_count'] for data in comparison_results.values())
        
        if total_extreme > 0 or total_high > 0:
            response += f"\n⚠️ DÖVİZ FONLARI RİSK UYARISI:\n"
            response += f"   🔴 {total_extreme} EXTREME RİSK döviz fonu tespit edildi\n"
            response += f"   🟠 {total_high} YÜKSEK RİSK döviz fonu mevcut\n"
            response += f"   💡 Sadece güvenli fonları tercih edin!\n\n"
        
        # HER DÖVİZDEN EN İYİ GÜVENLİ FON
        response += f"\n🌟 HER DÖVİZDEN EN İYİ GÜVENLİ FON:\n\n"
        
        for currency_type, data in sorted_currencies:
            currency_name = currency_names.get(currency_type, currency_type.upper())
            best_fund = data['best_safe_fund']
            risk_indicator = self._get_risk_indicator(best_fund['risk_level'])
            
            response += f"💱 {currency_name}:\n"
            response += f"   {best_fund['fcode']} - Skor: {best_fund['currency_score']:.1f} {risk_indicator}\n"
            response += f"   Getiri: %{best_fund['annual_return']:+.1f}, Risk: %{best_fund['volatility']:.1f}\n"
            response += f"   Risk Seviyesi: {best_fund['risk_level']}\n"
            response += f"   {best_fund['fund_name'][:35]}...\n\n"
        
        # PORTFÖY ÖNERİSİ - Risk Assessment Dahil
        winner = sorted_currencies[0]
        response += f"💼 GÜVENLİ DÖVİZ PORTFÖY ÖNERİSİ:\n"
        response += f"   🥇 Ana Güvenli Döviz: {currency_names.get(winner[0], winner[0]).upper()}\n"
        response += f"   📊 Önerilen Ağırlık: %40-60\n"
        response += f"   🛡️ Hedge Fonları: %20-30 (risk seviyesine dikkat)\n"
        response += f"   ⚖️ Diversifikasyon: TL + Altın %20-40\n"
        response += f"   🔴 EXTREME/YÜKSEK risk fonlarından uzak durun!\n"
        response += f"   🟢 Sadece DÜŞÜK/ORTA risk fonları tercih edin\n"
        
        return response
    
    def _handle_general_currency_overview(self):
        """Genel döviz/enflasyon fon genel bakış"""
        response = f"\n💱 DÖVİZ VE ENFLASYON FON ANALİZ SİSTEMİ (MV + Risk Assessment)\n"
        response += f"{'='*70}\n\n"
        
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
        response += f"   ✅ Materialized View entegrasyonu (hızlı analiz)\n"
        response += f"   ✅ TÜM veritabanı tarama (1700+ fon)\n"
        response += f"   ✅ Döviz özel skorlama sistemi\n"
        response += f"   ✅ Portföy uyumluluk analizi\n"
        response += f"   ✅ Risk-getiri optimizasyonu\n"
        response += f"   ✅ Enflasyon hedge analizi\n"
        response += f"   ✅ Döviz karşılaştırması\n"
        response += f"   ✅ Yatırım önerileri ve uyarılar\n"
        response += f"   🆕 **Risk Assessment entegrasyonu**\n"
        response += f"   🆕 **EXTREME/YÜKSEK risk tespiti**\n"
        response += f"   🆕 **Güvenli fon filtreleme**\n"
        response += f"   🆕 **Trade edilebilirlik kontrolü**\n\n"
        
        response += f"📈 HIZLI BAŞLANGIÇ:\n"
        response += f"   Döviz adı veya 'enflasyon' yazmanız yeterli!\n"
        response += f"   Örnek: 'dolar', 'euro', 'enflasyon', 'altın'\n\n"
        
        response += f"🛡️ RİSK ASSESSMENT ÖZELLİKLERİ:\n"
        response += f"   • Otomatik risk seviyesi tespiti\n"
        response += f"   • EXTREME risk fonları uyarısı\n"
        response += f"   • Trade edilebilirlik kontrolü\n"
        response += f"   • Güvenli fon önerileri\n"
        response += f"   • Risk faktörü analizi\n"
        response += f"   • Portföy güvenlik skoru\n\n"
        
        response += f"⚠️ ÖNEMLİ NOT:\n"
        response += f"   • Döviz yatırımları yüksek risk içerir\n"
        response += f"   • Kur hareketleri ani ve keskin olabilir\n"
        response += f"   • Portföy diversifikasyonu kritik önemde\n"
        response += f"   • Uzun vadeli yatırım stratejisi önerilir\n"
        response += f"   🔴 EXTREME risk fonlarından uzak durun!\n"
        response += f"   ⛔ Trade edilemez fonlara yatırım yapmayın!\n"
        response += f"   🟢 Sadece güvenli fonları tercih edin\n"
        
        return response

    # =============================================================
    # STATIC METHODS FOR INTEGRATION
    # =============================================================
    
    @staticmethod
    def get_examples():
        """Döviz ve enflasyon analiz örnekleri"""
        return [
            "Dolar fonlarının bu ayki performansı",
            "Euro bazlı fonlar",
            "Enflasyon korumalı fonlar",
            "Döviz hedge fonları",
            "USD cinsinden fonlar",
            "Altın fonları analizi",
            "Kıymetli maden fonları"
        ]
    
    @staticmethod
    def get_keywords():
        """Döviz/enflasyon anahtar kelimeleri"""
        return [
            "dolar", "dollar", "usd", "euro", "eur", "döviz", "currency",
            "enflasyon", "inflation", "hedge", "koruma", "altın", "gold",
            "kıymetli maden", "precious metals", "fx", "yabancı para"
        ]
    
    @staticmethod
    def get_patterns():
        """Döviz pattern'leri - GÜÇLENDİRİLMİŞ"""
        return [
            {
                'type': 'regex',
                'pattern': r'(dolar|euro|usd|eur)\s+fon',
                'score': 0.98
            },
            {
                'type': 'regex',
                'pattern': r'(dolar|euro|usd|eur).*?(performans|getiri|analiz)',
                'score': 0.97
            },
            {
                'type': 'contains_all',
                'words': ['döviz', 'fon'],
                'score': 0.95
            },
            {
                'type': 'contains_all',
                'words': ['enflasyon', 'korumalı'],
                'score': 0.95
            }
        ]    
    
    @staticmethod
    def get_method_patterns():
        """Method mapping"""
        return {
            'analyze_currency_funds': ['dolar', 'euro', 'döviz', 'currency'],
            'analyze_inflation_funds_mv': ['enflasyon', 'inflation', 'korumalı']
        }

# =============================================================
# GLOBAL UTILITY FUNCTION FOR RISK CHECKING
# =============================================================

def check_fund_risk_before_recommendation(coordinator, fcode):
    """
    Herhangi bir fon önerisinden önce risk kontrolü
    
    Returns:
        tuple: (is_safe, risk_assessment, risk_warning)
    """
    try:
        mv_query = f"SELECT * FROM mv_fund_technical_indicators WHERE fcode = '{fcode}'"
        mv_data = coordinator.db.execute_query(mv_query)
        
        if mv_data.empty:
            return True, None, ""  # Veri yoksa güvenli say
        
        risk_data = {
            'fcode': fcode,
            'price_vs_sma20': float(mv_data.iloc[0]['price_vs_sma20']),
            'rsi_14': float(mv_data.iloc[0]['rsi_14']),
            'stochastic_14': float(mv_data.iloc[0]['stochastic_14']),
            'days_since_last_trade': int(mv_data.iloc[0]['days_since_last_trade']),
            'investorcount': int(mv_data.iloc[0]['investorcount'])
        }
        
        risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
        risk_warning = RiskAssessment.format_risk_warning(risk_assessment)
        
        is_safe = risk_assessment['risk_level'] not in ['EXTREME'] and risk_assessment.get('tradeable', True)
        
        return is_safe, risk_assessment, risk_warning
        
    except Exception as e:
        print(f"Risk kontrolü hatası: {e}")
        return True, None, ""

# =============================================================
# PORTFOLIO ANALYSIS HELPERS
# =============================================================

def analyze_currency_portfolio_distribution(db_manager, fcode):
    """Detaylı portföy dağılım analizi - MV tabanlı"""
    try:
        # Önce MV'den kontrol et
        mv_query = f"""
        SELECT * FROM mv_fund_details_latest 
        WHERE fcode = '{fcode}'
        """
        
        result = db_manager.execute_query(mv_query)
        
        if not result.empty:
            return result.iloc[0].to_dict()
        
        # Fallback: Normal sorgu
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

# =============================================================
# ENHANCED MV QUERIES
# =============================================================

def get_currency_funds_from_mv(db_manager, currency_type='all'):
    """MV'den döviz fonlarını çek - performans dahil"""
    try:
        currency_filter = ""
        if currency_type != 'all':
            keywords = CurrencyInflationAnalyzer(db_manager, None).currency_keywords.get(currency_type, {}).get('keywords', [])
            if keywords:
                conditions = [f"UPPER(lf.ftitle) LIKE '%{kw}%'" for kw in keywords[:3]]
                currency_filter = f"WHERE ({' OR '.join(conditions)})"
        
        query = f"""
        SELECT 
            lf.fcode,
            lf.ftitle,
            lf.price,
            lf.fcapacity,
            lf.investorcount,
            pm.annual_return * 100 as annual_return_pct,
            pm.annual_volatility * 100 as volatility_pct,
            pm.sharpe_ratio,
            pm.win_rate * 100 as win_rate_pct,
            ti.rsi_14,
            ti.price_vs_sma20,
            ti.days_since_last_trade,
            pp.return_30d,
            pp.return_90d,
            pp.return_180d
        FROM mv_latest_fund_data lf
        LEFT JOIN mv_fund_performance_metrics pm ON lf.fcode = pm.fcode
        LEFT JOIN mv_fund_technical_indicators ti ON lf.fcode = ti.fcode
        LEFT JOIN mv_fund_period_performance pp ON lf.fcode = pp.fcode
        {currency_filter}
        ORDER BY pm.sharpe_ratio DESC NULLS LAST
        LIMIT 100
        """
        
        return db_manager.execute_query(query)
        
    except Exception as e:
        logging.getLogger(__name__).error(f"MV currency query error: {e}")
        return pd.DataFrame()

# =============================================================
# DEMO VE TEST FONKSİYONLARI
# =============================================================

def demo_currency_inflation_analysis():
    """Demo döviz/enflasyon analiz fonksiyonu - MV entegreli"""
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
    
    print("💱 DÖVİZ VE ENFLASYON ANALİZ SİSTEMİ DEMO (MV + Risk Assessment)")
    print("="*70)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[DEMO {i}/6] {question}")
        print("-" * 40)
        
        try:
            result = analyzer.analyze_currency_inflation_question(question)
            # İlk 300 karakteri göster
            preview = result[:300] + "..." if len(result) > 300 else result
            print(preview)
            print("✅ Demo başarılı (MV + Risk Assessment dahil)")
            
            if i < len(test_questions):
                input("\nDevam etmek için Enter'a basın...")
                
        except Exception as e:
            print(f"❌ Demo hatası: {e}")
    
    print(f"\n🎉 Döviz/Enflasyon analiz demo tamamlandı! (MV + Risk Assessment ile güçlendirilmiş)")

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
    'use_materialized_views': True,     # MV kullanımı
    'mv_refresh_hours': 24,             # MV yenileme süresi
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
    },
    # Risk Assessment konfigürasyonu
    'risk_settings': {
        'exclude_extreme_risk': True,    # Extreme risk fonları listeden çıkar
        'warn_high_risk': True,          # Yüksek risk uyarısı ver
        'prefer_safe_funds': True,       # Güvenli fonları önceliklendir
        'risk_weight_in_score': 0.3,     # Risk skorunun toplam skordaki ağırlığı
        'check_tradeability': True       # Trade edilebilirlik kontrolü
    }
}

if __name__ == "__main__":
    # Demo çalıştır
    demo_currency_inflation_analysis()