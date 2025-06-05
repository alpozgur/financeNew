from datetime import datetime
import time
import pandas as pd
import numpy as np
from risk_assessment import RiskAssessment

class PerformanceAnalyzerMain:
    def __init__(self, coordinator, active_funds, ai_status):
        self.coordinator = coordinator
        self.active_funds = active_funds
        self.ai_status = ai_status
    
    def _check_fund_risk(self, fcode):
        """
        Fon için risk kontrolü yap
        
        Returns:
            tuple: (is_safe, risk_assessment, risk_warning)
        """
        try:
            mv_query = f"""
            SELECT 
                fcode,
                current_price,
                price_vs_sma20,
                rsi_14,
                stochastic_14,
                days_since_last_trade,
                investorcount
            FROM mv_fund_technical_indicators 
            WHERE fcode = '{fcode}'
            """
            
            mv_data = self.coordinator.db.execute_query(mv_query)
            
            if mv_data.empty:
                return True, None, ""  # Veri yoksa güvenli say
            
            row = mv_data.iloc[0]
            
            risk_data = {
                'fcode': fcode,
                'price_vs_sma20': float(row['price_vs_sma20']) if pd.notna(row['price_vs_sma20']) else 0,
                'rsi_14': float(row['rsi_14']) if pd.notna(row['rsi_14']) else 50,
                'stochastic_14': float(row['stochastic_14']) if pd.notna(row['stochastic_14']) else 50,
                'days_since_last_trade': int(row['days_since_last_trade']) if pd.notna(row['days_since_last_trade']) else 0,
                'investorcount': int(row['investorcount']) if pd.notna(row['investorcount']) else 0
            }
            
            risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
            risk_warning = RiskAssessment.format_risk_warning(risk_assessment)
            
            # EXTREME risk fonları güvenli değil
            is_safe = risk_assessment['risk_level'] not in ['EXTREME']
            
            return is_safe, risk_assessment, risk_warning
            
        except Exception as e:
            print(f"Risk kontrolü hatası ({fcode}): {e}")
            return True, None, ""  # Hata durumunda güvenli say

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
        """Tek fon analizi - Risk kontrolü ile"""
        words = question.upper().split()
        fund_code = None

        for word in words:
            if len(word) == 3 and word.isalpha():
                if word.upper() in [x.upper() for x in self.active_funds]:
                    fund_code = word.upper()
                    break
        
        if fund_code:
            # ✅ RİSK KONTROLÜ
            is_safe, risk_assessment, risk_warning = self._check_fund_risk(fund_code)
            
            # Extreme risk durumunda özel yanıt
            if not is_safe and risk_assessment and risk_assessment['risk_level'] == 'EXTREME':
                response = f"\n⛔ {fund_code} FONU RİSK UYARISI\n"
                response += f"{'='*40}\n"
                response += risk_warning
                response += f"\n\n📊 Temel veriler için veritabanı sonuçlarına bakın.\n"
                response += f"❌ Bu fon için AI analizi önerilmiyor.\n"
                return response
        
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

            # ✅ RİSK DURUMU RAPORU
            if risk_assessment:
                response += f"🛡️ RİSK DEĞERLENDİRMESİ:\n"
                response += f"   Risk Seviyesi: {risk_assessment['risk_level']}\n"
                response += f"   Genel Değerlendirme: {'✅ Güvenli' if is_safe else '⚠️ Riskli'}\n"
                if risk_assessment['risk_factors']:
                    response += f"   Risk Faktörleri: {len(risk_assessment['risk_factors'])} adet\n"
                response += f"\n"

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
            Risk Seviyesi: {risk_assessment['risk_level'] if risk_assessment else 'Bilinmiyor'}

            Yukarıdaki fon bilgileriyle, bu fonun risk ve getiri profilini, avantaj/dezavantajlarını ve hangi yatırımcıya uygun olabileceğini 150 kelimeyi aşmadan açıklayıp özetle.
            """

            response += f"🤖 AI DEĞERLENDİRMESİ:\n"
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

            # ✅ Risk uyarısını en sona ekle
            if risk_warning and risk_assessment and risk_assessment['risk_level'] in ['HIGH', 'MEDIUM']:
                response += f"\n{risk_warning}"

            response += f"\n✅ Analiz tamamlandı: {datetime.now().strftime('%H:%M:%S')}\n"

            return response

        except Exception as e:
            return f"❌ Analiz hatası: {e}"
    
    def handle_2025_recommendation_dual(self, question):
        """2025 fon önerisi - Risk kontrolü ile"""
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
        
        # ✅ Risk kontrollü analiz
        analysis_results = []
        test_funds = self.active_funds[:20]  # Biraz daha fazla test et
        safe_funds = []
        risky_funds = []
        
        print(f"\n🔍 Analyzing {len(test_funds)} funds with risk control...")
        
        for i, fcode in enumerate(test_funds):
            try:
                print(f"   [{i+1}/{len(test_funds)}] {fcode}...", end='')
                
                # ✅ Önce risk kontrolü
                is_safe, risk_assessment, risk_warning = self._check_fund_risk(fcode)
                
                if not is_safe:
                    risky_funds.append((fcode, risk_assessment['risk_level'] if risk_assessment else 'UNKNOWN'))
                    print(" ❌ RISKY")
                    continue
                
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
                        'current_price': prices.iloc[-1],
                        'risk_level': risk_assessment['risk_level'] if risk_assessment else 'LOW'
                    })
                    
                    safe_funds.append(fcode)
                    print(f" ✅ (Score: {score:.1f})")
                else:
                    print(" ❌ INSUFFICIENT DATA")
                    
            except Exception as e:
                print(f" ❌ ERROR")
                continue
        
        if not analysis_results:
            return "❌ Risk kontrollü analiz için yeterli güvenli fon bulunamadı."
        
        # Sonuçları sırala
        df = pd.DataFrame(analysis_results)
        df = df.sort_values('score_2025', ascending=False)
        
        # Raporu oluştur
        response = f"\n🎯 2025 YIL SONU RİSK KONTROLLÜ FON ÖNERİSİ\n"
        response += f"{'='*55}\n\n"
        
        response += f"📊 ANALİZ PARAMETRELERİ:\n"
        response += f"   • Risk Toleransı: {risk_tolerance.upper()}\n"
        response += f"   • Yatırım Tutarı: {investment_amount:,.0f} TL\n"
        response += f"   • Analiz Edilen Fon: {len(test_funds)}\n"
        response += f"   • ✅ Güvenli Fonlar: {len(safe_funds)}\n"
        response += f"   • ❌ Riskli Fonlar: {len(risky_funds)}\n\n"
        
        # Riskli fonları göster
        if risky_funds:
            response += f"⚠️ ELENENRİSKLİ FONLAR ({len(risky_funds)} adet):\n"
            for fund_code, risk_level in risky_funds[:5]:
                response += f"   ❌ {fund_code} - {risk_level} RİSK\n"
            if len(risky_funds) > 5:
                response += f"   ... ve {len(risky_funds)-5} fon daha\n"
            response += f"\n"
        
        # VERİTABANI ANALİZİ SONUÇLARI - Sadece güvenli fonlar
        response += f"📈 RİSK KONTROLLÜ EN İYİ 5 FON:\n"
        top_5 = df.head(5)
        
        for i, (_, fund) in enumerate(top_5.iterrows(), 1):
            response += f"\n{i}. {fund['fund_code']} (2025 Skoru: {fund['score_2025']:.1f}/100) ✅\n"
            response += f"   📊 Beklenen Yıllık Getiri: %{fund['annual_return']:.1f}\n"
            response += f"   📉 Risk (Volatilite): %{fund['volatility']:.1f}\n"
            response += f"   ⚡ Sharpe Oranı: {fund['sharpe_ratio']:.3f}\n"
            response += f"   🎯 Kazanma Oranı: %{fund['win_rate']:.1f}\n"
            response += f"   💰 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
            response += f"   🛡️ Risk Seviyesi: {fund['risk_level']}\n"
        
        # PORTFÖY ÖNERİSİ - Sadece güvenli fonlardan
        response += f"\n💼 2025 GÜVENLİ PORTFÖY ÖNERİSİ ({investment_amount:,.0f} TL):\n"
        
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
                
                response += f"   {fund['fund_code']}: %{weight*100:.0f} ({amount:,.0f} TL) ✅\n"
                response += f"      Beklenen Katkı: %{fund['annual_return']*weight:.1f}\n"
                response += f"      Risk Kontrolü: {fund['risk_level']}\n"
            
            response += f"\n📊 GÜVENLİ PORTFÖY BEKLENTİLERİ:\n"
            response += f"   📈 Beklenen Yıllık Getiri: %{portfolio_return:.1f}\n"
            response += f"   🛡️ Tüm fonlar risk kontrolünden geçti\n"
        
        # AI ANALİZİ - Risk kontrollü fonlarla
        response += f"\n🤖 RİSK KONTROLLÜ AI YORUMLARI:\n"
        response += f"{'='*35}\n"
        
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
        2025 yılı için risk kontrolünden geçmiş TEFAS fon analizi:
        
        En iyi 3 güvenli fon: {chr(10).join(fund_descriptions)}

        Ortalama beklenen getiri: %{top_5.head(3)['annual_return'].mean():.1f}
        Risk toleransı: {risk_tolerance}
        Yatırım tutarı: {investment_amount:,.0f} TL
        Güvenli fon sayısı: {len(safe_funds)} / {len(test_funds)}

        Bu risk kontrollü fonların yatırımcısı için güvenlik profili ve stratejisi hakkında maksimum 300 kelimeyle değerlendirme ve öneri yap. Risk kontrolünün önemini vurgula.
        """
        
        if hasattr(self.coordinator, 'ai_provider') and self.coordinator.ai_provider.is_available():
            print("🤖 AI analizi yapılıyor...")
            try:
                ai_response = self.coordinator.ai_provider.query(
                    ai_prompt,
                    "Sen risk odaklı TEFAS uzmanı bir finansal analistsin."
                )
                response += f"\n{ai_response}\n"
            except Exception as e:
                response += f"\n❌ AI analizi alınamadı: {str(e)[:100]}\n"
        else:
            response += f"\n⚠️ AI sistemi şu anda kullanılamıyor.\n"
        
        # GÜVENLİK UYARILARI
        response += f"\n🛡️ 2025 GÜVENLİK UYARILARI:\n"
        response += f"   • Tüm öneriler risk değerlendirmesinden geçirilmiştir\n"
        response += f"   • EXTREME riskli {len(risky_funds)} fon otomatik elenmiştir\n"
        response += f"   • Geçmiş performans gelecek getiriyi garanti etmez\n"
        response += f"   • Portföyü çeyrek yıllık gözden geçirin\n"
        response += f"   • Risk kontrollü öneriler yatırım tavsiyesi değildir\n"
        
        response += f"\n✅ Risk kontrollü analiz tamamlandı: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        
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
        """En çok kazandıran fonların listesi - Risk kontrolü ile"""
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
        risky_gainers = []
        
        for fcode in self.active_funds[:50]:  # İlk 50 fonu kontrol et
            try:
                # ✅ Risk kontrolü
                is_safe, risk_assessment, risk_warning = self._check_fund_risk(fcode)
                
                data = self.coordinator.db.get_fund_price_history(fcode, days)
                
                if len(data) >= 10:
                    prices = data['price']
                    total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                    
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                    
                    gainer_data = {
                        'fcode': fcode,
                        'total_return': total_return,
                        'current_price': prices.iloc[-1],
                        'fund_name': fund_name,
                        'risk_level': risk_assessment['risk_level'] if risk_assessment else 'UNKNOWN'
                    }
                    
                    if is_safe:
                        top_gainers.append(gainer_data)
                    else:
                        risky_gainers.append(gainer_data)
                    
            except Exception:
                continue
        
        # Getiriye göre sırala
        top_gainers.sort(key=lambda x: x['total_return'], reverse=True)
        risky_gainers.sort(key=lambda x: x['total_return'], reverse=True)
        
        if top_gainers:
            response = f"\n📈 SON {period_name} EN ÇOK KAZANDIRAN GÜVENLİ {count} FON\n"
            response += f"{'='*55}\n\n"
            
            response += f"🛡️ RİSK KONTROLÜ SONUCU:\n"
            response += f"   ✅ Güvenli Kazananlar: {len(top_gainers)}\n"
            response += f"   ⚠️ Riskli Kazananlar: {len(risky_gainers)}\n\n"
            
            for i, fund in enumerate(top_gainers[:count], 1):
                response += f"{i:2d}. {fund['fcode']} ✅\n"
                response += f"    📊 {period_name} Getiri: %{fund['total_return']:.2f}\n"
                response += f"    💰 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
                response += f"    🛡️ Risk Seviyesi: {fund['risk_level']}\n"
                if fund['fund_name'] != 'N/A':
                    response += f"    📝 Adı: {fund['fund_name'][:45]}...\n"
                response += f"\n"
            
            # Riskli yüksek kazananları göster (uyarı olarak)
            if risky_gainers:
                response += f"\n⚠️ YÜKSEK KAZANÇ ELDE EDİCİ AMA RİSKLİ FONLAR ({len(risky_gainers)} adet):\n"
                for fund in risky_gainers[:3]:
                    response += f"   ❌ {fund['fcode']} - %{fund['total_return']:.2f} getiri, {fund['risk_level']} RİSK\n"
                response += f"   📋 Bu fonlar yüksek getiri sağlamış ama risk seviyesi yüksek!\n"
            
            return response
        else:
            return f"❌ {period_name} güvenli kazanan fon bulunamadı."
    
    def handle_safest_funds_sql_fast(self, count=10):
        """SQL tabanlı süper hızlı güvenli fonlar - Risk kontrolü ile"""
        print(f"🛡️ SQL ile en güvenli {count} fon analizi...")
        
        try:
            # SQL için biraz fazla çek
            sql_limit = count * 3  # Risk kontrolü sonrası elenmeler olacak
            
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
            
            # ✅ Risk kontrolü uygula
            safe_results = []
            risky_results = []
            
            print(f"   🔍 {len(result)} fon risk kontrolünden geçiriliyor...")
            
            for _, row in result.iterrows():
                fcode = row['fcode']
                is_safe, risk_assessment, risk_warning = self._check_fund_risk(fcode)
                
                row_dict = row.to_dict()
                row_dict['risk_level'] = risk_assessment['risk_level'] if risk_assessment else 'UNKNOWN'
                
                if is_safe:
                    safe_results.append(row_dict)
                else:
                    risky_results.append(row_dict)
            
            print(f"   ✅ Güvenli: {len(safe_results)}, Riskli: {len(risky_results)}")
            
            if len(safe_results) < count:
                print(f"   ⚠️ İstenen {count} fon bulunamadı, {len(safe_results)} güvenli fon bulundu")
            
            # Kullanıcının istediği sayıda güvenli fon al
            top_safe_results = safe_results[:count]
            
            # Fund details al (sadece gösterilecek fonlar için)
            fund_details = {}
            for row_dict in top_safe_results:
                fcode = row_dict['fcode']
                try:
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_details[fcode] = {
                        'name': details.get('fund_name', 'N/A') if details else 'N/A',
                        'type': details.get('fund_type', 'N/A') if details else 'N/A'
                    }
                except:
                    fund_details[fcode] = {'name': 'N/A', 'type': 'N/A'}
            
            # Sonuçları formatla
            response = f"\n🛡️ RİSK KONTROLLÜ EN GÜVENLİ {len(top_safe_results)} FON\n"
            response += f"{'='*50}\n\n"
            response += f"📊 ANALİZ SONUCU:\n"
            response += f"   • İstenen Fon: {count}\n"
            response += f"   • SQL Analizi: {len(result)} fon\n"
            response += f"   • ✅ Risk Kontrolü Geçen: {len(safe_results)}\n"
            response += f"   • ❌ Riskli Bulunan: {len(risky_results)}\n"
            if top_safe_results:
                response += f"   • En Düşük Volatilite: %{top_safe_results[0]['volatility']:.2f}\n\n"
            
            for i, row_dict in enumerate(top_safe_results, 1):
                fcode = row_dict['fcode']
                volatility = float(row_dict['volatility'])
                avg_return = float(row_dict['avg_return']) * 100
                data_points = int(row_dict['data_points'])
                risk_level = row_dict['risk_level']
                
                # Risk kategorisi
                if volatility < 1:
                    risk = "🟢 ÇOK GÜVENLİ"
                elif volatility < 2:
                    risk = "🟡 GÜVENLİ"
                elif volatility < 4:
                    risk = "🟠 ORTA"
                else:
                    risk = "🔴 RİSKLİ"
                
                response += f"{i:2d}. {fcode} - {risk} ✅\n"
                response += f"    📉 Volatilite: %{volatility:.2f}\n"
                response += f"    📊 Ortalama Getiri: %{avg_return:+.3f}\n"
                response += f"    📈 Veri Noktası: {data_points}\n"
                response += f"    🛡️ Risk Seviyesi: {risk_level}\n"
                response += f"    🏷️ Tür: {fund_details[fcode]['type']}\n"
                if fund_details[fcode]['name'] != 'N/A':
                    response += f"    📝 Adı: {fund_details[fcode]['name'][:35]}...\n"
                response += f"\n"
            
            # Riskli fonları bilgilendirme olarak göster
            if risky_results:
                response += f"⚠️ ELENENRİSKLİ DÜŞÜK VOLATİLİTE FONLARI ({len(risky_results)} adet):\n"
                for row_dict in risky_results[:3]:
                    response += f"   ❌ {row_dict['fcode']} - {row_dict['risk_level']} RİSK\n"
                if len(risky_results) > 3:
                    response += f"   ... ve {len(risky_results)-3} fon daha\n"
                response += f"\n"
            
            # İstatistikler - sadece güvenli fonlar
            if top_safe_results:
                avg_vol = sum(row['volatility'] for row in top_safe_results) / len(top_safe_results)
                avg_ret = sum(row['avg_return'] for row in top_safe_results) / len(top_safe_results) * 100
                
                response += f"📊 GÜVENLİ {len(top_safe_results)} FON ÖZET İSTATİSTİKLER:\n"
                response += f"   Ortalama Volatilite: %{avg_vol:.2f}\n"
                response += f"   Ortalama Getiri: %{avg_ret:+.2f}\n"
                response += f"   En Güvenli: {top_safe_results[0]['fcode']}\n"
                response += f"   Risk Kontrolü: ✅ Tamamlandı\n"
            
            return response
            
        except Exception as e:
            print(f"   ❌ SQL analizi hatası: {e}")
            # Fallback: Hızlı Python versiyonu
            return self.handle_safest_funds_list_fallback(count)
    
    def handle_safest_fund(self, days=60):
        """En güvenli (en düşük volatilite) fonu bulur - Risk kontrolü ile"""
        min_risk_fund = None
        min_vol = 1e9
        safe_funds = []
        risky_funds = []
        
        for fcode in self.active_funds[:30]:  # İlk 30 fonu kontrol et
            try:
                # ✅ Risk kontrolü
                is_safe, risk_assessment, risk_warning = self._check_fund_risk(fcode)
                
                data = self.coordinator.db.get_fund_price_history(fcode, days)
                if not data.empty:
                    returns = data['price'].pct_change().dropna()
                    volatility = returns.std() * 100
                    
                    fund_info = {
                        'fcode': fcode,
                        'volatility': volatility,
                        'risk_level': risk_assessment['risk_level'] if risk_assessment else 'UNKNOWN'
                    }
                    
                    if is_safe:
                        safe_funds.append(fund_info)
                        if volatility < min_vol:
                            min_vol = volatility
                            min_risk_fund = fcode
                    else:
                        risky_funds.append(fund_info)
            except:
                continue
        
        if min_risk_fund:
            response = f"🛡️ SON {days} GÜNDE EN GÜVENLİ FON (Risk Kontrollü)\n"
            response += f"{'='*50}\n\n"
            response += f"✅ En Güvenli Fon: **{min_risk_fund}**\n"
            response += f"📉 Risk (Volatilite): %{min_vol:.2f}\n"
            response += f"🛡️ Risk Kontrolü: Onaylandı\n\n"
            
            response += f"📊 KONTROL EDİLEN FONLAR:\n"
            response += f"   ✅ Güvenli Fonlar: {len(safe_funds)}\n"
            response += f"   ❌ Riskli Fonlar: {len(risky_funds)}\n"
            
            if risky_funds:
                response += f"\n⚠️ ELENENRİSKLİ FONLAR:\n"
                for fund in risky_funds[:3]:
                    response += f"   ❌ {fund['fcode']} - {fund['risk_level']} RİSK\n"
            
            return response
        else:
            return f"❌ Son {days} günde güvenli fon tespit edilemedi."
    
    def handle_riskiest_funds_list(self, count=10, days=60):
        """En riskli fonların listesi (yüksek volatilite) - Risk seviyesi ile"""
        print(f"📈 En riskli {count} fon analiz ediliyor...")
        
        risky_funds = []
        
        for fcode in self.active_funds[:50]:
            try:
                # Risk kontrolü
                is_safe, risk_assessment, risk_warning = self._check_fund_risk(fcode)
                
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
                        'fund_name': fund_name,
                        'risk_level': risk_assessment['risk_level'] if risk_assessment else 'UNKNOWN',
                        'is_extreme_risk': not is_safe and risk_assessment and risk_assessment['risk_level'] == 'EXTREME'
                    })
                    
            except Exception:
                continue
        
        # Volatiliteye göre sırala (en yüksek = en riskli)
        risky_funds.sort(key=lambda x: x['volatility'], reverse=True)
        
        if risky_funds:
            response = f"\n📈 EN RİSKLİ {count} FON (Yüksek Volatilite)\n"
            response += f"{'='*45}\n\n"
            
            # EXTREME risk fonları ayrı göster
            extreme_risk_funds = [f for f in risky_funds if f['is_extreme_risk']]
            if extreme_risk_funds:
                response += f"⛔ EXTREME RİSK FONLARI ({len(extreme_risk_funds)} adet):\n"
                for fund in extreme_risk_funds[:3]:
                    response += f"   ⛔ {fund['fcode']} - %{fund['volatility']:.2f} volatilite, {fund['risk_level']} RİSK\n"
                response += f"\n"
            
            response += f"📊 EN YÜKSEK VOLATİLİTE FONLARI:\n\n"
            
            for i, fund in enumerate(risky_funds[:count], 1):
                # Risk ikonları
                if fund['is_extreme_risk']:
                    risk_icon = "⛔"
                elif fund['risk_level'] == 'HIGH':
                    risk_icon = "🔴"
                elif fund['risk_level'] == 'MEDIUM':
                    risk_icon = "🟡"
                else:
                    risk_icon = "🟠"
                
                response += f"{i:2d}. {fund['fcode']} {risk_icon}\n"
                response += f"    📈 Risk (Volatilite): %{fund['volatility']:.2f}\n"
                response += f"    📊 Getiri: %{fund['total_return']:+.2f}\n"
                response += f"    💲 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
                response += f"    🛡️ Risk Seviyesi: {fund['risk_level']}\n"
                if fund['fund_name'] != 'N/A':
                    response += f"    📝 Adı: {fund['fund_name'][:45]}...\n"
                response += f"\n"
            
            # Uyarılar
            response += f"⚠️ RİSK UYARILARI:\n"
            response += f"   • Bu fonlar yüksek volatilite göstermektedir\n"
            response += f"   • EXTREME riskli fonlardan kaçının\n"
            response += f"   • Yatırım öncesi detaylı araştırma yapın\n"
            response += f"   • Risk toleransınızı göz önünde bulundurun\n"
            
            return response
        else:
            return f"❌ Riskli fon analizi yapılamadı."
    
    def handle_most_risky_fund(self, days=60):
        """En riskli (volatilitesi en yüksek) fonu bulur - Risk seviyesi ile"""
        max_risk_fund = None
        max_vol = -1
        extreme_risk_funds = []
        
        for fcode in self.active_funds[:30]:
            try:
                # Risk kontrolü
                is_safe, risk_assessment, risk_warning = self._check_fund_risk(fcode)
                
                data = self.coordinator.db.get_fund_price_history(fcode, days)
                if not data.empty:
                    returns = data['price'].pct_change().dropna()
                    volatility = returns.std() * 100
                    
                    # EXTREME risk olanları kaydet
                    if not is_safe and risk_assessment and risk_assessment['risk_level'] == 'EXTREME':
                        extreme_risk_funds.append({
                            'fcode': fcode,
                            'volatility': volatility,
                            'risk_level': risk_assessment['risk_level']
                        })
                    
                    if volatility > max_vol:
                        max_vol = volatility
                        max_risk_fund = fcode
            except:
                continue
        
        if max_risk_fund:
            response = f"📈 SON {days} GÜNDE EN RİSKLİ FON\n"
            response += f"{'='*35}\n\n"
            response += f"⛔ En Riskli Fon: **{max_risk_fund}**\n"
            response += f"📈 Risk (Volatilite): %{max_vol:.2f}\n\n"
            
            if extreme_risk_funds:
                response += f"⚠️ EXTREME RİSK FONLARI ({len(extreme_risk_funds)} adet):\n"
                for fund in extreme_risk_funds[:5]:
                    response += f"   ⛔ {fund['fcode']} - %{fund['volatility']:.2f} volatilite\n"
                response += f"\n📋 Bu fonlardan kaçınmanız önerilir!\n"
            
            return response
        else:
            return "En riskli fon tespit edilemedi."
    
    def handle_worst_funds_list(self, count=10, days=60):
        """En çok kaybettiren fonların listesi - Risk kontrolü ile"""
        print(f"🔻 En çok kaybettiren {count} fon analiz ediliyor...")
        
        worst_funds = []
        extreme_risk_funds = []
        
        for fcode in self.active_funds[:50]:
            try:
                # ✅ Risk kontrolü
                is_safe, risk_assessment, risk_warning = self._check_fund_risk(fcode)
                
                data = self.coordinator.db.get_fund_price_history(fcode, days)
                
                if len(data) >= 10:
                    prices = data['price']
                    total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                    
                    details = self.coordinator.db.get_fund_details(fcode)
                    fund_name = details.get('fund_name', 'N/A') if details else 'N/A'
                    
                    fund_data = {
                        'fcode': fcode,
                        'total_return': total_return,
                        'current_price': prices.iloc[-1],
                        'fund_name': fund_name,
                        'risk_level': risk_assessment['risk_level'] if risk_assessment else 'UNKNOWN',
                        'is_safe': is_safe
                    }
                    
                    worst_funds.append(fund_data)
                    
                    # EXTREME risk olanları ayrı topla
                    if not is_safe and risk_assessment and risk_assessment['risk_level'] == 'EXTREME':
                        extreme_risk_funds.append(fund_data)
                    
            except Exception:
                continue
        
        # Getiriye göre sırala (en düşük = en kötü)
        worst_funds.sort(key=lambda x: x['total_return'])
        
        if worst_funds:
            response = f"\n🔻 EN ÇOK KAYBETTİREN {count} FON (Son {days} Gün)\n"
            response += f"{'='*55}\n\n"
            
            # EXTREME risk fonları önce göster
            if extreme_risk_funds:
                response += f"⛔ EXTREME RİSK + KAYIP EDEN FONLAR ({len(extreme_risk_funds)} adet):\n"
                extreme_risk_funds.sort(key=lambda x: x['total_return'])
                for i, fund in enumerate(extreme_risk_funds[:3], 1):
                    response += f"   ⛔ {fund['fcode']} - %{fund['total_return']:.2f} kayıp, {fund['risk_level']} RİSK\n"
                response += f"\n"
            
            response += f"📉 EN KÖTÜ PERFORMANS GÖSTERENİLER:\n\n"
            
            for i, fund in enumerate(worst_funds[:count], 1):
                # Risk ikonları
                if not fund['is_safe'] and fund['risk_level'] == 'EXTREME':
                    risk_icon = " ⛔ EXTREME RİSK"
                elif fund['risk_level'] == 'HIGH':
                    risk_icon = " ⚠️ YÜKSEK RİSK"
                elif fund['risk_level'] == 'MEDIUM':
                    risk_icon = " 🟡 ORTA RİSK"
                else:
                    risk_icon = " 🟢 DÜŞÜK RİSK"
                
                response += f"{i:2d}. {fund['fcode']}{risk_icon}\n"
                response += f"    📉 Kayıp: %{fund['total_return']:.2f}\n"
                response += f"    💲 Güncel Fiyat: {fund['current_price']:.4f} TL\n"
                response += f"    🛡️ Risk Seviyesi: {fund['risk_level']}\n"
                if fund['fund_name'] != 'N/A':
                    response += f"    📝 Adı: {fund['fund_name'][:45]}...\n"
                response += f"\n"
            
            # İstatistikler ve uyarılar
            safe_worst = [f for f in worst_funds[:count] if f['is_safe']]
            risky_worst = [f for f in worst_funds[:count] if not f['is_safe']]
            
            response += f"📊 RİSK ANALİZ SONUCU:\n"
            response += f"   🟢 Güvenli ama Kaybeden: {len(safe_worst)} fon\n"
            response += f"   ⚠️ Riskli ve Kaybeden: {len(risky_worst)} fon\n\n"
            
            response += f"💡 YATIRIMCI UYARILARI:\n"
            response += f"   • EXTREME riskli kayıp fonlarından uzak durun\n"
            response += f"   • Geçici kayıplar normal olabilir\n"
            response += f"   • Risk seviyesini göz önünde bulundurun\n"
            response += f"   • Portföy çeşitlendirmesi yapın\n"
            
            return response
        else:
            return f"❌ Kayıp analizi yapılamadı."
    
    def handle_worst_fund(self, days=60):
        """En çok kaybettiren fonu bulur - Risk kontrolü ile"""
        min_return_fund = None
        min_return = 1e9
        extreme_risk_losers = []
        
        for fcode in self.active_funds[:30]:
            try:
                # Risk kontrolü
                is_safe, risk_assessment, risk_warning = self._check_fund_risk(fcode)
                
                data = self.coordinator.db.get_fund_price_history(fcode, days)
                if not data.empty:
                    prices = data['price']
                    ret = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                    
                    # EXTREME risk kaybedenler
                    if not is_safe and risk_assessment and risk_assessment['risk_level'] == 'EXTREME' and ret < 0:
                        extreme_risk_losers.append({
                            'fcode': fcode,
                            'return': ret,
                            'risk_level': risk_assessment['risk_level']
                        })
                    
                    if ret < min_return:
                        min_return = ret
                        min_return_fund = fcode
            except:
                continue
        
        if min_return_fund:
            response = f"🔻 SON {days} GÜNDE EN ÇOK KAYBETTİREN FON\n"
            response += f"{'='*45}\n\n"
            response += f"⛔ En Kötü Fon: **{min_return_fund}**\n"
            response += f"📉 Getiri: %{min_return:.2f}\n\n"
            
            if extreme_risk_losers:
                response += f"⚠️ EXTREME RİSK KAYBEDENLER ({len(extreme_risk_losers)} adet):\n"
                for fund in extreme_risk_losers[:5]:
                    response += f"   ⛔ {fund['fcode']} - %{fund['return']:.2f} kayıp\n"
                response += f"\n📋 Bu tip fonlardan kaçının!\n"
            
            return response
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
        """Fallback: Hızlı Python versiyonu - Risk kontrolü ile"""
        print(f"🛡️ Python fallback: En güvenli {count} fon...")
        
        safe_funds = []
        risky_funds = []
        start_time = time.time()
        
        for fcode in self.active_funds[:40]:  # 40 fon
            try:
                # ✅ Risk kontrolü
                is_safe, risk_assessment, risk_warning = self._check_fund_risk(fcode)
                
                # Kısa veri çek (20 gün)
                data = self.coordinator.db.get_fund_price_history(fcode, 20)
                
                if len(data) >= 10:
                    prices = data.set_index('pdate')['price'].sort_index()
                    returns = prices.pct_change().dropna()
                    
                    volatility = returns.std() * 100
                    total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                    
                    fund_data = {
                        'fcode': fcode,
                        'volatility': volatility,
                        'total_return': total_return,
                        'current_price': prices.iloc[-1],
                        'risk_level': risk_assessment['risk_level'] if risk_assessment else 'UNKNOWN'
                    }
                    
                    if is_safe:
                        safe_funds.append(fund_data)
                    else:
                        risky_funds.append(fund_data)
                    
            except Exception:
                continue
        
        elapsed = time.time() - start_time
        print(f"   ✅ {len(safe_funds)} güvenli, {len(risky_funds)} riskli fon analiz edildi ({elapsed:.1f} saniye)")
        
        if not safe_funds:
            response = "❌ Risk kontrollü analiz sonucunda güvenli fon bulunamadı.\n\n"
            if risky_funds:
                response += f"⚠️ {len(risky_funds)} riskli fon tespit edildi:\n"
                for fund in risky_funds[:5]:
                    response += f"   ❌ {fund['fcode']} - {fund['risk_level']} RİSK\n"
                response += f"\n💡 Güvenli alternatifler için farklı kriterler deneyin."
            return response
        
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
        response = f"\n🛡️ RİSK KONTROLLÜ EN GÜVENLİ {len(top_funds)} FON (Python Fallback)\n"
        response += f"{'='*60}\n\n"
        response += f"📊 ANALİZ SONUCU:\n"
        response += f"   • Analiz Süresi: {elapsed:.1f} saniye\n"
        response += f"   • ✅ Güvenli Fonlar: {len(safe_funds)}\n"
        response += f"   • ❌ Riskli Fonlar: {len(risky_funds)}\n"
        response += f"   • En Düşük Volatilite: %{top_funds[0]['volatility']:.2f}\n\n"
        
        for i, fund in enumerate(top_funds, 1):
            if fund['volatility'] < 1:
                risk_level = "🟢 ÇOK GÜVENLİ"
            elif fund['volatility'] < 2:
                risk_level = "🟡 GÜVENLİ"
            elif fund['volatility'] < 4:
                risk_level = "🟠 ORTA"
            else:
                risk_level = "🔴 RİSKLİ"
            
            response += f"{i:2d}. {fund['fcode']} - {risk_level} ✅\n"
            response += f"    📉 Volatilite: %{fund['volatility']:.2f}\n"
            response += f"    📈 Getiri: %{fund['total_return']:+.2f}\n"
            response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
            response += f"    🛡️ Risk Seviyesi: {fund['risk_level']}\n"
            response += f"    🏷️ Tür: {fund['fund_type']}\n"
            response += f"\n"
        
        if risky_funds:
            response += f"⚠️ ELENENRİSKLİ FONLAR ({len(risky_funds)} adet):\n"
            risky_funds.sort(key=lambda x: x['volatility'])
            for fund in risky_funds[:3]:
                response += f"   ❌ {fund['fcode']} - %{fund['volatility']:.2f} volatilite, {fund['risk_level']} RİSK\n"
            if len(risky_funds) > 3:
                response += f"   ... ve {len(risky_funds)-3} fon daha\n"
        
        return response
    def get_fund_risk_indicator(self, risk_level):
        """Risk seviyesi için ikon döndür"""
        indicators = {
            'LOW': '🟢',
            'MEDIUM': '🟡', 
            'HIGH': '🟠',
            'EXTREME': '⛔'
        }
        return indicators.get(risk_level, '❓')
    
    def filter_safe_funds(self, fund_list, max_risk_level='HIGH'):
        """Fon listesini risk seviyesine göre filtrele"""
        safe_funds = []
        risky_funds = []
        
        risk_hierarchy = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'EXTREME': 4}
        max_risk_value = risk_hierarchy.get(max_risk_level, 3)
        
        for fund_data in fund_list:
            fcode = fund_data.get('fcode') or fund_data.get('fund_code')
            if not fcode:
                continue
                
            is_safe, risk_assessment, risk_warning = self._check_fund_risk(fcode)
            
            if risk_assessment:
                fund_risk_value = risk_hierarchy.get(risk_assessment['risk_level'], 4)
                fund_data['risk_level'] = risk_assessment['risk_level']
                fund_data['risk_assessment'] = risk_assessment
                
                if fund_risk_value <= max_risk_value:
                    safe_funds.append(fund_data)
                else:
                    risky_funds.append(fund_data)
            else:
                fund_data['risk_level'] = 'UNKNOWN'
                safe_funds.append(fund_data)
        
        return safe_funds, risky_funds
    
    def format_risk_summary(self, safe_count, risky_count, extreme_count=0):
        """Risk özeti formatla"""
        total = safe_count + risky_count
        if total == 0:
            return "📊 Risk analizi yapılamadı.\n"
        
        summary = f"📊 RİSK ANALİZ ÖZETI:\n"
        summary += f"   ✅ Güvenli Fonlar: {safe_count} (%{safe_count/total*100:.0f})\n"
        summary += f"   ⚠️ Riskli Fonlar: {risky_count} (%{risky_count/total*100:.0f})\n"
        
        if extreme_count > 0:
            summary += f"   ⛔ Extreme Risk: {extreme_count} adet\n"
        
        summary += f"   📈 Toplam Analiz: {total} fon\n\n"
        return summary
    
    def add_risk_warnings(self, response, risky_funds, context=""):
        """Yanıta risk uyarıları ekle"""
        if not risky_funds:
            return response
        
        response += f"\n⚠️ RİSK UYARILARI {context}:\n"
        
        extreme_funds = [f for f in risky_funds if f.get('risk_level') == 'EXTREME']
        if extreme_funds:
            response += f"   ⛔ EXTREME RİSK FONLARI ({len(extreme_funds)} adet):\n"
            for fund in extreme_funds[:3]:
                fcode = fund.get('fcode') or fund.get('fund_code')
                response += f"      • {fcode} - Bu fondan kaçının!\n"
            if len(extreme_funds) > 3:
                response += f"      ... ve {len(extreme_funds)-3} fon daha\n"
        
        high_risk_funds = [f for f in risky_funds if f.get('risk_level') == 'HIGH']
        if high_risk_funds:
            response += f"   🔴 YÜKSEK RİSK FONLARI ({len(high_risk_funds)} adet):\n"
            for fund in high_risk_funds[:2]:
                fcode = fund.get('fcode') or fund.get('fund_code')
                response += f"      • {fcode} - Dikkatli yatırım yapın\n"
        
        response += f"\n💡 Güvenli alternatifler için 'güvenli fonlar' sorusunu sorun.\n"
        return response

    def batch_risk_check(self, fund_codes, chunk_size=10):
        """Toplu risk kontrolü"""
        results = {}
        
        for i in range(0, len(fund_codes), chunk_size):
            chunk = fund_codes[i:i + chunk_size]
            
            try:
                codes_str = "', '".join(chunk)
                batch_query = f"""
                SELECT fcode, current_price, price_vs_sma20, rsi_14, stochastic_14, 
                       days_since_last_trade, investorcount
                FROM mv_fund_technical_indicators 
                WHERE fcode IN ('{codes_str}')
                """
                
                batch_data = self.coordinator.db.execute_query(batch_query)
                
                for _, row in batch_data.iterrows():
                    fcode = row['fcode']
                    
                    risk_data = {
                        'fcode': fcode,
                        'price_vs_sma20': float(row['price_vs_sma20']) if pd.notna(row['price_vs_sma20']) else 0,
                        'rsi_14': float(row['rsi_14']) if pd.notna(row['rsi_14']) else 50,
                        'stochastic_14': float(row['stochastic_14']) if pd.notna(row['stochastic_14']) else 50,
                        'days_since_last_trade': int(row['days_since_last_trade']) if pd.notna(row['days_since_last_trade']) else 0,
                        'investorcount': int(row['investorcount']) if pd.notna(row['investorcount']) else 0
                    }
                    
                    risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                    results[fcode] = {
                        'is_safe': risk_assessment['risk_level'] not in ['EXTREME'],
                        'risk_assessment': risk_assessment,
                        'risk_warning': RiskAssessment.format_risk_warning(risk_assessment)
                    }
                
                for fcode in chunk:
                    if fcode not in results:
                        results[fcode] = {
                            'is_safe': True,
                            'risk_assessment': None,
                            'risk_warning': ""
                        }
                        
            except Exception as e:
                print(f"Batch risk check hatası: {e}")
                for fcode in chunk:
                    if fcode not in results:
                        is_safe, risk_assessment, risk_warning = self._check_fund_risk(fcode)
                        results[fcode] = {
                            'is_safe': is_safe,
                            'risk_assessment': risk_assessment,
                            'risk_warning': risk_warning
                        }
        
        return results

    def create_risk_performance_report(self, fund_data_list, title="PERFORMANS + RİSK RAPORU"):
        """Performans ve risk birleşik raporu oluştur"""
        if not fund_data_list:
            return f"❌ {title} için veri bulunamadı."
        
        fund_codes = [f.get('fcode') or f.get('fund_code') for f in fund_data_list if f.get('fcode') or f.get('fund_code')]
        risk_results = self.batch_risk_check(fund_codes)
        
        for fund_data in fund_data_list:
            fcode = fund_data.get('fcode') or fund_data.get('fund_code')
            if fcode in risk_results:
                fund_data.update(risk_results[fcode])
        
        safe_funds = [f for f in fund_data_list if f.get('is_safe', True)]
        risky_funds = [f for f in fund_data_list if not f.get('is_safe', True)]
        
        response = f"\n📊 {title}\n"
        response += f"{'='*len(title)}\n\n"
        
        response += self.format_risk_summary(len(safe_funds), len(risky_funds))
        
        if safe_funds:
            response += f"✅ GÜVENLİ YÜKSEK PERFORMANS FONLARI ({len(safe_funds)} adet):\n\n"
            
            for i, fund in enumerate(safe_funds[:10], 1):
                fcode = fund.get('fcode') or fund.get('fund_code')
                risk_level = fund.get('risk_assessment', {}).get('risk_level', 'LOW')
                risk_icon = self.get_fund_risk_indicator(risk_level)
                
                response += f"{i:2d}. {fcode} {risk_icon}\n"
                
                if 'total_return' in fund:
                    response += f"    📈 Getiri: %{fund['total_return']:+.2f}\n"
                if 'volatility' in fund:
                    response += f"    📊 Volatilite: %{fund['volatility']:.2f}\n"
                if 'current_price' in fund:
                    response += f"    💰 Fiyat: {fund['current_price']:.4f} TL\n"
                
                response += f"    🛡️ Risk: {risk_level}\n\n"
        
        if risky_funds:
            response = self.add_risk_warnings(response, risky_funds, "- PERFORMANS FONLARI")
        
        return response

    @staticmethod
    def get_examples():
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
        return [
            "güvenli", "riskli", "kazanan", "kaybettiren", "performans",
            "getiri", "analiz", "öneri", "2025", "en iyi", "en kötü",
            "volatilite", "sharpe", "kazandıran", "kaybeden", "düşen",
            "yükselen", "artış", "düşüş", "değerlendirme"
        ]
    
    @staticmethod
    def get_patterns():
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
                'score': 0.90
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
