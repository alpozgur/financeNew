from datetime import datetime
import time
import pandas as pd
import numpy as np

class PerformanceAnalyzerMain:
    def __init__(self, coordinator, active_funds, ai_status):
        self.coordinator = coordinator
        self.active_funds = active_funds
        self.ai_status = ai_status
    def handle_fund_past_performance_question(self, question):
        words = question.upper().split()
        fund_code = None
        for word in words:
            if len(word) == 3 and word.isalpha():
                if word.upper() in [x.upper() for x in self.active_funds]:
                    fund_code = word.upper()
                    break
        if not fund_code:
            return "❌ Geçerli bir fon kodu tespit edilemedi."
        data = self.coordinator.db.get_fund_price_history(fund_code, 252)
        if data.empty:
            return f"❌ {fund_code} için 1 yıllık veri bulunamadı."
        prices = data.set_index('pdate')['price'].sort_index()
        total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
        response = f"\n📈 {fund_code} FONU SON 1 YIL PERFORMANSI\n{'='*40}\n"
        response += f"Başlangıç Fiyatı: {prices.iloc[0]:.4f} TL\n"
        response += f"Son Fiyat: {prices.iloc[-1]:.4f} TL\n"
        response += f"Toplam Getiri: %{total_return:.2f}\n"
        return response

    def handle_top_gainer_fund_question(self, question):
        max_return = -999
        best_fund = None
        for fcode in self.active_funds:
            data = self.coordinator.db.get_fund_price_history(fcode, 30)
            if not data.empty:
                prices = data['price']
                ret = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                if ret > max_return:
                    max_return = ret
                    best_fund = fcode
        if best_fund:
            return f"🚀 Son 30 günde en çok kazandıran fon: {best_fund}\nGetiri: %{max_return:.2f}"
        else:
            return "En çok kazandıran fon bulunamadı."

    def handle_top_loser_fund_question(self, question):
        min_return = 999
        worst_fund = None
        for fcode in self.active_funds:
            data = self.coordinator.db.get_fund_price_history(fcode, 30)
            if not data.empty:
                prices = data['price']
                ret = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                if ret < min_return:
                    min_return = ret
                    worst_fund = fcode
        if worst_fund:
            return f"🔻 Son 30 günde en çok kaybettiren fon: {worst_fund}\nGetiri: %{min_return:.2f}"
        else:
            return "En çok kaybettiren fon bulunamadı."

    def handle_top_sharpe_funds_question(self, question):
        results = []
        for fcode in self.active_funds:
            data = self.coordinator.db.get_fund_price_history(fcode, 60)
            if not data.empty:
                prices = data.set_index('pdate')['price'].sort_index()
                returns = prices.pct_change().dropna()
                annual_return = (prices.iloc[-1] / prices.iloc[0] - 1) * (252 / len(prices)) * 100
                volatility = returns.std() * np.sqrt(252) * 100
                sharpe = (annual_return - 15) / volatility if volatility > 0 else 0
                results.append((fcode, sharpe))
        if not results:
            return "Sharpe oranı hesaplanamadı."
        results.sort(key=lambda x: x[1], reverse=True)
        response = "\n🏆 Sharpe Oranı En Yüksek 3 Fon\n"
        for fcode, sharpe in results[:3]:
            response += f"{fcode}: Sharpe Oranı: {sharpe:.2f}\n"
        return response
    
    def handle_low_volatility_funds_question(self, question):
        import re
        m = re.search(r'volatilite.*?(\d+)', question)
        threshold = 10  # default
        if m:
            threshold = float(m.group(1))
        results = []
        for fcode in self.active_funds:
            data = self.coordinator.db.get_fund_price_history(fcode, 60)
            if not data.empty:
                prices = data.set_index('pdate')['price'].sort_index()
                returns = prices.pct_change().dropna()
                volatility = returns.std() * 100
                if volatility < threshold:
                    results.append((fcode, volatility))
        if not results:
            return f"Volatilitesi {threshold}'in altında fon bulunamadı."
        response = f"\n📉 Volatilitesi {threshold}'in Altında Fonlar\n"
        for fcode, vol in results:
            response += f"{fcode}: Volatilite: %{vol:.2f}\n"
        return response
    
    def handle_analysis_question_dual(self, question):
        """Tek fon analizi - Her iki AI ile (fonun detayları AI prompt'una eklenir)"""
        words = question.upper().split()
        fund_code = None

        for word in words:
            if len(word) == 3 and word.isalpha():
                if word.upper() in [x.upper() for x in self.active_funds]:
                    fund_code = word.upper()
                    break
        # Eğer aktif fonlar içinde bulamazsan, tüm fonlarda ara
        if not fund_code:
            all_funds = [x.upper() for x in self.coordinator.db.get_all_fund_codes()]
            for word in words:
                if len(word) == 3 and word.isalpha():
                    if word.upper() in all_funds:
                        fund_code = word.upper()
                        break
        if not fund_code:
            return f"❌ Geçerli bir fon kodu bulunamadı. Örnek: 'AKB fonunu analiz et'\nMevcut fonlar: {', '.join(self.active_funds[:10])}..."

        try:
            print(f"🔍 {fund_code} fonu dual AI analizi...")

            # Veritabanı analizi
            data = self.coordinator.db.get_fund_price_history(fund_code, 100)

            if data.empty:
                return f"❌ {fund_code} için veri bulunamadı"

            prices = data.set_index('pdate')['price'].sort_index()
            returns = prices.pct_change().dropna()

            # Temel metrikler
            total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
            annual_return = total_return * (252 / len(prices))
            volatility = returns.std() * np.sqrt(252) * 100
            sharpe = (annual_return - 15) / volatility if volatility > 0 else 0
            win_rate = (returns > 0).sum() / len(returns) * 100

            # --- FON DETAYLARI ---
            details = self.coordinator.db.get_fund_details(fund_code) if hasattr(self.coordinator.db, 'get_fund_details') else {}
            name = details.get('fund_name', '')
            category = details.get('fund_category', '')
            fund_type = details.get('fund_type', '')
            description = details.get('description', '')
            details_text = f"{fund_code}: {name} - {category} - {fund_type}. {description}".strip()

            # Sonuçları formatla
            response = f"\n📊 {fund_code} FONU DUAL AI ANALİZ RAPORU\n"
            response += f"{'='*45}\n\n"

            response += f"💰 TEMEL VERİLER:\n"
            response += f"   Güncel Fiyat: {prices.iloc[-1]:.4f} TL\n"
            response += f"   Son {len(prices)} Gün Getiri: %{total_return:.2f}\n"
            response += f"   Yıllık Getiri (Tahmini): %{annual_return:.1f}\n"
            response += f"   Volatilite: %{volatility:.1f}\n"
            response += f"   Sharpe Oranı: {sharpe:.3f}\n"
            response += f"   Kazanma Oranı: %{win_rate:.1f}\n\n"

            # AI Analizleri
            ai_prompt = f"""
            {details_text}

            Analiz verileri:
            Güncel Fiyat: {prices.iloc[-1]:.4f} TL
            Yıllık Getiri: %{annual_return:.1f}
            Volatilite: %{volatility:.1f}
            Sharpe Oranı: {sharpe:.3f}
            Kazanma Oranı: %{win_rate:.1f}
            Veri Periyodu: {len(prices)} gün

            Yukarıdaki fon bilgileriyle, bu fonun risk ve getiri profilini, avantaj/dezavantajlarını ve hangi yatırımcıya uygun olabileceğini 150 kelimeyi aşmadan açıklayıp özetle.
            """

            response += f"🤖 DUAL AI DEĞERLENDİRMESİ:\n"
            response += f"{'='*30}\n"

            response += f"\n🤖 AI DEĞERLENDİRMESİ:\n"
            response += f"{'='*30}\n"

            if hasattr(self.coordinator, 'ai_provider') and self.coordinator.ai_provider.is_available():
                try:
                    ai_analysis = self.coordinator.ai_provider.query(
                        ai_prompt,
                        "Sen TEFAS fonu uzmanısın."
                    )
                    response += ai_analysis
                except Exception as e:
                    response += f"❌ AI analizi alınamadı: {str(e)[:50]}\n"
            else:
                response += "⚠️ AI sistemi şu anda kullanılamıyor.\n"

            response += f"\n✅ Analiz tamamlandı: {datetime.now().strftime('%H:%M:%S')}\n"

            return response

        except Exception as e:
            return f"❌ Analiz hatası: {e}"
    
    def handle_2025_recommendation_dual(self, question):
            """2025 fon önerisi - Her iki AI ile analiz"""
            print("🎯 2025 Fund Recommendation Analysis - Dual AI...")
            
            # Tutar parsing
            import re
            amounts = re.findall(r'\b(\d{5,})\b', question)
            investment_amount = 100000
            if amounts:
                try:
                    investment_amount = int(amounts[0])
                except:
                    pass
            
            # Risk toleransını tespit et
            risk_tolerance = "moderate"
            if any(word in question.lower() for word in ['güvenli', 'safe', 'conservative']):
                risk_tolerance = "conservative"
            elif any(word in question.lower() for word in ['agresif', 'aggressive', 'risk']):
                risk_tolerance = "aggressive"
            
            print(f"📊 Analysis Parameters:")
            print(f"   Risk Tolerance: {risk_tolerance}")
            print(f"   Investment Amount: {investment_amount:,.0f} TL")
            
            # Veritabanı analizi (önceki kodla aynı)
            analysis_results = []
            test_funds = self.active_funds[:10]
            
            print(f"\n🔍 Analyzing {len(test_funds)} funds...")
            
            for i, fcode in enumerate(test_funds):
                try:
                    print(f"   [{i+1}/{len(test_funds)}] {fcode}...", end='')
                    
                    data = self.coordinator.db.get_fund_price_history(fcode, 60)
                    
                    if len(data) >= 20:
                        prices = data.set_index('pdate')['price'].sort_index()
                        returns = prices.pct_change().dropna()
                        
                        # Basit metrikler
                        total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                        annual_return = total_return * (252 / len(prices))
                        volatility = returns.std() * np.sqrt(252) * 100
                        sharpe = (annual_return - 15) / volatility if volatility > 0 else 0
                        win_rate = (returns > 0).sum() / len(returns) * 100
                        
                        # 2025 skorunu hesapla
                        score = self.calculate_2025_score(annual_return, volatility, sharpe, win_rate, risk_tolerance)
                        
                        analysis_results.append({
                            'fund_code': fcode,
                            'annual_return': annual_return,
                            'volatility': volatility,
                            'sharpe_ratio': sharpe,
                            'win_rate': win_rate,
                            'score_2025': score,
                            'current_price': prices.iloc[-1]
                        })
                        
                        print(f" ✅ (Score: {score:.1f})")
                    else:
                        print(" ❌")
                        
                except Exception as e:
                    print(f" ❌")
                    continue
            
            if not analysis_results:
                return "❌ Analiz için yeterli veri bulunamadı."
            
            # Sonuçları sırala
            df = pd.DataFrame(analysis_results)
            df = df.sort_values('score_2025', ascending=False)
            
            # Raporu oluştur
            response = f"\n🎯 2025 YIL SONU FON ÖNERİSİ RAPORU (DUAL AI)\n"
            response += f"{'='*55}\n\n"
            
            response += f"📊 ANALİZ PARAMETRELERİ:\n"
            response += f"   • Risk Toleransı: {risk_tolerance.upper()}\n"
            response += f"   • Yatırım Tutarı: {investment_amount:,.0f} TL\n"
            response += f"   • Analiz Edilen Fon: {len(df)}\n\n"
            
            # VERİTABANI ANALİZİ SONUÇLARI
            response += f"📈 VERİTABANI ANALİZİ - EN İYİ 5 FON:\n"
            top_5 = df.head(5)
            
            for i, (_, fund) in enumerate(top_5.iterrows(), 1):
                response += f"\n{i}. {fund['fund_code']} (2025 Skoru: {fund['score_2025']:.1f}/100)\n"
                response += f"   📊 Beklenen Yıllık Getiri: %{fund['annual_return']:.1f}\n"
                response += f"   📉 Risk (Volatilite): %{fund['volatility']:.1f}\n"
                response += f"   ⚡ Sharpe Oranı: {fund['sharpe_ratio']:.3f}\n"
                response += f"   🎯 Kazanma Oranı: %{fund['win_rate']:.1f}\n"
                response += f"   💰 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
            
            # PORTFÖY ÖNERİSİ
            response += f"\n💼 2025 PORTFÖY ÖNERİSİ ({investment_amount:,.0f} TL):\n"
            
            if len(top_5) >= 3:
                # Risk toleransına göre ağırlık dağılımı
                if risk_tolerance == "conservative":
                    weights = [0.4, 0.3, 0.2, 0.1, 0.0][:len(top_5)]
                elif risk_tolerance == "aggressive":
                    weights = [0.35, 0.25, 0.2, 0.15, 0.05][:len(top_5)]
                else:  # moderate
                    weights = [0.35, 0.25, 0.2, 0.15, 0.05][:len(top_5)]
                
                # Normalize weights
                weights = weights[:len(top_5)]
                weights = [w/sum(weights) for w in weights]
                
                portfolio_return = 0
                
                for i, ((_, fund), weight) in enumerate(zip(top_5.iterrows(), weights)):
                    amount = investment_amount * weight
                    portfolio_return += fund['annual_return'] * weight
                    
                    response += f"   {fund['fund_code']}: %{weight*100:.0f} ({amount:,.0f} TL)\n"
                    response += f"      Beklenen Katkı: %{fund['annual_return']*weight:.1f}\n"
                
                response += f"\n📊 PORTFÖY BEKLENTİLERİ:\n"
                response += f"   📈 Beklenen Yıllık Getiri: %{portfolio_return:.1f}\n"
            
            # ÇİFT AI ANALİZİ - HER İKİSİNİ DE ÇALIŞTIR
            response += f"\n🤖 ÇİFT AI YORUMLARI:\n"
            response += f"{'='*25}\n"
            fund_descriptions = []
            for fund_code in top_5.head(3)['fund_code']:
                details = self.coordinator.db.get_fund_details(fund_code)
                if not details:
                    details = {}
                name = details.get('fund_name', '')
                category = details.get('fund_category', '')
                fund_type = details.get('fund_type', '')
                description = details.get('description', '')
                summary = f"{fund_code}: {name} - {category} - {fund_type}. {description}"
                fund_descriptions.append(summary)

            # AI prompt hazırla
            ai_prompt = f"""
            2025 yılı için TEFAS fon analizi sonuçları:
            
            En iyi 3 fon: {chr(10).join(fund_descriptions)}

            Ortalama beklenen getiri: %{top_5.head(3)['annual_return'].mean():.1f}
            Risk toleransı: {risk_tolerance}
            Yatırım tutarı: {investment_amount:,.0f} TL

            Yukarıdaki bilgilerle bu fonların yatırımcısı için risk/getiri profili ve stratejisi hakkında maksimum 300 kelimeyle değerlendirme ve öneri yap.
            """
            
            response += f"\n🤖 AI YORUM VE ÖNERİLER:\n"
            response += f"{'='*25}\n"

            if hasattr(self.coordinator, 'ai_provider') and self.coordinator.ai_provider.is_available():
                print("🤖 AI analizi yapılıyor...")
                try:
                    ai_response = self.coordinator.ai_provider.query(
                        ai_prompt,
                        "Sen TEFAS uzmanı bir finansal analistsin."
                    )
                    response += f"\n{ai_response}\n"
                except Exception as e:
                    response += f"\n❌ AI analizi alınamadı: {str(e)[:100]}\n"
            else:
                response += f"\n⚠️ AI sistemi şu anda kullanılamıyor.\n"
            
            # AI Karşılaştırma Özeti
            # if self.ai_status['openai'] and self.ai_status['ollama']:
            #     response += f"\n🎯 AI KARŞILAŞTIRMASI:\n"
            #     response += f"   Her iki AI de analiz tamamlandı. Yukarıdaki yorumları karşılaştırabilirsiniz.\n"
            #     response += f"   OpenAI genellikle daha detaylı, Ollama daha özlü yorumlar yapar.\n"
            
            # RİSK UYARILARI
            response += f"\n⚠️ 2025 RİSK UYARILARI:\n"
            response += f"   • Geçmiş performans gelecek getiriyi garanti etmez\n"
            response += f"   • Türkiye ekonomik göstergelerini takip edin\n"
            response += f"   • Portföyü çeyrek yıllık gözden geçirin\n"
            response += f"   • AI öneriler bilgilendirme amaçlıdır, yatırım tavsiyesi değildir\n"
            
            response += f"\n✅ Dual AI analizi tamamlandı: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            
            return response
    
    def handle_comparison_question(self, question):
        """Fon karşılaştırması (önceki kodla aynı)"""
        words = question.upper().split()
        fund_codes = []
        
        for word in words:
            if len(word) == 3 and word.isalpha():
                if word in self.active_funds:
                    fund_codes.append(word)
        
        if len(fund_codes) < 2:
            return f"❌ Karşılaştırma için en az 2 fon kodu gerekli. Örnek: 'AKB ve YAS karşılaştır'"
        
        try:
            comparison_data = []
            
            for fcode in fund_codes:
                data = self.coordinator.db.get_fund_price_history(fcode, 30)
                if not data.empty:
                    prices = data['price']
                    return_30d = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                    
                    comparison_data.append({
                        'fund': fcode,
                        'return_30d': return_30d,
                        'current_price': prices.iloc[-1]
                    })
            
            if not comparison_data:
                return "❌ Karşılaştırma için veri bulunamadı"
            
            response = f"\n⚖️ FON KARŞILAŞTIRMASI\n"
            response += f"{'='*22}\n\n"
            
            for fund_data in comparison_data:
                response += f"📊 {fund_data['fund']}:\n"
                response += f"   30 Gün Getiri: %{fund_data['return_30d']:.2f}\n"
                response += f"   Güncel Fiyat: {fund_data['current_price']:.4f} TL\n\n"
            
            # Kazanan
            best = max(comparison_data, key=lambda x: x['return_30d'])
            response += f"🏆 En İyi Performans: {best['fund']} (%{best['return_30d']:.2f})\n"
            
            return response
            
        except Exception as e:
            return f"❌ Karşılaştırma hatası: {e}"
    
    def handle_top_gainers(self, question, count=10):
        """En çok kazandıran fonların listesi"""
        print(f"[PERF] handle_top_gainers called with question='{question}', count={count}")
        
        # Zaman periyodunu belirle
        if 'son 1 ay' in question.lower() or '1 ay' in question.lower():
            days = 30
            period_name = "1 AY"
        elif 'son 3 ay' in question.lower():
            days = 90
            period_name = "3 AY"
        elif 'son 6 ay' in question.lower():
            days = 180
            period_name = "6 AY"
        else:
            days = 30
            period_name = "30 GÜN"
        
        top_gainers = []
        
        for fcode in self.active_funds[:50]:  # İlk 50 fonu kontrol et
            try:
                data = self.coordinator.db.get_fund_price_history(fcode, days)
                
                if len(data) >= 10:
                    prices = data['price']
                    total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                    
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                    
                    top_gainers.append({
                        'fcode': fcode,
                        'total_return': total_return,
                        'current_price': prices.iloc[-1],
                        'fund_name': fund_name
                    })
                    
            except Exception:
                continue
        
        # Getiriye göre sırala
        top_gainers.sort(key=lambda x: x['total_return'], reverse=True)
        
        if top_gainers:
            response = f"\n📈 SON {period_name} EN ÇOK KAZANDIRAN {count} FON\n"
            response += f"{'='*50}\n\n"
            
            for i, fund in enumerate(top_gainers[:count], 1):
                response += f"{i:2d}. {fund['fcode']}\n"
                response += f"    📊 {period_name} Getiri: %{fund['total_return']:.2f}\n"
                response += f"    💰 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
                if fund['fund_name'] != 'N/A':
                    response += f"    📝 Adı: {fund['fund_name'][:45]}...\n"
                response += f"\n"
            
            return response
        else:
            return f"❌ {period_name} getiri analizi yapılamadı."
    
    def handle_safest_funds_sql_fast(self, count=10):
        """SQL tabanlı süper hızlı güvenli fonlar - Kullanıcı sayısına göre"""
        print(f"🛡️ SQL ile en güvenli {count} fon analizi...")
        
        try:
            # SQL için biraz fazla çek
            sql_limit = count * 2
            
            query = f"""
                    SELECT 
                        fcode,
                        annual_volatility as volatility,
                        annual_return as avg_return,
                        trading_days as data_points,
                        current_price
                    FROM mv_fund_performance_metrics
                    WHERE annual_volatility > 0
                    ORDER BY annual_volatility ASC
                    LIMIT {sql_limit}
                    """
            
            result = self.coordinator.db.execute_query(query)
            
            if result.empty:
                return "❌ SQL analizi sonuç vermedi."
            
            # Kullanıcının istediği sayıda al
            top_results = result.head(count)
            
            print(f"   ⚡ SQL ile {len(result)} fon analiz edildi, {len(top_results)} gösteriliyor")
            
            # Fund details al (sadece gösterilecek fonlar için)
            fund_details = {}
            for _, row in top_results.iterrows():
                fcode = row['fcode']
                try:
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_details[fcode] = {
                        'name': details.get('fund_name', 'N/A') if details else 'N/A',
                        'type': details.get('fund_type', 'N/A') if details else 'N/A'
                    }
                except:
                    fund_details[fcode] = {'name': 'N/A', 'type': 'N/A'}
            
            # Sonuçları formatla
            response = f"\n🛡️ EN GÜVENLİ {count} FON (SQL Hızlı Analiz)\n"
            response += f"{'='*45}\n\n"
            response += f"📊 ANALİZ SONUCU:\n"
            response += f"   • İstenen Fon: {count}\n"
            response += f"   • SQL Analizi: {len(result)} fon\n"
            response += f"   • En Düşük Volatilite: %{top_results.iloc[0]['volatility']:.2f}\n\n"
            
            for i, (_, row) in enumerate(top_results.iterrows(), 1):
                fcode = row['fcode']
                volatility = float(row['volatility'])
                avg_return = float(row['avg_return']) * 100
                data_points = int(row['data_points'])
                
                # Risk kategorisi
                if volatility < 1:
                    risk = "🟢 ÇOK GÜVENLİ"
                elif volatility < 2:
                    risk = "🟡 GÜVENLİ"
                elif volatility < 4:
                    risk = "🟠 ORTA"
                else:
                    risk = "🔴 RİSKLİ"
                
                response += f"{i:2d}. {fcode} - {risk}\n"
                response += f"    📉 Volatilite: %{volatility:.2f}\n"
                response += f"    📊 Ortalama Getiri: %{avg_return:+.3f}\n"
                response += f"    📈 Veri Noktası: {data_points}\n"
                response += f"    🏷️ Tür: {fund_details[fcode]['type']}\n"
                if fund_details[fcode]['name'] != 'N/A':
                    response += f"    📝 Adı: {fund_details[fcode]['name'][:35]}...\n"
                response += f"\n"
            
            # İstatistikler
            avg_vol = top_results['volatility'].mean()
            avg_ret = top_results['avg_return'].mean() * 100
            
            response += f"📊 {count} FON ÖZET İSTATİSTİKLER:\n"
            response += f"   Ortalama Volatilite: %{avg_vol:.2f}\n"
            response += f"   Ortalama Getiri: %{avg_ret:+.2f}\n"
            response += f"   En Güvenli: {top_results.iloc[0]['fcode']}\n"
            
            return response
            
        except Exception as e:
            print(f"   ❌ SQL analizi hatası: {e}")
            # Fallback: Hızlı Python versiyonu
            return self.handle_safest_funds_list_fallback(count)
    
    def handle_safest_fund(self, days=60):
        """En güvenli (en düşük volatilite) fonu bulur"""
        min_risk_fund = None
        min_vol = 1e9
        for fcode in self.active_funds:
            data = self.coordinator.db.get_fund_price_history(fcode, days)
            if not data.empty:
                returns = data['price'].pct_change().dropna()
                volatility = returns.std() * 100
                if volatility < min_vol:
                    min_vol = volatility
                    min_risk_fund = fcode
        if min_risk_fund:
            return f"🛡️ Son {days} günde volatilitesi en düşük fon: **{min_risk_fund}**\nRisk (Volatilite): %{min_vol:.2f}"
        else:
            return "En güvenli fon tespit edilemedi."
    
    def handle_riskiest_funds_list(self, count=10, days=60):
        """En riskli fonların listesi (yüksek volatilite)"""
        print(f"📈 En riskli {count} fon analiz ediliyor...")
        
        risky_funds = []
        
        for fcode in self.active_funds[:50]:
            try:
                data = self.coordinator.db.get_fund_price_history(fcode, days)
                
                if len(data) >= 20:
                    prices = data.set_index('pdate')['price'].sort_index()
                    returns = prices.pct_change().dropna()
                    
                    volatility = returns.std() * 100
                    total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                    
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                    
                    risky_funds.append({
                        'fcode': fcode,
                        'volatility': volatility,
                        'total_return': total_return,
                        'current_price': prices.iloc[-1],
                        'fund_name': fund_name
                    })
                    
            except Exception:
                continue
        
        # Volatiliteye göre sırala (en yüksek = en riskli)
        risky_funds.sort(key=lambda x: x['volatility'], reverse=True)
        
        if risky_funds:
            response = f"\n📈 EN RİSKLİ {count} FON (Yüksek Volatilite)\n"
            response += f"{'='*45}\n\n"
            
            for i, fund in enumerate(risky_funds[:count], 1):
                response += f"{i:2d}. {fund['fcode']}\n"
                response += f"    📈 Risk (Volatilite): %{fund['volatility']:.2f}\n"
                response += f"    📊 Getiri: %{fund['total_return']:+.2f}\n"
                response += f"    💲 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
                if fund['fund_name'] != 'N/A':
                    response += f"    📝 Adı: {fund['fund_name'][:45]}...\n"
                response += f"\n"
            
            return response
        else:
            return f"❌ Riskli fon analizi yapılamadı."
    
    def handle_most_risky_fund(self, days=60):
        """En riskli (volatilitesi en yüksek) fonu bulur"""
        max_risk_fund = None
        max_vol = -1
        for fcode in self.active_funds:
            data = self.coordinator.db.get_fund_price_history(fcode, days)
            if not data.empty:
                returns = data['price'].pct_change().dropna()
                volatility = returns.std() * 100
                if volatility > max_vol:
                    max_vol = volatility
                    max_risk_fund = fcode
        if max_risk_fund:
            return f"📈 Son {days} günde volatilitesi en yüksek fon: **{max_risk_fund}**\nRisk (Volatilite): %{max_vol:.2f}"
        else:
            return "En riskli fon tespit edilemedi."
    
    def handle_worst_funds_list(self, count=10, days=60):
        """En çok kaybettiren fonların listesi"""
        print(f"🔻 En çok kaybettiren {count} fon analiz ediliyor...")
        
        worst_funds = []
        
        for fcode in self.active_funds[:50]:
            try:
                data = self.coordinator.db.get_fund_price_history(fcode, days)
                
                if len(data) >= 10:
                    prices = data['price']
                    total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                    
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                    
                    worst_funds.append({
                        'fcode': fcode,
                        'total_return': total_return,
                        'current_price': prices.iloc[-1],
                        'fund_name': fund_name
                    })
                    
            except Exception:
                continue
        
        # Getiriye göre sırala (en düşük = en kötü)
        worst_funds.sort(key=lambda x: x['total_return'])
        
        if worst_funds:
            response = f"\n🔻 EN ÇOK KAYBETTİREN {count} FON (Son {days} Gün)\n"
            response += f"{'='*55}\n\n"
            
            for i, fund in enumerate(worst_funds[:count], 1):
                response += f"{i:2d}. {fund['fcode']}\n"
                response += f"    📉 Kayıp: %{fund['total_return']:.2f}\n"
                response += f"    💲 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
                if fund['fund_name'] != 'N/A':
                    response += f"    📝 Adı: {fund['fund_name'][:45]}...\n"
                response += f"\n"
            
            return response
        else:
            return f"❌ Kayıp analizi yapılamadı."
    
    def handle_worst_fund(self, days=60):
        """En çok kaybettiren fonu bulur"""
        min_return_fund = None
        min_return = 1e9
        for fcode in self.active_funds:
            data = self.coordinator.db.get_fund_price_history(fcode, days)
            if not data.empty:
                prices = data['price']
                ret = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                if ret < min_return:
                    min_return = ret
                    min_return_fund = fcode
        if min_return_fund:
            return f"🔻 Son {days} günde en çok kaybettiren fon: **{min_return_fund}**\nGetiri: %{min_return:.2f}"
        else:
            return "En çok kaybettiren fon tespit edilemedi."    

    def calculate_2025_score(self, annual_return, volatility, sharpe, win_rate, risk_tolerance):
        """2025 için özel skorlama"""
        score = 0
        
        # Getiri skoru (0-30)
        return_score = min(max(annual_return, 0) / 30 * 30, 30)
        score += return_score
        
        # Sharpe skoru (0-25)
        sharpe_score = min(max(sharpe, 0) * 10, 25)
        score += sharpe_score
        
        # Risk skoru (0-25)
        if risk_tolerance == "conservative":
            risk_score = max(25 - volatility, 0)
        elif risk_tolerance == "aggressive":
            risk_score = min(volatility / 2, 25)
        else:  # moderate
            risk_score = max(20 - abs(volatility - 20) / 2, 0)
        score += risk_score
        
        # Konsistans skoru (0-20)
        consistency_score = win_rate / 5
        score += consistency_score
        
        return max(min(score, 100), 0)

    def handle_safest_funds_list_fallback(self, count=10):
        """Fallback: Hızlı Python versiyonu"""
        print(f"🛡️ Python fallback: En güvenli {count} fon...")
        
        safe_funds = []
        start_time = time.time()
        
        for fcode in self.active_funds:  # 50 fon
            try:
                # Kısa veri çek (20 gün)
                data = self.coordinator.db.get_fund_price_history(fcode, 20)
                
                if len(data) >= 10:
                    prices = data.set_index('pdate')['price'].sort_index()
                    returns = prices.pct_change().dropna()
                    
                    volatility = returns.std() * 100
                    total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                    
                    safe_funds.append({
                        'fcode': fcode,
                        'volatility': volatility,
                        'total_return': total_return,
                        'current_price': prices.iloc[-1]
                    })
                    
            except Exception:
                continue
        
        elapsed = time.time() - start_time
        print(f"   ✅ {len(safe_funds)} fon analiz edildi ({elapsed:.1f} saniye)")
        
        if not safe_funds:
            return "❌ Analiz edilebilir güvenli fon bulunamadı."
        
        # Volatiliteye göre sırala
        safe_funds.sort(key=lambda x: x['volatility'])
        top_funds = safe_funds[:count]
        
        # Fund details al
        for fund in top_funds:
            try:
                details = self.coordinator.db.get_fund_details(fund['fcode'])
                fund['fund_name'] = details.get('fund_name', 'N/A') if details else 'N/A'
                fund['fund_type'] = details.get('fund_type', 'N/A') if details else 'N/A'
            except:
                fund['fund_name'] = 'N/A'
                fund['fund_type'] = 'N/A'
        
        # Response oluştur
        response = f"\n🛡️ EN GÜVENLİ {count} FON (Python Fallback)\n"
        response += f"{'='*45}\n\n"
        response += f"📊 ANALİZ SONUCU:\n"
        response += f"   • Analiz Süresi: {elapsed:.1f} saniye\n"
        response += f"   • En Düşük Volatilite: %{top_funds[0]['volatility']:.2f}\n\n"
        
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
        
        return response

    @staticmethod
    def get_examples():
        """Bu handler'ın işleyebileceği örnek sorular"""
        return [
            "En güvenli 5 fon hangileri?",
            "En güvenli 10 fon",
            "En çok kazanan fonlar",
            "Son 30 gün en iyi performans gösteren fonlar",
            "En riskli fonlar hangileri?",
            "2025 için hangi fonları önerirsin?",
            "AKB fonunu analiz et",
            "En çok kaybettiren fonlar",
            "Son 1 ayda en çok kazandıran fonlar",
            "Sharpe oranı en yüksek fonlar",
            "Volatilitesi düşük fonlar",
            "TYH fonunu analiz et",
            "2025 yılı için 100000 TL ile önerilerin nedir?"
        ]
    
    @staticmethod
    def get_keywords():
        """Bu handler için anahtar kelimeler"""
        return [
            "güvenli", "riskli", "kazanan", "kaybettiren", "performans",
            "getiri", "analiz", "öneri", "2025", "en iyi", "en kötü",
            "volatilite", "sharpe", "kazandıran", "kaybeden", "düşen",
            "yükselen", "artış", "düşüş", "değerlendirme"
        ]
    
    @staticmethod
    def get_patterns():
        """Gelişmiş pattern tanımları"""
        return [
            {
                'type': 'regex',
                'pattern': r'en\s+(güvenli|riskli)\s+\d*\s*fon',
                'score': 0.95
            },
            {
                'type': 'regex',
                'pattern': r'en\s+(iyi|kötü|çok)\s+(kazandıran|kaybettiren)\s*fon',
                'score': 0.95
            },
            {
                'type': 'regex',
                'pattern': r'son\s+\d+\s*(gün|ay|hafta).*?(performans|getiri|kazandıran)',
                'score': 0.90  # Time_based ile çakışmasın diye score düşük
            },
            {
                'type': 'regex',
                'pattern': r'\b[A-Z]{3}\b\s+(fonu?n?u?|analiz)',
                'score': 0.90
            },
            {
                'type': 'contains_all',
                'words': ['performans', 'analiz'],
                'score': 0.85
            },
            {
                'type': 'contains_all',
                'words': ['2025', 'öneri'],
                'score': 0.95
            }
        ]

    @staticmethod
    def get_method_patterns():
        """Method seçimi için pattern'ler - GÜNCELLEME"""
        return {
            'handle_safest_funds_sql_fast': ['güvenli', 'en az riskli', 'düşük risk', 'güvenli fon'],
            'handle_top_gainers': ['kazandıran', 'en iyi performans', 'getiri', 'yükselen', 'son.*gün.*performans'],
            'handle_worst_funds_list': ['kaybettiren', 'en çok kaybeden', 'düşen', 'kayıp'],
            'handle_riskiest_funds_list': ['riskli', 'en riskli', 'yüksek risk', 'volatil'],
            'handle_2025_recommendation_dual': ['2025', 'öneri', 'tavsiye', 'yıl sonu'],
            'handle_analysis_question_dual': ['analiz et', 'incele', 'değerlendir', 'fonu analiz'],
            'handle_top_sharpe_funds_question': ['sharpe', 'sharpe oranı'],
            'handle_low_volatility_funds_question': ['volatilite', 'düşük volatilite'],
            'handle_fund_past_performance_question': ['geçmiş performans', 'son 1 yıl', 'yıllık getiri']
        }