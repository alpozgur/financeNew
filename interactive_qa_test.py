# interactive_qa_test.py
"""
TEFAS Analysis System - Interaktif Soru-Cevap Test Sistemi
2025 fon önerileri ve diğer analizler için gerçek verilerle test
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config.config import Config
from analysis.coordinator import AnalysisCoordinator

class TefasQASystem:
    """TEFAS Soru-Cevap Sistemi"""
    
    def __init__(self):
        print("🚀 TEFAS Analysis Q&A System Loading...")
        self.config = Config()
        self.coordinator = AnalysisCoordinator(self.config)
        
        # Aktif fonları yükle
        print("📊 Loading active funds...")
        self.active_funds = self._load_active_funds()
        print(f"✅ Loaded {len(self.active_funds)} active funds")
        
        # AI durumunu kontrol et
        self.ai_available = self._check_ai_availability()
        
    def _load_active_funds(self, max_funds=50):
        """Aktif fonları yükle"""
        all_funds = self.coordinator.db.get_all_fund_codes()
        active_funds = []
        
        for fcode in all_funds[:max_funds]:  # İlk 50 fonu kontrol et
            try:
                recent_data = self.coordinator.db.get_fund_price_history(fcode, 5)
                if not recent_data.empty:
                    last_date = pd.to_datetime(recent_data['pdate'].max())
                    days_ago = (datetime.now() - last_date).days
                    
                    if days_ago < 60:  # Son 60 gün içinde veri var
                        active_funds.append(fcode)
                        
            except Exception:
                continue
                
        return active_funds
    
    def _check_ai_availability(self):
        """AI sistemlerinin durumunu kontrol et"""
        ai_status = {
            'openai': self.coordinator.ai_analyzer.openai_available,
            'ollama': self.coordinator.ai_analyzer.ollama_available
        }
        
        if ai_status['openai']:
            print("🤖 OpenAI: Available")
        else:
            print("⚠️ OpenAI: Not configured")
            
        if ai_status['ollama']:
            print("🦙 Ollama: Available")
        else:
            print("⚠️ Ollama: Not available")
            
        return ai_status
    
    def answer_question(self, question):
        """Soruya cevap ver"""
        question_lower = question.lower()
        
        # Soru tipini tespit et
        if any(word in question_lower for word in ['2025', 'öneri', 'öner', 'recommend', 'suggest']):
            return self._handle_2025_recommendation(question)
        elif any(word in question_lower for word in ['analiz', 'analyze', 'performance']):
            return self._handle_analysis_question(question)
        elif any(word in question_lower for word in ['karşılaştır', 'compare', 'vs']):
            return self._handle_comparison_question(question)
        elif any(word in question_lower for word in ['risk', 'güvenli', 'safe']):
            return self._handle_risk_question(question)
        elif any(word in question_lower for word in ['portföy', 'portfolio']):
            return self._handle_portfolio_question(question)
        elif any(word in question_lower for word in ['piyasa', 'market', 'durum']):
            return self._handle_market_question(question)
        else:
            return self._handle_general_question(question)
    
    def _handle_2025_recommendation(self, question):
        """2025 fon önerisi soruları"""
        print("🎯 2025 Fund Recommendation Analysis...")
        
        # Risk toleransını sorudan çıkarmaya çalış
        risk_tolerance = "moderate"
        if any(word in question.lower() for word in ['güvenli', 'safe', 'conservative']):
            risk_tolerance = "conservative"
        elif any(word in question.lower() for word in ['agresif', 'aggressive', 'risk']):
            risk_tolerance = "aggressive"
        
        # Tutarı sorudan çıkarmaya çalış - Düzeltilmiş
        import re
        # Sadece büyük sayıları yakala (1000+)
        amounts = re.findall(r'\b(\d{4,})\b', question.replace('.', '').replace(',', ''))
        investment_amount = 100000  # Default
        
        if amounts:
            try:
                parsed_amount = int(amounts[0])
                if parsed_amount >= 1000:  # Minimum 1000 TL
                    investment_amount = parsed_amount
            except:
                pass
        
        print(f"📊 Analysis Parameters:")
        print(f"   Risk Tolerance: {risk_tolerance}")
        print(f"   Investment Amount: {investment_amount:,.0f} TL")  # Düzeltildi        
        # Aktif fonları analiz et
        analysis_results = []
        test_funds = self.active_funds[:15]  # İlk 15 aktif fon
        
        print(f"\n🔍 Analyzing {len(test_funds)} funds...")
        
        for i, fcode in enumerate(test_funds):
            try:
                print(f"   [{i+1}/{len(test_funds)}] {fcode}...", end='')
                
                # 3 aylık veri al
                data = self.coordinator.db.get_fund_price_history(fcode, 60)
                
                if len(data) >= 20:
                    prices = data.set_index('pdate')['price'].sort_index()
                    returns = prices.pct_change().dropna()
                    
                    # Temel metrikler hesapla
                    total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                    annual_return = total_return * (252 / len(prices))
                    volatility = returns.std() * np.sqrt(252) * 100
                    sharpe = (annual_return - 15) / volatility if volatility > 0 else 0
                    win_rate = (returns > 0).sum() / len(returns) * 100
                    
                    # Max drawdown
                    cumulative = (1 + returns).cumprod()
                    running_max = cumulative.expanding().max()
                    drawdown = (cumulative - running_max) / running_max
                    max_drawdown = drawdown.min() * 100
                    
                    # 2025 skorunu hesapla
                    score = self._calculate_2025_score(annual_return, volatility, sharpe, win_rate, max_drawdown, risk_tolerance)
                    
                    analysis_results.append({
                        'fund_code': fcode,
                        'annual_return': annual_return,
                        'volatility': volatility,
                        'sharpe_ratio': sharpe,
                        'win_rate': win_rate,
                        'max_drawdown': max_drawdown,
                        'score_2025': score,
                        'current_price': prices.iloc[-1]
                    })
                    
                    print(f" ✅ (Score: {score:.1f})")
                else:
                    print(" ❌ (Insufficient data)")
                    
            except Exception as e:
                print(f" ❌ (Error: {str(e)[:20]})")
                continue
        
        if not analysis_results:
            return "❌ Analiz için yeterli veri bulunamadı."
        
        # Sonuçları sırala
        df = pd.DataFrame(analysis_results)
        df = df.sort_values('score_2025', ascending=False)
        
        # Cevabı oluştur
        response = f"\n🎯 2025 YIL SONU FON ÖNERİSİ RAPORU\n"
        response += f"{'='*50}\n\n"
        
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
            portfolio_risk = 0
            
            for i, ((_, fund), weight) in enumerate(zip(top_5.iterrows(), weights)):
                amount = investment_amount * weight
                portfolio_return += fund['annual_return'] * weight
                portfolio_risk += (fund['volatility'] ** 2) * (weight ** 2)  # Simplified
                
                response += f"   {fund['fund_code']}: %{weight*100:.0f} ({amount:,.0f} TL)\n"
                response += f"      Beklenen Katkı: %{fund['annual_return']*weight:.1f}\n"
            
            portfolio_risk = np.sqrt(portfolio_risk)
            portfolio_sharpe = (portfolio_return - 15) / portfolio_risk if portfolio_risk > 0 else 0
            
            response += f"\n📊 PORTFÖY BEKLENTİLERİ:\n"
            response += f"   📈 Beklenen Yıllık Getiri: %{portfolio_return:.1f}\n"
            response += f"   📉 Portföy Riski: %{portfolio_risk:.1f}\n"
            response += f"   ⚡ Portföy Sharpe Oranı: {portfolio_sharpe:.3f}\n"
        
        # AI ANALİZİ (eğer mevcut ise)
        if self.ai_available['openai'] or self.ai_available['ollama']:
            response += f"\n🤖 AI YORUMU:\n"
            ai_prompt = f"""
            2025 yılı için TEFAS fon analizi:
            En iyi 3 fon: {', '.join(top_5.head(3)['fund_code'].tolist())}
            Ortalama beklenen getiri: %{top_5.head(3)['annual_return'].mean():.1f}
            Risk toleransı: {risk_tolerance}
            
            Bu sonuçlara dayanarak 2025 için kısa ve özlü yorum yap.
            """
            
            try:
                if self.ai_available['openai']:
                    ai_response = self.coordinator.ai_analyzer.query_openai(ai_prompt, "Sen TEFAS uzmanısın.")
                    response += f"   {ai_response[:200]}...\n"
                elif self.ai_available['ollama']:
                    ai_response = self.coordinator.ai_analyzer.query_ollama(ai_prompt, "Sen TEFAS uzmanısın.")
                    response += f"   {ai_response[:200]}...\n"
            except Exception as e:
                response += f"   AI yorumu alınamadı: {e}\n"
        
        # RİSK UYARILARI
        response += f"\n⚠️ 2025 RİSK UYARILARI:\n"
        response += f"   • Geçmiş performans gelecek getiriyi garanti etmez\n"
        response += f"   • Türkiye ekonomik göstergelerini takip edin\n"
        response += f"   • Portföyü çeyrek yıllık gözden geçirin\n"
        response += f"   • Acil durumlar için nakit rezerv tutun\n"
        
        # UYGULAMA PLANI
        response += f"\n📅 UYGULAMA PLANI:\n"
        response += f"   1. İlk ay: En güvenli 2 fona %60 yatırım\n"
        response += f"   2. 2-3. ay: Portföyü tamamlama\n"
        response += f"   3. Aylık takip ve gerektiğinde rebalancing\n"
        
        response += f"\n✅ Analiz tamamlandı: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        
        return response
    
    def _calculate_2025_score(self, annual_return, volatility, sharpe, win_rate, max_drawdown, risk_tolerance):
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
        
        # Drawdown penaltısı
        drawdown_penalty = min(abs(max_drawdown) / 2, 10)
        score -= drawdown_penalty
        
        return max(min(score, 100), 0)
    
    def _handle_analysis_question(self, question):
        """Analiz soruları"""
        # Fon kodunu sorudan çıkarmaya çalış
        words = question.upper().split()
        fund_code = None
        
        for word in words:
            if len(word) == 3 and word.isalpha():  # 3 harfli kod
                if word in self.active_funds:
                    fund_code = word
                    break
        
        if not fund_code:
            return f"❌ Geçerli bir fon kodu bulunamadı. Örnek: 'AKB fonunu analiz et'\nMevcut fonlar: {', '.join(self.active_funds[:10])}..."
        
        try:
            print(f"🔍 {fund_code} fonu analiz ediliyor...")
            
            # Kapsamlı analiz yap
            result = self.coordinator.comprehensive_fund_analysis(fund_code, days=100)
            
            if 'error' in result:
                return f"❌ {fund_code} analizi başarısız: {result['error']}"
            
            # Sonuçları formatla
            response = f"\n📊 {fund_code} FONU ANALİZ RAPORU\n"
            response += f"{'='*40}\n\n"
            
            # Performance
            if 'performance_analysis' in result:
                perf = result['performance_analysis']['basic_metrics']
                response += f"📈 PERFORMANS ANALİZİ:\n"
                response += f"   Yıllık Getiri: %{perf.get('annual_return', 0)*100:.2f}\n"
                response += f"   Volatilite: %{perf.get('annual_volatility', 0)*100:.2f}\n"
                response += f"   Sharpe Oranı: {perf.get('sharpe_ratio', 0):.3f}\n"
                response += f"   Kazanma Oranı: %{perf.get('win_rate', 0)*100:.1f}\n\n"
            
            # Technical
            if 'technical_analysis' in result:
                tech = result['technical_analysis']['latest_values']
                response += f"📊 TEKNİK ANALİZ:\n"
                response += f"   Güncel Fiyat: {tech.get('price', 0):.4f} TL\n"
                response += f"   RSI: {tech.get('rsi', 0):.1f}\n"
                response += f"   Sinyal Gücü: {tech.get('signal_strength', 0):.2f}\n\n"
            
            # Investment Score
            if 'investment_score' in result:
                score = result['investment_score']
                response += f"💯 YATIRIM SKORU:\n"
                response += f"   Toplam Skor: {score.get('total_score', 0):.1f}/100\n"
                response += f"   Öneri: {score.get('recommendation', 'Bilinmiyor')}\n"
                response += f"   Kategori: {score.get('category', 'Bilinmiyor')}\n\n"
            
            response += f"✅ Analiz tamamlandı: {datetime.now().strftime('%H:%M:%S')}\n"
            
            return response
            
        except Exception as e:
            return f"❌ Analiz hatası: {e}"
    
    def _handle_comparison_question(self, question):
        """Karşılaştırma soruları"""
        # Fon kodlarını bul
        words = question.upper().split()
        fund_codes = []
        
        for word in words:
            if len(word) == 3 and word.isalpha():
                if word in self.active_funds:
                    fund_codes.append(word)
        
        if len(fund_codes) < 2:
            return f"❌ Karşılaştırma için en az 2 fon kodu gerekli. Örnek: 'AKB ve YAS karşılaştır'"
        
        try:
            print(f"⚖️ {fund_codes} fonları karşılaştırılıyor...")
            
            comparison_data = []
            
            for fcode in fund_codes:
                data = self.coordinator.db.get_fund_price_history(fcode, 60)
                if not data.empty:
                    prices = data['price']
                    returns = prices.pct_change().dropna()
                    
                    comparison_data.append({
                        'fund': fcode,
                        'return_60d': (prices.iloc[-1] / prices.iloc[0] - 1) * 100,
                        'volatility': returns.std() * 100,
                        'current_price': prices.iloc[-1]
                    })
            
            if not comparison_data:
                return "❌ Karşılaştırma için veri bulunamadı"
            
            df = pd.DataFrame(comparison_data)
            
            response = f"\n⚖️ FON KARŞILAŞTIRMASI\n"
            response += f"{'='*30}\n\n"
            
            for _, fund in df.iterrows():
                response += f"📊 {fund['fund']}:\n"
                response += f"   60 Gün Getiri: %{fund['return_60d']:.2f}\n"
                response += f"   Volatilite: %{fund['volatility']:.2f}\n"
                response += f"   Güncel Fiyat: {fund['current_price']:.4f} TL\n\n"
            
            # Kazanan belirleme
            best_return = df.loc[df['return_60d'].idxmax()]
            lowest_risk = df.loc[df['volatility'].idxmin()]
            
            response += f"🏆 KAZANANLAR:\n"
            response += f"   En İyi Getiri: {best_return['fund']} (%{best_return['return_60d']:.2f})\n"
            response += f"   En Düşük Risk: {lowest_risk['fund']} (%{lowest_risk['volatility']:.2f})\n"
            
            return response
            
        except Exception as e:
            return f"❌ Karşılaştırma hatası: {e}"
    
    def _handle_risk_question(self, question):
        """Risk ile ilgili sorular"""
        response = f"\n🛡️ RİSK ANALİZİ VE GÜVENLİ YATIRIM\n"
        response += f"{'='*35}\n\n"
        
        # Düşük riskli fonları bul
        low_risk_funds = []
        
        for fcode in self.active_funds[:10]:
            try:
                data = self.coordinator.db.get_fund_price_history(fcode, 60)
                if not data.empty:
                    returns = data['price'].pct_change().dropna()
                    volatility = returns.std() * 100
                    
                    if volatility < 15:  # %15'ten düşük volatilite
                        low_risk_funds.append({
                            'fund': fcode,
                            'volatility': volatility,
                            'return': (data['price'].iloc[-1] / data['price'].iloc[0] - 1) * 100
                        })
            except:
                continue
        
        if low_risk_funds:
            df = pd.DataFrame(low_risk_funds).sort_values('volatility')
            
            response += f"🛡️ DÜŞÜK RİSKLİ FONLAR:\n"
            for _, fund in df.head(5).iterrows():
                response += f"   {fund['fund']}: Risk %{fund['volatility']:.1f}, Getiri %{fund['return']:.1f}\n"
        
        response += f"\n📋 RİSK YÖNETİMİ PRİNSİPLERİ:\n"
        response += f"   • Portföyünüzü diversifiye edin\n"
        response += f"   • Risk toleransınızı bilin\n"
        response += f"   • Acil fon ayırın (6-12 aylık gider)\n"
        response += f"   • Düzenli olarak rebalancing yapın\n"
        response += f"   • Uzun vadeli düşünün\n"
        
        return response
    
    def _handle_portfolio_question(self, question):
        """Portföy soruları"""
        response = f"\n💼 PORTFÖY YÖNETİMİ REHBERİ\n"
        response += f"{'='*30}\n\n"
        
        response += f"🎯 PORTFÖY DAĞILIMI ÖNERİLERİ:\n\n"
        
        response += f"Conservative (Güvenli):\n"
        response += f"   • %60 Tahvil/Para Piyasası Fonları\n"
        response += f"   • %25 Karma Fonlar\n"
        response += f"   • %15 Hisse Senedi Fonları\n\n"
        
        response += f"Moderate (Dengeli):\n"
        response += f"   • %40 Tahvil/Para Piyasası\n"
        response += f"   • %35 Karma Fonlar\n"
        response += f"   • %25 Hisse Senedi Fonları\n\n"
        
        response += f"Aggressive (Agresif):\n"
        response += f"   • %20 Tahvil/Para Piyasası\n"
        response += f"   • %30 Karma Fonlar\n"
        response += f"   • %50 Hisse Senedi Fonları\n\n"
        
        response += f"📅 REBALANCING TAKVİMİ:\n"
        response += f"   • Çeyreklik: Ağırlık kontrolü\n"
        response += f"   • Altı aylık: Strateji gözden geçirme\n"
        response += f"   • Yıllık: Kapsamlı değerlendirme\n"
        
        return response
    
    def _handle_market_question(self, question):
        """Piyasa durumu soruları"""
        print("📊 Piyasa durumu analiz ediliyor...")
        
        try:
            # Son günlerin verilerini analiz et
            market_data = []
            
            for fcode in self.active_funds[:20]:
                try:
                    data = self.coordinator.db.get_fund_price_history(fcode, 10)
                    if not data.empty:
                        prices = data['price']
                        recent_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                        market_data.append(recent_return)
                except:
                    continue
            
            if market_data:
                avg_return = np.mean(market_data)
                positive_funds = sum(1 for r in market_data if r > 0)
                total_funds = len(market_data)
                
                response = f"\n📈 PİYASA DURUMU RAPORU\n"
                response += f"{'='*25}\n\n"
                
                response += f"📊 SON 10 GÜN ANALİZİ:\n"
                response += f"   Analiz Edilen Fon: {total_funds}\n"
                response += f"   Ortalama Getiri: %{avg_return:.2f}\n"
                response += f"   Pozitif Performans: {positive_funds}/{total_funds} (%{positive_funds/total_funds*100:.1f})\n\n"
                
                # Piyasa durumu
                if avg_return > 2:
                    mood = "🟢 ÇOK POZİTİF"
                elif avg_return > 0:
                    mood = "🟡 POZİTİF"
                elif avg_return > -2:
                    mood = "🟠 NÖTR"
                else:
                    mood = "🔴 NEGATİF"
                
                response += f"🌡️ PİYASA DUYARLILIĞI: {mood}\n\n"
                
                response += f"💡 YATIRIMCI ÖNERİLERİ:\n"
                if avg_return > 0:
                    response += f"   • Pozitif momentum devam edebilir\n"
                    response += f"   • Kademeli yatırım düşünülebilir\n"
                else:
                    response += f"   • Temkinli yaklaşım öneriliyor\n"
                    response += f"   • Fırsat kollama zamanı olabilir\n"
                
                return response
            else:
                return "❌ Piyasa analizi için yeterli veri bulunamadı"
                
        except Exception as e:
            return f"❌ Piyasa analizi hatası: {e}"
    
    def _handle_general_question(self, question):
        """Genel sorular"""
        response = f"\n❓ GENEL BILGI\n"
        response += f"{'='*15}\n\n"
        
        response += f"🤖 TEFAS Analysis System Q&A\n\n"
        
        response += f"📋 SORU TİPLERİ:\n"
        response += f"   • '2025 için hangi fonları önerirsin?'\n"
        response += f"   • 'AKB fonunu analiz et'\n"
        response += f"   • 'AKB ve YAS karşılaştır'\n"
        response += f"   • 'Güvenli fonlar neler?'\n"
        response += f"   • 'Portföy nasıl oluştururum?'\n"
        response += f"   • 'Piyasa durumu nasıl?'\n\n"
        
        response += f"📊 SİSTEM DURUMU:\n"
        response += f"   Aktif Fonlar: {len(self.active_funds)}\n"
        response += f"   OpenAI: {'✅' if self.ai_available['openai'] else '❌'}\n"
        response += f"   Ollama: {'✅' if self.ai_available['ollama'] else '❌'}\n\n"
        
        response += f"💡 İPUÇLARI:\n"
        response += f"   • Belirli fon kodları kullanın (örn: AKB, YAS)\n"
        response += f"   • Yatırım tutarını belirtin (örn: 50000 TL)\n"
        response += f"   • Risk tercihini belirtin (güvenli/agresif)\n"
        
        return response
    
    def run_interactive_session(self):
        """İnteraktif soru-cevap oturumu"""
        print("\n" + "="*60)
        print("🤖 TEFAS ANALYSIS SYSTEM - INTERACTIVE Q&A")
        print("="*60)
        print("💡 Örnek sorular:")
        print("   • '2025 için 100000 TL ile hangi fonları önerirsin?'")
        print("   • 'AKB fonunu analiz et'")
        print("   • 'AKB ve YAS karşılaştır'")
        print("   • 'Güvenli fonlar neler?'")
        print("   • 'Piyasa durumu nasıl?'")
        print("\n💬 Sorunuzu yazın (çıkmak için 'exit' yazın):")
        print("-" * 60)
        
        while True:
            try:
                question = input("\n🔍 Soru: ").strip()
                
                if question.lower() in ['exit', 'çıkış', 'quit', 'q']:
                    print("\n👋 TEFAS Analysis Q&A Session sona erdi!")
                    break
                
                if not question:
                    continue
                
                print(f"\n🔄 İşleniyor...")
                answer = self.answer_question(question)
                print(answer)
                
                print("\n" + "-" * 60)
                
            except KeyboardInterrupt:
                print("\n\n👋 Session sona erdi!")
                break
            except Exception as e:
                print(f"\n❌ Hata oluştu: {e}")
                continue

def main():
    """Ana fonksiyon"""
    try:
        # Q&A sistemini başlat
        qa_system = TefasQASystem()
        
        # Test modunu kontrol et
        if len(sys.argv) > 1:
            if sys.argv[1] == "--test":
                # Otomatik test modu
                run_automated_tests(qa_system)
            elif sys.argv[1] == "--demo":
                # Demo sorular
                run_demo_questions(qa_system)
            else:
                # Tek soru modu
                question = " ".join(sys.argv[1:])
                answer = qa_system.answer_question(question)
                print(answer)
        else:
            # İnteraktif mod
            qa_system.run_interactive_session()
            
    except Exception as e:
        print(f"❌ Sistem başlatma hatası: {e}")
        return False
    
    return True

def run_automated_tests(qa_system):
    """Otomatik test soruları"""
    test_questions = [
        "2025 için 100000 TL ile hangi fonları önerirsin?",
        "AKB fonunu analiz et",
        "Piyasa durumu nasıl?",
        "Güvenli fonlar neler?",
        "Portföy nasıl oluştururum?"
    ]
    
    print("🧪 OTOMATIK TEST MODU")
    print("="*30)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[TEST {i}/5] {question}")
        print("-" * 40)
        
        try:
            answer = qa_system.answer_question(question)
            print(answer[:300] + "..." if len(answer) > 300 else answer)
            print("✅ Test başarılı")
        except Exception as e:
            print(f"❌ Test hatası: {e}")
    
    print(f"\n🎉 Otomatik testler tamamlandı!")

def run_demo_questions(qa_system):
    """Demo sorular"""
    demo_questions = [
        {
            "question": "2025 için 50000 TL ile güvenli fonlar önerirsin?",
            "description": "2025 yılı için güvenli yatırım önerisi"
        },
        {
            "question": "AKB fonunu analiz et",
            "description": "Tek fon detaylı analizi"
        },
        {
            "question": "Piyasa durumu nasıl?",
            "description": "Genel piyasa durumu"
        }
    ]
    
    print("🎬 DEMO MODU")
    print("="*20)
    
    for i, demo in enumerate(demo_questions, 1):
        print(f"\n[DEMO {i}/3] {demo['description']}")
        print(f"Soru: {demo['question']}")
        print("-" * 50)
        
        try:
            answer = qa_system.answer_question(demo['question'])
            # İlk 500 karakteri göster
            preview = answer[:500] + "..." if len(answer) > 500 else answer
            print(preview)
            print("✅ Demo başarılı")
            
            input("\nDevam etmek için Enter'a basın...")
            
        except Exception as e:
            print(f"❌ Demo hatası: {e}")
    
    print(f"\n🎉 Demo tamamlandı!")

if __name__ == "__main__":
    main()