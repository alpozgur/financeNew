import re
import time
from datetime import datetime, timedelta

import pandas as pd

class FundamentalAnalysisEnhancement:
    """Fundamental Analiz eklentisi - interactive_qa_dual_ai.py'ye entegre edilecek"""
    
    def __init__(self, coordinator, active_funds):
        self.coordinator = coordinator
        self.active_funds = active_funds
    
    # =============================================================
    # 2. HANDLER METODLARI - Mevcut sistemi kullanır
    # =============================================================

    def handle_capacity_questions(self, question):
        """Kapasite analizi - GÜNCEL KAYITLARLA"""
        
        print("💰 Fon kapasitesi analiz ediliyor...")
        
        numbers = re.findall(r'(\d+(?:\.\d+)?)\s*(milyon|milyar|million|billion)', question.lower())
        
        if numbers:
            amount = float(numbers[0][0])
            unit = numbers[0][1]
            
            if unit in ['milyon', 'million']:
                threshold = amount * 1000000
            else:
                threshold = amount * 1000000000
            
            response = f"\n💰 FON KAPASİTE ANALİZİ - {amount:,.0f} {unit.upper()}\n"
            response += f"{'='*55}\n\n"
            response += f"🎯 Aranılan Eşik: {threshold:,.0f} TL\n\n"
            
            large_funds = []
            
            try:
                # 🔧 DÜZELTME: Her fon için en güncel kaydı al
                query = f"""
                WITH latest_records AS (
                    SELECT fcode, fcapacity, investorcount, price, pdate,
                        ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY pdate DESC) as rn
                    FROM tefasfunds 
                    WHERE fcapacity > {threshold}
                    AND pdate >= CURRENT_DATE - INTERVAL '7 days'
                )
                SELECT fcode, fcapacity, investorcount, price
                FROM latest_records 
                WHERE rn = 1
                ORDER BY fcapacity DESC
                LIMIT 20
                """
                
                result = self.coordinator.db.execute_query(query)
                print(f"   📊 SQL sorgusu: {len(result)} BENZERSIZ büyük fon bulundu")
                
                for _, row in result.iterrows():
                    fcode = row['fcode']
                    capacity = float(row['fcapacity'])
                    price = float(row['price']) if pd.notna(row['price']) else 0
                    investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                    
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                    
                    large_funds.append({
                        'fcode': fcode,
                        'capacity': capacity,
                        'current_price': price,
                        'investors': investors,
                        'fund_name': fund_name
                    })
                    
            except Exception as e:
                print(f"   ❌ SQL sorgu hatası: {e}")
                return f"❌ Kapasite analizi başarısız: {e}"
            
            # Sonuçları sırala
            large_funds.sort(key=lambda x: x['capacity'], reverse=True)
            
            if large_funds:
                response += f"🏆 BÜYÜK KAPASİTELİ FONLAR (Benzersiz - En Güncel):\n\n"
                
                for i, fund in enumerate(large_funds[:15], 1):
                    response += f"{i:2d}. {fund['fcode']}\n"
                    response += f"    💰 Kapasite: {fund['capacity']:,.0f} TL\n"
                    response += f"    💲 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
                    if fund['investors'] > 0:
                        response += f"    👥 Yatırımcı: {fund['investors']:,} kişi\n"
                    if fund['fund_name'] != 'N/A':
                        response += f"    📝 Adı: {fund['fund_name'][:50]}...\n"
                    response += f"\n"
                
                response += f"💡 NOT: Her fon sadece 1 kez gösteriliyor (en güncel verilerle)\n"
                
            else:
                response += f"❌ {threshold:,.0f} TL üstü kapasiteli fon bulunamadı.\n"
            
            return response
        
        else:
            return "❌ Kapasite değeri belirtilmedi. Örnek: 'Kapasitesi 500 milyon TL üstü fonlar'"

    def handle_investor_count_questions(self, question):
        """Yatırımcı sayısı analizi - GÜNCEL KAYITLARLA DÜZELTILMIŞ"""
        
        print("👥 Yatırımcı sayısı analiz ediliyor...")
        
        # Sayısal değer çıkar
        numbers = re.findall(r'(\d+)', question)
        min_investors = int(numbers[0]) if numbers else 1000
        
        response = f"\n👥 YATIRIMCI SAYISI ANALİZİ\n"
        response += f"{'='*40}\n\n"
        response += f"🎯 Minimum Yatırımcı: {min_investors:,}\n\n"
        
        popular_funds = []
        
        # 🔧 DÜZELTME: Her fon için EN GÜNCEL kaydı al
        try:
            # OPTION 1: Window Function ile (en güvenilir)
            query = f"""
            WITH latest_records AS (
                SELECT fcode, investorcount, price, fcapacity, pdate,
                    ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY pdate DESC) as rn
                FROM tefasfunds 
                WHERE investorcount > {min_investors}
                AND pdate >= CURRENT_DATE - INTERVAL '7 days'
            )
            SELECT fcode, investorcount, price, fcapacity
            FROM latest_records 
            WHERE rn = 1
            ORDER BY investorcount DESC
            LIMIT 20
            """
            
            result = self.coordinator.db.execute_query(query)
            
            print(f"   📊 SQL sorgusu: {len(result)} BENZERSIZ fon bulundu")
            
            for _, row in result.iterrows():
                fcode = row['fcode']
                investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                price = float(row['price']) if pd.notna(row['price']) else 0
                capacity = float(row['fcapacity']) if pd.notna(row['fcapacity']) else 0
                
                # Fund details'den isim al
                details = self.coordinator.db.get_fund_details(fcode)
                fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                fund_type = details.get('fund_type', 'N/A') if details else 'N/A'
                
                popular_funds.append({
                    'fcode': fcode,
                    'investors': investors,
                    'fund_name': fund_name,
                    'fund_type': fund_type,
                    'current_price': price,
                    'capacity': capacity
                })
                
        except Exception as e:
            print(f"   ❌ Window function hatası: {e}")
            
            # FALLBACK: Basit güncel tarih sorgusu
            try:
                fallback_query = f"""
                SELECT fcode, investorcount, price, fcapacity
                FROM tefasfunds 
                WHERE investorcount > {min_investors}
                AND pdate = (SELECT MAX(pdate) FROM tefasfunds)
                ORDER BY investorcount DESC
                LIMIT 20
                """
                
                result = self.coordinator.db.execute_query(fallback_query)
                print(f"   📊 Fallback sorgusu: {len(result)} fon bulundu")
                
                for _, row in result.iterrows():
                    fcode = row['fcode']
                    investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                    price = float(row['price']) if pd.notna(row['price']) else 0
                    capacity = float(row['fcapacity']) if pd.notna(row['fcapacity']) else 0
                    
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                    fund_type = details.get('fund_type', 'N/A') if details else 'N/A'
                    
                    popular_funds.append({
                        'fcode': fcode,
                        'investors': investors,
                        'fund_name': fund_name,
                        'fund_type': fund_type,
                        'current_price': price,
                        'capacity': capacity
                    })
                    
            except Exception as e2:
                print(f"   ❌ Fallback de başarısız: {e2}")
                return "❌ Yatırımcı sayısı analizi yapılamadı - veritabanı hatası"
        
        # Yatırımcı sayısına göre sırala (Python'da da kontrol et)
        popular_funds.sort(key=lambda x: x['investors'], reverse=True)
        
        if popular_funds:
            response += f"🏆 EN POPÜLER FONLAR (Benzersiz Fonlar - En Güncel Veriler):\n\n"
            
            for i, fund in enumerate(popular_funds[:15], 1):  # İlk 15'i göster
                response += f"{i:2d}. {fund['fcode']}\n"
                response += f"    👥 Yatırımcı: {fund['investors']:,} kişi\n"
                response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
                if fund['capacity'] > 0:
                    response += f"    💰 Kapasite: {fund['capacity']:,.0f} TL\n"
                response += f"    🏷️ Tür: {fund['fund_type']}\n"
                if fund['fund_name'] != 'N/A':
                    response += f"    📝 Adı: {fund['fund_name'][:40]}...\n"
                response += f"\n"
            
            # İstatistikler
            total_investors = sum(f['investors'] for f in popular_funds)
            avg_investors = total_investors / len(popular_funds)
            
            response += f"📊 İSTATİSTİKLER (Benzersiz Fonlar):\n"
            response += f"   Bulunan Fon Sayısı: {len(popular_funds)}\n"
            response += f"   Toplam Yatırımcı: {total_investors:,}\n"
            response += f"   Ortalama: {avg_investors:,.0f}\n"
            response += f"   En Popüler: {popular_funds[0]['fcode']} ({popular_funds[0]['investors']:,} kişi)\n"
            
            # En büyük 3'ün detayı
            response += f"\n🥇 TOP 3 BENZERSIZ FONLAR:\n"
            for i, fund in enumerate(popular_funds[:3], 1):
                response += f"   {i}. {fund['fcode']}: {fund['investors']:,} yatırımcı\n"
            
            # Duplicate uyarısı
            response += f"\n💡 NOT: Artık her fon sadece 1 kez gösteriliyor (en güncel verilerle)\n"
            
        else:
            response += f"❌ {min_investors:,} üstü yatırımcısı olan fon bulunamadı.\n"
            response += f"💡 Daha düşük bir eşik deneyin (örn: {min_investors//2:,}).\n"
        
        return response

    def handle_safest_funds_list(self, count=10, days=60):
        """En güvenli fonların listesi - HIZLANDIRILAN VERSİYON"""
        print(f"🛡️ En güvenli {count} fon analiz ediliyor...")
        
        safe_funds = []
        
        # 🚀 HIZLANDIRMA 1: Sadece active_funds kullan (1753 değil, 50 fon)
        print(f"   ⚡ {len(self.active_funds)} aktif fonu analiz ediliyor...")
        
        start_time = time.time()
        processed = 0
        
        for fcode in self.active_funds:  # Zaten optimize edilmiş 50 fon
            try:
                processed += 1
                if processed % 10 == 0:
                    elapsed = time.time() - start_time
                    print(f"   📊 {processed}/{len(self.active_funds)} işlendi ({elapsed:.1f}s)")
                
                # 🚀 HIZLANDIRMA 2: Daha az veri çek (60 gün yerine 30)
                data = self.coordinator.db.get_fund_price_history(fcode, 30)
                
                if len(data) >= 15:  # 15 gün yeterli
                    prices = data.set_index('pdate')['price'].sort_index()
                    returns = prices.pct_change().dropna()
                    
                    # 🚀 HIZLANDIRMA 3: Sadece temel metrikler
                    volatility = returns.std() * 100
                    total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                    
                    # 🚀 HIZLANDIRMA 4: Fund details'i sonradan al
                    safe_funds.append({
                        'fcode': fcode,
                        'volatility': volatility,
                        'total_return': total_return,
                        'current_price': prices.iloc[-1],
                        'data_points': len(prices)
                    })
                    
            except Exception:
                continue
        
        elapsed = time.time() - start_time
        print(f"   ✅ {len(safe_funds)} fon analiz edildi ({elapsed:.1f} saniye)")
        
        if not safe_funds:
            return f"❌ Analiz edilebilir güvenli fon bulunamadı."
        
        # Volatiliteye göre sırala
        safe_funds.sort(key=lambda x: x['volatility'])
        
        # 🚀 HIZLANDIRMA 5: Sadece top fonlar için fund details al
        top_funds = safe_funds[:count]
        
        for fund in top_funds:
            try:
                details = self.coordinator.db.get_fund_details(fund['fcode'])
                fund['fund_name'] = details.get('fund_name', 'N/A') if details else 'N/A'
                fund['fund_type'] = details.get('fund_type', 'N/A') if details else 'N/A'
            except:
                fund['fund_name'] = 'N/A'
                fund['fund_type'] = 'N/A'
        
        # Response oluştur
        response = f"\n🛡️ EN GÜVENLİ {count} FON (Son 30 Gün Volatilite)\n"
        response += f"{'='*50}\n\n"
        response += f"📊 ANALİZ SONUCU:\n"
        response += f"   • Analiz Edilen: {len(safe_funds)} fon\n"
        response += f"   • Analiz Süresi: {elapsed:.1f} saniye\n"
        response += f"   • En Düşük Volatilite: %{safe_funds[0]['volatility']:.2f}\n\n"
        
        response += f"🛡️ EN GÜVENLİ FONLAR:\n\n"
        
        for i, fund in enumerate(top_funds, 1):
            # Risk seviyesi
            if fund['volatility'] < 1:
                risk_level = "🟢 ÇOK GÜVENLİ"
            elif fund['volatility'] < 2:
                risk_level = "🟡 GÜVENLİ"
            elif fund['volatility'] < 4:
                risk_level = "🟠 ORTA"
            else:
                risk_level = "🔴 RİSKLİ"
            
            response += f"{i:2d}. {fund['fcode']} - {risk_level}\n"
            response += f"    📉 Volatilite: %{fund['volatility']:.2f}\n"
            response += f"    📈 Getiri: %{fund['total_return']:+.2f}\n"
            response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
            response += f"    🏷️ Tür: {fund['fund_type']}\n"
            response += f"\n"
        
        # Hızlı istatistikler
        avg_vol = sum(f['volatility'] for f in top_funds) / len(top_funds)
        avg_return = sum(f['total_return'] for f in top_funds) / len(top_funds)
        
        response += f"📊 ÖZEİ:\n"
        response += f"   Ortalama Volatilite: %{avg_vol:.2f}\n"
        response += f"   Ortalama Getiri: %{avg_return:+.2f}\n"
        response += f"   En Güvenli: {top_funds[0]['fcode']} (%{top_funds[0]['volatility']:.2f})\n"
        
        return response

    def handle_new_funds_questions(self, question):
        """Yeni kurulan fonlar analizi"""
        
        print("🆕 Yeni fonlar analiz ediliyor...")
        
        # Son 1 yıl içinde kurulan fonları bul
        cutoff_date = datetime.now() - timedelta(days=365)
        
        response = f"\n🆕 YENİ KURULAN FONLAR ANALİZİ\n"
        response += f"{'='*45}\n\n"
        response += f"📅 Arama Periyodu: Son 1 yıl ({cutoff_date.strftime('%d.%m.%Y')} sonrası)\n\n"
        
        new_funds = []
        
        for fcode in self.active_funds[:40]:
            try:
                # Fonun geçmiş verilerini al
                data = self.coordinator.db.get_fund_price_history(fcode, 400)
                
                if not data.empty:
                    # İlk veri tarihi = kuruluş tarihi (yaklaşık)
                    first_date = pd.to_datetime(data['pdate'].min())
                    
                    if first_date >= cutoff_date:
                        # Fund details'den bilgi al
                        details = self.coordinator.db.get_fund_details(fcode)
                        fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                        fund_type = details.get('fund_type', 'N/A') if details else 'N/A'
                        
                        # Performans hesapla
                        current_price = data['price'].iloc[-1]
                        first_price = data['price'].iloc[0]
                        performance = (current_price / first_price - 1) * 100
                        
                        new_funds.append({
                            'fcode': fcode,
                            'start_date': first_date,
                            'fund_name': fund_name,
                            'fund_type': fund_type,
                            'performance': performance,
                            'days_old': (datetime.now() - first_date).days,
                            'current_price': current_price
                        })
                        
            except Exception:
                continue
        
        # Tarihe göre sırala (en yeni önce)
        new_funds.sort(key=lambda x: x['start_date'], reverse=True)
        
        if new_funds:
            response += f"🚀 BULUNAN YENİ FONLAR ({len(new_funds)} adet):\n\n"
            
            for i, fund in enumerate(new_funds[:8], 1):
                days_old = fund['days_old']
                months_old = days_old / 30
                
                response += f"{i}. {fund['fcode']}\n"
                response += f"   📅 Kuruluş: {fund['start_date'].strftime('%d.%m.%Y')}\n"
                response += f"   ⏰ Yaş: {months_old:.1f} ay ({days_old} gün)\n"
                response += f"   📊 Performans: %{fund['performance']:+.2f}\n"
                response += f"   🏷️ Tür: {fund['fund_type']}\n"
                response += f"   💲 Fiyat: {fund['current_price']:.4f} TL\n"
                if fund['fund_name'] != 'N/A':
                    response += f"   📝 Adı: {fund['fund_name'][:35]}...\n"
                response += f"\n"
            
            # En iyi performans
            best_performer = max(new_funds, key=lambda x: x['performance'])
            response += f"🏆 EN İYİ YENİ FON PERFORMANSI:\n"
            response += f"   {best_performer['fcode']}: %{best_performer['performance']:+.2f}\n"
            
        else:
            response += f"❌ Son 1 yılda kurulan fon bulunamadı.\n"
            response += f"💡 Tüm fonlar 1 yıldan eski görünüyor.\n"
        
        return response

    def handle_largest_funds_questions(self, question, count=None):
        """En büyük fonlar analizi - Kullanıcının istediği sayıda"""
        print("🏢 En büyük fonlar SQL analizi...")
        
        # Kullanıcının istediği sayıyı tespit et
        numbers_in_question = re.findall(r'(\d+)', question)
        requested_count = int(numbers_in_question[0]) if numbers_in_question else 10
        
        # SQL için biraz fazla çek (filtering için)
        sql_limit = max(requested_count * 2, 20)
        
        try:
            # SQL ile en büyük fonları bul - JOIN ile her iki tablodan veri çek
            query = f'''
            WITH latest_data AS (
                SELECT f.fcode, f.fcapacity, f.investorcount, f.price, f.pdate,
                    f.ftitle as fund_name, null as fund_type,
                    ROW_NUMBER() OVER (PARTITION BY f.fcode ORDER BY f.pdate DESC) as rn
                FROM tefasfunds f
                LEFT JOIN tefasfunddetails d ON f.fcode = d.fcode
                WHERE f.fcapacity > 1000000  -- En az 1M TL
                AND f.investorcount > 100    -- En az 100 yatırımcı
                AND f.pdate >= CURRENT_DATE - INTERVAL '7 days'
            )
            SELECT fcode, fcapacity, investorcount, price, fund_name, fund_type
            FROM latest_data 
            WHERE rn = 1
            ORDER BY fcapacity DESC
            LIMIT {sql_limit}
            '''
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                # Fallback: Eşiği düşür
                print("   💡 Yüksek eşikle sonuç yok, eşik düşürülüyor...")
                
                fallback_query = f'''
                WITH latest_data AS (
                    SELECT f.fcode, f.fcapacity, f.investorcount, f.price,
                        f.ftitle as fund_name, null as fund_type,
                        ROW_NUMBER() OVER (PARTITION BY f.fcode ORDER BY f.pdate DESC) as rn
                    FROM tefasfunds f
                    LEFT JOIN tefasfunddetails d ON f.fcode = d.fcode
                    WHERE f.fcapacity > 100000   -- En az 100K TL
                    AND f.pdate >= CURRENT_DATE - INTERVAL '14 days'
                )
                SELECT fcode, fcapacity, investorcount, price, fund_name, fund_type
                FROM latest_data 
                WHERE rn = 1
                ORDER BY fcapacity DESC
                LIMIT {sql_limit}
                '''
                
                result = self.coordinator.db.execute_query(fallback_query)
                
            if result.empty:
                return f"❌ En büyük {requested_count} fon verisi bulunamadı - veritabanında kapasite bilgisi eksik olabilir."
            
            # Sadece kullanıcının istediği sayıda al
            result = result.head(requested_count)
            
            print(f"   ✅ {len(result)} büyük fon bulundu (istenen: {requested_count})")
            
            response = f"\n🏢 EN BÜYÜK {requested_count} FON (Kapasite Bazlı)\n"
            response += f"{'='*45}\n\n"
            response += f"📊 ANALİZ SONUCU:\n"
            response += f"   • İstenen Fon Sayısı: {requested_count}\n"
            response += f"   • Bulunan Fon: {len(result)}\n"
            response += f"   • En Büyük Kapasite: {result.iloc[0]['fcapacity']:,.0f} TL\n\n"
            
            for i, (_, row) in enumerate(result.iterrows(), 1):
                fcode = row['fcode']
                capacity = float(row['fcapacity'])
                investors = int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                price = float(row['price']) if pd.notna(row['price']) else 0
                fund_name = row['fund_name'] if pd.notna(row['fund_name']) else 'N/A'
                fund_type = row['fund_type'] if pd.notna(row['fund_type']) else 'N/A'
                
                # Kapasiteyi okunabilir formatta göster
                if capacity >= 1000000000:  # 1 milyar+
                    capacity_text = f"{capacity/1000000000:.1f} milyar TL"
                elif capacity >= 1000000:  # 1 milyon+
                    capacity_text = f"{capacity/1000000:.0f} milyon TL"
                else:
                    capacity_text = f"{capacity:,.0f} TL"
                
                response += f"{i:2d}. {fcode}\n"
                response += f"    💰 Kapasite: {capacity_text}\n"
                response += f"    👥 Yatırımcı: {investors:,} kişi\n"
                response += f"    💲 Güncel Fiyat: {price:.4f} TL\n"
                response += f"    🏷️ Tür: {fund_type}\n"
                if fund_name != 'N/A':
                    response += f"    📝 Adı: {fund_name[:45]}...\n"
                response += f"\n"
            
            # En büyük 3'ün özeti (veya daha az varsa hepsini göster)
            top_count = min(3, len(result))
            response += f"🏆 TOP {top_count} ÖZET:\n"
            for i, (_, row) in enumerate(result.head(top_count).iterrows(), 1):
                capacity_billion = row['fcapacity'] / 1000000000
                if capacity_billion >= 1:
                    response += f"   {i}. {row['fcode']}: {capacity_billion:.1f} milyar TL\n"
                else:
                    response += f"   {i}. {row['fcode']}: {row['fcapacity']/1000000:.0f} milyon TL\n"
            
            # İstatistikler
            total_capacity = result['fcapacity'].sum()
            avg_capacity = result['fcapacity'].mean()
            total_investors = result['investorcount'].sum()
            
            response += f"\n📊 {requested_count} FON İSTATİSTİKLERİ:\n"
            response += f"   Toplam Kapasite: {total_capacity/1000000000:.1f} milyar TL\n"
            response += f"   Ortalama Kapasite: {avg_capacity/1000000:.0f} milyon TL\n"
            response += f"   Toplam Yatırımcı: {total_investors:,} kişi\n"
            
            return response
            
        except Exception as e:
            print(f"   ❌ SQL analizi hatası: {e}")
            return f"❌ SQL analizi hatası: {e}\n💡 Veritabanı şemasını kontrol edin - fcapacity kolonu mevcut mu?"
    
    def handle_fund_age_questions(self, question):
        """Fon yaşı analizi"""
        print("⏰ Fon yaşları analiz ediliyor...")
        
        response = f"\n⏰ EN ESKİ/KÖKLÜ FONLAR ANALİZİ\n"
        response += f"{'='*40}\n\n"
        
        fund_ages = []
        
        for fcode in self.active_funds[:40]:
            try:
                # En eski veriyi bul
                data = self.coordinator.db.get_fund_price_history(fcode, 2000)  # Maksimum veri
                
                if not data.empty:
                    oldest_date = pd.to_datetime(data['pdate'].min())
                    newest_date = pd.to_datetime(data['pdate'].max())
                    
                    # Yaş hesapla
                    fund_age_days = (datetime.now() - oldest_date).days
                    fund_age_years = fund_age_days / 365.25
                    
                    # Fund details
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                    
                    # Performans (tüm zamanlar)
                    first_price = data['price'].iloc[0]
                    last_price = data['price'].iloc[-1]
                    total_performance = (last_price / first_price - 1) * 100
                    
                    fund_ages.append({
                        'fcode': fcode,
                        'start_date': oldest_date,
                        'age_years': fund_age_years,
                        'age_days': fund_age_days,
                        'fund_name': fund_name,
                        'total_performance': total_performance,
                        'current_price': last_price,
                        'data_points': len(data)
                    })
                    
            except Exception:
                continue
        
        # Yaşa göre sırala (en eski önce)
        fund_ages.sort(key=lambda x: x['age_years'], reverse=True)
        
        if fund_ages:
            response += f"🏛️ EN ESKİ/KÖKLÜ FONLAR:\n\n"
            
            for i, fund in enumerate(fund_ages[:8], 1):
                response += f"{i}. {fund['fcode']}\n"
                response += f"   📅 Kuruluş: {fund['start_date'].strftime('%d.%m.%Y')}\n"
                response += f"   ⏰ Yaş: {fund['age_years']:.1f} yıl ({fund['age_days']:,} gün)\n"
                response += f"   📊 Toplam Performans: %{fund['total_performance']:+.1f}\n"
                response += f"   📈 Veri Noktası: {fund['data_points']:,}\n"
                response += f"   💲 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
                if fund['fund_name'] != 'N/A':
                    response += f"   📝 Adı: {fund['fund_name'][:35]}...\n"
                response += f"\n"
            
            # İstatistikler
            avg_age = sum(f['age_years'] for f in fund_ages) / len(fund_ages)
            oldest_fund = fund_ages[0]
            
            response += f"📊 YAŞ İSTATİSTİKLERİ:\n"
            response += f"   Ortalama Yaş: {avg_age:.1f} yıl\n"
            response += f"   En Eski Fon: {oldest_fund['fcode']} ({oldest_fund['age_years']:.1f} yıl)\n"
            response += f"   En Başarılı Eski Fon: {max(fund_ages, key=lambda x: x['total_performance'])['fcode']}\n"
            
        else:
            response += f"❌ Fon yaşı verileri alınamadı.\n"
        
        return response

    def handle_fund_category_questions(self, question):
        """Fon kategori/tür analizi"""
        print("🏷️ Fon kategorileri analiz ediliyor...")
        
        response = f"\n🏷️ FON KATEGORİ/TÜR ANALİZİ\n"
        response += f"{'='*40}\n\n"
        
        categories = {}
        fund_types = {}
        
        for fcode in self.active_funds[:50]:
            try:
                details = self.coordinator.db.get_fund_details(fcode)
                
                if details:
                    category = details.get('fund_category', 'Bilinmiyor')
                    fund_type = details.get('fund_type', 'Bilinmiyor')
                    
                    # Kategori sayımı
                    if category in categories:
                        categories[category].append(fcode)
                    else:
                        categories[category] = [fcode]
                    
                    # Tür sayımı
                    if fund_type in fund_types:
                        fund_types[fund_type].append(fcode)
                    else:
                        fund_types[fund_type] = [fcode]
                        
            except Exception:
                continue
        
        # Kategorileri sırala
        sorted_categories = sorted(categories.items(), key=lambda x: len(x[1]), reverse=True)
        sorted_types = sorted(fund_types.items(), key=lambda x: len(x[1]), reverse=True)
        
        response += f"📊 FON KATEGORİLERİ (En Popüler → En Az):\n\n"
        
        for i, (category, funds) in enumerate(sorted_categories[:8], 1):
            response += f"{i:2d}. {category}\n"
            response += f"    📊 Fon Sayısı: {len(funds)}\n"
            response += f"    📝 Örnek Fonlar: {', '.join(funds[:3])}\n"
            response += f"\n"
        
        response += f"🏷️ FON TÜRLERİ:\n\n"
        
        for i, (fund_type, funds) in enumerate(sorted_types[:6], 1):
            response += f"{i}. {fund_type}: {len(funds)} fon\n"
        
        response += f"\n📈 DAĞILIM İSTATİSTİKLERİ:\n"
        response += f"   Toplam Kategori: {len(categories)}\n"
        response += f"   Toplam Tür: {len(fund_types)}\n"
        response += f"   En Popüler Kategori: {sorted_categories[0][0]} ({len(sorted_categories[0][1])} fon)\n"
        
        return response

    def capacity_help_message(self):
        """Kapasite sorusu için yardım mesajı"""
        return f"""
❌ Kapasite değeri belirtilmedi!

💡 ÖRNEK KULLANIM:
   • "Kapasitesi 500 milyon TL üstü fonlar"
   • "1 milyar TL üzerinde fon var mı?"
   • "Büyüklüğü 100 milyon üstü fonları listele"

📝 DESTEKLENENLER:
   • milyon/million
   • milyar/billion  
   • Sayısal değerler (100, 500, 1.5 vb.)
"""

    @staticmethod
    def get_examples():
        """Temel analiz örnekleri"""
        return [
            "En büyük 10 fon hangileri?",
            "Kapasitesi en yüksek fonlar",
            "En çok yatırımcısı olan fonlar",
            "Yeni kurulan fonlar",
            "En eski fonlar hangileri?",
            "Popüler fonlar listesi"
        ]
    
    @staticmethod
    def get_keywords():
        """Temel analiz anahtar kelimeleri"""
        return [
            "büyük", "kapasite", "yatırımcı", "popüler", "yeni",
            "eski", "köklü", "kurulan", "largest", "biggest"
        ]
    
    @staticmethod
    def get_patterns():
        """Temel analiz pattern'leri"""
        return [
            {
                'type': 'regex',
                'pattern': r'en büyük\s*\d*\s*fon',
                'score': 0.95
            },
            {
                'type': 'contains_all',
                'words': ['kapasite', 'yüksek'],
                'score': 0.9
            },
            {
                'type': 'contains_all',
                'words': ['yatırımcı', 'çok'],
                'score': 0.9
            }
        ]
    
    @staticmethod
    def get_method_patterns():
        """Method mapping"""
        return {
            'handle_largest_funds_questions': ['en büyük', 'largest', 'kapasite'],
            'handle_investor_count_questions': ['yatırımcı', 'popüler'],
            'handle_new_funds_questions': ['yeni', 'kurulan'],
            'handle_fund_age_questions': ['eski', 'köklü']
        }