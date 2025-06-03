# thematic_fund_analyzer.py
"""
TEFAS Tematik Fon Analizi Sistemi - TÜM VERİTABANI KULLANIMI (DÜZELTİLMİŞ)
Teknoloji, ESG, Enerji, Sağlık, Fintek gibi tematik fonların analizi
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
import time
import re
from datetime import datetime, timedelta
from database.connection import DatabaseManager
from config.config import Config

class ThematicFundAnalyzer:
    """Tematik fon analizi sistemi - TÜM VERİTABANI"""
    
    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.db = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 🎯 TETATİK FON KEYWORD MAPPING
        self.thematic_keywords = {
            'teknoloji': {
                'keywords': [
                    'TEKNOLOJİ', 'TECHNOLOGY', 'BİLİŞİM', 'BİLGİ TEKNOLOJİLERİ',
                    'YAZILIM', 'SOFTWARE', 'DİJİTAL', 'DIGITAL', 'BİLGİSAYAR',
                    'TELEKOM', 'TELEKOMÜNİKASYON', 'TELECOM', 'INTERNET',
                    'DONANIM', 'HARDWARE', 'SİBER', 'CYBER', 'VERİ', 'DATA',
                    'YAPAY ZEKA', 'AI', 'ROBOTIK', 'ROBOT', 'OTOMASYON'
                ],
                'description': 'Teknoloji ve bilişim sektörü fonları'
            },
            'esg': {
                'keywords': [
                    'ESG', 'SÜRDÜRÜLEBİLİRLİK', 'SUSTAINABILITY', 'YEŞİL', 'GREEN',
                    'ÇEVRE', 'ENVIRONMENTAL', 'SOSYAL', 'SOCIAL', 'YÖNETİŞİM',
                    'GOVERNANCE', 'ETİK', 'ETHICAL', 'SORUMLU', 'RESPONSIBLE',
                    'İKLİM', 'CLIMATE', 'KARBON', 'CARBON', 'TEMİZ ENERJİ',
                    'CLEAN ENERGY', 'YENİLENEBİLİR', 'RENEWABLE'
                ],
                'description': 'ESG ve sürdürülebilirlik odaklı fonlar'
            },
            'enerji': {
                'keywords': [
                    'ENERJİ', 'ENERGY', 'PETROL', 'OIL', 'GAZ', 'GAS',
                    'ELEKTRİK', 'ELECTRIC', 'GÜNEŞ', 'SOLAR', 'RÜZGAR', 'WIND',
                    'HİDROELEKTRİK', 'HYDRO', 'NÜKLEERİ', 'NUCLEAR', 'KÖMÜR',
                    'COAL', 'DOĞALGAZ', 'LNG', 'RAFİNERİ', 'REFINERY',
                    'YENİLENEBİLİR ENERJİ', 'RENEWABLE ENERGY', 'BİOYAKIT'
                ],
                'description': 'Enerji sektörü ve alt dalları fonları'
            },
            'sağlık': {
                'keywords': [
                    'SAĞLIK', 'HEALTH', 'HEALTHCARE', 'TIBBİ', 'MEDICAL',
                    'İLAÇ', 'PHARMACEUTICAL', 'PHARMA', 'BİYOTEKNOLOJİ',
                    'BIOTECH', 'HASTANE', 'HOSPITAL', 'TIBBİ CİHAZ',
                    'MEDICAL DEVICE', 'DENTAL', 'DİŞ', 'VETERİNER',
                    'VACCINE', 'AŞI', 'SAĞLIK TURİZMİ', 'HEALTH TOURISM'
                ],
                'description': 'Sağlık ve tıp sektörü fonları'
            },
            'fintek': {
                'keywords': [
                    'FİNTEK', 'FINTECH', 'BLOCKCHAIN', 'BLOKZİNCİR',
                    'KRİPTO', 'CRYPTO', 'BITCOIN', 'DİJİTAL PARA',
                    'DIGITAL CURRENCY', 'ÖDEME SİSTEMLERİ', 'PAYMENT',
                    'ONLINE BANKING', 'MOBILE BANKING', 'DİJİTAL BANKA',
                    'INSURTECH', 'REGTECH', 'WEALTHTECH', 'CROWDFUNDING',
                    'P2P', 'PEER TO PEER', 'ROBO ADVISOR'
                ],
                'description': 'Finansal teknoloji ve blockchain fonları'
            },
            'ihracat': {
                'keywords': [
                    'İHRACAT', 'EXPORT', 'İHRACATÇI', 'EXPORTER',
                    'DIŞ TİCARET', 'FOREIGN TRADE', 'ULUSLARARASI',
                    'INTERNATIONAL', 'GLOBAL', 'YURTDIŞI', 'OVERSEAS',
                    'İMALAT', 'MANUFACTURING', 'ÜRETİM', 'PRODUCTION',
                    'SANAYİ', 'INDUSTRY', 'TEKSTİL', 'TEXTILE', 'OTOMOTİV',
                    'AUTOMOTIVE', 'MAKİNE', 'MACHINERY'
                ],
                'description': 'İhracatçı şirketler ve dış ticaret fonları'
            },
            'emlak': {
                'keywords': [
                    'EMLAK', 'REAL ESTATE', 'REIT', 'GYO', 'PROPERTY',
                    'MÜLKİYET', 'İNŞAAT', 'CONSTRUCTION', 'YAPIM',
                    'BUILDING', 'KONUT', 'HOUSING', 'RESIDENTIAL',
                    'TİCARİ EMLAK', 'COMMERCIAL', 'OFFICE', 'OFİS',
                    'WAREHOUSE', 'DEPO', 'RETAIL', 'PERAKENDE'
                ],
                'description': 'Emlak ve gayrimenkul yatırım fonları'
            },
            'gıda': {
                'keywords': [
                    'GIDA', 'FOOD', 'TARIM', 'AGRICULTURE', 'AGRI',
                    'HAYVANCILIK', 'LIVESTOCK', 'SÜT', 'DAIRY', 'ET',
                    'MEAT', 'TAVUKÇULUK', 'POULTRY', 'BALIKÇILIK',
                    'FISHING', 'TOHUM', 'SEED', 'GÜBRE', 'FERTILIZER',
                    'ORGANIC', 'ORGANİK', 'FAST FOOD', 'RESTAURANT'
                ],
                'description': 'Gıda ve tarım sektörü fonları'
            },
            'turizm': {
                'keywords': [
                    'TURİZM', 'TOURISM', 'OTEL', 'HOTEL', 'HOSPITALITY',
                    'KONAKLAMA', 'ACCOMMODATION', 'SEYAHAT', 'TRAVEL',
                    'UÇAK', 'AIRLINE', 'HAVAYOLLAri', 'AIRPORT',
                    'HAVAALANÜ', 'CRUISE', 'KRUVAZİYER', 'TATİL',
                    'VACATION', 'RESORT', 'ENTERTAINMENT', 'EĞLENcE'
                ],
                'description': 'Turizm ve seyahat sektörü fonları'
            },
            'bankacılık': {
                'keywords': [
                    'BANKA', 'BANK', 'BANKING', 'FİNANS', 'FINANCE',
                    'KREDİ', 'CREDIT', 'SİGORTA', 'INSURANCE', 'HAYAT SİGORTASI',
                    'LIFE INSURANCE', 'LEASING', 'KİRALAMA', 'FACTORİNG',
                    'YATIRIM BANKASI', 'INVESTMENT BANK', 'KATILIM BANKASI',
                    'PARTICIPATION BANK', 'ASSET MANAGEMENT'
                ],
                'description': 'Bankacılık ve finansal hizmetler fonları'
            }
        }
    
    def determine_fund_type_from_portfolio(self, fcode):
        """Portföy dağılımından fon tipini belirle"""
        try:
            # En son portföy dağılımını al
            query = f"""
            SELECT * FROM tefasfunddetails 
            WHERE fcode = '{fcode}' 
            ORDER BY fdate DESC 
            LIMIT 1
            """
            
            result = self.db.execute_query(query)
            if result.empty:
                return "Bilinmeyen", "Genel"
            
            row = result.iloc[0]
            
            # Hisse oranı
            stock_ratio = float(row.get('stock', 0) or 0)
            # Yabancı hisse oranı
            foreign_equity_ratio = float(row.get('foreignequity', 0) or 0)
            # Devlet tahvili oranı  
            gov_bond_ratio = float(row.get('governmentbond', 0) or 0)
            # Özel sektör tahvili
            private_bond_ratio = float(row.get('privatesectorbond', 0) or 0)
            # Altın/kıymetli maden
            precious_metals_ratio = float(row.get('preciousmetals', 0) or 0)
            # ETF oranı
            etf_ratio = float(row.get('exchangetradedfund', 0) or 0)
            # Gayrimenkul sertifikası
            real_estate_ratio = float(row.get('realestatecertificate', 0) or 0)
            # Fon katılım belgesi
            fund_participation_ratio = float(row.get('fundparticipationcertificate', 0) or 0)
            
            total_equity = stock_ratio + foreign_equity_ratio
            total_bonds = gov_bond_ratio + private_bond_ratio
            
            # Fon tipini belirle
            if total_equity > 80:
                fund_type = "Hisse Senedi Fonu"
                if foreign_equity_ratio > stock_ratio:
                    fund_category = "Yabancı Hisse Senedi"
                else:
                    fund_category = "Yerli Hisse Senedi"
            elif total_equity > 40:
                fund_type = "Karma Fon"
                fund_category = "Esnek Karma"
            elif total_bonds > 60:
                fund_type = "Borçlanma Araçları Fonu"
                if gov_bond_ratio > private_bond_ratio:
                    fund_category = "Devlet Tahvili"
                else:
                    fund_category = "Karma Borçlanma"
            elif precious_metals_ratio > 50:
                fund_type = "Kıymetli Madenler Fonu"
                fund_category = "Altın Fonu"
            elif etf_ratio > 50:
                fund_type = "Fon Sepeti Fonu"
                fund_category = "ETF Fonu"
            elif real_estate_ratio > 50:
                fund_type = "Gayrimenkul Fonu"
                fund_category = "Emlak Sertifikası"
            elif fund_participation_ratio > 50:
                fund_type = "Fon Sepeti Fonu"
                fund_category = "Fon Portföyü"
            else:
                fund_type = "Para Piyasası Fonu"
                fund_category = "Kısa Vadeli"
            
            return fund_type, fund_category
            
        except Exception as e:
            self.logger.warning(f"Fon tipi belirlenemedi {fcode}: {e}")
            return "Bilinmeyen", "Genel"
    
    def analyze_thematic_question(self, question):
        question_lower = question.lower()

        # Öncelik: Manuel tema yakalama
        if any(word in question_lower for word in ['teknoloji', 'bilişim', 'digital', 'yazılım']):
            return self.analyze_single_theme_comprehensive('teknoloji', question)
        elif any(word in question_lower for word in ['ihracat', 'ihracatçı', 'dış ticaret']):
            return self.analyze_single_theme_comprehensive('ihracat', question)
        elif any(word in question_lower for word in ['esg', 'sürdürülebilir', 'yeşil', 'çevre']):
            return self.analyze_single_theme_comprehensive('esg', question)
        # ... diğer temalar ...

        # Sonra keyword matching ile fallback
        detected_themes = []
        for theme, data in self.thematic_keywords.items():
            for keyword in data['keywords']:
                if keyword.lower() in question_lower:
                    detected_themes.append(theme)
                    break

        if not detected_themes:
            return self._handle_general_thematic_overview()
        if len(detected_themes) == 1:
            return self.analyze_single_theme_comprehensive(detected_themes[0], question)
        return self.compare_multiple_themes(detected_themes, question)
    
    def analyze_single_theme_comprehensive(self, theme, question):
        """Tek tema için kapsamlı analiz - TÜM VERİTABANI"""
        print(f"🎯 {theme.upper()} teması analiz ediliyor (TÜM VERİTABANI)...")
        
        start_time = time.time()
        
        # 1. TETATİK FONLARI BUL
        thematic_funds = self.find_thematic_funds_sql(theme)
        
        if not thematic_funds:
            return f"❌ {theme.upper()} temasında fon bulunamadı."
        
        print(f"   📊 {len(thematic_funds)} tematik fon bulundu")
        
        # 2. PERFORMANS ANALİZİ
        performance_results = self.analyze_thematic_performance(thematic_funds, theme)
        
        if not performance_results:
            return f"❌ {theme.upper()} fonları için performans verisi hesaplanamadı."
        
        elapsed = time.time() - start_time
        print(f"   ⏱️ Analiz tamamlandı: {elapsed:.1f} saniye")
        
        # 3. SONUÇLARI FORMATLA
        return self.format_thematic_analysis_results(theme, performance_results, elapsed)
    
    def find_thematic_funds_sql(self, theme):
        """SQL ile tematik fonları bul - TÜM VERİTABANI"""
        theme_data = self.thematic_keywords.get(theme, {})
        keywords = theme_data.get('keywords', [])
        
        if not keywords:
            return []
        
        try:
            # SQL LIKE koşulları oluştur
            like_conditions = []
            for keyword in keywords:
                like_conditions.append(f"UPPER(f.ftitle) LIKE '%{keyword}%'")
            
            where_clause = " OR ".join(like_conditions)
            
            # TÜM VERİTABANI SORGUSU
            query = f"""
            WITH thematic_funds AS (
                SELECT DISTINCT f.fcode, f.ftitle as fund_name, f.fcapacity, 
                    f.investorcount, f.price, f.pdate,
                    ROW_NUMBER() OVER (PARTITION BY f.fcode ORDER BY f.pdate DESC) as rn
                FROM tefasfunds f
                WHERE ({where_clause})
                AND f.pdate >= CURRENT_DATE - INTERVAL '30 days'
                AND f.price > 0
                AND f.investorcount > 50  -- Minimum yatırımcı filtresi
            )
            SELECT fcode, fund_name, fcapacity, investorcount, price
            FROM thematic_funds 
            WHERE rn = 1
            ORDER BY fcapacity DESC NULLS LAST
            """
            
            result = self.db.execute_query(query)
            
            funds_list = []
            for _, row in result.iterrows():
                # Fon tipini portföy dağılımından belirle
                fund_type, fund_category = self.determine_fund_type_from_portfolio(row['fcode'])
                
                funds_list.append({
                    'fcode': row['fcode'],
                    'fund_name': row['fund_name'],
                    'capacity': float(row['fcapacity']) if pd.notna(row['fcapacity']) else 0,
                    'investors': int(row['investorcount']) if pd.notna(row['investorcount']) else 0,
                    'current_price': float(row['price']) if pd.notna(row['price']) else 0,
                    'fund_type': fund_type,
                    'fund_category': fund_category
                })
            
            return funds_list
            
        except Exception as e:
            print(f"   ❌ SQL sorgu hatası: {e}")
            return []
    
    def analyze_thematic_performance(self, funds_list, theme, analysis_days=180):
        """Tematik fonlar performans analizi"""
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
                    
                    # Tematik skor (tema özel)
                    thematic_score = self.calculate_thematic_score(
                        annual_return, volatility, sharpe, win_rate, theme
                    )
                    
                    fund_result = {
                        'fcode': fcode,
                        'fund_name': fund_info['fund_name'],
                        'capacity': fund_info['capacity'],
                        'investors': fund_info['investors'],
                        'fund_type': fund_info['fund_type'],
                        'fund_category': fund_info['fund_category'],
                        'current_price': fund_info['current_price'],
                        'total_return': total_return,
                        'annual_return': annual_return,
                        'volatility': volatility,
                        'sharpe_ratio': sharpe,
                        'win_rate': win_rate,
                        'max_drawdown': max_drawdown,
                        'thematic_score': thematic_score,
                        'data_points': len(prices)
                    }
                    
                    performance_results.append(fund_result)
                    successful += 1
                    
            except Exception as e:
                continue
        
        print(f"   ✅ {successful}/{len(funds_list)} fon başarıyla analiz edildi")
        return performance_results
    
    def calculate_thematic_score(self, annual_return, volatility, sharpe, win_rate, theme):
        """Tema özel skor hesaplama"""
        base_score = 0
        
        # Temel skor (0-60)
        base_score += min(max(annual_return, 0) / 50 * 30, 30)  # Getiri
        base_score += min(max(sharpe, 0) * 15, 20)  # Sharpe
        base_score += min(win_rate / 10, 10)  # Kazanma oranı
        
        # Tema özel bonus (0-40)
        if theme == 'teknoloji':
            # Teknoloji fonları için yüksek getiri bonusu
            if annual_return > 30:
                base_score += 20
            elif annual_return > 15:
                base_score += 10
                
        elif theme == 'esg':
            # ESG fonları için düşük risk bonusu
            if volatility < 15:
                base_score += 15
            if sharpe > 0.5:
                base_score += 15
                
        elif theme == 'enerji':
            # Enerji fonları volatilite toleransı
            if volatility < 25:
                base_score += 10
            if annual_return > 20:
                base_score += 20
                
        elif theme == 'sağlık':
            # Sağlık fonları için istikrar bonusu
            if win_rate > 60:
                base_score += 15
            if volatility < 20:
                base_score += 15
                
        elif theme == 'fintek':
            # Fintek için yüksek getiri toleransı
            if annual_return > 25:
                base_score += 25
            elif annual_return > 10:
                base_score += 10
                
        else:
            # Diğer temalar için genel bonus
            if sharpe > 0.3:
                base_score += 15
            if annual_return > 10:
                base_score += 15
        
        return min(max(base_score, 0), 100)
    
    def format_thematic_analysis_results(self, theme, results, analysis_time):
        """Tematik analiz sonuçlarını formatla"""
        
        # Tematik skora göre sırala
        results.sort(key=lambda x: x['thematic_score'], reverse=True)
        
        theme_data = self.thematic_keywords.get(theme, {})
        theme_description = theme_data.get('description', theme.upper())
        
        response = f"\n🎯 {theme.upper()} TEMATİK FON ANALİZİ - TÜM VERİTABANI\n"
        response += f"{'='*60}\n\n"
        
        response += f"📊 {theme_description}\n"
        response += f"🔍 Analiz Kapsamı: {len(results)} fon\n"
        response += f"⏱️ Analiz Süresi: {analysis_time:.1f} saniye\n\n"
        
        # TEMA İSTATİSTİKLERİ
        if results:
            total_capacity = sum(r['capacity'] for r in results)
            total_investors = sum(r['investors'] for r in results)
            avg_return = sum(r['annual_return'] for r in results) / len(results)
            avg_volatility = sum(r['volatility'] for r in results) / len(results)
            avg_score = sum(r['thematic_score'] for r in results) / len(results)
            
            response += f"💰 TEMA GENEL İSTATİSTİKLERİ:\n"
            response += f"   📊 Toplam Fon: {len(results)}\n"
            response += f"   💰 Toplam Varlık: {total_capacity:,.0f} TL ({total_capacity/1000000000:.1f} milyar)\n"
            response += f"   👥 Toplam Yatırımcı: {total_investors:,} kişi\n"
            response += f"   📈 Ortalama Getiri: %{avg_return:+.2f}\n"
            response += f"   📊 Ortalama Risk: %{avg_volatility:.2f}\n"
            response += f"   🎯 Ortalama Tema Skoru: {avg_score:.1f}/100\n\n"
        
        # FON TİPİ DAĞILIMI
        if results:
            fund_types = {}
            for fund in results:
                fund_type = fund['fund_type']
                if fund_type not in fund_types:
                    fund_types[fund_type] = {'count': 0, 'capacity': 0}
                fund_types[fund_type]['count'] += 1
                fund_types[fund_type]['capacity'] += fund['capacity']
            
            response += f"📋 FON TİPİ DAĞILIMI:\n"
            for fund_type, data in sorted(fund_types.items(), key=lambda x: x[1]['count'], reverse=True):
                response += f"   {fund_type}: {data['count']} fon ({data['capacity']/1000000:.0f}M TL)\n"
            response += f"\n"
        
        # EN İYİ 15 FON
        response += f"🏆 EN İYİ {min(15, len(results))} {theme.upper()} FONU (Tema Skoruna Göre):\n\n"
        
        for i, fund in enumerate(results[:15], 1):
            # Skor kategorisi
            score = fund['thematic_score']
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
            
            response += f"{i:2d}. {fund['fcode']} - {rating}\n"
            response += f"    🎯 Tema Skoru: {score:.1f}/100\n"
            response += f"    📈 Yıllık Getiri: %{fund['annual_return']:+.2f}\n"
            response += f"    ⚡ Sharpe Oranı: {fund['sharpe_ratio']:.3f}\n"
            response += f"    📊 Volatilite: %{fund['volatility']:.2f}\n"
            response += f"    🎯 Kazanma Oranı: %{fund['win_rate']:.1f}\n"
            response += f"    💰 Kapasite: {fund['capacity']:,.0f} TL\n"
            response += f"    👥 Yatırımcı: {fund['investors']:,} kişi\n"
            response += f"    🏷️ Tip: {fund['fund_type']} - {fund['fund_category']}\n"
            response += f"    📝 Adı: {fund['fund_name'][:45]}...\n"
            response += f"\n"
        
        # TEMA LİDERLERİ
        if results:
            best_return = max(results, key=lambda x: x['annual_return'])
            best_sharpe = max(results, key=lambda x: x['sharpe_ratio'])
            safest = min(results, key=lambda x: x['volatility'])
            biggest = max(results, key=lambda x: x['capacity'])
            most_popular = max(results, key=lambda x: x['investors'])
            
            response += f"🏅 {theme.upper()} TEMA LİDERLERİ:\n"
            response += f"   📈 En Yüksek Getiri: {best_return['fcode']} (%{best_return['annual_return']:+.1f})\n"
            response += f"   ⚡ En İyi Sharpe: {best_sharpe['fcode']} ({best_sharpe['sharpe_ratio']:.3f})\n"
            response += f"   🛡️ En Güvenli: {safest['fcode']} (%{safest['volatility']:.1f} risk)\n"
            response += f"   💰 En Büyük: {biggest['fcode']} ({biggest['capacity']/1000000:.0f}M TL)\n"
            response += f"   👥 En Popüler: {most_popular['fcode']} ({most_popular['investors']:,} kişi)\n\n"
        
        # PERFORMANS DAĞILIMI
        if results:
            excellent = len([f for f in results if f['thematic_score'] > 70])
            good = len([f for f in results if 50 < f['thematic_score'] <= 70])
            average = len([f for f in results if 30 < f['thematic_score'] <= 50])
            poor = len([f for f in results if f['thematic_score'] <= 30])
            
            response += f"📊 {theme.upper()} PERFORMANS DAĞILIMI:\n"
            response += f"   🌟 Mükemmel (>70): {excellent} fon (%{excellent/len(results)*100:.1f})\n"
            response += f"   🔶 İyi (50-70): {good} fon (%{good/len(results)*100:.1f})\n"
            response += f"   🟡 Orta (30-50): {average} fon (%{average/len(results)*100:.1f})\n"
            response += f"   🔻 Zayıf (≤30): {poor} fon (%{poor/len(results)*100:.1f})\n\n"
        
        # YATIRIM ÖNERİSİ
        response += f"💡 {theme.upper()} YATIRIM ÖNERİSİ:\n"
        
        if results:
            top_fund = results[0]
            if avg_return > 15:
                response += f"   🟢 {theme.upper()} teması güçlü performans gösteriyor\n"
                response += f"   ✅ Önerilen fon: {top_fund['fcode']} (Skor: {top_fund['thematic_score']:.1f})\n"
            elif avg_return > 5:
                response += f"   🟡 {theme.upper()} teması makul performans sergiliyor\n"
                response += f"   💡 Dikkatli yatırım önerilir\n"
            else:
                response += f"   🔴 {theme.upper()} teması zayıf performans gösteriyor\n"
                response += f"   ⚠️ Risk yönetimi kritik\n"
            
            # Risk değerlendirmesi
            if avg_volatility > 25:
                response += f"   📊 Yüksek risk teması (%{avg_volatility:.1f} ortalama volatilite)\n"
            elif avg_volatility > 15:
                response += f"   📊 Orta risk teması (%{avg_volatility:.1f} ortalama volatilite)\n"
            else:
                response += f"   📊 Düşük risk teması (%{avg_volatility:.1f} ortalama volatilite)\n"
        
        return response
    
    def compare_multiple_themes(self, themes, question):
        """Çoklu tema karşılaştırması"""
        print(f"⚖️ {len(themes)} tema karşılaştırılıyor: {', '.join(themes)}")
        
        theme_results = {}
        
        for theme in themes:
            print(f"   📊 {theme} analizi...")
            funds = self.find_thematic_funds_sql(theme)
            if funds:
                performance = self.analyze_thematic_performance(funds, theme, 120)  # 4 ay
                if performance:
                    # Özet istatistikler
                    avg_return = sum(f['annual_return'] for f in performance) / len(performance)
                    avg_volatility = sum(f['volatility'] for f in performance) / len(performance)
                    avg_score = sum(f['thematic_score'] for f in performance) / len(performance)
                    total_capacity = sum(f['capacity'] for f in performance)
                    
                    theme_results[theme] = {
                        'fund_count': len(performance),
                        'avg_return': avg_return,
                        'avg_volatility': avg_volatility,
                        'avg_score': avg_score,
                        'total_capacity': total_capacity,
                        'best_fund': max(performance, key=lambda x: x['thematic_score']),
                        'performance_data': performance
                    }
        
        if not theme_results:
            return "❌ Karşılaştırma için yeterli veri bulunamadı."
        
        return self.format_theme_comparison_results(theme_results, themes)
    
    def format_theme_comparison_results(self, theme_results, themes):
        """Tema karşılaştırma sonuçlarını formatla"""
        
        response = f"\n⚖️ TEMATİK TEMA KARŞILAŞTIRMASI - {', '.join(themes).upper()}\n"
        response += f"{'='*70}\n\n"
        
        response += f"📊 KARŞILAŞTIRILAN TEMALAR: {len(themes)}\n\n"
        
        # KARŞILAŞTIRMA TABLOSU
        response += f"📈 PERFORMANS KARŞILAŞTIRMASI:\n\n"
        response += f"{'Tema':<12} | {'Fon':<4} | {'Getiri':<8} | {'Risk':<7} | {'Skor':<5} | {'Varlık':<8}\n"
        response += f"{'-'*12}|{'-'*5}|{'-'*9}|{'-'*8}|{'-'*6}|{'-'*8}\n"
        
        # Skor bazında sırala
        sorted_themes = sorted(theme_results.items(), key=lambda x: x[1]['avg_score'], reverse=True)
        
        for theme, data in sorted_themes:
            varlık_milyar = data['total_capacity'] / 1000000000
            response += f"{theme:<12} | {data['fund_count']:<4} | %{data['avg_return']:+5.1f} | %{data['avg_volatility']:5.1f} | {data['avg_score']:4.1f} | {varlık_milyar:5.1f}B\n"
        
        # KAZANANLAR
        response += f"\n🏆 KATEGORİ KAZANANLARI:\n"
        
        best_return_theme = max(theme_results.items(), key=lambda x: x[1]['avg_return'])
        best_score_theme = max(theme_results.items(), key=lambda x: x[1]['avg_score'])
        safest_theme = min(theme_results.items(), key=lambda x: x[1]['avg_volatility'])
        biggest_theme = max(theme_results.items(), key=lambda x: x[1]['total_capacity'])
        
        response += f"   📈 En Yüksek Getiri: {best_return_theme[0].upper()} (%{best_return_theme[1]['avg_return']:+.1f})\n"
        response += f"   🎯 En Yüksek Skor: {best_score_theme[0].upper()} ({best_score_theme[1]['avg_score']:.1f})\n"
        response += f"   🛡️ En Güvenli: {safest_theme[0].upper()} (%{safest_theme[1]['avg_volatility']:.1f} risk)\n"
        response += f"   💰 En Büyük Varlık: {biggest_theme[0].upper()} ({biggest_theme[1]['total_capacity']/1000000000:.1f}B TL)\n"
        
        # HER TEMADAN EN İYİ FON
        response += f"\n🌟 HER TEMADAN EN İYİ FON:\n\n"
        
        for theme, data in sorted_themes:
            best_fund = data['best_fund']
            response += f"🎯 {theme.upper()}:\n"
            response += f"   {best_fund['fcode']} - Skor: {best_fund['thematic_score']:.1f}\n"
            response += f"   Getiri: %{best_fund['annual_return']:+.1f}, Risk: %{best_fund['volatility']:.1f}\n"
            response += f"   Tip: {best_fund['fund_type']}\n"
            response += f"   {best_fund['fund_name'][:40]}...\n\n"
        
        # GENEL DEĞERLENDİRME
        response += f"🎯 GENEL DEĞERLENDİRME:\n"
        winner = sorted_themes[0]
        response += f"   🥇 En Başarılı Tema: {winner[0].upper()}\n"
        response += f"   📊 Ortalama Skor: {winner[1]['avg_score']:.1f}/100\n"
        response += f"   📈 Ortalama Getiri: %{winner[1]['avg_return']:+.1f}\n"
        
        return response
    
    def _handle_general_thematic_overview(self):
        """Genel tematik fon genel bakış"""
        response = f"\n🎯 TEMATİK FON ANALİZ SİSTEMİ - GENEL BAKIŞ\n"
        response += f"{'='*50}\n\n"
        
        response += f"📊 DESTEKLENEN TEMATİK ALANLAR:\n\n"
        
        for i, (theme, data) in enumerate(self.thematic_keywords.items(), 1):
            response += f"{i:2d}. {theme.upper():<15} - {data['description']}\n"
        
        response += f"\n💡 KULLANIM ÖRNEKLERİ:\n"
        response += f"   • 'Teknoloji fonları hangileri?'\n"
        response += f"   • 'ESG sürdürülebilirlik fonları analizi'\n"
        response += f"   • 'Enerji vs Sağlık sektörü karşılaştırması'\n"
        response += f"   • 'Fintek blockchain fonları nasıl?'\n"
        response += f"   • 'İhracatçı şirketler fonu performansı'\n\n"
        
        response += f"🎯 ANALİZ ÖZELLİKLERİ:\n"
        response += f"   ✅ TÜM veritabanı tarama (1700+ fon)\n"
        response += f"   ✅ Tema özel skorlama sistemi\n"
        response += f"   ✅ Performans karşılaştırması\n"
        response += f"   ✅ Risk-getiri analizi\n"
        response += f"   ✅ Sektör liderleri belirleme\n"
        response += f"   ✅ Yatırım önerileri\n"
        response += f"   ✅ Portföy analizi ile fon tipi belirleme\n\n"
        
        response += f"📈 HIZLI BAŞLANGIÇ:\n"
        response += f"   Bir tema adı yazmanız yeterli!\n"
        response += f"   Örnek: 'teknoloji', 'sağlık', 'enerji'\n"
        
        return response

    def get_portfolio_distribution_summary(self, fcode):
        """Fonun portföy dağılımını detaylı getir"""
        try:
            query = f"""
            SELECT 
                stock, foreignequity, governmentbond, privatesectorbond,
                preciousmetals, exchangetradedfund, realestatecertificate,
                fundparticipationcertificate, tmm, termdeposit, repo,
                participationaccount, other
            FROM tefasfunddetails 
            WHERE fcode = '{fcode}' 
            ORDER BY fdate DESC 
            LIMIT 1
            """
            
            result = self.db.execute_query(query)
            if not result.empty:
                return result.iloc[0].to_dict()
            return {}
            
        except Exception as e:
            self.logger.warning(f"Portföy dağılımı alınamadı {fcode}: {e}")
            return {}

# =============================================================
# INTERACTIVE_QA_DUAL_AI.PY'YE ENTEGRASYON KODU
# =============================================================

"""
Aşağıdaki kodu interactive_qa_dual_ai.py dosyasına entegre edin:

1. İMPORT bölümüne ekleyin:
from thematic_fund_analyzer import ThematicFundAnalyzer

2. DualAITefasQA.__init__ metodunda analyzer'ı başlatın:
self.thematic_analyzer = ThematicFundAnalyzer(self.coordinator.db, self.config)

3. answer_question metoduna şu elif bloğunu ekleyin:
"""

def add_to_answer_question(self, question):
    """Bu kodu answer_question metoduna ekleyin"""
    question_lower = question.lower()
    
    # 📈 TEMATİK FON SORULARI - TÜM VERİTABANI 
    if any(word in question_lower for word in [
        'teknoloji fonları', 'bilişim fonları', 'digital fonlar',
        'esg fonları', 'sürdürülebilir fonlar', 'yeşil fonlar', 'çevre fonları',
        'enerji fonları', 'petrol fonları', 'elektrik fonları',
        'sağlık fonları', 'tıbbi fonlar', 'ilaç fonları', 'healthcare',
        'fintek fonları', 'blockchain fonları', 'kripto fonları',
        'ihracat fonları', 'ihracatçı fonlar', 'dış ticaret fonları',
        'emlak fonları', 'gayrimenkul fonları', 'reit fonları',
        'gıda fonları', 'tarım fonları', 'agriculture fonları',
        'turizm fonları', 'otel fonları', 'seyahat fonları',
        'banka fonları', 'bankacılık fonları', 'finans fonları'
    ]):
        return self.thematic_analyzer.analyze_thematic_question(question)
    
    # Tek kelime tema tespiti
    elif any(word in question_lower for word in [
        'teknoloji', 'bilişim', 'digital', 'yazılım', 'software',
        'esg', 'sürdürülebilir', 'yeşil', 'çevre', 'sustainability',
        'enerji', 'energy', 'petrol', 'elektrik', 'güneş', 'rüzgar',
        'sağlık', 'health', 'tıbbi', 'ilaç', 'medical', 'healthcare',
        'fintek', 'fintech', 'blockchain', 'kripto', 'bitcoin',
        'ihracat', 'export', 'ihracatçı', 'dış ticaret',
        'emlak', 'gayrimenkul', 'reit', 'real estate',
        'gıda', 'food', 'tarım', 'agriculture',
        'turizm', 'tourism', 'otel', 'hotel', 'seyahat',
        'banka', 'bank', 'bankacılık', 'finans'
    ]) and any(word in question_lower for word in ['fon', 'fund', 'yatırım']):
        return self.thematic_analyzer.analyze_thematic_question(question)

# =============================================================
# FON TİPİ BELİRLEME KURALLAR
# =============================================================

FUND_TYPE_RULES = {
    'equity_threshold': 80,      # %80+ hisse senedi = Hisse senedi fonu
    'mixed_threshold': 40,       # %40+ hisse senedi = Karma fon
    'bond_threshold': 60,        # %60+ tahvil = Borçlanma araçları fonu
    'precious_metals_threshold': 50,  # %50+ altın = Altın fonu
    'etf_threshold': 50,         # %50+ ETF = ETF fonu
    'real_estate_threshold': 50, # %50+ emlak sertifikası = Emlak fonu
    'fund_participation_threshold': 50,  # %50+ fon katılım = Fon sepeti
}

# =============================================================
# PERFORMANCE BENCHMARKS
# =============================================================

THEMATIC_BENCHMARKS = {
    'teknoloji': {
        'expected_return': 20,    # Beklenen yıllık getiri %
        'max_volatility': 30,     # Maksimum kabul edilebilir volatilite %
        'min_sharpe': 0.4,        # Minimum Sharpe oranı
    },
    'esg': {
        'expected_return': 12,
        'max_volatility': 18,
        'min_sharpe': 0.5,
    },
    'enerji': {
        'expected_return': 15,
        'max_volatility': 35,
        'min_sharpe': 0.3,
    },
    'sağlık': {
        'expected_return': 14,
        'max_volatility': 22,
        'min_sharpe': 0.4,
    },
    'fintek': {
        'expected_return': 25,
        'max_volatility': 40,
        'min_sharpe': 0.3,
    },
    'default': {
        'expected_return': 12,
        'max_volatility': 25,
        'min_sharpe': 0.3,
    }
}

# =============================================================
# KULLANIM ÖRNEKLERİ VE TEST FONKSİYONLARI
# =============================================================

def demo_thematic_analysis():
    """Demo tematik analiz fonksiyonu"""
    from config.config import Config
    from database.connection import DatabaseManager
    
    config = Config()
    db = DatabaseManager(config)
    analyzer = ThematicFundAnalyzer(db, config)
    
    # Test soruları
    test_questions = [
        "Teknoloji fonları hangileri?",
        "ESG sürdürülebilirlik fonları analizi",
        "Enerji sektörü fonları nasıl?",
        "Sağlık vs teknoloji karşılaştırması",
        "Fintek blockchain fonları"
    ]
    
    print("🎯 TEMATİK FON ANALİZ SİSTEMİ DEMO")
    print("="*50)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[DEMO {i}/5] {question}")
        print("-" * 40)
        
        try:
            result = analyzer.analyze_thematic_question(question)
            # İlk 300 karakteri göster
            preview = result[:300] + "..." if len(result) > 300 else result
            print(preview)
            print("✅ Demo başarılı")
            
            if i < len(test_questions):
                input("\nDevam etmek için Enter'a basın...")
                
        except Exception as e:
            print(f"❌ Demo hatası: {e}")
    
    print(f"\n🎉 Tematik analiz demo tamamlandı!")

# =============================================================
# SQL PERFORMANS OPTİMİZASYONU
# =============================================================

def create_thematic_database_indexes():
    """Tematik analiz için veritabanı indeksleri"""
    indexes_sql = """
    -- Tematik analiz için performans indeksleri
    CREATE INDEX IF NOT EXISTS idx_tefasfunds_ftitle_upper 
    ON tefasfunds (UPPER(ftitle));
    
    CREATE INDEX IF NOT EXISTS idx_tefasfunds_fcode_pdate 
    ON tefasfunds (fcode, pdate DESC);
    
    CREATE INDEX IF NOT EXISTS idx_tefasfunds_investorcount 
    ON tefasfunds (investorcount) WHERE investorcount > 50;
    
    CREATE INDEX IF NOT EXISTS idx_tefasfunds_capacity 
    ON tefasfunds (fcapacity DESC) WHERE fcapacity > 0;
    
    CREATE INDEX IF NOT EXISTS idx_tefasfunddetails_fcode_fdate
    ON tefasfunddetails (fcode, fdate DESC);
    
    -- Composite index for thematic analysis
    CREATE INDEX IF NOT EXISTS idx_tefasfunds_thematic 
    ON tefasfunds (pdate DESC, investorcount, fcapacity) 
    WHERE price > 0 AND investorcount > 50;
    """
    
    return indexes_sql

# =============================================================
# CONFIGURATION VE SETUP
# =============================================================

THEMATIC_CONFIG = {
    'analysis_period_days': 180,  # 6 ay default
    'minimum_investors': 50,      # Minimum yatırımcı sayısı
    'minimum_data_points': 30,    # Minimum veri noktası
    'performance_threshold': 10,  # Performans eşiği %
    'max_funds_per_theme': 100,   # Tema başına maksimum fon
    'sql_timeout': 30,           # SQL timeout saniye
    'cache_duration': 3600,      # Cache süresi saniye
    'risk_free_rate': 15         # Risksiz faiz oranı %
}

# =============================================================
# ERROR HANDLING VE LOGGING
# =============================================================

def setup_thematic_logging():
    """Tematik analiz için özel logging"""
    import logging
    
    # Tematik analiz logger
    thematic_logger = logging.getLogger('thematic_analyzer')
    thematic_logger.setLevel(logging.INFO)
    
    # File handler
    handler = logging.FileHandler('logs/thematic_analysis.log')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    thematic_logger.addHandler(handler)
    
    return thematic_logger

if __name__ == "__main__":
    # Demo çalıştır
    demo_thematic_analysis()