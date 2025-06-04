"""
Kişisel Duruma Özel Fon Analiz Sistemi
Emeklilik, eğitim, ev alma gibi hedeflere özel portföy önerileri
"""
import re
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
class PersonalFinanceAnalyzer:
    """Kişisel finans hedeflerine özel fon analiz sistemi"""
    def __init__(self, coordinator, active_funds):
        self.coordinator = coordinator
        self.active_funds = active_funds
        self.db = coordinator.db
        
    def is_personal_finance_question(self, question):
        """Kişisel finans sorusu mu kontrol et"""
        question_lower = question.lower()
        
        personal_keywords = [
            'emeklilik', 'emekliliğe', 'retirement',
            'üniversite', 'eğitim', 'okul', 'burs',
            'ev almak', 'ev için', 'gayrimenkul', 'konut',
            'çocuk', 'bebek', 'evlilik', 'düğün',
            'birikim', 'tasarruf', 'yatırım planı',
            'yıl kala', 'yıllık plan', 'aylık birikim'
        ]
        
        return any(keyword in question_lower for keyword in personal_keywords)

    def analyze_personal_finance_question(self, question):
        """Kişisel finans sorusunu analiz et ve yanıtla"""
        question_lower = question.lower()
        
        # Emeklilik soruları
        if any(word in question_lower for word in ['emeklilik', 'emekliliğe', 'retirement']):
            return self._handle_retirement_planning(question)
        
        # Eğitim soruları
        elif any(word in question_lower for word in ['üniversite', 'eğitim', 'okul', 'burs']):
            return self._handle_education_planning(question)
        
        # Ev alma soruları
        elif any(word in question_lower for word in ['ev almak', 'ev için', 'gayrimenkul', 'konut']):
            return self._handle_home_purchase_planning(question)
        
        # Çocuk/bebek soruları
        elif any(word in question_lower for word in ['çocuk', 'bebek']):
            return self._handle_child_planning(question)
        
        # Genel birikim soruları
        else:
            return self._handle_general_savings_planning(question)

    def _handle_retirement_planning(self, question):
        """Emeklilik planlaması"""
        print("👴 Emeklilik planlaması analizi yapılıyor...")
        
        # Süre tespiti
        years_match = re.search(r'(\d+)\s*yıl', question.lower())
        years_to_retirement = int(years_match.group(1)) if years_match else 10
        
        response = f"\n👴 EMEKLİLİK PORTFÖY ÖNERİSİ ({years_to_retirement} YIL)\n"
        response += f"{'='*55}\n\n"
        
        # Risk profili belirleme
        if years_to_retirement >= 20:
            risk_profile = "agresif"
            response += f"⚡ RİSK PROFİLİ: YÜKSEK (20+ yıl var)\n"
        elif years_to_retirement >= 10:
            risk_profile = "dengeli"
            response += f"⚖️ RİSK PROFİLİ: DENGELİ (10-20 yıl)\n"
        elif years_to_retirement >= 5:
            risk_profile = "muhafazakar"
            response += f"🛡️ RİSK PROFİLİ: MUHAFAZAKAR (5-10 yıl)\n"
        else:
            risk_profile = "çok muhafazakar"
            response += f"🛡️🛡️ RİSK PROFİLİ: ÇOK MUHAFAZAKAR (<5 yıl)\n"
        
        response += f"\n📊 PORTFÖY DAĞILIMI ÖNERİSİ:\n"
        
        # Portföy dağılımı
        if risk_profile == "agresif":
            distribution = {
                "Hisse Senedi Fonları": 70,
                "Borçlanma Araçları": 20,
                "Para Piyasası": 10
            }
        elif risk_profile == "dengeli":
            distribution = {
                "Hisse Senedi Fonları": 50,
                "Borçlanma Araçları": 35,
                "Para Piyasası": 15
            }
        elif risk_profile == "muhafazakar":
            distribution = {
                "Hisse Senedi Fonları": 30,
                "Borçlanma Araçları": 50,
                "Para Piyasası": 20
            }
        else:  # çok muhafazakar
            distribution = {
                "Hisse Senedi Fonları": 10,
                "Borçlanma Araçları": 40,
                "Para Piyasası": 50
            }
        
        for asset_type, percentage in distribution.items():
            response += f"   • {asset_type}: %{percentage}\n"
        
        # SQL ile uygun fonları bul
        response += f"\n🎯 ÖNERİLEN FONLAR:\n\n"
        
        # Hisse senedi fonları
        if distribution["Hisse Senedi Fonları"] > 0:
            equity_funds = self._get_funds_by_type_sql("stock", distribution["Hisse Senedi Fonları"])
            response += f"📈 HİSSE SENEDİ FONLARI (%{distribution['Hisse Senedi Fonları']}):\n"
            for fund in equity_funds[:3]:
                response += f"   • {fund['fcode']}: {fund['fund_name'][:40]}...\n"
                response += f"     Getiri: %{fund['performance']:.2f}, Risk: %{fund['volatility']:.2f}\n"
            response += "\n"
        
        # Borçlanma araçları fonları
        if distribution["Borçlanma Araçları"] > 0:
            bond_funds = self._get_funds_by_type_sql("governmentbond", distribution["Borçlanma Araçları"])
            response += f"📊 BORÇLANMA ARAÇLARI FONLARI (%{distribution['Borçlanma Araçları']}):\n"
            for fund in bond_funds[:3]:
                response += f"   • {fund['fcode']}: {fund['fund_name'][:40]}...\n"
                response += f"     Getiri: %{fund['performance']:.2f}, Risk: %{fund['volatility']:.2f}\n"
            response += "\n"
        
        # Para piyasası fonları
        if distribution["Para Piyasası"] > 0:
            money_market_funds = self._get_low_risk_funds_sql(distribution["Para Piyasası"])
            response += f"💰 PARA PİYASASI FONLARI (%{distribution['Para Piyasası']}):\n"
            for fund in money_market_funds[:3]:
                response += f"   • {fund['fcode']}: {fund['fund_name'][:40]}...\n"
                response += f"     Getiri: %{fund['performance']:.2f}, Risk: %{fund['volatility']:.2f}\n"
        
        # Tavsiyeler
        response += f"\n💡 EMEKLİLİK TAVSİYELERİ:\n"
        response += f"   • Aylık düzenli yatırım yapın (DCA stratejisi)\n"
        response += f"   • Yılda bir portföyü gözden geçirin\n"
        response += f"   • Emekliliğe yaklaştıkça riski azaltın\n"
        response += f"   • Enflasyonu hesaba katın (TÜFE+%2-3)\n"
        response += f"   • BES avantajlarını değerlendirin\n"
        
        # Hesaplama örneği
        monthly_savings = 5000  # Örnek
        expected_return = 0.25 if risk_profile == "agresif" else 0.15
        months = years_to_retirement * 12
        future_value = monthly_savings * (((1 + expected_return/12)**months - 1) / (expected_return/12))
        
        response += f"\n📊 ÖRNEK HESAPLAMA:\n"
        response += f"   Aylık {monthly_savings:,.0f} TL birikim\n"
        response += f"   Beklenen yıllık getiri: %{expected_return*100:.0f}\n"
        response += f"   {years_to_retirement} yıl sonunda tahmini birikim: {future_value:,.0f} TL\n"
        
        return response

    def _handle_education_planning(self, question):
        """Eğitim planlaması"""
        print("🎓 Eğitim birikim planı analizi yapılıyor...")
        
        response = f"\n🎓 EĞİTİM BİRİKİM PORTFÖYÜ\n"
        response += f"{'='*40}\n\n"
        
        # Üniversite mi, genel eğitim mi tespit et
        is_university = 'üniversite' in question.lower()
        
        if is_university:
            response += f"🎯 HEDEF: ÜNİVERSİTE EĞİTİMİ\n"
            response += f"📅 Tahmini süre: 10-18 yıl\n\n"
            
            # Uzun vadeli dengeli portföy
            distribution = {
                "Hisse Senedi Fonları": 40,
                "Borçlanma Araçları": 40,
                "Altın/Döviz Fonları": 20
            }
        else:
            response += f"🎯 HEDEF: GENEL EĞİTİM BİRİKİMİ\n"
            response += f"📅 Esnek planlama\n\n"
            
            distribution = {
                "Hisse Senedi Fonları": 35,
                "Borçlanma Araçları": 45,
                "Para Piyasası": 20
            }
        
        response += f"📊 ÖNERİLEN DAĞILIM:\n"
        for asset_type, percentage in distribution.items():
            response += f"   • {asset_type}: %{percentage}\n"
        
        # Uygun fonları bul
        response += f"\n🎯 EĞİTİM İÇİN ÖNERİLEN FONLAR:\n\n"
        
        # Dengeli ve güvenli fonları öner
        safe_funds = self._get_balanced_funds_for_education()
        
        for i, fund in enumerate(safe_funds[:5], 1):
            response += f"{i}. {fund['fcode']}\n"
            response += f"   📝 {fund['fund_name'][:45]}...\n"
            response += f"   📊 1 Yıllık Getiri: %{fund['performance']:.2f}\n"
            response += f"   📉 Risk (Volatilite): %{fund['volatility']:.2f}\n"
            response += f"   👥 Yatırımcı Sayısı: {fund['investors']:,}\n\n"
        
        # Eğitim maliyeti hesaplama
        current_year = datetime.now().year
        university_start_year = current_year + 10  # Örnek
        
        response += f"💰 EĞİTİM MALİYETİ TAHMİNİ ({university_start_year}):\n"
        response += f"   • Devlet Üniversitesi: 200,000 - 400,000 TL\n"
        response += f"   • Özel Üniversite: 800,000 - 2,000,000 TL\n"
        response += f"   • Yurtdışı: 2,000,000 - 5,000,000 TL\n\n"
        
        # Birikim önerisi
        monthly_target = 3000  # Örnek
        years_to_save = 10
        expected_return = 0.20  # %20 yıllık
        
        future_value = self._calculate_future_value(monthly_target, expected_return, years_to_save)
        
        response += f"📈 BİRİKİM PLANI:\n"
        response += f"   Aylık hedef: {monthly_target:,.0f} TL\n"
        response += f"   Süre: {years_to_save} yıl\n"
        response += f"   Beklenen getiri: %{expected_return*100:.0f}\n"
        response += f"   Tahmini birikim: {future_value:,.0f} TL\n\n"
        
        response += f"💡 EĞİTİM BİRİKİMİ TAVSİYELERİ:\n"
        response += f"   • Çocuk hesabı açın (vergi avantajı)\n"
        response += f"   • Düzenli aylık yatırım yapın\n"
        response += f"   • Enflasyona karşı korumalı fonları tercih edin\n"
        response += f"   • Devlet desteklerini araştırın\n"
        response += f"   • Alternatif gelir kaynakları oluşturun\n"
        
        return response

    def _handle_home_purchase_planning(self, question):
        """Ev alma planlaması"""
        print("🏠 Ev alma birikim planı analizi yapılıyor...")
        
        # Süre tespiti
        years_match = re.search(r'(\d+)\s*yıl', question.lower())
        years_to_save = int(years_match.group(1)) if years_match else 2
        
        response = f"\n🏠 EV ALMA BİRİKİM PLANI ({years_to_save} YIL)\n"
        response += f"{'='*45}\n\n"
        
        # Kısa vadeli hedef - düşük riskli portföy
        response += f"⏰ KISA VADELİ HEDEF - GÜVENLİ PORTFÖY\n\n"
        
        # Portföy önerisi
        if years_to_save <= 1:
            distribution = {
                "Para Piyasası": 70,
                "Kısa Vadeli Tahvil": 20,
                "Likit Fonlar": 10
            }
        elif years_to_save <= 3:
            distribution = {
                "Para Piyasası": 50,
                "Borçlanma Araçları": 30,
                "Döviz/Altın": 20
            }
        else:
            distribution = {
                "Borçlanma Araçları": 40,
                "Para Piyasası": 30,
                "Hisse Senedi": 20,
                "Döviz/Altın": 10
            }
        
        response += f"📊 ÖNERİLEN PORTFÖY DAĞILIMI:\n"
        for asset_type, percentage in distribution.items():
            response += f"   • {asset_type}: %{percentage}\n"
        
        # Güvenli fonları bul
        response += f"\n🛡️ EV İÇİN GÜVENLİ FONLAR:\n\n"
        
        # SQL ile düşük riskli fonları getir
        safe_funds = self._get_home_purchase_funds(years_to_save)
        
        for i, fund in enumerate(safe_funds[:5], 1):
            response += f"{i}. {fund['fcode']}\n"
            response += f"   📝 {fund['fund_name'][:45]}...\n"
            response += f"   💰 Yıllık Getiri: %{fund['performance']:.2f}\n"
            response += f"   🛡️ Risk: %{fund['volatility']:.2f} (Düşük)\n"
            response += f"   💲 Güncel Fiyat: {fund['current_price']:.4f} TL\n\n"
        
        # Ev fiyatları ve hedef hesaplama
        response += f"🏠 GÜNCEL EV FİYATLARI (2025 TAHMİNİ):\n"
        response += f"   • İstanbul (Ortalama): 4,000,000 - 8,000,000 TL\n"
        response += f"   • Ankara: 2,500,000 - 5,000,000 TL\n"
        response += f"   • İzmir: 2,000,000 - 4,500,000 TL\n"
        response += f"   • Anadolu Şehirleri: 1,000,000 - 2,500,000 TL\n\n"
        
        # Birikim hesaplama
        target_home_price = 3000000  # 3 milyon TL örnek
        down_payment = target_home_price * 0.25  # %25 peşinat
        
        monthly_required = down_payment / (years_to_save * 12)
        
        response += f"💰 BİRİKİM HESAPLAMASI:\n"
        response += f"   Hedef ev fiyatı: {target_home_price:,.0f} TL\n"
        response += f"   Peşinat (%25): {down_payment:,.0f} TL\n"
        response += f"   Aylık birikim: {monthly_required:,.0f} TL\n\n"
        
        # Alternatif senaryolar
        response += f"📊 ALTERNATİF SENARYOLAR:\n"
        
        scenarios = [
            (5000, 0.15),   # 5000 TL, %15 getiri
            (7500, 0.15),   # 7500 TL, %15 getiri
            (10000, 0.15),  # 10000 TL, %15 getiri
        ]
        
        for monthly, return_rate in scenarios:
            fv = self._calculate_future_value(monthly, return_rate, years_to_save)
            response += f"   • Aylık {monthly:,} TL → {years_to_save} yıl sonra: {fv:,.0f} TL\n"
        
        response += f"\n💡 EV ALMA TAVSİYELERİ:\n"
        response += f"   • Enflasyondan korunmak için döviz/altın fonları ekleyin\n"
        response += f"   • Kısa vadede likidite önemli - para piyasası fonları\n"
        response += f"   • Konut kredisi faizlerini takip edin\n"
        response += f"   • Devlet desteklerini araştırın\n"
        response += f"   • Acele etmeyin, piyasayı takip edin\n"
        
        return response

    def _handle_child_planning(self, question):
        """Çocuk için birikim planlaması"""
        print("👶 Çocuk birikim planı analizi yapılıyor...")
        
        response = f"\n👶 ÇOCUK İÇİN BİRİKİM PORTFÖYÜ\n"
        response += f"{'='*40}\n\n"
        
        response += f"🎯 UZUN VADELİ BİRİKİM PLANI (18 YIL)\n\n"
        
        # Çocuk yaşına göre portföy
        distribution = {
            "0-6 yaş": {"Hisse": 60, "Tahvil": 30, "Altın": 10},
            "7-12 yaş": {"Hisse": 50, "Tahvil": 35, "Altın": 15},
            "13-18 yaş": {"Hisse": 30, "Tahvil": 50, "Para Piyasası": 20}
        }
        
        response += f"📊 YAŞ GRUPLARINA GÖRE PORTFÖY:\n"
        for age_group, dist in distribution.items():
            response += f"\n{age_group}:\n"
            for asset, pct in dist.items():
                response += f"   • {asset}: %{pct}\n"
        
        # Çocuk dostu fonlar
        response += f"\n🌟 ÇOCUK BİRİKİMİ İÇİN ÖNERİLEN FONLAR:\n\n"
        
        # Uzun vadeli büyüme fonları
        growth_funds = self._get_child_savings_funds()
        
        for i, fund in enumerate(growth_funds[:5], 1):
            response += f"{i}. {fund['fcode']}\n"
            response += f"   📝 {fund['fund_name'][:45]}...\n"
            response += f"   📈 5 Yıllık Ort. Getiri: %{fund['performance']:.2f}\n"
            response += f"   🎯 Uzun Vade Skoru: {fund['score']}/100\n\n"
        
        # Çocuk giderleri ve hedefler
        response += f"💰 ÇOCUK İÇİN FİNANSAL HEDEFLER:\n"
        response += f"   • Üniversite eğitimi: 1,000,000 - 3,000,000 TL\n"
        response += f"   • Yurtdışı eğitimi: 3,000,000 - 5,000,000 TL\n"
        response += f"   • İlk ev yardımı: 500,000 - 1,000,000 TL\n"
        response += f"   • Düğün/Başlangıç: 300,000 - 500,000 TL\n\n"
        
        # Aylık birikim örnekleri
        response += f"📈 AYLIK BİRİKİM ÖRNEKLERİ (18 yıl, %20 getiri):\n"
        
        monthly_amounts = [500, 1000, 2000, 3000, 5000]
        for amount in monthly_amounts:
            fv = self._calculate_future_value(amount, 0.20, 18)
            response += f"   • {amount:,} TL/ay → 18 yıl sonra: {fv:,.0f} TL\n"
        
        response += f"\n🎁 ÇOCUK HESABI AVANTAJLARI:\n"
        response += f"   • Vergi muafiyeti (belirli limitlerde)\n"
        response += f"   • Düşük komisyon oranları\n"
        response += f"   • Otomatik birikim imkanı\n"
        response += f"   • Eğitim teşvikleri\n\n"
        
        response += f"💡 ÇOCUK BİRİKİMİ TAVSİYELERİ:\n"
        response += f"   • Doğumda hemen başlayın\n"
        response += f"   • Düzenli aylık yatırım yapın\n"
        response += f"   • Bayram harçlıklarını değerlendirin\n"
        response += f"   • Çocuğa finansal okuryazarlık öğretin\n"
        response += f"   • Uzun vadeli düşünün, panik yapmayın\n"
        
        return response

    def _handle_general_savings_planning(self, question):
        """Genel birikim planlaması"""
        print("💰 Genel birikim planı analizi yapılıyor...")
        
        response = f"\n💰 GENEL BİRİKİM VE YATIRIM PLANI\n"
        response += f"{'='*45}\n\n"
        
        # Genel tavsiyeler
        response += f"📊 TEMEL YATIRIM PRENSİPLERİ:\n\n"
        
        response += f"1️⃣ ACİL FON (3-6 aylık gider):\n"
        response += f"   • Para piyasası fonları\n"
        response += f"   • Likit fonlar\n"
        response += f"   • Kısa vadeli mevduat\n\n"
        
        response += f"2️⃣ KISA VADE (1-3 yıl):\n"
        response += f"   • %60 Para piyasası\n"
        response += f"   • %30 Borçlanma araçları\n"
        response += f"   • %10 Altın/Döviz\n\n"
        
        response += f"3️⃣ ORTA VADE (3-5 yıl):\n"
        response += f"   • %40 Borçlanma araçları\n"
        response += f"   • %35 Hisse senedi\n"
        response += f"   • %25 Alternatif yatırımlar\n\n"
        
        response += f"4️⃣ UZUN VADE (5+ yıl):\n"
        response += f"   • %50 Hisse senedi\n"
        response += f"   • %30 Borçlanma araçları\n"
        response += f"   • %20 Alternatif yatırımlar\n\n"
        
        # Genel amaçlı fonlar
        response += f"🎯 ÇOK AMAÇLI ÖNERİLEN FONLAR:\n\n"
        
        versatile_funds = self._get_versatile_funds()
        
        for i, fund in enumerate(versatile_funds[:5], 1):
            response += f"{i}. {fund['fcode']}\n"
            response += f"   📝 {fund['fund_name'][:45]}...\n"
            response += f"   ⚖️ Dengeli Yapı\n"
            response += f"   📊 Getiri/Risk: {fund['sharpe']:.2f}\n\n"
        
        response += f"💡 GENEL TAVSİYELER:\n"
        response += f"   • Gelirin %20'sini biriktirin\n"
        response += f"   • Çeşitlendirme yapın\n"
        response += f"   • Düzenli gözden geçirin\n"
        response += f"   • Duygusal karar vermeyin\n"
        response += f"   • Uzun vadeli düşünün\n"
        
        return response

    # Yardımcı metodlar
    def _get_funds_by_type_sql(self, fund_type, target_percentage):
        """SQL ile belirli tipteki fonları getir - DÜZELTILMIŞ"""
        try:
            query = f"""
            SELECT 
                pm.fcode,
                lf.ftitle as fund_name,
                pm.annual_return as performance,
                pm.annual_volatility * 100 as volatility,
                lf.investorcount as investors,
                pm.current_price,
                COALESCE(fd.{fund_type}, 0) as allocation
            FROM mv_fund_performance_metrics pm
            JOIN mv_latest_fund_data lf ON pm.fcode = lf.fcode
            LEFT JOIN tefasfunddetails fd ON pm.fcode = fd.fcode
            WHERE COALESCE(fd.{fund_type}, 0) > 50
            ORDER BY pm.annual_return DESC
            LIMIT 10
            """            
            result = self.db.execute_query(query)
            return result.to_dict('records') if not result.empty else []
            
        except Exception as e:
            print(f"SQL hatası: {e}")
            # Alternatif basit sorgu
            try:
                simple_query = f"""
                SELECT DISTINCT f.fcode, 
                    f.ftitle as fund_name,
                    f.price as current_price,
                    f.investorcount as investors,
                    0 as performance,
                    0 as volatility
                FROM tefasfunds f
                WHERE f.pdate >= CURRENT_DATE - INTERVAL '7 days'
                AND f.investorcount > 100
                AND f.price > 0
                ORDER BY f.investorcount DESC
                LIMIT 10
                """
                result = self.db.execute_query(simple_query)
                return result.to_dict('records') if not result.empty else []
            except:
                return []

    def _get_low_risk_funds_sql(self, target_percentage):
        """Düşük riskli fonları getir - DÜZELTILMIŞ"""
        try:
            query = """
            WITH fund_risk AS (
                SELECT fcode, 
                    MAX(ftitle) as fund_name,
                    CASE
                        WHEN MIN(price) > 0 THEN (MAX(price) - MIN(price)) / MIN(price) * 100
                        ELSE 0
                    END as performance,
                    CASE
                        WHEN AVG(price) > 0 THEN STDDEV(price) / AVG(price) * 100
                        ELSE 0
                    END as volatility,
                    MAX(price) as current_price,
                    MAX(investorcount) as investors
                FROM tefasfunds
                WHERE pdate >= CURRENT_DATE - INTERVAL '90 days'
                AND investorcount > 100
                AND price > 0
                GROUP BY fcode
                HAVING COUNT(*) >= 60
                AND MIN(price) > 0
            )
            SELECT * FROM fund_risk
            WHERE volatility < 5 AND volatility > 0  -- Düşük volatilite
            ORDER BY performance DESC
            LIMIT 10
            """
            
            result = self.db.execute_query(query)
            return result.to_dict('records') if not result.empty else []
            
        except Exception as e:
            print(f"SQL hatası: {e}")
            return []

    def _get_balanced_funds_for_education(self):
        """Eğitim için dengeli fonları getir - DÜZELTILMIŞ"""
        try:
            query = """
            WITH balanced_funds AS (
                SELECT f.fcode, 
                    MAX(f.ftitle) as fund_name,
                    CASE
                        WHEN MIN(f.price) > 0 THEN (MAX(f.price) - MIN(f.price)) / MIN(f.price) * 100
                        ELSE 0
                    END as performance,
                    CASE
                        WHEN AVG(f.price) > 0 THEN STDDEV(f.price) / AVG(f.price) * 100
                        ELSE 0
                    END as volatility,
                    MAX(f.investorcount) as investors,
                    COUNT(DISTINCT f.pdate) as trading_days
                FROM tefasfunds f
                WHERE f.pdate >= CURRENT_DATE - INTERVAL '365 days'
                AND f.investorcount > 200
                AND f.price > 0
                GROUP BY f.fcode
                HAVING COUNT(*) >= 200
                AND MIN(f.price) > 0
                AND AVG(f.price) > 0
            )
            SELECT * FROM balanced_funds
            WHERE volatility > 0 AND volatility < 15  -- Orta risk
            AND performance > 10  -- Minimum %10 getiri
            ORDER BY 
                CASE 
                    WHEN volatility > 0 THEN performance / volatility 
                    ELSE 0 
                END DESC
            LIMIT 10
            """
            
            result = self.db.execute_query(query)
            return result.to_dict('records') if not result.empty else []
            
        except Exception as e:
            print(f"SQL hatası: {e}")
            return []

    def _get_home_purchase_funds(self, years_to_save):
        """Ev alımı için uygun fonları getir - DÜZELTILMIŞ"""
        max_volatility = 10 if years_to_save <= 2 else 15
        
        try:
            query = f"""
            WITH stable_funds AS (
                SELECT f.fcode, 
                    MAX(f.ftitle) as fund_name,
                    CASE
                        WHEN MIN(f.price) > 0 THEN (MAX(f.price) - MIN(f.price)) / MIN(f.price) * 100
                        ELSE 0
                    END as performance,
                    CASE
                        WHEN AVG(f.price) > 0 THEN STDDEV(f.price) / AVG(f.price) * 100
                        ELSE 0
                    END as volatility,
                    MAX(f.price) as current_price,
                    MAX(f.investorcount) as investors
                FROM tefasfunds f
                WHERE f.pdate >= CURRENT_DATE - INTERVAL '180 days'
                AND f.investorcount > 300
                AND f.price > 0
                GROUP BY f.fcode
                HAVING MIN(f.price) > 0
                AND AVG(f.price) > 0
            )
            SELECT * FROM stable_funds
            WHERE volatility > 0 AND volatility < {max_volatility}
            AND performance > 5
            ORDER BY volatility ASC, performance DESC
            LIMIT 10
            """
            
            result = self.db.execute_query(query)
            return result.to_dict('records') if not result.empty else []
            
        except Exception as e:
            print(f"SQL hatası: {e}")
            return []

    def _get_child_savings_funds(self):
        """Çocuk birikimleri için uzun vadeli fonlar - DÜZELTILMIŞ"""
        try:
            query = """
            WITH growth_funds AS (
                SELECT f.fcode, 
                    MAX(f.ftitle) as fund_name,
                    CASE
                        WHEN MIN(f.price) > 0 THEN (MAX(f.price) - MIN(f.price)) / MIN(f.price) * 100
                        ELSE 0
                    END as performance,
                    CASE
                        WHEN AVG(f.price) > 0 THEN STDDEV(f.price) / AVG(f.price) * 100
                        ELSE 0
                    END as volatility,
                    MAX(f.investorcount) as investors,
                    CASE
                        WHEN STDDEV(f.price) > 0 AND AVG(f.price) > 0 AND MIN(f.price) > 0 THEN
                            ((MAX(f.price) - MIN(f.price)) / MIN(f.price) * 100) / 
                            (STDDEV(f.price) / AVG(f.price) * 100)
                        ELSE 0
                    END as sharpe_proxy
                FROM tefasfunds f
                WHERE f.pdate >= CURRENT_DATE - INTERVAL '1825 days'
                AND f.investorcount > 500
                AND f.price > 0
                GROUP BY f.fcode
                HAVING COUNT(*) >= 1000
                AND MIN(f.price) > 0
            )
            SELECT *, 
                CASE 
                    WHEN performance > 100 AND volatility > 0 AND volatility < 25 THEN 90
                    WHEN performance > 50 AND volatility > 0 AND volatility < 20 THEN 80
                    WHEN performance > 30 AND volatility > 0 AND volatility < 15 THEN 70
                    ELSE 50
                END as score
            FROM growth_funds
            WHERE performance > 0
            ORDER BY score DESC, sharpe_proxy DESC
            LIMIT 10
            """
            
            result = self.db.execute_query(query)
            return result.to_dict('records') if not result.empty else []
            
        except Exception as e:
            print(f"SQL hatası: {e}")
            return []

    def _get_versatile_funds(self):
        """Çok amaçlı dengeli fonlar - DÜZELTILMIŞ"""
        try:
            query = """
            WITH versatile_funds AS (
                SELECT f.fcode, 
                    MAX(f.ftitle) as fund_name,
                    CASE
                        WHEN MIN(f.price) > 0 THEN (MAX(f.price) - MIN(f.price)) / MIN(f.price) * 100
                        ELSE 0
                    END as performance,
                    CASE
                        WHEN AVG(f.price) > 0 THEN STDDEV(f.price) / AVG(f.price) * 100
                        ELSE 0
                    END as volatility,
                    CASE
                        WHEN STDDEV(f.price) > 0 AND AVG(f.price) > 0 AND MIN(f.price) > 0 THEN
                            ((MAX(f.price) - MIN(f.price)) / MIN(f.price) * 100) /
                            (STDDEV(f.price) / AVG(f.price) * 100)
                        ELSE 0
                    END as sharpe,
                    MAX(f.investorcount) as investors
                FROM tefasfunds f
                WHERE f.pdate >= CURRENT_DATE - INTERVAL '365 days'
                AND f.investorcount > 1000
                AND f.price > 0
                GROUP BY f.fcode
                HAVING COUNT(*) >= 200
                AND MIN(f.price) > 0
                AND AVG(f.price) > 0
            )
            SELECT * FROM versatile_funds
            WHERE volatility > 5 AND volatility < 20
            AND performance > 15
            ORDER BY sharpe DESC
            LIMIT 10
            """
            
            result = self.db.execute_query(query)
            return result.to_dict('records') if not result.empty else []
            
        except Exception as e:
            print(f"SQL hatası: {e}")
            return []
    def _calculate_future_value(self, monthly_payment, annual_return, years):
        """Gelecek değer hesaplama (aylık ödemeli)"""
        monthly_rate = annual_return / 12
        months = years * 12
        
        if monthly_rate == 0:
            return monthly_payment * months
        
        future_value = monthly_payment * (((1 + monthly_rate)**months - 1) / monthly_rate)
        return future_value
    
    @staticmethod
    def get_examples():
        """Kişisel finans örnekleri"""
        return [
            "Emekliliğe 10 yıl kala nasıl yatırım yapmalıyım?",
            "Emeklilik için birikim planı",
            "Çocuğum için eğitim fonu",
            "Ev almak için birikim stratejisi",
            "35 yaşındayım, emeklilik planım nasıl olmalı?",
            "Acil durum fonu oluşturma"
        ]
    
    @staticmethod
    def get_keywords():
        """Kişisel finans anahtar kelimeleri"""
        return [
            "emeklilik", "emekliliğe", "retirement", "birikim", "yaş",
            "eğitim fonu", "ev alma", "acil fon", "kişisel", "planlama",
            "gelecek", "birikim planı"
        ]
    
    @staticmethod
    def get_patterns():
        """Kişisel finans pattern'leri"""
        return [
            {
                'type': 'regex',
                'pattern': r'emekliliğe?\s*\d*\s*(yıl|sene)',
                'score': 0.95
            },
            {
                'type': 'contains_all',
                'words': ['yaş', 'emeklilik'],
                'score': 0.9
            },
            {
                'type': 'contains_all',
                'words': ['eğitim', 'fon'],
                'score': 0.9
            }
        ]
    
    @staticmethod
    def get_method_patterns():
        """Method mapping"""
        return {
            'handle_retirement_planning': ['emeklilik', 'emekliliğe', 'retirement'],
            'handle_education_planning': ['eğitim', 'okul', 'üniversite'],
            'handle_house_planning': ['ev', 'konut', 'gayrimenkul'],
            'handle_emergency_fund': ['acil', 'acil durum']
        }