# macroeconomic_analyzer.py
"""
Makroekonomik Analiz Modülü
Faiz, seçim, jeopolitik risk ve TCMB kararlarının fon performansına etkilerini analiz eder
"""

import traceback
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
from typing import Dict, List, Tuple

class MacroeconomicAnalyzer:
    """Makroekonomik olayların TEFAS fonlarına etkisini analiz eden sınıf"""
    
    def __init__(self, db_manager, config, coordinator):
        self.db = db_manager
        self.config = config
        self.coordinator = coordinator
        
        # Makroekonomik kategoriler ve ilgili fon türleri
        self.macro_fund_mapping = {
            'faiz_duyarlı': {
                'keywords': ['faiz', 'interest rate', 'tcmb', 'merkez bankası'],
                'fund_types': ['Borçlanma Araçları', 'Para Piyasası', 'Tahvil', 'Hazine Bonosu'],
                'fund_keywords': ['tahvil', 'bono', 'borçlanma', 'para piyasası', 'likit', 'kısa vadeli'],
                'sensitivity': 'high'
            },
            'hisse_bazlı': {
                'keywords': ['seçim', 'election', 'politik', 'political'],
                'fund_types': ['Hisse Senedi', 'Değişken', 'Karma'],
                'fund_keywords': ['hisse', 'değişken', 'karma', 'serbest', 'büyüme'],
                'sensitivity': 'very_high'
            },
            'döviz_korumalı': {
                'keywords': ['jeopolitik', 'geopolitical', 'savaş', 'kriz', 'risk'],
                'fund_types': ['Döviz', 'Eurobond', 'Uluslararası'],
                'fund_keywords': ['döviz', 'euro', 'dolar', 'usd', 'eur', 'altın', 'kıymetli maden'],
                'sensitivity': 'medium'
            },
            'enflasyon_korumalı': {
                'keywords': ['enflasyon', 'inflation', 'tüfe'],
                'fund_types': ['Altın', 'Kıymetli Madenler', 'Endeks'],
                'fund_keywords': ['altın', 'gümüş', 'kıymetli', 'emtia', 'endeks', 'tüfe'],
                'sensitivity': 'high'
            }
        }
        
    def is_macroeconomic_question(self, question: str) -> bool:
        """Sorunun makroekonomik analiz gerektirip gerektirmediğini kontrol eder"""
        question_lower = question.lower()
        
        macro_keywords = [
            'faiz', 'interest', 'tcmb', 'merkez bankası',
            'seçim', 'election', 'politik',
            'jeopolitik', 'geopolitical', 'savaş', 'kriz',
            'enflasyon', 'inflation', 'tüfe',
            'makro', 'ekonomik', 'karar', 'strateji'
        ]
        
        return any(keyword in question_lower for keyword in macro_keywords)
    
    def analyze_macroeconomic_impact(self, question: str) -> str:
        """Makroekonomik soruları analiz eder"""
        question_lower = question.lower()
        
        # Faiz soruları
        if any(word in question_lower for word in ['faiz', 'interest rate', 'tcmb faiz']):
            return self._analyze_interest_rate_impact(question)
        
        # Seçim soruları
        elif any(word in question_lower for word in ['seçim', 'election']):
            return self._analyze_election_impact(question)
        
        # Jeopolitik risk soruları
        elif any(word in question_lower for word in ['jeopolitik', 'geopolitical', 'savaş', 'kriz']):
            return self._analyze_geopolitical_impact(question)
        
        # TCMB kararları
        elif any(word in question_lower for word in ['tcmb', 'merkez bankası']):
            return self._analyze_tcmb_decisions(question)
        
        # Genel makroekonomik strateji
        else:
            return self._analyze_general_macro_strategy(question)
    
# macroeconomic_analyzer.py dosyasında _analyze_interest_rate_impact metodunu düzeltin:

    def _analyze_interest_rate_impact(self, question: str) -> str:
        """Faiz değişimlerinin fon performansına etkisini analiz eder"""
        try:
            print("📊 Faiz etkisi analiz ediliyor...")
            
            # Faiz artışı mı düşüşü mü?
            is_rate_cut = any(word in question.lower() for word in ['indirim', 'düşüş', 'azalma', 'cut', 'decrease'])
            is_rate_hike = any(word in question.lower() for word in ['artış', 'yükseliş', 'artırım', 'hike', 'increase'])
            
            scenario = "indirim" if is_rate_cut else "artış" if is_rate_hike else "değişim"
            
            response = f"\n💹 FAİZ {scenario.upper()} ETKİ ANALİZİ\n"
            response += f"{'='*50}\n\n"
            
            # SQL ile ilgili fon türlerini bul
            try:
                relevant_funds = self._find_macro_sensitive_funds('faiz_duyarlı')
            except Exception as e:
                print(f"_find_macro_sensitive_funds hatası: {e}")
                traceback.print_exc()
                relevant_funds = {}
            
            if is_rate_cut:
                response += f"📉 FAİZ İNDİRİMİ SENARYOSU:\n\n"
                
                response += f"🟢 OLUMLU ETKİLENECEK FON TÜRLERİ:\n"
                response += f"   • Hisse Senedi Fonları (büyüme beklentisi)\n"
                response += f"   • Karma/Değişken Fonlar\n"
                response += f"   • Serbest Fonlar\n"
                response += f"   • Gayrimenkul Fonları\n\n"
                
                response += f"🔴 OLUMSUZ ETKİLENECEK FON TÜRLERİ:\n"
                response += f"   • Para Piyasası Fonları (getiri düşüşü)\n"
                response += f"   • Kısa Vadeli Tahvil Fonları\n"
                response += f"   • Likit Fonlar\n\n"
                
                response += f"💡 STRATEJİ ÖNERİLERİ:\n"
                response += f"   1. Para piyasası fonlarından hisse fonlarına geçiş\n"
                response += f"   2. Uzun vadeli tahvil fonlarını değerlendirin\n"
                response += f"   3. Büyüme odaklı fonlara yönelin\n"
                
            elif is_rate_hike:
                response += f"📈 FAİZ ARTIŞI SENARYOSU:\n\n"
                
                response += f"🟢 OLUMLU ETKİLENECEK FON TÜRLERİ:\n"
                response += f"   • Para Piyasası Fonları (yüksek getiri)\n"
                response += f"   • Kısa Vadeli Tahvil Fonları\n"
                response += f"   • Likit Fonlar\n"
                response += f"   • Mevduat Benzeri Fonlar\n\n"
                
                response += f"🔴 OLUMSUZ ETKİLENECEK FON TÜRLERİ:\n"
                response += f"   • Hisse Senedi Fonları (değerleme baskısı)\n"
                response += f"   • Uzun Vadeli Tahvil Fonları\n"
                response += f"   • Gayrimenkul Fonları\n\n"
                
                response += f"💡 STRATEJİ ÖNERİLERİ:\n"
                response += f"   1. Hisse fonlarından para piyasasına geçiş\n"
                response += f"   2. Kısa vadeli enstrümanlara odaklanın\n"
                response += f"   3. Volatiliteye karşı korunma sağlayın\n"
            
            # Spesifik fon önerileri - DÜZELTME BURADA
            if relevant_funds:
                response += f"\n📊 İLGİLİ FONLAR (Veritabanından):\n\n"
                
                # Dictionary'yi listeye çevir ve ilk 10'u al
                fund_items = list(relevant_funds.items())[:10]
                for i, (fcode, fund_info) in enumerate(fund_items, 1):
                    response += f"{i}. {fcode}\n"
                    response += f"   📈 Son 30 gün getiri: %{fund_info.get('return_30d', 0):.2f}\n"
                    response += f"   📉 Volatilite: %{fund_info.get('volatility', 0):.2f}\n"
                    response += f"   🏷️ Tür: {fund_info.get('fund_type', 'N/A')}\n"
                    response += f"\n"
            
            # AI yorumu ekle
            try:
                if hasattr(self.coordinator, 'ai_analyzer') and self.coordinator.ai_analyzer.openai_available:
                    response += self._get_ai_macro_commentary('faiz', scenario, relevant_funds)
            except Exception as e:
                print(f"AI yorum hatası: {e}")
            
            return response
            
        except Exception as e:
            print(f"_analyze_interest_rate_impact hatası: {e}")
            traceback.print_exc()
            return f"❌ Faiz analizi sırasında hata oluştu: {str(e)}"
        
    def _analyze_election_impact(self, question: str) -> str:
        """Seçim dönemlerinin fon performansına etkisini analiz eder"""
        print("🗳️ Seçim etkisi analiz ediliyor...")
        
        response = f"\n🗳️ SEÇİM DÖNEMİ FON STRATEJİSİ\n"
        response += f"{'='*50}\n\n"
        
        response += f"📊 SEÇİM DÖNEMLERİNDE FON PERFORMANSLARI:\n\n"
        
        response += f"🔍 TARİHSEL ANALİZ:\n"
        response += f"   • Seçim öncesi 3 ay: Yüksek volatilite\n"
        response += f"   • Seçim sonrası 1 ay: Keskin hareketler\n"
        response += f"   • Belirsizlik primi: %5-15 arası\n\n"
        
        response += f"🟢 AVANTAJLI FON TÜRLERİ:\n"
        response += f"   1. **Döviz Fonları** (hedge amaçlı)\n"
        response += f"   2. **Altın/Kıymetli Maden Fonları** (güvenli liman)\n"
        response += f"   3. **Para Piyasası Fonları** (düşük risk)\n"
        response += f"   4. **Kısa Vadeli Tahvil Fonları**\n\n"
        
        response += f"🔴 RİSKLİ FON TÜRLERİ:\n"
        response += f"   1. **Hisse Senedi Fonları** (yüksek volatilite)\n"
        response += f"   2. **Sektörel Fonlar** (politik etki)\n"
        response += f"   3. **Küçük Şirket Fonları**\n"
        response += f"   4. **Uzun Vadeli Tahvil Fonları**\n\n"
        
        # SQL ile volatilitesi düşük fonları bul
        safe_election_funds = self._find_low_volatility_funds()
        
        if safe_election_funds:
            response += f"📊 SEÇİM DÖNEMİ İÇİN GÜVENLİ FONLAR:\n\n"
            
            # Dictionary'yi listeye çevir - DÜZELTME
            fund_items = list(safe_election_funds.items())[:8]
            for i, (fcode, metrics) in enumerate(fund_items, 1):
                response += f"{i}. {fcode}\n"
                response += f"   📉 Volatilite: %{metrics.get('volatility', 0):.2f} (düşük)\n"
                response += f"   📈 30 gün getiri: %{metrics.get('return_30d', 0):.2f}\n"
                response += f"   🛡️ Risk skoru: {metrics.get('risk_score', 0)}/10\n"
                response += f"\n"
        
        response += f"💡 SEÇİM STRATEJİSİ ÖNERİLERİ:\n"
        response += f"   1. **Seçim öncesi 2-3 ay**: Portföyü defensive yapın\n"
        response += f"   2. **Volatilite hedge**: %20-30 döviz/altın\n"
        response += f"   3. **Nakit pozisyon**: %10-20 para piyasası\n"
        response += f"   4. **Seçim sonrası**: Kademeli giriş stratejisi\n"
        response += f"   5. **Stop-loss**: Mutlaka kullanın\n"
        
        return response
    
    def _analyze_geopolitical_impact(self, question: str) -> str:
        """Jeopolitik risklerin fon performansına etkisini analiz eder"""
        print("🌍 Jeopolitik risk analizi yapılıyor...")
        
        response = f"\n🌍 JEOPOLİTİK RİSK ANALİZİ\n"
        response += f"{'='*50}\n\n"
        
        response += f"⚠️ GÜNCEL JEOPOLİTİK RİSKLER:\n"
        response += f"   • Bölgesel çatışmalar ve savaşlar\n"
        response += f"   • Ticaret savaşları ve ambargolar\n"
        response += f"   • Enerji krizi ve tedarik zinciri\n"
        response += f"   • Küresel resesyon endişeleri\n\n"
        
        response += f"🛡️ KORUNMA SAĞLAYAN FON TÜRLERİ:\n\n"
        
        response += f"1. **ALTIN FONLARI** 🥇\n"
        response += f"   • Klasik güvenli liman\n"
        response += f"   • Kriz dönemlerinde %10-30 prim\n"
        response += f"   • Enflasyon koruması bonus\n\n"
        
        response += f"2. **DÖVİZ FONLARI** 💵\n"
        response += f"   • USD/EUR bazlı fonlar\n"
        response += f"   • TL değer kaybına karşı koruma\n"
        response += f"   • Küresel diversifikasyon\n\n"
        
        response += f"3. **KIYMETI MADEN FONLARI** 💎\n"
        response += f"   • Altın + Gümüş + Platin\n"
        response += f"   • Fiziki dayanak avantajı\n"
        response += f"   • Uzun vadeli değer saklama\n\n"
        
        # Döviz ve altın fonları bul
        safe_haven_funds = self._find_safe_haven_funds()
        
        if safe_haven_funds:
            response += f"📊 GÜVENLİ LİMAN FONLARI:\n\n"
            
            # Dictionary'yi listeye çevir - DÜZELTME
            fund_items = list(safe_haven_funds.items())[:10]
            for i, (fcode, info) in enumerate(fund_items, 1):
                response += f"{i}. {fcode}\n"
                response += f"   🏷️ Tür: {info.get('fund_type', 'N/A')}\n"
                response += f"   📈 30 gün getiri: %{info.get('return_30d', 0):.2f}\n"
                response += f"   💰 Kapasite: {info.get('capacity', 0)/1e6:.1f}M TL\n"
                response += f"\n"
        
        response += f"🎯 JEOPOLİTİK RİSK YÖNETİM STRATEJİSİ:\n\n"
        response += f"📊 ÖNERİLEN PORTFÖY DAĞILIMI:\n"
        response += f"   • %25-30 Döviz Fonları (USD/EUR mix)\n"
        response += f"   • %20-25 Altın/Kıymetli Maden\n"
        response += f"   • %20 Para Piyasası (likidite)\n"
        response += f"   • %15-20 Kısa Vadeli Tahvil\n"
        response += f"   • %10-15 Defansif Hisse Fonları\n\n"
        
        response += f"⚡ TAKTİKSEL ÖNERİLER:\n"
        response += f"   1. Varlık çeşitlendirmesi kritik\n"
        response += f"   2. Coğrafi diversifikasyon şart\n"
        response += f"   3. Likidite tamponu (%10-20)\n"
        response += f"   4. Düzenli rebalancing\n"
        response += f"   5. Panik satış yapmayın\n"
        
        return response
    
    def _analyze_tcmb_decisions(self, question: str) -> str:
        """TCMB kararlarının etkisini analiz eder"""
        print("🏦 TCMB karar etkisi analiz ediliyor...")
        
        response = f"\n🏦 TCMB KARARLARI SONRASI STRATEJİ\n"
        response += f"{'='*50}\n\n"
        
        response += f"📊 TCMB POLİTİKA ARAÇLARI VE ETKİLERİ:\n\n"
        
        response += f"1. **POLİTİKA FAİZİ**\n"
        response += f"   • ↑ Artış → Para piyasası fonları ✅\n"
        response += f"   • ↓ İndirim → Hisse fonları ✅\n\n"
        
        response += f"2. **ZORUNLU KARŞILIKLAR**\n"
        response += f"   • ↑ Artış → Likidite daralması\n"
        response += f"   • ↓ İndirim → Kredi genişlemesi\n\n"
        
        response += f"3. **DÖVİZ REZERVLERİ**\n"
        response += f"   • Müdahale → Döviz fonları etkilenir\n"
        response += f"   • Swap anlaşmaları → TL güçlenir\n\n"
        
        # Son dönem performans analizi
        response += f"📈 TCMB KARARLARI SONRASI TİPİK HAREKETLER:\n\n"
        
        response += f"⏱️ **İLK 24 SAAT**\n"
        response += f"   • Yüksek volatilite\n"
        response += f"   • Keskin fiyat hareketleri\n"
        response += f"   • Yüksek işlem hacmi\n\n"
        
        response += f"📅 **İLK HAFTA**\n"
        response += f"   • Trend oluşumu\n"
        response += f"   • Sektörel ayrışma\n"
        response += f"   • Pozisyon ayarlamaları\n\n"
        
        # Strateji matrisi
        response += f"🎯 TCMB KARAR MATRİSİ:\n\n"
        response += f"┌─────────────────┬──────────────────┬─────────────────┐\n"
        response += f"│ TCMB KARARI     │ KAZANAN FONLAR   │ KAYBEDEN FONLAR │\n"
        response += f"├─────────────────┼──────────────────┼─────────────────┤\n"
        response += f"│ Faiz Artışı     │ Para Piyasası    │ Hisse Senedi    │\n"
        response += f"│                 │ Tahvil (Kısa)    │ Uzun Tahvil     │\n"
        response += f"├─────────────────┼──────────────────┼─────────────────┤\n"
        response += f"│ Faiz İndirimi   │ Hisse Senedi     │ Para Piyasası   │\n"
        response += f"│                 │ Gayrimenkul      │ Mevduat Tipi    │\n"
        response += f"├─────────────────┼──────────────────┼─────────────────┤\n"
        response += f"│ Sıkılaştırma    │ Döviz Fonları    │ Büyüme Fonları  │\n"
        response += f"│                 │ Defansif Hisse   │ Küçük Şirket    │\n"
        response += f"└─────────────────┴──────────────────┴─────────────────┘\n\n"
        
        response += f"💡 TCMB SONRASI AKSİYON PLANI:\n"
        response += f"   1. **T+0**: Karar anını bekleyin\n"
        response += f"   2. **T+1**: İlk tepkiyi gözlemleyin\n"
        response += f"   3. **T+2-5**: Pozisyon ayarlayın\n"
        response += f"   4. **T+7**: Trend teyidi\n"
        response += f"   5. **T+30**: Performans değerlendirme\n"
        
        # AI yorumu
        if hasattr(self.coordinator, 'ai_analyzer'):
            response += self._get_tcmb_ai_analysis()
        
        return response
    
    def _analyze_general_macro_strategy(self, question: str) -> str:
        """Genel makroekonomik strateji analizi"""
        print("📈 Genel makro strateji analiz ediliyor...")
        
        response = f"\n📈 GENEL MAKROEKONOMİK STRATEJİ\n"
        response += f"{'='*50}\n\n"
        
        response += f"🌍 GÜNCEL MAKRO GÖRÜNÜM:\n"
        response += f"   • Küresel: Fed politikaları, resesyon riski\n"
        response += f"   • Yerel: TCMB duruşu, enflasyon seyri\n"
        response += f"   • Jeopolitik: Bölgesel riskler\n"
        response += f"   • Piyasalar: Risk iştahı düşük\n\n"
        
        response += f"📊 MAKRO BAZLI FON SEÇİM MATRİSİ:\n\n"
        
        # Senaryo bazlı öneriler
        scenarios = {
            'Enflasyonist Ortam': {
                'funds': ['Altın', 'TÜFE Endeksli', 'Kıymetli Maden', 'Döviz'],
                'weight': '40%'
            },
            'Resesyon Riski': {
                'funds': ['Para Piyasası', 'Kısa Tahvil', 'Defansif Hisse'],
                'weight': '30%'
            },
            'Büyüme Dönemi': {
                'funds': ['Hisse Senedi', 'Teknoloji', 'Küçük Şirket'],
                'weight': '20%'
            },
            'Belirsizlik': {
                'funds': ['Karma/Dengeli', 'Serbest Fon'],
                'weight': '10%'
            }
        }
        
        for scenario, details in scenarios.items():
            response += f"📍 {scenario}:\n"
            response += f"   Önerilen: {', '.join(details['funds'])}\n"
            response += f"   Ağırlık: {details['weight']}\n\n"
        
        # Dinamik portföy önerisi
        response += f"🎯 DİNAMİK PORTFÖY ÖNERİSİ (Güncel Durum):\n\n"
        
        portfolio = self._create_macro_portfolio()
        
        for asset_class, allocation in portfolio.items():
            response += f"   • {asset_class}: %{allocation['weight']}\n"
            response += f"     Gerekçe: {allocation['reason']}\n\n"
        
        response += f"🔄 REBALANCING TAKVİMİ:\n"
        response += f"   • Haftalık: Piyasa taraması\n"
        response += f"   • Aylık: Pozisyon gözden geçirme\n"
        response += f"   • Çeyreklik: Strateji revizyonu\n"
        response += f"   • Yıllık: Tam portföy analizi\n"
        
        return response
    
    def _find_macro_sensitive_funds(self, category: str) -> Dict:
        """Makroekonomik olaylara duyarlı fonları bulur"""
        try:
            mapping = self.macro_fund_mapping.get(category, {})
            keywords = mapping.get('fund_keywords', [])
            
            if not keywords:
                return {}
            
            # SQL sorgusu - düzeltilmiş versiyon
            keyword_conditions = " OR ".join([f"LOWER(ftitle) LIKE '%{kw}%'" for kw in keywords])
            
            query = f"""
            WITH latest_prices AS (
                SELECT DISTINCT ON (fcode) 
                    fcode, ftitle, price as latest_price, pdate
                FROM tefasfunds
                WHERE pdate >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY fcode, pdate DESC
            ),
            month_ago_prices AS (
                SELECT DISTINCT ON (fcode) 
                    fcode, price as price_30d_ago
                FROM tefasfunds
                WHERE pdate >= CURRENT_DATE - INTERVAL '35 days'
                AND pdate <= CURRENT_DATE - INTERVAL '25 days'
                ORDER BY fcode, pdate DESC
            )
            SELECT DISTINCT 
                lp.fcode, 
                lp.ftitle,
                lp.latest_price,
                map.price_30d_ago,
                CASE 
                    WHEN map.price_30d_ago > 0 THEN 
                        ((lp.latest_price - map.price_30d_ago) / map.price_30d_ago * 100)
                    ELSE 0 
                END as return_30d
            FROM latest_prices lp
            LEFT JOIN month_ago_prices map ON lp.fcode = map.fcode
            WHERE ({keyword_conditions})
            AND lp.latest_price IS NOT NULL 
            AND map.price_30d_ago IS NOT NULL
            ORDER BY return_30d DESC
            LIMIT 20
            """
            
            result = self.db.execute_query(query)
            
            funds = {}
            for _, row in result.iterrows():
                try:
                    # Fund details al
                    details = self.db.get_fund_details(row['fcode'])
                    
                    # Volatilite hesapla
                    hist = self.db.get_fund_price_history(row['fcode'], 30)
                    volatility = 0
                    if not hist.empty and len(hist) > 1:
                        prices = hist.set_index('pdate')['price'].sort_index()
                        returns = prices.pct_change().dropna()
                        if len(returns) > 0:
                            volatility = returns.std() * 100
                    
                    funds[row['fcode']] = {
                        'fund_name': row['ftitle'],
                        'return_30d': float(row['return_30d']) if pd.notna(row['return_30d']) else 0,
                        'volatility': volatility,
                        'fund_type': details.get('fund_type', 'N/A') if details else 'N/A'
                    }
                except Exception as e:
                    print(f"Fon detay hatası {row['fcode']}: {e}")
                    continue
            
            return funds
            
        except Exception as e:
            print(f"Makro duyarlı fon arama hatası: {e}")
            import traceback
            traceback.print_exc()
            return {}
        
    def _find_low_volatility_funds(self) -> Dict:
        """Düşük volatiliteli fonları bulur (seçim dönemi için)"""
        try:
            query = """
            WITH price_data AS (
                SELECT 
                    fcode,
                    price,
                    pdate,
                    LAG(price) OVER (PARTITION BY fcode ORDER BY pdate) as prev_price
                FROM tefasfunds
                WHERE pdate >= CURRENT_DATE - INTERVAL '60 days'
                AND price > 0
            ),
            returns_calc AS (
                SELECT 
                    fcode,
                    CASE 
                        WHEN prev_price > 0 THEN (price - prev_price) / prev_price 
                        ELSE 0 
                    END as daily_return
                FROM price_data
                WHERE prev_price IS NOT NULL
            ),
            volatility_calc AS (
                SELECT 
                    fcode,
                    STDDEV(daily_return) * SQRT(252) * 100 as volatility,
                    COUNT(*) as data_points
                FROM returns_calc
                GROUP BY fcode
                HAVING COUNT(*) >= 20
            ),
            latest_prices AS (
                SELECT DISTINCT ON (fcode) 
                    fcode, price as latest_price
                FROM tefasfunds
                WHERE pdate >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY fcode, pdate DESC
            ),
            month_ago_prices AS (
                SELECT DISTINCT ON (fcode) 
                    fcode, price as price_30d_ago
                FROM tefasfunds
                WHERE pdate >= CURRENT_DATE - INTERVAL '35 days'
                AND pdate <= CURRENT_DATE - INTERVAL '25 days'
                ORDER BY fcode, pdate DESC
            )
            SELECT 
                v.fcode, 
                v.volatility,
                CASE 
                    WHEN m.price_30d_ago > 0 THEN 
                        ((l.latest_price - m.price_30d_ago) / m.price_30d_ago * 100)
                    ELSE 0 
                END as return_30d
            FROM volatility_calc v
            JOIN latest_prices l ON v.fcode = l.fcode
            JOIN month_ago_prices m ON v.fcode = m.fcode
            WHERE v.volatility < 5  -- Düşük volatilite
            ORDER BY v.volatility ASC
            LIMIT 15
            """
            
            result = self.db.execute_query(query)
            
            funds = {}
            for _, row in result.iterrows():
                risk_score = min(10, max(1, float(row['volatility']) * 2))  # 1-10 arası risk skoru
                
                funds[row['fcode']] = {
                    'volatility': float(row['volatility']),
                    'return_30d': float(row['return_30d']) if pd.notna(row['return_30d']) else 0,
                    'risk_score': round(risk_score, 1)
                }
            
            return funds
            
        except Exception as e:
            print(f"Düşük volatilite fon arama hatası: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _find_safe_haven_funds(self) -> Dict:
        """Güvenli liman fonları bulur (altın, döviz)"""
        try:
            query = """
            WITH latest_data AS (
                SELECT DISTINCT ON (fcode) 
                    fcode, ftitle, fcapacity, price as latest_price, pdate
                FROM tefasfunds
                WHERE pdate >= CURRENT_DATE - INTERVAL '7 days'
                AND (
                    LOWER(ftitle) LIKE '%altın%' OR
                    LOWER(ftitle) LIKE '%döviz%' OR
                    LOWER(ftitle) LIKE '%dolar%' OR
                    LOWER(ftitle) LIKE '%euro%' OR
                    LOWER(ftitle) LIKE '%usd%' OR
                    LOWER(ftitle) LIKE '%eur%' OR
                    LOWER(ftitle) LIKE '%kıymetli maden%'
                )
                ORDER BY fcode, pdate DESC
            ),
            month_ago_data AS (
                SELECT DISTINCT ON (fcode) 
                    fcode, price as price_30d_ago
                FROM tefasfunds
                WHERE pdate >= CURRENT_DATE - INTERVAL '35 days'
                AND pdate <= CURRENT_DATE - INTERVAL '25 days'
                ORDER BY fcode, pdate DESC
            )
            SELECT 
                l.fcode, 
                l.ftitle, 
                l.fcapacity,
                l.latest_price,
                m.price_30d_ago,
                CASE 
                    WHEN m.price_30d_ago > 0 THEN 
                        ((l.latest_price - m.price_30d_ago) / m.price_30d_ago * 100)
                    ELSE 0 
                END as return_30d
            FROM latest_data l
            LEFT JOIN month_ago_data m ON l.fcode = m.fcode
            WHERE l.fcapacity > 0
            ORDER BY l.fcapacity DESC
            LIMIT 20
            """
            
            result = self.db.execute_query(query)
            
            funds = {}
            for _, row in result.iterrows():
                # Fund type belirleme
                title_lower = row['ftitle'].lower() if row['ftitle'] else ''
                if 'altın' in title_lower:
                    fund_type = 'Altın Fonu'
                elif any(curr in title_lower for curr in ['dolar', 'usd']):
                    fund_type = 'USD Fonu'
                elif any(curr in title_lower for curr in ['euro', 'eur']):
                    fund_type = 'EUR Fonu'
                elif 'döviz' in title_lower:
                    fund_type = 'Döviz Fonu'
                else:
                    fund_type = 'Kıymetli Maden'
                
                funds[row['fcode']] = {
                    'fund_name': row['ftitle'],
                    'fund_type': fund_type,
                    'return_30d': float(row['return_30d']) if pd.notna(row['return_30d']) else 0,
                    'capacity': float(row['fcapacity']) if pd.notna(row['fcapacity']) else 0
                }
            
            return funds
            
        except Exception as e:
            print(f"Güvenli liman fon arama hatası: {e}")
            import traceback
            traceback.print_exc()
            return {}
        
    def _create_macro_portfolio(self) -> Dict:
        """Güncel makro duruma göre portföy önerisi oluşturur"""
        # Basit bir makro skorlama (gerçek uygulamada daha sofistike olabilir)
        portfolio = {
            'Döviz/Altın Fonları': {
                'weight': 30,
                'reason': 'Jeopolitik risk ve enflasyon koruması'
            },
            'Para Piyasası': {
                'weight': 25,
                'reason': 'Yüksek faiz ortamı ve likidite'
            },
            'Kısa Vadeli Tahvil': {
                'weight': 20,
                'reason': 'Düşük risk ve stabil getiri'
            },
            'Defansif Hisse': {
                'weight': 15,
                'reason': 'Uzun vadeli büyüme potansiyeli'
            },
            'Serbest Fon': {
                'weight': 10,
                'reason': 'Aktif yönetim ve esneklik'
            }
        }
        
        return portfolio
    
    def _get_ai_macro_commentary(self, event_type: str, scenario: str, funds: Dict) -> str:
        """AI ile makroekonomik yorum"""
        try:
            if not hasattr(self.coordinator, 'ai_analyzer'):
                return ""
            
            # Dictionary'den ilk 5 fon kodunu al - DÜZELTME
            fund_codes = list(funds.keys())[:5] if funds else []
            
            prompt = f"""
            Türkiye ekonomisinde {event_type} {scenario} durumu için TEFAS fon analizi:
            
            İlgili fonlar: {', '.join(fund_codes)}
            
            Bu makroekonomik değişimin fon performanslarına etkisi ve yatırımcılar için 
            öneriler hakkında kısa bir değerlendirme yap. Maksimum 150 kelime.
            """
            
            response = "\n\n🤖 AI MAKROEKONOMİK YORUM:\n"
            
            if self.coordinator.ai_analyzer.openai_available:
                try:
                    ai_response = self.coordinator.ai_provider.query(
                        prompt,
                        "Sen makroekonomi ve yatırım fonları uzmanısın."
                    )
                    response += f"📱 {ai_response}\n"
                except:
                    pass
            
            return response
            
        except Exception as e:
            print(f"AI makro yorum hatası: {e}")
            return ""
    
    def _get_tcmb_ai_analysis(self) -> str:
        """TCMB kararları için AI analizi"""
        try:
            if not hasattr(self.coordinator, 'ai_analyzer'):
                return ""
            
            prompt = """
            TCMB'nin son dönem para politikası kararları ve bunların TEFAS fonlarına 
            etkisi hakkında kısa bir değerlendirme yap. Faiz kararları, likidite 
            yönetimi ve piyasa beklentilerini değerlendir. Maksimum 200 kelime.
            """
            
            response = "\n\n🤖 AI TCMB ANALİZİ:\n"
            
            # Her iki AI'dan da yorum al
            if self.coordinator.ai_analyzer.openai_available:
                try:
                    ai_response = self.coordinator.ai_provider.query(
                        prompt,
                        "Sen Türkiye ekonomisi ve para politikası uzmanısın."
                    )

                    response += f"\n📱 OpenAI Değerlendirmesi:\n{ai_response}\n"
                except:
                    pass
                        
            return response
            
        except Exception as e:
            print(f"AI TCMB analiz hatası: {e}")
            return ""
        
    @staticmethod
    def get_examples():
        """Makroekonomik analiz örnekleri"""
        return [
            "Faiz artışı fonları nasıl etkiler?",
            "TCMB kararının fon piyasasına etkisi",
            "Fed faiz kararı sonrası strateji",
            "Enflasyon verisi fonları nasıl etkiler?",
            "Seçim döneminde hangi fonlar tercih edilmeli?"
        ]
    
    @staticmethod
    def get_keywords():
        """Makro anahtar kelimeler"""
        return [
            "faiz", "tcmb", "fed", "merkez bankası", "enflasyon",
            "makro", "ekonomik", "seçim", "jeopolitik", "kriz"
        ]
    
    @staticmethod
    def get_patterns():
        """Makro pattern'leri"""
        return [
            {
                'type': 'regex',
                'pattern': r'(faiz|tcmb|fed)\s*(artış|kararı|etkisi)',
                'score': 0.95
            },
            {
                'type': 'contains_all',
                'words': ['ekonomik', 'etki'],
                'score': 0.85
            }
        ]
    
    @staticmethod
    def get_method_patterns():
        """Method mapping"""
        return {
            'analyze_interest_rate_impact': ['faiz', 'interest rate'],
            'analyze_tcmb_decisions': ['tcmb', 'merkez bankası'],
            'analyze_election_impact': ['seçim', 'election'],
            'analyze_geopolitical_impact': ['jeopolitik', 'savaş', 'kriz']
        }