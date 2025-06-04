import time

import numpy as np
import pandas as pd

class EnhancedPortfolioCompanyAnalyzer:
    """Gelişmiş Portföy Şirketi Analiz Sistemi"""
    
    def __init__(self, coordinator):
        self.coordinator = coordinator
        
        # 🎯 GELİŞTİRİLMİŞ Şirket keyword mapping
        self.company_keywords = {
            'İş Portföy': ['İŞ PORTFÖY', 'IS PORTFOY', 'ISBANK PORTFOY'],
            'Ak Portföy': ['AK PORTFÖY', 'AKBANK PORTFÖY', 'AKPORTFOY'],
            'Garanti Portföy': ['GARANTİ PORTFÖY', 'GARANTI PORTFOY', 'GARANTIBANK'],
            'Ata Portföy': ['ATA PORTFÖY', 'ATA PORTFOY'],
            'QNB Portföy': ['QNB PORTFÖY', 'QNB PORTFOY', 'FINANSBANK'],
            'Fiba Portföy': ['FİBA PORTFÖY', 'FIBA PORTFOY', 'FIBABANK'],
            'Yapı Kredi Portföy': ['YAPI KREDİ PORTFÖY', 'YKB PORTFÖY', 'YAPIKREDI'],
            'TEB Portföy': ['TEB PORTFÖY', 'TEB PORTFOY'],
            'Deniz Portföy': ['DENİZ PORTFÖY', 'DENIZ PORTFOY', 'DENIZBANK'],
            'Ziraat Portföy': ['ZİRAAT PORTFÖY', 'ZIRAAT PORTFOY', 'ZIRAATBANK'],
            'Halk Portföy': ['HALK PORTFÖY', 'HALK PORTFOY', 'HALKBANK'],
            'İstanbul Portföy': ['İSTANBUL PORTFÖY', 'ISTANBUL PORTFOY'],
            'Vakıf Portföy': ['VAKIF PORTFÖY', 'VAKIFBANK PORTFÖY'],
            'ICBC Turkey Portföy': ['ICBC', 'INDUSTRIAL'],
            'Bizim Portföy': ['BİZİM PORTFÖY', 'BIZIM PORTFOY'],
            'Tacirler Portföy': ['TACİRLER PORTFÖY', 'TACIRLER'],
            'Gedik Portföy': ['GEDİK PORTFÖY', 'GEDIK'],
            'Info Portföy': ['INFO PORTFÖY', 'INFORMATICS'],
            'Marmara Portföy': ['MARMARA PORTFÖY', 'MARMARA'],
            'Kare Portföy': ['KARE PORTFÖY', 'KARE'],
            'Strateji Portföy': ['STRATEJİ PORTFÖY', 'STRATEJI'],
            'Global Portföy': ['GLOBAL PORTFÖY', 'GLOBAL MD'],
            'Azimut Portföy': ['AZİMUT PORTFÖY', 'AZIMUT'],
            'ING Portföy': ['ING PORTFÖY', 'ING BANK']
        }
    
    def get_all_company_funds_unlimited(self, company_name):
        """Şirketin TÜM fonlarını bul - LİMİTSİZ"""
        print(f"🔍 {company_name} - TÜM fonları aranıyor (limitsiz)...")
        
        try:
            company_funds = []
            keywords = self.company_keywords.get(company_name, [])
            
            if not keywords:
                print(f"   ⚠️ {company_name} için keyword bulunamadı")
                return []
            
            for keyword in keywords:
                try:
                    # 🚀 LİMİTSİZ SORGU - Tüm fonları bul
                    query = f"""
                        SELECT 
                            fcode,
                            fund_name,
                            fcapacity,
                            investorcount,
                            current_price
                        FROM mv_portfolio_company_summary
                        WHERE company_name = %s
                        ORDER BY fcapacity DESC NULLS LAST
"""
                    
                    result = self.coordinator.db.execute_query(query)
                    
                    for _, row in result.iterrows():
                        fund_info = {
                            'fcode': row['fcode'],
                            'fund_name': row['fund_name'],
                            'capacity': float(row['fcapacity']) if pd.notna(row['fcapacity']) else 0,
                            'investors': int(row['investorcount']) if pd.notna(row['investorcount']) else 0,
                            'current_price': float(row['price']) if pd.notna(row['price']) else 0
                        }
                        
                        # Duplicate kontrolü
                        if not any(f['fcode'] == fund_info['fcode'] for f in company_funds):
                            company_funds.append(fund_info)
                            
                except Exception as e:
                    print(f"   ⚠️ Keyword '{keyword}' sorgu hatası: {e}")
                    continue
            
            print(f"   ✅ {len(company_funds)} FON BULUNDU")
            return company_funds
            
        except Exception as e:
            print(f"   ❌ Genel hata: {e}")
            return []

    def calculate_comprehensive_performance(self, fund_code, days=252):
        """MV kullanarak hızlı performans hesaplama"""
        try:
            # Önce MV'den hazır metrikleri al
            query = """
            SELECT * FROM mv_fund_performance_metrics
            WHERE fcode = :fcode
            """
            result = self.coordinator.db.execute_query(query, {'fcode': fund_code})            
            if not result.empty:
                row = result.iloc[0]
                
                # Sortino ratio için yaklaşık hesaplama
                sortino_ratio = row['sharpe_ratio'] * 1.2  # Yaklaşık değer
                
                # Max drawdown için yaklaşık hesaplama
                if row['calmar_ratio'] > 0 and row['annual_return'] > 0:
                    max_drawdown = abs(row['annual_return'] / row['calmar_ratio'])
                else:
                    max_drawdown = row['annual_volatility'] * 2  # Yaklaşık
                
                return {
                    'total_return': (row['annual_return'] / 252 * min(days, row['data_points'])) * 100,
                    'annual_return': row['annual_return'] * 100,
                    'volatility': row['annual_volatility'] * 100,
                    'sharpe_ratio': row['sharpe_ratio'],
                    'sortino_ratio': sortino_ratio,
                    'calmar_ratio': row['calmar_ratio'],
                    'win_rate': row['win_rate'] * 100,
                    'max_drawdown': max_drawdown,
                    'data_points': row['data_points'],
                    'current_price': row['current_price']
                }
        except Exception as e:
            print(f"MV sorgu hatası: {e}, fallback kullanılıyor")
        
        # Orijinal hesaplama (MV yoksa veya hata varsa)
        try:
            # Veri çekimi
            data = self.coordinator.db.get_fund_price_history(fund_code, days)
            
            if len(data) < 10:
                return None
            
            prices = data.set_index('pdate')['price'].sort_index()
            returns = prices.pct_change().dropna()
            
            # İlk ve son fiyat kontrolü
            first_price = prices.iloc[0]
            last_price = prices.iloc[-1]
            
            if first_price <= 0 or last_price <= 0 or pd.isna(first_price) or pd.isna(last_price):
                print(f"   ⚠️ {fund_code} geçersiz fiyat verisi: başlangıç={first_price}, son={last_price}")
                return None
            
            # Temel metrikler
            total_return = (last_price / first_price - 1) * 100
            
            returns_std = returns.std()
            if pd.isna(returns_std) or returns_std == 0:
                print(f"   ⚠️ {fund_code} volatilite hesaplanamadı")
                return None
            
            annual_return = total_return * (252 / len(prices))
            volatility = returns_std * np.sqrt(252) * 100
            
            # Sharpe ratio
            if volatility > 0 and not pd.isna(volatility):
                sharpe = (annual_return - 15) / volatility
            else:
                sharpe = 0
            
            win_rate = (returns > 0).sum() / len(returns) * 100
            
            # Max drawdown
            try:
                cumulative = (1 + returns).cumprod()
                running_max = cumulative.expanding().max()
                drawdown = (cumulative - running_max) / running_max
                max_drawdown = abs(drawdown.min()) * 100
                
                if pd.isna(max_drawdown):
                    max_drawdown = 0
            except Exception:
                max_drawdown = 0
            
            # Calmar ratio
            if max_drawdown > 0 and not pd.isna(max_drawdown):
                calmar = abs(annual_return / max_drawdown)
            else:
                calmar = 0
            
            # Sortino ratio
            negative_returns = returns[returns < 0]
            if len(negative_returns) > 0:
                downside_std = negative_returns.std()
                if not pd.isna(downside_std) and downside_std > 0:
                    downside_deviation = downside_std * np.sqrt(252) * 100
                    sortino = (annual_return - 15) / downside_deviation
                else:
                    sortino = 0
            else:
                sortino = sharpe * 1.5  # Yaklaşık değer
            
            result = {
                'total_return': total_return,
                'annual_return': annual_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe,
                'sortino_ratio': sortino,
                'calmar_ratio': calmar,
                'win_rate': win_rate,
                'max_drawdown': max_drawdown,
                'data_points': len(prices),
                'current_price': last_price
            }
            
            # Infinity ve NaN temizleme
            for key, value in result.items():
                if pd.isna(value) or np.isinf(value):
                    print(f"   ⚠️ {fund_code} {key} değeri geçersiz: {value}")
                    if key in ['sharpe_ratio', 'sortino_ratio', 'calmar_ratio']:
                        result[key] = 0
                    elif key in ['volatility', 'max_drawdown']:
                        result[key] = 0
                    else:
                        result[key] = 0
            
            return result
            
        except Exception as e:
            print(f"   ❌ {fund_code} performans hatası: {e}")
            return None

    def analyze_company_comprehensive(self, company_name, analysis_days=252):
        """Şirket kapsamlı analizi - TÜM FONLARLA"""
        print(f"\n🏢 {company_name.upper()} - KAPSAMLI ANALİZ BAŞLATIYOR...")
        print("="*60)
        
        start_time = time.time()
        
        # 1. TÜM FONLARI BUL
        company_funds = self.get_all_company_funds_unlimited(company_name)
        
        if not company_funds:
            return f"❌ {company_name} fonları bulunamadı."
        
        print(f"📊 BULUNAN FONLAR: {len(company_funds)}")
        print(f"📅 ANALİZ PERİYODU: {analysis_days} gün")
        
        # 2. HER FON İÇİN DETAYLI PERFORMANS ANALİZİ
        print(f"\n🔍 PERFORMANS ANALİZİ BAŞLATIYOR...")
        
        performance_results = []
        successful_analysis = 0
        
        for i, fund_info in enumerate(company_funds, 1):
            fcode = fund_info['fcode']
            print(f"   [{i}/{len(company_funds)}] {fcode}...", end='')
            
            perf = self.calculate_comprehensive_performance(fcode, analysis_days)
            
            if perf:
                fund_result = {
                    'fcode': fcode,
                    'fund_name': fund_info['fund_name'],
                    'capacity': fund_info['capacity'],
                    'investors': fund_info['investors'],
                    **perf  # Performans metriklerini ekle
                }
                performance_results.append(fund_result)
                successful_analysis += 1
                print(f" ✅ ({perf['annual_return']:+.1f}%)")
            else:
                print(f" ❌")
        
        elapsed = time.time() - start_time
        print(f"\n⏱️ ANALİZ TAMAMLANDI: {elapsed:.1f} saniye")
        print(f"✅ BAŞARILI: {successful_analysis}/{len(company_funds)} fon")
        
        if not performance_results:
            return f"❌ {company_name} için performans verisi hesaplanamadı."
        
        # 3. SONUÇLARI FORMATLA
        return self.format_company_analysis_results(company_name, performance_results, elapsed)

    def format_company_analysis_results(self, company_name, results, analysis_time):
        """Analiz sonuçlarını formatla - INF/NaN güvenli"""
        
        # Sonuçları Sharpe ratio'ya göre sırala
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        
        response = f"\n🏢 {company_name.upper()} - KAPSAMLI ANALİZ RAPORU\n"
        response += f"{'='*55}\n\n"
        
        # ÖZET İSTATİSTİKLER - güvenli hesaplama
        total_funds = len(results)
        total_capacity = sum(r['capacity'] for r in results)
        total_investors = sum(r['investors'] for r in results)
        
        # 🔧 DÜZELTİLMİŞ: INF ve NaN değerleri filtrele
        valid_returns = [r['annual_return'] for r in results if not (pd.isna(r['annual_return']) or np.isinf(r['annual_return']))]
        valid_sharpes = [r['sharpe_ratio'] for r in results if not (pd.isna(r['sharpe_ratio']) or np.isinf(r['sharpe_ratio']))]
        valid_volatilities = [r['volatility'] for r in results if not (pd.isna(r['volatility']) or np.isinf(r['volatility']))]
        
        avg_return = sum(valid_returns) / len(valid_returns) if valid_returns else 0
        avg_sharpe = sum(valid_sharpes) / len(valid_sharpes) if valid_sharpes else 0
        avg_volatility = sum(valid_volatilities) / len(valid_volatilities) if valid_volatilities else 0
        
        response += f"📊 ŞİRKET GENEL İSTATİSTİKLERİ:\n"
        response += f"   🔢 Toplam Fon Sayısı: {total_funds}\n"
        response += f"   💰 Toplam Varlık: {total_capacity:,.0f} TL ({total_capacity/1000000000:.1f} milyar)\n"
        response += f"   👥 Toplam Yatırımcı: {total_investors:,} kişi\n"
        response += f"   📈 Ortalama Yıllık Getiri: %{avg_return:+.2f}\n"
        response += f"   ⚡ Ortalama Sharpe Oranı: {avg_sharpe:.3f}\n"
        response += f"   📊 Ortalama Volatilite: %{avg_volatility:.2f}\n"
        response += f"   ⏱️ Analiz Süresi: {analysis_time:.1f} saniye\n"
        response += f"   📊 Geçerli Veri: {len(valid_returns)}/{total_funds} fon\n\n"
        
        # EN İYİ PERFORMANS FONLARI (TOP 10) - geçerli veriler
        valid_results = [r for r in results if not (pd.isna(r['sharpe_ratio']) or np.isinf(r['sharpe_ratio']))]
        
        response += f"🏆 EN İYİ PERFORMANS FONLARI (Sharpe Oranına Göre):\n\n"
        
        for i, fund in enumerate(valid_results[:10], 1):
            # Performance tier belirleme
            if fund['sharpe_ratio'] > 1.0:
                tier = "🌟 MÜKEMMEL"
            elif fund['sharpe_ratio'] > 0.5:
                tier = "⭐ ÇOK İYİ"
            elif fund['sharpe_ratio'] > 0:
                tier = "🔶 İYİ"
            elif fund['sharpe_ratio'] > -0.5:
                tier = "🔸 ORTA"
            else:
                tier = "🔻 ZAYIF"
            
            response += f"{i:2d}. {fund['fcode']} - {tier}\n"
            response += f"    📈 Yıllık Getiri: %{fund['annual_return']:+.2f}\n"
            response += f"    ⚡ Sharpe Oranı: {fund['sharpe_ratio']:.3f}\n"
            response += f"    📊 Volatilite: %{fund['volatility']:.2f}\n"
            response += f"    🎯 Kazanma Oranı: %{fund['win_rate']:.1f}\n"
            response += f"    📉 Max Düşüş: %{fund['max_drawdown']:.2f}\n"
            response += f"    💰 Kapasite: {fund['capacity']:,.0f} TL\n"
            response += f"    👥 Yatırımcı: {fund['investors']:,} kişi\n"
            response += f"    💲 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
            response += f"    📝 Adı: {fund['fund_name'][:45]}...\n"
            response += f"\n"
        
        # KATEGORİ LİDERLERİ - güvenli
        if valid_results:
            # En yüksek getiri - INF olmayan
            best_return_fund = max(valid_results, key=lambda x: x['annual_return'] if not np.isinf(x['annual_return']) else -999)
            best_sharpe_fund = max(valid_results, key=lambda x: x['sharpe_ratio'])
            lowest_vol_fund = min(valid_results, key=lambda x: x['volatility'] if x['volatility'] > 0 else 999)
            
            response += f"🏅 KATEGORİ LİDERLERİ:\n"
            response += f"   🥇 En Yüksek Getiri: {best_return_fund['fcode']} (%{best_return_fund['annual_return']:+.1f})\n"
            response += f"   🛡️ En Düşük Risk: {lowest_vol_fund['fcode']} (%{lowest_vol_fund['volatility']:.1f})\n"
            response += f"   ⚡ En Yüksek Sharpe: {best_sharpe_fund['fcode']} ({best_sharpe_fund['sharpe_ratio']:.3f})\n"
            response += f"   💰 En Büyük Fon: {max(results, key=lambda x: x['capacity'])['fcode']} ({max(results, key=lambda x: x['capacity'])['capacity']/1000000:.0f}M TL)\n"
            response += f"   👥 En Popüler: {max(results, key=lambda x: x['investors'])['fcode']} ({max(results, key=lambda x: x['investors'])['investors']:,} kişi)\n"
        
        # PERFORMANCE DAĞILIMI - geçerli verilerle
        if valid_results:
            excellent_funds = len([f for f in valid_results if f['sharpe_ratio'] > 1.0])
            good_funds = len([f for f in valid_results if 0.5 < f['sharpe_ratio'] <= 1.0])
            average_funds = len([f for f in valid_results if 0 < f['sharpe_ratio'] <= 0.5])
            poor_funds = len([f for f in valid_results if f['sharpe_ratio'] <= 0])
            
            response += f"\n📊 PERFORMANS DAĞILIMI:\n"
            response += f"   🌟 Mükemmel (Sharpe>1.0): {excellent_funds} fon (%{excellent_funds/len(valid_results)*100:.1f})\n"
            response += f"   ⭐ Çok İyi (0.5-1.0): {good_funds} fon (%{good_funds/len(valid_results)*100:.1f})\n"
            response += f"   🔶 İyi (0-0.5): {average_funds} fon (%{average_funds/len(valid_results)*100:.1f})\n"
            response += f"   🔻 Zayıf (≤0): {poor_funds} fon (%{poor_funds/len(valid_results)*100:.1f})\n"
        
        # GENEL DEĞERLENDİRME
        if avg_sharpe > 0.5:
            overall_rating = "🌟 MÜKEMMEL"
        elif avg_sharpe > 0.2:
            overall_rating = "⭐ ÇOK İYİ"
        elif avg_sharpe > 0:
            overall_rating = "🔶 İYİ"
        elif avg_sharpe > -0.2:
            overall_rating = "🔸 ORTA"
        else:
            overall_rating = "🔻 ZAYIF"
        
        response += f"\n🎯 GENEL DEĞERLENDİRME: {overall_rating}\n"
        response += f"   Ortalama Sharpe {avg_sharpe:.3f} ile {company_name} "
        
        if avg_sharpe > 0.3:
            response += "güçlü performans sergiliyor.\n"
        elif avg_sharpe > 0:
            response += "makul bir performans gösteriyor.\n"
        else:
            response += "performansını iyileştirmesi gerekiyor.\n"
        
        # VERİ KALİTESİ UYARISI
        invalid_count = total_funds - len(valid_results)
        if invalid_count > 0:
            response += f"\n⚠️ VERİ KALİTESİ NOTU:\n"
            response += f"   {invalid_count} fon geçersiz veri nedeniyle hariç tutuldu\n"
            response += f"   (INF, NaN veya sıfır değerler içeren fonlar)\n"
        
        return response

    def compare_companies_unlimited(self, company1, company2, analysis_days=252):
        """İki şirketi kapsamlı karşılaştır - LİMİTSİZ"""
        print(f"\n⚖️ {company1} vs {company2} - KAPSAMLI KARŞILAŞTIRMA")
        print("="*65)
        
        # Her iki şirket için analiz
        results1 = self.analyze_company_detailed_data(company1, analysis_days)
        results2 = self.analyze_company_detailed_data(company2, analysis_days)
        
        if not results1['success'] or not results2['success']:
            return f"❌ Karşılaştırma için yeterli veri yok."
        
        response = f"\n⚖️ {company1.upper()} vs {company2.upper()} - DETAYLI KARŞILAŞTIRMA\n"
        response += f"{'='*70}\n\n"
        
        # GENEL İSTATİSTİKLER KARŞILAŞTIRMASI
        metrics = [
            ('Fon Sayısı', 'total_funds', 'adet', 'higher'),
            ('Toplam Varlık', 'total_capacity', 'milyar TL', 'higher'), 
            ('Ortalama Getiri', 'avg_return', '%', 'higher'),
            ('Ortalama Sharpe', 'avg_sharpe', '', 'higher'),
            ('Ortalama Risk', 'avg_volatility', '%', 'lower'),
            ('Toplam Yatırımcı', 'total_investors', 'K kişi', 'higher')
        ]
        
        response += f"📊 GENEL KARŞILAŞTIRMA:\n\n"
        response += f"{'Metrik':<15} | {company1:<15} | {company2:<15} | Kazanan\n"
        response += f"{'-'*15}|{'-'*16}|{'-'*16}|{'-'*15}\n"
        
        score1 = 0
        score2 = 0
        
        for metric_name, key, unit, better in metrics:
            val1 = results1['stats'][key]
            val2 = results2['stats'][key]
            
            # Değer formatlama
            if 'milyar' in unit:
                val1_display = f"{val1/1000000000:.1f}"
                val2_display = f"{val2/1000000000:.1f}"
            elif 'K kişi' in unit:
                val1_display = f"{val1/1000:.0f}"
                val2_display = f"{val2/1000:.0f}"
            elif '%' in unit:
                val1_display = f"{val1:+.1f}"
                val2_display = f"{val2:+.1f}"
            else:
                val1_display = f"{val1:.2f}"
                val2_display = f"{val2:.2f}"
            
            # Kazanan belirleme
            if better == 'higher':
                winner = company1 if val1 > val2 else company2
                if val1 > val2:
                    score1 += 1
                else:
                    score2 += 1
            else:  # lower is better (risk)
                winner = company1 if val1 < val2 else company2
                if val1 < val2:
                    score1 += 1
                else:
                    score2 += 1
            
            response += f"{metric_name:<15} | {val1_display:<15} | {val2_display:<15} | 🏆 {winner}\n"
        
        # GENEL SKOR
        response += f"\n🏆 GENEL SKOR: {company1} {score1}-{score2} {company2}\n"
        
        if score1 > score2:
            overall_winner = company1
            response += f"🥇 KAZANAN: {company1}\n"
        elif score2 > score1:
            overall_winner = company2
            response += f"🥇 KAZANAN: {company2}\n"
        else:
            response += f"🤝 BERABERE\n"
        
        # EN İYİ FONLAR KARŞILAŞTIRMASI
        response += f"\n🌟 EN İYİ FONLAR KARŞILAŞTIRMASI:\n\n"
        
        response += f"🏢 {company1.upper()} EN İYİLERİ:\n"
        for i, fund in enumerate(results1['top_funds'][:3], 1):
            response += f"   {i}. {fund['fcode']}: Sharpe {fund['sharpe_ratio']:.3f}, Getiri %{fund['annual_return']:+.1f}\n"
        
        response += f"\n🏢 {company2.upper()} EN İYİLERİ:\n"
        for i, fund in enumerate(results2['top_funds'][:3], 1):
            response += f"   {i}. {fund['fcode']}: Sharpe {fund['sharpe_ratio']:.3f}, Getiri %{fund['annual_return']:+.1f}\n"
        
        # GÜÇLÜ/ZAYIF YÖNLER
        response += f"\n💪 GÜÇLÜ YÖNLER:\n"
        response += f"🏢 {company1}:\n"
        if results1['stats']['avg_sharpe'] > results2['stats']['avg_sharpe']:
            response += f"   ✅ Daha iyi risk-ayarlı getiri\n"
        if results1['stats']['total_capacity'] > results2['stats']['total_capacity']:
            response += f"   ✅ Daha büyük varlık yönetimi\n"
        if results1['stats']['total_funds'] > results2['stats']['total_funds']:
            response += f"   ✅ Daha geniş fon yelpazesi\n"
        
        response += f"\n🏢 {company2}:\n"
        if results2['stats']['avg_sharpe'] > results1['stats']['avg_sharpe']:
            response += f"   ✅ Daha iyi risk-ayarlı getiri\n"
        if results2['stats']['total_capacity'] > results1['stats']['total_capacity']:
            response += f"   ✅ Daha büyük varlık yönetimi\n"
        if results2['stats']['total_funds'] > results1['stats']['total_funds']:
            response += f"   ✅ Daha geniş fon yelpazesi\n"
        
        return response

    def analyze_company_detailed_data(self, company_name, analysis_days=252):
        """Şirket için detaylı veri analizi (karşılaştırma için)"""
        try:
            company_funds = self.get_all_company_funds_unlimited(company_name)
            
            if not company_funds:
                return {'success': False}
            
            performance_results = []
            
            for fund_info in company_funds:
                perf = self.calculate_comprehensive_performance(fund_info['fcode'], analysis_days)
                if perf:
                    fund_result = {
                        'fcode': fund_info['fcode'],
                        'fund_name': fund_info['fund_name'],
                        'capacity': fund_info['capacity'],
                        'investors': fund_info['investors'],
                        **perf
                    }
                    performance_results.append(fund_result)
            
            if not performance_results:
                return {'success': False}
            
            # İstatistikleri hesapla
            total_funds = len(performance_results)
            total_capacity = sum(r['capacity'] for r in performance_results)
            total_investors = sum(r['investors'] for r in performance_results)
            avg_return = sum(r['annual_return'] for r in performance_results) / total_funds
            avg_sharpe = sum(r['sharpe_ratio'] for r in performance_results) / total_funds
            avg_volatility = sum(r['volatility'] for r in performance_results) / total_funds
            
            # En iyi fonları bul
            performance_results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
            
            return {
                'success': True,
                'stats': {
                    'total_funds': total_funds,
                    'total_capacity': total_capacity,
                    'total_investors': total_investors,
                    'avg_return': avg_return,
                    'avg_sharpe': avg_sharpe,
                    'avg_volatility': avg_volatility
                },
                'top_funds': performance_results[:5],
                'all_funds': performance_results
            }
            
        except Exception as e:
            print(f"   ❌ {company_name} detaylı analiz hatası: {e}")
            return {'success': False}

    def find_best_portfolio_company_unlimited(self):
        """En başarılı portföy şirketini bul - TÜM ŞİRKETLER"""
        print(f"\n🏆 EN BAŞARILI PORTFÖY ŞİRKETİ ANALİZİ - TÜM ŞİRKETLER")
        print("="*65)
        
        company_results = []
        total_companies = len(self.company_keywords)
        
        for i, company_name in enumerate(self.company_keywords.keys(), 1):
            print(f"\n📊 [{i}/{total_companies}] {company_name} analizi...")
            
            try:
                result = self.analyze_company_detailed_data(company_name, analysis_days=180)  # 6 ay
                
                if result['success']:
                    stats = result['stats']
                    
                    # BAŞARI SKORU hesaplama (çok boyutlu)
                    success_score = (
                        stats['avg_sharpe'] * 40 +          # Risk-ayarlı getiri (en önemli)
                        (stats['avg_return'] / 100) * 30 +   # Mutlak getiri 
                        (stats['total_funds'] / 10) * 15 +   # Fon çeşitliliği
                        min(stats['total_capacity'] / 1000000000, 5) * 10 +  # Büyüklük (max 5 puan)
                        (stats['total_investors'] / 100000) * 5  # Popülerlik
                    )
                    
                    company_results.append({
                        'company': company_name,
                        'success_score': success_score,
                        **stats,
                        'best_fund': result['top_funds'][0] if result['top_funds'] else None
                    })
                    
                    print(f"   ✅ Başarı Skoru: {success_score:.2f}")
                else:
                    print(f"   ❌ Veri yetersiz")
                    
            except Exception as e:
                print(f"   ❌ Hata: {e}")
                continue
        
        if not company_results:
            return "❌ Hiçbir şirket analiz edilemedi."
        
        # Başarı skoruna göre sırala
        company_results.sort(key=lambda x: x['success_score'], reverse=True)
        
        return self.format_best_company_results(company_results)

    def format_best_company_results(self, results):
        """En başarılı şirket sonuçlarını formatla"""
        
        response = f"\n🏆 EN BAŞARILI PORTFÖY YÖNETİM ŞİRKETİ SIRALAMASI\n"
        response += f"{'='*60}\n\n"
        response += f"📊 {len(results)} şirket analiz edildi (TÜM FONLARLA)\n\n"
        
        # TOP 10 ŞİRKET
        response += f"🥇 EN BAŞARILI 10 ŞİRKET (Çok Boyutlu Skorlama):\n\n"
        
        for i, company in enumerate(results[:10], 1):
            # Başarı kategorisi
            score = company['success_score']
            if score > 15:
                rating = "🌟 EFSANE"
            elif score > 10:
                rating = "⭐ MÜKEMMEL"
            elif score > 7:
                rating = "🔶 ÇOK İYİ"
            elif score > 5:
                rating = "🔸 İYİ"
            elif score > 3:
                rating = "🟡 ORTA"
            else:
                rating = "🔻 ZAYIF"
            
            response += f"{i:2d}. {company['company']} - {rating}\n"
            response += f"    🎯 Başarı Skoru: {score:.2f}/25\n"
            response += f"    📊 Fon Sayısı: {company['total_funds']}\n"
            response += f"    📈 Ort. Getiri: %{company['avg_return']:+.2f}\n"
            response += f"    ⚡ Ort. Sharpe: {company['avg_sharpe']:.3f}\n"
            response += f"    💰 Varlık: {company['total_capacity']/1000000000:.1f} milyar TL\n"
            response += f"    👥 Yatırımcı: {company['total_investors']:,} kişi\n"
            
            if company['best_fund']:
                bf = company['best_fund']
                response += f"    🏆 En İyi Fon: {bf['fcode']} (Sharpe: {bf['sharpe_ratio']:.3f})\n"
            
            response += f"\n"
        
        # ŞAMPİYONLAR
        winner = results[0]
        response += f"🏆 GENEL ŞAMPİYON: {winner['company']}\n"
        response += f"   🎯 Toplam Skor: {winner['success_score']:.2f}\n"
        response += f"   📊 {winner['total_funds']} fon ile %{winner['avg_return']:+.1f} ortalama getiri\n"
        
        # KATEGORİ ŞAMPİYONLARI
        response += f"\n🏅 KATEGORİ ŞAMPİYONLARI:\n"
        
        # En yüksek getiri
        best_return = max(results, key=lambda x: x['avg_return'])
        response += f"   📈 En Yüksek Getiri: {best_return['company']} (%{best_return['avg_return']:+.1f})\n"
        
        # En iyi Sharpe
        best_sharpe = max(results, key=lambda x: x['avg_sharpe'])
        response += f"   ⚡ En İyi Sharpe: {best_sharpe['company']} ({best_sharpe['avg_sharpe']:.3f})\n"
        
        # En büyük varlık
        biggest_aum = max(results, key=lambda x: x['total_capacity'])
        response += f"   💰 En Büyük Varlık: {biggest_aum['company']} ({biggest_aum['total_capacity']/1000000000:.1f} milyar TL)\n"
        
        # En çok fon
        most_funds = max(results, key=lambda x: x['total_funds'])
        response += f"   📊 En Çok Fon: {most_funds['company']} ({most_funds['total_funds']} fon)\n"
        
        # En popüler
        most_popular = max(results, key=lambda x: x['total_investors'])
        response += f"   👥 En Popüler: {most_popular['company']} ({most_popular['total_investors']:,} yatırımcı)\n"
        
        # SEKTÖR ANALİZİ
        avg_sector_score = sum(r['success_score'] for r in results) / len(results)
        avg_sector_return = sum(r['avg_return'] for r in results) / len(results)
        avg_sector_sharpe = sum(r['avg_sharpe'] for r in results) / len(results)
        
        response += f"\n📊 SEKTÖR GENEL ANALİZİ:\n"
        response += f"   Ortalama Başarı Skoru: {avg_sector_score:.2f}\n"
        response += f"   Ortalama Getiri: %{avg_sector_return:+.2f}\n"
        response += f"   Ortalama Sharpe: {avg_sector_sharpe:.3f}\n"
        
        # PERFORMANS DAĞILIMI
        excellent = len([r for r in results if r['success_score'] > 10])
        good = len([r for r in results if 7 < r['success_score'] <= 10])
        average = len([r for r in results if 5 < r['success_score'] <= 7])
        poor = len([r for r in results if r['success_score'] <= 5])
        
        response += f"\n📈 PERFORMANS DAĞILIMI:\n"
        response += f"   🌟 Mükemmel (>10): {excellent} şirket\n"
        response += f"   ⭐ Çok İyi (7-10): {good} şirket\n"
        response += f"   🔶 İyi (5-7): {average} şirket\n"
        response += f"   🔻 Gelişmeli (≤5): {poor} şirket\n"
        
        return response

    @staticmethod
    def get_examples():
        """Portföy şirketi analizi örnekleri"""
        return [
            "İş Portföy fonları nasıl performans gösteriyor?",
            "Ak Portföy analizi",
            "Garanti Portföy fonlarının durumu nedir?",
            "En başarılı portföy şirketi hangisi?",
            "İş Portföy vs Ak Portföy karşılaştırması",
            "QNB Portföy fonları",
            "Ata Portföy performansı"
        ]
    
    @staticmethod
    def get_keywords():
        """Portföy şirketleri için anahtar kelimeler"""
        return [
            "portföy", "iş portföy", "ak portföy", "garanti portföy",
            "qnb portföy", "ata portföy", "fiba portföy", "yapı kredi portföy",
            "ziraat portföy", "vakıf portföy", "halk portföy"
        ]
    
    @staticmethod
    def get_patterns():
        """Portföy şirketi pattern'leri"""
        return [
            {
                'type': 'regex',
                'pattern': r'(iş|ak|garanti|qnb|ata|fiba)\s*portföy',
                'score': 1.0
            },
            {
                'type': 'contains_all',
                'words': ['portföy', 'şirket'],
                'score': 0.85
            },
            {
                'type': 'contains_all',
                'words': ['başarılı', 'portföy'],
                'score': 0.9
            }
        ]
    
    @staticmethod
    def get_method_patterns():
        """Method mapping"""
        return {
            'analyze_company_comprehensive': ['analiz', 'performans', 'durum', 'nasıl'],
            'compare_companies_unlimited': ['vs', 'karşılaştır', 'karşı', 'compare'],
            'find_best_portfolio_company_unlimited': ['en başarılı', 'en iyi', 'best']
        }