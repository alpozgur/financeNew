# personal_finance_analyzer.py
"""
Kişisel Duruma Özel Fon Analiz Sistemi - Risk Assessment Entegre Edilmiş
Emeklilik, eğitim, ev alma gibi hedeflere özel portföy önerileri
Risk değerlendirmesi ile güvenli yatırım önerileri
"""
import re
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from risk_assessment import RiskAssessment

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
            return self.handle_retirement_planning(question)
        
        # Eğitim soruları
        elif any(word in question_lower for word in ['üniversite', 'eğitim', 'okul', 'burs']):
            return self.handle_education_planning(question)
        
        # Ev alma soruları
        elif any(word in question_lower for word in ['ev almak', 'ev için', 'gayrimenkul', 'konut']):
            return self.handle_house_planning(question)
        
        # Çocuk/bebek soruları
        elif any(word in question_lower for word in ['çocuk', 'bebek']):
            return self.handle_child_planning(question)
        
        # Genel birikim soruları
        else:
            return self.handle_general_savings_planning(question)

    def handle_retirement_planning(self, question):
        """Emeklilik planlaması - Risk Assessment Entegre Edilmiş"""
        print("👴 Emeklilik planlaması analizi yapılıyor...")
        
        # Süre tespiti
        years_match = re.search(r'(\d+)\s*yıl', question.lower())
        years_to_retirement = int(years_match.group(1)) if years_match else 10
        
        # Risk toleransı belirleme
        risk_tolerance = self._determine_risk_tolerance(question, years_to_retirement)
        
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
        distribution = self._get_portfolio_distribution(risk_profile)
        
        for asset_type, percentage in distribution.items():
            response += f"   • {asset_type}: %{percentage}\n"
        
        # Risk kontrolü ile fon önerileri
        response += f"\n🎯 ÖNERİLEN FONLAR (RİSK KONTROLÜ İLE):\n\n"
        
        # Hisse senedi fonları
        if distribution["Hisse Senedi Fonları"] > 0:
            equity_funds = self._get_funds_by_type_with_risk_control("stock", risk_tolerance)
            response += f"📈 HİSSE SENEDİ FONLARI (%{distribution['Hisse Senedi Fonları']}):\n"
            
            if not equity_funds:
                response += f"   ⚠️ Risk kriterlerine uygun hisse senedi fonu bulunamadı.\n"
            else:
                for fund in equity_funds[:3]:
                    risk_indicator = self._get_risk_indicator(fund.get('risk_level', 'UNKNOWN'))
                    response += f"   • {fund['fcode']}: {fund['fund_name'][:40]}... {risk_indicator}\n"
                    response += f"     Getiri: %{fund['performance']:.2f}, Risk: %{fund['volatility']:.2f}\n"
            response += "\n"
        
        # Borçlanma araçları fonları
        if distribution["Borçlanma Araçları"] > 0:
            bond_funds = self._get_funds_by_type_with_risk_control("governmentbond", risk_tolerance)
            response += f"📊 BORÇLANMA ARAÇLARI FONLARI (%{distribution['Borçlanma Araçları']}):\n"
            
            if not bond_funds:
                response += f"   ⚠️ Risk kriterlerine uygun borçlanma araçları fonu bulunamadı.\n"
            else:
                for fund in bond_funds[:3]:
                    risk_indicator = self._get_risk_indicator(fund.get('risk_level', 'UNKNOWN'))
                    response += f"   • {fund['fcode']}: {fund['fund_name'][:40]}... {risk_indicator}\n"
                    response += f"     Getiri: %{fund['performance']:.2f}, Risk: %{fund['volatility']:.2f}\n"
            response += "\n"
        
        # Para piyasası fonları
        if distribution["Para Piyasası"] > 0:
            money_market_funds = self._get_low_risk_funds_with_risk_control()
            response += f"💰 PARA PİYASASI FONLARI (%{distribution['Para Piyasası']}):\n"
            
            if not money_market_funds:
                response += f"   ⚠️ Risk kriterlerine uygun para piyasası fonu bulunamadı.\n"
            else:
                for fund in money_market_funds[:3]:
                    risk_indicator = self._get_risk_indicator(fund.get('risk_level', 'UNKNOWN'))
                    response += f"   • {fund['fcode']}: {fund['fund_name'][:40]}... {risk_indicator}\n"
                    response += f"     Getiri: %{fund['performance']:.2f}, Risk: %{fund['volatility']:.2f}\n"
        
        # Risk uyarıları ve engellenen fonlar
        blocked_funds = self._get_blocked_high_risk_funds()
        if blocked_funds:
            response += f"\n⛔ YÜKSEK RİSKLİ FONLAR (ÖNERİLMİYOR):\n"
            for fund in blocked_funds[:5]:
                response += f"   • {fund['fcode']}: {fund['risk_level']} RİSK - {fund['reason']}\n"
        
        # Tavsiyeler
        response += f"\n💡 EMEKLİLİK TAVSİYELERİ:\n"
        response += f"   • Aylık düzenli yatırım yapın (DCA stratejisi)\n"
        response += f"   • Yılda bir portföyü gözden geçirin\n"
        response += f"   • Emekliliğe yaklaştıkça riski azaltın\n"
        response += f"   • Enflasyonu hesaba katın (TÜFE+%2-3)\n"
        response += f"   • BES avantajlarını değerlendirin\n"
        response += f"   • Risk seviyenizi düzenli kontrol edin\n"
        
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

    def handle_education_planning(self, question):
        """Eğitim planlaması - Risk Assessment Entegre Edilmiş"""
        print("🎓 Eğitim birikim planı analizi yapılıyor...")
        
        response = f"\n🎓 EĞİTİM BİRİKİM PORTFÖYÜ (GÜVENLİ)\n"
        response += f"{'='*45}\n\n"
        
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
        
        # Risk kontrolü ile uygun fonları bul
        response += f"\n🎯 EĞİTİM İÇİN ÖNERİLEN FONLAR (RİSK KONTROLÜ İLE):\n\n"
        
        # Dengeli ve güvenli fonları öner
        safe_funds = self._get_balanced_funds_for_education_with_risk()
        
        if not safe_funds:
            response += f"⚠️ Risk kriterlerine uygun eğitim fonu bulunamadı.\n"
            response += f"Lütfen daha sonra tekrar deneyin veya manuel kontrol yapın.\n\n"
        else:
            for i, fund in enumerate(safe_funds[:5], 1):
                risk_indicator = self._get_risk_indicator(fund.get('risk_level', 'UNKNOWN'))
                response += f"{i}. {fund['fcode']} {risk_indicator}\n"
                response += f"   📝 {fund['fund_name'][:45]}...\n"
                response += f"   📊 1 Yıllık Getiri: %{fund['performance']:.2f}\n"
                response += f"   📉 Risk (Volatilite): %{fund['volatility']:.2f}\n"
                response += f"   👥 Yatırımcı Sayısı: {fund['investors']:,}\n"
                response += f"   🛡️ Risk Seviyesi: {fund.get('risk_level', 'BİLİNMİYOR')}\n\n"
        
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
        expected_return = 0.15  # Daha muhafazakar getiri beklentisi
        
        future_value = self._calculate_future_value(monthly_target, expected_return, years_to_save)
        
        response += f"📈 BİRİKİM PLANI:\n"
        response += f"   Aylık hedef: {monthly_target:,.0f} TL\n"
        response += f"   Süre: {years_to_save} yıl\n"
        response += f"   Beklenen getiri: %{expected_return*100:.0f} (muhafazakar)\n"
        response += f"   Tahmini birikim: {future_value:,.0f} TL\n\n"
        
        response += f"💡 EĞİTİM BİRİKİMİ TAVSİYELERİ:\n"
        response += f"   • Çocuk hesabı açın (vergi avantajı)\n"
        response += f"   • Düzenli aylık yatırım yapın\n"
        response += f"   • Enflasyona karşı korumalı fonları tercih edin\n"
        response += f"   • Devlet desteklerini araştırın\n"
        response += f"   • Alternatif gelir kaynakları oluşturun\n"
        response += f"   • Fonların risk seviyelerini düzenli kontrol edin\n"
        
        return response

    def handle_house_planning(self, question):
        """Ev alma planlaması - Risk Assessment Entegre Edilmiş"""
        print("🏠 Ev alma birikim planı analizi yapılıyor...")
        
        # Süre tespiti
        years_match = re.search(r'(\d+)\s*yıl', question.lower())
        years_to_save = int(years_match.group(1)) if years_match else 2
        
        response = f"\n🏠 EV ALMA BİRİKİM PLANI ({years_to_save} YIL)\n"
        response += f"{'='*45}\n\n"
        
        # Kısa vadeli hedef - düşük riskli portföy
        response += f"⏰ KISA VADELİ HEDEF - GÜVENLİ PORTFÖY\n\n"
        
        # Portföy önerisi
        distribution = self._get_home_purchase_distribution(years_to_save)
        
        response += f"📊 ÖNERİLEN PORTFÖY DAĞILIMI:\n"
        for asset_type, percentage in distribution.items():
            response += f"   • {asset_type}: %{percentage}\n"
        
        # Risk kontrolü ile güvenli fonları bul
        response += f"\n🛡️ EV İÇİN GÜVENLİ FONLAR (RİSK KONTROLÜ İLE):\n\n"
        
        # SQL ile düşük riskli fonları getir
        safe_funds = self._get_home_purchase_funds_with_risk(years_to_save)
        
        if not safe_funds:
            response += f"⚠️ Risk kriterlerine uygun ev alma fonu bulunamadı.\n"
            response += f"Kısa vadeli hedefler için mevduat veya devlet tahvillerini değerlendirin.\n\n"
        else:
            for i, fund in enumerate(safe_funds[:5], 1):
                risk_indicator = self._get_risk_indicator(fund.get('risk_level', 'UNKNOWN'))
                response += f"{i}. {fund['fcode']} {risk_indicator}\n"
                response += f"   📝 {fund['fund_name'][:45]}...\n"
                response += f"   💰 Yıllık Getiri: %{fund['performance']:.2f}\n"
                response += f"   🛡️ Risk: %{fund['volatility']:.2f} (Düşük)\n"
                response += f"   💲 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
                response += f"   🔒 Risk Seviyesi: {fund.get('risk_level', 'BİLİNMİYOR')}\n\n"
        
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
        response += f"📊 ALTERNATİF SENARYOLAR (Muhafazakar %10 getiri):\n"
        
        scenarios = [
            (5000, 0.10),   # 5000 TL, %10 getiri
            (7500, 0.10),   # 7500 TL, %10 getiri
            (10000, 0.10),  # 10000 TL, %10 getiri
        ]
        
        for monthly, return_rate in scenarios:
            fv = self._calculate_future_value(monthly, return_rate, years_to_save)
            response += f"   • Aylık {monthly:,} TL → {years_to_save} yıl sonra: {fv:,.0f} TL\n"
        
        response += f"\n💡 EV ALMA TAVSİYELERİ:\n"
        response += f"   • Kısa vadede güvenlik öncelikli\n"
        response += f"   • Extreme riskli fonlardan kaçının\n"
        response += f"   • Likiditeyi koruyun - para piyasası fonları\n"
        response += f"   • Konut kredisi faizlerini takip edin\n"
        response += f"   • Devlet desteklerini araştırın\n"
        response += f"   • Acele etmeyin, piyasayı takip edin\n"
        
        return response

    def handle_child_planning(self, question):
        """Çocuk için birikim planlaması - Risk Assessment Entegre Edilmiş"""
        print("👶 Çocuk birikim planı analizi yapılıyor...")
        
        response = f"\n👶 ÇOCUK İÇİN BİRİKİM PORTFÖYÜ (GÜVENLİ)\n"
        response += f"{'='*45}\n\n"
        
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
        
        # Risk kontrolü ile çocuk dostu fonlar
        response += f"\n🌟 ÇOCUK BİRİKİMİ İÇİN ÖNERİLEN FONLAR (RİSK KONTROLÜ İLE):\n\n"
        
        # Uzun vadeli büyüme fonları
        growth_funds = self._get_child_savings_funds_with_risk()
        
        if not growth_funds:
            response += f"⚠️ Risk kriterlerine uygun çocuk birikimleri fonu bulunamadı.\n"
            response += f"Manuel kontrol önerilir.\n\n"
        else:
            for i, fund in enumerate(growth_funds[:5], 1):
                risk_indicator = self._get_risk_indicator(fund.get('risk_level', 'UNKNOWN'))
                response += f"{i}. {fund['fcode']} {risk_indicator}\n"
                response += f"   📝 {fund['fund_name'][:45]}...\n"
                response += f"   📈 5 Yıllık Ort. Getiri: %{fund['performance']:.2f}\n"
                response += f"   🎯 Uzun Vade Skoru: {fund['score']}/100\n"
                response += f"   🛡️ Risk Seviyesi: {fund.get('risk_level', 'BİLİNMİYOR')}\n\n"
        
        # Çocuk giderleri ve hedefler
        response += f"💰 ÇOCUK İÇİN FİNANSAL HEDEFLER:\n"
        response += f"   • Üniversite eğitimi: 1,000,000 - 3,000,000 TL\n"
        response += f"   • Yurtdışı eğitimi: 3,000,000 - 5,000,000 TL\n"
        response += f"   • İlk ev yardımı: 500,000 - 1,000,000 TL\n"
        response += f"   • Düğün/Başlangıç: 300,000 - 500,000 TL\n\n"
        
        # Aylık birikim örnekleri
        response += f"📈 AYLIK BİRİKİM ÖRNEKLERİ (18 yıl, %15 getiri - muhafazakar):\n"
        
        monthly_amounts = [500, 1000, 2000, 3000, 5000]
        for amount in monthly_amounts:
            fv = self._calculate_future_value(amount, 0.15, 18)  # Daha muhafazakar getiri
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
        response += f"   • Risk seviyelerini düzenli kontrol edin\n"
        
        return response

    def handle_general_savings_planning(self, question):
        """Genel birikim planlaması - Risk Assessment Entegre Edilmiş"""
        print("💰 Genel birikim planı analizi yapılıyor...")
        
        response = f"\n💰 GENEL BİRİKİM VE YATIRIM PLANI (GÜVENLİ)\n"
        response += f"{'='*50}\n\n"
        
        # Genel tavsiyeler
        response += f"📊 TEMEL YATIRIM PRENSİPLERİ:\n\n"
        
        response += f"1️⃣ ACİL FON (3-6 aylık gider):\n"
        response += f"   • Para piyasası fonları (DÜŞÜK RİSK)\n"
        response += f"   • Likit fonlar (DÜŞÜK RİSK)\n"
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
        
        # Risk kontrolü ile genel amaçlı fonlar
        response += f"🎯 ÇOK AMAÇLI ÖNERİLEN FONLAR (RİSK KONTROLÜ İLE):\n\n"
        
        versatile_funds = self._get_versatile_funds_with_risk()
        
        if not versatile_funds:
            response += f"⚠️ Risk kriterlerine uygun çok amaçlı fon bulunamadı.\n"
            response += f"Manuel inceleme önerilir.\n\n"
        else:
            for i, fund in enumerate(versatile_funds[:5], 1):
                risk_indicator = self._get_risk_indicator(fund.get('risk_level', 'UNKNOWN'))
                response += f"{i}. {fund['fcode']} {risk_indicator}\n"
                response += f"   📝 {fund['fund_name'][:45]}...\n"
                response += f"   ⚖️ Dengeli Yapı\n"
                response += f"   📊 Getiri/Risk: {fund['sharpe']:.2f}\n"
                response += f"   🛡️ Risk Seviyesi: {fund.get('risk_level', 'BİLİNMİYOR')}\n\n"
        
        response += f"💡 GENEL TAVSİYELER:\n"
        response += f"   • Gelirin %20'sini biriktirin\n"
        response += f"   • Çeşitlendirme yapın\n"
        response += f"   • Düzenli gözden geçirin\n"
        response += f"   • Duygusal karar vermeyin\n"
        response += f"   • Uzun vadeli düşünün\n"
        response += f"   • Risk seviyelerini sürekli kontrol edin\n"
        response += f"   • EXTREME riskli fonlardan kaçının\n"
        
        return response

    # Risk Assessment Entegre Edilmiş Yardımcı Metodlar
    def _determine_risk_tolerance(self, question, years_to_goal):
        """Risk toleransını belirle"""
        question_lower = question.lower()
        
        # Muhafazakar kelimeler
        if any(word in question_lower for word in ['güvenli', 'muhafazakar', 'az riskli', 'garantili']):
            return 'conservative'
        
        # Agresif kelimeler
        elif any(word in question_lower for word in ['agresif', 'riskli', 'yüksek getiri', 'hızlı büyüme']):
            return 'aggressive'
        
        # Süreye göre varsayılan
        elif years_to_goal <= 3:
            return 'conservative'
        elif years_to_goal <= 10:
            return 'moderate'
        else:
            return 'aggressive'

    def _get_portfolio_distribution(self, risk_profile):
        """Risk profiline göre portföy dağılımı"""
        distributions = {
            "agresif": {
                "Hisse Senedi Fonları": 70,
                "Borçlanma Araçları": 20,
                "Para Piyasası": 10
            },
            "dengeli": {
                "Hisse Senedi Fonları": 50,
                "Borçlanma Araçları": 35,
                "Para Piyasası": 15
            },
            "muhafazakar": {
                "Hisse Senedi Fonları": 30,
                "Borçlanma Araçları": 50,
                "Para Piyasası": 20
            },
            "çok muhafazakar": {
                "Hisse Senedi Fonları": 10,
                "Borçlanma Araçları": 40,
                "Para Piyasası": 50
            }
        }
        return distributions.get(risk_profile, distributions["dengeli"])

    def _get_home_purchase_distribution(self, years_to_save):
        """Ev alma için portföy dağılımı"""
        if years_to_save <= 1:
            return {
                "Para Piyasası": 70,
                "Kısa Vadeli Tahvil": 20,
                "Likit Fonlar": 10
            }
        elif years_to_save <= 3:
            return {
                "Para Piyasası": 50,
                "Borçlanma Araçları": 30,
                "Döviz/Altın": 20
            }
        else:
            return {
                "Borçlanma Araçları": 40,
                "Para Piyasası": 30,
                "Hisse Senedi": 20,
                "Döviz/Altın": 10
            }

    def _get_funds_by_type_with_risk_control(self, fund_type, risk_tolerance):
        """Risk kontrolü ile fon türü filtresi"""
        try:
            query = f"""
            SELECT DISTINCT
                pm.fcode,
                lf.ftitle as fund_name,
                pm.annual_return as performance,
                pm.annual_volatility * 100 as volatility,
                lf.investorcount as investors,
                pm.current_price,
                mv.price_vs_sma20,
                mv.rsi_14,
                mv.stochastic_14,
                mv.days_since_last_trade
            FROM mv_fund_performance_metrics pm
            JOIN mv_latest_fund_data lf ON pm.fcode = lf.fcode
            JOIN mv_fund_technical_indicators mv ON pm.fcode = mv.fcode
            LEFT JOIN tefasfunddetails fd ON pm.fcode = fd.fcode
            WHERE COALESCE(fd.{fund_type}, 0) > 50
            AND pm.annual_return > 5
            AND pm.annual_volatility < 0.5
            ORDER BY pm.annual_return DESC
            LIMIT 20
            """
            
            result = self.db.execute_query(query)
            if result.empty:
                return []
            
            # Risk kontrolü uygula
            safe_funds = []
            for _, fund in result.iterrows():
                risk_data = {
                    'fcode': fund['fcode'],
                    'price_vs_sma20': float(fund.get('price_vs_sma20', 0)),
                    'rsi_14': float(fund.get('rsi_14', 50)),
                    'stochastic_14': float(fund.get('stochastic_14', 50)),
                    'days_since_last_trade': int(fund.get('days_since_last_trade', 0)),
                    'investorcount': int(fund.get('investors', 0))
                }
                
                risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                
                # Risk toleransına göre filtrele
                if self._is_fund_suitable_for_risk_tolerance(risk_assessment, risk_tolerance):
                    fund_dict = fund.to_dict()
                    fund_dict['risk_level'] = risk_assessment['risk_level']
                    fund_dict['risk_factors'] = risk_assessment['risk_factors']
                    safe_funds.append(fund_dict)
            
            return safe_funds
            
        except Exception as e:
            print(f"Risk kontrolü SQL hatası: {e}")
            return []

    def _get_low_risk_funds_with_risk_control(self):
        """Risk kontrolü ile düşük riskli fonlar"""
        try:
            query = """
            WITH fund_risk AS (
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
                WHERE f.pdate >= CURRENT_DATE - INTERVAL '90 days'
                AND f.investorcount > 500
                AND f.price > 0
                GROUP BY f.fcode
                HAVING COUNT(*) >= 60
                AND MIN(f.price) > 0
            )
            SELECT fr.*, 
                mv.price_vs_sma20,
                mv.rsi_14,
                mv.stochastic_14,
                mv.days_since_last_trade
            FROM fund_risk fr
            JOIN mv_fund_technical_indicators mv ON fr.fcode = mv.fcode
            WHERE fr.volatility < 5 AND fr.volatility > 0
            ORDER BY fr.performance DESC
            LIMIT 15
            """
            
            result = self.db.execute_query(query)
            if result.empty:
                return []
            
            # Risk kontrolü uygula
            safe_funds = []
            for _, fund in result.iterrows():
                risk_data = {
                    'fcode': fund['fcode'],
                    'price_vs_sma20': float(fund.get('price_vs_sma20', 0)),
                    'rsi_14': float(fund.get('rsi_14', 50)),
                    'stochastic_14': float(fund.get('stochastic_14', 50)),
                    'days_since_last_trade': int(fund.get('days_since_last_trade', 0)),
                    'investorcount': int(fund.get('investors', 0))
                }
                
                risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                
                # Sadece LOW ve MEDIUM risk kabul et
                if risk_assessment['risk_level'] in ['LOW', 'MEDIUM']:
                    fund_dict = fund.to_dict()
                    fund_dict['risk_level'] = risk_assessment['risk_level']
                    safe_funds.append(fund_dict)
            
            return safe_funds
            
        except Exception as e:
            print(f"Para piyasası risk kontrolü hatası: {e}")
            return []

    def _get_balanced_funds_for_education_with_risk(self):
        """Risk kontrolü ile eğitim fonları"""
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
            SELECT bf.*, 
                mv.price_vs_sma20,
                mv.rsi_14,
                mv.stochastic_14,
                mv.days_since_last_trade
            FROM balanced_funds bf
            JOIN mv_fund_technical_indicators mv ON bf.fcode = mv.fcode
            WHERE bf.volatility > 0 AND bf.volatility < 15
            AND bf.performance > 10
            ORDER BY 
                CASE 
                    WHEN bf.volatility > 0 THEN bf.performance / bf.volatility 
                    ELSE 0 
                END DESC
            LIMIT 15
            """
            
            result = self.db.execute_query(query)
            if result.empty:
                return []
            
            # Risk kontrolü uygula
            safe_funds = []
            for _, fund in result.iterrows():
                risk_data = {
                    'fcode': fund['fcode'],
                    'price_vs_sma20': float(fund.get('price_vs_sma20', 0)),
                    'rsi_14': float(fund.get('rsi_14', 50)),
                    'stochastic_14': float(fund.get('stochastic_14', 50)),
                    'days_since_last_trade': int(fund.get('days_since_last_trade', 0)),
                    'investorcount': int(fund.get('investors', 0))
                }
                
                risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                
                # Eğitim için LOW, MEDIUM, HIGH kabul et ama EXTREME değil
                if risk_assessment['risk_level'] in ['LOW', 'MEDIUM', 'HIGH']:
                    fund_dict = fund.to_dict()
                    fund_dict['risk_level'] = risk_assessment['risk_level']
                    safe_funds.append(fund_dict)
            
            return safe_funds
            
        except Exception as e:
            print(f"Eğitim fonları risk kontrolü hatası: {e}")
            return []

    def _get_home_purchase_funds_with_risk(self, years_to_save):
        """Risk kontrolü ile ev alma fonları"""
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
            SELECT sf.*, 
                mv.price_vs_sma20,
                mv.rsi_14,
                mv.stochastic_14,
                mv.days_since_last_trade
            FROM stable_funds sf
            JOIN mv_fund_technical_indicators mv ON sf.fcode = mv.fcode
            WHERE sf.volatility > 0 AND sf.volatility < {max_volatility}
            AND sf.performance > 5
            ORDER BY sf.volatility ASC, sf.performance DESC
            LIMIT 15
            """
            
            result = self.db.execute_query(query)
            if result.empty:
                return []
            
            # Risk kontrolü uygula
            safe_funds = []
            for _, fund in result.iterrows():
                risk_data = {
                    'fcode': fund['fcode'],
                    'price_vs_sma20': float(fund.get('price_vs_sma20', 0)),
                    'rsi_14': float(fund.get('rsi_14', 50)),
                    'stochastic_14': float(fund.get('stochastic_14', 50)),
                    'days_since_last_trade': int(fund.get('days_since_last_trade', 0)),
                    'investorcount': int(fund.get('investors', 0))
                }
                
                risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                
                # Ev alma için sadece LOW ve MEDIUM risk
                if risk_assessment['risk_level'] in ['LOW', 'MEDIUM']:
                    fund_dict = fund.to_dict()
                    fund_dict['risk_level'] = risk_assessment['risk_level']
                    safe_funds.append(fund_dict)
            
            return safe_funds
            
        except Exception as e:
            print(f"Ev alma fonları risk kontrolü hatası: {e}")
            return []

    def _get_child_savings_funds_with_risk(self):
        """Risk kontrolü ile çocuk birikimleri fonları"""
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
            SELECT gf.*, 
                mv.price_vs_sma20,
                mv.rsi_14,
                mv.stochastic_14,
                mv.days_since_last_trade,
                CASE 
                    WHEN gf.performance > 100 AND gf.volatility > 0 AND gf.volatility < 25 THEN 90
                    WHEN gf.performance > 50 AND gf.volatility > 0 AND gf.volatility < 20 THEN 80
                    WHEN gf.performance > 30 AND gf.volatility > 0 AND gf.volatility < 15 THEN 70
                    ELSE 50
                END as score
            FROM growth_funds gf
            JOIN mv_fund_technical_indicators mv ON gf.fcode = mv.fcode
            WHERE gf.performance > 0
            ORDER BY score DESC, gf.sharpe_proxy DESC
            LIMIT 15
            """
            
            result = self.db.execute_query(query)
            if result.empty:
                return []
            
            # Risk kontrolü uygula
            safe_funds = []
            for _, fund in result.iterrows():
                risk_data = {
                    'fcode': fund['fcode'],
                    'price_vs_sma20': float(fund.get('price_vs_sma20', 0)),
                    'rsi_14': float(fund.get('rsi_14', 50)),
                    'stochastic_14': float(fund.get('stochastic_14', 50)),
                    'days_since_last_trade': int(fund.get('days_since_last_trade', 0)),
                    'investorcount': int(fund.get('investors', 0))
                }
                
                risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                
                # Çocuk birikimleri için EXTREME hariç tümü kabul
                if risk_assessment['risk_level'] != 'EXTREME':
                    fund_dict = fund.to_dict()
                    fund_dict['risk_level'] = risk_assessment['risk_level']
                    safe_funds.append(fund_dict)
            
            return safe_funds
            
        except Exception as e:
            print(f"Çocuk birikimleri risk kontrolü hatası: {e}")
            return []

    def _get_versatile_funds_with_risk(self):
        """Risk kontrolü ile çok amaçlı fonlar"""
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
            SELECT vf.*, 
                mv.price_vs_sma20,
                mv.rsi_14,
                mv.stochastic_14,
                mv.days_since_last_trade
            FROM versatile_funds vf
            JOIN mv_fund_technical_indicators mv ON vf.fcode = mv.fcode
            WHERE vf.volatility > 5 AND vf.volatility < 20
            AND vf.performance > 15
            ORDER BY vf.sharpe DESC
            LIMIT 15
            """
            
            result = self.db.execute_query(query)
            if result.empty:
                return []
            
            # Risk kontrolü uygula
            safe_funds = []
            for _, fund in result.iterrows():
                risk_data = {
                    'fcode': fund['fcode'],
                    'price_vs_sma20': float(fund.get('price_vs_sma20', 0)),
                    'rsi_14': float(fund.get('rsi_14', 50)),
                    'stochastic_14': float(fund.get('stochastic_14', 50)),
                    'days_since_last_trade': int(fund.get('days_since_last_trade', 0)),
                    'investorcount': int(fund.get('investors', 0))
                }
                
                risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                
                # Çok amaçlı için EXTREME hariç kabul
                if risk_assessment['risk_level'] != 'EXTREME':
                    fund_dict = fund.to_dict()
                    fund_dict['risk_level'] = risk_assessment['risk_level']
                    safe_funds.append(fund_dict)
            
            return safe_funds
            
        except Exception as e:
            print(f"Çok amaçlı fonlar risk kontrolü hatası: {e}")
            return []

    def _get_blocked_high_risk_funds(self):
        """Yüksek riskli engellenen fonları listele"""
        try:
            query = """
            SELECT mv.fcode, mv.rsi_14, mv.price_vs_sma20, mv.days_since_last_trade, mv.investorcount
            FROM mv_fund_technical_indicators mv
            WHERE mv.investorcount > 100
            ORDER BY mv.rsi_14 DESC
            LIMIT 50
            """
            
            result = self.db.execute_query(query)
            if result.empty:
                return []
            
            blocked_funds = []
            for _, fund in result.iterrows():
                risk_data = {
                    'fcode': fund['fcode'],
                    'price_vs_sma20': float(fund.get('price_vs_sma20', 0)),
                    'rsi_14': float(fund.get('rsi_14', 50)),
                    'stochastic_14': 50,  # Default değer
                    'days_since_last_trade': int(fund.get('days_since_last_trade', 0)),
                    'investorcount': int(fund.get('investorcount', 0))
                }
                
                risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                
                if risk_assessment['risk_level'] in ['HIGH', 'EXTREME']:
                    reason = ', '.join([f['factor'] for f in risk_assessment['risk_factors'][:2]])
                    blocked_funds.append({
                        'fcode': fund['fcode'],
                        'risk_level': risk_assessment['risk_level'],
                        'reason': reason
                    })
            
            return blocked_funds[:10]
            
        except Exception as e:
            print(f"Bloke fonlar listesi hatası: {e}")
            return []

    def _is_fund_suitable_for_risk_tolerance(self, risk_assessment, risk_tolerance):
        """Risk toleransına uygunluk kontrolü"""
        risk_level = risk_assessment['risk_level']
        
        if risk_tolerance == 'conservative':
            return risk_level in ['LOW', 'MEDIUM']
        elif risk_tolerance == 'moderate':
            return risk_level in ['LOW', 'MEDIUM', 'HIGH']
        elif risk_tolerance == 'aggressive':
            return risk_level != 'EXTREME'  # EXTREME hariç her şey kabul
        
        return False

    def _get_risk_indicator(self, risk_level):
        """Risk seviyesi göstergesi"""
        indicators = {
            'LOW': '🟢',
            'MEDIUM': '🟡',
            'HIGH': '🟠',
            'EXTREME': '🔴',
            'UNKNOWN': '⚪'
        }
        return indicators.get(risk_level, '⚪')

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