# mathematical_calculations.py
"""
TEFAS Yatırım Hesaplama Modülü
Compound faiz, hedef tutar, portföy dağılımı vb. matematiksel hesaplamalar
"""

import re
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

class MathematicalCalculator:
    """TEFAS fonları için matematiksel hesaplama sınıfı"""
    
    def __init__(self, coordinator, active_funds):
        self.coordinator = coordinator
        self.active_funds = active_funds
        self.logger = coordinator.logger if hasattr(coordinator, 'logger') else None
        
    @staticmethod
    def is_mathematical_question(question: str) -> bool:
        """Matematiksel hesaplama sorusu mu kontrol et"""
        math_keywords = [
            'aylık yatırım', 'yılda ne kadar', 'compound', 'faiz',
            'böl', 'ayır', 'dağıt', 'hedef tutar', 'kaç yıl',
            'ne kadar yatırmalı', 'birikir', 'biriktir',
            'hesapla', 'calculate', 'toplam tutar', 'birikim'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in math_keywords)
    
    def analyze_mathematical_question(self, question: str) -> str:
        """Matematiksel soruyu analiz et ve cevapla"""
        question_lower = question.lower()
        
        # Aylık yatırım - compound hesaplama
        if any(word in question_lower for word in ['aylık yatırım', 'yılda ne kadar', 'birikir']):
            return self._handle_monthly_investment_calculation(question)
        
        # Portföy dağıtımı
        elif any(word in question_lower for word in ['böl', 'ayır', 'dağıt', 'portföy']):
            return self._handle_portfolio_distribution(question)
        
        # Hedef tutar hesaplama
        elif any(word in question_lower for word in ['hedef tutar', 'ne kadar yatırmalı', 'hedefe ulaş']):
            return self._handle_target_amount_calculation(question)
        
        # Genel compound faiz hesaplama
        elif any(word in question_lower for word in ['compound', 'bileşik faiz']):
            return self._handle_compound_interest_calculation(question)
        
        else:
            return self._handle_general_calculation(question)
    
    def _handle_monthly_investment_calculation(self, question: str) -> str:
        """Aylık yatırım hesaplama - gerçek fon performanslarıyla"""
        print("💰 Aylık yatırım hesaplaması yapılıyor...")
        
        # Parametreleri çıkar
        numbers = re.findall(r'(\d+(?:\.\d+)?)', question)
        monthly_amount = float(numbers[0]) if numbers else 100
        years = float(numbers[1]) if len(numbers) > 1 else 10
        
        # Yıl kelimesi kontrol
        if 'yıl' in question.lower():
            for i, num in enumerate(numbers):
                if 'yıl' in question.lower().split(str(int(float(num))))[1][:10]:
                    years = float(num)
                    if i == 0 and len(numbers) > 1:
                        monthly_amount = float(numbers[1])
                    break
        
        months = int(years * 12)
        
        response = f"\n💰 AYLIK YATIRIM HESAPLAMASI\n"
        response += f"{'='*50}\n\n"
        response += f"📊 PARAMETRELER:\n"
        response += f"   • Aylık Yatırım: {monthly_amount:,.0f} TL\n"
        response += f"   • Süre: {years:.0f} yıl ({months} ay)\n"
        response += f"   • Toplam Yatırım: {monthly_amount * months:,.0f} TL\n\n"
        
        # Farklı senaryolar için hesapla
        scenarios = []
        
        # 1. Sabit getiri senaryoları
        fixed_rates = [
            ("Düşük Risk (%15/yıl)", 0.15),
            ("Orta Risk (%25/yıl)", 0.25),
            ("Yüksek Risk (%40/yıl)", 0.40)
        ]
        
        response += f"📈 SABİT GETİRİ SENARYOLARI:\n\n"
        
        for scenario_name, annual_rate in fixed_rates:
            monthly_rate = annual_rate / 12
            future_value = self._calculate_future_value_monthly(monthly_amount, monthly_rate, months)
            total_gain = future_value - (monthly_amount * months)
            gain_percentage = (total_gain / (monthly_amount * months)) * 100
            
            response += f"🎯 {scenario_name}:\n"
            response += f"   Birikecek Tutar: {future_value:,.0f} TL\n"
            response += f"   Toplam Kazanç: {total_gain:,.0f} TL\n"
            response += f"   Kazanç Oranı: %{gain_percentage:.1f}\n\n"
            
            scenarios.append({
                'name': scenario_name,
                'future_value': future_value,
                'total_gain': total_gain
            })
        
        # 2. Gerçek fon performanslarına dayalı hesaplama
        response += f"📊 GERÇEK FON PERFORMANSLARINA DAYALI TAHMİN:\n\n"
        
        fund_scenarios = []
        analyzed_funds = 0
        
        for fcode in self.active_funds[:10]:  # İlk 10 fon
            try:
                # Son 1 yıllık veriyi al
                data = self.coordinator.db.get_fund_price_history(fcode, 252)
                
                if len(data) >= 200:  # Yeterli veri varsa
                    prices = data.set_index('pdate')['price'].sort_index()
                    
                    # Sıfır veya negatif fiyat kontrolü
                    if prices.iloc[0] <= 0 or prices.iloc[-1] <= 0:
                        continue
                    
                    # Yıllık getiri hesapla - güvenli versiyon
                    if len(prices) > 0:
                        annual_return = (prices.iloc[-1] / prices.iloc[0]) ** (252 / max(len(prices), 1)) - 1
                    else:
                        continue
                    
                    # Volatilite hesapla - güvenli versiyon
                    returns = prices.pct_change().dropna()
                    
                    # NaN veya inf değerleri temizle
                    returns = returns[~np.isinf(returns)]
                    returns = returns.dropna()
                    
                    if len(returns) > 0:
                        volatility = returns.std() * np.sqrt(252)
                    else:
                        volatility = 0.20  # Default volatilite
                    
                    # Mantıksız değerleri filtrele
                    if abs(annual_return) > 2 or volatility > 1:  # %200'den fazla getiri veya %100'den fazla volatilite
                        continue
                    
                    # Monte Carlo simülasyonu ile gelecek değer tahmini
                    simulated_value = self._monte_carlo_monthly_investment(
                        monthly_amount, annual_return, volatility, months, simulations=1000
                    )
                    
                    fund_scenarios.append({
                        'fcode': fcode,
                        'annual_return': annual_return,
                        'volatility': volatility,
                        'expected_value': simulated_value['expected'],
                        'pessimistic': simulated_value['percentile_10'],
                        'optimistic': simulated_value['percentile_90']
                    })
                    
                    analyzed_funds += 1
                    
            except Exception as e:
                continue
        
        if fund_scenarios:
            # Ortalama senaryoları hesapla
            avg_expected = np.mean([f['expected_value'] for f in fund_scenarios])
            avg_pessimistic = np.mean([f['pessimistic'] for f in fund_scenarios])
            avg_optimistic = np.mean([f['optimistic'] for f in fund_scenarios])
            
            response += f"📊 {analyzed_funds} Fon Analizine Dayalı Tahmin:\n\n"
            response += f"😟 Kötümser Senaryo (10. yüzdelik):\n"
            response += f"   Tahmini Birikim: {avg_pessimistic:,.0f} TL\n"
            response += f"   Kazanç: {avg_pessimistic - monthly_amount * months:,.0f} TL\n\n"
            
            response += f"😊 Beklenen Senaryo (Ortalama):\n"
            response += f"   Tahmini Birikim: {avg_expected:,.0f} TL\n"
            response += f"   Kazanç: {avg_expected - monthly_amount * months:,.0f} TL\n\n"
            
            response += f"🚀 İyimser Senaryo (90. yüzdelik):\n"
            response += f"   Tahmini Birikim: {avg_optimistic:,.0f} TL\n"
            response += f"   Kazanç: {avg_optimistic - monthly_amount * months:,.0f} TL\n\n"
            
            # En iyi performans gösteren fonlar
            best_funds = sorted(fund_scenarios, key=lambda x: x['annual_return'], reverse=True)[:3]
            
            response += f"🏆 EN İYİ PERFORMANS GÖSTEREN FONLAR:\n"
            for i, fund in enumerate(best_funds, 1):
                response += f"   {i}. {fund['fcode']}: Yıllık %{fund['annual_return']*100:.1f} getiri\n"
        
        # Özet ve tavsiyeler
        response += f"\n💡 ÖNEMLİ NOTLAR:\n"
        response += f"   • Geçmiş performans gelecek garantisi değildir\n"
        response += f"   • Enflasyon etkisi hesaba katılmamıştır\n"
        response += f"   • Düzenli yatırım (DCA) riski azaltır\n"
        response += f"   • Vergi avantajlı fonları değerlendirin\n"
        
        return response
    
    def _handle_portfolio_distribution(self, question: str) -> str:
        """Portföy dağıtımı hesaplama"""
        print("📊 Portföy dağıtımı hesaplanıyor...")
        
        try:
            # Tutarı ve fon sayısını çıkar
            numbers = re.findall(r'(\d+(?:\.\d+)?)', question)
            total_amount = float(numbers[0]) if numbers else 100000
            
            # Fon sayısı belirleme
            fund_count = 3  # Default
            for num in numbers[1:]:
                if int(float(num)) <= 10:  # Makul fon sayısı
                    fund_count = int(float(num))
                    break
            
            response = f"\n📊 PORTFÖY DAĞITIM ÖNERİSİ\n"
            response += f"{'='*50}\n\n"
            response += f"💰 Toplam Tutar: {total_amount:,.0f} TL\n"
            response += f"📈 Fon Sayısı: {fund_count}\n\n"
            
            # Risk bazlı dağıtım stratejileri
            strategies = {
                "Muhafazakar": self._conservative_distribution(total_amount, fund_count),
                "Dengeli": self._balanced_distribution(total_amount, fund_count),
                "Agresif": self._aggressive_distribution(total_amount, fund_count)
            }
            
            for strategy_name, distribution in strategies.items():
                response += f"🎯 {strategy_name.upper()} STRATEJİ:\n"
                response += f"{'='*30}\n"
                
                total_allocated = 0
                expected_annual_return = 0
                
                for i, allocation in enumerate(distribution['allocations'], 1):
                    fund_type = allocation['type']
                    amount = allocation['amount']
                    percentage = allocation['percentage']
                    expected_return = allocation['expected_return']
                    
                    response += f"{i}. {fund_type}:\n"
                    response += f"   Tutar: {amount:,.0f} TL (%{percentage:.0f})\n"
                    response += f"   Beklenen Yıllık Getiri: %{expected_return:.0f}\n"
                    
                    # Uygun fon önerileri
                    if 'fund_suggestions' in allocation and allocation['fund_suggestions']:
                        suggestions = allocation['fund_suggestions'][:3]
                        if suggestions:
                            response += f"   Öneri Fonlar: {', '.join(suggestions)}\n"
                    
                    response += f"\n"
                    
                    total_allocated += amount
                    expected_annual_return += expected_return * percentage / 100
                
                response += f"📊 STRATEJİ ÖZETİ:\n"
                response += f"   Toplam Dağıtılan: {total_allocated:,.0f} TL\n"
                response += f"   Beklenen Yıllık Getiri: %{expected_annual_return:.1f}\n"
                response += f"   1 Yıl Sonra Tahmini: {total_amount * (1 + expected_annual_return/100):,.0f} TL\n"
                response += f"\n{'='*50}\n\n"
            
            # Gerçek fon önerileri
            response += self._get_real_fund_suggestions(fund_count)
            
            return response
            
        except Exception as e:
            print(f"Portföy dağıtımı hatası: {e}")
            return f"❌ Portföy dağıtımı hesaplanamadı: {str(e)}"
        
    def _handle_target_amount_calculation(self, question: str) -> str:
        """Hedef tutar için gerekli yatırım hesaplama"""
        print("🎯 Hedef tutar hesaplaması yapılıyor...")
        
        # Parametreleri çıkar
        numbers = re.findall(r'(\d+(?:\.\d+)?)', question)
        target_amount = float(numbers[0]) if numbers else 1000000
        years = float(numbers[1]) if len(numbers) > 1 else 10
        
        # Milyon/bin kontrolü
        if 'milyon' in question.lower():
            for i, num in enumerate(numbers):
                if 'milyon' in question.lower().split(str(int(float(num))))[1][:10]:
                    target_amount = float(num) * 1000000
                    break
        
        months = int(years * 12)
        
        response = f"\n🎯 HEDEF TUTAR HESAPLAMASI\n"
        response += f"{'='*50}\n\n"
        response += f"📊 HEDEF BİLGİLERİ:\n"
        response += f"   • Hedef Tutar: {target_amount:,.0f} TL\n"
        response += f"   • Süre: {years:.0f} yıl ({months} ay)\n\n"
        
        # Farklı getiri senaryoları için gerekli aylık yatırım
        response += f"💰 GEREKLİ AYLIK YATIRIM TUTARLARI:\n\n"
        
        scenarios = [
            ("Düşük Getiri (%10/yıl)", 0.10),
            ("Orta Getiri (%20/yıl)", 0.20),
            ("Yüksek Getiri (%30/yıl)", 0.30),
            ("Çok Yüksek Getiri (%40/yıl)", 0.40)
        ]
        
        for scenario_name, annual_rate in scenarios:
            monthly_rate = annual_rate / 12
            
            # Aylık yatırım formülü: PMT = FV * r / ((1+r)^n - 1)
            if monthly_rate > 0:
                required_monthly = target_amount * monthly_rate / ((1 + monthly_rate)**months - 1)
            else:
                required_monthly = target_amount / months
            
            total_investment = required_monthly * months
            total_gain = target_amount - total_investment
            
            response += f"📈 {scenario_name}:\n"
            response += f"   Aylık Yatırım: {required_monthly:,.0f} TL\n"
            response += f"   Toplam Yatırım: {total_investment:,.0f} TL\n"
            response += f"   Kazanç: {total_gain:,.0f} TL\n"
            response += f"   Getiri Oranı: %{(total_gain/total_investment*100):.1f}\n\n"
        
        # Tek seferlik yatırım alternatifi
        response += f"💵 TEK SEFERLİK YATIRIM ALTERNATİFİ:\n\n"
        
        for scenario_name, annual_rate in scenarios[:3]:  # İlk 3 senaryo
            # PV = FV / (1+r)^n
            present_value = target_amount / (1 + annual_rate)**years
            
            response += f"   {scenario_name}: {present_value:,.0f} TL\n"
        
        # Gerçek fon performanslarına dayalı tahmin
        response += f"\n📊 GERÇEK FON PERFORMANSLARINA DAYALI TAHMİN:\n"
        response += self._calculate_required_investment_real_funds(target_amount, years)
        
        return response
    
    def _handle_compound_interest_calculation(self, question: str) -> str:
        """Genel compound faiz hesaplama"""
        print("📈 Bileşik faiz hesaplaması yapılıyor...")
        
        # Parametreleri çıkar
        numbers = re.findall(r'(\d+(?:\.\d+)?)', question)
        principal = float(numbers[0]) if numbers else 10000
        rate = float(numbers[1]) if len(numbers) > 1 else 20
        years = float(numbers[2]) if len(numbers) > 2 else 5
        
        # Yüzde işareti kontrolü
        if rate > 1:
            rate = rate / 100
        
        response = f"\n📈 BİLEŞİK FAİZ HESAPLAMASI\n"
        response += f"{'='*40}\n\n"
        response += f"💰 Ana Para: {principal:,.0f} TL\n"
        response += f"📊 Yıllık Faiz: %{rate*100:.1f}\n"
        response += f"⏰ Süre: {years:.0f} yıl\n\n"
        
        # Farklı bileşik dönemleri
        compounds = [
            ("Yıllık", 1),
            ("6 Aylık", 2),
            ("3 Aylık", 4),
            ("Aylık", 12),
            ("Günlük", 365)
        ]
        
        response += f"📊 FARKLI BİLEŞİK DÖNEMLER:\n\n"
        
        for compound_name, n in compounds:
            # A = P(1 + r/n)^(nt)
            future_value = principal * (1 + rate/n)**(n * years)
            total_interest = future_value - principal
            
            response += f"{compound_name} Bileşik:\n"
            response += f"   Gelecek Değer: {future_value:,.0f} TL\n"
            response += f"   Toplam Faiz: {total_interest:,.0f} TL\n"
            response += f"   Getiri: %{(total_interest/principal*100):.1f}\n\n"
        
        # Enflasyon etkisi
        inflation_rate = 0.20  # %20 varsayılan enflasyon
        real_rate = (1 + rate) / (1 + inflation_rate) - 1
        real_future_value = principal * (1 + real_rate)**years
        
        response += f"📉 ENFLASYON ETKİSİ (%{inflation_rate*100:.0f}):\n"
        response += f"   Reel Getiri Oranı: %{real_rate*100:.1f}\n"
        response += f"   Reel Gelecek Değer: {real_future_value:,.0f} TL\n"
        response += f"   Alım Gücü Kaybı: {future_value - real_future_value:,.0f} TL\n"
        
        return response
    
    def _handle_general_calculation(self, question: str) -> str:
        """Genel hesaplama soruları"""
        response = f"\n🧮 MATEMATİKSEL HESAPLAMA YARDIMI\n"
        response += f"{'='*40}\n\n"
        
        response += f"📋 YAPABILECEĞIM HESAPLAMALAR:\n\n"
        
        response += f"1️⃣ AYLIK YATIRIM HESABI:\n"
        response += f"   Örnek: '100 TL aylık yatırımla 10 yılda ne kadar birikir?'\n\n"
        
        response += f"2️⃣ PORTFÖY DAĞITIMI:\n"
        response += f"   Örnek: '500000 TL'yi 3 fona böl'\n\n"
        
        response += f"3️⃣ HEDEF TUTAR:\n"
        response += f"   Örnek: '1 milyon TL için 5 yılda ne kadar yatırmalıyım?'\n\n"
        
        response += f"4️⃣ BİLEŞİK FAİZ:\n"
        response += f"   Örnek: '10000 TL %25 faizle 5 yılda ne olur?'\n\n"
        
        response += f"💡 İPUCU: Sorunuzda tutarları ve süreleri net belirtin!\n"
        
        return response
    
    # Yardımcı metodlar
    def _calculate_future_value_monthly(self, pmt: float, rate: float, periods: int) -> float:
        """Aylık düzenli yatırım için gelecek değer hesaplama"""
        if rate == 0:
            return pmt * periods
        return pmt * ((1 + rate)**periods - 1) / rate
    
    def _monte_carlo_monthly_investment(self, monthly_amount: float, annual_return: float, 
                                    volatility: float, months: int, simulations: int = 1000) -> Dict:
        """Monte Carlo simülasyonu ile aylık yatırım tahmini"""
        results = []
        monthly_return = annual_return / 12
        monthly_vol = volatility / np.sqrt(12)
        
        # Makul sınırlar koy
        monthly_return = np.clip(monthly_return, -0.10, 0.10)  # Aylık %10 sınırı
        monthly_vol = np.clip(monthly_vol, 0.01, 0.20)  # Aylık volatilite sınırı
        
        for _ in range(simulations):
            total_value = 0
            for month in range(months):
                # Her ay için random getiri
                random_return = np.random.normal(monthly_return, monthly_vol)
                
                # Aşırı değerleri sınırla
                random_return = np.clip(random_return, -0.50, 0.50)  # Aylık %50 kayıp/kazanç sınırı
                
                # Mevcut birikime getiri ekle
                total_value = total_value * (1 + random_return) + monthly_amount
            
            results.append(total_value)
        
        # Sonuçları temizle
        results = [r for r in results if r > 0 and not np.isnan(r) and not np.isinf(r)]
        
        if not results:
            # Fallback değerler
            basic_value = monthly_amount * months * (1 + annual_return) ** (months/12)
            return {
                'expected': basic_value,
                'std': basic_value * 0.1,
                'percentile_10': basic_value * 0.8,
                'percentile_90': basic_value * 1.2,
                'min': basic_value * 0.7,
                'max': basic_value * 1.3
            }
        
        return {
            'expected': np.mean(results),
            'std': np.std(results),
            'percentile_10': np.percentile(results, 10),
            'percentile_90': np.percentile(results, 90),
            'min': np.min(results),
            'max': np.max(results)
        }    
    def _conservative_distribution(self, total_amount: float, fund_count: int) -> Dict:
        """Muhafazakar portföy dağıtımı"""
        if fund_count >= 3:
            return {
                'allocations': [
                    {
                        'type': 'Para Piyasası Fonu',
                        'amount': total_amount * 0.4,
                        'percentage': 40,
                        'expected_return': 20,
                        'fund_suggestions': self._get_fund_suggestions('para piyasası', 3)
                    },
                    {
                        'type': 'Borçlanma Araçları Fonu',
                        'amount': total_amount * 0.4,
                        'percentage': 40,
                        'expected_return': 25,
                        'fund_suggestions': self._get_fund_suggestions('borçlanma', 3)
                    },
                    {
                        'type': 'Hisse Senedi Fonu',
                        'amount': total_amount * 0.2,
                        'percentage': 20,
                        'expected_return': 35,
                        'fund_suggestions': self._get_fund_suggestions('hisse', 3)
                    }
                ]
            }
        else:
            # 2 fon için
            return {
                'allocations': [
                    {
                        'type': 'Para Piyasası Fonu',
                        'amount': total_amount * 0.6,
                        'percentage': 60,
                        'expected_return': 20,
                        'fund_suggestions': self._get_fund_suggestions('para piyasası', 2)
                    },
                    {
                        'type': 'Dengeli Fon',
                        'amount': total_amount * 0.4,
                        'percentage': 40,
                        'expected_return': 30,
                        'fund_suggestions': self._get_fund_suggestions('dengeli', 2)
                    }
                ]
            }
    
    def _balanced_distribution(self, total_amount: float, fund_count: int) -> Dict:
        """Dengeli portföy dağıtımı"""
        if fund_count >= 3:
            return {
                'allocations': [
                    {
                        'type': 'Borçlanma Araçları Fonu',
                        'amount': total_amount * 0.3,
                        'percentage': 30,
                        'expected_return': 25,
                        'fund_suggestions': self._get_fund_suggestions('borçlanma', 3)
                    },
                    {
                        'type': 'Hisse Senedi Fonu',
                        'amount': total_amount * 0.4,
                        'percentage': 40,
                        'expected_return': 35,
                        'fund_suggestions': self._get_fund_suggestions('hisse', 3)
                    },
                    {
                        'type': 'Altın/Döviz Fonu',
                        'amount': total_amount * 0.3,
                        'percentage': 30,
                        'expected_return': 30,
                        'fund_suggestions': self._get_fund_suggestions('altın', 3)
                    }
                ]
            }
        else:
            return {
                'allocations': [
                    {
                        'type': 'Dengeli Fon',
                        'amount': total_amount * 0.5,
                        'percentage': 50,
                        'expected_return': 30,
                        'fund_suggestions': self._get_fund_suggestions('dengeli', 2)
                    },
                    {
                        'type': 'Hisse Senedi Fonu',
                        'amount': total_amount * 0.5,
                        'percentage': 50,
                        'expected_return': 35,
                        'fund_suggestions': self._get_fund_suggestions('hisse', 2)
                    }
                ]
            }

    def _aggressive_distribution(self, total_amount: float, fund_count: int) -> Dict:
        """Agresif portföy dağıtımı"""
        if fund_count >= 3:
            return {
                'allocations': [
                    {
                        'type': 'Hisse Senedi Fonu',
                        'amount': total_amount * 0.6,
                        'percentage': 60,
                        'expected_return': 40,
                        'fund_suggestions': self._get_fund_suggestions('hisse', 3)
                    },
                    {
                        'type': 'Teknoloji Sektör Fonu',
                        'amount': total_amount * 0.25,
                        'percentage': 25,
                        'expected_return': 45,
                        'fund_suggestions': self._get_fund_suggestions('teknoloji', 3)
                    },
                    {
                        'type': 'Gelişen Piyasalar Fonu',
                        'amount': total_amount * 0.15,
                        'percentage': 15,
                        'expected_return': 35,
                        'fund_suggestions': self._get_fund_suggestions('gelişen', 3)
                    }
                ]
            }
        else:
            return {
                'allocations': [
                    {
                        'type': 'Hisse Senedi Fonu',
                        'amount': total_amount * 0.8,
                        'percentage': 80,
                        'expected_return': 40,
                        'fund_suggestions': self._get_fund_suggestions('hisse', 2)
                    },
                    {
                        'type': 'Sektör/Tema Fonu',
                        'amount': total_amount * 0.2,
                        'percentage': 20,
                        'expected_return': 45,
                        'fund_suggestions': self._get_fund_suggestions('sektör', 2)
                    }
                ]
            }

    
    def _get_fund_suggestions(self, fund_type: str, count: int = 3) -> List[str]:
        """Belirli tip için fon önerileri"""
        suggestions = []
        
        for fcode in self.active_funds[:30]:
            try:
                details = self.coordinator.db.get_fund_details(fcode)
                if details:
                    fund_name = details.get('fund_name', '').lower()
                    fund_category = details.get('fund_category', '').lower()
                    
                    if fund_type in fund_name or fund_type in fund_category:
                        suggestions.append(fcode)
                        
                    if len(suggestions) >= count:
                        break
                        
            except:
                continue
        
        return suggestions
    
    def _get_real_fund_suggestions(self, fund_count: int) -> str:
        """Gerçek fon önerileri"""
        response = f"🏆 GERÇEK FON ÖNERİLERİ:\n"
        response += f"{'='*30}\n\n"
        
        # En iyi performans gösteren fonları bul
        top_funds = []
        
        for fcode in self.active_funds[:20]:
            try:
                data = self.coordinator.db.get_fund_price_history(fcode, 60)
                
                if len(data) >= 30:
                    prices = data.set_index('pdate')['price'].sort_index()
                    returns = prices.pct_change().dropna()
                    
                    annual_return = (prices.iloc[-1] / prices.iloc[0]) ** (252/len(prices)) - 1
                    volatility = returns.std() * np.sqrt(252)
                    sharpe = (annual_return - 0.15) / volatility if volatility > 0 else 0
                    
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                    
                    top_funds.append({
                        'fcode': fcode,
                        'name': fund_name,
                        'annual_return': annual_return,
                        'volatility': volatility,
                        'sharpe': sharpe
                    })
                    
            except:
                continue
        
        if top_funds:
            # Sharpe oranına göre sırala
            top_funds.sort(key=lambda x: x['sharpe'], reverse=True)
            
            for i, fund in enumerate(top_funds[:fund_count], 1):
                response += f"{i}. {fund['fcode']}\n"
                response += f"   Yıllık Getiri: %{fund['annual_return']*100:.1f}\n"
                response += f"   Risk: %{fund['volatility']*100:.1f}\n"
                response += f"   Sharpe: {fund['sharpe']:.2f}\n\n"
        
        return response
    
    def _calculate_required_investment_real_funds(self, target: float, years: float) -> str:
        """Gerçek fon performanslarına dayalı gerekli yatırım hesaplama"""
        response = ""
        
        # En iyi performans gösteren fonları analiz et
        fund_returns = []
        
        for fcode in self.active_funds[:15]:
            try:
                data = self.coordinator.db.get_fund_price_history(fcode, 252)
                
                if len(data) >= 200:
                    prices = data.set_index('pdate')['price'].sort_index()
                    annual_return = (prices.iloc[-1] / prices.iloc[0]) ** (252/len(prices)) - 1
                    
                    if annual_return > 0:
                        fund_returns.append(annual_return)
                        
            except:
                continue
        
        if fund_returns:
            avg_return = np.mean(fund_returns)
            min_return = np.min(fund_returns)
            max_return = np.max(fund_returns)
            
            response += f"\n📊 {len(fund_returns)} Fon Analizi Sonucu:\n"
            response += f"   Ortalama Yıllık Getiri: %{avg_return*100:.1f}\n"
            response += f"   En Düşük: %{min_return*100:.1f}\n"
            response += f"   En Yüksek: %{max_return*100:.1f}\n\n"
            
            # Ortalama getiri ile hesapla
            monthly_rate = avg_return / 12
            months = int(years * 12)
            
            if monthly_rate > 0:
                required_monthly = target * monthly_rate / ((1 + monthly_rate)**months - 1)
                response += f"💰 Gerçek Fon Ortalamasına Göre:\n"
                response += f"   Gerekli Aylık Yatırım: {required_monthly:,.0f} TL\n"
                response += f"   Toplam Yatırım: {required_monthly * months:,.0f} TL\n"
        
        return response