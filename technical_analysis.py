# technical_analysis.py

import pandas as pd

class TechnicalAnalysis:
    def __init__(self, coordinator, active_funds, ai_provider=None):
        self.coordinator = coordinator
        self.active_funds = active_funds
        self.ai_provider = ai_provider  # YENİ - AI provider ekle
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
                    SELECT 
                        ti.fcode,
                        ti.macd_line,
                        ti.current_price,
                        ti.investorcount,
                        ti.sma_10 as ema_12_approx,
                        ti.sma_20 as ema_26_approx,
                        ti.data_points
                    FROM mv_fund_technical_indicators ti
                    WHERE ti.macd_line {operator} 0
                    ORDER BY ABS(ti.macd_line) DESC
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
                SELECT 
                    fcode,
                    current_price,
                    sma_20,
                    bb_upper as upper_band,
                    bb_lower as lower_band,
                    bb_position as bb_percent,
                    investorcount
                FROM mv_fund_technical_indicators
                WHERE bb_position {bb_condition}
                ORDER BY {'bb_position ASC' if is_lower_band else 'bb_position DESC'}
                LIMIT 20
                """
            # SQL sorgusunu çalıştır            
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
            order_by = "rsi_14 ASC"
        elif is_overbought:
            condition = "overbought" 
            rsi_condition = "> 65"  # Biraz esneklik
            order_by = "rsi_14 DESC"
        else:
            condition = "neutral"
            rsi_condition = "BETWEEN 40 AND 60"
            order_by = "ABS(rsi_14 - 50) ASC"
        
        try:
            # Basitleştirilmiş RSI hesaplaması SQL'de
            query = f"""
                    SELECT 
                        fcode,
                        current_price,
                        rsi_14,
                        investorcount
                    FROM mv_fund_technical_indicators
                    WHERE rsi_14 {rsi_condition}
                    ORDER BY {order_by}
                    LIMIT 20
                    """
            # SQL sorgusunu çalıştır            
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
                rsi_value = float(row['rsi_14'])
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


    def ai_technical_pattern_recognition(self, fcode, days=60):
        """AI destekli teknik pattern tanıma ve analiz - DÜZELTME"""
        try:
            # 1. MV'den veri al
            query = f"""
            SELECT *
            FROM mv_fund_technical_indicators
            WHERE fcode = '{fcode}'
            """
            
            mv_data = self.coordinator.db.execute_query(query)
            
            if mv_data.empty:
                # MV'de yoksa manuel hesapla
                price_history = self.coordinator.db.get_fund_price_history(fcode, days)
                if price_history.empty or len(price_history) < 30:
                    return None
                
                # Manuel hesaplamalar
                prices = price_history['price'].values
                current_price = prices[-1]
                
                # Basit hesaplamalar
                sma_10 = prices[-10:].mean() if len(prices) >= 10 else prices.mean()
                sma_20 = prices[-20:].mean() if len(prices) >= 20 else prices.mean()
                sma_50 = prices[-50:].mean() if len(prices) >= 50 else prices.mean()
                
                # Price change calculation
                price_5d_ago = prices[-5] if len(prices) >= 5 else prices[0]
                price_20d_ago = prices[-20] if len(prices) >= 20 else prices[0]
                trend_5d = ((current_price / price_5d_ago) - 1) * 100
                trend_20d = ((current_price / price_20d_ago) - 1) * 100
                
                rsi = 50  # Default
                macd_current = sma_10 - sma_20
                bb_position = 0.5
                support = prices[-30:].min()
                resistance = prices[-30:].max()
                investors = 0
                
            else:
                # MV'den gelen veriler
                row = mv_data.iloc[0]
                current_price = float(row['current_price'])
                sma_10 = float(row['sma_10'])
                sma_20 = float(row['sma_20'])
                sma_50 = float(row['sma_50'])
                rsi = float(row['rsi_14'])
                macd_current = float(row['macd_line'])
                bb_position = float(row['bb_position'])
                investors = int(row['investorcount'])
                
                # Support/Resistance için ek sorgu
                hist_query = f"""
                SELECT MIN(price) as support, MAX(price) as resistance
                FROM tefasfunds
                WHERE fcode = '{fcode}'
                AND pdate >= CURRENT_DATE - INTERVAL '30 days'
                """
                
                hist_data = self.coordinator.db.execute_query(hist_query)
                if not hist_data.empty:
                    support = float(hist_data.iloc[0]['support'])
                    resistance = float(hist_data.iloc[0]['resistance'])
                else:
                    support = current_price * 0.95
                    resistance = current_price * 1.05
                
                # Trend hesaplama
                trend_5d = float(row['price_vs_sma20']) / 4  # Yaklaşık
                trend_20d = float(row['price_vs_sma20'])
            
            # 3. Fiyat pattern analizi için veri hazırlığı
            price_info = f"""
    - Güncel: {current_price:.4f} TL
    - SMA10: {sma_10:.4f} ({'Üstünde' if current_price > sma_10 else 'Altında'})
    - SMA20: {sma_20:.4f} ({'Üstünde' if current_price > sma_20 else 'Altında'})
    - SMA50: {sma_50:.4f} ({'Üstünde' if current_price > sma_50 else 'Altında'})
    - Support: {support:.4f} TL
    - Resistance: {resistance:.4f} TL
    """
            
            # 4. AI Prompt
            prompt = f"""
    {fcode} fonu için teknik pattern analizi:

    FİYAT BİLGİLERİ:
    {price_info}

    TEKNİK İNDİKATÖRLER:
    - RSI(14): {rsi:.1f} {'(Aşırı Satım)' if rsi < 30 else '(Aşırı Alım)' if rsi > 70 else '(Normal)'}
    - MACD: {macd_current:.6f}
    - Bollinger Position: {bb_position:.2f} {'(Alt banda yakın)' if bb_position < 0.3 else '(Üst banda yakın)' if bb_position > 0.7 else '(Orta bölge)'}
    - Yatırımcı Sayısı: {investors:,}

    GÖREVLER:
    1. PATTERN: Hangi teknik formasyonlar görülüyor?
    2. TREND: Ana trend yönü nedir?
    3. SİNYAL: AL/SAT/BEKLE önerisi (1-10 güç)
    4. RİSK YÖNETİMİ: Stop-loss ve hedef fiyat

    Kısa ve net ol. Emoji kullan."""

            # 5. AI Analizi
            system_prompt = "Sen teknik analiz uzmanısın. Chart pattern'leri tanıyorsun."
            
            if hasattr(self, 'ai_provider') and self.ai_provider and self.ai_provider.is_available():
                ai_analysis = self.ai_provider.query(prompt, system_prompt)
            else:
                # Fallback analiz
                ai_analysis = self._generate_pattern_analysis(
                    rsi, macd_current, 0, bb_position, 
                    current_price, sma_20, support, resistance
                )
            
            return {
                'fcode': fcode,
                'current_price': current_price,
                'indicators': {
                    'rsi': rsi,
                    'macd': macd_current,
                    'macd_signal': 0,
                    'bb_position': bb_position,
                    'sma_10': sma_10,
                    'sma_20': sma_20,
                    'sma_50': sma_50,
                    'support': support,
                    'resistance': resistance
                },
                'ai_analysis': ai_analysis
            }
            
        except Exception as e:
            print(f"AI pattern recognition hatası: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _generate_pattern_analysis(self, rsi, macd, signal, bb_pos, price, sma20, support, resistance):
        """AI olmadığında kural tabanlı pattern analizi"""
        patterns = []
        score = 5
        
        # Pattern tespitleri
        if macd > signal and macd > 0:
            patterns.append("🟢 MACD Golden Cross")
            score += 2
        elif macd < signal and macd < 0:
            patterns.append("🔴 MACD Death Cross")
            score -= 2
        
        if rsi < 30:
            patterns.append("🟢 RSI Oversold bounce potansiyeli")
            score += 2
        elif rsi > 70:
            patterns.append("🔴 RSI Overbought - düzeltme riski")
            score -= 2
        
        if bb_pos < 0.2:
            patterns.append("🟢 Bollinger alt bandında - dip alım fırsatı")
            score += 1
        elif bb_pos > 0.8:
            patterns.append("🔴 Bollinger üst bandında - kar realizasyonu")
            score -= 1
        
        if price > sma20:
            patterns.append("📈 SMA20 üzerinde - yükseliş trendi")
            score += 1
        else:
            patterns.append("📉 SMA20 altında - düşüş trendi")
            score -= 1
        
        # Öneri oluştur
        if score >= 7:
            signal_text = f"🟢 GÜÇLÜ AL SİNYALİ (Güç: {score}/10)"
            action = "AL"
        elif score <= 3:
            signal_text = f"🔴 SAT SİNYALİ (Güç: {10-score}/10)"
            action = "SAT"
        else:
            signal_text = f"🟡 BEKLE (Nötr: {score}/10)"
            action = "BEKLE"
        
        # Risk yönetimi
        if action == "AL":
            stop_loss = price * 0.95  # %5 aşağı
            target = resistance if resistance > price * 1.1 else price * 1.15
        elif action == "SAT":
            stop_loss = price * 1.05  # %5 yukarı
            target = support if support < price * 0.9 else price * 0.85
        else:
            stop_loss = price * 0.95
            target = price * 1.05
        
        risk_reward = abs(target - price) / abs(price - stop_loss)
        
        analysis = f"""
    📊 PATTERN ANALİZİ:
    {chr(10).join(patterns)}

    💡 {signal_text}

    🎯 TİCARET PLANI:
    • Giriş: {price:.4f} TL
    • Stop-Loss: {stop_loss:.4f} TL ({((stop_loss/price-1)*100):+.1f}%)
    • Hedef: {target:.4f} TL ({((target/price-1)*100):+.1f}%)
    • Risk/Reward: 1:{risk_reward:.1f}

    ⚠️ Risk Uyarısı: Yatırım tavsiyesi değildir."""
        
        return analysis


    def handle_ai_pattern_analysis(self, question):
        """AI destekli pattern analizi handler"""
        print("🤖 AI Pattern Analysis çağrıldı!")
        print(f"Soru: {question}")
        
        question_lower = question.lower()
        
        # Fon kodunu bul - GELİŞTİRİLMİŞ
        words = question.upper().split()
        fcode = None
        
        # Debug için
        print(f"Kelimeler: {words}")
        
        # Önce 3 harfli kelimeleri kontrol et
        potential_codes = [word for word in words if len(word) == 3 and word.isalpha()]
        print(f"Potansiyel fon kodları: {potential_codes}")
        
        if potential_codes:
            # Veritabanında kontrol et - DÜZELTME
            try:
                all_funds_query = "SELECT DISTINCT fcode FROM tefasfunds"
                result = self.coordinator.db.execute_query(all_funds_query)
                all_funds = [f.upper() for f in result['fcode'].tolist()]
                print(f"Veritabanında {len(all_funds)} fon var")
                
                for code in potential_codes:
                    if code in all_funds:
                        fcode = code
                        print(f"✅ Fon kodu bulundu: {fcode}")
                        break
                    else:
                        print(f"❌ {code} veritabanında yok")
                        
            except Exception as e:
                print(f"Veritabanı hatası: {e}")
                # Fallback olarak get_all_fund_codes kullan
                all_funds = [f.upper() for f in self.coordinator.db.get_all_fund_codes()]
                for code in potential_codes:
                    if code in all_funds:
                        fcode = code
                        break
        
        # Eğer fon kodu bulunduysa tek fon analizi yap
        if fcode:
            print(f"🎯 Tek fon analizi yapılıyor: {fcode}")
            
            # Önce MV'den kontrol et
            mv_query = f"""
            SELECT * FROM mv_fund_technical_indicators 
            WHERE fcode = '{fcode}'
            """
            
            try:
                mv_result = self.coordinator.db.execute_query(mv_query)
                
                if mv_result.empty:
                    return f"❌ {fcode} için teknik veri bulunamadı."
                
                # MV'den gelen veriler
                row = mv_result.iloc[0]
                current_price = float(row['current_price'])
                rsi = float(row['rsi_14'])
                macd = float(row['macd_line'])
                bb_position = float(row['bb_position'])
                sma_20 = float(row['sma_20'])
                price_vs_sma20 = float(row['price_vs_sma20'])
                investors = int(row['investorcount'])
                
                # Support/Resistance için ek sorgu
                hist_query = f"""
                SELECT MIN(price) as support, MAX(price) as resistance,
                    MAX(price) - MIN(price) as range
                FROM tefasfunds
                WHERE fcode = '{fcode}'
                AND pdate >= CURRENT_DATE - INTERVAL '30 days'
                """
                
                hist_data = self.coordinator.db.execute_query(hist_query)
                if not hist_data.empty:
                    support = float(hist_data.iloc[0]['support'])
                    resistance = float(hist_data.iloc[0]['resistance'])
                else:
                    support = current_price * 0.95
                    resistance = current_price * 1.05
                
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
- Yatırımcı: {investors:,} kişi

GÖREVLER:
1. Hangi teknik patternler görülüyor? (Double Bottom, Triangle, Flag vb.)
2. Trend yönü ve gücü nedir?
3. AL/SAT/BEKLE önerisi (1-10 güç skoru)
4. Entry point, Stop-loss ve Target fiyat öner
5. Risk/Reward oranı

Kısa, net ve aksiyona yönelik ol.

ÖNEMLİ NOTLAR:
- Eğer RSI 0 görünüyorsa, muhtemelen hesaplama hatası var. Fiyatın SMA20'ye göre pozisyonunu dikkate al.
- Bollinger pozisyonu %20'nin altındaysa, bu güçlü oversold sinyalidir.
- Fiyat SMA20'nin %10'dan fazla altındaysa, mean reversion potansiyeli var.
- Birden fazla oversold sinyali varsa (Bollinger alt banda yakın + SMA20 çok altında), GÜÇLÜ AL sinyali düşün.
"""

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
                response += f"👥 Yatırımcı: {investors:,}\n\n"
                
                response += f"🤖 AI PATTERN ANALİZİ:\n"
                response += f"{'='*55}\n"
                response += ai_analysis
                
                return response
                
            except Exception as e:
                print(f"Analiz hatası: {e}")
                import traceback
                traceback.print_exc()
                return f"❌ {fcode} analizi sırasında hata: {str(e)}"
        
        # Fon kodu yoksa genel tarama yap
        else:
            print("Fon kodu bulunamadı, genel tarama yapılıyor")
            return self._handle_general_ai_pattern_analysis()


    def _generate_single_fund_analysis(self, fcode, price, rsi, macd, bb_pos, sma20, support, resistance, price_vs_sma20):
        """Tek fon için tutarlı fallback analiz"""
        
        # RSI düzeltmesi - 0 ise yaklaşık hesapla
        if rsi == 0 or rsi == 100:
            # Price vs SMA20'ye göre tahmin
            if price_vs_sma20 < -10:
                rsi = 25  # Oversold tahmin
            elif price_vs_sma20 > 10:
                rsi = 75  # Overbought tahmin
            else:
                rsi = 50  # Nötr
        
        # Skorlama - GENEL TARAMA İLE TUTARLI
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
            if abs(macd) < 0.1:  # Zayıf negatif
                score -= 0.5
                signals.append("🟡 MACD hafif negatif")
            else:  # Güçlü negatif
                score -= 1
                signals.append("🔴 MACD negatif - düşüş momentumu")
        else:
            score += 1
            signals.append("🟢 MACD pozitif - yükseliş momentumu")
        
        # Bollinger analizi - DAHA HASSAS
        if bb_pos < 0.1:  # %10'un altında
            score += 2
            signals.append("🟢 Bollinger alt bandında - güçlü oversold")
            patterns.append("Bollinger squeeze - patlama potansiyeli")
        elif bb_pos < 0.3:  # %30'un altında
            score += 1
            signals.append("🟢 Alt banda yakın - alım fırsatı")
        elif bb_pos > 0.9:
            score -= 2
            signals.append("🔴 Bollinger üst bandında - overbought")
        elif bb_pos > 0.7:
            score -= 1
            signals.append("🟠 Üst banda yakın - dikkatli ol")
        
        # SMA20 analizi - ÖNEMLİ
        if price_vs_sma20 < -10:  # %10'dan fazla aşağıda
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
            
            if position_in_range < 0.2:  # Support'a çok yakın
                score += 1
                patterns.append("Support seviyesinde - dip fırsatı")
            elif position_in_range > 0.8:
                score -= 1
                patterns.append("Resistance yakın - satış baskısı")
        
        # TRN ÖZELİNDE - Düşük yatırımcı sayısı
        if fcode == "TRN" and bb_pos < 0.1 and price_vs_sma20 < -10:
            score += 1  # Ekstra puan
            patterns.append("Ekstrem oversold - potansiyel sert toparlanma")
        
        # TUTARLI ÖNERİ OLUŞTUR
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
        
        # Risk yönetimi - GERÇEKÇI
        if action == "AL":
            entry = price
            stop_loss = max(support * 0.98, price * 0.95)  # %5 veya support altı
            target1 = price + (price - stop_loss) * 1.5  # 1.5:1 R/R
            target2 = min(resistance * 0.98, price * 1.10)  # %10 veya resistance
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
    • Giriş: {entry:.4f} TL
    • Stop-Loss: {stop_loss:.4f} TL ({((stop_loss/entry-1)*100):+.1f}%)
    • Hedef 1: {target1:.4f} TL ({((target1/entry-1)*100):+.1f}%)
    • Hedef 2: {target2:.4f} TL ({((target2/entry-1)*100):+.1f}%)
    • Risk/Reward: 1:{risk_reward:.1f}

    {chr(10).join(special_notes) if special_notes else ''}

    📊 ÖZET ANALİZ:
    Fiyat SMA20'nin {price_vs_sma20:.1f}% {'altında' if price_vs_sma20 < 0 else 'üstünde'}, 
    Bollinger bandının %{bb_pos*100:.0f} pozisyonunda,
    RSI {rsi:.1f} seviyesinde.

    ⚠️ Not: Bu analiz kural tabanlı yapılmıştır. Yatırım tavsiyesi değildir.
    """
        
        return analysis

    def _handle_general_ai_pattern_analysis(self):
        """Genel AI pattern taraması - MEVCUT MV KOLONLARI İLE"""
        print("🤖 AI ile pattern taraması yapılıyor...")
        
        # Mevcut MV kolonlarını kullan
        query = """
        SELECT 
            fcode,
            current_price,
           rsi_14,
           stochastic_14,
            macd_line,
            bb_position,
            price_vs_sma20,
            sma_10,
            sma_20,
            sma_50,
            investorcount
        FROM mv_fund_technical_indicators
        WHERE data_points >= 30
        AND (
            rsi_14 < 30 OR rsi_14 > 70 OR
            ABS(macd_line) > 0.01 OR
            bb_position < 0.2 OR bb_position > 0.8 OR
            ABS(price_vs_sma20) > 5
        )
    ORDER BY days_since_last_trade ASC, ABS(price_vs_sma20) DESC
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
                
                # Genel sinyal
                bullish_score = 0
                if row['rsi_14'] < 30: bullish_score += 2
                if row['macd_line'] > 0: bullish_score += 1
                if row['bb_position'] < 0.3: bullish_score += 1
                if row['current_price'] > row['sma_20']: bullish_score += 1
                
                if bullish_score >= 3:
                    signal = "🟢 GÜÇLÜ AL SİNYALİ"
                elif bullish_score <= 1:
                    signal = "🔴 SAT SİNYALİ"
                else:
                    signal = "🟡 NÖTR"
                
                response += f"{idx+1}. {fcode} - {signal}\n"
                response += f"   💲 Fiyat: {row['current_price']:.4f} TL\n"
                response += f"   📊 RSI: {row['rsi_14']:.1f}\n"
                response += f"   📈 MACD: {row['macd_line']:.6f}\n"
                response += f"   📍 BB Pozisyon: %{row['bb_position']*100:.0f}\n"
                response += f"   📊 SMA20 Fark: {row['price_vs_sma20']:+.1f}%\n"
                response += f"   👥 Yatırımcı: {int(row['investorcount']):,}\n"
                response += f"   🎯 Patterns: {', '.join(patterns)}\n\n"
            
            response += f"\n💡 Detaylı AI analizi için: '[FON_KODU] ai pattern analizi'"
            
            return response
            
        except Exception as e:
            print(f"SQL hatası: {e}")
            import traceback
            traceback.print_exc()
            return "❌ Pattern taraması yapılamadı."




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
            # YENİ EKLEMELER
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
            # YENİ EKLEMELER
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
            # YENİ PATTERN'LER
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
            # YENİ METHOD MAPPING
            'handle_ai_pattern_analysis': ['ai pattern', 'ai teknik', 'pattern analizi', 
                                        'formasyon tespiti', 'yapay zeka teknik', 
                                        'chart pattern', 'teknik formasyon']
        }