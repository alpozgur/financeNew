# scenario_analysis.py
"""
Senaryo Analizi Modülü - What-if senaryoları için analiz
Enflasyon, kur, borsa çöküşü gibi senaryolarda fon önerileri
GERÇEK FON VERİLERİ İLE ÇALIŞIR
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import re

class ScenarioAnalyzer:
    """Senaryo bazlı analiz ve öneriler - Gerçek fon verileriyle"""
    
    def __init__(self, coordinator, active_funds):
        self.coordinator = coordinator
        self.active_funds = active_funds
        self.db = coordinator.db
        
        # Senaryo tanımlamaları
        self.scenario_keywords = {
            'inflation': ['enflasyon', 'inflation', 'tüfe', 'üfe'],
            'stock_crash': ['borsa düş', 'borsa çök', 'stock crash', 'bist düş'],
            'recession': ['resesyon', 'recession', 'durgunluk', 'kriz'],
            'currency': ['dolar', 'euro', 'kur', 'döviz', 'fx', 'currency']
        }
        
        # Yatırım alanı kolonları (tefasfunddetails'den)
        self.investment_columns = {
            'gold': ['preciousmetals', 'preciousmetalskba', 'preciousmetalskks'],
            'equity': ['stock', 'foreignequity'],
            'fx': ['foreigncurrencybills', 'eurobonds', 'foreigndebtinstruments', 
                   'foreigndomesticdebtinstruments', 'foreignprivatesectordebtinstruments'],
            'bond': ['governmentbond', 'governmentbondsandbillsfx', 'treasurybill',
                     'governmentleasecertificates', 'privatesectorbond'],
            'money_market': ['reverserepo', 'repo', 'termdeposit', 'termdeposittl']
        }
    
    def is_scenario_question(self, question):
        """Senaryo sorusu mu kontrolü"""
        question_lower = question.lower()
        
        # Senaryo anahtar kelimeleri
        scenario_indicators = ['olursa', 'durumunda', 'senaryosu', 'eğer', 'what if', 
                              'durumda', 'halinde', 'ihtimalinde']
        
        # Senaryo tipi kontrolü
        has_scenario_keyword = any(keyword in question_lower for keyword in scenario_indicators)
        
        # Spesifik senaryo kontrolü
        has_specific_scenario = any(
            any(keyword in question_lower for keyword in keywords)
            for keywords in self.scenario_keywords.values()
        )
        
        return has_scenario_keyword or has_specific_scenario
    
    def analyze_scenario_question(self, question):
        """Senaryo sorusunu analiz et ve yanıtla"""
        question_lower = question.lower()
        
        # Enflasyon senaryosu
        if any(keyword in question_lower for keyword in self.scenario_keywords['inflation']):
            return self._analyze_inflation_scenario(question)
        
        # Borsa çöküşü senaryosu
        elif any(keyword in question_lower for keyword in self.scenario_keywords['stock_crash']):
            return self._analyze_stock_crash_scenario(question)
        
        # Resesyon senaryosu
        elif any(keyword in question_lower for keyword in self.scenario_keywords['recession']):
            return self._analyze_recession_scenario(question)
        
        # Döviz/Kur senaryosu
        elif any(keyword in question_lower for keyword in self.scenario_keywords['currency']):
            return self._analyze_currency_scenario(question)
        
        else:
            return self._general_scenario_analysis(question)
    
    def _analyze_inflation_scenario(self, question):
        """Enflasyon senaryosu analizi - GERÇEK FONLARLA"""
        print("📊 Enflasyon senaryosu analiz ediliyor...")
        
        # Enflasyon oranını çıkar
        inflation_rate = self._extract_percentage(question, default=50)
        
        response = f"\n💹 ENFLASYON SENARYOSU ANALİZİ - %{inflation_rate}\n"
        response += f"{'='*60}\n\n"
        response += f"🎯 Senaryo: Yıllık enflasyon %{inflation_rate} olması durumu\n\n"
        
        # GERÇEK FON ANALİZİ
        inflation_funds = self._analyze_funds_for_inflation()
        
        if inflation_funds['gold_funds']:
            response += f"🥇 ALTIN/KIYMETLİ MADEN FONLARI (En İyi Koruma):\n\n"
            for i, fund in enumerate(inflation_funds['gold_funds'][:5], 1):
                response += f"{i}. {fund['fcode']} - {fund['fname'][:40]}...\n"
                response += f"   📈 30 gün getiri: %{fund['return_30d']:.2f}\n"
                response += f"   📊 Volatilite: %{fund['volatility']:.2f}\n"
                response += f"   💰 Güncel fiyat: {fund['current_price']:.4f} TL\n"
                response += f"   🥇 Kıymetli maden oranı: %{fund['gold_ratio']:.1f}\n"
                response += f"   👥 Yatırımcı: {fund['investors']:,}\n"
                response += f"   🎯 Tavsiye: Enflasyon koruması için ideal\n\n"
        
        if inflation_funds['equity_funds']:
            response += f"\n📈 HİSSE SENEDİ AĞIRLIKLI FONLAR (Reel Varlık):\n\n"
            for i, fund in enumerate(inflation_funds['equity_funds'][:5], 1):
                response += f"{i}. {fund['fcode']} - {fund['fname'][:40]}...\n"
                response += f"   📈 30 gün getiri: %{fund['return_30d']:.2f}\n"
                response += f"   📊 Sharpe: {fund['sharpe']:.3f}\n"
                response += f"   💰 Güncel fiyat: {fund['current_price']:.4f} TL\n"
                response += f"   📊 Hisse oranı: %{fund['equity_ratio']:.1f}\n"
                response += f"   🎯 Tavsiye: Uzun vadede enflasyonu yener\n\n"
        
        if inflation_funds['fx_funds']:
            response += f"\n💱 DÖVİZ/EUROBOND AĞIRLIKLI FONLAR (Kur Koruması):\n\n"
            for i, fund in enumerate(inflation_funds['fx_funds'][:5], 1):
                response += f"{i}. {fund['fcode']} - {fund['fname'][:40]}...\n"
                response += f"   📈 30 gün getiri: %{fund['return_30d']:.2f}\n"
                response += f"   💰 Güncel fiyat: {fund['current_price']:.4f} TL\n"
                response += f"   💱 Döviz varlık oranı: %{fund['fx_ratio']:.1f}\n"
                response += f"   🎯 Tavsiye: TL değer kaybına karşı koruma\n\n"
        
        # PORTFÖY ÖNERİSİ
        response += f"\n💼 %{inflation_rate} ENFLASYON İÇİN ÖRNEK PORTFÖY:\n"
        response += f"{'='*50}\n\n"
        
        portfolio = self._create_inflation_portfolio(inflation_funds, inflation_rate)
        total_weight = 0
        
        for item in portfolio:
            response += f"• {item['fcode']} - %{item['weight']}\n"
            response += f"  {item['reason']}\n\n"
            total_weight += item['weight']
        
        # PERFORMANS TAHMİNİ
        response += f"\n📊 PORTFÖY PERFORMANS TAHMİNİ:\n"
        estimated_return = self._estimate_portfolio_return(portfolio, inflation_rate)
        response += f"   Beklenen Nominal Getiri: %{estimated_return['nominal']:.1f}\n"
        response += f"   Enflasyon Sonrası Reel Getiri: %{estimated_return['real']:.1f}\n"
        
        # RİSK UYARILARI
        response += f"\n⚠️ ÖNEMLİ UYARILAR:\n"
        response += f"   • Bu tahminler geçmiş verilere dayanır\n"
        response += f"   • %{inflation_rate} enflasyon çok yüksek - ekonomik belirsizlik artar\n"
        response += f"   • Portföyü aylık gözden geçirin\n"
        response += f"   • Yatırım tavsiyesi değildir\n"
        
        return response
    
    def _analyze_stock_crash_scenario(self, question):
        """Borsa çöküşü senaryosu - GERÇEK FONLARLA"""
        print("📉 Borsa çöküşü senaryosu analiz ediliyor...")
        
        crash_rate = self._extract_percentage(question, default=30)
        
        response = f"\n📉 BORSA ÇÖKÜŞÜ SENARYOSU - %{crash_rate} DÜŞÜŞ\n"
        response += f"{'='*60}\n\n"
        
        # Defansif fonları analiz et
        defensive_funds = self._analyze_defensive_funds()
        
        if defensive_funds['money_market']:
            response += f"💵 PARA PİYASASI FONLARI (En Güvenli):\n\n"
            for i, fund in enumerate(defensive_funds['money_market'][:5], 1):
                response += f"{i}. {fund['fcode']} - {fund['fname'][:40]}...\n"
                response += f"   📊 Volatilite: %{fund['volatility']:.3f} (çok düşük)\n"
                response += f"   📈 Stabil getiri: %{fund['return_30d']:.2f}\n"
                response += f"   💰 Fiyat: {fund['current_price']:.4f} TL\n"
                response += f"   🔄 Ters repo oranı: %{fund['repo_ratio']:.1f}\n"
                response += f"   🛡️ Güvenlik: ⭐⭐⭐⭐⭐\n\n"
        
        if defensive_funds['bond_funds']:
            response += f"\n📋 BORÇLANMA ARAÇLARI FONLARI:\n\n"
            for i, fund in enumerate(defensive_funds['bond_funds'][:5], 1):
                response += f"{i}. {fund['fcode']} - {fund['fname'][:40]}...\n"
                response += f"   📊 Volatilite: %{fund['volatility']:.2f}\n"
                response += f"   📈 30 gün getiri: %{fund['return_30d']:.2f}\n"
                response += f"   📊 Devlet tahvili oranı: %{fund['bond_ratio']:.1f}\n"
                response += f"   🛡️ Güvenlik: ⭐⭐⭐⭐\n\n"
        
        # KRİZ PORTFÖYÜ
        response += f"\n💼 %{crash_rate} DÜŞÜŞ İÇİN KRİZ PORTFÖYÜ:\n"
        response += f"{'='*50}\n\n"
        
        crisis_portfolio = self._create_crisis_portfolio(defensive_funds, crash_rate)
        
        for item in crisis_portfolio:
            response += f"• {item['fcode']} - %{item['weight']}\n"
            response += f"  {item['reason']}\n"
            response += f"  Beklenen kayıp: %{item['expected_loss']:.1f}\n\n"
        
        # STRATEJİK ÖNERİLER
        response += f"\n📋 KRİZ YÖNETİM STRATEJİSİ:\n"
        response += f"   1. Hemen panik satış yapmayın\n"
        response += f"   2. Yukarıdaki defansif fonlara geçiş yapın\n"
        response += f"   3. %{crash_rate} düşüş sonrası kademeli alım planlayın\n"
        response += f"   4. Nakit oranını %20-30'a çıkarın\n"
        
        return response
    
    def _analyze_currency_scenario(self, question):
        """Döviz senaryosu - GERÇEK DÖVİZ FONLARI İLE"""
        print("💱 Döviz/Kur senaryosu analiz ediliyor...")
        
        currency_level = self._extract_currency_level(question)
        
        response = f"\n💱 DÖVİZ/KUR SENARYOSU ANALİZİ\n"
        response += f"{'='*50}\n\n"
        
        if currency_level:
            response += f"🎯 Senaryo: Dolar = {currency_level} TL durumu\n\n"
        
        # Gerçek döviz fonlarını analiz et
        fx_funds = self._analyze_fx_funds()
        
        if fx_funds['high_fx']:
            response += f"💵 YÜKSEK DÖVİZ İÇERİKLİ FONLAR:\n\n"
            for i, fund in enumerate(fx_funds['high_fx'][:5], 1):
                response += f"{i}. {fund['fcode']} - {fund['fname'][:40]}...\n"
                response += f"   📈 30 gün getiri: %{fund['return_30d']:.2f}\n"
                response += f"   💰 Fiyat: {fund['current_price']:.4f} TL\n"
                response += f"   💱 Toplam döviz içeriği: %{fund['total_fx']:.1f}\n"
                response += f"   📊 Detay: Eurobond %{fund['eurobond']:.1f}, Döviz %{fund['fx_bills']:.1f}\n"
                response += f"   🎯 Dolar koruması sağlar\n\n"
        
        if fx_funds['mixed']:
            response += f"\n🌐 KARMA FON ÖNERİLERİ:\n\n"
            for i, fund in enumerate(fx_funds['mixed'][:3], 1):
                response += f"{i}. {fund['fcode']} - {fund['fname'][:40]}...\n"
                response += f"   📈 30 gün getiri: %{fund['return_30d']:.2f}\n"
                response += f"   💰 Fiyat: {fund['current_price']:.4f} TL\n"
                response += f"   📊 Döviz %{fund['total_fx']:.1f}, Hisse %{fund['equity']:.1f}, Tahvil %{fund['bond']:.1f}\n"
                response += f"   🎯 Dengeli koruma\n\n"
        
        # DÖVİZ PORTFÖYÜ ÖNERİSİ
        response += f"\n💼 KUR RİSKİ YÖNETİM PORTFÖYÜ:\n"
        response += f"{'='*45}\n\n"
        
        fx_portfolio = self._create_fx_portfolio(fx_funds, currency_level)
        
        for item in fx_portfolio:
            response += f"• {item['fcode']} - %{item['weight']}\n"
            response += f"  {item['reason']}\n\n"
        
        return response
    
    def _analyze_funds_for_inflation(self):
        """Enflasyona dayanıklı gerçek fonları bul ve analiz et"""
        result = {
            'gold_funds': [],
            'equity_funds': [],
            'fx_funds': []
        }
        
        try:
            # TÜM FONLARIN DETAYLARINI ÇEK
            all_details_query = """
            SELECT 
                d.*,
                lf.price as current_price,
                lf.investorcount,
                lf.ftitle as fname,
                pm.annual_return / 252 * 30 as return_30d,
                pm.annual_volatility * 100 as volatility,
                pm.sharpe_ratio as sharpe
            FROM tefasfunddetails d
            JOIN mv_latest_fund_data lf ON d.fcode = lf.fcode
            LEFT JOIN mv_fund_performance_metrics pm ON d.fcode = pm.fcode
            WHERE pm.fcode IS NOT NULL
            """            
            all_funds_data = self.db.execute_query(all_details_query)
            
            for _, fund in all_funds_data.iterrows():
                fcode = fund['fcode']
                
                # Kıymetli maden oranını hesapla
                gold_ratio = 0
                for col in self.investment_columns['gold']:
                    if col in fund and pd.notna(fund[col]):
                        gold_ratio += float(fund[col])
                
                # Hisse senedi oranını hesapla
                equity_ratio = 0
                for col in self.investment_columns['equity']:
                    if col in fund and pd.notna(fund[col]):
                        equity_ratio += float(fund[col])
                
                # Döviz oranını hesapla
                fx_ratio = 0
                for col in self.investment_columns['fx']:
                    if col in fund and pd.notna(fund[col]):
                        fx_ratio += float(fund[col])
                
                # Performans hesapla
                hist_data = self.db.get_fund_price_history(fcode, 30)
                if len(hist_data) >= 10:
                    returns = hist_data['price'].pct_change().dropna()
                    volatility = returns.std() * 100
                    return_30d = (hist_data['price'].iloc[-1] / hist_data['price'].iloc[0] - 1) * 100
                    
                    # 60 günlük veri varsa Sharpe hesapla
                    if len(hist_data) >= 60:
                        annual_return = (hist_data['price'].iloc[-1] / hist_data['price'].iloc[0] - 1) * (252/len(hist_data)) * 100
                        annual_vol = volatility * np.sqrt(252/30)
                        sharpe = (annual_return - 15) / annual_vol if annual_vol > 0 else 0
                    else:
                        sharpe = 0
                    
                    # Kategorilere göre ayır
                    if gold_ratio > 20:  # %20'den fazla kıymetli maden
                        result['gold_funds'].append({
                            'fcode': fcode,
                            'fname': fund['fname'] or f'Fon {fcode}',
                            'current_price': float(fund['current_price']),
                            'investors': int(fund['investorcount']) if pd.notna(fund['investorcount']) else 0,
                            'return_30d': return_30d,
                            'volatility': volatility,
                            'gold_ratio': gold_ratio
                        })
                    
                    if equity_ratio > 50:  # %50'den fazla hisse
                        result['equity_funds'].append({
                            'fcode': fcode,
                            'fname': fund['fname'] or f'Fon {fcode}',
                            'current_price': float(fund['current_price']),
                            'return_30d': return_30d,
                            'sharpe': sharpe,
                            'equity_ratio': equity_ratio
                        })
                    
                    if fx_ratio > 30:  # %30'dan fazla döviz varlık
                        result['fx_funds'].append({
                            'fcode': fcode,
                            'fname': fund['fname'] or f'Fon {fcode}',
                            'current_price': float(fund['current_price']),
                            'return_30d': return_30d,
                            'fx_ratio': fx_ratio
                        })
            
            # Sonuçları sırala
            result['gold_funds'].sort(key=lambda x: x['gold_ratio'], reverse=True)
            result['equity_funds'].sort(key=lambda x: x['sharpe'], reverse=True)
            result['fx_funds'].sort(key=lambda x: x['return_30d'], reverse=True)
            
        except Exception as e:
            print(f"Enflasyon fon analizi hatası: {e}")
        
        return result
    
    def _analyze_defensive_funds(self):
        """Defansif fonları analiz et"""
        result = {
            'money_market': [],
            'bond_funds': []
        }
        
        try:
            # Tüm fon detaylarını çek
            query = """
            SELECT DISTINCT ON (d.fcode) 
                d.*,
                f.price as current_price,
                f.ftitle as fname
            FROM tefasfunddetails d
            JOIN tefasfunds f ON d.fcode = f.fcode
            WHERE f.pdate >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY d.fcode, f.pdate DESC
            """
            
            all_funds = self.db.execute_query(query)
            
            for _, fund in all_funds.iterrows():
                fcode = fund['fcode']
                
                # Para piyasası oranını hesapla (repo, ters repo, vadeli mevduat)
                money_market_ratio = 0
                for col in self.investment_columns['money_market']:
                    if col in fund and pd.notna(fund[col]):
                        money_market_ratio += float(fund[col])
                
                # Tahvil oranını hesapla
                bond_ratio = 0
                for col in self.investment_columns['bond']:
                    if col in fund and pd.notna(fund[col]):
                        bond_ratio += float(fund[col])
                
                # Performans hesapla
                hist_data = self.db.get_fund_price_history(fcode, 30)
                if len(hist_data) >= 10:
                    returns = hist_data['price'].pct_change().dropna()
                    volatility = returns.std() * 100
                    return_30d = (hist_data['price'].iloc[-1] / hist_data['price'].iloc[0] - 1) * 100
                    
                    # Para piyasası fonları (düşük volatilite + yüksek para piyasası oranı)
                    if money_market_ratio > 50 and volatility < 1:
                        result['money_market'].append({
                            'fcode': fcode,
                            'fname': fund['fname'] or f'Fon {fcode}',
                            'current_price': float(fund['current_price']),
                            'volatility': volatility,
                            'return_30d': return_30d,
                            'repo_ratio': float(fund.get('reverserepo', 0)) if 'reverserepo' in fund else 0
                        })
                    
                    # Tahvil fonları
                    if bond_ratio > 50 and volatility < 5:
                        result['bond_funds'].append({
                            'fcode': fcode,
                            'fname': fund['fname'] or f'Fon {fcode}',
                            'current_price': float(fund['current_price']),
                            'volatility': volatility,
                            'return_30d': return_30d,
                            'bond_ratio': bond_ratio
                        })
            
            # Volatiliteye göre sırala (düşük = iyi)
            result['money_market'].sort(key=lambda x: x['volatility'])
            result['bond_funds'].sort(key=lambda x: x['volatility'])
            
        except Exception as e:
            print(f"Defansif fon analizi hatası: {e}")
        
        return result
    
    def _analyze_fx_funds(self):
        """Döviz fonlarını analiz et"""
        result = {
            'high_fx': [],
            'mixed': []
        }
        
        try:
            query = """
            SELECT DISTINCT ON (d.fcode) 
                d.*,
                f.price as current_price,
                f.ftitle as fname
            FROM tefasfunddetails d
            JOIN tefasfunds f ON d.fcode = f.fcode
            WHERE f.pdate >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY d.fcode, f.pdate DESC
            """
            
            all_funds = self.db.execute_query(query)
            
            for _, fund in all_funds.iterrows():
                fcode = fund['fcode']
                
                # Döviz içeriği hesapla
                total_fx = 0
                eurobond = float(fund.get('eurobonds', 0)) if 'eurobonds' in fund and pd.notna(fund['eurobonds']) else 0
                fx_bills = float(fund.get('foreigncurrencybills', 0)) if 'foreigncurrencybills' in fund and pd.notna(fund['foreigncurrencybills']) else 0
                
                for col in self.investment_columns['fx']:
                    if col in fund and pd.notna(fund[col]):
                        total_fx += float(fund[col])
                
                # Diğer varlıklar
                equity = 0
                for col in self.investment_columns['equity']:
                    if col in fund and pd.notna(fund[col]):
                        equity += float(fund[col])
                
                bond = 0
                for col in self.investment_columns['bond']:
                    if col in fund and pd.notna(fund[col]):
                        bond += float(fund[col])
                
                # Performans
                hist_data = self.db.get_fund_price_history(fcode, 30)
                if len(hist_data) >= 10 and total_fx > 0:
                    return_30d = (hist_data['price'].iloc[-1] / hist_data['price'].iloc[0] - 1) * 100
                    
                    fund_info = {
                        'fcode': fcode,
                        'fname': fund['fname'] or f'Fon {fcode}',
                        'current_price': float(fund['current_price']),
                        'return_30d': return_30d,
                        'total_fx': total_fx,
                        'eurobond': eurobond,
                        'fx_bills': fx_bills,
                        'equity': equity,
                        'bond': bond
                    }
                    
                    if total_fx > 60:  # %60'tan fazla döviz
                        result['high_fx'].append(fund_info)
                    elif total_fx > 20:  # Karma fonlar
                        result['mixed'].append(fund_info)
            
            # Performansa göre sırala
            result['high_fx'].sort(key=lambda x: x['total_fx'], reverse=True)
            result['mixed'].sort(key=lambda x: x['return_30d'], reverse=True)
            
        except Exception as e:
            print(f"Döviz fon analizi hatası: {e}")
        
        return result
    
    def _create_inflation_portfolio(self, funds_data, inflation_rate):
        """Enflasyon senaryosuna göre portföy oluştur"""
        portfolio = []
        
        # Yüksek enflasyonda agresif koruma
        if inflation_rate >= 50:
            # Altın ağırlıklı
            if funds_data['gold_funds']:
                portfolio.append({
                    'fcode': funds_data['gold_funds'][0]['fcode'],
                    'weight': 30,
                    'reason': f"En yüksek altın içeriği (%{funds_data['gold_funds'][0]['gold_ratio']:.1f}) - güçlü enflasyon koruması"
                })
                if len(funds_data['gold_funds']) > 1:
                    portfolio.append({
                        'fcode': funds_data['gold_funds'][1]['fcode'],
                        'weight': 20,
                        'reason': 'İkinci altın fonu - çeşitlendirme'
                    })
            
            # Hisse senedi
            if funds_data['equity_funds']:
                portfolio.append({
                    'fcode': funds_data['equity_funds'][0]['fcode'],
                    'weight': 25,
                    'reason': f'En yüksek Sharpe oranlı ({funds_data["equity_funds"][0]["sharpe"]:.2f}) hisse fonu'
                })
            
            # Döviz
            if funds_data['fx_funds']:
                portfolio.append({
                    'fcode': funds_data['fx_funds'][0]['fcode'],
                    'weight': 25,
                    'reason': f'%{funds_data["fx_funds"][0]["fx_ratio"]:.1f} döviz içeriği - kur koruması'
                })
        else:
            # Daha dengeli yaklaşım
            if funds_data['equity_funds']:
                portfolio.append({
                    'fcode': funds_data['equity_funds'][0]['fcode'],
                    'weight': 35,
                    'reason': 'Hisse ağırlıklı - uzun vadeli enflasyon koruması'
                })
            
            if funds_data['gold_funds']:
                portfolio.append({
                    'fcode': funds_data['gold_funds'][0]['fcode'],
                    'weight': 25,
                    'reason': 'Altın - güvenli liman'
                })
            
            if funds_data['fx_funds']:
                portfolio.append({
                    'fcode': funds_data['fx_funds'][0]['fcode'],
                    'weight': 40,
                    'reason': 'Döviz ağırlıklı - dengeli koruma'
                })
        
        return portfolio
    
    def _create_crisis_portfolio(self, defensive_funds, crash_rate):
        """Kriz portföyü oluştur"""
        portfolio = []
        
        # Çöküş oranına göre agresiflik
        if crash_rate >= 40:
            # Çok defansif
            if defensive_funds['money_market']:
                best_mm = defensive_funds['money_market'][0]
                portfolio.append({
                    'fcode': best_mm['fcode'],
                    'weight': 50,
                    'reason': f'En düşük volatilite (%{best_mm["volatility"]:.3f}) - maksimum güvenlik',
                    'expected_loss': 0
                })
            
            if defensive_funds['bond_funds']:
                best_bond = defensive_funds['bond_funds'][0]
                portfolio.append({
                    'fcode': best_bond['fcode'],
                    'weight': 30,
                    'reason': f'Tahvil ağırlıklı (%{best_bond["bond_ratio"]:.1f}) - düşük risk',
                    'expected_loss': -2
                })
            
            # Altın varsa ekle
            portfolio.append({
                'fcode': 'GOLD_FUND',
                'weight': 20,
                'reason': 'Kıymetli maden fonu önerisi - kriz hedge',
                'expected_loss': 5
            })
        else:
            # Orta defansif
            if defensive_funds['money_market']:
                portfolio.append({
                    'fcode': defensive_funds['money_market'][0]['fcode'],
                    'weight': 30,
                    'reason': 'Para piyasası - güvenlik',
                    'expected_loss': 0
                })
            
            if defensive_funds['bond_funds'] and len(defensive_funds['bond_funds']) >= 2:
                portfolio.append({
                    'fcode': defensive_funds['bond_funds'][0]['fcode'],
                    'weight': 30,
                    'reason': 'Tahvil fonu 1',
                    'expected_loss': -3
                })
                portfolio.append({
                    'fcode': defensive_funds['bond_funds'][1]['fcode'],
                    'weight': 20,
                    'reason': 'Tahvil fonu 2 - çeşitlendirme',
                    'expected_loss': -3
                })
            
            portfolio.append({
                'fcode': 'BALANCED',
                'weight': 20,
                'reason': 'Dengeli/karma fon önerisi',
                'expected_loss': -10
            })
        
        return portfolio
    
    def _create_fx_portfolio(self, fx_funds, target_level):
        """Döviz portföyü oluştur"""
        portfolio = []
        
        # Yüksek döviz içerikli fonlar
        if fx_funds['high_fx']:
            best_fx = fx_funds['high_fx'][0]
            portfolio.append({
                'fcode': best_fx['fcode'],
                'weight': 40,
                'reason': f'En yüksek döviz içeriği (%{best_fx["total_fx"]:.1f}) - maksimum kur koruması'
            })
            
            if len(fx_funds['high_fx']) > 1:
                second_fx = fx_funds['high_fx'][1]
                portfolio.append({
                    'fcode': second_fx['fcode'],
                    'weight': 20,
                    'reason': f'İkinci döviz fonu (%{second_fx["total_fx"]:.1f} döviz) - çeşitlendirme'
                })
        
        # Karma fonlar
        if fx_funds['mixed']:
            best_mixed = fx_funds['mixed'][0]
            portfolio.append({
                'fcode': best_mixed['fcode'],
                'weight': 25,
                'reason': f'Dengeli fon - %{best_mixed["total_fx"]:.1f} döviz, %{best_mixed["equity"]:.1f} hisse'
            })
        
        # Bir miktar TL pozisyon
        portfolio.append({
            'fcode': 'TL_MONEY_MARKET',
            'weight': 15,
            'reason': 'TL para piyasası - likidite ihtiyacı'
        })
        
        return portfolio
    
    def _estimate_portfolio_return(self, portfolio, inflation_rate):
        """Portföy getiri tahmini"""
        # Basit tahmin modeli
        nominal_return = 0
        
        for item in portfolio:
            if 'altın' in item['reason'].lower() or 'gold' in item['reason'].lower():
                # Altın genelde enflasyonu yakalar
                nominal_return += item['weight'] * inflation_rate * 0.9 / 100
            elif 'hisse' in item['reason'].lower() or 'equity' in item['reason'].lower():
                # Hisse uzun vadede enflasyon + risk primi
                nominal_return += item['weight'] * (inflation_rate + 5) / 100
            elif 'döviz' in item['reason'].lower() or 'fx' in item['reason'].lower():
                # Döviz kur artışına bağlı
                nominal_return += item['weight'] * inflation_rate * 0.8 / 100
            else:
                # Diğerleri (tahvil, para piyasası)
                nominal_return += item['weight'] * 10 / 100
        
        real_return = nominal_return - inflation_rate
        
        return {
            'nominal': nominal_return * 100,  # Yüzde olarak
            'real': real_return
        }
    
    def _analyze_recession_scenario(self, question):
        """Resesyon senaryosu analizi"""
        print("📊 Resesyon senaryosu analiz ediliyor...")
        
        response = f"\n🔴 RESESYON SENARYOSU ANALİZİ\n"
        response += f"{'='*45}\n\n"
        response += f"🎯 Senaryo: Ekonomik resesyon/durgunluk dönemi\n\n"
        
        # Defansif fonları kullan
        defensive_funds = self._analyze_defensive_funds()
        
        response += f"🛡️ RESESYONA DAYANIKLI FONLAR:\n\n"
        
        # Para piyasası ve tahvil fonlarını birleştir
        all_defensive = []
        
        for fund in defensive_funds.get('money_market', [])[:5]:
            fund['type'] = 'Para Piyasası'
            fund['resilience'] = 'Çok Yüksek'
            all_defensive.append(fund)
        
        for fund in defensive_funds.get('bond_funds', [])[:5]:
            fund['type'] = 'Tahvil'
            fund['resilience'] = 'Yüksek'
            all_defensive.append(fund)
        
        # Volatiliteye göre sırala
        all_defensive.sort(key=lambda x: x['volatility'])
        
        for i, fund in enumerate(all_defensive[:8], 1):
            response += f"{i}. {fund['fcode']} - {fund['fname'][:35]}...\n"
            response += f"   📊 Kategori: {fund['type']}\n"
            response += f"   💪 Dayanıklılık: {fund['resilience']}\n"
            response += f"   📉 Volatilite: %{fund['volatility']:.3f}\n"
            response += f"   📈 30 gün getiri: %{fund['return_30d']:.2f}\n\n"
        
        # Portföy önerisi
        response += f"\n💼 RESESYON PORTFÖYÜ:\n"
        response += f"   • %40 Para piyasası fonları (likidite)\n"
        response += f"   • %30 Devlet tahvili fonları (güvenlik)\n"
        response += f"   • %15 Kıymetli maden fonları (hedge)\n"
        response += f"   • %15 Nakit/Likit (fırsat alımları)\n\n"
        
        response += f"🎯 STRATEJİLER:\n"
        response += f"   • Borç azaltma öncelikli\n"
        response += f"   • Acil fon miktarını artırın\n"
        response += f"   • Defansif sektörlere yönelin\n"
        response += f"   • Uzun vadeli bakış açısı\n"
        
        return response
    
    def _general_scenario_analysis(self, question):
        """Genel senaryo analizi"""
        response = f"\n🎲 GENEL SENARYO ANALİZİ\n"
        response += f"{'='*40}\n\n"
        
        response += f"📊 MEVCUT ANALİZ YETENEKLERİ:\n\n"
        
        response += f"1️⃣ ENFLASYON SENARYOLARI:\n"
        response += f"   • 'Enflasyon %50 olursa hangi fonlar korunur?'\n"
        response += f"   • Altın, hisse ve döviz fonları önerilir\n\n"
        
        response += f"2️⃣ BORSA ÇÖKÜŞÜ SENARYOLARI:\n"
        response += f"   • 'Borsa %30 düşerse portföy önerisi'\n"
        response += f"   • Para piyasası ve tahvil fonları önerilir\n\n"
        
        response += f"3️⃣ RESESYON SENARYOLARI:\n"
        response += f"   • 'Resesyon senaryosunda güvenli limanlar'\n"
        response += f"   • Defansif fonlar analiz edilir\n\n"
        
        response += f"4️⃣ DÖVİZ/KUR SENARYOLARI:\n"
        response += f"   • 'Dolar 50 TL olursa ne yapmak lazım?'\n"
        response += f"   • Döviz içerikli fonlar önerilir\n\n"
        
        response += f"💡 Spesifik bir senaryo belirtin!"
        
        return response
    
    def _extract_percentage(self, text, default=30):
        """Metinden yüzde değeri çıkar"""
        numbers = re.findall(r'%?\s*(\d+)\s*%?', text)
        if numbers:
            return int(numbers[0])
        return default
    
    def _extract_currency_level(self, text):
        """Metinden kur seviyesi çıkar"""
        patterns = [
            r'(\d+)\s*tl',
            r'(\d+)\s*₺',
            r'tl\s*(\d+)',
            r'₺\s*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))
        
        return None