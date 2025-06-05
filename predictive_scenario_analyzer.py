# predictive_scenario_analyzer.py
"""
Prediktif Senaryo Analizi - AI Destekli Gelecek Tahminleri
Mevcut scenario_analysis.py'yi kullanarak gelecek projeksiyonları yapar
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
from typing import Dict, List, Optional, Tuple

class PredictiveScenarioAnalyzer:
    """AI destekli gelecek senaryo tahminleri"""
    
    def __init__(self, coordinator, scenario_analyzer):
        self.coordinator = coordinator
        self.scenario_analyzer = scenario_analyzer
        self.db = coordinator.db
        self.ai_provider = coordinator.ai_provider if hasattr(coordinator, 'ai_provider') else None
        
        # Tahmin periyotları
        self.time_periods = {
            'kısa_vade': {'days': 30, 'label': '1 ay'},
            'orta_vade': {'days': 90, 'label': '3 ay'},
            'uzun_vade': {'days': 180, 'label': '6 ay'}
        }
        
        # Senaryo tahmin parametreleri
        self.scenario_impacts = {
            'enflasyon': {
                'high': {'threshold': 80, 'multiplier': 1.5},
                'medium': {'threshold': 60, 'multiplier': 1.2},
                'low': {'threshold': 40, 'multiplier': 1.0}
            },
            'dolar': {
                'high': {'threshold': 40, 'multiplier': 1.4},
                'medium': {'threshold': 35, 'multiplier': 1.2},
                'low': {'threshold': 30, 'multiplier': 1.0}
            },
            'faiz': {
                'high': {'threshold': 60, 'multiplier': 1.3},
                'medium': {'threshold': 45, 'multiplier': 1.1},
                'low': {'threshold': 30, 'multiplier': 1.0}
            }
        }
    
    def is_predictive_question(self, question):
        """Tahmin sorusu mu kontrolü"""
        question_lower = question.lower()
        
        predictive_keywords = [
            'tahmin', 'predict', 'gelecek', 'sonra', 'olacak',
            'beklenti', 'projeksiyon', 'öngörü', 'forecast',
            'ilerleyen', 'önümüzdeki', 'vadede', 'sonunda',
            '2025', '2026', 'yıl sonu', 'ay sonra', 'hafta sonra'
        ]
        
        return any(keyword in question_lower for keyword in predictive_keywords)
    
    def analyze_predictive_scenario(self, question):
        """Ana tahmin analizi metodu"""
        question_lower = question.lower()
        
        # Senaryo tipini belirle
        scenario_type = self._identify_scenario_type(question_lower)
        
        # Zaman periyodunu belirle
        time_period = self._extract_time_period(question_lower)
        
        # Hedef değeri çıkar
        target_value = self._extract_target_value(question_lower)
        
        print(f"🔮 Prediktif Analiz: {scenario_type} - {time_period['label']} - Hedef: {target_value}")
        
        # Mevcut durumu analiz et
        current_state = self._analyze_current_state(scenario_type)
        
        # Tarihsel trendi analiz et
        historical_trend = self._analyze_historical_trend(scenario_type, time_period['days'])
        
        # AI tahminlerini al
        ai_predictions = self._get_ai_predictions(
            scenario_type, target_value, time_period, 
            current_state, historical_trend, question
        )
        
        # Sonuçları formatla
        return self._format_predictive_results(
            scenario_type, target_value, time_period,
            current_state, historical_trend, ai_predictions
        )
    
    def _identify_scenario_type(self, question_lower):
        """Senaryo tipini belirle"""
        if any(word in question_lower for word in ['enflasyon', 'tüfe', 'üfe']):
            return 'enflasyon'
        elif any(word in question_lower for word in ['dolar', 'euro', 'döviz', 'kur']):
            return 'döviz'
        elif any(word in question_lower for word in ['faiz', 'tcmb', 'para politikası']):
            return 'faiz'
        elif any(word in question_lower for word in ['borsa', 'bist', 'hisse']):
            return 'borsa'
        else:
            return 'genel'
    
    def _extract_time_period(self, question_lower):
        """Zaman periyodunu çıkar"""
        # Spesifik ay/gün belirtimi
        month_match = re.search(r'(\d+)\s*ay', question_lower)
        if month_match:
            months = int(month_match.group(1))
            return {'days': months * 30, 'label': f'{months} ay'}
        
        # Yıl sonu
        if 'yıl sonu' in question_lower or '2025' in question_lower:
            today = datetime.now()
            year_end = datetime(today.year, 12, 31)
            days_to_end = (year_end - today).days
            return {'days': days_to_end, 'label': 'yıl sonu'}
        
        # Kısa/orta/uzun vade
        if any(word in question_lower for word in ['kısa', 'yakın']):
            return self.time_periods['kısa_vade']
        elif any(word in question_lower for word in ['uzun', 'ileri']):
            return self.time_periods['uzun_vade']
        else:
            return self.time_periods['orta_vade']
    
    def _extract_target_value(self, question_lower):
        """Hedef değeri çıkar (örn: enflasyon %80)"""
        # Yüzde değeri
        percent_match = re.search(r'%?\s*(\d+)\s*%?', question_lower)
        if percent_match:
            return float(percent_match.group(1))
        
        # Dolar değeri
        dollar_match = re.search(r'(\d+)\s*tl', question_lower)
        if dollar_match:
            return float(dollar_match.group(1))
        
        return None
    
    def _analyze_current_state(self, scenario_type):
        """Mevcut durumu analiz et"""
        try:
            # SQL düzeltmesi - fund_type yerine protection_category kullan
            query = """
            SELECT 
                AVG(CASE WHEN protection_category = 'PARA_PIYASASI' THEN return_30d END) as money_market_avg,
                AVG(CASE WHEN gold_ratio > 30 THEN return_30d END) as gold_funds_avg,
                AVG(CASE WHEN fx_ratio > 30 THEN return_30d END) as fx_funds_avg,
                AVG(CASE WHEN equity_ratio > 50 THEN return_30d END) as equity_funds_avg,
                AVG(volatility_30d) as avg_volatility,
                COUNT(DISTINCT fcode) as total_funds
            FROM mv_scenario_analysis_funds
            WHERE return_30d IS NOT NULL
            """
            
            result = self.db.execute_query(query)
            
            if not result.empty:
                row = result.iloc[0].to_dict()
                # NULL değerleri kontrol et
                for key in row:
                    if pd.isna(row[key]):
                        if 'avg' in key:
                            row[key] = 0.8 if 'money_market' in key else 2.0
                        elif key == 'total_funds':
                            row[key] = 100
                return row
                
        except Exception as e:
            print(f"Mevcut durum analizi hatası: {e}")
        
        # Varsayılan değerler
        return {
            'money_market_avg': 0.8,
            'gold_funds_avg': 2.5,
            'fx_funds_avg': 1.8,
            'equity_funds_avg': 1.2,
            'avg_volatility': 15.0,
            'total_funds': 1700
        }    
    def _analyze_historical_trend(self, scenario_type, days):
        """Tarihsel trend analizi"""
        try:
            # Senaryo tipine göre ilgili fonları seç
            if scenario_type == 'enflasyon':
                fund_filter = "gold_ratio > 30 OR equity_ratio > 50"
            elif scenario_type == 'döviz':
                fund_filter = "fx_ratio > 30"
            elif scenario_type == 'faiz':
                fund_filter = "bond_ratio > 30 OR money_market_ratio > 50"
            else:
                fund_filter = "1=1"
            
            # Daha basit ve güvenilir sorgu
            query = f"""
            SELECT 
                s.fcode,
                s.return_30d,
                s.return_90d,
                s.volatility_30d
            FROM mv_scenario_analysis_funds s
            WHERE {fund_filter}
            AND s.return_30d IS NOT NULL
            AND s.volatility_30d IS NOT NULL
            AND s.volatility_30d < 100  -- Aşırı değerleri filtrele
            LIMIT 100
            """
            
            result = self.db.execute_query(query)
            
            if not result.empty:
                avg_return = result['return_30d'].mean()
                avg_volatility = result['volatility_30d'].mean()
                fund_count = len(result)
                
                # Mantıklı değer aralığında tut
                avg_volatility = min(avg_volatility, 50.0)  # Max %50 volatilite
                
                return {
                    'avg_return': avg_return,
                    'return_volatility': avg_volatility,
                    'fund_count': fund_count
                }
                    
        except Exception as e:
            print(f"Tarihsel trend hatası: {e}")
        
        return {
            'avg_return': 10.0,
            'return_volatility': 20.0,
            'fund_count': 50
        }

    def _get_ai_predictions(self, scenario_type, target_value, time_period, 
                        current_state, historical_trend, original_question):
        """AI tahminlerini al"""
        
        if not self.ai_provider or not self.ai_provider.is_available():
            return self._generate_rule_based_predictions(
                scenario_type, target_value, time_period, current_state, historical_trend
            )
        
        # Gerçek fonları al
        affected_funds = self._get_scenario_relevant_funds_simple(scenario_type)
        
        # En iyi fonları seç
        top_funds = {
            'gold': [],
            'fx': [],
            'equity': [],
            'money_market': []
        }
        
        for fund in affected_funds[:20]:  # İlk 20 fon
            if fund.get('gold_ratio', 0) > 30:
                top_funds['gold'].append(fund['fcode'])
            elif fund.get('fx_ratio', 0) > 30:
                top_funds['fx'].append(fund['fcode'])
            elif fund.get('equity_ratio', 0) > 50:
                top_funds['equity'].append(fund['fcode'])
            elif fund.get('money_market_ratio', 0) > 50:
                top_funds['money_market'].append(fund['fcode'])
        
        # AI prompt hazırla
        prompt = f"""
        SENARYO TAHMİNİ: {scenario_type.upper()}
        Zaman: {time_period['label']} ({time_period['days']} gün)
        Hedef Değer: {target_value if target_value else 'Belirtilmemiş'}
        
        MEVCUT DURUM:
        - Para Piyasası Fonları Ortalama Getiri: %{current_state['money_market_avg']:.2f}
        - Altın Fonları Ortalama Getiri: %{current_state['gold_funds_avg']:.2f}
        - Döviz Fonları Ortalama Getiri: %{current_state['fx_funds_avg']:.2f}
        - Hisse Fonları Ortalama Getiri: %{current_state['equity_funds_avg']:.2f}
        - Ortalama Volatilite: %{current_state['avg_volatility']:.2f}
        
        GERÇEK FON KODLARI (3 harfli TEFAS kodları):
        - Altın Fonları: {', '.join(top_funds['gold'][:5]) or 'AFO, GEA, AFA, TKF, GAF'}
        - Döviz Fonları: {', '.join(top_funds['fx'][:5]) or 'AKE, IDA, IDE, YAC, TTE'}
        - Hisse Fonları: {', '.join(top_funds['equity'][:5]) or 'TI2, YAS, AKU, TYH, GMR'}
        - Para Piyasası: {', '.join(top_funds['money_market'][:5]) or 'IPB, GEL, AK3, TI3, TPL'}
        
        ÖNEMLİ: Sadece yukarıda verilen GERÇEK FON KODLARINI kullan! 
        Kesinlikle PP1234, AF2345 gibi uydurma kodlar KULLANMA!
        
        GÖREVLER:
        
        1. TAHMİNİ ETKİ ANALİZİ:
        - Her fon kategorisi için beklenen getiri değişimi
        - Yukarıdaki GERÇEK FON KODLARINDAN en çok etkilenecek 5 tanesini seç
        - Her biri için tahmini etki %'si (-100% ile +100% arası)
        
        2. KORUNMA STRATEJİSİ:
        - Yukarıdaki GERÇEK FON KODLARINDAN en iyi koruma sağlayacak 5 tanesini seç
        - Her birinin korunma mekanizması
        
        3. ZAMAN ÇİZELGESİ:
        - İlk etkilerin görüleceği zaman (gün/hafta)
        - Maksimum etkinin oluşacağı zaman
        - Toparlanma süresi tahmini
        
        4. OLASILIK ANALİZİ:
        - Senaryonun gerçekleşme olasılığı (0-100)
        - Ana risk faktörleri
        - İzlenmesi gereken göstergeler
        
        5. AKSİYON PLANI:
        - Hemen yapılması gerekenler
        - {time_period['label']} içinde yapılacaklar
        - Çıkış stratejisi
        
        Yanıtında SADECE verilen gerçek fon kodlarını kullan!
        """
        
        system_prompt = """Sen deneyimli bir TEFAS fon analistisin.
        SADECE sana verilen gerçek fon kodlarını kullanmalısın.
        Asla uydurma fon kodu üretme! Her fon kodu 3 harfli olmalı."""
        
        try:
            ai_response = self.ai_provider.query(prompt, system_prompt)
            return self._parse_ai_predictions(ai_response)
        except Exception as e:
            print(f"AI tahmin hatası: {e}")
            return self._generate_rule_based_predictions(
                scenario_type, target_value, time_period, current_state, historical_trend
            )

    def _parse_ai_predictions(self, ai_response):
        """AI yanıtını parse et"""
        # AI yanıtı zaten formatlanmış gelecek
        return {
            'raw_prediction': ai_response,
            'parsed': True
        }
    
    def _get_scenario_relevant_funds_simple(self, scenario_type):
        """Senaryoya uygun GERÇEK fonları veritabanından çek"""
        try:
            print(f"[DEBUG] {scenario_type} için gerçek fonlar yükleniyor...")
            
            # Önce hangi tablolar/kolonlar mevcut kontrol edelim
            check_tables_query = """
            SELECT table_name, column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name IN ('tefasfunds', 'tefasfunddetails', 'mv_latest_fund_data', 'mv_scenario_analysis_funds')
            AND column_name IN ('fund_type', 'fund_category', 'ftitle', 'fund_name', 'protection_category', 
                            'gold_ratio', 'fx_ratio', 'equity_ratio', 'money_market_ratio')
            ORDER BY table_name, column_name
            """
            
            schema_info = self.db.execute_query(check_tables_query)
            print("[DEBUG] Mevcut kolonlar:")
            for _, row in schema_info.iterrows():
                print(f"  - {row['table_name']}.{row['column_name']}")
            
            # Eğer mv_scenario_analysis_funds varsa önce onu dene
            if 'mv_scenario_analysis_funds' in schema_info['table_name'].values:
                return self._get_funds_from_mv(scenario_type)
            
            # Yoksa basit bir sorgu ile devam et
            return self._get_funds_basic(scenario_type)
            
        except Exception as e:
            print(f"❌ Veritabanı hatası: {e}")
            return []

    def _get_funds_from_mv(self, scenario_type):
        """MV'den kategori bilgisiyle fonları çek"""
        try:
            if scenario_type == 'enflasyon':
                query = """
                SELECT 
                    fcode,
                    fund_name,
                    current_price,
                    gold_ratio,
                    fx_ratio,
                    equity_ratio,
                    money_market_ratio,
                    protection_category,
                    inflation_protection_score
                FROM mv_scenario_analysis_funds
                WHERE (gold_ratio > 20 OR fx_ratio > 20 OR equity_ratio > 40)
                AND current_price IS NOT NULL
                ORDER BY 
                    CASE 
                        WHEN gold_ratio > 50 THEN 1
                        WHEN fx_ratio > 50 THEN 2
                        WHEN equity_ratio > 50 THEN 3
                        ELSE 4
                    END,
                    inflation_protection_score DESC NULLS LAST
                LIMIT 30
                """
            
            elif scenario_type == 'döviz':
                query = """
                SELECT 
                    fcode,
                    fund_name,
                    current_price,
                    fx_ratio,
                    protection_category
                FROM mv_scenario_analysis_funds
                WHERE fx_ratio > 30
                AND current_price IS NOT NULL
                ORDER BY fx_ratio DESC
                LIMIT 20
                """
            
            else:  # Genel
                query = """
                SELECT 
                    fcode,
                    fund_name,
                    current_price,
                    protection_category
                FROM mv_scenario_analysis_funds
                WHERE current_price IS NOT NULL
                ORDER BY investorcount DESC NULLS LAST
                LIMIT 20
                """
            
            result = self.db.execute_query(query)
            
            if result.empty:
                print(f"❌ MV'de {scenario_type} için uygun fon bulunamadı")
                return self._get_funds_basic(scenario_type)
            
            funds = []
            for _, row in result.iterrows():
                fund_data = {
                    'fcode': row['fcode'],
                    'fund_name': row.get('fund_name', ''),
                    'current_price': float(row['current_price']),
                    'category': row.get('protection_category', 'BILINMIYOR')
                }
                
                # Kategoriye göre ek bilgi
                if scenario_type == 'enflasyon':
                    if row.get('gold_ratio', 0) > 50:
                        fund_data['type'] = 'ALTIN'
                        fund_data['ratio'] = row['gold_ratio']
                    elif row.get('fx_ratio', 0) > 50:
                        fund_data['type'] = 'DOVIZ'
                        fund_data['ratio'] = row['fx_ratio']
                    elif row.get('equity_ratio', 0) > 50:
                        fund_data['type'] = 'HISSE'
                        fund_data['ratio'] = row['equity_ratio']
                    else:
                        fund_data['type'] = 'KARMA'
                        fund_data['ratio'] = 0
                
                funds.append(fund_data)
            
            print(f"✅ MV'den {len(funds)} fon yüklendi")
            print(f"[DEBUG] İlk 5 fon: {[(f['fcode'], f.get('type', 'N/A')) for f in funds[:5]]}")
            
            return funds
            
        except Exception as e:
            print(f"❌ MV sorgu hatası: {e}")
            return self._get_funds_basic(scenario_type)

    def _get_funds_basic(self, scenario_type):
        """Basit sorgu - sadece aktif fonları getir"""
        try:
            # En basit hali - sadece son işlem gören fonlar
            query = """
            WITH latest_funds AS (
                SELECT DISTINCT ON (fcode) 
                    fcode, 
                    price,
                    investorcount,
                    pdate
                FROM tefasfunds
                WHERE pdate >= CURRENT_DATE - INTERVAL '7 days'
                AND investorcount > 50  -- En az 50 yatırımcı
                ORDER BY fcode, pdate DESC
            )
            SELECT 
                fcode,
                price as current_price,
                investorcount
            FROM latest_funds
            ORDER BY 
                CASE 
                    WHEN investorcount > 10000 THEN 1  -- Popüler fonlar
                    WHEN investorcount > 1000 THEN 2   -- Orta
                    ELSE 3                              -- Az bilinen
                END,
                fcode
            LIMIT 30
            """
            
            result = self.db.execute_query(query)
            
            if result.empty:
                print("❌ Hiç aktif fon bulunamadı!")
                return []
            
            funds = []
            for _, row in result.iterrows():
                funds.append({
                    'fcode': row['fcode'],
                    'current_price': float(row['current_price']),
                    'investors': int(row['investorcount']),
                    'category': 'BILINMIYOR'  # Kategori bilgisi yok
                })
            
            print(f"✅ Basit sorgudan {len(funds)} fon bulundu")
            print(f"[DEBUG] En popüler 5 fon: {[(f['fcode'], f['investors']) for f in funds[:5]]}")
            
            return funds
            
        except Exception as e:
            print(f"❌ Basit sorgu hatası: {e}")
            return []

    def _generate_rule_based_predictions(self, scenario_type, target_value, 
                                    time_period, current_state, historical_trend):
        """Kural tabanlı tahminler - GERÇEK FONLARLA"""
        
        # Gerçek fonları al
        real_funds = self._get_scenario_relevant_funds_simple(scenario_type)
        
        if not real_funds:
            return {
                'raw_prediction': f"""
    ❌ YETERSIZ VERİ

    {scenario_type.upper()} senaryosu için veritabanında yeterli fon verisi bulunamadı.

    Olası sebepler:
    - Veritabanı bağlantı problemi
    - Güncel fon verisi yok
    - Sorgu hatası

    Lütfen daha sonra tekrar deneyin.
    """,
                'parsed': False
            }
        
        predictions = {
            'impact_analysis': {},
            'protection_funds': [],
            'timeline': {},
            'probability': 0,
            'action_plan': []
        }
        
        # Senaryo tipine göre tahminler
        if scenario_type == 'enflasyon':
            impact_multiplier = 1.5 if target_value and target_value > 80 else 1.2
            
            predictions['impact_analysis'] = {
                'para_piyasası': -10 * impact_multiplier,
                'tahvil': -8 * impact_multiplier,
                'altın': 25 * impact_multiplier,
                'hisse': 15 * impact_multiplier,
                'döviz': 20 * impact_multiplier
            }
            
            # Fonları kategorize et (eğer MV'den geldiyse type bilgisi var)
            gold_funds = [f for f in real_funds if f.get('type') == 'ALTIN']
            fx_funds = [f for f in real_funds if f.get('type') == 'DOVIZ']
            equity_funds = [f for f in real_funds if f.get('type') == 'HISSE']
            
            # Eğer kategorize edilmemişse, en popülerleri al
            if not gold_funds and not fx_funds and not equity_funds:
                # Popülerlik sırasına göre dağıt
                total = len(real_funds)
                gold_funds = real_funds[:total//3]
                fx_funds = real_funds[total//3:2*total//3]
                equity_funds = real_funds[2*total//3:]
            
            # Koruma fonları öner
            for fund in gold_funds[:2]:
                predictions['protection_funds'].append(
                    (fund['fcode'], f"Yüksek yatırımcılı fon ({fund.get('investors', 'N/A')} kişi)")
                )
            
            for fund in fx_funds[:2]:
                predictions['protection_funds'].append(
                    (fund['fcode'], f"Popüler fon - {fund.get('investors', 'N/A')} yatırımcı")
                )
            
            if equity_funds:
                predictions['protection_funds'].append(
                    (equity_funds[0]['fcode'], f"Aktif işlem gören fon")
                )
            
            predictions['probability'] = 70 if target_value and target_value > 70 else 50
        
        # Diğer senaryolar benzer şekilde...
        
        # Zaman çizelgesi
        predictions['timeline'] = {
            'ilk_etki': f"{max(time_period['days'] // 10, 7)} gün",
            'maksimum_etki': f"{time_period['days'] // 2} gün",
            'toparlanma': f"{time_period['days'] * 2} gün"
        }
        
        # Aksiyon planı
        predictions['action_plan'] = [
            'Portföyü gözden geçir',
            f"Listelenen {len(predictions['protection_funds'])} fondan uygun olanları araştır",
            'Fon detaylarını incele (prospektüs, geçmiş performans)',
            'Risk yönetimine dikkat et'
        ]
        
        return {
            'raw_prediction': self._format_rule_based_predictions(predictions, scenario_type, time_period),
            'parsed': False
        }
    def _format_rule_based_predictions(self, predictions, scenario_type, time_period):
        """Kural tabanlı tahminleri formatla"""
        
        response = f"📊 KURAL TABANLI TAHMİN ({scenario_type.upper()})\n\n"
        
        response += f"1️⃣ TAHMİNİ ETKİ ANALİZİ ({time_period['label']}):\n"
        for category, impact in predictions['impact_analysis'].items():
            icon = "📈" if impact > 0 else "📉"
            response += f"   {icon} {category.title()}: %{impact:+.1f}\n"
        
        response += f"\n2️⃣ KORUNMA SAĞLAYACAK FONLAR:\n"
        for i, (fund, reason) in enumerate(predictions['protection_funds'][:5], 1):
            response += f"   {i}. {fund}: {reason}\n"
        
        # Eğer gerçek fon bulunamadıysa uyarı ekle
        if len(predictions['protection_funds']) < 3:
            response += f"\n   ⚠️ Not: Yeterli sayıda uygun fon bulunamadı.\n"
            response += f"   💡 Öneri: Altın (AFO, GEA), Döviz (AKE, IDA) fonlarını araştırın.\n"
        
        response += f"\n3️⃣ ZAMAN ÇİZELGESİ:\n"
        response += f"   🕐 İlk etki: {predictions['timeline']['ilk_etki']}\n"
        response += f"   🎯 Maksimum etki: {predictions['timeline']['maksimum_etki']}\n"
        response += f"   🔄 Toparlanma: {predictions['timeline']['toparlanma']}\n"
        
        response += f"\n4️⃣ OLASILIK ANALİZİ:\n"
        response += f"   📊 Gerçekleşme olasılığı: %{predictions['probability']}\n"
        response += f"   ⚠️ Risk faktörleri: Küresel gelişmeler, TCMB kararları\n"
        response += f"   👁️ İzlenecek: TÜFE, Dolar/TL, Altın fiyatları\n"
        
        response += f"\n5️⃣ AKSİYON PLANI:\n"
        for i, action in enumerate(predictions['action_plan'], 1):
            response += f"   {i}. {action}\n"
        
        return response    
    def _format_predictive_results(self, scenario_type, target_value, time_period,
                                  current_state, historical_trend, ai_predictions):
        """Tahmin sonuçlarını formatla"""
        
        response = f"\n🔮 PREDİKTİF SENARYO ANALİZİ\n"
        response += f"{'='*60}\n\n"
        
        response += f"📊 SENARYO: {scenario_type.upper()}"
        if target_value:
            response += f" - HEDEF: {target_value}"
        response += f"\n📅 TAHMİN PERİYODU: {time_period['label']} ({time_period['days']} gün)\n"
        response += f"🕐 Analiz Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        # Mevcut durum özeti
        response += f"📈 MEVCUT DURUM:\n"
        response += f"   • Ortalama Volatilite: %{current_state['avg_volatility']:.2f}\n"
        response += f"   • Para Piyasası Getirisi: %{current_state['money_market_avg']:.2f}\n"
        response += f"   • Altın Fonları Getirisi: %{current_state['gold_funds_avg']:.2f}\n"
        response += f"   • Döviz Fonları Getirisi: %{current_state['fx_funds_avg']:.2f}\n\n"
        
        # Tarihsel trend
        response += f"📊 TARİHSEL TREND ({time_period['days']} günlük):\n"
        response += f"   • Ortalama Getiri: %{historical_trend['avg_return']:.2f}\n"
        response += f"   • Volatilite: %{historical_trend['return_volatility']:.2f}\n"
        response += f"   • Veri Sayısı: {historical_trend['fund_count']} fon\n\n"
        
        # AI tahminleri
        response += f"🤖 AI TAHMİNLERİ:\n"
        response += f"{'='*60}\n"
        response += ai_predictions['raw_prediction']
        response += f"\n{'='*60}\n"
        
        # Risk uyarıları
        response += f"\n⚠️ ÖNEMLİ UYARILAR:\n"
        response += f"   • Bu tahminler tarihsel verilere ve AI analizine dayanır\n"
        response += f"   • Piyasa koşulları ani değişebilir\n"
        response += f"   • Kesin sonuç garantisi verilmez\n"
        response += f"   • Yatırım kararlarında profesyonel destek alın\n"
        response += f"   • Portföyünüzü çeşitlendirin\n"
        
        return response
    
    @staticmethod
    def get_examples():
        """Prediktif analiz örnekleri"""
        return [
            "Enflasyon %80 olursa 6 ay sonra fonlar nasıl etkilenir?",
            "Dolar 40 TL olursa gelecek 3 ay tahmini?",
            "Faiz %60'a çıkarsa yıl sonu fon performansları?",
            "2025 sonunda hangi fonlar en iyi performans gösterir?",
            "Önümüzdeki 3 ayda altın fonları tahmini?",
            "Kısa vadede döviz fonları nasıl performans gösterir?"
        ]
    
    @staticmethod
    def get_keywords():
        """Prediktif analiz anahtar kelimeleri"""
        return [
            "tahmin", "predict", "gelecek", "sonra", "olacak",
            "beklenti", "projeksiyon", "öngörü", "forecast",
            "vadede", "2025", "2026", "yıl sonu"
        ]
    
    @staticmethod
    def get_patterns():
        """Prediktif analiz pattern'leri"""
        return [
            {
                'type': 'regex',
                'pattern': r'(\d+\s*ay|yıl)\s*(sonra|sonunda)',
                'score': 0.95
            },
            {
                'type': 'contains_all',
                'words': ['tahmin', 'fon'],
                'score': 0.90
            },
            {
                'type': 'regex',
                'pattern': r'gelecek\s*\d+\s*(ay|gün|hafta)',
                'score': 0.95
            }
        ]