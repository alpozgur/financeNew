# technical_analysis.py

import pandas as pd
from risk_assessment import RiskAssessment

class TechnicalAnalysis:
    def __init__(self, coordinator, active_funds, ai_provider=None):
        self.coordinator = coordinator
        self.active_funds = active_funds
        self.ai_provider = ai_provider

    def handle_macd_signals_sql(self, question):
        """Optimize edilmiş MACD analizi - TEK SORGU"""
        print("📊 SQL ile MACD sinyali analiz ediliyor (Optimized)...")

        # Pozitif/negatif sinyali tespit et
        is_positive = any(word in question.lower() for word in ['pozitif', 'positive', 'alım', 'buy'])
        signal_type = "pozitif" if is_positive else "negatif"
        operator = ">" if is_positive else "<"

        try:
            # TEK SORGUDA TÜM VERİLER - JOIN ile
            query = f"""
            SELECT 
                ti.fcode,
                ti.macd_line,
                ti.current_price,
                ti.investorcount,
                ti.rsi_14,
                ti.stochastic_14,
                ti.bb_position,
                ti.price_vs_sma20,
                ti.days_since_last_trade,
                ti.data_points,
                COALESCE(lf.ftitle, 'N/A') as fund_name,
                CASE 
                    WHEN lf.ftitle LIKE '%HİSSE%' THEN 'Hisse'
                    WHEN lf.ftitle LIKE '%TAHVİL%' THEN 'Tahvil'
                    WHEN lf.ftitle LIKE '%PARA%' THEN 'Para Piyasası'
                    WHEN lf.ftitle LIKE '%ALTIN%' THEN 'Kıymetli Maden'
                    WHEN lf.ftitle LIKE '%KATILIM%' THEN 'Katılım'
                    ELSE 'Karma'
                END as fund_type
            FROM mv_fund_technical_indicators ti
            LEFT JOIN mv_latest_fund_data lf ON ti.fcode = lf.fcode
            WHERE ti.macd_line {operator} 0
            AND ti.days_since_last_trade < 14
            ORDER BY ABS(ti.macd_line) DESC
            LIMIT 20
            """

            result = self.coordinator.db.execute_query(query)
            if result.empty:
                return f"❌ {signal_type.upper()} MACD sinyali olan fon bulunamadı."

            print(f"   ✅ SQL analizi: {len(result)} fon bulundu")

            response = f"\n📊 MACD SİNYALİ {signal_type.upper()} - SQL ANALİZİ\n"
            response += f"{'='*60}\n\n"
            response += f"🎯 Toplam {len(result)} fon {signal_type} MACD sinyali veriyor\n\n"

            for i, (_, row) in enumerate(result.head(15).iterrows(), 1):
                fcode = row['fcode']
                macd_value = float(row['macd_line'])
                current_price = float(row['current_price'])
                investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                days_inactive = int(row['days_since_last_trade'])
                rsi = float(row['rsi_14'])
                fund_name = row['fund_name']
                fund_type = row['fund_type']

                if abs(macd_value) > 0.01:
                    strength = "🟢 GÜÇLÜ"
                elif abs(macd_value) > 0.005:
                    strength = "🟡 ORTA"
                else:
                    strength = "🟠 ZAYIF"

                # İnaktif uyarısı
                activity_warning = f" ⚠️ {days_inactive} gündür işlem yok" if days_inactive > 7 else ""

                response += f"{i:2d}. {fcode} - {strength}{activity_warning}\n"
                response += f"    📊 MACD: {macd_value:+.6f}\n"
                response += f"    💲 Fiyat: {current_price:.4f} TL\n"
                response += f"    📈 RSI: {rsi:.1f}\n"
                response += f"    👥 Yatırımcı: {investors:,} kişi\n"
                response += f"    🏷️ Tür: {fund_type}\n"
                if fund_name != 'N/A':
                    response += f"    📝 Adı: {fund_name[:40]}...\n"
                response += f"\n"

            avg_macd = result['macd_line'].mean()
            strongest_macd = result.iloc[0]

            response += f"📊 {signal_type.upper()} MACD İSTATİSTİKLERİ:\n"
            response += f"   Ortalama MACD: {avg_macd:+.6f}\n"
            response += f"   En Güçlü: {strongest_macd['fcode']} ({strongest_macd['macd_line']:+.6f})\n"
            response += f"   Toplam Bulunan: {len(result)} fon\n"

            return response

        except Exception as e:
            print(f"   ❌ SQL MACD analizi hatası: {e}")
            return f"❌ SQL MACD analizi hatası: {e}"

    def handle_bollinger_signals_sql(self, question):
        """Optimize edilmiş Bollinger Bantları analizi"""
        print("📊 SQL ile Bollinger Bantları analiz ediliyor (Optimized)...")
        
        # Alt/üst banda yakın tespit et
        is_lower_band = any(word in question.lower() for word in ['alt banda', 'lower band', 'alt', 'düşük'])
        band_type = "alt banda" if is_lower_band else "üst banda"
        bb_condition = "< 0.3" if is_lower_band else "> 0.7"
        
        try:
            # Optimize edilmiş sorgu - JOIN ile
            query = f"""
            SELECT 
                ti.fcode,
                ti.current_price,
                ti.sma_20,
                ti.bb_upper as upper_band,
                ti.bb_lower as lower_band,
                ti.bb_position as bb_percent,
                ti.investorcount,
                ti.rsi_14,
                ti.stochastic_14,
                ti.days_since_last_trade,
                COALESCE(lf.ftitle, 'N/A') as fund_name,
                CASE 
                    WHEN lf.ftitle LIKE '%HİSSE%' THEN 'Hisse'
                    WHEN lf.ftitle LIKE '%TAHVİL%' THEN 'Tahvil'
                    WHEN lf.ftitle LIKE '%PARA%' THEN 'Para Piyasası'
                    ELSE 'Karma'
                END as fund_type
            FROM mv_fund_technical_indicators ti
            LEFT JOIN mv_latest_fund_data lf ON ti.fcode = lf.fcode
            WHERE ti.bb_position {bb_condition}
            AND ti.days_since_last_trade < 30
            ORDER BY {'ti.bb_position ASC' if is_lower_band else 'ti.bb_position DESC'}
            LIMIT 20
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return f"❌ {band_type.upper()} yakın Bollinger sinyali olan fon bulunamadı."
            
            print(f"   ✅ SQL analizi: {len(result)} fon bulundu")
            
            response = f"\n📊 BOLLİNGER BANTLARI - {band_type.upper()} YAKIN FONLAR\n"
            response += f"{'='*55}\n\n"
            response += f"🎯 {len(result)} fon {band_type} yakın pozisyonda\n\n"
            
            for i, (_, row) in enumerate(result.head(15).iterrows(), 1):
                fcode = row['fcode']
                current_price = float(row['current_price'])
                bb_percent = float(row['bb_percent'])
                upper_band = float(row['upper_band'])
                lower_band = float(row['lower_band'])
                sma_20 = float(row['sma_20'])
                investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                rsi = float(row['rsi_14'])
                days_inactive = int(row['days_since_last_trade'])
                fund_type = row['fund_type']
                
                # Pozisyon belirleme
                if bb_percent < 0.2:
                    position = "🔴 ALT BANT ÇOK YAKIN"
                elif bb_percent < 0.3:
                    position = "🟠 ALT BANT YAKIN"
                elif bb_percent > 0.8:
                    position = "🟢 ÜST BANT ÇOK YAKIN"
                elif bb_percent > 0.7:
                    position = "🟡 ÜST BANT YAKIN"
                else:
                    position = "⚪ ORTA BÖLGE"
                
                activity_warning = f" ({days_inactive}g)" if days_inactive > 7 else ""
                
                response += f"{i:2d}. {fcode} - {position}{activity_warning}\n"
                response += f"    💲 Fiyat: {current_price:.4f} TL\n"
                response += f"    📊 BB%: {bb_percent:.3f} (%{bb_percent*100:.1f})\n"
                response += f"    📈 RSI: {rsi:.1f}\n"
                response += f"    📈 Üst Bant: {upper_band:.4f} TL\n"
                response += f"    📉 Alt Bant: {lower_band:.4f} TL\n"
                response += f"    📊 SMA(20): {sma_20:.4f} TL\n"
                response += f"    👥 Yatırımcı: {investors:,} kişi\n"
                response += f"    🏷️ Tür: {fund_type}\n"
                response += f"\n"
            
            # İstatistikler
            avg_bb_percent = result['bb_percent'].mean()
            closest = result.iloc[0]
            
            response += f"📊 {band_type.upper()} BOLLİNGER İSTATİSTİKLERİ:\n"
            response += f"   Ortalama BB%: {avg_bb_percent:.3f}\n"
            response += f"   En Yakın: {closest['fcode']} ({closest['bb_percent']:.3f})\n"
            response += f"   Toplam Bulunan: {len(result)} fon\n"
            
            return response
            
        except Exception as e:
            print(f"   ❌ SQL Bollinger analizi hatası: {e}")
            return f"❌ SQL Bollinger analizi hatası: {e}"

    def handle_rsi_signals_sql(self, question):
        """Optimize edilmiş RSI analizi"""
        print("📊 SQL ile RSI analiz ediliyor (Optimized)...")
        
        # RSI seviyesini tespit et
        is_oversold = any(word in question.lower() for word in ['düşük', 'oversold', 'aşırı satım', '30', 'altında'])
        is_overbought = any(word in question.lower() for word in ['yüksek', 'overbought', 'aşırı alım', '70', 'üstünde'])
        
        if is_oversold:
            condition = "oversold"
            rsi_condition = "< 35"
            order_by = "ti.rsi_14 ASC"
        elif is_overbought:
            condition = "overbought" 
            rsi_condition = "> 65"
            order_by = "ti.rsi_14 DESC"
        else:
            condition = "neutral"
            rsi_condition = "BETWEEN 40 AND 60"
            order_by = "ABS(ti.rsi_14 - 50) ASC"
        
        try:
            # Basitleştirilmiş sorgu - MV kullanarak
            query = f"""
            SELECT 
                ti.fcode,
                ti.current_price,
                ti.rsi_14,
                ti.investorcount,
                ti.days_since_last_trade,
                COALESCE(lf.ftitle, 'N/A') as fund_name,
                CASE 
                    WHEN lf.ftitle LIKE '%HİSSE%' THEN 'Hisse'
                    WHEN lf.ftitle LIKE '%TAHVİL%' THEN 'Tahvil'
                    WHEN lf.ftitle LIKE '%PARA%' THEN 'Para Piyasası'
                    ELSE 'Karma'
                END as fund_type
            FROM mv_fund_technical_indicators ti
            LEFT JOIN mv_latest_fund_data lf ON ti.fcode = lf.fcode
            WHERE ti.rsi_14 {rsi_condition}
            AND ti.days_since_last_trade < 30
            ORDER BY {order_by}
            LIMIT 20
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return f"❌ RSI {condition} seviyesinde fon bulunamadı."
            
            print(f"   ✅ SQL analizi: {len(result)} fon bulundu")
            
            response = f"\n📊 RSI ANALİZİ - {condition.upper()} SEVİYE\n"
            response += f"{'='*40}\n\n"
            response += f"🎯 {len(result)} fon RSI {condition} seviyesinde\n\n"
            
            for i, (_, row) in enumerate(result.head(15).iterrows(), 1):
                fcode = row['fcode']
                current_price = float(row['current_price'])
                rsi_value = float(row['rsi_14'])
                investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                fund_name = row['fund_name']
                fund_type = row['fund_type']
                
                # RSI kategorisi
                if rsi_value < 30:
                    rsi_category = "🔴 AŞIRI SATIM"
                elif rsi_value < 50:
                    rsi_category = "🟡 DÜŞÜK"
                elif rsi_value > 70:
                    rsi_category = "🟢 AŞIRI ALIM"
                elif rsi_value > 50:
                    rsi_category = "🟠 YÜKSEK"
                else:
                    rsi_category = "⚪ NORMAL"
                
                response += f"{i:2d}. {fcode} - {rsi_category}\n"
                response += f"    📊 RSI: {rsi_value:.1f}\n"
                response += f"    💲 Fiyat: {current_price:.4f} TL\n"
                response += f"    👥 Yatırımcı: {investors:,} kişi\n"
                response += f"    🏷️ Tür: {fund_type}\n"
                if fund_name != 'N/A':
                    response += f"    📝 Adı: {fund_name[:35]}...\n"
                response += f"\n"
            
            # İstatistikler
            avg_rsi = result['rsi_14'].mean()
            extreme = result.iloc[0]
            
            response += f"📊 RSI {condition.upper()} İSTATİSTİKLERİ:\n"
            response += f"   Ortalama RSI: {avg_rsi:.1f}\n"
            response += f"   En Ekstrem: {extreme['fcode']} ({extreme['rsi_14']:.1f})\n"
            response += f"   Toplam Bulunan: {len(result)} fon\n"
            
            return response
            
        except Exception as e:
            print(f"   ❌ SQL RSI analizi hatası: {e}")
            return f"❌ SQL RSI analizi hatası: {e}"

    def handle_moving_average_signals_sql(self, question):
        """Optimize edilmiş Hareketli Ortalama analizi"""
        print("📊 SQL ile Hareketli Ortalama analiz ediliyor (Optimized)...")
        
        # Golden/Death Cross tespit et
        is_golden_cross = any(word in question.lower() for word in ['golden cross', 'alım sinyali', 'pozitif'])
        signal_type = "Golden Cross" if is_golden_cross else "Death Cross"
        ma_condition = ">" if is_golden_cross else "<"
        
        try:
            # Optimize edilmiş sorgu - MV kullanarak
            query = f"""
            SELECT 
                t.fcode,
                t.current_price,
                t.sma_10,
                t.sma_20,
                t.sma_50,
                t.rsi_14,
                t.investorcount,
                t.days_since_last_trade,
                CASE 
                    WHEN t.sma_50 > 0 THEN ((t.sma_20 / t.sma_50) - 1) * 100 
                    ELSE 0 
                END as ma_spread,
                lf.ftitle as fund_name,
                CASE 
                    WHEN lf.ftitle LIKE '%HİSSE%' THEN 'Hisse'
                    WHEN lf.ftitle LIKE '%TAHVİL%' THEN 'Tahvil'
                    ELSE 'Karma'
                END as fund_type
            FROM mv_fund_technical_indicators t
            LEFT JOIN mv_latest_fund_data lf ON t.fcode = lf.fcode
            WHERE t.sma_20 {ma_condition} t.sma_50
            AND t.sma_20 IS NOT NULL 
            AND t.sma_50 IS NOT NULL
            AND t.days_since_last_trade < 14
            AND t.data_points >= 50
            ORDER BY ABS(((t.sma_20 / NULLIF(t.sma_50, 0)) - 1) * 100) DESC
            LIMIT 25
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return f"❌ {signal_type} sinyali olan fon bulunamadı."
            
            print(f"   ✅ SQL analizi: {len(result)} fon bulundu")
            
            response = f"\n📊 HAREKETLİ ORTALAMA - {signal_type.upper()} SİNYALLERİ\n"
            response += f"{'='*55}\n\n"
            response += f"🎯 {len(result)} fon {signal_type} sinyali veriyor\n\n"
            
            for i, (_, row) in enumerate(result.head(15).iterrows(), 1):
                fcode = row['fcode']
                current_price = float(row['current_price'])
                sma_20 = float(row['sma_20'])
                sma_50 = float(row['sma_50'])
                ma_spread = float(row['ma_spread'])
                investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                rsi = float(row['rsi_14'])
                days_inactive = int(row['days_since_last_trade'])
                fund_name = row['fund_name']
                fund_type = row['fund_type']
                
                # Sinyal gücü
                if abs(ma_spread) > 5:
                    strength = "🟢 ÇOK GÜÇLÜ"
                elif abs(ma_spread) > 2:
                    strength = "🟡 GÜÇLÜ"
                elif abs(ma_spread) > 1:
                    strength = "🟠 ORTA"
                else:
                    strength = "⚪ ZAYIF"
                
                signal_icon = "🚀" if is_golden_cross else "📉"
                activity_note = f" ({days_inactive}g)" if days_inactive > 7 else ""
                
                response += f"{i:2d}. {fcode} - {strength} {signal_icon}{activity_note}\n"
                response += f"    💲 Fiyat: {current_price:.4f} TL\n"
                response += f"    📊 SMA20: {sma_20:.4f} TL\n"
                response += f"    📈 SMA50: {sma_50:.4f} TL\n"
                response += f"    📍 Fark: %{ma_spread:+.2f}\n"
                response += f"    📈 RSI: {rsi:.1f}\n"
                response += f"    👥 Yatırımcı: {investors:,} kişi\n"
                response += f"    🏷️ Tür: {fund_type}\n"
                response += f"\n"
            
            # İstatistikler
            avg_spread = result['ma_spread'].mean()
            strongest = result.iloc[0]
            
            response += f"📊 {signal_type.upper()} İSTATİSTİKLERİ:\n"
            response += f"   Ortalama Fark: %{avg_spread:+.2f}\n"
            response += f"   En Güçlü: {strongest['fcode']} (%{strongest['ma_spread']:+.2f})\n"
            response += f"   Toplam Bulunan: {len(result)} fon\n"
            
            return response
            
        except Exception as e:
            print(f"   ❌ SQL Moving Average analizi hatası: {e}")
            return f"❌ SQL Moving Average analizi hatası: {e}"

    def handle_general_technical_signals_sql(self, question):
        """Optimize edilmiş Genel Teknik Sinyal analizi"""
        print("📊 SQL ile Genel Teknik Sinyaller analiz ediliyor (Optimized)...")
        
        try:
            # Tamamen MV bazlı optimize sorgu
            query = """
            SELECT 
                ti.fcode,
                ti.current_price,
                ti.investorcount,
                ti.rsi_14,
                ti.macd_line,
                ti.bb_position,
                ti.price_vs_sma20,
                ti.days_since_last_trade,
                -- Period performance'tan getiriler
                COALESCE(pp.return_30d, 0) as momentum_30d,
                COALESCE(pp.return_90d, 0) as momentum_90d,
                -- Combined score
                CASE 
                    WHEN ti.rsi_14 < 30 AND ti.bb_position < 0.3 THEN 4
                    WHEN ti.rsi_14 < 30 OR ti.bb_position < 0.3 THEN 2
                    WHEN ti.rsi_14 > 70 AND ti.bb_position > 0.7 THEN -4
                    WHEN ti.rsi_14 > 70 OR ti.bb_position > 0.7 THEN -2
                    ELSE 0
                END +
                CASE 
                    WHEN ti.macd_line > 0.01 THEN 2
                    WHEN ti.macd_line > 0 THEN 1
                    WHEN ti.macd_line < -0.01 THEN -2
                    WHEN ti.macd_line < 0 THEN -1
                    ELSE 0
                END as technical_score,
                lf.ftitle as fund_name,
                CASE 
                    WHEN lf.ftitle LIKE '%HİSSE%' THEN 'Hisse'
                    WHEN lf.ftitle LIKE '%TAHVİL%' THEN 'Tahvil'
                    ELSE 'Karma'
                END as fund_type
            FROM mv_fund_technical_indicators ti
            LEFT JOIN mv_fund_period_performance pp ON ti.fcode = pp.fcode
            LEFT JOIN mv_latest_fund_data lf ON ti.fcode = lf.fcode
            WHERE ti.days_since_last_trade < 30
            AND ti.data_points >= 20
            AND (
                ti.rsi_14 < 30 OR ti.rsi_14 > 70 OR
                ABS(ti.macd_line) > 0.005 OR
                ti.bb_position < 0.3 OR ti.bb_position > 0.7 OR
                ABS(ti.price_vs_sma20) > 5
            )
            ORDER BY ABS(technical_score) DESC, ABS(COALESCE(pp.return_30d, 0)) DESC
            LIMIT 25
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return "❌ Güçlü teknik sinyal olan fon bulunamadı."
            
            print(f"   ✅ SQL analizi: {len(result)} fon bulundu")
            
            response = f"\n📊 GENEL TEKNİK SİNYAL ANALİZİ\n"
            response += f"{'='*55}\n\n"
            response += f"🎯 {len(result)} fon güçlü teknik sinyal veriyor\n\n"
            
            # Alım ve satım sinyallerini ayır
            buy_signals = result[result['technical_score'] > 0].copy()
            sell_signals = result[result['technical_score'] < 0].copy()
            
            # ALIM SİNYALLERİ
            if not buy_signals.empty:
                response += f"🟢 GÜÇLÜ ALIM SİNYALLERİ ({len(buy_signals)} fon):\n\n"
                
                for i, (_, row) in enumerate(buy_signals.head(8).iterrows(), 1):
                    fcode = row['fcode']
                    current_price = float(row['current_price'])
                    momentum_30d = float(row['momentum_30d'])
                    technical_score = int(row['technical_score'])
                    investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                    fund_type = row['fund_type']
                    rsi = float(row['rsi_14'])
                    macd = float(row['macd_line'])
                    bb_pos = float(row['bb_position'])
                    
                    # Sinyal gücü
                    if technical_score >= 4:
                        strength = "🟢 ÇOK GÜÇLÜ"
                    elif technical_score >= 3:
                        strength = "🟡 GÜÇLÜ"
                    else:
                        strength = "🟠 ORTA"
                    
                    # Pattern özeti
                    patterns = []
                    if rsi < 30: patterns.append("RSI oversold")
                    if bb_pos < 0.3: patterns.append("BB alt band")
                    if macd > 0: patterns.append("MACD pozitif")
                    
                    response += f"{i}. {fcode} - {strength} 🚀\n"
                    response += f"   💲 Fiyat: {current_price:.4f} TL\n"
                    response += f"   📊 30-Gün Getiri: %{momentum_30d:+.2f}\n"
                    response += f"   ⚡ Teknik Skor: +{technical_score}\n"
                    response += f"   🎯 Sinyaller: {', '.join(patterns)}\n"
                    response += f"   👥 Yatırımcı: {investors:,} kişi\n"
                    response += f"   🏷️ Tür: {fund_type}\n"
                    response += f"\n"
            
            # SATIM SİNYALLERİ
            if not sell_signals.empty:
                response += f"\n🔴 GÜÇLÜ SATIM SİNYALLERİ ({len(sell_signals)} fon):\n\n"
                
                for i, (_, row) in enumerate(sell_signals.head(5).iterrows(), 1):
                    fcode = row['fcode']
                    current_price = float(row['current_price'])
                    momentum_30d = float(row['momentum_30d'])
                    technical_score = int(row['technical_score'])
                    investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                    fund_type = row['fund_type']
                    rsi = float(row['rsi_14'])
                    macd = float(row['macd_line'])
                    bb_pos = float(row['bb_position'])
                    
                    # Sinyal gücü
                    if technical_score <= -4:
                        strength = "🔴 ÇOK GÜÇLÜ"
                    elif technical_score <= -3:
                        strength = "🟠 GÜÇLÜ"
                    else:
                        strength = "🟡 ORTA"
                    
                    # Pattern özeti
                    patterns = []
                    if rsi > 70: patterns.append("RSI overbought")
                    if bb_pos > 0.7: patterns.append("BB üst band")
                    if macd < 0: patterns.append("MACD negatif")
                    
                    response += f"{i}. {fcode} - {strength} 📉\n"
                    response += f"   💲 Fiyat: {current_price:.4f} TL\n"
                    response += f"   📊 30-Gün Getiri: %{momentum_30d:+.2f}\n"
                    response += f"   ⚡ Teknik Skor: {technical_score}\n"
                    response += f"   🎯 Sinyaller: {', '.join(patterns)}\n"
                    response += f"   👥 Yatırımcı: {investors:,} kişi\n"
                    response += f"   🏷️ Tür: {fund_type}\n"
                    response += f"\n"
            
            # GENEL İSTATİSTİKLER
            total_buy = len(buy_signals)
            total_sell = len(sell_signals)
            avg_momentum = result['momentum_30d'].mean()
            
            response += f"📊 GENEL TEKNİK SİNYAL İSTATİSTİKLERİ:\n"
            response += f"   🟢 Alım Sinyali: {total_buy} fon\n"
            response += f"   🔴 Satım Sinyali: {total_sell} fon\n"
            response += f"   📊 Ortalama 30-Gün Momentum: %{avg_momentum:+.2f}\n"
            response += f"   🎯 Toplam Analiz Edilen: {len(result)} fon\n"
            
            if total_buy > total_sell:
                response += f"\n💡 PİYASA YORUMU: Teknik sinyaller ALIMdan yana (%{total_buy/(total_buy+total_sell)*100:.0f})\n"
            elif total_sell > total_buy:
                response += f"\n💡 PİYASA YORUMU: Teknik sinyaller SATIMdan yana (%{total_sell/(total_buy+total_sell)*100:.0f})\n"
            else:
                response += f"\n💡 PİYASA YORUMU: Teknik sinyaller DENGELİ görünüyor\n"
            
            return response
            
        except Exception as e:
            print(f"   ❌ SQL Genel Teknik analizi hatası: {e}")
            return f"❌ SQL Genel Teknik analizi hatası: {e}"

    def handle_ai_pattern_analysis(self, question):
        """AI destekli pattern analizi handler - optimize edilmiş"""
        print("🤖 AI Pattern Analysis çağrıldı!")
        print(f"Soru: {question}")
        
        question_lower = question.lower()
        
        # Fon kodunu bul
        words = question.upper().split()
        fcode = None
        
        # Önce 3 harfli kelimeleri kontrol et
        potential_codes = [word for word in words if len(word) == 3 and word.isalpha()]
        
        if potential_codes:
            # Veritabanında kontrol et
            try:
                check_query = f"""
                SELECT DISTINCT fcode 
                FROM mv_fund_technical_indicators
                WHERE fcode IN ({','.join(f"'{code}'" for code in potential_codes)})
                LIMIT 1
                """
                result = self.coordinator.db.execute_query(check_query)
                if not result.empty:
                    fcode = result.iloc[0]['fcode']
                    print(f"✅ Fon kodu bulundu: {fcode}")
                        
            except Exception as e:
                print(f"Veritabanı kontrol hatası: {e}")
        
        # Eğer fon kodu bulunduysa tek fon analizi yap
        if fcode:
            return self._analyze_single_fund_pattern(fcode)
        else:
            # Fon kodu yoksa genel tarama yap
            return self._handle_general_ai_pattern_analysis()

    def _analyze_single_fund_pattern(self, fcode):
        """Tek fon için AI pattern analizi - optimize edilmiş"""
        try:
            # Tek sorguda tüm veriler
            query = f"""
            SELECT 
                ti.*,
                pp.return_30d,
                pp.return_90d,
                pp.volatility_30d,
                lf.ftitle as fund_name,
                -- Support/Resistance hesapla
                (SELECT MIN(price) FROM tefasfunds 
                 WHERE fcode = ti.fcode 
                 AND pdate >= CURRENT_DATE - INTERVAL '30 days') as support,
                (SELECT MAX(price) FROM tefasfunds 
                 WHERE fcode = ti.fcode 
                 AND pdate >= CURRENT_DATE - INTERVAL '30 days') as resistance
            FROM mv_fund_technical_indicators ti
            LEFT JOIN mv_fund_period_performance pp ON ti.fcode = pp.fcode
            LEFT JOIN mv_latest_fund_data lf ON ti.fcode = lf.fcode
            WHERE ti.fcode = '{fcode}'
            """

            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return f"❌ {fcode} için teknik veri bulunamadı."
            
            # Verileri al
            row = result.iloc[0]
            current_price = float(row['current_price'])
            rsi = float(row['rsi_14'])
            macd = float(row['macd_line'])
            bb_position = float(row['bb_position'])
            sma_20 = float(row['sma_20'])
            price_vs_sma20 = float(row['price_vs_sma20'])
            investors = int(row['investorcount'])
            support = float(row['support']) if row['support'] else current_price * 0.95
            resistance = float(row['resistance']) if row['resistance'] else current_price * 1.05
            return_30d = float(row['return_30d']) if pd.notna(row['return_30d']) else 0
            
            # Risk değerlendirmesi
            risk_data = {
                'fcode': fcode,
                'price_vs_sma20': price_vs_sma20,
                'rsi_14': rsi,
                'stochastic_14': float(row['stochastic_14']),
                'days_since_last_trade': int(row['days_since_last_trade']),
                'investorcount': investors
            }
            
            risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
            risk_warning = RiskAssessment.format_risk_warning(risk_assessment)
            
            # Eğer EXTREME risk varsa, AI analizi yapma
            if risk_assessment['risk_level'] == 'EXTREME':
                response = f"\n🤖 {fcode} - RİSK ANALİZİ\n"
                response += f"{'='*55}\n\n"
                response += risk_warning
                response += f"\n\n❌ Bu fon için AI pattern analizi yapılamıyor.\n"
                response += f"Önce risk faktörlerini araştırın!\n"
                return response

            # AI Prompt hazırla
            prompt = f"""
{fcode} fonu için teknik pattern analizi:

GÜNCEL VERİLER:
- Fiyat: {current_price:.4f} TL
- RSI: {rsi:.1f} {'(Aşırı Satım)' if rsi < 30 else '(Aşırı Alım)' if rsi > 70 else '(Normal)'}
- MACD: {macd:.6f} {'(Pozitif)' if macd > 0 else '(Negatif)'}
- Bollinger Pozisyon: %{bb_position*100:.0f} {'(Alt banda yakın)' if bb_position < 0.3 else '(Üst banda yakın)' if bb_position > 0.7 else '(Orta bölge)'}
- SMA20: {sma_20:.4f} TL (Fiyat %{price_vs_sma20:.1f} {'üstünde' if price_vs_sma20 > 0 else 'altında'})
- Support: {support:.4f} TL
- Resistance: {resistance:.4f} TL
- 30 Gün Getiri: %{return_30d:.2f}
- Yatırımcı: {investors:,} kişi

GÖREVLER:
1. Hangi teknik patternler görülüyor? (Double Bottom, Triangle, Flag vb.)
2. Trend yönü ve gücü nedir?
3. AL/SAT/BEKLE önerisi (1-10 güç skoru)
4. Entry point, Stop-loss ve Target fiyat öner
5. Risk/Reward oranı

Kısa, net ve aksiyona yönelik ol."""

            # AI Analizi
            if hasattr(self, 'ai_provider') and self.ai_provider and self.ai_provider.is_available():
                ai_analysis = self.ai_provider.query(prompt, "Sen teknik analiz uzmanısın.")
            else:
                # Fallback analiz
                ai_analysis = self._generate_single_fund_analysis(
                    fcode, current_price, rsi, macd, bb_position, 
                    sma_20, support, resistance, price_vs_sma20
                )
            
            # Sonucu formatla
            response = f"\n🤖 {fcode} - AI PATTERN RECOGNITION ANALİZİ\n"
            response += f"{'='*55}\n\n"
            
            response += f"📊 TEKNİK VERİLER:\n"
            response += f"💲 Fiyat: {current_price:.4f} TL\n"
            response += f"📈 RSI: {rsi:.1f}\n"
            response += f"📊 MACD: {macd:.6f}\n"
            response += f"📍 Bollinger: %{bb_position*100:.0f}\n"
            response += f"📊 SMA20: {sma_20:.4f} TL (%{price_vs_sma20:+.1f})\n"
            response += f"🎯 Support: {support:.4f} TL\n"
            response += f"🎯 Resistance: {resistance:.4f} TL\n"
            response += f"📊 30-Gün Getiri: %{return_30d:+.2f}\n"
            response += f"👥 Yatırımcı: {investors:,}\n\n"
            
            response += f"🤖 AI PATTERN ANALİZİ:\n"
            response += f"{'='*55}\n"
            response += ai_analysis
            
            # Risk uyarısını ekle
            if risk_warning and risk_assessment['risk_level'] in ['HIGH', 'MEDIUM']:
                response += f"\n{risk_warning}"

            return response
            
        except Exception as e:
            print(f"Analiz hatası: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ {fcode} analizi sırasında hata: {str(e)}"

    def _handle_general_ai_pattern_analysis(self):
        """Genel AI pattern taraması - optimize edilmiş"""
        print("🤖 AI ile pattern taraması yapılıyor...")
        
        # Optimize edilmiş sorgu
        query = """
        SELECT 
            ti.fcode,
            ti.current_price,
            ti.rsi_14,
            ti.stochastic_14,
            ti.macd_line,
            ti.bb_position,
            ti.price_vs_sma20,
            ti.sma_10,
            ti.sma_20,
            ti.sma_50,
            ti.investorcount,
            ti.days_since_last_trade,
            COALESCE(pp.return_30d, 0) as return_30d,
            lf.ftitle as fund_name,
            -- Technical score for ordering
            (
                CASE WHEN ti.rsi_14 < 30 THEN 2 ELSE 0 END +
                CASE WHEN ti.bb_position < 0.3 THEN 2 ELSE 0 END +
                CASE WHEN ti.macd_line > 0 THEN 1 ELSE -1 END +
                CASE WHEN ABS(ti.price_vs_sma20) > 10 THEN 1 ELSE 0 END
            ) as pattern_score
        FROM mv_fund_technical_indicators ti
        LEFT JOIN mv_fund_period_performance pp ON ti.fcode = pp.fcode
        LEFT JOIN mv_latest_fund_data lf ON ti.fcode = lf.fcode
        WHERE ti.data_points >= 30
        AND ti.days_since_last_trade < 30
        AND (
            ti.rsi_14 < 30 OR ti.rsi_14 > 70 OR
            ABS(ti.macd_line) > 0.01 OR
            ti.bb_position < 0.2 OR ti.bb_position > 0.8 OR
            ABS(ti.price_vs_sma20) > 5
        )
        ORDER BY pattern_score DESC, ti.days_since_last_trade ASC
        LIMIT 10
        """
        
        try:
            results = self.coordinator.db.execute_query(query)
            
            if results.empty:
                return "❌ Güçlü pattern sinyali veren fon bulunamadı."
            
            response = f"\n🤖 AI PATTERN TARAMASI - EN GÜÇLÜ SİNYALLER\n"
            response += f"{'='*55}\n\n"
            
            for idx, row in results.iterrows():
                fcode = row['fcode']
                days_inactive = int(row['days_since_last_trade'])
                pattern_score = int(row['pattern_score'])
                
                # Risk değerlendirmesi
                risk_data = {
                    'fcode': fcode,
                    'price_vs_sma20': row['price_vs_sma20'],
                    'rsi_14': row['rsi_14'],
                    'stochastic_14': row['stochastic_14'],
                    'days_since_last_trade': days_inactive,
                    'investorcount': int(row['investorcount'])
                }
                
                risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                
                # Pattern sinyalleri
                patterns = []
                
                # RSI sinyalleri
                if row['rsi_14'] < 30:
                    patterns.append("📉 RSI Oversold")
                elif row['rsi_14'] > 70:
                    patterns.append("📈 RSI Overbought")
                
                # MACD sinyalleri
                if row['macd_line'] > 0.01:
                    patterns.append("🟢 MACD Bullish")
                elif row['macd_line'] < -0.01:
                    patterns.append("🔴 MACD Bearish")
                
                # Bollinger Band sinyalleri
                if row['bb_position'] < 0.2:
                    patterns.append("⬇️ BB Alt Band")
                elif row['bb_position'] > 0.8:
                    patterns.append("⬆️ BB Üst Band")
                
                # SMA pozisyon
                if row['price_vs_sma20'] > 5:
                    patterns.append("🚀 SMA20 %5+ üstünde")
                elif row['price_vs_sma20'] < -5:
                    patterns.append("💥 SMA20 %5+ altında")
                
                # Risk faktörlerini pattern'lere ekle
                if risk_assessment['risk_level'] in ['EXTREME', 'HIGH']:
                    patterns.append(f"⚠️ {risk_assessment['risk_level']} RİSK")
                
                # Genel sinyal
                if pattern_score >= 3:
                    signal = "🟢 GÜÇLÜ AL SİNYALİ"
                elif pattern_score <= -1:
                    signal = "🔴 SAT SİNYALİ"
                else:
                    signal = "🟡 NÖTR"
                
                # Risk seviyesine göre sinyal güncelle
                if risk_assessment['risk_level'] == 'EXTREME':
                    signal = "⛔ EXTREME RİSK"
                elif risk_assessment['risk_level'] == 'HIGH' and signal == "🟢 GÜÇLÜ AL SİNYALİ":
                    signal = "🟡 RİSKLİ AL"
                
                # İnaktif uyarısı
                activity_warning = f" (⚠️ {days_inactive} gündür işlem yok)" if days_inactive > 7 else ""
                
                response += f"{idx+1}. {fcode} - {signal}{activity_warning}\n"
                response += f"   💲 Fiyat: {row['current_price']:.4f} TL\n"
                response += f"   📊 RSI: {row['rsi_14']:.1f} / Stoch: {row['stochastic_14']:.1f}\n"
                response += f"   📈 MACD: {row['macd_line']:.6f}\n"
                response += f"   📍 BB Pozisyon: %{row['bb_position']*100:.0f}\n"
                response += f"   📊 SMA20 Fark: {row['price_vs_sma20']:+.1f}%\n"
                response += f"   📊 30-Gün Getiri: %{row['return_30d']:+.2f}\n"
                response += f"   👥 Yatırımcı: {int(row['investorcount']):,}\n"
                response += f"   🎯 Patterns: {', '.join(patterns)}\n\n"
            
            response += f"\n💡 Detaylı AI analizi için: '[FON_KODU] ai pattern analizi'"
            
            return response
            
        except Exception as e:
            print(f"SQL hatası: {e}")
            import traceback
            traceback.print_exc()
            return "❌ Pattern taraması yapılamadı."

    def _generate_single_fund_analysis(self, fcode, price, rsi, macd, bb_pos, sma20, support, resistance, price_vs_sma20):
        """Tek fon için tutarlı fallback analiz"""
        
        # RSI düzeltmesi - 0 ise yaklaşık hesapla
        if rsi == 0 or rsi == 100:
            if price_vs_sma20 < -10:
                rsi = 25  # Oversold tahmin
            elif price_vs_sma20 > 10:
                rsi = 75  # Overbought tahmin
            else:
                rsi = 50  # Nötr
        
        # Skorlama
        score = 5
        signals = []
        patterns = []
        
        # RSI analizi
        if rsi < 30:
            score += 2
            signals.append("🟢 RSI aşırı satımda - güçlü alım sinyali")
            patterns.append("Oversold bounce potansiyeli")
        elif rsi > 70:
            score -= 2
            signals.append("🔴 RSI aşırı alımda - satış baskısı")
            patterns.append("Overbought düzeltme riski")
        
        # MACD analizi
        if macd < 0:
            if abs(macd) < 0.1:
                score -= 0.5
                signals.append("🟡 MACD hafif negatif")
            else:
                score -= 1
                signals.append("🔴 MACD negatif - düşüş momentumu")
        else:
            score += 1
            signals.append("🟢 MACD pozitif - yükseliş momentumu")
        
        # Bollinger analizi
        if bb_pos < 0.1:
            score += 2
            signals.append("🟢 Bollinger alt bandında - güçlü oversold")
            patterns.append("Bollinger squeeze - patlama potansiyeli")
        elif bb_pos < 0.3:
            score += 1
            signals.append("🟢 Alt banda yakın - alım fırsatı")
        elif bb_pos > 0.9:
            score -= 2
            signals.append("🔴 Bollinger üst bandında - overbought")
        elif bb_pos > 0.7:
            score -= 1
            signals.append("🟠 Üst banda yakın - dikkatli ol")
        
        # SMA20 analizi
        if price_vs_sma20 < -10:
            score += 1.5
            signals.append("🟢 SMA20'nin çok altında - toparlanma potansiyeli")
            patterns.append("Mean reversion fırsatı")
        elif price_vs_sma20 < -5:
            score += 0.5
            signals.append("🟡 SMA20 altında - zayıf trend")
        elif price_vs_sma20 > 5:
            score -= 0.5
            signals.append("🟠 SMA20 üstünde - momentum var")
        
        # Support/Resistance analizi
        price_range = resistance - support
        if price_range > 0:
            position_in_range = (price - support) / price_range
            
            if position_in_range < 0.2:
                score += 1
                patterns.append("Support seviyesinde - dip fırsatı")
            elif position_in_range > 0.8:
                score -= 1
                patterns.append("Resistance yakın - satış baskısı")
        
        # Öneri oluştur
        if score >= 7:
            recommendation = f"🟢 GÜÇLÜ AL (Skor: {score:.1f}/10)"
            action = "AL"
            confidence = "YÜKSEK"
        elif score >= 6:
            recommendation = f"🟢 AL (Skor: {score:.1f}/10)"
            action = "AL"
            confidence = "ORTA"
        elif score <= 3:
            recommendation = f"🔴 SAT (Skor: {score:.1f}/10)"
            action = "SAT"
            confidence = "YÜKSEK"
        elif score <= 4:
            recommendation = f"🟠 SAT (Skor: {score:.1f}/10)"
            action = "SAT"
            confidence = "ORTA"
        else:
            recommendation = f"🟡 BEKLE (Skor: {score:.1f}/10)"
            action = "BEKLE"
            confidence = "DÜŞÜK"
        
        # Risk yönetimi
        if action == "AL":
            entry = price
            stop_loss = max(support * 0.98, price * 0.95)
            target1 = price + (price - stop_loss) * 1.5
            target2 = min(resistance * 0.98, price * 1.10)
        elif action == "SAT":
            entry = price
            stop_loss = min(resistance * 1.02, price * 1.05)
            target1 = price - (stop_loss - price) * 1.5
            target2 = max(support * 1.02, price * 0.95)
        else:
            entry = price
            stop_loss = price * 0.97
            target1 = price * 1.03
            target2 = price * 1.05
        
        risk_reward = abs(target1 - entry) / abs(entry - stop_loss) if abs(entry - stop_loss) > 0 else 1
        
        # Özel durumlar
        special_notes = []
        if bb_pos < 0.1 and price_vs_sma20 < -10:
            special_notes.append("⚡ EKSTREM OVERSOLD - Sert toparlanma potansiyeli")
        if rsi < 20:
            special_notes.append("🎯 RSI ekstrem düşük - Tarihsel dip seviyesi")
        if macd < 0 and bb_pos < 0.2:
            special_notes.append("🔄 Teknik göstergeler dip sinyali veriyor")
        
        analysis = f"""
📊 PATTERN TESPİTLERİ:
{chr(10).join(f'• {p}' for p in patterns) if patterns else '• Belirgin pattern yok'}

📈 TEKNİK SİNYALLER:
{chr(10).join(signals)}

💡 ÖNERİ: {recommendation}
🎯 Güven Seviyesi: {confidence}

🎯 TİCARET PLANI:
- Giriş: {entry:.4f} TL
- Stop-Loss: {stop_loss:.4f} TL ({((stop_loss/entry-1)*100):+.1f}%)
- Hedef 1: {target1:.4f} TL ({((target1/entry-1)*100):+.1f}%)
- Hedef 2: {target2:.4f} TL ({((target2/entry-1)*100):+.1f}%)
- Risk/Reward: 1:{risk_reward:.1f}

{chr(10).join(special_notes) if special_notes else ''}

📊 ÖZET ANALİZ:
Fiyat SMA20'nin {price_vs_sma20:.1f}% {'altında' if price_vs_sma20 < 0 else 'üstünde'}, 
Bollinger bandının %{bb_pos*100:.0f} pozisyonunda,
RSI {rsi:.1f} seviyesinde.

⚠️ Not: Bu analiz kural tabanlı yapılmıştır. Yatırım tavsiyesi değildir.
"""
        
        return analysis

    @staticmethod
    def get_examples():
        """Teknik analiz örnekleri"""
        return [
            "MACD sinyali pozitif olan fonlar",
            "RSI 30'un altında olan fonlar",
            "Bollinger bantlarının altında olan fonlar",
            "Golden cross oluşan fonlar",
            "Aşırı satım bölgesindeki fonlar",
            "Teknik alım sinyali veren fonlar",
            "Death cross yakın fonlar",
            "AKB ai pattern analizi",
            "ai teknik sinyal taraması",
            "yapay zeka formasyon tespiti",
            "hangi fonlarda pattern var"
        ]
    
    @staticmethod
    def get_keywords():
        """Teknik analiz anahtar kelimeleri"""
        return [
            "macd", "rsi", "bollinger", "sma", "ema", "golden cross",
            "death cross", "teknik", "sinyal", "alım sinyali", "satım sinyali",
            "aşırı alım", "aşırı satım", "hareketli ortalama", "band", "bant",
            "pattern", "formasyon", "ai teknik", "yapay zeka teknik",
            "chart pattern", "teknik formasyon"
        ]
    
    @staticmethod
    def get_patterns():
        """Teknik analiz pattern'leri"""
        return [
            {
                'type': 'regex',
                'pattern': r'(macd|rsi|bollinger)\s*(sinyali|değeri|seviyesi)?',
                'score': 0.95
            },
            {
                'type': 'contains_all',
                'words': ['teknik', 'sinyal'],
                'score': 0.9
            },
            {
                'type': 'regex',
                'pattern': r'(golden|death)\s*cross',
                'score': 0.95
            },
            {
                'type': 'regex',
                'pattern': r'(ai|yapay zeka)\s*(pattern|patern|formasyon|teknik)',
                'score': 0.98
            },
            {
                'type': 'contains_all',
                'words': ['pattern', 'analiz'],
                'score': 0.92
            },
            {
                'type': 'contains_all', 
                'words': ['formasyon', 'tespit'],
                'score': 0.92
            }
        ]
    
    @staticmethod
    def get_method_patterns():
        """Method mapping"""
        return {
            'handle_macd_signals_sql': ['macd', 'macd sinyali'],
            'handle_rsi_signals_sql': ['rsi', 'aşırı satım', 'aşırı alım'],
            'handle_bollinger_signals_sql': ['bollinger', 'bant', 'band'],
            'handle_moving_average_signals_sql': ['sma', 'ema', 'hareketli ortalama', 'golden cross', 'death cross'],
            'handle_general_technical_signals_sql': ['teknik sinyal', 'alım sinyali', 'satım sinyali'],
            'handle_ai_pattern_analysis': ['ai pattern', 'ai teknik', 'pattern analizi', 
                                        'formasyon tespiti', 'yapay zeka teknik', 
                                        'chart pattern', 'teknik formasyon']
        }