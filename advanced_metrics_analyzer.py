# advanced_metrics_analyzer.py
"""
İleri Finansal Metrikler Analizi - Risk Assessment Entegre Edilmiş
Beta, Alpha, Tracking Error, Information Ratio hesaplamaları
Risk değerlendirmesi ile güvenli metrik analizleri
"""

import re
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
from scipy import stats
from risk_assessment import RiskAssessment

class AdvancedMetricsAnalyzer:
    """İleri finansal metrikler için analiz sınıfı - Risk Kontrolü İle"""
    
    def __init__(self, coordinator, active_funds, ai_status):
        self.coordinator = coordinator
        self.active_funds = active_funds
        self.ai_status = ai_status
        self.logger = logging.getLogger(__name__)
        
        # Benchmark olarak kullanılacak index fonları (BIST100 vb. temsil eden)
        self.benchmark_funds = ['TI2', 'TKF', 'GAF']  # Örnek index fonlar
        self.risk_free_rate = 0.15  # %15 risksiz faiz oranı (Türkiye için)
        
    def handle_beta_analysis(self, question):
        """Beta katsayısı analizi - SQL ve Python hibrit + RİSK KONTROLÜ"""
        print("📊 Beta katsayısı analiz ediliyor (risk kontrolü ile)...")
        
        # Beta eşiğini belirle
        beta_threshold = 1.0
        if "düşük" in question.lower() or "altında" in question.lower():
            comparison = "<"
        else:
            comparison = ">"
            
        response = f"\n📊 BETA KATSAYISI ANALİZİ (RİSK KONTROLÜ İLE)\n"
        response += f"{'='*60}\n\n"
        response += f"🎯 Beta {comparison} {beta_threshold} olan fonlar aranıyor...\n"
        response += f"🛡️ Risk değerlendirmesi aktif\n\n"
        
        # Önce benchmark verilerini al
        benchmark_data = self._get_benchmark_data()
        if benchmark_data is None:
            return "❌ Benchmark verisi alınamadı. Beta hesaplaması yapılamıyor."
        
        beta_results = []
        high_risk_funds = []
        blocked_extreme_funds = []
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
        
        # Her fon için beta hesapla + Risk değerlendirmesi
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
                            
                            # Risk değerlendirmesi
                            risk_data = self._get_fund_risk_data(fcode)
                            risk_assessment = None
                            risk_level = 'UNKNOWN'
                            
                            if risk_data:
                                risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                                risk_level = risk_assessment['risk_level']
                            
                            fund_result = {
                                'fcode': fcode,
                                'beta': beta,
                                'annual_return': annual_return,
                                'volatility': volatility,
                                'current_price': fund_data['price'].iloc[-1],
                                'risk_level': risk_level,
                                'risk_factors': risk_assessment['risk_factors'] if risk_assessment else [],
                                'risk_score': risk_assessment['risk_score'] if risk_assessment else 0
                            }
                            
                            # Risk seviyesine göre kategorize et
                            if risk_level == 'EXTREME':
                                blocked_extreme_funds.append(fund_result)
                            elif risk_level in ['HIGH']:
                                high_risk_funds.append(fund_result)
                                beta_results.append(fund_result)
                            else:
                                beta_results.append(fund_result)
                
            except Exception as e:
                continue
        
        # Sonuçları sırala
        beta_results.sort(key=lambda x: x['beta'])
        
        if not beta_results and not blocked_extreme_funds:
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
        
        # Sonuçları göster - RİSK BİLGİLERİ İLE
        response += f"🏆 BETA {comparison} {beta_threshold} OLAN FONLAR (Risk-Filtreli):\n\n"
        
        for i, fund in enumerate(beta_results[:10], 1):
            # Beta profili
            if fund['beta'] < 0.5:
                beta_profile = "🟢 ÇOK SAVUNMACI"
            elif fund['beta'] < 0.8:
                beta_profile = "🟡 SAVUNMACI"
            elif fund['beta'] < 1.2:
                beta_profile = "🟠 DENGELİ"
            elif fund['beta'] < 1.5:
                beta_profile = "🔴 AGRESİF"
            else:
                beta_profile = "🔥 ÇOK AGRESİF"
            
            # Risk göstergesi
            risk_indicator = self._get_risk_indicator(fund['risk_level'])
            
            response += f"{i:2d}. {fund['fcode']} - {beta_profile} {risk_indicator}\n"
            response += f"    📊 Beta: {fund['beta']:.3f}\n"
            response += f"    📈 Yıllık Getiri: %{fund['annual_return']:.1f}\n"
            response += f"    📉 Volatilite: %{fund['volatility']:.1f}\n"
            response += f"    🛡️ Risk Seviyesi: {fund['risk_level']}\n"
            response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
            response += f"    🏷️ Tür: {fund['fund_type']}\n"
            
            # Risk faktörleri varsa göster
            if fund['risk_factors'] and fund['risk_level'] in ['HIGH', 'EXTREME']:
                top_risks = [f['factor'] for f in fund['risk_factors'][:2]]
                response += f"    ⚠️ Risk Faktörleri: {', '.join(top_risks)}\n"
            
            if fund['fund_name'] != 'N/A':
                response += f"    📝 Adı: {fund['fund_name'][:40]}...\n"
            response += f"\n"
        
        # YÜKSEK RİSKLİ FONLAR UYARISI
        if high_risk_funds:
            response += f"🟠 YÜKSEK RİSKLİ BETA FONLARI ({len(high_risk_funds)} adet):\n"
            response += f"   ⚠️ Bu fonlar yüksek risk taşımaktadır!\n\n"
            
            for i, fund in enumerate(high_risk_funds[:3], 1):
                risk_factors = [f['factor'] for f in fund['risk_factors'][:2]]
                response += f"   {i}. {fund['fcode']} - Beta: {fund['beta']:.3f}\n"
                response += f"      ⚠️ Risk: {', '.join(risk_factors)}\n"
            response += f"\n"
        
        # EXTREME RİSKLİ (ENGELLENEN) FONLAR
        if blocked_extreme_funds:
            response += f"🔴 EXTREME RİSKLİ BETA FONLARI - ÖNERİLMİYOR ({len(blocked_extreme_funds)} adet):\n"
            response += f"   ❌ Bu fonlar extreme risk taşıdığı için analiz dışı bırakıldı!\n\n"
            
            for i, fund in enumerate(blocked_extreme_funds[:3], 1):
                top_risk_factors = [f['factor'] for f in fund['risk_factors'][:2]]
                response += f"   {i}. {fund['fcode']} - Beta: {fund['beta']:.3f} - ENGELLENEN\n"
                response += f"      🚨 Sebepler: {', '.join(top_risk_factors)}\n"
            response += f"\n"
        
        # İstatistikler - güvenli fonlar dahil
        safe_funds = [f for f in beta_results if f['risk_level'] in ['LOW', 'MEDIUM']]
        
        if beta_results:
            avg_beta = sum(f['beta'] for f in beta_results) / len(beta_results)
            avg_return = sum(f['annual_return'] for f in beta_results) / len(beta_results)
            
            response += f"📊 BETA İSTATİSTİKLERİ (Risk-Filtreli):\n"
            response += f"   🔢 Toplam Bulunan: {len(beta_results) + len(blocked_extreme_funds)} fon\n"
            response += f"   ✅ Güvenli/Orta: {len(safe_funds)} fon\n"
            response += f"   🟠 Yüksek Risk: {len(high_risk_funds)} fon\n"
            response += f"   🔴 Extreme (Engellenen): {len(blocked_extreme_funds)} fon\n"
            response += f"   📊 Ortalama Beta: {avg_beta:.3f}\n"
            response += f"   📈 Ortalama Getiri: %{avg_return:.1f}\n"
            
            if safe_funds:
                safest_beta = min(safe_funds, key=lambda x: abs(x['beta'] - 1))
                response += f"   🛡️ En Güvenli: {safest_beta['fcode']} (Beta: {safest_beta['beta']:.3f}, {safest_beta['risk_level']})\n"
        
        # AI Yorumu - Risk dahil
        if hasattr(self.coordinator, 'ai_provider') and self.coordinator.ai_provider.is_available():
            response += self._get_ai_commentary_for_beta_with_risk(beta_results, blocked_extreme_funds, comparison, beta_threshold)
        
        return response
    
    def handle_alpha_analysis(self, question):
        """Alpha değeri analizi - RİSK KONTROLÜ İLE"""
        print("📊 Alpha değeri analiz ediliyor (risk kontrolü ile)...")
        
        # Alpha koşulunu belirle
        is_positive = "pozitif" in question.lower() or "yüksek" in question.lower()
        
        response = f"\n📊 ALPHA DEĞERİ ANALİZİ (RİSK KONTROLÜ İLE)\n"
        response += f"{'='*60}\n\n"
        response += f"🎯 {'Pozitif' if is_positive else 'Negatif'} Alpha değerine sahip fonlar aranıyor...\n"
        response += f"🛡️ Risk değerlendirmesi aktif\n\n"
        
        # Benchmark verilerini al
        benchmark_data = self._get_benchmark_data()
        if benchmark_data is None:
            return "❌ Benchmark verisi alınamadı. Alpha hesaplaması yapılamıyor."
        
        alpha_results = []
        high_risk_funds = []
        blocked_extreme_funds = []
        
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
                            
                            # Risk değerlendirmesi
                            risk_data = self._get_fund_risk_data(fcode)
                            risk_assessment = None
                            risk_level = 'UNKNOWN'
                            
                            if risk_data:
                                risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                                risk_level = risk_assessment['risk_level']
                            
                            fund_result = {
                                'fcode': fcode,
                                'alpha': alpha,
                                'beta': alpha_data['beta'],
                                'annual_return': alpha_data['fund_return'],
                                'benchmark_return': alpha_data['benchmark_return'],
                                'r_squared': alpha_data['r_squared'],
                                'current_price': fund_data['price'].iloc[-1],
                                'risk_level': risk_level,
                                'risk_factors': risk_assessment['risk_factors'] if risk_assessment else [],
                                'risk_score': risk_assessment['risk_score'] if risk_assessment else 0
                            }
                            
                            # Risk seviyesine göre kategorize et
                            if risk_level == 'EXTREME':
                                blocked_extreme_funds.append(fund_result)
                            elif risk_level in ['HIGH']:
                                high_risk_funds.append(fund_result)
                                alpha_results.append(fund_result)
                            else:
                                alpha_results.append(fund_result)
                
            except Exception:
                continue
        
        # Alpha'ya göre sırala
        alpha_results.sort(key=lambda x: x['alpha'], reverse=True)
        
        if not alpha_results and not blocked_extreme_funds:
            return f"❌ {'Pozitif' if is_positive else 'Negatif'} Alpha değerine sahip güvenli fon bulunamadı."
        
        # Fund details al
        for result in alpha_results[:10]:
            try:
                details = self.coordinator.db.get_fund_details(result['fcode'])
                result['fund_name'] = details.get('fund_name', 'N/A') if details else 'N/A'
                result['fund_type'] = details.get('fund_type', 'N/A') if details else 'N/A'
            except:
                result['fund_name'] = 'N/A'
                result['fund_type'] = 'N/A'
        
        # Sonuçları göster - RİSK BİLGİLERİ İLE
        response += f"🏆 EN YÜKSEK ALPHA DEĞERLERİ (Risk-Filtreli):\n\n"
        
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
            
            # Risk göstergesi
            risk_indicator = self._get_risk_indicator(fund['risk_level'])
            
            response += f"{i:2d}. {fund['fcode']} - {performance} {risk_indicator}\n"
            response += f"    📊 Alpha: %{fund['alpha']:.2f} (yıllık)\n"
            response += f"    📈 Beta: {fund['beta']:.3f}\n"
            response += f"    💰 Fon Getirisi: %{fund['annual_return']:.1f}\n"
            response += f"    📊 Benchmark Getirisi: %{fund['benchmark_return']:.1f}\n"
            response += f"    📉 R²: {fund['r_squared']:.3f}\n"
            response += f"    🛡️ Risk Seviyesi: {fund['risk_level']}\n"
            response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
            response += f"    🏷️ Tür: {fund['fund_type']}\n"
            
            # Risk faktörleri varsa göster
            if fund['risk_factors'] and fund['risk_level'] in ['HIGH', 'EXTREME']:
                top_risks = [f['factor'] for f in fund['risk_factors'][:2]]
                response += f"    ⚠️ Risk Faktörleri: {', '.join(top_risks)}\n"
            
            response += f"\n"
        
        # YÜKSEK RİSKLİ ALPHA FONLARI
        if high_risk_funds:
            response += f"🟠 YÜKSEK RİSKLİ ALPHA FONLARI ({len(high_risk_funds)} adet):\n"
            response += f"   ⚠️ Yüksek alpha ama aynı zamanda yüksek risk!\n\n"
            
            for i, fund in enumerate(high_risk_funds[:3], 1):
                response += f"   {i}. {fund['fcode']} - Alpha: %{fund['alpha']:.2f}\n"
            response += f"\n"
        
        # EXTREME RİSKLİ (ENGELLENEN) ALPHA FONLARI
        if blocked_extreme_funds:
            response += f"🔴 EXTREME RİSKLİ ALPHA FONLARI - ÖNERİLMİYOR ({len(blocked_extreme_funds)} adet):\n"
            response += f"   ❌ Yüksek alpha olsa bile extreme risk nedeniyle önerilmiyor!\n\n"
            
            for i, fund in enumerate(blocked_extreme_funds[:3], 1):
                response += f"   {i}. {fund['fcode']} - Alpha: %{fund['alpha']:.2f} - ENGELLENEN\n"
            response += f"\n"
        
        # İstatistikler - güvenli fonlar dahil
        safe_funds = [f for f in alpha_results if f['risk_level'] in ['LOW', 'MEDIUM']]
        
        if alpha_results:
            avg_alpha = sum(f['alpha'] for f in alpha_results) / len(alpha_results)
            positive_alpha_count = sum(1 for f in alpha_results if f['alpha'] > 0)
            
            response += f"📊 ALPHA İSTATİSTİKLERİ (Risk-Filtreli):\n"
            response += f"   🔢 Toplam Bulunan: {len(alpha_results) + len(blocked_extreme_funds)} fon\n"
            response += f"   ✅ Güvenli Pozitif Alpha: {len([f for f in safe_funds if f['alpha'] > 0])} fon\n"
            response += f"   🟠 Riskli Alpha: {len(high_risk_funds)} fon\n"
            response += f"   🔴 Extreme (Engellenen): {len(blocked_extreme_funds)} fon\n"
            response += f"   📊 Ortalama Alpha: %{avg_alpha:.2f}\n"
            response += f"   📈 Pozitif Alpha: {positive_alpha_count} fon\n"
            
            if safe_funds and any(f['alpha'] > 0 for f in safe_funds):
                best_safe = max([f for f in safe_funds if f['alpha'] > 0], key=lambda x: x['alpha'])
                response += f"   🛡️ En Güvenli Pozitif: {best_safe['fcode']} (Alpha: %{best_safe['alpha']:.2f}, {best_safe['risk_level']})\n"
        
        # AI Yorumu - Risk dahil
        if hasattr(self.coordinator, 'ai_provider') and self.coordinator.ai_provider.is_available():
            response += self._get_ai_commentary_for_alpha_with_risk(alpha_results, blocked_extreme_funds)
        
        return response
    
    def handle_tracking_error_analysis(self, question):
        """Tracking Error analizi - Index fonlar için + RİSK KONTROLÜ"""
        print("📊 Tracking Error analiz ediliyor (risk kontrolü ile)...")
        
        response = f"\n📊 TRACKING ERROR ANALİZİ (INDEX FONLAR - RİSK KONTROLÜ İLE)\n"
        response += f"{'='*70}\n\n"
        response += f"🎯 En düşük tracking error'a sahip index fonlar aranıyor...\n"
        response += f"🛡️ Risk değerlendirmesi aktif\n\n"
        
        # Index fonları filtrele
        index_funds = self._identify_index_funds()
        
        if not index_funds:
            return "❌ Index fon bulunamadı. Tracking error analizi yapılamıyor."
        
        tracking_error_results = []
        high_risk_funds = []
        blocked_extreme_funds = []
        
        # Benchmark verilerini al
        benchmark_data = self._get_benchmark_data()
        if benchmark_data is None:
            return "❌ Benchmark verisi alınamadı."
        
        # Her index fon için tracking error hesapla + Risk kontrolü
        for fcode in index_funds[:20]:
            try:
                fund_data = self.coordinator.db.get_fund_price_history(fcode, 252)
                
                if len(fund_data) >= 60:
                    # Tracking error hesapla
                    te_data = self._calculate_tracking_error(fund_data, benchmark_data)
                    
                    if te_data is not None:
                        # Risk değerlendirmesi
                        risk_data = self._get_fund_risk_data(fcode)
                        risk_assessment = None
                        risk_level = 'UNKNOWN'
                        
                        if risk_data:
                            risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                            risk_level = risk_assessment['risk_level']
                        
                        fund_result = {
                            'fcode': fcode,
                            'tracking_error': te_data['tracking_error'],
                            'correlation': te_data['correlation'],
                            'beta': te_data['beta'],
                            'annual_return': te_data['fund_return'],
                            'benchmark_return': te_data['benchmark_return'],
                            'current_price': fund_data['price'].iloc[-1],
                            'risk_level': risk_level,
                            'risk_factors': risk_assessment['risk_factors'] if risk_assessment else [],
                            'risk_score': risk_assessment['risk_score'] if risk_assessment else 0
                        }
                        
                        # Risk seviyesine göre kategorize et
                        if risk_level == 'EXTREME':
                            blocked_extreme_funds.append(fund_result)
                        elif risk_level in ['HIGH']:
                            high_risk_funds.append(fund_result)
                            tracking_error_results.append(fund_result)
                        else:
                            tracking_error_results.append(fund_result)
                
            except Exception:
                continue
        
        # Tracking error'a göre sırala (düşükten yükseğe)
        tracking_error_results.sort(key=lambda x: x['tracking_error'])
        
        if not tracking_error_results and not blocked_extreme_funds:
            return "❌ Tracking error hesaplanabilir güvenli index fon bulunamadı."
        
        # Fund details al
        for result in tracking_error_results[:10]:
            try:
                details = self.coordinator.db.get_fund_details(result['fcode'])
                result['fund_name'] = details.get('fund_name', 'N/A') if details else 'N/A'
                result['fund_type'] = details.get('fund_type', 'N/A') if details else 'N/A'
            except:
                result['fund_name'] = 'N/A'
                result['fund_type'] = 'N/A'
        
        # Sonuçları göster - RİSK BİLGİLERİ İLE
        response += f"🏆 EN DÜŞÜK TRACKING ERROR'LU INDEX FONLAR (Risk-Filtreli):\n\n"
        
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
            
            # Risk göstergesi
            risk_indicator = self._get_risk_indicator(fund['risk_level'])
            
            response += f"{i:2d}. {fund['fcode']} - {quality} {risk_indicator}\n"
            response += f"    📊 Tracking Error: %{fund['tracking_error']:.2f} (yıllık)\n"
            response += f"    🔗 Korelasyon: {fund['correlation']:.3f}\n"
            response += f"    📈 Beta: {fund['beta']:.3f}\n"
            response += f"    💰 Fon Getirisi: %{fund['annual_return']:.1f}\n"
            response += f"    📊 Benchmark Getirisi: %{fund['benchmark_return']:.1f}\n"
            response += f"    🛡️ Risk Seviyesi: {fund['risk_level']}\n"
            response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
            
            # Risk faktörleri varsa göster
            if fund['risk_factors'] and fund['risk_level'] in ['HIGH', 'EXTREME']:
                top_risks = [f['factor'] for f in fund['risk_factors'][:2]]
                response += f"    ⚠️ Risk Faktörleri: {', '.join(top_risks)}\n"
            
            if fund['fund_name'] != 'N/A':
                response += f"    📝 Adı: {fund['fund_name'][:40]}...\n"
            response += f"\n"
        
        # YÜKSEK RİSKLİ INDEX FONLARI
        if high_risk_funds:
            response += f"🟠 YÜKSEK RİSKLİ INDEX FONLARI ({len(high_risk_funds)} adet):\n"
            response += f"   ⚠️ Düşük tracking error ama yüksek risk!\n\n"
            
            for i, fund in enumerate(high_risk_funds[:3], 1):
                response += f"   {i}. {fund['fcode']} - TE: %{fund['tracking_error']:.2f}\n"
            response += f"\n"
        
        # EXTREME RİSKLİ (ENGELLENEN) INDEX FONLARI
        if blocked_extreme_funds:
            response += f"🔴 EXTREME RİSKLİ INDEX FONLARI - ÖNERİLMİYOR ({len(blocked_extreme_funds)} adet):\n"
            response += f"   ❌ Index fon olsa bile extreme risk nedeniyle önerilmiyor!\n\n"
            
            for i, fund in enumerate(blocked_extreme_funds[:3], 1):
                response += f"   {i}. {fund['fcode']} - TE: %{fund['tracking_error']:.2f} - ENGELLENEN\n"
            response += f"\n"
        
        # İstatistikler - güvenli fonlar dahil
        safe_funds = [f for f in tracking_error_results if f['risk_level'] in ['LOW', 'MEDIUM']]
        
        if tracking_error_results:
            avg_te = sum(f['tracking_error'] for f in tracking_error_results) / len(tracking_error_results)
            avg_correlation = sum(f['correlation'] for f in tracking_error_results) / len(tracking_error_results)
            
            response += f"📊 TRACKING ERROR İSTATİSTİKLERİ (Risk-Filtreli):\n"
            response += f"   🔢 Analiz Edilen: {len(tracking_error_results) + len(blocked_extreme_funds)} index fon\n"
            response += f"   ✅ Güvenli Index: {len(safe_funds)} fon\n"
            response += f"   🟠 Riskli Index: {len(high_risk_funds)} fon\n"
            response += f"   🔴 Extreme (Engellenen): {len(blocked_extreme_funds)} fon\n"
            response += f"   📊 Ortalama Tracking Error: %{avg_te:.2f}\n"
            response += f"   🔗 Ortalama Korelasyon: {avg_correlation:.3f}\n"
            
            if safe_funds:
                best_safe = min(safe_funds, key=lambda x: x['tracking_error'])
                response += f"   🛡️ En Güvenli En İyi: {best_safe['fcode']} (TE: %{best_safe['tracking_error']:.2f}, {best_safe['risk_level']})\n"
        
        return response
    
    def handle_information_ratio_analysis(self, question):
        """Information Ratio analizi - Aktif yönetilen fonlar için + RİSK KONTROLÜ"""
        print("📊 Information Ratio analiz ediliyor (risk kontrolü ile)...")
        
        response = f"\n📊 INFORMATION RATIO ANALİZİ (RİSK KONTROLÜ İLE)\n"
        response += f"{'='*60}\n\n"
        response += f"🎯 En yüksek information ratio'ya sahip aktif fonlar aranıyor...\n"
        response += f"🛡️ Risk değerlendirmesi aktif\n\n"
        
        # Benchmark verilerini al
        benchmark_data = self._get_benchmark_data()
        if benchmark_data is None:
            return "❌ Benchmark verisi alınamadı. Information ratio hesaplaması yapılamıyor."
        
        ir_results = []
        high_risk_funds = []
        blocked_extreme_funds = []
        
        # Aktif fonları analiz et (index fonları hariç)
        active_managed_funds = [f for f in self.active_funds if f not in self._identify_index_funds()]
        
        for fcode in active_managed_funds[:40]:
            try:
                fund_data = self.coordinator.db.get_fund_price_history(fcode, 252)
                
                if len(fund_data) >= 60:
                    # Information ratio hesapla
                    ir_data = self._calculate_information_ratio(fund_data, benchmark_data)
                    
                    if ir_data is not None and ir_data['information_ratio'] is not None:
                        # Risk değerlendirmesi
                        risk_data = self._get_fund_risk_data(fcode)
                        risk_assessment = None
                        risk_level = 'UNKNOWN'
                        
                        if risk_data:
                            risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                            risk_level = risk_assessment['risk_level']
                        
                        fund_result = {
                            'fcode': fcode,
                            'information_ratio': ir_data['information_ratio'],
                            'active_return': ir_data['active_return'],
                            'tracking_error': ir_data['tracking_error'],
                            'annual_return': ir_data['fund_return'],
                            'sharpe_ratio': ir_data['sharpe_ratio'],
                            'current_price': fund_data['price'].iloc[-1],
                            'risk_level': risk_level,
                            'risk_factors': risk_assessment['risk_factors'] if risk_assessment else [],
                            'risk_score': risk_assessment['risk_score'] if risk_assessment else 0
                        }
                        
                        # Risk seviyesine göre kategorize et
                        if risk_level == 'EXTREME':
                            blocked_extreme_funds.append(fund_result)
                        elif risk_level in ['HIGH']:
                            high_risk_funds.append(fund_result)
                            ir_results.append(fund_result)
                        else:
                            ir_results.append(fund_result)
                
            except Exception:
                continue
        
        # Information ratio'ya göre sırala (yüksekten düşüğe)
        ir_results.sort(key=lambda x: x['information_ratio'], reverse=True)
        
        if not ir_results and not blocked_extreme_funds:
            return "❌ Information ratio hesaplanabilir güvenli aktif fon bulunamadı."
        
        # Fund details al
        for result in ir_results[:10]:
            try:
                details = self.coordinator.db.get_fund_details(result['fcode'])
                result['fund_name'] = details.get('fund_name', 'N/A') if details else 'N/A'
                result['fund_type'] = details.get('fund_type', 'N/A') if details else 'N/A'
            except:
                result['fund_name'] = 'N/A'
                result['fund_type'] = 'N/A'
        
        # Sonuçları göster - RİSK BİLGİLERİ İLE
        response += f"🏆 EN YÜKSEK INFORMATION RATIO'LU AKTİF FONLAR (Risk-Filtreli):\n\n"
        
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
            
            # Risk göstergesi
            risk_indicator = self._get_risk_indicator(fund['risk_level'])
            
            response += f"{i:2d}. {fund['fcode']} - {quality} {risk_indicator}\n"
            response += f"    📊 Information Ratio: {fund['information_ratio']:.3f}\n"
            response += f"    📈 Aktif Getiri: %{fund['active_return']:.2f} (yıllık)\n"
            response += f"    📉 Tracking Error: %{fund['tracking_error']:.2f}\n"
            response += f"    💰 Toplam Getiri: %{fund['annual_return']:.1f}\n"
            response += f"    ⚡ Sharpe Oranı: {fund['sharpe_ratio']:.3f}\n"
            response += f"    🛡️ Risk Seviyesi: {fund['risk_level']}\n"
            response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
            response += f"    🏷️ Tür: {fund['fund_type']}\n"
            
            # Risk faktörleri varsa göster
            if fund['risk_factors'] and fund['risk_level'] in ['HIGH', 'EXTREME']:
                top_risks = [f['factor'] for f in fund['risk_factors'][:2]]
                response += f"    ⚠️ Risk Faktörleri: {', '.join(top_risks)}\n"
            
            response += f"\n"
        
        # YÜKSEK RİSKLİ IR FONLARI
        if high_risk_funds:
            response += f"🟠 YÜKSEK RİSKLİ IR FONLARI ({len(high_risk_funds)} adet):\n"
            response += f"   ⚠️ Yüksek IR ama aynı zamanda yüksek risk!\n\n"
            
            for i, fund in enumerate(high_risk_funds[:3], 1):
                response += f"   {i}. {fund['fcode']} - IR: {fund['information_ratio']:.3f}\n"
            response += f"\n"
        
        # EXTREME RİSKLİ (ENGELLENEN) IR FONLARI
        if blocked_extreme_funds:
            response += f"🔴 EXTREME RİSKLİ IR FONLARI - ÖNERİLMİYOR ({len(blocked_extreme_funds)} adet):\n"
            response += f"   ❌ Yüksek IR olsa bile extreme risk nedeniyle önerilmiyor!\n\n"
            
            for i, fund in enumerate(blocked_extreme_funds[:3], 1):
                response += f"   {i}. {fund['fcode']} - IR: {fund['information_ratio']:.3f} - ENGELLENEN\n"
            response += f"\n"
        
        # İstatistikler - güvenli fonlar dahil
        safe_funds = [f for f in ir_results if f['risk_level'] in ['LOW', 'MEDIUM']]
        
        if ir_results:
            avg_ir = sum(f['information_ratio'] for f in ir_results) / len(ir_results)
            positive_ir_count = sum(1 for f in ir_results if f['information_ratio'] > 0)
            
            response += f"📊 INFORMATION RATIO İSTATİSTİKLERİ (Risk-Filtreli):\n"
            response += f"   🔢 Analiz Edilen: {len(ir_results) + len(blocked_extreme_funds)} aktif fon\n"
            response += f"   ✅ Güvenli Pozitif IR: {len([f for f in safe_funds if f['information_ratio'] > 0])} fon\n"
            response += f"   🟠 Riskli IR: {len(high_risk_funds)} fon\n"
            response += f"   🔴 Extreme (Engellenen): {len(blocked_extreme_funds)} fon\n"
            response += f"   📊 Ortalama IR: {avg_ir:.3f}\n"
            response += f"   📈 Pozitif IR: {positive_ir_count} fon\n"
            
            if safe_funds and any(f['information_ratio'] > 0 for f in safe_funds):
                best_safe = max([f for f in safe_funds if f['information_ratio'] > 0], key=lambda x: x['information_ratio'])
                response += f"   🛡️ En Güvenli En İyi: {best_safe['fcode']} (IR: {best_safe['information_ratio']:.3f}, {best_safe['risk_level']})\n"
        
        # AI Yorumu - Risk dahil
        if hasattr(self.coordinator, 'ai_provider') and self.coordinator.ai_provider.is_available():
            response += self._get_ai_commentary_for_ir_with_risk(ir_results, blocked_extreme_funds)
        
        return response
    
    def handle_sharpe_ratio_analysis(self, question):
        """Sharpe Oranı analizi - RİSK KONTROLÜ İLE"""
        print("📊 Sharpe oranı analiz ediliyor (risk kontrolü ile)...")
        
        # Sharpe threshold belirleme
        threshold_match = re.search(r'(\d+\.?\d*)', question)
        sharpe_threshold = float(threshold_match.group(1)) if threshold_match else 0.5
        
        response = f"\n📊 SHARPE ORANI ANALİZİ (RİSK KONTROLÜ İLE)\n"
        response += f"{'='*60}\n\n"
        response += f"🎯 Sharpe oranı > {sharpe_threshold} olan fonlar aranıyor...\n"
        response += f"🛡️ Risk değerlendirmesi aktif\n\n"
        
        sharpe_results = []
        high_risk_funds = []
        blocked_extreme_funds = []
        
        # SQL ile hızlı Sharpe hesaplama ve risk kontrolü
        try:
            query = f"""
            WITH fund_returns AS (
                SELECT 
                    f.fcode,
                    AVG(f.price) as avg_price,
                    STDDEV(f.price / LAG(f.price) OVER (PARTITION BY f.fcode ORDER BY f.pdate) - 1) as volatility,
                    (MAX(f.price) - MIN(f.price)) / MIN(f.price) as total_return,
                    COUNT(*) as data_points,
                    MAX(f.price) as current_price,
                    MAX(f.investorcount) as investors
                FROM tefasfunds f
                WHERE f.pdate >= CURRENT_DATE - INTERVAL '252 days'
                AND f.investorcount > 100
                AND f.price > 0
                GROUP BY f.fcode
                HAVING COUNT(*) >= 60
                AND MIN(f.price) > 0
            ),
            sharpe_calc AS (
                SELECT 
                    fcode,
                    current_price,
                    investors,
                    total_return * 252 / data_points as annualized_return,
                    volatility * SQRT(252) as annual_volatility,
                    CASE 
                        WHEN volatility > 0 AND volatility IS NOT NULL THEN
                            ((total_return * 252 / data_points) - 0.15) / (volatility * SQRT(252))
                        ELSE 0
                    END as sharpe_ratio
                FROM fund_returns
                WHERE volatility > 0
            )
            SELECT fcode, current_price, investors, annualized_return, annual_volatility, sharpe_ratio
            FROM sharpe_calc
            WHERE sharpe_ratio > {sharpe_threshold}
            ORDER BY sharpe_ratio DESC
            LIMIT 30
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if not result.empty:
                for _, row in result.iterrows():
                    fcode = row['fcode']
                    
                    # Risk değerlendirmesi
                    risk_data = self._get_fund_risk_data(fcode)
                    risk_assessment = None
                    risk_level = 'UNKNOWN'
                    
                    if risk_data:
                        risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                        risk_level = risk_assessment['risk_level']
                    
                    fund_result = {
                        'fcode': fcode,
                        'sharpe_ratio': float(row['sharpe_ratio']),
                        'annual_return': float(row['annualized_return']) * 100,
                        'volatility': float(row['annual_volatility']) * 100,
                        'current_price': float(row['current_price']),
                        'investors': int(row['investors']),
                        'risk_level': risk_level,
                        'risk_factors': risk_assessment['risk_factors'] if risk_assessment else [],
                        'risk_score': risk_assessment['risk_score'] if risk_assessment else 0
                    }
                    
                    # Risk seviyesine göre kategorize et
                    if risk_level == 'EXTREME':
                        blocked_extreme_funds.append(fund_result)
                    elif risk_level in ['HIGH']:
                        high_risk_funds.append(fund_result)
                        sharpe_results.append(fund_result)
                    else:
                        sharpe_results.append(fund_result)
                        
        except Exception as e:
            print(f"   ⚠️ SQL Sharpe hesaplama hatası: {e}")
            return "❌ Sharpe oranı analizi yapılamadı."
        
        if not sharpe_results and not blocked_extreme_funds:
            return f"❌ Sharpe oranı > {sharpe_threshold} olan güvenli fon bulunamadı."
        
        # Fund details al
        for result in sharpe_results[:10]:
            try:
                details = self.coordinator.db.get_fund_details(result['fcode'])
                result['fund_name'] = details.get('fund_name', 'N/A') if details else 'N/A'
                result['fund_type'] = details.get('fund_type', 'N/A') if details else 'N/A'
            except:
                result['fund_name'] = 'N/A'
                result['fund_type'] = 'N/A'
        
        # Sonuçları göster - RİSK BİLGİLERİ İLE
        response += f"🏆 EN YÜKSEK SHARPE ORANLI FONLAR (Risk-Filtreli):\n\n"
        
        for i, fund in enumerate(sharpe_results[:10], 1):
            # Sharpe kalitesi
            if fund['sharpe_ratio'] > 2.0:
                quality = "🌟 EFSANE"
            elif fund['sharpe_ratio'] > 1.5:
                quality = "⭐ MÜKEMMEL"
            elif fund['sharpe_ratio'] > 1.0:
                quality = "🟢 ÇOK İYİ"
            elif fund['sharpe_ratio'] > 0.5:
                quality = "🟡 İYİ"
            else:
                quality = "🟠 ORTA"
            
            # Risk göstergesi
            risk_indicator = self._get_risk_indicator(fund['risk_level'])
            
            response += f"{i:2d}. {fund['fcode']} - {quality} {risk_indicator}\n"
            response += f"    ⚡ Sharpe Oranı: {fund['sharpe_ratio']:.3f}\n"
            response += f"    📈 Yıllık Getiri: %{fund['annual_return']:.1f}\n"
            response += f"    📉 Volatilite: %{fund['volatility']:.1f}\n"
            response += f"    🛡️ Risk Seviyesi: {fund['risk_level']}\n"
            response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
            response += f"    👥 Yatırımcı: {fund['investors']:,} kişi\n"
            response += f"    🏷️ Tür: {fund['fund_type']}\n"
            
            # Risk faktörleri varsa göster
            if fund['risk_factors'] and fund['risk_level'] in ['HIGH', 'EXTREME']:
                top_risks = [f['factor'] for f in fund['risk_factors'][:2]]
                response += f"    ⚠️ Risk Faktörleri: {', '.join(top_risks)}\n"
            
            response += f"\n"
        
        # YÜKSEK RİSKLİ SHARPE FONLARI
        if high_risk_funds:
            response += f"🟠 YÜKSEK RİSKLİ SHARPE FONLARI ({len(high_risk_funds)} adet):\n"
            response += f"   ⚠️ Yüksek Sharpe ama aynı zamanda yüksek risk!\n\n"
            
            for i, fund in enumerate(high_risk_funds[:3], 1):
                response += f"   {i}. {fund['fcode']} - Sharpe: {fund['sharpe_ratio']:.3f}\n"
            response += f"\n"
        
        # EXTREME RİSKLİ (ENGELLENEN) SHARPE FONLARI
        if blocked_extreme_funds:
            response += f"🔴 EXTREME RİSKLİ SHARPE FONLARI - ÖNERİLMİYOR ({len(blocked_extreme_funds)} adet):\n"
            response += f"   ❌ Yüksek Sharpe olsa bile extreme risk nedeniyle önerilmiyor!\n\n"
            
            for i, fund in enumerate(blocked_extreme_funds[:3], 1):
                response += f"   {i}. {fund['fcode']} - Sharpe: {fund['sharpe_ratio']:.3f} - ENGELLENEN\n"
            response += f"\n"
        
        # İstatistikler - güvenli fonlar dahil
        safe_funds = [f for f in sharpe_results if f['risk_level'] in ['LOW', 'MEDIUM']]
        
        if sharpe_results:
            avg_sharpe = sum(f['sharpe_ratio'] for f in sharpe_results) / len(sharpe_results)
            
            response += f"📊 SHARPE ORANI İSTATİSTİKLERİ (Risk-Filtreli):\n"
            response += f"   🔢 Toplam Bulunan: {len(sharpe_results) + len(blocked_extreme_funds)} fon\n"
            response += f"   ✅ Güvenli Yüksek Sharpe: {len(safe_funds)} fon\n"
            response += f"   🟠 Riskli Sharpe: {len(high_risk_funds)} fon\n"
            response += f"   🔴 Extreme (Engellenen): {len(blocked_extreme_funds)} fon\n"
            response += f"   📊 Ortalama Sharpe: {avg_sharpe:.3f}\n"
            
            if safe_funds:
                best_safe = max(safe_funds, key=lambda x: x['sharpe_ratio'])
                response += f"   🛡️ En Güvenli En İyi: {best_safe['fcode']} (Sharpe: {best_safe['sharpe_ratio']:.3f}, {best_safe['risk_level']})\n"
        
        return response
    
    # === YARDIMCI METODLAR ===
    
    def _get_fund_risk_data(self, fcode):
        """Fonun risk verilerini MV'den çek"""
        try:
            query = """
            SELECT 
                price_vs_sma20,
                rsi_14,
                stochastic_14,
                days_since_last_trade,
                investorcount
            FROM mv_fund_technical_indicators
            WHERE fcode = %s
            """
            
            result = self.coordinator.db.execute_query(query, [fcode])
            
            if not result.empty:
                row = result.iloc[0]
                
                return {
                    'fcode': fcode,
                    'price_vs_sma20': float(row.get('price_vs_sma20', 0)),
                    'rsi_14': float(row.get('rsi_14', 50)),
                    'stochastic_14': float(row.get('stochastic_14', 50)),
                    'days_since_last_trade': int(row.get('days_since_last_trade', 0)),
                    'investorcount': int(row.get('investorcount', 0))
                }
            else:
                return None
                
        except Exception as e:
            print(f"Risk veri hatası ({fcode}): {e}")
            return None

    def _get_risk_indicator(self, risk_level):
        """Risk seviyesi göstergesi"""
        indicators = {
            'LOW': '🟢',
            'MEDIUM': '🟡',
            'HIGH': '🟠',
            'EXTREME': '🔴',
            'UNKNOWN': '⚪'
        }
        return indicators.get(risk_level, '⚪')
    
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
        return ((1 + total_return) ** (252 / n_days) - 1) * 100
    
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
            fund_annual_return = self._annualized_return(fund_returns)
            benchmark_annual_return = self._annualized_return(benchmark_returns)
            
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
                'fund_return': self._annualized_return(fund_returns),
                'benchmark_return': self._annualized_return(benchmark_returns)
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
    
    def _get_ai_commentary_for_beta_with_risk(self, beta_results: List[Dict], blocked_funds: List[Dict], comparison: str, threshold: float) -> str:
        """Beta analizi için AI yorumu - Risk dahil"""
        response = "\n🤖 AI BETA ANALİZİ (RİSK DAHİL):\n"
        response += "="*40 + "\n"
        
        # En iyi 5 güvenli fonu al
        safe_funds = [f for f in beta_results if f['risk_level'] in ['LOW', 'MEDIUM']][:5]
        
        prompt = f"""
        Beta katsayısı {comparison} {threshold} olan fonlar analiz edildi (risk kontrolü ile).
        
        Güvenli fonlar (En iyi 5):
        {', '.join([f"{f['fcode']} (Beta: {f['beta']:.3f}, Risk: {f['risk_level']})" for f in safe_funds])}
        
        Toplam bulunan: {len(beta_results)} güvenli fon
        Engellenen extreme riskli: {len(blocked_funds)} fon
        
        Ortalama beta: {sum(f['beta'] for f in beta_results) / len(beta_results):.3f}
        Ortalama getiri: %{sum(f['annual_return'] for f in beta_results) / len(beta_results):.1f}
        
        Bu fonların risk-ayarlı performansı ve yatırımcı için uygunluğu hakkında kısa yorum yap (max 150 kelime).
        """
        
        if hasattr(self.coordinator, 'ai_provider') and self.coordinator.ai_provider.is_available():
            try:
                ai_comment = self.coordinator.ai_provider.query(
                    prompt, "Sen finansal risk analisti uzmanısın."
                )
                response += f"\n🤖 AI Yorumu:\n{ai_comment}\n"
            except Exception as e:
                self.logger.warning(f"AI yorum hatası: {e}")
                pass        
        return response
    
    def _get_ai_commentary_for_alpha_with_risk(self, alpha_results: List[Dict], blocked_funds: List[Dict]) -> str:
        """Alpha analizi için AI yorumu - Risk dahil"""
        response = "\n🤖 AI ALPHA ANALİZİ (RİSK DAHİL):\n"
        response += "="*40 + "\n"
        
        safe_positive = [f for f in alpha_results if f['alpha'] > 0 and f['risk_level'] in ['LOW', 'MEDIUM']]
        
        prompt = f"""
        Alpha analizi sonuçları (risk kontrolü ile):
        
        Toplam fon: {len(alpha_results)} güvenli fon
        Güvenli pozitif alpha: {len(safe_positive)} fon
        Engellenen extreme riskli: {len(blocked_funds)} fon
        
        En yüksek güvenli alpha: {safe_positive[0]['fcode'] if safe_positive else 'N/A'} 
        (%{safe_positive[0]['alpha']:.2f} - {safe_positive[0]['risk_level']} risk)
        
        Bu sonuçların anlamı ve risk-ayarlı aktif fon yönetiminin başarısı hakkında yorum yap (max 150 kelime).
        """
        
        if hasattr(self.coordinator, 'ai_provider') and self.coordinator.ai_provider.is_available():
            try:
                ai_comment = self.coordinator.ai_provider.query(
                    prompt, "Sen portföy yönetimi uzmanısın."
                )
                response += f"\n🤖 AI Yorumu:\n{ai_comment}\n"
            except Exception as e:
                self.logger.warning(f"AI yorum hatası: {e}")
                pass        
        return response
    
    def _get_ai_commentary_for_ir_with_risk(self, ir_results: List[Dict], blocked_funds: List[Dict]) -> str:
        """Information Ratio analizi için AI yorumu - Risk dahil"""
        response = "\n🤖 AI INFORMATION RATIO ANALİZİ (RİSK DAHİL):\n"
        response += "="*50 + "\n"
        
        safe_funds = [f for f in ir_results if f['risk_level'] in ['LOW', 'MEDIUM']][:3]
        
        prompt = f"""
        Information Ratio analizi sonuçları (risk kontrolü ile):
        
        En güvenli 3 fon:
        {', '.join([f"{f['fcode']} (IR: {f['information_ratio']:.3f}, Risk: {f['risk_level']})" for f in safe_funds])}
        
        Toplam güvenli fon: {len(ir_results)}
        Engellenen extreme riskli: {len(blocked_funds)} fon
        
        IR > 0.5 olan güvenli fon: {len([f for f in safe_funds if f['information_ratio'] > 0.5])}
        
        Risk-ayarlı aktif fon yönetiminin performansı hakkında yorum yap (max 150 kelime).
        """
        
        if hasattr(self.coordinator, 'ai_provider') and self.coordinator.ai_provider.is_available():
            try:
                ai_comment = self.coordinator.ai_provider.query(
                    prompt, "Sen portföy yönetimi uzmanısın."
                )
                response += f"\n🤖 AI Yorumu:\n{ai_comment}\n"
            except Exception as e:
                self.logger.warning(f"AI yorum hatası: {e}")
                pass        
        
        return response
    
    @staticmethod
    def get_examples():
        """İleri metrik analiz örnekleri"""
        return [
            "Beta katsayısı 1'den düşük fonlar",
            "Beta değeri 0.5 altında olan fonlar",
            "Alpha değeri pozitif olan fonlar",
            "Sharpe oranı 0.5'ten yüksek fonlar",
            "Tracking error düşük index fonlar",
            "Information ratio yüksek aktif fonlar",
            "Beta 1 üstü agresif fonlar"
        ]
    
    @staticmethod
    def get_keywords():
        """İleri metrik anahtar kelimeleri"""
        return [
            "beta", "alpha", "sharpe", "tracking error", "information ratio",
            "katsayı", "katsayısı", "değeri", "oranı", "metrik",
            "risk-adjusted", "jensen", "treynor"
        ]
    
    @staticmethod
    def get_patterns():
        """İleri metrik pattern'leri"""
        return [
            {
                'type': 'regex',
                'pattern': r'(beta|alpha|sharpe)\s*(katsayısı|değeri|oranı)?',
                'score': 0.95
            },
            {
                'type': 'regex',
                'pattern': r'(tracking error|information ratio)',
                'score': 0.95
            },
            {
                'type': 'contains_all',
                'words': ['sharpe', 'oranı'],
                'score': 0.95
            }
        ]
    
    @staticmethod
    def get_method_patterns():
        """Method mapping"""
        return {
            'handle_beta_analysis': ['beta', 'beta katsayısı', 'beta değeri'],
            'handle_alpha_analysis': ['alpha', 'alpha değeri', 'jensen alpha'],
            'handle_sharpe_ratio_analysis': ['sharpe', 'sharpe oranı'],
            'handle_tracking_error_analysis': ['tracking error', 'takip hatası'],
            'handle_information_ratio_analysis': ['information ratio', 'bilgi oranı']
        }