# advanced_metrics_analyzer.py
"""
İleri Finansal Metrikler Analizi
Beta, Alpha, Tracking Error, Information Ratio hesaplamaları
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
from scipy import stats

class AdvancedMetricsAnalyzer:
    """İleri finansal metrikler için analiz sınıfı"""
    
    def __init__(self, coordinator, active_funds, ai_status):
        self.coordinator = coordinator
        self.active_funds = active_funds
        self.ai_status = ai_status
        self.logger = logging.getLogger(__name__)
        
        # Benchmark olarak kullanılacak index fonları (BIST100 vb. temsil eden)
        self.benchmark_funds = ['TI2', 'TKF', 'GAF']  # Örnek index fonlar
        self.risk_free_rate = 0.15  # %15 risksiz faiz oranı (Türkiye için)
        
    def handle_beta_analysis(self, question):
        """Beta katsayısı analizi - SQL ve Python hibrit"""
        print("📊 Beta katsayısı analiz ediliyor...")
        
        # Beta eşiğini belirle
        beta_threshold = 1.0
        if "düşük" in question.lower() or "altında" in question.lower():
            comparison = "<"
        else:
            comparison = ">"
            
        response = f"\n📊 BETA KATSAYISI ANALİZİ\n"
        response += f"{'='*50}\n\n"
        response += f"🎯 Beta {comparison} {beta_threshold} olan fonlar aranıyor...\n\n"
        
        # Önce benchmark verilerini al
        benchmark_data = self._get_benchmark_data()
        if benchmark_data is None:
            return "❌ Benchmark verisi alınamadı. Beta hesaplaması yapılamıyor."
        
        beta_results = []
        processed = 0
        
        # SQL ile hızlı filtreleme
        try:
            # Son 60 günlük volatilite bazlı ön filtreleme
            query = """
            WITH price_changes AS (
                SELECT fcode, 
                    price,
                    pdate,
                    LAG(price) OVER (PARTITION BY fcode ORDER BY pdate) as prev_price
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '90 days'
                AND investorcount > 50
                AND price > 0  -- Sıfır fiyat kontrolü
            ),
            volatility_calc AS (
                SELECT fcode,
                    STDDEV(
                        CASE 
                            WHEN prev_price > 0 AND prev_price IS NOT NULL 
                            THEN (price - prev_price) / prev_price 
                            ELSE NULL 
                        END
                    ) * SQRT(252) as annual_vol,
                    COUNT(*) as data_points
                FROM price_changes
                WHERE prev_price IS NOT NULL AND prev_price > 0
                GROUP BY fcode
                HAVING COUNT(*) >= 60
            )
            SELECT fcode, annual_vol
            FROM volatility_calc
            WHERE annual_vol IS NOT NULL
            ORDER BY annual_vol
            LIMIT 100
            """
            
            pre_filtered = self.coordinator.db.execute_query(query)
            candidate_funds = pre_filtered['fcode'].tolist() if not pre_filtered.empty else self.active_funds[:30]
            
        except Exception as e:
            print(f"   ⚠️ SQL ön filtreleme hatası: {e}")
            candidate_funds = self.active_funds[:30]
        
        # Her fon için beta hesapla
        for fcode in candidate_funds:
            try:
                processed += 1
                if processed % 10 == 0:
                    print(f"   📊 {processed}/{len(candidate_funds)} fon işlendi...")
                
                # Fon verilerini al
                fund_data = self.coordinator.db.get_fund_price_history(fcode, 252)
                
                if len(fund_data) >= 60:
                    # Beta hesapla
                    beta = self._calculate_beta(fund_data, benchmark_data)
                    
                    if beta is not None:
                        # Beta koşulunu kontrol et
                        if (comparison == "<" and beta < beta_threshold) or \
                           (comparison == ">" and beta >= beta_threshold):
                            
                            # Diğer metrikleri de hesapla
                            fund_returns = self._calculate_returns(fund_data)
                            annual_return = self._annualized_return(fund_returns)
                            volatility = fund_returns.std() * np.sqrt(252)
                            
                            beta_results.append({
                                'fcode': fcode,
                                'beta': beta,
                                'annual_return': annual_return,
                                'volatility': volatility,
                                'current_price': fund_data['price'].iloc[-1]
                            })
                
            except Exception as e:
                continue
        
        # Sonuçları sırala
        beta_results.sort(key=lambda x: x['beta'])
        
        if not beta_results:
            return f"❌ Beta {comparison} {beta_threshold} olan fon bulunamadı."
        
        # Fund details al
        for result in beta_results[:10]:
            try:
                details = self.coordinator.db.get_fund_details(result['fcode'])
                result['fund_name'] = details.get('fund_name', 'N/A') if details else 'N/A'
                result['fund_type'] = details.get('fund_type', 'N/A') if details else 'N/A'
            except:
                result['fund_name'] = 'N/A'
                result['fund_type'] = 'N/A'
        
        # Sonuçları göster
        response += f"🏆 BETA {comparison} {beta_threshold} OLAN FONLAR:\n\n"
        
        for i, fund in enumerate(beta_results[:10], 1):
            # Risk profili
            if fund['beta'] < 0.5:
                risk_profile = "🟢 ÇOK SAVUNMACI"
            elif fund['beta'] < 0.8:
                risk_profile = "🟡 SAVUNMACI"
            elif fund['beta'] < 1.2:
                risk_profile = "🟠 DENGELİ"
            elif fund['beta'] < 1.5:
                risk_profile = "🔴 AGRESİF"
            else:
                risk_profile = "🔥 ÇOK AGRESİF"
            
            response += f"{i:2d}. {fund['fcode']} - {risk_profile}\n"
            response += f"    📊 Beta: {fund['beta']:.3f}\n"
            response += f"    📈 Yıllık Getiri: %{fund['annual_return']:.1f}\n"
            response += f"    📉 Volatilite: %{fund['volatility']:.1f}\n"
            response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
            response += f"    🏷️ Tür: {fund['fund_type']}\n"
            if fund['fund_name'] != 'N/A':
                response += f"    📝 Adı: {fund['fund_name'][:40]}...\n"
            response += f"\n"
        
        # İstatistikler
        avg_beta = sum(f['beta'] for f in beta_results) / len(beta_results)
        avg_return = sum(f['annual_return'] for f in beta_results) / len(beta_results)
        
        response += f"📊 BETA İSTATİSTİKLERİ:\n"
        response += f"   Bulunan Fon Sayısı: {len(beta_results)}\n"
        response += f"   Ortalama Beta: {avg_beta:.3f}\n"
        response += f"   Ortalama Getiri: %{avg_return:.1f}\n"
        response += f"   En Düşük Beta: {beta_results[0]['fcode']} ({beta_results[0]['beta']:.3f})\n"
        
        # AI Yorumu
        if self.ai_status['openai'] or self.ai_status['ollama']:
            response += self._get_ai_commentary_for_beta(beta_results, comparison, beta_threshold)
        
        return response
    
    def handle_alpha_analysis(self, question):
        """Alpha değeri analizi"""
        print("📊 Alpha değeri analiz ediliyor...")
        
        # Alpha koşulunu belirle
        is_positive = "pozitif" in question.lower() or "yüksek" in question.lower()
        
        response = f"\n📊 ALPHA DEĞERİ ANALİZİ\n"
        response += f"{'='*50}\n\n"
        response += f"🎯 {'Pozitif' if is_positive else 'Negatif'} Alpha değerine sahip fonlar aranıyor...\n\n"
        
        # Benchmark verilerini al
        benchmark_data = self._get_benchmark_data()
        if benchmark_data is None:
            return "❌ Benchmark verisi alınamadı. Alpha hesaplaması yapılamıyor."
        
        alpha_results = []
        
        # Aktif fonları analiz et
        for fcode in self.active_funds[:40]:
            try:
                fund_data = self.coordinator.db.get_fund_price_history(fcode, 252)
                
                if len(fund_data) >= 60:
                    # Alpha ve diğer metrikleri hesapla
                    alpha_data = self._calculate_alpha(fund_data, benchmark_data)
                    
                    if alpha_data is not None:
                        alpha = alpha_data['alpha']
                        
                        # Alpha koşulunu kontrol et
                        if (is_positive and alpha > 0) or (not is_positive and alpha <= 0):
                            alpha_results.append({
                                'fcode': fcode,
                                'alpha': alpha,
                                'beta': alpha_data['beta'],
                                'annual_return': alpha_data['fund_return'],
                                'benchmark_return': alpha_data['benchmark_return'],
                                'r_squared': alpha_data['r_squared'],
                                'current_price': fund_data['price'].iloc[-1]
                            })
                
            except Exception:
                continue
        
        # Alpha'ya göre sırala
        alpha_results.sort(key=lambda x: x['alpha'], reverse=True)
        
        if not alpha_results:
            return f"❌ {'Pozitif' if is_positive else 'Negatif'} Alpha değerine sahip fon bulunamadı."
        
        # Fund details al
        for result in alpha_results[:10]:
            try:
                details = self.coordinator.db.get_fund_details(result['fcode'])
                result['fund_name'] = details.get('fund_name', 'N/A') if details else 'N/A'
                result['fund_type'] = details.get('fund_type', 'N/A') if details else 'N/A'
            except:
                result['fund_name'] = 'N/A'
                result['fund_type'] = 'N/A'
        
        # Sonuçları göster
        response += f"🏆 EN YÜKSEK ALPHA DEĞERLERİ:\n\n"
        
        for i, fund in enumerate(alpha_results[:10], 1):
            # Alpha performansı
            if fund['alpha'] > 10:
                performance = "🌟 ÜSTÜN PERFORMANS"
            elif fund['alpha'] > 5:
                performance = "🟢 ÇOK İYİ"
            elif fund['alpha'] > 0:
                performance = "🟡 İYİ"
            elif fund['alpha'] > -5:
                performance = "🟠 ZAYIF"
            else:
                performance = "🔴 KÖTÜ"
            
            response += f"{i:2d}. {fund['fcode']} - {performance}\n"
            response += f"    📊 Alpha: %{fund['alpha']:.2f} (yıllık)\n"
            response += f"    📈 Beta: {fund['beta']:.3f}\n"
            response += f"    💰 Fon Getirisi: %{fund['annual_return']:.1f}\n"
            response += f"    📊 Benchmark Getirisi: %{fund['benchmark_return']:.1f}\n"
            response += f"    📉 R²: {fund['r_squared']:.3f}\n"
            response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
            response += f"    🏷️ Tür: {fund['fund_type']}\n"
            response += f"\n"
        
        # İstatistikler
        avg_alpha = sum(f['alpha'] for f in alpha_results) / len(alpha_results)
        positive_alpha_count = sum(1 for f in alpha_results if f['alpha'] > 0)
        
        response += f"📊 ALPHA İSTATİSTİKLERİ:\n"
        response += f"   Bulunan Fon Sayısı: {len(alpha_results)}\n"
        response += f"   Pozitif Alpha: {positive_alpha_count} fon\n"
        response += f"   Ortalama Alpha: %{avg_alpha:.2f}\n"
        response += f"   En Yüksek Alpha: {alpha_results[0]['fcode']} (%{alpha_results[0]['alpha']:.2f})\n"
        
        # AI Yorumu
        if self.ai_status['openai'] or self.ai_status['ollama']:
            response += self._get_ai_commentary_for_alpha(alpha_results)
        
        return response
    
    def handle_tracking_error_analysis(self, question):
        """Tracking Error analizi - Index fonlar için"""
        print("📊 Tracking Error analiz ediliyor...")
        
        response = f"\n📊 TRACKING ERROR ANALİZİ (INDEX FONLAR)\n"
        response += f"{'='*50}\n\n"
        response += f"🎯 En düşük tracking error'a sahip index fonlar aranıyor...\n\n"
        
        # Index fonları filtrele
        index_funds = self._identify_index_funds()
        
        if not index_funds:
            return "❌ Index fon bulunamadı. Tracking error analizi yapılamıyor."
        
        tracking_error_results = []
        
        # Benchmark verilerini al
        benchmark_data = self._get_benchmark_data()
        if benchmark_data is None:
            return "❌ Benchmark verisi alınamadı."
        
        # Her index fon için tracking error hesapla
        for fcode in index_funds[:20]:
            try:
                fund_data = self.coordinator.db.get_fund_price_history(fcode, 252)
                
                if len(fund_data) >= 60:
                    # Tracking error hesapla
                    te_data = self._calculate_tracking_error(fund_data, benchmark_data)
                    
                    if te_data is not None:
                        tracking_error_results.append({
                            'fcode': fcode,
                            'tracking_error': te_data['tracking_error'],
                            'correlation': te_data['correlation'],
                            'beta': te_data['beta'],
                            'annual_return': te_data['fund_return'],
                            'benchmark_return': te_data['benchmark_return'],
                            'current_price': fund_data['price'].iloc[-1]
                        })
                
            except Exception:
                continue
        
        # Tracking error'a göre sırala (düşükten yükseğe)
        tracking_error_results.sort(key=lambda x: x['tracking_error'])
        
        if not tracking_error_results:
            return "❌ Tracking error hesaplanabilir index fon bulunamadı."
        
        # Fund details al
        for result in tracking_error_results[:10]:
            try:
                details = self.coordinator.db.get_fund_details(result['fcode'])
                result['fund_name'] = details.get('fund_name', 'N/A') if details else 'N/A'
                result['fund_type'] = details.get('fund_type', 'N/A') if details else 'N/A'
            except:
                result['fund_name'] = 'N/A'
                result['fund_type'] = 'N/A'
        
        # Sonuçları göster
        response += f"🏆 EN DÜŞÜK TRACKING ERROR'LU INDEX FONLAR:\n\n"
        
        for i, fund in enumerate(tracking_error_results[:10], 1):
            # Tracking kalitesi
            if fund['tracking_error'] < 2:
                quality = "🌟 MÜKEMMEL"
            elif fund['tracking_error'] < 5:
                quality = "🟢 ÇOK İYİ"
            elif fund['tracking_error'] < 10:
                quality = "🟡 İYİ"
            else:
                quality = "🔴 ZAYIF"
            
            response += f"{i:2d}. {fund['fcode']} - {quality}\n"
            response += f"    📊 Tracking Error: %{fund['tracking_error']:.2f} (yıllık)\n"
            response += f"    🔗 Korelasyon: {fund['correlation']:.3f}\n"
            response += f"    📈 Beta: {fund['beta']:.3f}\n"
            response += f"    💰 Fon Getirisi: %{fund['annual_return']:.1f}\n"
            response += f"    📊 Benchmark Getirisi: %{fund['benchmark_return']:.1f}\n"
            response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
            if fund['fund_name'] != 'N/A':
                response += f"    📝 Adı: {fund['fund_name'][:40]}...\n"
            response += f"\n"
        
        # İstatistikler
        avg_te = sum(f['tracking_error'] for f in tracking_error_results) / len(tracking_error_results)
        avg_correlation = sum(f['correlation'] for f in tracking_error_results) / len(tracking_error_results)
        
        response += f"📊 TRACKING ERROR İSTATİSTİKLERİ:\n"
        response += f"   Analiz Edilen Index Fon: {len(tracking_error_results)}\n"
        response += f"   Ortalama Tracking Error: %{avg_te:.2f}\n"
        response += f"   Ortalama Korelasyon: {avg_correlation:.3f}\n"
        response += f"   En İyi: {tracking_error_results[0]['fcode']} (%{tracking_error_results[0]['tracking_error']:.2f})\n"
        
        return response
    
    def handle_information_ratio_analysis(self, question):
        """Information Ratio analizi - Aktif yönetilen fonlar için"""
        print("📊 Information Ratio analiz ediliyor...")
        
        response = f"\n📊 INFORMATION RATIO ANALİZİ\n"
        response += f"{'='*50}\n\n"
        response += f"🎯 En yüksek information ratio'ya sahip aktif fonlar aranıyor...\n\n"
        
        # Benchmark verilerini al
        benchmark_data = self._get_benchmark_data()
        if benchmark_data is None:
            return "❌ Benchmark verisi alınamadı. Information ratio hesaplaması yapılamıyor."
        
        ir_results = []
        
        # Aktif fonları analiz et (index fonları hariç)
        active_managed_funds = [f for f in self.active_funds if f not in self._identify_index_funds()]
        
        for fcode in active_managed_funds[:40]:
            try:
                fund_data = self.coordinator.db.get_fund_price_history(fcode, 252)
                
                if len(fund_data) >= 60:
                    # Information ratio hesapla
                    ir_data = self._calculate_information_ratio(fund_data, benchmark_data)
                    
                    if ir_data is not None and ir_data['information_ratio'] is not None:
                        ir_results.append({
                            'fcode': fcode,
                            'information_ratio': ir_data['information_ratio'],
                            'active_return': ir_data['active_return'],
                            'tracking_error': ir_data['tracking_error'],
                            'annual_return': ir_data['fund_return'],
                            'sharpe_ratio': ir_data['sharpe_ratio'],
                            'current_price': fund_data['price'].iloc[-1]
                        })
                
            except Exception:
                continue
        
        # Information ratio'ya göre sırala (yüksekten düşüğe)
        ir_results.sort(key=lambda x: x['information_ratio'], reverse=True)
        
        if not ir_results:
            return "❌ Information ratio hesaplanabilir aktif fon bulunamadı."
        
        # Fund details al
        for result in ir_results[:10]:
            try:
                details = self.coordinator.db.get_fund_details(result['fcode'])
                result['fund_name'] = details.get('fund_name', 'N/A') if details else 'N/A'
                result['fund_type'] = details.get('fund_type', 'N/A') if details else 'N/A'
            except:
                result['fund_name'] = 'N/A'
                result['fund_type'] = 'N/A'
        
        # Sonuçları göster
        response += f"🏆 EN YÜKSEK INFORMATION RATIO'LU AKTİF FONLAR:\n\n"
        
        for i, fund in enumerate(ir_results[:10], 1):
            # IR kalitesi
            if fund['information_ratio'] > 1.0:
                quality = "🌟 ÜSTÜN"
            elif fund['information_ratio'] > 0.5:
                quality = "🟢 ÇOK İYİ"
            elif fund['information_ratio'] > 0:
                quality = "🟡 İYİ"
            else:
                quality = "🔴 ZAYIF"
            
            response += f"{i:2d}. {fund['fcode']} - {quality}\n"
            response += f"    📊 Information Ratio: {fund['information_ratio']:.3f}\n"
            response += f"    📈 Aktif Getiri: %{fund['active_return']:.2f} (yıllık)\n"
            response += f"    📉 Tracking Error: %{fund['tracking_error']:.2f}\n"
            response += f"    💰 Toplam Getiri: %{fund['annual_return']:.1f}\n"
            response += f"    ⚡ Sharpe Oranı: {fund['sharpe_ratio']:.3f}\n"
            response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
            response += f"    🏷️ Tür: {fund['fund_type']}\n"
            response += f"\n"
        
        # İstatistikler
        avg_ir = sum(f['information_ratio'] for f in ir_results) / len(ir_results)
        positive_ir_count = sum(1 for f in ir_results if f['information_ratio'] > 0)
        
        response += f"📊 INFORMATION RATIO İSTATİSTİKLERİ:\n"
        response += f"   Analiz Edilen Aktif Fon: {len(ir_results)}\n"
        response += f"   Pozitif IR: {positive_ir_count} fon\n"
        response += f"   Ortalama IR: {avg_ir:.3f}\n"
        response += f"   En Yüksek: {ir_results[0]['fcode']} ({ir_results[0]['information_ratio']:.3f})\n"
        
        # AI Yorumu
        if self.ai_status['openai'] or self.ai_status['ollama']:
            response += self._get_ai_commentary_for_ir(ir_results)
        
        return response
    
    # === YARDIMCI METODLAR ===
    
    def _get_benchmark_data(self) -> Optional[pd.DataFrame]:
        """Benchmark verilerini al (BIST100 proxy olarak)"""
        try:
            # Önce TI2 (BIST100 index fonu) dene
            benchmark_data = self.coordinator.db.get_fund_price_history('TI2', 252)
            if not benchmark_data.empty and len(benchmark_data) > 60:
                return benchmark_data
            
            # Alternatif benchmark fonları dene
            for fund in ['TKF', 'GAF', 'GEH', 'TYH']:
                benchmark_data = self.coordinator.db.get_fund_price_history(fund, 252)
                if not benchmark_data.empty and len(benchmark_data) > 60:
                    return benchmark_data
            
            # Son çare: En büyük hisse senedi fonunu benchmark olarak kullan
            print("   ⚠️ Index fon bulunamadı, alternatif benchmark aranıyor...")
            query = """
            SELECT DISTINCT f.fcode 
            FROM tefasfunds f
            JOIN tefasfunddetails d ON f.fcode = d.fcode
            WHERE d.stock > 80  -- %80+ hisse senedi
            GROUP BY f.fcode 
            ORDER BY AVG(f.fcapacity) DESC 
            LIMIT 1
            """
            result = self.coordinator.db.execute_query(query)
            if not result.empty:
                benchmark_data = self.coordinator.db.get_fund_price_history(result.iloc[0]['fcode'], 252)
                if not benchmark_data.empty:
                    print(f"   ✅ Alternatif benchmark: {result.iloc[0]['fcode']}")
                    return benchmark_data
                    
        except Exception as e:
            self.logger.error(f"Benchmark verisi alınamadı: {e}")
        
        return None
    
    def _calculate_returns(self, price_data: pd.DataFrame) -> pd.Series:
        """Günlük getirileri hesapla"""
        prices = price_data.set_index('pdate')['price'].sort_index()
        return prices.pct_change().dropna()
    
    def _annualized_return(self, returns: pd.Series) -> float:
        """Yıllık getiri hesapla"""
        if len(returns) == 0:
            return 0
        # Compound annual return
        total_return = (1 + returns).prod() - 1
        n_days = len(returns)
        return ((1 + total_return) ** (252 / n_days) - 1)
    
    def _calculate_beta(self, fund_data: pd.DataFrame, benchmark_data: pd.DataFrame) -> Optional[float]:
        """Beta katsayısını hesapla"""
        try:
            # Ortak tarihler için veri al
            fund_prices = fund_data.set_index('pdate')['price'].sort_index()
            benchmark_prices = benchmark_data.set_index('pdate')['price'].sort_index()
            
            # Ortak tarihleri bul
            common_dates = fund_prices.index.intersection(benchmark_prices.index)
            if len(common_dates) < 30:
                return None
            
            # Ortak tarihlerdeki fiyatları al
            fund_prices = fund_prices[common_dates]
            benchmark_prices = benchmark_prices[common_dates]
            
            # Günlük getiriler
            fund_returns = fund_prices.pct_change().dropna()
            benchmark_returns = benchmark_prices.pct_change().dropna()
            
            # Getiri tarihlerini tekrar eşleştir (dropna sonrası farklı olabilir)
            common_return_dates = fund_returns.index.intersection(benchmark_returns.index)
            if len(common_return_dates) < 20:
                return None
                
            fund_returns = fund_returns[common_return_dates]
            benchmark_returns = benchmark_returns[common_return_dates]
            
            # Boyutların eşit olduğundan emin ol
            if len(fund_returns) != len(benchmark_returns):
                # En kısa olanın boyutuna göre kes
                min_len = min(len(fund_returns), len(benchmark_returns))
                fund_returns = fund_returns.iloc[:min_len]
                benchmark_returns = benchmark_returns.iloc[:min_len]
            
            # Numpy array'e çevir ve NaN kontrolü yap
            fund_arr = fund_returns.values
            bench_arr = benchmark_returns.values
            
            # NaN değerleri temizle
            mask = ~(np.isnan(fund_arr) | np.isnan(bench_arr))
            fund_arr = fund_arr[mask]
            bench_arr = bench_arr[mask]
            
            if len(fund_arr) < 20:
                return None
            
            # Beta = Cov(fund, market) / Var(market)
            covariance = np.cov(fund_arr, bench_arr)[0, 1]
            benchmark_variance = np.var(bench_arr)
            
            if benchmark_variance > 0:
                beta = covariance / benchmark_variance
                # Beta'yı makul aralıkta tut
                if -5 < beta < 5:  # Makul beta aralığı
                    return beta
            
        except Exception as e:
            # Hata detayını yazdırma, sadece logla
            pass
        
        return None
    
    def _calculate_alpha(self, fund_data: pd.DataFrame, benchmark_data: pd.DataFrame) -> Optional[Dict]:
        """Alpha değerini hesapla (Jensen's Alpha)"""
        try:
            # Beta hesapla
            beta = self._calculate_beta(fund_data, benchmark_data)
            if beta is None:
                return None
            
            # Getiriler
            fund_returns = self._calculate_returns(fund_data)
            benchmark_returns = self._calculate_returns(benchmark_data)
            
            # Ortak tarihler
            common_dates = fund_returns.index.intersection(benchmark_returns.index)
            fund_returns = fund_returns[common_dates]
            benchmark_returns = benchmark_returns[common_dates]
            
            # Yıllık getiriler
            fund_annual_return = self._annualized_return(fund_returns) * 100
            benchmark_annual_return = self._annualized_return(benchmark_returns) * 100
            
            # Alpha = Fund Return - (Risk Free Rate + Beta * (Market Return - Risk Free Rate))
            alpha = fund_annual_return - (self.risk_free_rate * 100 + beta * (benchmark_annual_return - self.risk_free_rate * 100))
            
            # R-squared hesapla
            correlation = fund_returns.corr(benchmark_returns)
            r_squared = correlation ** 2
            
            return {
                'alpha': alpha,
                'beta': beta,
                'fund_return': fund_annual_return,
                'benchmark_return': benchmark_annual_return,
                'r_squared': r_squared
            }
            
        except Exception as e:
            self.logger.error(f"Alpha hesaplama hatası: {e}")
        
        return None
    
    def _calculate_tracking_error(self, fund_data: pd.DataFrame, benchmark_data: pd.DataFrame) -> Optional[Dict]:
        """Tracking Error hesapla"""
        try:
            # Getiriler
            fund_returns = self._calculate_returns(fund_data)
            benchmark_returns = self._calculate_returns(benchmark_data)
            
            # Ortak tarihler
            common_dates = fund_returns.index.intersection(benchmark_returns.index)
            fund_returns = fund_returns[common_dates]
            benchmark_returns = benchmark_returns[common_dates]
            
            # Tracking error = Std(Fund Return - Benchmark Return)
            active_returns = fund_returns - benchmark_returns
            tracking_error = active_returns.std() * np.sqrt(252) * 100  # Yıllık %
            
            # Diğer metrikler
            correlation = fund_returns.corr(benchmark_returns)
            beta = self._calculate_beta(fund_data, benchmark_data)
            
            return {
                'tracking_error': tracking_error,
                'correlation': correlation,
                'beta': beta if beta else 1.0,
                'fund_return': self._annualized_return(fund_returns) * 100,
                'benchmark_return': self._annualized_return(benchmark_returns) * 100
            }
            
        except Exception as e:
            self.logger.error(f"Tracking error hesaplama hatası: {e}")
        
        return None
    
    def _calculate_information_ratio(self, fund_data: pd.DataFrame, benchmark_data: pd.DataFrame) -> Optional[Dict]:
        """Information Ratio hesapla"""
        try:
            # Tracking error hesapla
            te_data = self._calculate_tracking_error(fund_data, benchmark_data)
            if te_data is None or te_data['tracking_error'] == 0:
                return None
            
            # Active return
            active_return = te_data['fund_return'] - te_data['benchmark_return']
            
            # Information Ratio = Active Return / Tracking Error
            information_ratio = active_return / te_data['tracking_error']
            
            # Sharpe ratio da hesapla
            fund_returns = self._calculate_returns(fund_data)
            fund_volatility = fund_returns.std() * np.sqrt(252)
            sharpe_ratio = (te_data['fund_return'] - self.risk_free_rate * 100) / (fund_volatility * 100)
            
            return {
                'information_ratio': information_ratio,
                'active_return': active_return,
                'tracking_error': te_data['tracking_error'],
                'fund_return': te_data['fund_return'],
                'sharpe_ratio': sharpe_ratio
            }
            
        except Exception as e:
            self.logger.error(f"Information ratio hesaplama hatası: {e}")
        
        return None
    
    def _identify_index_funds(self) -> List[str]:
        """Index fonları tespit et"""
        index_keywords = ['index', 'endeks', 'bist', 'xbank', 'xu100', 'xu030']
        index_funds = []
        
        try:
            # Fund details'den index fonları bul
            all_details = self.coordinator.db.get_all_fund_details()
            
            for _, fund in all_details.iterrows():
                fund_name = str(fund.get('fund_name', '')).lower()
                fund_type = str(fund.get('fund_type', '')).lower()
                
                if any(keyword in fund_name or keyword in fund_type for keyword in index_keywords):
                    index_funds.append(fund['fcode'])
            
            # Bilinen index fonları ekle
            known_index_funds = ['TI2', 'TKF', 'GAF', 'GEH', 'TYH', 'TTE']
            for fund in known_index_funds:
                if fund not in index_funds:
                    index_funds.append(fund)
                    
        except Exception as e:
            self.logger.error(f"Index fon tespiti hatası: {e}")
        
        return index_funds
    
    def _get_ai_commentary_for_beta(self, beta_results: List[Dict], comparison: str, threshold: float) -> str:
        """Beta analizi için AI yorumu"""
        response = "\n🤖 AI YORUMLARI:\n"
        response += "="*30 + "\n"
        
        # En iyi 5 fonu al
        top_funds = beta_results[:5]
        
        prompt = f"""
        Beta katsayısı {comparison} {threshold} olan fonlar analiz edildi.
        
        En iyi 5 fon:
        {', '.join([f"{f['fcode']} (Beta: {f['beta']:.3f})" for f in top_funds])}
        
        Ortalama beta: {sum(f['beta'] for f in beta_results) / len(beta_results):.3f}
        Ortalama getiri: %{sum(f['annual_return'] for f in beta_results) / len(beta_results):.1f}
        
        Bu fonların risk profili ve yatırımcı için uygunluğu hakkında kısa yorum yap (max 150 kelime).
        """
        
        if self.ai_status['openai']:
            try:
                openai_comment = self.coordinator.ai_analyzer.query_openai(
                    prompt, "Sen finansal risk analisti uzmanısın."
                )
                response += f"\n📱 OpenAI Yorumu:\n{openai_comment}\n"
            except:
                pass
        
        if self.ai_status['ollama']:
            try:
                ollama_comment = self.coordinator.ai_analyzer.query_ollama(
                    prompt, "Sen finansal risk analisti uzmanısın."
                )
                response += f"\n🦙 Ollama Yorumu:\n{ollama_comment}\n"
            except:
                pass
        
        return response
    
    def _get_ai_commentary_for_alpha(self, alpha_results: List[Dict]) -> str:
        """Alpha analizi için AI yorumu"""
        response = "\n🤖 AI ALPHA ANALİZİ:\n"
        response += "="*30 + "\n"
        
        positive_count = sum(1 for f in alpha_results if f['alpha'] > 0)
        
        prompt = f"""
        Alpha analizi sonuçları:
        
        Toplam fon: {len(alpha_results)}
        Pozitif alpha: {positive_count} fon
        En yüksek alpha: %{alpha_results[0]['alpha']:.2f} ({alpha_results[0]['fcode']})
        Ortalama alpha: %{sum(f['alpha'] for f in alpha_results) / len(alpha_results):.2f}
        
        Bu sonuçların anlamı ve aktif fon yönetiminin başarısı hakkında yorum yap (max 150 kelime).
        """
        
        if self.ai_status['openai']:
            try:
                openai_comment = self.coordinator.ai_analyzer.query_openai(
                    prompt, "Sen portföy yönetimi uzmanısın."
                )
                response += f"\n📱 OpenAI Yorumu:\n{openai_comment}\n"
            except:
                pass
        
        return response
    
    def _get_ai_commentary_for_ir(self, ir_results: List[Dict]) -> str:
        """Information Ratio analizi için AI yorumu"""
        response = "\n🤖 AI INFORMATION RATIO ANALİZİ:\n"
        response += "="*30 + "\n"
        
        top_3 = ir_results[:3]
        
        prompt = f"""
        Information Ratio analizi sonuçları:
        
        En iyi 3 fon:
        {', '.join([f"{f['fcode']} (IR: {f['information_ratio']:.3f})" for f in top_3])}
        
        Ortalama IR: {sum(f['information_ratio'] for f in ir_results) / len(ir_results):.3f}
        IR > 0.5 olan fon sayısı: {sum(1 for f in ir_results if f['information_ratio'] > 0.5)}
        
        Aktif fon yönetiminin risk-ayarlı performansı hakkında yorum yap (max 150 kelime).
        """
        
        if self.ai_status['ollama']:
            try:
                ollama_comment = self.coordinator.ai_analyzer.query_ollama(
                    prompt, "Sen aktif portföy yönetimi uzmanısın."
                )
                response += f"\n🦙 Ollama Yorumu:\n{ollama_comment}\n"
            except:
                pass
        
        return response