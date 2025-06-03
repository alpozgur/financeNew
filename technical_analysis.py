# technical_analysis.py

import pandas as pd

class TechnicalAnalysis:
    def __init__(self, coordinator, active_funds):
        self.coordinator = coordinator
        self.active_funds = active_funds

    def handle_macd_signals_sql(self, question):
        """SQL ile MACD analizi - TÜM FONLAR"""
        print("📊 SQL ile MACD sinyali analiz ediliyor (TÜM VERİTABANI)...")

        # Pozitif/negatif sinyali tespit et
        is_positive = any(word in question.lower() for word in ['pozitif', 'positive', 'alım', 'buy'])
        signal_type = "pozitif" if is_positive else "negatif"
        operator = ">" if is_positive else "<"

        try:
            # SQL ile MACD hesaplama ve filtreleme
            query = f"""
            WITH recent_prices AS (
                SELECT fcode, price, pdate,
                    ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY pdate DESC) as rn
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '40 days'
                AND price > 0
                AND investorcount > 50
            ),
            price_series AS (
                SELECT fcode, price, pdate
                FROM recent_prices 
                WHERE rn <= 30
            ),
            ema_calculations AS (
                SELECT fcode,
                    AVG(CASE WHEN rn <= 12 THEN price END) as ema_12_approx,
                    AVG(CASE WHEN rn <= 26 THEN price END) as ema_26_approx,
                    COUNT(*) as data_points
                FROM (
                    SELECT fcode, price,
                        ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY pdate DESC) as rn
                    FROM price_series
                ) ranked_prices
                GROUP BY fcode
                HAVING COUNT(*) >= 26
            ),
            macd_signals AS (
                SELECT fcode,
                    ema_12_approx,
                    ema_26_approx,
                    (ema_12_approx - ema_26_approx) as macd_line,
                    data_points
                FROM ema_calculations
                WHERE ema_12_approx IS NOT NULL AND ema_26_approx IS NOT NULL
            )
            SELECT ms.fcode, ms.macd_line, ms.ema_12_approx, ms.ema_26_approx, 
                ms.data_points, f.price as current_price, f.investorcount
            FROM macd_signals ms
            JOIN (
                SELECT DISTINCT ON (fcode) fcode, price, investorcount
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY fcode, pdate DESC
            ) f ON ms.fcode = f.fcode
            WHERE ms.macd_line {operator} 0
            ORDER BY ABS(ms.macd_line) DESC
            LIMIT 20
            """

            result = self.coordinator.db.execute_query(query)
            if result.empty:
                return f"❌ {signal_type.upper()} MACD sinyali olan fon bulunamadı."

            print(f"   ✅ SQL analizi: {len(result)} fon bulundu")

            response = f"\n📊 MACD SİNYALİ {signal_type.upper()} - SQL ANALİZİ (TÜM VERİTABANI)\n"
            response += f"{'='*60}\n\n"
            response += f"🎯 Toplam {len(result)} fon {signal_type} MACD sinyali veriyor\n\n"

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

            for i, (_, row) in enumerate(result.head(15).iterrows(), 1):
                fcode = row['fcode']
                macd_value = float(row['macd_line'])
                current_price = float(row['current_price'])
                investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0

                fund_info = fund_details_dict.get(fcode, {'name': 'N/A', 'type': 'N/A'})

                if abs(macd_value) > 0.01:
                    strength = "🟢 GÜÇLÜ"
                elif abs(macd_value) > 0.005:
                    strength = "🟡 ORTA"
                else:
                    strength = "🟠 ZAYIF"

                response += f"{i:2d}. {fcode} - {strength}\n"
                response += f"    📊 MACD: {macd_value:+.6f}\n"
                response += f"    💲 Fiyat: {current_price:.4f} TL\n"
                response += f"    👥 Yatırımcı: {investors:,} kişi\n"
                response += f"    🏷️ Tür: {fund_info['type']}\n"
                if fund_info['name'] != 'N/A':
                    response += f"    📝 Adı: {fund_info['name'][:40]}...\n"
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
        """SQL ile Bollinger Bantları analizi - TÜM FONLAR"""
        print("📊 SQL ile Bollinger Bantları analiz ediliyor (TÜM VERİTABANI)...")
        
        # Alt/üst banda yakın tespit et
        is_lower_band = any(word in question.lower() for word in ['alt banda', 'lower band', 'alt', 'düşük'])
        band_type = "alt banda" if is_lower_band else "üst banda"
        bb_condition = "< 0.3" if is_lower_band else "> 0.7"
        
        try:
            query = f"""
            WITH recent_prices AS (
                SELECT fcode, price, pdate,
                    ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY pdate DESC) as rn
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '30 days'
                AND price > 0
                AND investorcount > 50
            ),
            price_series AS (
                SELECT fcode, price, pdate
                FROM recent_prices 
                WHERE rn <= 20  -- Son 20 gün (Bollinger için yeterli)
            ),
            bollinger_calc AS (
                SELECT fcode,
                    AVG(price) as sma_20,
                    STDDEV(price) as std_20,
                    COUNT(*) as data_points,
                    (SELECT price FROM recent_prices WHERE fcode = ps.fcode AND rn = 1) as current_price
                FROM price_series ps
                GROUP BY fcode
                HAVING COUNT(*) >= 15  -- En az 15 gün
            ),
            bollinger_bands AS (
                SELECT fcode,
                    current_price,
                    sma_20,
                    std_20,
                    (sma_20 + 2 * std_20) as upper_band,
                    (sma_20 - 2 * std_20) as lower_band,
                    CASE 
                        WHEN (sma_20 + 2 * std_20) - (sma_20 - 2 * std_20) = 0 THEN 0
                        ELSE (current_price - (sma_20 - 2 * std_20)) / 
                            ((sma_20 + 2 * std_20) - (sma_20 - 2 * std_20))
                    END as bb_percent
                FROM bollinger_calc
                WHERE std_20 > 0
            )
            SELECT bb.fcode, bb.current_price, bb.sma_20, bb.upper_band, bb.lower_band, 
                bb.bb_percent, f.investorcount
            FROM bollinger_bands bb
            JOIN (
                SELECT DISTINCT ON (fcode) fcode, investorcount
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY fcode, pdate DESC
            ) f ON bb.fcode = f.fcode
            WHERE bb.bb_percent {bb_condition}
            ORDER BY {'bb.bb_percent ASC' if is_lower_band else 'bb.bb_percent DESC'}
            LIMIT 20
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return f"❌ {band_type.upper()} yakın Bollinger sinyali olan fon bulunamadı."
            
            print(f"   ✅ SQL analizi: {len(result)} fon bulundu")
            
            response = f"\n📊 BOLLİNGER BANTLARI - {band_type.upper()} YAKIN FONLAR (SQL)\n"
            response += f"{'='*55}\n\n"
            response += f"🎯 {len(result)} fon {band_type} yakın pozisyonda\n\n"
            
            # Fund details'leri toplu al
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
            
            for i, (_, row) in enumerate(result.head(15).iterrows(), 1):
                fcode = row['fcode']
                current_price = float(row['current_price'])
                bb_percent = float(row['bb_percent'])
                upper_band = float(row['upper_band'])
                lower_band = float(row['lower_band'])
                sma_20 = float(row['sma_20'])
                investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                
                fund_info = fund_details_dict.get(fcode, {'name': 'N/A', 'type': 'N/A'})
                
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
                
                response += f"{i:2d}. {fcode} - {position}\n"
                response += f"    💲 Fiyat: {current_price:.4f} TL\n"
                response += f"    📊 BB%: {bb_percent:.3f} (%{bb_percent*100:.1f})\n"
                response += f"    📈 Üst Bant: {upper_band:.4f} TL\n"
                response += f"    📉 Alt Bant: {lower_band:.4f} TL\n"
                response += f"    📊 SMA(20): {sma_20:.4f} TL\n"
                response += f"    👥 Yatırımcı: {investors:,} kişi\n"
                response += f"    🏷️ Tür: {fund_info['type']}\n"
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
        """SQL ile RSI analizi - TÜM FONLAR"""
        print("📊 SQL ile RSI analiz ediliyor (TÜM VERİTABANI)...")
        
        # RSI seviyesini tespit et
        is_oversold = any(word in question.lower() for word in ['düşük', 'oversold', 'aşırı satım', '30', 'altında'])
        is_overbought = any(word in question.lower() for word in ['yüksek', 'overbought', 'aşırı alım', '70', 'üstünde'])
        
        if is_oversold:
            condition = "oversold"
            rsi_condition = "< 35"  # Biraz esneklik
            order_by = "rsi_approx ASC"
        elif is_overbought:
            condition = "overbought" 
            rsi_condition = "> 65"  # Biraz esneklik
            order_by = "rsi_approx DESC"
        else:
            condition = "neutral"
            rsi_condition = "BETWEEN 40 AND 60"
            order_by = "ABS(rsi_approx - 50) ASC"
        
        try:
            # Basitleştirilmiş RSI hesaplaması SQL'de
            query = f"""
            WITH recent_prices AS (
                SELECT fcode, price, pdate,
                    LAG(price) OVER (PARTITION BY fcode ORDER BY pdate) as prev_price,
                    ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY pdate DESC) as rn
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '25 days'
                AND price > 0
                AND investorcount > 50
            ),
            price_changes AS (
                SELECT fcode, price, pdate,
                    CASE WHEN price > prev_price THEN price - prev_price ELSE 0 END as gain,
                    CASE WHEN price < prev_price THEN prev_price - price ELSE 0 END as loss
                FROM recent_prices 
                WHERE prev_price IS NOT NULL
                AND rn <= 15  -- Son 15 gün değişim
            ),
            rsi_calc AS (
                SELECT fcode,
                    AVG(gain) as avg_gain,
                    AVG(loss) as avg_loss,
                    COUNT(*) as data_points,
                    (SELECT price FROM recent_prices WHERE fcode = pc.fcode AND rn = 1) as current_price
                FROM price_changes pc
                GROUP BY fcode
                HAVING COUNT(*) >= 10  -- En az 10 gün
            ),
            rsi_values AS (
                SELECT fcode, current_price,
                    CASE 
                        WHEN avg_loss = 0 THEN 100
                        WHEN avg_gain = 0 THEN 0
                        ELSE 100 - (100 / (1 + (avg_gain / avg_loss)))
                    END as rsi_approx
                FROM rsi_calc
                WHERE avg_gain IS NOT NULL AND avg_loss IS NOT NULL
            )
            SELECT rv.fcode, rv.current_price, rv.rsi_approx, f.investorcount
            FROM rsi_values rv
            JOIN (
                SELECT DISTINCT ON (fcode) fcode, investorcount
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY fcode, pdate DESC
            ) f ON rv.fcode = f.fcode
            WHERE rv.rsi_approx {rsi_condition}
            ORDER BY {order_by}
            LIMIT 20
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return f"❌ RSI {condition} seviyesinde fon bulunamadı."
            
            print(f"   ✅ SQL analizi: {len(result)} fon bulundu")
            
            response = f"\n📊 RSI ANALİZİ - {condition.upper()} SEVİYE (SQL)\n"
            response += f"{'='*40}\n\n"
            response += f"🎯 {len(result)} fon RSI {condition} seviyesinde\n\n"
            
            # Fund details'leri toplu al
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
            
            for i, (_, row) in enumerate(result.head(15).iterrows(), 1):
                fcode = row['fcode']
                current_price = float(row['current_price'])
                rsi_value = float(row['rsi_approx'])
                investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                
                fund_info = fund_details_dict.get(fcode, {'name': 'N/A', 'type': 'N/A'})
                
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
                response += f"    🏷️ Tür: {fund_info['type']}\n"
                if fund_info['name'] != 'N/A':
                    response += f"    📝 Adı: {fund_info['name'][:35]}...\n"
                response += f"\n"
            
            # İstatistikler
            avg_rsi = result['rsi_approx'].mean()
            extreme = result.iloc[0]
            
            response += f"📊 RSI {condition.upper()} İSTATİSTİKLERİ:\n"
            response += f"   Ortalama RSI: {avg_rsi:.1f}\n"
            response += f"   En Ekstrem: {extreme['fcode']} ({extreme['rsi_approx']:.1f})\n"
            response += f"   Toplam Bulunan: {len(result)} fon\n"
            
            return response
            
        except Exception as e:
            print(f"   ❌ SQL RSI analizi hatası: {e}")
            return f"❌ SQL RSI analizi hatası: {e}"

    def handle_moving_average_signals_sql(self, question):
        """SQL ile Hareketli Ortalama analizi - TÜM FONLAR"""
        print("📊 SQL ile Hareketli Ortalama analiz ediliyor (TÜM VERİTABANI)...")
        
        # Golden/Death Cross tespit et
        is_golden_cross = any(word in question.lower() for word in ['golden cross', 'alım sinyali', 'pozitif'])
        signal_type = "Golden Cross" if is_golden_cross else "Death Cross"
        ma_condition = ">" if is_golden_cross else "<"
        
        try:
            query = f"""
            WITH recent_prices AS (
                SELECT fcode, price, pdate,
                    ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY pdate DESC) as rn
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '60 days'
                AND price > 0
                AND investorcount > 50
            ),
            ma_calculations AS (
                SELECT fcode,
                    AVG(CASE WHEN rn <= 20 THEN price END) as sma_20,
                    AVG(CASE WHEN rn <= 50 THEN price END) as sma_50,
                    COUNT(*) as data_points,
                    (SELECT price FROM recent_prices WHERE fcode = rp.fcode AND rn = 1) as current_price
                FROM recent_prices rp
                GROUP BY fcode
                HAVING COUNT(*) >= 50  -- En az 50 gün veri gerekli
            ),
            ma_signals AS (
                SELECT fcode, current_price, sma_20, sma_50,
                    ((sma_20 / sma_50) - 1) * 100 as ma_spread,
                    CASE 
                        WHEN sma_20 > sma_50 THEN 'Golden Cross'
                        WHEN sma_20 < sma_50 THEN 'Death Cross'
                        ELSE 'Neutral'
                    END as signal_type
                FROM ma_calculations
                WHERE sma_20 IS NOT NULL AND sma_50 IS NOT NULL
            )
            SELECT ms.fcode, ms.current_price, ms.sma_20, ms.sma_50, 
                ms.ma_spread, ms.signal_type, f.investorcount
            FROM ma_signals ms
            JOIN (
                SELECT DISTINCT ON (fcode) fcode, investorcount
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY fcode, pdate DESC
            ) f ON ms.fcode = f.fcode
            WHERE ms.sma_20 {ma_condition} ms.sma_50
            ORDER BY ABS(ms.ma_spread) DESC
            LIMIT 25
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return f"❌ {signal_type} sinyali olan fon bulunamadı."
            
            print(f"   ✅ SQL analizi: {len(result)} fon bulundu")
            
            response = f"\n📊 HAREKETLİ ORTALAMA - {signal_type.upper()} SİNYALLERİ (SQL)\n"
            response += f"{'='*55}\n\n"
            response += f"🎯 {len(result)} fon {signal_type} sinyali veriyor\n\n"
            
            # Fund details'leri toplu al
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
            
            for i, (_, row) in enumerate(result.head(15).iterrows(), 1):
                fcode = row['fcode']
                current_price = float(row['current_price'])
                sma_20 = float(row['sma_20'])
                sma_50 = float(row['sma_50'])
                ma_spread = float(row['ma_spread'])
                investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                
                fund_info = fund_details_dict.get(fcode, {'name': 'N/A', 'type': 'N/A'})
                
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
                
                response += f"{i:2d}. {fcode} - {strength} {signal_icon}\n"
                response += f"    💲 Fiyat: {current_price:.4f} TL\n"
                response += f"    📊 SMA20: {sma_20:.4f} TL\n"
                response += f"    📈 SMA50: {sma_50:.4f} TL\n"
                response += f"    📍 Fark: %{ma_spread:+.2f}\n"
                response += f"    👥 Yatırımcı: {investors:,} kişi\n"
                response += f"    🏷️ Tür: {fund_info['type']}\n"
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
        """SQL ile Genel Teknik Sinyal analizi - TÜM FONLAR"""
        print("📊 SQL ile Genel Teknik Sinyaller analiz ediliyor (TÜM VERİTABANI)...")
        
        try:
            # Kompleks SQL sorgusu - multiple technical indicators
            query = """
            WITH recent_data AS (
                SELECT fcode, price, pdate, investorcount,
                    LAG(price, 1) OVER (PARTITION BY fcode ORDER BY pdate) as price_1d_ago,
                    LAG(price, 5) OVER (PARTITION BY fcode ORDER BY pdate) as price_5d_ago,
                    LAG(price, 10) OVER (PARTITION BY fcode ORDER BY pdate) as price_10d_ago,
                    ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY pdate DESC) as rn
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '30 days'
                AND price > 0
                AND investorcount > 100  -- Minimum yatırımcı sayısı
            ),
            latest_prices AS (
                SELECT fcode, price as current_price, investorcount
                FROM recent_data 
                WHERE rn = 1
            ),
            momentum_calc AS (
                SELECT rd.fcode,
                    lp.current_price,
                    lp.investorcount,
                    AVG(rd.price) as avg_price_20d,
                    STDDEV(rd.price) as std_price_20d,
                    -- Momentum indicators
                    CASE WHEN rd.price_5d_ago > 0 THEN 
                        ((lp.current_price - rd.price_5d_ago) / rd.price_5d_ago) * 100 
                        ELSE 0 END as momentum_5d,
                    CASE WHEN rd.price_10d_ago > 0 THEN 
                        ((lp.current_price - rd.price_10d_ago) / rd.price_10d_ago) * 100 
                        ELSE 0 END as momentum_10d,
                    COUNT(*) as data_points
                FROM recent_data rd
                JOIN latest_prices lp ON rd.fcode = lp.fcode
                WHERE rd.rn <= 20  -- Son 20 gün
                GROUP BY rd.fcode, lp.current_price, lp.investorcount
                HAVING COUNT(*) >= 15
            ),
            technical_scores AS (
                SELECT fcode, current_price, investorcount,
                    momentum_5d, momentum_10d,
                    -- Bollinger position approximation
                    CASE 
                        WHEN std_price_20d = 0 THEN 0.5
                        ELSE (current_price - (avg_price_20d - 2 * std_price_20d)) / 
                            (4 * std_price_20d)
                    END as bb_position,
                    -- Price vs moving average
                    CASE 
                        WHEN avg_price_20d = 0 THEN 0
                        ELSE ((current_price / avg_price_20d) - 1) * 100
                    END as price_vs_ma,
                    -- Combined technical score
                    CASE 
                        WHEN momentum_5d > 5 THEN 2
                        WHEN momentum_5d > 0 THEN 1
                        WHEN momentum_5d < -5 THEN -2
                        WHEN momentum_5d < 0 THEN -1
                        ELSE 0
                    END +
                    CASE 
                        WHEN momentum_10d > 10 THEN 2
                        WHEN momentum_10d > 0 THEN 1
                        WHEN momentum_10d < -10 THEN -2
                        WHEN momentum_10d < 0 THEN -1
                        ELSE 0
                    END as momentum_score
                FROM momentum_calc
            )
            SELECT fcode, current_price, investorcount, momentum_5d, momentum_10d,
                bb_position, price_vs_ma, momentum_score
            FROM technical_scores
            WHERE ABS(momentum_score) >= 2  -- Sadece güçlü sinyaller
            ORDER BY momentum_score DESC, ABS(momentum_5d) DESC
            LIMIT 25
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return "❌ Güçlü teknik sinyal olan fon bulunamadı."
            
            print(f"   ✅ SQL analizi: {len(result)} fon bulundu")
            
            response = f"\n📊 GENEL TEKNİK SİNYAL ANALİZİ - SQL (TÜM VERİTABANI)\n"
            response += f"{'='*55}\n\n"
            response += f"🎯 {len(result)} fon güçlü teknik sinyal veriyor\n\n"
            
            # Alım ve satım sinyallerini ayır
            buy_signals = result[result['momentum_score'] > 0].copy()
            sell_signals = result[result['momentum_score'] < 0].copy()
            
            # Fund details'leri toplu al
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
            
            # ALIM SİNYALLERİ
            if not buy_signals.empty:
                response += f"🟢 GÜÇLÜ ALIM SİNYALLERİ ({len(buy_signals)} fon):\n\n"
                
                for i, (_, row) in enumerate(buy_signals.head(8).iterrows(), 1):
                    fcode = row['fcode']
                    current_price = float(row['current_price'])
                    momentum_5d = float(row['momentum_5d'])
                    momentum_10d = float(row['momentum_10d'])
                    momentum_score = int(row['momentum_score'])
                    investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                    
                    fund_info = fund_details_dict.get(fcode, {'name': 'N/A', 'type': 'N/A'})
                    
                    # Sinyal gücü
                    if momentum_score >= 4:
                        strength = "🟢 ÇOK GÜÇLÜ"
                    elif momentum_score >= 3:
                        strength = "🟡 GÜÇLÜ"
                    else:
                        strength = "🟠 ORTA"
                    
                    response += f"{i}. {fcode} - {strength} 🚀\n"
                    response += f"   💲 Fiyat: {current_price:.4f} TL\n"
                    response += f"   📊 5-Gün Momentum: %{momentum_5d:+.2f}\n"
                    response += f"   📈 10-Gün Momentum: %{momentum_10d:+.2f}\n"
                    response += f"   ⚡ Teknik Skor: +{momentum_score}\n"
                    response += f"   👥 Yatırımcı: {investors:,} kişi\n"
                    response += f"   🏷️ Tür: {fund_info['type']}\n"
                    response += f"\n"
            
            # SATIM SİNYALLERİ
            if not sell_signals.empty:
                response += f"\n🔴 GÜÇLÜ SATIM SİNYALLERİ ({len(sell_signals)} fon):\n\n"
                
                for i, (_, row) in enumerate(sell_signals.head(5).iterrows(), 1):
                    fcode = row['fcode']
                    current_price = float(row['current_price'])
                    momentum_5d = float(row['momentum_5d'])
                    momentum_10d = float(row['momentum_10d'])
                    momentum_score = int(row['momentum_score'])
                    investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                    
                    fund_info = fund_details_dict.get(fcode, {'name': 'N/A', 'type': 'N/A'})
                    
                    # Sinyal gücü
                    if momentum_score <= -4:
                        strength = "🔴 ÇOK GÜÇLÜ"
                    elif momentum_score <= -3:
                        strength = "🟠 GÜÇLÜ"
                    else:
                        strength = "🟡 ORTA"
                    
                    response += f"{i}. {fcode} - {strength} 📉\n"
                    response += f"   💲 Fiyat: {current_price:.4f} TL\n"
                    response += f"   📊 5-Gün Momentum: %{momentum_5d:+.2f}\n"
                    response += f"   📈 10-Gün Momentum: %{momentum_10d:+.2f}\n"
                    response += f"   ⚡ Teknik Skor: {momentum_score}\n"
                    response += f"   👥 Yatırımcı: {investors:,} kişi\n"
                    response += f"   🏷️ Tür: {fund_info['type']}\n"
                    response += f"\n"
            
            # GENEL İSTATİSTİKLER
            total_buy = len(buy_signals)
            total_sell = len(sell_signals)
            avg_momentum_5d = result['momentum_5d'].mean()
            
            response += f"📊 GENEL TEKNİK SİNYAL İSTATİSTİKLERİ:\n"
            response += f"   🟢 Alım Sinyali: {total_buy} fon\n"
            response += f"   🔴 Satım Sinyali: {total_sell} fon\n"
            response += f"   📊 Ortalama 5-Gün Momentum: %{avg_momentum_5d:+.2f}\n"
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

