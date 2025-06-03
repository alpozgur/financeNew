# time_based_analysis.py
"""
Zaman Bazlı Fon Analizleri
- Farklı zaman periyotlarında performans analizi
- Trend analizi
- İstikrar ölçümleri
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re

class TimeBasedAnalyzer:
    """Zaman bazlı fon analizleri"""
    
    def __init__(self, coordinator, active_funds):
        self.coordinator = coordinator
        self.active_funds = active_funds
        self.db = coordinator.db
        
    def analyze_time_based_question(self, question):
        """Zaman bazlı soruları analiz et ve yönlendir"""
        question_lower = question.lower()
        
        # Son X dönem analizi
        if any(phrase in question_lower for phrase in ['son 3 ay', 'son 6 ay', 'son 1 yıl', 'geçtiğimiz']):
            return self.handle_period_performance(question)
        
        # Haftalık trend analizi
        elif any(phrase in question_lower for phrase in ['haftalık', 'weekly', 'hafta bazında']):
            return self.handle_weekly_trend_analysis(question)
        
        # Aylık liderler
        elif any(phrase in question_lower for phrase in ['aylık getiri', 'ay bazında', 'monthly']):
            return self.handle_monthly_leaders(question)
        
        # Yıl başından beri
        elif any(phrase in question_lower for phrase in ['yıl başından', 'ytd', 'year to date', 'ocak']):
            return self.handle_year_to_date_analysis(question)
        
        # Uzun dönem istikrar
        elif any(phrase in question_lower for phrase in ['5 yıl', 'istikrarlı', 'tutarlı', 'stable']):
            return self.handle_long_term_stability(question)
        
        else:
            return None
    
    def handle_period_performance(self, question):
        """Belirli dönem performans analizi (son 3 ay, 6 ay, 1 yıl vb.)"""
        print("📊 Dönem performans analizi yapılıyor...")
        
        # Dönem tespiti
        question_lower = question.lower()
        if 'son 3 ay' in question_lower or '3 ay' in question_lower:
            days = 90
            period_name = "3 AY"
        elif 'son 6 ay' in question_lower or '6 ay' in question_lower:
            days = 180
            period_name = "6 AY"
        elif 'son 1 yıl' in question_lower or '1 yıl' in question_lower:
            days = 365
            period_name = "1 YIL"
        elif 'son 2 yıl' in question_lower:
            days = 730
            period_name = "2 YIL"
        else:
            # Varsayılan 3 ay
            days = 90
            period_name = "3 AY"
        
        # En çok yükselen mi, düşen mi?
        is_top_gainers = 'yükselen' in question_lower or 'kazandıran' in question_lower
        is_top_losers = 'düşen' in question_lower or 'kaybettiren' in question_lower
        
        try:
            # SQL ile hızlı analiz
            query = f"""
            WITH period_data AS (
                SELECT DISTINCT ON (fcode) fcode, price as end_price, pdate as end_date
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '7 days'
                AND investorcount > 50
                ORDER BY fcode, pdate DESC
            ),
            start_data AS (
                SELECT DISTINCT ON (fcode) fcode, price as start_price, pdate as start_date
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '{days} days' - INTERVAL '7 days'
                AND pdate <= CURRENT_DATE - INTERVAL '{days} days' + INTERVAL '7 days'
                AND investorcount > 50
                ORDER BY fcode, pdate ASC
            ),
            performance AS (
                SELECT 
                    p.fcode,
                    p.end_price,
                    s.start_price,
                    p.end_date,
                    s.start_date,
                    ((p.end_price / s.start_price) - 1) * 100 as return_pct,
                    p.end_date - s.start_date as actual_days
                FROM period_data p
                JOIN start_data s ON p.fcode = s.fcode
                WHERE s.start_price > 0 AND p.end_price > 0
                AND p.end_date - s.start_date >= {days * 0.8}  -- En az %80 veri
            )
            SELECT 
                pf.*, 
                f.investorcount,
                f.fcapacity
            FROM performance pf
            JOIN (
                SELECT DISTINCT ON (fcode) fcode, investorcount, fcapacity
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY fcode, pdate DESC
            ) f ON pf.fcode = f.fcode
            ORDER BY return_pct {'DESC' if is_top_gainers or not is_top_losers else 'ASC'}
            LIMIT 20
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return f"❌ Son {period_name} için yeterli veri bulunamadı."
            
            # Fund details al
            fund_codes = result['fcode'].tolist()
            fund_details_dict = {}
            
            try:
                details_df = self.coordinator.db.get_all_fund_details()
                for _, detail_row in details_df.iterrows():
                    if detail_row['fcode'] in fund_codes:
                        fund_details_dict[detail_row['fcode']] = {
                            'name': detail_row.get('fund_name', 'N/A'),
                            'type': detail_row.get('fund_type', 'N/A')
                        }
            except:
                pass
            
            # Başlık
            if is_top_gainers:
                title = f"📈 SON {period_name} EN ÇOK YÜKSELEN FONLAR"
            elif is_top_losers:
                title = f"📉 SON {period_name} EN ÇOK DÜŞEN FONLAR"
            else:
                title = f"📊 SON {period_name} PERFORMANS LİDERLERİ"
            
            response = f"\n{title}\n"
            response += f"{'='*50}\n\n"
            response += f"📅 Analiz Periyodu: Son {days} gün ({period_name})\n"
            response += f"📊 Toplam Analiz Edilen: {len(result)} fon\n\n"
            
            # İlk 10 fonu göster
            for i, (_, row) in enumerate(result.head(10).iterrows(), 1):
                fcode = row['fcode']
                return_pct = float(row['return_pct'])
                end_price = float(row['end_price'])
                start_price = float(row['start_price'])
                actual_days = int(row['actual_days'])
                investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                
                fund_info = fund_details_dict.get(fcode, {'name': 'N/A', 'type': 'N/A'})
                
                # Performans emoji
                if return_pct > 20:
                    emoji = "🚀"
                elif return_pct > 10:
                    emoji = "📈"
                elif return_pct > 0:
                    emoji = "➕"
                elif return_pct > -10:
                    emoji = "➖"
                else:
                    emoji = "📉"
                
                response += f"{i:2d}. {fcode} {emoji}\n"
                response += f"    📊 {period_name} Getiri: %{return_pct:+.2f}\n"
                response += f"    💰 Başlangıç: {start_price:.4f} → Son: {end_price:.4f} TL\n"
                response += f"    📅 Veri Süresi: {actual_days} gün\n"
                response += f"    👥 Yatırımcı: {investors:,} kişi\n"
                response += f"    🏷️ Tür: {fund_info['type']}\n"
                if fund_info['name'] != 'N/A':
                    response += f"    📝 {fund_info['name'][:40]}...\n"
                response += f"\n"
            
            # İstatistikler
            avg_return = result['return_pct'].mean()
            positive_funds = len(result[result['return_pct'] > 0])
            
            response += f"📊 {period_name} İSTATİSTİKLERİ:\n"
            response += f"   • Ortalama Getiri: %{avg_return:+.2f}\n"
            response += f"   • Pozitif Getiri: {positive_funds}/{len(result)} fon\n"
            response += f"   • En İyi: {result.iloc[0]['fcode']} (%{result.iloc[0]['return_pct']:+.2f})\n"
            response += f"   • En Kötü: {result.iloc[-1]['fcode']} (%{result.iloc[-1]['return_pct']:+.2f})\n"
            
            return response
            
        except Exception as e:
            print(f"❌ Dönem analizi hatası: {e}")
            return f"❌ {period_name} analizi yapılırken hata oluştu: {e}"
    
    def handle_weekly_trend_analysis(self, question):
        """Haftalık trend analizi"""
        print("📊 Haftalık trend analizi yapılıyor...")
        
        try:
            # Son 8 haftalık veriyi al
            weeks_to_analyze = 8
            
            query = f"""
            WITH weekly_data AS (
                SELECT 
                    fcode,
                    DATE_TRUNC('week', pdate) as week_start,
                    AVG(price) as avg_price,
                    MAX(price) as max_price,
                    MIN(price) as min_price,
                    COUNT(*) as data_points
                FROM tefasfunds
                WHERE pdate >= CURRENT_DATE - INTERVAL '{weeks_to_analyze} weeks'
                AND investorcount > 100
                GROUP BY fcode, DATE_TRUNC('week', pdate)
                HAVING COUNT(*) >= 3  -- Haftada en az 3 gün veri
            ),
            weekly_changes AS (
                SELECT 
                    fcode,
                    week_start,
                    avg_price,
                    LAG(avg_price) OVER (PARTITION BY fcode ORDER BY week_start) as prev_week_price,
                    ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY week_start) as week_num
                FROM weekly_data
            ),
            trend_analysis AS (
                SELECT 
                    fcode,
                    COUNT(*) as weeks_with_data,
                    -- Pozitif hafta sayısı
                    SUM(CASE WHEN avg_price > prev_week_price THEN 1 ELSE 0 END) as positive_weeks,
                    -- Trend skoru (linear regression slope)
                    REGR_SLOPE(avg_price, week_num) as trend_slope,
                    -- Haftalık ortalama değişim
                    AVG(CASE 
                        WHEN prev_week_price > 0 THEN ((avg_price - prev_week_price) / prev_week_price) * 100 
                        ELSE NULL 
                    END) as avg_weekly_change,
                    -- Volatilite
                    STDDEV(avg_price) / NULLIF(AVG(avg_price), 0) * 100 as weekly_volatility,
                    -- İlk ve son hafta fiyatları
                    MIN(CASE WHEN week_num = 1 THEN avg_price END) as first_week_price,
                    MAX(CASE WHEN week_num = (SELECT MAX(week_num) FROM weekly_changes wc2 WHERE wc2.fcode = wc.fcode) 
                        THEN avg_price END) as last_week_price
                FROM weekly_changes wc
                WHERE prev_week_price IS NOT NULL OR week_num = 1
                GROUP BY fcode
                HAVING COUNT(*) >= {weeks_to_analyze - 2}  -- En az 6 hafta veri
            ),
            final_analysis AS (
                SELECT 
                    ta.*,
                    -- Toplam değişim yüzdesi
                    CASE 
                        WHEN first_week_price > 0 THEN 
                            ((last_week_price - first_week_price) / first_week_price) * 100 
                        ELSE 0 
                    END as total_change_pct,
                    -- Güncel fiyat
                    (SELECT price FROM tefasfunds WHERE fcode = ta.fcode ORDER BY pdate DESC LIMIT 1) as current_price,
                    -- Güncel yatırımcı sayısı
                    (SELECT investorcount FROM tefasfunds WHERE fcode = ta.fcode ORDER BY pdate DESC LIMIT 1) as current_investors
                FROM trend_analysis ta
            )
            SELECT *
            FROM final_analysis
            WHERE trend_slope IS NOT NULL
            ORDER BY trend_slope DESC
            LIMIT 20
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return "❌ Haftalık trend analizi için yeterli veri bulunamadı."
            
            # Fund details al
            fund_codes = result['fcode'].tolist()
            fund_details_dict = {}
            
            try:
                details_df = self.coordinator.db.get_all_fund_details()
                for _, detail_row in details_df.iterrows():
                    if detail_row['fcode'] in fund_codes:
                        fund_details_dict[detail_row['fcode']] = {
                            'name': detail_row.get('fund_name', 'N/A'),
                            'type': detail_row.get('fund_type', 'N/A')
                        }
            except:
                pass
            
            response = f"\n📈 HAFTALIK TREND ANALİZİ (Son {weeks_to_analyze} Hafta)\n"
            response += f"{'='*55}\n\n"
            
            # Yükselen trendler
            uptrend_funds = result[result['trend_slope'] > 0]
            downtrend_funds = result[result['trend_slope'] < 0]
            
            response += f"🚀 YÜKSELEN TREND ({len(uptrend_funds)} fon):\n\n"
            
            for i, (_, row) in enumerate(uptrend_funds.head(7).iterrows(), 1):
                fcode = row['fcode']
                trend_slope = float(row['trend_slope']) if pd.notna(row['trend_slope']) else 0
                positive_weeks = int(row['positive_weeks']) if pd.notna(row['positive_weeks']) else 0
                weeks_with_data = int(row['weeks_with_data']) if pd.notna(row['weeks_with_data']) else 0
                volatility = float(row['weekly_volatility']) if pd.notna(row['weekly_volatility']) else 0
                total_change = float(row['total_change_pct']) if pd.notna(row['total_change_pct']) else 0
                avg_weekly_change = float(row['avg_weekly_change']) if pd.notna(row['avg_weekly_change']) else 0
                current_price = float(row['current_price']) if pd.notna(row['current_price']) else 0
                investors = int(row['current_investors']) if pd.notna(row['current_investors']) else 0
                
                fund_info = fund_details_dict.get(fcode, {'name': 'N/A', 'type': 'N/A'})
                
                # Trend gücü
                if trend_slope > 0.5 and positive_weeks >= weeks_with_data * 0.7:
                    strength = "🟢 ÇOK GÜÇLÜ"
                elif trend_slope > 0.2 and positive_weeks >= weeks_with_data * 0.6:
                    strength = "🟡 GÜÇLÜ"
                else:
                    strength = "🟠 ORTA"
                
                response += f"{i}. {fcode} - {strength}\n"
                response += f"   📈 {weeks_to_analyze} Haftalık Değişim: %{total_change:+.2f}\n"
                response += f"   📊 Haftalık Ortalama: %{avg_weekly_change:+.2f}\n"
                response += f"   ✅ Pozitif Hafta: {positive_weeks}/{weeks_with_data}\n"
                response += f"   📉 Haftalık Volatilite: %{volatility:.2f}\n"
                response += f"   💰 Güncel Fiyat: {current_price:.4f} TL\n"
                response += f"   👥 Yatırımcı: {investors:,} kişi\n"
                response += f"   🏷️ Tür: {fund_info['type']}\n"
                if fund_info['name'] != 'N/A':
                    response += f"   📝 {fund_info['name'][:35]}...\n"
                response += f"\n"
            
            if len(downtrend_funds) > 0:
                response += f"\n📉 DÜŞEN TREND ({len(downtrend_funds)} fon):\n\n"
                
                for i, (_, row) in enumerate(downtrend_funds.tail(3).iterrows(), 1):
                    fcode = row['fcode']
                    total_change = float(row['total_change_pct']) if pd.notna(row['total_change_pct']) else 0
                    positive_weeks = int(row['positive_weeks']) if pd.notna(row['positive_weeks']) else 0
                    weeks_with_data = int(row['weeks_with_data']) if pd.notna(row['weeks_with_data']) else 0
                    
                    response += f"{i}. {fcode}\n"
                    response += f"   📉 {weeks_to_analyze} Haftalık Değişim: %{total_change:+.2f}\n"
                    response += f"   ❌ Pozitif Hafta: {positive_weeks}/{weeks_with_data}\n\n"
            
            # Özet istatistikler
            response += f"📊 HAFTALIK TREND ÖZETİ:\n"
            response += f"   • Toplam Analiz: {len(result)} fon\n"
            response += f"   • Yükselen Trend: {len(uptrend_funds)} fon (%{len(uptrend_funds)/len(result)*100:.0f})\n"
            response += f"   • Düşen Trend: {len(downtrend_funds)} fon (%{len(downtrend_funds)/len(result)*100:.0f})\n"
            
            if len(uptrend_funds) > 0:
                best_fund = uptrend_funds.iloc[0]
                response += f"   • En Güçlü Trend: {best_fund['fcode']} (%{best_fund['total_change_pct']:+.1f})\n"
            
            if len(downtrend_funds) > 0:
                worst_fund = downtrend_funds.iloc[-1]
                response += f"   • En Zayıf Trend: {worst_fund['fcode']} (%{worst_fund['total_change_pct']:+.1f})\n"
            
            # Piyasa yorumu
            uptrend_ratio = len(uptrend_funds) / len(result) if len(result) > 0 else 0
            
            response += f"\n💡 PİYASA YORUMU:\n"
            if uptrend_ratio > 0.7:
                response += f"   🟢 Piyasa genel olarak YÜKSELIŞTE (%{uptrend_ratio*100:.0f} pozitif)\n"
            elif uptrend_ratio > 0.5:
                response += f"   🟡 Piyasa DENGELİ görünüyor (%{uptrend_ratio*100:.0f} pozitif)\n"
            else:
                response += f"   🔴 Piyasa genel olarak DÜŞÜŞTE (%{uptrend_ratio*100:.0f} pozitif)\n"
            
            return response
            
        except Exception as e:
            print(f"❌ Haftalık trend analizi hatası: {e}")
            return f"❌ Haftalık trend analizi hatası: {e}"
        
    def handle_monthly_leaders(self, question):
        """Aylık getiri liderleri"""
        print("📊 Aylık liderler analiz ediliyor...")
        
        try:
            # Son 12 ayın liderleri
            query = """
            WITH monthly_performance AS (
                SELECT 
                    fcode,
                    DATE_TRUNC('month', pdate) as month,
                    FIRST_VALUE(price) OVER (PARTITION BY fcode, DATE_TRUNC('month', pdate) ORDER BY pdate) as month_start_price,
                    LAST_VALUE(price) OVER (PARTITION BY fcode, DATE_TRUNC('month', pdate) ORDER BY pdate 
                        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as month_end_price,
                    COUNT(*) OVER (PARTITION BY fcode, DATE_TRUNC('month', pdate)) as days_in_month
                FROM tefasfunds
                WHERE pdate >= CURRENT_DATE - INTERVAL '12 months'
                AND investorcount > 100
            ),
            monthly_returns AS (
                SELECT DISTINCT
                    fcode,
                    month,
                    ((month_end_price / month_start_price) - 1) * 100 as monthly_return,
                    days_in_month
                FROM monthly_performance
                WHERE month_start_price > 0 AND month_end_price > 0
                AND days_in_month >= 15  -- En az 15 gün veri
            ),
            leaders AS (
                SELECT 
                    month,
                    fcode,
                    monthly_return,
                    ROW_NUMBER() OVER (PARTITION BY month ORDER BY monthly_return DESC) as rank_desc,
                    ROW_NUMBER() OVER (PARTITION BY month ORDER BY monthly_return ASC) as rank_asc
                FROM monthly_returns
            )
            SELECT *
            FROM leaders
            WHERE rank_desc <= 3 OR rank_asc <= 1  -- Her ay için top 3 ve en kötü
            ORDER BY month DESC, rank_desc
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return "❌ Aylık lider analizi için veri bulunamadı."
            
            response = f"\n📅 AYLIK GETİRİ LİDERLERİ (Son 12 Ay)\n"
            response += f"{'='*50}\n\n"
            
            # Ayları grupla
            months = result['month'].unique()
            
            for month in sorted(months, reverse=True)[:6]:  # Son 6 ay göster
                month_data = result[result['month'] == month]
                month_str = pd.to_datetime(month).strftime('%Y %B')
                
                response += f"📅 {month_str}:\n"
                
                # En iyi 3
                top_3 = month_data[month_data['rank_desc'] <= 3].sort_values('rank_desc')
                for _, row in top_3.iterrows():
                    rank = int(row['rank_desc'])
                    fcode = row['fcode']
                    monthly_return = float(row['monthly_return'])
                    
                    emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉"
                    response += f"   {emoji} {fcode}: %{monthly_return:+.2f}\n"
                
                # En kötü
                worst = month_data[month_data['rank_asc'] == 1]
                if not worst.empty:
                    worst_row = worst.iloc[0]
                    response += f"   📉 En Kötü: {worst_row['fcode']} (%{worst_row['monthly_return']:+.2f})\n"
                
                response += f"\n"
            
            # Genel istatistikler
            all_time_best = result.loc[result['monthly_return'].idxmax()]
            all_time_worst = result.loc[result['monthly_return'].idxmin()]
            
            response += f"🏆 TÜM ZAMANLAR:\n"
            response += f"   • En İyi Aylık: {all_time_best['fcode']} - %{all_time_best['monthly_return']:+.2f}\n"
            response += f"     ({pd.to_datetime(all_time_best['month']).strftime('%Y %B')})\n"
            response += f"   • En Kötü Aylık: {all_time_worst['fcode']} - %{all_time_worst['monthly_return']:+.2f}\n"
            response += f"     ({pd.to_datetime(all_time_worst['month']).strftime('%Y %B')})\n"
            
            return response
            
        except Exception as e:
            print(f"❌ Aylık liderler analizi hatası: {e}")
            return f"❌ Aylık liderler analizi hatası: {e}"
    
    def handle_year_to_date_analysis(self, question):
        """Yıl başından bu yana analiz (YTD)"""
        print("📊 Yıl başından bu yana (YTD) analiz yapılıyor...")
        
        current_year = datetime.now().year
        year_start = f"{current_year}-01-01"
        
        try:
            query = f"""
            WITH ytd_start AS (
                SELECT DISTINCT ON (fcode) fcode, price as start_price, pdate as start_date
                FROM tefasfunds
                WHERE pdate >= '{year_start}'::date
                AND pdate <= '{year_start}'::date + INTERVAL '7 days'
                AND investorcount > 50
                ORDER BY fcode, pdate ASC
            ),
            ytd_current AS (
                SELECT DISTINCT ON (fcode) fcode, price as current_price, pdate as current_date,
                    investorcount, fcapacity
                FROM tefasfunds
                WHERE pdate >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY fcode, pdate DESC
            ),
            ytd_performance AS (
                SELECT 
                    c.fcode,
                    s.start_price,
                    c.current_price,
                    s.start_date,
                    c.current_date,
                    ((c.current_price / s.start_price) - 1) * 100 as ytd_return,
                    c.investorcount,
                    c.fcapacity,
                    c.current_date - s.start_date as days_elapsed
                FROM ytd_current c
                JOIN ytd_start s ON c.fcode = s.fcode
                WHERE s.start_price > 0 AND c.current_price > 0
            )
            SELECT *
            FROM ytd_performance
            ORDER BY ytd_return DESC
            LIMIT 25
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return f"❌ {current_year} yılı başından bu yana veri bulunamadı."
            
            # Fund details
            fund_codes = result['fcode'].tolist()
            fund_details_dict = {}
            
            try:
                details_df = self.coordinator.db.get_all_fund_details()
                for _, detail_row in details_df.iterrows():
                    if detail_row['fcode'] in fund_codes:
                        fund_details_dict[detail_row['fcode']] = {
                            'name': detail_row.get('fund_name', 'N/A'),
                            'type': detail_row.get('fund_type', 'N/A')
                        }
            except:
                pass
            
            response = f"\n📅 {current_year} YIL BAŞINDAN BU YANA (YTD) EN İYİLER\n"
            response += f"{'='*55}\n\n"
            
            # Tarih bilgisi
            days_passed = (datetime.now() - datetime(current_year, 1, 1)).days
            response += f"📊 Analiz Dönemi: 1 Ocak {current_year} - {datetime.now().strftime('%d %B %Y')}\n"
            response += f"📅 Geçen Gün: {days_passed}\n"
            response += f"📈 Toplam Analiz: {len(result)} fon\n\n"
            
            response += f"🏆 YTD PERFORMANS LİDERLERİ:\n\n"
            
            for i, (_, row) in enumerate(result.head(15).iterrows(), 1):
                fcode = row['fcode']
                ytd_return = float(row['ytd_return'])
                start_price = float(row['start_price'])
                current_price = float(row['current_price'])
                investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                
                fund_info = fund_details_dict.get(fcode, {'name': 'N/A', 'type': 'N/A'})
                
                # Performans kategorisi
                if ytd_return > 50:
                    perf_emoji = "🚀"
                    perf_text = "MUHTEŞEM"
                elif ytd_return > 30:
                    perf_emoji = "🔥"
                    perf_text = "ÇOK İYİ"
                elif ytd_return > 15:
                    perf_emoji = "📈"
                    perf_text = "İYİ"
                else:
                    perf_emoji = "➕"
                    perf_text = "POZİTİF"
                
                response += f"{i:2d}. {fcode} {perf_emoji} {perf_text}\n"
                response += f"    📊 YTD Getiri: %{ytd_return:+.2f}\n"
                response += f"    💰 Yıl Başı: {start_price:.4f} → Şimdi: {current_price:.4f} TL\n"
                response += f"    👥 Yatırımcı: {investors:,} kişi\n"
                response += f"    🏷️ Tür: {fund_info['type']}\n"
                if fund_info['name'] != 'N/A':
                    response += f"    📝 {fund_info['name'][:40]}...\n"
                response += f"\n"
            
            # İstatistikler
            avg_ytd = result['ytd_return'].mean()
            positive_count = len(result[result['ytd_return'] > 0])
            
            response += f"📊 {current_year} YTD İSTATİSTİKLERİ:\n"
            response += f"   • Ortalama YTD Getiri: %{avg_ytd:+.2f}\n"
            response += f"   • Pozitif Getiri: {positive_count}/{len(result)} fon\n"
            response += f"   • En İyi YTD: {result.iloc[0]['fcode']} (%{result.iloc[0]['ytd_return']:+.2f})\n"
            
            # Kategoriler
            response += f"\n🎯 PERFORMANS DAĞILIMI:\n"
            excellent = len(result[result['ytd_return'] > 50])
            very_good = len(result[(result['ytd_return'] > 30) & (result['ytd_return'] <= 50)])
            good = len(result[(result['ytd_return'] > 15) & (result['ytd_return'] <= 30)])
            
            response += f"   🚀 Muhteşem (>%50): {excellent} fon\n"
            response += f"   🔥 Çok İyi (%30-50): {very_good} fon\n"
            response += f"   📈 İyi (%15-30): {good} fon\n"
            
            return response
            
        except Exception as e:
            print(f"❌ YTD analizi hatası: {e}")
            return f"❌ YTD analizi hatası: {e}"
    
    def handle_long_term_stability(self, question):
        """Uzun dönem istikrar analizi (5 yıl)"""
        print("📊 Uzun dönem istikrar analizi yapılıyor...")
        
        try:
            # Son 5 yıl = 1260 işlem günü
            query = """
            WITH long_term_data AS (
                SELECT 
                    fcode,
                    price,
                    pdate,
                    LAG(price) OVER (PARTITION BY fcode ORDER BY pdate) as prev_price
                FROM tefasfunds
                WHERE pdate >= CURRENT_DATE - INTERVAL '5 years'
                AND investorcount > 100
            ),
            fund_stats AS (
                SELECT 
                    fcode,
                    COUNT(*) as total_days,
                    MIN(pdate) as start_date,
                    MAX(pdate) as end_date,
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    AVG(price) as avg_price,
                    STDDEV(price) as price_std,
                    -- Günlük getiriler
                    AVG(CASE WHEN prev_price > 0 THEN (price - prev_price) / prev_price ELSE NULL END) as avg_daily_return,
                    STDDEV(CASE WHEN prev_price > 0 THEN (price - prev_price) / prev_price ELSE NULL END) as daily_return_std,
                    -- Pozitif gün oranı
                    SUM(CASE WHEN price > prev_price THEN 1 ELSE 0 END)::float / 
                        NULLIF(SUM(CASE WHEN prev_price IS NOT NULL THEN 1 ELSE 0 END), 0) as positive_days_ratio,
                    -- Toplam getiri
                    (SELECT price FROM tefasfunds WHERE fcode = ltd.fcode ORDER BY pdate DESC LIMIT 1) as current_price,
                    (SELECT price FROM tefasfunds WHERE fcode = ltd.fcode ORDER BY pdate ASC LIMIT 1) as first_price
                FROM long_term_data ltd
                GROUP BY fcode
                HAVING COUNT(*) >= 1000  -- En az 4 yıllık veri
            ),
            stability_scores AS (
                SELECT 
                    fcode,
                    total_days,
                    start_date,
                    end_date,
                    current_price,
                    first_price,
                    ((current_price / first_price) - 1) * 100 as total_return,
                    -- Yıllık getiri
                    POWER((current_price / first_price), 365.0 / (end_date - start_date)) - 1 as annual_return,
                    -- Volatilite (yıllık)
                    daily_return_std * SQRT(252) as annual_volatility,
                    -- Sharpe benzeri oran
                    CASE 
                        WHEN daily_return_std > 0 THEN 
                            (avg_daily_return * 252) / (daily_return_std * SQRT(252))
                        ELSE 0 
                    END as sharpe_like_ratio,
                    -- İstikrar skoru (düşük volatilite + tutarlı getiri)
                    positive_days_ratio * 100 as consistency_score,
                    -- Maksimum düşüş yaklaşımı
                    ((max_price - min_price) / max_price) * 100 as price_range_pct
                FROM fund_stats
                WHERE first_price > 0 AND current_price > 0
            )
            SELECT *
            FROM stability_scores
            WHERE annual_volatility > 0
            ORDER BY (consistency_score / NULLIF(annual_volatility, 1)) DESC  -- İstikrar = tutarlılık / volatilite
            LIMIT 20
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return "❌ 5 yıllık istikrar analizi için yeterli veri bulunamadı."
            
            # Fund details
            fund_codes = result['fcode'].tolist()
            fund_details_dict = {}
            
            try:
                details_df = self.coordinator.db.get_all_fund_details()
                for _, detail_row in details_df.iterrows():
                    if detail_row['fcode'] in fund_codes:
                        fund_details_dict[detail_row['fcode']] = {
                            'name': detail_row.get('fund_name', 'N/A'),
                            'type': detail_row.get('fund_type', 'N/A')
                        }
            except:
                pass
            
            response = f"\n🏛️ SON 5 YILIN EN İSTİKRARLI FONLARI\n"
            response += f"{'='*50}\n\n"
            response += f"📊 İstikrar Kriterleri:\n"
            response += f"   • Düşük volatilite\n"
            response += f"   • Tutarlı pozitif getiri\n"
            response += f"   • Yüksek Sharpe oranı\n"
            response += f"   • En az 4 yıllık veri\n\n"
            
            response += f"🏆 EN İSTİKRARLI FONLAR:\n\n"
            
            for i, (_, row) in enumerate(result.head(10).iterrows(), 1):
                fcode = row['fcode']
                total_days = int(row['total_days'])
                total_return = float(row['total_return'])
                annual_return = float(row['annual_return']) * 100
                annual_volatility = float(row['annual_volatility']) * 100
                consistency_score = float(row['consistency_score'])
                sharpe_ratio = float(row['sharpe_like_ratio'])
                current_price = float(row['current_price'])
                
                fund_info = fund_details_dict.get(fcode, {'name': 'N/A', 'type': 'N/A'})
                
                # İstikrar seviyesi
                if consistency_score > 55 and annual_volatility < 15:
                    stability = "🟢 ÇOK İSTİKRARLI"
                elif consistency_score > 50 and annual_volatility < 20:
                    stability = "🟡 İSTİKRARLI"
                else:
                    stability = "🟠 ORTA İSTİKRARLI"
                
                response += f"{i:2d}. {fcode} - {stability}\n"
                response += f"    📈 5 Yıllık Toplam Getiri: %{total_return:+.2f}\n"
                response += f"    📊 Yıllık Ortalama: %{annual_return:+.2f}\n"
                response += f"    📉 Yıllık Volatilite: %{annual_volatility:.2f}\n"
                response += f"    ⚡ Sharpe Oranı: {sharpe_ratio:.3f}\n"
                response += f"    ✅ Pozitif Gün Oranı: %{consistency_score:.1f}\n"
                response += f"    📅 Veri Süresi: {total_days} gün ({total_days/252:.1f} yıl)\n"
                response += f"    💰 Güncel Fiyat: {current_price:.4f} TL\n"
                response += f"    🏷️ Tür: {fund_info['type']}\n"
                if fund_info['name'] != 'N/A':
                    response += f"    📝 {fund_info['name'][:40]}...\n"
                response += f"\n"
            
            # En istikrarlı fon detayı
            most_stable = result.iloc[0]
            
            response += f"🥇 EN İSTİKRARLI FON: {most_stable['fcode']}\n"
            response += f"   • 5 yılda sadece %{most_stable['annual_volatility']*100:.1f} volatilite\n"
            response += f"   • %{most_stable['consistency_score']:.1f} oranında pozitif gün\n"
            response += f"   • Tutarlı %{most_stable['annual_return']*100:+.1f} yıllık getiri\n"
            
            return response
            
        except Exception as e:
            print(f"❌ İstikrar analizi hatası: {e}")
            return f"❌ İstikrar analizi hatası: {e}"
    
    @staticmethod
    def is_time_based_question(question):
        """Sorunun zaman bazlı olup olmadığını kontrol et"""
        time_keywords = [
            'son 3 ay', 'son 6 ay', 'son 1 yıl', 'son 2 yıl',
            'haftalık', 'weekly', 'hafta bazında',
            'aylık', 'ay bazında', 'monthly',
            'yıl başından', 'ytd', 'year to date',
            '5 yıl', 'istikrarlı', 'tutarlı', 'stable',
            'trend', 'dönem', 'periyot'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in time_keywords)