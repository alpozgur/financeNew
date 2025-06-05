# ai_personalized_advisor.py
"""
AI-Powered Personalized Financial Advisor for TEFAS
Kişiselleştirilmiş finansal danışmanlık hizmeti
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np

@dataclass
class UserProfile:
    """Kullanıcı profili"""
    age: int
    monthly_income: float
    risk_tolerance: str  # 'low', 'medium', 'high', 'very_high'
    financial_goal: str
    years_to_goal: int
    current_savings: float
    monthly_expenses: Optional[float] = None
    has_emergency_fund: bool = False
    investment_experience: str = 'beginner'  # 'beginner', 'intermediate', 'advanced'
    family_status: str = 'single'  # 'single', 'married', 'married_with_kids'
    existing_investments: Optional[Dict] = None

class AIPersonalizedAdvisor:
    """AI destekli kişisel finansal danışman"""
    
    def __init__(self, coordinator, ai_provider):
        self.coordinator = coordinator
        self.ai_provider = ai_provider
        self.db = coordinator.db
        
        # Risk profilleri ve yaş grupları
        self.risk_profiles = {
            'low': {'equity': 20, 'bond': 60, 'money_market': 20},
            'medium': {'equity': 40, 'bond': 40, 'money_market': 20},
            'high': {'equity': 60, 'bond': 30, 'money_market': 10},
            'very_high': {'equity': 80, 'bond': 15, 'money_market': 5}
        }
        
        self.life_stages = {
            'young': (18, 35),
            'middle': (36, 50),
            'mature': (51, 65),
            'senior': (66, 100)
        }
    
    def get_personalized_advice(self, user_profile: UserProfile) -> str:
        """Ana metod - Kişiselleştirilmiş finansal tavsiye"""
        
        # 1. Profil analizi
        profile_analysis = self._analyze_user_profile(user_profile)
        
        # 2. Uygun fonları bul
        suitable_funds = self._get_suitable_funds(user_profile, profile_analysis)
        
        # 3. AI'dan kişisel tavsiye al
        ai_advice = self._get_ai_personalized_advice(user_profile, profile_analysis, suitable_funds)
        
        # 4. Sonuçları formatla
        return self._format_personalized_response(user_profile, profile_analysis, suitable_funds, ai_advice)
    
    def _analyze_user_profile(self, profile: UserProfile) -> Dict:
        """Kullanıcı profilini analiz et"""
        analysis = {
            'life_stage': self._get_life_stage(profile.age),
            'savings_rate': self._calculate_savings_rate(profile),
            'risk_capacity': self._assess_risk_capacity(profile),
            'adjusted_risk_profile': self._adjust_risk_profile(profile),
            'investment_horizon': profile.years_to_goal,
            'liquidity_needs': self._assess_liquidity_needs(profile),
            'tax_considerations': self._get_tax_considerations(profile)
        }
        
        return analysis
    
    def _get_life_stage(self, age: int) -> str:
        """Yaşam evresini belirle"""
        for stage, (min_age, max_age) in self.life_stages.items():
            if min_age <= age <= max_age:
                return stage
        return 'senior'
    
    def _calculate_savings_rate(self, profile: UserProfile) -> float:
        """Tasarruf oranını hesapla"""
        if profile.monthly_expenses:
            available_for_savings = profile.monthly_income - profile.monthly_expenses
            return (available_for_savings / profile.monthly_income) * 100
        else:
            # Varsayılan: gelirin %20'si
            return 20.0
    
    def _assess_risk_capacity(self, profile: UserProfile) -> str:
        """Risk kapasitesini değerlendir"""
        # Yaş faktörü
        age_factor = 1.0
        if profile.age > 50:
            age_factor = 0.7
        elif profile.age > 60:
            age_factor = 0.5
        
        # Gelir faktörü
        income_factor = 1.0
        if profile.monthly_income > 50000:
            income_factor = 1.3
        elif profile.monthly_income < 15000:
            income_factor = 0.8
        
        # Zaman faktörü
        time_factor = 1.0
        if profile.years_to_goal < 3:
            time_factor = 0.5
        elif profile.years_to_goal > 10:
            time_factor = 1.5
        
        # Toplam kapasite skoru
        capacity_score = age_factor * income_factor * time_factor
        
        if capacity_score >= 1.5:
            return 'high'
        elif capacity_score >= 1.0:
            return 'medium'
        else:
            return 'low'
    
    def _adjust_risk_profile(self, profile: UserProfile) -> str:
        """Risk profilini kapasite ile dengele"""
        capacity = self._assess_risk_capacity(profile)
        tolerance = profile.risk_tolerance
        
        # Risk tolerance ve capacity uyumu
        risk_map = {
            ('low', 'low'): 'low',
            ('low', 'medium'): 'low',
            ('low', 'high'): 'medium',
            ('medium', 'low'): 'low',
            ('medium', 'medium'): 'medium',
            ('medium', 'high'): 'medium',
            ('high', 'low'): 'medium',
            ('high', 'medium'): 'high',
            ('high', 'high'): 'high',
            ('very_high', 'low'): 'medium',
            ('very_high', 'medium'): 'high',
            ('very_high', 'high'): 'very_high'
        }
        
        return risk_map.get((tolerance, capacity), 'medium')
    
    def _assess_liquidity_needs(self, profile: UserProfile) -> str:
        """Likidite ihtiyacını değerlendir"""
        if not profile.has_emergency_fund:
            return 'high'
        elif profile.years_to_goal < 2:
            return 'high'
        elif profile.years_to_goal < 5:
            return 'medium'
        else:
            return 'low'
    
    def _get_tax_considerations(self, profile: UserProfile) -> List[str]:
        """Vergi avantajlarını belirle"""
        considerations = []
        
        # BES avantajı
        if profile.age < 56:
            considerations.append('BES - %30 devlet katkısı')
        
        # Çocuk hesabı
        if profile.family_status == 'married_with_kids':
            considerations.append('Çocuk yatırım hesabı - Vergi muafiyeti')
        
        # Stopaj avantajlı fonlar
        considerations.append('Hisse yoğun fonlar - Stopaj avantajı')
        
        return considerations
    
    def _get_suitable_funds(self, profile: UserProfile, analysis: Dict) -> Dict:
        """Profile uygun fonları bul"""
        risk_profile = analysis['adjusted_risk_profile']
        
        # Risk profiline göre varlık dağılımı
        allocation = self.risk_profiles[risk_profile]
        
        suitable_funds = {
            'equity_funds': self._get_equity_funds(allocation['equity'], profile),
            'bond_funds': self._get_bond_funds(allocation['bond'], profile),
            'money_market_funds': self._get_money_market_funds(allocation['money_market'], profile),
            'special_funds': self._get_special_situation_funds(profile, analysis)
        }
        
        return suitable_funds
    
    def _get_equity_funds(self, allocation_pct: int, profile: UserProfile) -> List[Dict]:
        """Hisse senedi fonlarını getir"""
        try:
            query = """
            SELECT 
                pm.fcode,
                lf.ftitle as fund_name,
                pm.annual_return * 100 as annual_return,
                pm.annual_volatility * 100 as volatility,
                pm.sharpe_ratio,
                lf.totalfundsize / 1000000 as size_million_tl,
                lf.investorcount
            FROM mv_fund_performance_metrics pm
            JOIN mv_latest_fund_data lf ON pm.fcode = lf.fcode
            JOIN tefasfunddetails fd ON pm.fcode = fd.fcode
            WHERE fd.stock > 50
            AND lf.investorcount > 1000
            AND pm.sharpe_ratio > 0.5
            ORDER BY pm.sharpe_ratio DESC
            LIMIT 10
            """
            
            result = self.db.execute_query(query)
            if not result.empty:
                return result.to_dict('records')[:5]
            return []
            
        except Exception as e:
            print(f"Hisse fonu sorgulama hatası: {e}")
            return []
    
    def _get_bond_funds(self, allocation_pct: int, profile: UserProfile) -> List[Dict]:
        """Borçlanma araçları fonlarını getir"""
        try:
            query = """
            SELECT 
                pm.fcode,
                lf.ftitle as fund_name,
                pm.annual_return * 100 as annual_return,
                pm.annual_volatility * 100 as volatility,
                pm.sharpe_ratio,
                lf.totalfundsize / 1000000 as size_million_tl
            FROM mv_fund_performance_metrics pm
            JOIN mv_latest_fund_data lf ON pm.fcode = lf.fcode
            JOIN tefasfunddetails fd ON pm.fcode = fd.fcode
            WHERE (fd.governmentbond > 30 OR fd.eurobonds > 30)
            AND pm.annual_volatility < 0.15
            ORDER BY pm.sharpe_ratio DESC
            LIMIT 10
            """
            
            result = self.db.execute_query(query)
            if not result.empty:
                return result.to_dict('records')[:5]
            return []
            
        except Exception as e:
            print(f"Tahvil fonu sorgulama hatası: {e}")
            return []
    
    def _get_money_market_funds(self, allocation_pct: int, profile: UserProfile) -> List[Dict]:
        """Para piyasası fonlarını getir"""
        try:
            query = """
            SELECT 
                pm.fcode,
                lf.ftitle as fund_name,
                pm.annual_return * 100 as annual_return,
                pm.annual_volatility * 100 as volatility,
                lf.totalfundsize / 1000000 as size_million_tl
            FROM mv_fund_performance_metrics pm
            JOIN mv_latest_fund_data lf ON pm.fcode = lf.fcode
            WHERE lf.ftitle LIKE '%PARA PIYASASI%'
            AND pm.annual_volatility < 0.05
            ORDER BY pm.annual_return DESC
            LIMIT 5
            """
            
            result = self.db.execute_query(query)
            if not result.empty:
                return result.to_dict('records')
            return []
            
        except Exception as e:
            print(f"Para piyasası fonu sorgulama hatası: {e}")
            return []
    
    def _get_special_situation_funds(self, profile: UserProfile, analysis: Dict) -> List[Dict]:
        """Özel durum fonları (altın, döviz, sektörel)"""
        special_funds = []
        
        # Enflasyon koruması
        if profile.years_to_goal > 5:
            special_funds.extend(self._get_inflation_protection_funds())
        
        # Emeklilik yakınsa güvenli fonlar
        if profile.financial_goal == 'retirement' and profile.years_to_goal < 5:
            special_funds.extend(self._get_conservative_funds())
        
        return special_funds
    
    def _get_inflation_protection_funds(self) -> List[Dict]:
        """Enflasyon korumalı fonlar"""
        try:
            query = """
            SELECT 
                pm.fcode,
                lf.ftitle as fund_name,
                pm.annual_return * 100 as annual_return
            FROM mv_fund_performance_metrics pm
            JOIN mv_latest_fund_data lf ON pm.fcode = lf.fcode
            WHERE (lf.ftitle LIKE '%ALTIN%' OR lf.ftitle LIKE '%EURO%' OR lf.ftitle LIKE '%DOLAR%')
            AND pm.annual_return > 20
            ORDER BY pm.annual_return DESC
            LIMIT 3
            """
            
            result = self.db.execute_query(query)
            if not result.empty:
                return result.to_dict('records')
            return []
            
        except:
            return []
    
    def _get_conservative_funds(self) -> List[Dict]:
        """Muhafazakar fonlar"""
        try:
            query = """
            SELECT 
                pm.fcode,
                lf.ftitle as fund_name,
                pm.annual_return * 100 as annual_return,
                pm.annual_volatility * 100 as volatility
            FROM mv_fund_performance_metrics pm
            JOIN mv_latest_fund_data lf ON pm.fcode = lf.fcode
            WHERE pm.annual_volatility < 0.10
            AND pm.annual_return > 15
            ORDER BY pm.sharpe_ratio DESC
            LIMIT 3
            """
            
            result = self.db.execute_query(query)
            if not result.empty:
                return result.to_dict('records')
            return []
            
        except:
            return []
    
    def _get_ai_personalized_advice(self, profile: UserProfile, analysis: Dict, suitable_funds: Dict) -> str:
        """AI'dan kişiselleştirilmiş tavsiye al"""
        
        # Fon önerilerini formatla
        fund_recommendations = self._format_fund_recommendations(suitable_funds)
        
        prompt = f"""
        TEFAS Yatırımcı Profili Analizi:
        
        KİŞİSEL BİLGİLER:
        - Yaş: {profile.age} ({analysis['life_stage']} dönem)
        - Aylık Gelir: {profile.monthly_income:,.0f} TL
        - Risk Toleransı: {profile.risk_tolerance}
        - Düzeltilmiş Risk Profili: {analysis['adjusted_risk_profile']}
        - Hedef: {profile.financial_goal} ({profile.years_to_goal} yıl)
        - Mevcut Birikim: {profile.current_savings:,.0f} TL
        - Aile Durumu: {profile.family_status}
        - Yatırım Deneyimi: {profile.investment_experience}
        
        ANALİZ SONUÇLARI:
        - Tasarruf Oranı: %{analysis['savings_rate']:.1f}
        - Risk Kapasitesi: {analysis['risk_capacity']}
        - Likidite İhtiyacı: {analysis['liquidity_needs']}
        - Vergi Avantajları: {', '.join(analysis['tax_considerations'])}
        
        ÖNERİLEN FONLAR:
        {fund_recommendations}
        
        Lütfen bu kişiye özel:
        
        1. UYGUN RİSK PROFİLİ DEĞERLENDİRMESİ
        - Neden bu risk profili uygun?
        - Yaşam evresine göre düzeltmeler
        
        2. AYLIK BİRİKİM ÖNERİSİ
        - Hedefine ulaşması için aylık ne kadar biriktirmeli?
        - Gelir/gider dengesine göre makul mu?
        
        3. DETAYLI PORTFÖY DAĞILIMI
        - Yukarıdaki fonlardan spesifik öneriler
        - Her fon için yatırım miktarı/yüzdesi
        - Neden bu fonlar seçildi?
        
        4. ALTERNATİF SENARYOLAR
        - Daha agresif yaklaşım
        - Daha muhafazakar yaklaşım
        - Farklı birikim tutarları
        
        5. KRİTİK UYARILAR VE RİSKLER
        - Bu profil için özel riskler
        - Kaçınılması gereken hatalar
        - Periyodik gözden geçirme önerileri
        
        6. TÜRK EKONOMİSİ BAĞLAMINDA DEĞERLENDİRME
        - Enflasyon etkisi
        - Döviz riski
        - Faiz ortamı
        
        Tavsiyeler somut, uygulanabilir ve kişiye özel olmalı.
        """
        
        try:
            ai_response = self.ai_provider.query(
                prompt,
                "Sen uzman bir finansal danışmansın. Kişiye özel, uygulanabilir tavsiyeler veriyorsun."
            )
            return ai_response
        except Exception as e:
            print(f"AI danışmanlık hatası: {e}")
            return self._get_fallback_advice(profile, analysis)
    
    def _format_fund_recommendations(self, suitable_funds: Dict) -> str:
        """Fon önerilerini formatla"""
        recommendations = []
        
        for fund_type, funds in suitable_funds.items():
            if funds:
                recommendations.append(f"\n{fund_type.upper()}:")
                for fund in funds[:3]:  # Her tipten max 3 fon
                    recommendations.append(
                        f"- {fund['fcode']}: {fund.get('fund_name', 'N/A')} "
                        f"(Yıllık: %{fund.get('annual_return', 0):.1f}, "
                        f"Risk: %{fund.get('volatility', 0):.1f})"
                    )
        
        return '\n'.join(recommendations)
    
    def _format_personalized_response(self, profile: UserProfile, analysis: Dict, 
                                    suitable_funds: Dict, ai_advice: str) -> str:
        """Kişiselleştirilmiş yanıtı formatla"""
        
        response = f"\n🎯 KİŞİSELLEŞTİRİLMİŞ FİNANSAL PLAN\n"
        response += f"{'='*60}\n\n"
        
        # Profil özeti
        response += f"👤 PROFİL ÖZETİ:\n"
        response += f"   • Yaş: {profile.age} ({analysis['life_stage']} dönem)\n"
        response += f"   • Hedef: {profile.financial_goal} ({profile.years_to_goal} yıl)\n"
        response += f"   • Risk Profili: {analysis['adjusted_risk_profile'].upper()}\n"
        response += f"   • Mevcut Birikim: {profile.current_savings:,.0f} TL\n\n"
        
        # AI tavsiyesi
        response += f"🤖 KİŞİYE ÖZEL AI TAVSİYELERİ:\n"
        response += f"{'='*60}\n"
        response += ai_advice
        response += f"\n{'='*60}\n\n"
        
        # Hızlı başlangıç
        response += f"⚡ HEMEN BAŞLAYABİLİRSİNİZ:\n"
        response += f"   1. Acil fon oluşturun (3-6 aylık gider)\n"
        response += f"   2. Aylık düzenli talimat verin\n"
        response += f"   3. Portföyü 3 ayda bir gözden geçirin\n"
        response += f"   4. Hedefleriniz değişirse planı güncelleyin\n\n"
        
        # Uyarı
        response += f"⚠️ ÖNEMLİ: Bu tavsiyeler genel bilgilendirme amaçlıdır. "
        response += f"Yatırım kararı vermeden önce kendi araştırmanızı yapın.\n"
        
        return response
    
    def _get_fallback_advice(self, profile: UserProfile, analysis: Dict) -> str:
        """AI kullanılamadığında fallback tavsiye"""
        return f"""
        Risk profilinize ({analysis['adjusted_risk_profile']}) uygun genel tavsiyeler:
        
        1. PORTFÖY DAĞILIMI:
        {self._get_allocation_text(analysis['adjusted_risk_profile'])}
        
        2. AYLIK BİRİKİM:
        Gelirin minimum %10-20'sini biriktirmeyi hedefleyin.
        
        3. ÖNEMLİ UYARILAR:
        - Acil durum fonu oluşturun
        - Çeşitlendirme yapın
        - Düzenli gözden geçirin
        
        Detaylı analiz için AI servisi aktif olduğunda tekrar deneyin.
        """
    
    def _get_allocation_text(self, risk_profile: str) -> str:
        """Risk profiline göre dağılım metni"""
        allocation = self.risk_profiles.get(risk_profile, self.risk_profiles['medium'])
        return f"""
        - Hisse Senedi: %{allocation['equity']}
        - Tahvil/Bono: %{allocation['bond']}  
        - Para Piyasası: %{allocation['money_market']}
        """
    
    # Kullanım kolaylığı için yardımcı metodlar
    def create_profile_from_text(self, text: str) -> Optional[UserProfile]:
        """Gelişmiş metin parser - tüm detayları yakalar"""
        
        # Varsayılan değerler
        defaults = {
            'age': 35,
            'monthly_income': 25000,
            'risk_tolerance': 'medium',
            'financial_goal': 'general_savings',
            'years_to_goal': 10,
            'current_savings': 0,
            'monthly_expenses': None,
            'has_emergency_fund': False,
            'investment_experience': 'beginner',
            'family_status': 'single'
        }
        
        text_lower = text.lower()
        
        # 1. YAŞ BULMA
        age_patterns = [
            r'(\d+)\s*yaş',
            r'yaşım\s*(\d+)',
            r'(\d+)\s*years?\s*old',
            r'ben\s*(\d+)'
        ]
        for pattern in age_patterns:
            match = re.search(pattern, text_lower)
            if match:
                defaults['age'] = int(match.group(1))
                break
        
        # 2. GELİR BULMA
        income_match = re.search(r'(\d+\.?\d*)\s*(?:bin|k)?', text_lower)
        if income_match:
            income = float(income_match.group(1))
            # "bin" veya "k" varsa 1000 ile çarp
            if 'bin' in text_lower[income_match.start():income_match.end()+5] or \
            'k' in text_lower[income_match.start():income_match.end()+5]:
                income *= 1000
            defaults['monthly_income'] = income
        
        # 3. RİSK TOLERANSI
        if any(word in text_lower for word in ['güvenli', 'muhafazakar', 'düşük risk']):
            defaults['risk_tolerance'] = 'low'
        elif any(word in text_lower for word in ['agresif', 'yüksek risk']):
            defaults['risk_tolerance'] = 'high'
        elif any(word in text_lower for word in ['çok agresif']):
            defaults['risk_tolerance'] = 'very_high'
        
        # 4. FİNANSAL HEDEF
        if 'emekli' in text_lower:
            defaults['financial_goal'] = 'retirement'
            defaults['years_to_goal'] = max(65 - defaults['age'], 1)
        elif any(word in text_lower for word in ['ev', 'konut', 'daire']):
            defaults['financial_goal'] = 'house'
            defaults['years_to_goal'] = 5
        elif any(word in text_lower for word in ['eğitim', 'okul', 'üniversite']):
            defaults['financial_goal'] = 'education'
            defaults['years_to_goal'] = 10
        
        # 5. AİLE DURUMU
        if 'evli' in text_lower:
            if 'çocuk' in text_lower:
                defaults['family_status'] = 'married_with_kids'
            else:
                defaults['family_status'] = 'married'
        
        # 6. BİRİKİM VARSA
        savings_match = re.search(r'(\d+)\s*(?:bin)?\s*birikim', text_lower)
        if savings_match:
            savings = float(savings_match.group(1))
            if 'bin' in text_lower[savings_match.start():savings_match.end()+5]:
                savings *= 1000
            defaults['current_savings'] = savings
        
        # 7. AKILLI TAHMİNLER
        # Gelire göre gider tahmini
        if defaults['monthly_income'] and not defaults['monthly_expenses']:
            if defaults['monthly_income'] < 20000:
                defaults['monthly_expenses'] = defaults['monthly_income'] * 0.85
            elif defaults['monthly_income'] < 50000:
                defaults['monthly_expenses'] = defaults['monthly_income'] * 0.75
            else:
                defaults['monthly_expenses'] = defaults['monthly_income'] * 0.65
        
        return UserProfile(**defaults)
    
    def analyze_from_question(self, question: str) -> str:
        """Sorudan direkt analiz"""
        profile = self.create_profile_from_text(question)
        
        if profile:
            return self.get_personalized_advice(profile)
        else:
            return self._get_profile_creation_help()
    
    def _get_profile_creation_help(self) -> str:
        """Profil oluşturma yardımı"""
        return """
        🤖 KİŞİSEL FİNANS DANIŞMANI
        
        Size özel tavsiye verebilmem için lütfen şu bilgileri belirtin:
        
        📋 ÖRNEK KULLANIM:
        "35 yaşındayım, aylık 25000 TL gelirim var, emeklilik için birikim yapmak istiyorum"
        "28 yaşında, 40K gelir, 5 yıl sonra ev almak istiyorum, orta risk alabilirim"
        "45 yaşında, muhafazakar yatırımcı, 10 yıl sonra emeklilik"
        
        📊 GEREKLİ BİLGİLER:
        • Yaşınız
        • Aylık geliriniz
        • Hedefiniz (emeklilik/ev/eğitim/genel)
        • Risk toleransınız (düşük/orta/yüksek)
        • Hedefe kaç yıl var
        
        Bilgilerinizi paylaşın, size özel plan hazırlayayım!
        """