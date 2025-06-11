# advanced_metrics_analyzer.py
"""
İleri Finansal Metrikler Analizi - Risk Assessment ve MV Entegre Edilmiş
Beta, Alpha, Tracking Error, Information Ratio hesaplamaları
Risk değerlendirmesi ile güvenli metrik analizleri
Materialized View'lar kullanılarak performans optimizasyonu
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
    """İleri finansal metrikler için analiz sınıfı - Risk Kontrolü ve MV İle"""
    
    def __init__(self, coordinator, active_funds, ai_status):
        self.coordinator = coordinator
        self.active_funds = active_funds
        self.ai_status = ai_status
        self.logger = logging.getLogger(__name__)
        
        # Benchmark olarak kullanılacak index fonları (BIST100 vb. temsil eden)
        self.benchmark_funds = ['TI2', 'TKF', 'GAF']  # Örnek index fonlar
        self.risk_free_rate = 0.15  # %15 risksiz faiz oranı (Türkiye için)
        
    def handle_beta_analysis(self, question):
        """Beta katsayısı analizi - MV tabanlı hızlı analiz + RİSK KONTROLÜ"""
        print("📊 Beta katsayısı analiz ediliyor (MV + risk kontrolü ile)...")
        
        # Beta eşiğini belirle
        beta_threshold = 1.0
        match = re.search(r'(\d+\.?\d*)', question)
        if match:
            beta_threshold = float(match.group(1))
            
        if "düşük" in question.lower() or "altında" in question.lower():
            comparison = "<"
        else:
            comparison = ">"
            
        response = f"\n📊 BETA KATSAYISI ANALİZİ (MV + RİSK KONTROLÜ İLE)\n"
        response += f"{'='*60}\n\n"
        response += f"🎯 Beta {comparison} {beta_threshold} olan fonlar aranıyor...\n"
        response += f"🛡️ Risk değerlendirmesi aktif\n"
        response += f"⚡ Materialized View kullanılıyor\n\n"
        
        beta_results = []
        high_risk_funds = []
        blocked_extreme_funds = []
        
        try:
            # MV'den performance metrics al - beta için proxy olarak volatilite/sharpe kullan
            # Not: Gerçek beta hesabı için benchmark ile korelasyon gerekir
            query = f"""
            WITH beta_proxy AS (
                SELECT 
                    pm.fcode,
                    pm.current_price,
                    pm.annual_return,
                    pm.annual_volatility,
                    pm.sharpe_ratio,
                    pm.win_rate,
                    pm.worst_daily_return,
                    pm.best_daily_return,
                    -- Beta proxy: Volatilite ve getiri bazlı tahmin
                    CASE 
                        WHEN pm.annual_volatility > 0 THEN
                            -- Basit beta tahmini: volatilite ve piyasa korelasyonu
                            (pm.annual_volatility / 20.0) * -- Piyasa volatilitesi ~20 varsayımı
                            (1 + (pm.annual_return - 15) / 100) -- Getiri bazlı ayarlama
                        ELSE 1.0
                    END as beta_estimate,
                    ti.rsi_14,
                    ti.stochastic_14,
                    ti.price_vs_sma20,
                    ti.days_since_last_trade,
                    ti.investorcount,
                    lf.ftitle as fund_name
                FROM mv_fund_performance_metrics pm
                JOIN mv_fund_technical_indicators ti ON pm.fcode = ti.fcode
                JOIN mv_latest_fund_data lf ON pm.fcode = lf.fcode
                WHERE pm.trading_days >= 60
            )
            SELECT * FROM beta_proxy
            WHERE beta_estimate {comparison} {beta_threshold}
            ORDER BY beta_estimate {'ASC' if comparison == '<' else 'DESC'}
            LIMIT 50
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if not result.empty:
                print(f"   ✅ MV'den {len(result)} aday fon yüklendi")
                
                # Her fon için detaylı beta hesabı ve risk değerlendirmesi
                benchmark_data = self._get_benchmark_data()
                
                for _, fund in result.iterrows():
                    fcode = fund['fcode']
                    
                    # Gerçek beta hesabı için fiyat verisi çek
                    fund_data = self.coordinator.db.get_fund_price_history(fcode, 120)
                    
                    if len(fund_data) >= 30 and benchmark_data is not None:
                        # Gerçek beta hesapla
                        real_beta = self._calculate_beta(fund_data, benchmark_data)
                        
                        if real_beta is not None and self._check_beta_condition(real_beta, beta_threshold, comparison):
                            # Risk değerlendirmesi - MV'den gelen verilerle
                            risk_data = {
                                'fcode': fcode,
                                'price_vs_sma20': float(fund['price_vs_sma20']),
                                'rsi_14': float(fund['rsi_14']),
                                'stochastic_14': float(fund['stochastic_14']),
                                'days_since_last_trade': int(fund['days_since_last_trade']),
                                'investorcount': int(fund['investorcount'])
                            }
                            
                            risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                            risk_level = risk_assessment['risk_level']
                            
                            fund_result = {
                                'fcode': fcode,
                                'beta': real_beta,
                                'beta_estimate': float(fund['beta_estimate']),  # MV tahmini
                                'annual_return': float(fund['annual_return']) * 100,
                                'volatility': float(fund['annual_volatility']) * 100,
                                'sharpe_ratio': float(fund['sharpe_ratio']),
                                'win_rate': float(fund['win_rate']) * 100,
                                'current_price': float(fund['current_price']),
                                'fund_name': fund['fund_name'],
                                'risk_level': risk_level,
                                'risk_factors': risk_assessment['risk_factors'],
                                'risk_score': risk_assessment['risk_score']
                            }
                            
                            # Risk seviyesine göre kategorize et
                            if risk_level == 'EXTREME':
                                blocked_extreme_funds.append(fund_result)
                            elif risk_level in ['HIGH']:
                                high_risk_funds.append(fund_result)
                                beta_results.append(fund_result)
                            else:
                                beta_results.append(fund_result)
                    
                    # Sadece MV beta tahmini kullan (hızlı mod)
                    elif self._check_beta_condition(float(fund['beta_estimate']), beta_threshold, comparison):
                        # Risk değerlendirmesi
                        risk_data = {
                            'fcode': fcode,
                            'price_vs_sma20': float(fund['price_vs_sma20']),
                            'rsi_14': float(fund['rsi_14']),
                            'stochastic_14': float(fund['stochastic_14']),
                            'days_since_last_trade': int(fund['days_since_last_trade']),
                            'investorcount': int(fund['investorcount'])
                        }
                        
                        risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                        risk_level = risk_assessment['risk_level']
                        
                        fund_result = {
                            'fcode': fcode,
                            'beta': float(fund['beta_estimate']),  # Tahmin kullan
                            'beta_estimate': float(fund['beta_estimate']),
                            'annual_return': float(fund['annual_return']) * 100,
                            'volatility': float(fund['annual_volatility']) * 100,
                            'sharpe_ratio': float(fund['sharpe_ratio']),
                            'win_rate': float(fund['win_rate']) * 100,
                            'current_price': float(fund['current_price']),
                            'fund_name': fund['fund_name'],
                            'risk_level': risk_level,
                            'risk_factors': risk_assessment['risk_factors'],
                            'risk_score': risk_assessment['risk_score'],
                            'is_estimate': True  # Beta tahmin olduğunu işaretle
                        }
                        
                        # Risk seviyesine göre kategorize et
                        if risk_level == 'EXTREME':
                            blocked_extreme_funds.append(fund_result)
                        elif risk_level in ['HIGH']:
                            high_risk_funds.append(fund_result)
                            beta_results.append(fund_result)
                        else:
                            beta_results.append(fund_result)
                
                print(f"   📊 {len(beta_results)} güvenli/orta riskli fon bulundu")
                print(f"   ⚠️ {len(high_risk_funds)} yüksek riskli fon tespit edildi")
                print(f"   🚫 {len(blocked_extreme_funds)} extreme riskli fon engellendi")
                
            else:
                print("   ⚠️ MV'de uygun fon bulunamadı, alternatif yöntem kullanılıyor...")
                # Fallback: Eski yöntem
                return self._handle_beta_analysis_fallback(question, beta_threshold, comparison)
                
        except Exception as e:
            print(f"   ❌ MV sorgu hatası: {e}")
            # Fallback
            return self._handle_beta_analysis_fallback(question, beta_threshold, comparison)
        
        # Sonuçları beta'ya göre sırala
        beta_results.sort(key=lambda x: x['beta'])
        
        if not beta_results and not blocked_extreme_funds:
            return f"❌ Beta {comparison} {beta_threshold} olan fon bulunamadı."
        
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
            response += f"    📊 Beta: {fund['beta']:.3f}"
            if fund.get('is_estimate'):
                response += " (tahmini)"
            response += f"\n"
            response += f"    📈 Yıllık Getiri: %{fund['annual_return']:.1f}\n"
            response += f"    📉 Volatilite: %{fund['volatility']:.1f}\n"
            response += f"    ⚡ Sharpe: {fund['sharpe_ratio']:.3f}\n"
            response += f"    🎯 Kazanma Oranı: %{fund['win_rate']:.1f}\n"
            response += f"    🛡️ Risk Seviyesi: {fund['risk_level']} ({fund['risk_score']}/100)\n"
            response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
            
            # Risk faktörleri varsa göster
            if fund['risk_factors'] and fund['risk_level'] in ['HIGH', 'EXTREME']:
                top_risks = [f['description'] for f in fund['risk_factors'][:2]]
                response += f"    ⚠️ Riskler: {' | '.join(top_risks)}\n"
            
            if fund['fund_name']:
                response += f"    📝 {fund['fund_name'][:40]}...\n"
            response += f"\n"
        
        # YÜKSEK RİSKLİ FONLAR UYARISI
        if high_risk_funds:
            response += f"🟠 YÜKSEK RİSKLİ BETA FONLARI ({len(high_risk_funds)} adet):\n"
            response += f"   ⚠️ Bu fonlar yüksek risk taşımaktadır!\n\n"
            
            for i, fund in enumerate(high_risk_funds[:3], 1):
                risk_factors = [f['description'] for f in fund['risk_factors'][:2]]
                response += f"   {i}. {fund['fcode']} - Beta: {fund['beta']:.3f}\n"
                response += f"      ⚠️ Risk: {', '.join(risk_factors)}\n"
            response += f"\n"
        
        # EXTREME RİSKLİ (ENGELLENEN) FONLAR
        if blocked_extreme_funds:
            response += f"🔴 EXTREME RİSKLİ BETA FONLARI - ÖNERİLMİYOR ({len(blocked_extreme_funds)} adet):\n"
            response += f"   ❌ Bu fonlar extreme risk taşıdığı için analiz dışı bırakıldı!\n\n"
            
            for i, fund in enumerate(blocked_extreme_funds[:3], 1):
                top_risk_factors = [f['description'] for f in fund['risk_factors'][:2]]
                response += f"   {i}. {fund['fcode']} - Beta: {fund['beta']:.3f} - ENGELLENEN\n"
                response += f"      🚨 Sebepler: {', '.join(top_risk_factors)}\n"
            response += f"\n"
        
        # İstatistikler
        response += self._get_beta_statistics(beta_results, blocked_extreme_funds, comparison, beta_threshold)
        
        # AI Yorumu
        if hasattr(self.coordinator, 'ai_provider') and self.coordinator.ai_provider.is_available():
            response += self._get_ai_commentary_for_beta_with_risk(beta_results, blocked_extreme_funds, comparison, beta_threshold)
        
        return response
    
    def handle_alpha_analysis(self, question):
        """Alpha değeri analizi - MV tabanlı hızlı analiz + RİSK KONTROLÜ"""
        print("📊 Alpha değeri analiz ediliyor (MV + risk kontrolü ile)...")
        
        # Alpha koşulunu belirle
        is_positive = "pozitif" in question.lower() or "yüksek" in question.lower()
        
        response = f"\n📊 ALPHA DEĞERİ ANALİZİ (MV + RİSK KONTROLÜ İLE)\n"
        response += f"{'='*60}\n\n"
        response += f"🎯 {'Pozitif' if is_positive else 'Negatif'} Alpha değerine sahip fonlar aranıyor...\n"
        response += f"🛡️ Risk değerlendirmesi aktif\n"
        response += f"⚡ Materialized View kullanılıyor\n\n"
        
        alpha_results = []
        high_risk_funds = []
        blocked_extreme_funds = []
        
        try:
            # MV'den alpha proxy hesapla
            # Alpha = Fon Getirisi - (Risk Free Rate + Beta * (Market Return - Risk Free Rate))
            # Market return olarak BIST100 tahmini kullan
            market_return = 25  # BIST100 tahmini yıllık getiri
            risk_free_rate = self.risk_free_rate * 100
            
            query = f"""
            WITH alpha_calc AS (
                SELECT 
                    pm.fcode,
                    pm.current_price,
                    pm.annual_return * 100 as annual_return_pct,
                    pm.annual_volatility * 100 as annual_volatility_pct,
                    pm.sharpe_ratio,
                    pm.calmar_ratio_approx,
                    -- Beta tahmini
                    CASE 
                        WHEN pm.annual_volatility > 0 THEN
                            (pm.annual_volatility / 0.20) * 
                            (1 + (pm.annual_return - 0.15) / 1.0)
                        ELSE 1.0
                    END as beta_estimate,
                    -- Alpha tahmini
                    (pm.annual_return * 100) - 
                    ({risk_free_rate} + 
                     CASE 
                        WHEN pm.annual_volatility > 0 THEN
                            (pm.annual_volatility / 0.20) * ({market_return} - {risk_free_rate})
                        ELSE ({market_return} - {risk_free_rate})
                     END
                    ) as alpha_estimate,
                    ti.rsi_14,
                    ti.stochastic_14,
                    ti.price_vs_sma20,
                    ti.days_since_last_trade,
                    ti.investorcount,
                    lf.ftitle as fund_name
                FROM mv_fund_performance_metrics pm
                JOIN mv_fund_technical_indicators ti ON pm.fcode = ti.fcode
                JOIN mv_latest_fund_data lf ON pm.fcode = lf.fcode
                WHERE pm.trading_days >= 60
            )
            SELECT * FROM alpha_calc
            WHERE alpha_estimate {'>' if is_positive else '<='} 0
            ORDER BY alpha_estimate DESC
            LIMIT 50
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if not result.empty:
                print(f"   ✅ MV'den {len(result)} aday fon yüklendi")
                
                # Benchmark verilerini al
                benchmark_data = self._get_benchmark_data()
                
                for _, fund in result.iterrows():
                    fcode = fund['fcode']
                    
                    # Risk değerlendirmesi
                    risk_data = {
                        'fcode': fcode,
                        'price_vs_sma20': float(fund['price_vs_sma20']),
                        'rsi_14': float(fund['rsi_14']),
                        'stochastic_14': float(fund['stochastic_14']),
                        'days_since_last_trade': int(fund['days_since_last_trade']),
                        'investorcount': int(fund['investorcount'])
                    }
                    
                    risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                    risk_level = risk_assessment['risk_level']
                    
                    # Detaylı alpha hesabı için fiyat verisi çek (opsiyonel)
                    real_alpha = None
                    if benchmark_data is not None and len(alpha_results) < 20:  # İlk 20 fon için
                        try:
                            fund_data = self.coordinator.db.get_fund_price_history(fcode, 120)
                            if len(fund_data) >= 30:
                                alpha_data = self._calculate_alpha(fund_data, benchmark_data)
                                if alpha_data:
                                    real_alpha = alpha_data['alpha']
                        except:
                            pass
                    
                    fund_result = {
                        'fcode': fcode,
                        'alpha': real_alpha if real_alpha is not None else float(fund['alpha_estimate']),
                        'alpha_estimate': float(fund['alpha_estimate']),
                        'beta': float(fund['beta_estimate']),
                        'annual_return': float(fund['annual_return_pct']),
                        'volatility': float(fund['annual_volatility_pct']),
                        'sharpe_ratio': float(fund['sharpe_ratio']),
                        'calmar_ratio': float(fund['calmar_ratio_approx']) if pd.notna(fund['calmar_ratio_approx']) else 0,
                        'current_price': float(fund['current_price']),
                        'fund_name': fund['fund_name'],
                        'risk_level': risk_level,
                        'risk_factors': risk_assessment['risk_factors'],
                        'risk_score': risk_assessment['risk_score'],
                        'is_estimate': real_alpha is None
                    }
                    
                    # Risk seviyesine göre kategorize et
                    if risk_level == 'EXTREME':
                        blocked_extreme_funds.append(fund_result)
                    elif risk_level in ['HIGH']:
                        high_risk_funds.append(fund_result)
                        alpha_results.append(fund_result)
                    else:
                        alpha_results.append(fund_result)
                
                print(f"   📊 {len(alpha_results)} güvenli/orta riskli fon bulundu")
                print(f"   ⚠️ {len(high_risk_funds)} yüksek riskli fon tespit edildi")
                print(f"   🚫 {len(blocked_extreme_funds)} extreme riskli fon engellendi")
                
            else:
                print("   ⚠️ MV'de uygun fon bulunamadı, alternatif yöntem kullanılıyor...")
                return self._handle_alpha_analysis_fallback(question, is_positive)
                
        except Exception as e:
            print(f"   ❌ MV sorgu hatası: {e}")
            return self._handle_alpha_analysis_fallback(question, is_positive)
        
        # Alpha'ya göre sırala
        alpha_results.sort(key=lambda x: x['alpha'], reverse=True)
        
        if not alpha_results and not blocked_extreme_funds:
            return f"❌ {'Pozitif' if is_positive else 'Negatif'} Alpha değerine sahip güvenli fon bulunamadı."
        
        # Sonuçları göster
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
            response += f"    📊 Alpha: %{fund['alpha']:.2f}"
            if fund.get('is_estimate'):
                response += " (tahmini)"
            response += f" (yıllık)\n"
            response += f"    📈 Beta: {fund['beta']:.3f}\n"
            response += f"    💰 Fon Getirisi: %{fund['annual_return']:.1f}\n"
            response += f"    📉 Volatilite: %{fund['volatility']:.1f}\n"
            response += f"    ⚡ Sharpe: {fund['sharpe_ratio']:.3f}\n"
            if fund['calmar_ratio'] > 0:
                response += f"    📊 Calmar: {fund['calmar_ratio']:.3f}\n"
            response += f"    🛡️ Risk Seviyesi: {fund['risk_level']} ({fund['risk_score']}/100)\n"
            response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
            
            # Risk faktörleri varsa göster
            if fund['risk_factors'] and fund['risk_level'] in ['HIGH', 'EXTREME']:
                top_risks = [f['description'] for f in fund['risk_factors'][:2]]
                response += f"    ⚠️ Riskler: {' | '.join(top_risks)}\n"
            
            if fund['fund_name']:
                response += f"    📝 {fund['fund_name'][:40]}...\n"
            response += f"\n"
        
        # Risk uyarıları
        if high_risk_funds:
            response += self._format_high_risk_alpha_funds(high_risk_funds)
        
        if blocked_extreme_funds:
            response += self._format_extreme_risk_alpha_funds(blocked_extreme_funds)
        
        # İstatistikler
        response += self._get_alpha_statistics(alpha_results, blocked_extreme_funds, is_positive)
        
        # AI Yorumu
        if hasattr(self.coordinator, 'ai_provider') and self.coordinator.ai_provider.is_available():
            response += self._get_ai_commentary_for_alpha_with_risk(alpha_results, blocked_extreme_funds)
        
        return response
    
    def handle_tracking_error_analysis(self, question):
        """Tracking Error analizi - Index fonlar için MV tabanlı + RİSK KONTROLÜ"""
        print("📊 Tracking Error analiz ediliyor (MV + risk kontrolü ile)...")
        
        response = f"\n📊 TRACKING ERROR ANALİZİ (INDEX FONLAR - MV + RİSK KONTROLÜ)\n"
        response += f"{'='*70}\n\n"
        response += f"🎯 En düşük tracking error'a sahip index fonlar aranıyor...\n"
        response += f"🛡️ Risk değerlendirmesi aktif\n"
        response += f"⚡ Materialized View kullanılıyor\n\n"
        
        tracking_error_results = []
        high_risk_funds = []
        blocked_extreme_funds = []
        
        try:
            # MV'den index benzeri fonları bul
            # Index fonları genelde düşük volatilite ve yüksek korelasyona sahip
            query = """
            WITH index_candidates AS (
                SELECT 
                    pm.fcode,
                    pm.current_price,
                    pm.annual_return * 100 as annual_return_pct,
                    pm.annual_volatility * 100 as annual_volatility_pct,
                    pm.sharpe_ratio,
                    pm.win_rate,
                    -- Tracking error proxy: düşük volatilite + istikrarlı performans
                    pm.annual_volatility * 100 as tracking_error_proxy,
                    ti.rsi_14,
                    ti.stochastic_14,
                    ti.price_vs_sma20,
                    ti.bb_position,
                    ti.days_since_last_trade,
                    ti.investorcount,
                    lf.ftitle as fund_name
                FROM mv_fund_performance_metrics pm
                JOIN mv_fund_technical_indicators ti ON pm.fcode = ti.fcode
                JOIN mv_latest_fund_data lf ON pm.fcode = lf.fcode
                WHERE pm.trading_days >= 60
                AND pm.win_rate > 0.45  -- İstikrarlı performans
                AND pm.win_rate < 0.65  -- Aşırı değil
                AND (
                    UPPER(lf.ftitle) LIKE '%INDEX%' OR
                    UPPER(lf.ftitle) LIKE '%ENDEKS%' OR
                    UPPER(lf.ftitle) LIKE '%BIST%' OR
                    UPPER(lf.ftitle) LIKE '%XU100%' OR
                    UPPER(lf.ftitle) LIKE '%XU030%' OR
                    pm.annual_volatility < 0.15  -- Düşük volatilite
                )
            )
            SELECT * FROM index_candidates
            ORDER BY tracking_error_proxy ASC
            LIMIT 30
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if not result.empty:
                print(f"   ✅ MV'den {len(result)} index fonu adayı yüklendi")
                
                # Benchmark verilerini al
                benchmark_data = self._get_benchmark_data()
                
                for _, fund in result.iterrows():
                    fcode = fund['fcode']
                    
                    # Risk değerlendirmesi
                    risk_data = {
                        'fcode': fcode,
                        'price_vs_sma20': float(fund['price_vs_sma20']),
                        'rsi_14': float(fund['rsi_14']),
                        'stochastic_14': float(fund['stochastic_14']),
                        'days_since_last_trade': int(fund['days_since_last_trade']),
                        'investorcount': int(fund['investorcount'])
                    }
                    
                    risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                    risk_level = risk_assessment['risk_level']
                    
                    # Gerçek tracking error hesabı (opsiyonel)
                    real_tracking_error = None
                    correlation = None
                    if benchmark_data is not None and len(tracking_error_results) < 10:
                        try:
                            fund_data = self.coordinator.db.get_fund_price_history(fcode, 120)
                            if len(fund_data) >= 30:
                                te_data = self._calculate_tracking_error(fund_data, benchmark_data)
                                if te_data:
                                    real_tracking_error = te_data['tracking_error']
                                    correlation = te_data['correlation']
                        except:
                            pass
                    
                    fund_result = {
                        'fcode': fcode,
                        'tracking_error': real_tracking_error if real_tracking_error is not None else float(fund['tracking_error_proxy']),
                        'tracking_error_proxy': float(fund['tracking_error_proxy']),
                        'correlation': correlation if correlation is not None else (1 - float(fund['tracking_error_proxy'])/100),  # Tahmin
                        'annual_return': float(fund['annual_return_pct']),
                        'volatility': float(fund['annual_volatility_pct']),
                        'sharpe_ratio': float(fund['sharpe_ratio']),
                        'win_rate': float(fund['win_rate']) * 100,
                        'bb_position': float(fund['bb_position']),
                        'current_price': float(fund['current_price']),
                        'fund_name': fund['fund_name'],
                        'risk_level': risk_level,
                        'risk_factors': risk_assessment['risk_factors'],
                        'risk_score': risk_assessment['risk_score'],
                        'is_estimate': real_tracking_error is None
                    }
                    
                    # Risk seviyesine göre kategorize et
                    if risk_level == 'EXTREME':
                        blocked_extreme_funds.append(fund_result)
                    elif risk_level in ['HIGH']:
                        high_risk_funds.append(fund_result)
                        tracking_error_results.append(fund_result)
                    else:
                        tracking_error_results.append(fund_result)
                
                print(f"   📊 {len(tracking_error_results)} güvenli/orta riskli index fon bulundu")
                print(f"   ⚠️ {len(high_risk_funds)} yüksek riskli index fon tespit edildi")
                print(f"   🚫 {len(blocked_extreme_funds)} extreme riskli fon engellendi")
                
            else:
                print("   ⚠️ MV'de index fon bulunamadı")
                return "❌ Index fon bulunamadı. Tracking error analizi yapılamıyor."
                
        except Exception as e:
            print(f"   ❌ MV sorgu hatası: {e}")
            return self._handle_tracking_error_fallback(question)
        
        # Tracking error'a göre sırala (düşükten yükseğe)
        tracking_error_results.sort(key=lambda x: x['tracking_error'])
        
        if not tracking_error_results and not blocked_extreme_funds:
            return "❌ Tracking error hesaplanabilir güvenli index fon bulunamadı."
        
        # Sonuçları göster
        response += f"🏆 EN DÜŞÜK TRACKING ERROR'LU INDEX FONLAR (Risk-Filtreli):\n\n"
        
        for i, fund in enumerate(tracking_error_results[:10], 1):
            # Tracking kalitesi
            te = fund['tracking_error']
            if te < 2:
                quality = "🌟 MÜKEMMEL"
            elif te < 5:
                quality = "🟢 ÇOK İYİ"
            elif te < 10:
                quality = "🟡 İYİ"
            else:
                quality = "🔴 ZAYIF"
            
            # Risk göstergesi
            risk_indicator = self._get_risk_indicator(fund['risk_level'])
            
            response += f"{i:2d}. {fund['fcode']} - {quality} {risk_indicator}\n"
            response += f"    📊 Tracking Error: %{te:.2f}"
            if fund.get('is_estimate'):
                response += " (tahmini)"
            response += f" (yıllık)\n"
            response += f"    🔗 Korelasyon: {fund['correlation']:.3f}\n"
            response += f"    📈 Yıllık Getiri: %{fund['annual_return']:.1f}\n"
            response += f"    📉 Volatilite: %{fund['volatility']:.1f}\n"
            response += f"    ⚡ Sharpe: {fund['sharpe_ratio']:.3f}\n"
            response += f"    🎯 Kazanma Oranı: %{fund['win_rate']:.1f}\n"
            response += f"    📊 BB Pozisyon: {fund['bb_position']:.2f}\n"
            response += f"    🛡️ Risk Seviyesi: {fund['risk_level']} ({fund['risk_score']}/100)\n"
            response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
            
            # Risk faktörleri varsa göster
            if fund['risk_factors'] and fund['risk_level'] in ['HIGH', 'EXTREME']:
                critical_risks = [f for f in fund['risk_factors'] if f['severity'] in ['CRITICAL', 'HIGH']]
                if critical_risks:
                    response += f"    ⚠️ Riskler: {critical_risks[0]['description']}\n"
            
            if fund['fund_name']:
                response += f"    📝 {fund['fund_name'][:40]}...\n"
            response += f"\n"
        
        # Risk uyarıları
        if high_risk_funds or blocked_extreme_funds:
            response += self._format_tracking_error_risk_warnings(high_risk_funds, blocked_extreme_funds)
        
        # İstatistikler
        response += self._get_tracking_error_statistics(tracking_error_results, blocked_extreme_funds)
        
        return response
    
    def handle_information_ratio_analysis(self, question):
        """Information Ratio analizi - MV tabanlı aktif yönetim analizi + RİSK KONTROLÜ"""
        print("📊 Information Ratio analiz ediliyor (MV + risk kontrolü ile)...")
        
        response = f"\n📊 INFORMATION RATIO ANALİZİ (MV + RİSK KONTROLÜ)\n"
        response += f"{'='*60}\n\n"
        response += f"🎯 En yüksek information ratio'ya sahip aktif fonlar aranıyor...\n"
        response += f"🛡️ Risk değerlendirmesi aktif\n"
        response += f"⚡ Materialized View kullanılıyor\n\n"
        
        ir_results = []
        high_risk_funds = []
        blocked_extreme_funds = []
        
        try:
            # MV'den Information Ratio proxy hesapla
            # IR = (Aktif Getiri) / (Tracking Error)
            # Aktif fonlar için Sharpe oranı ve volatilite bazlı tahmin
            query = """
            WITH ir_candidates AS (
                SELECT 
                    pm.fcode,
                    pm.current_price,
                    pm.annual_return * 100 as annual_return_pct,
                    pm.annual_volatility * 100 as annual_volatility_pct,
                    pm.sharpe_ratio,
                    pm.calmar_ratio_approx,
                    pm.win_rate * 100 as win_rate_pct,
                    -- IR proxy: Sharpe benzeri ama aktif getiriye odaklı
                    CASE 
                        WHEN pm.annual_volatility > 0 AND pm.annual_return > 0.20 THEN
                            (pm.annual_return - 0.20) / pm.annual_volatility  -- Aktif getiri / risk
                        ELSE 0
                    END as ir_proxy,
                    -- Aktif getiri tahmini (piyasa üstü)
                    (pm.annual_return * 100 - 25) as active_return_estimate,
                    ti.rsi_14,
                    ti.stochastic_14,
                    ti.price_vs_sma20,
                    ti.macd_line,
                    ti.days_since_last_trade,
                    ti.investorcount,
                    lf.ftitle as fund_name
                FROM mv_fund_performance_metrics pm
                JOIN mv_fund_technical_indicators ti ON pm.fcode = ti.fcode
                JOIN mv_latest_fund_data lf ON pm.fcode = lf.fcode
                WHERE pm.trading_days >= 60
                AND pm.annual_return > 0.20  -- %20+ getiri (aktif yönetim göstergesi)
                AND NOT (
                    UPPER(lf.ftitle) LIKE '%INDEX%' OR
                    UPPER(lf.ftitle) LIKE '%ENDEKS%'
                )  -- Index fonları hariç
            )
            SELECT * FROM ir_candidates
            WHERE ir_proxy > 0
            ORDER BY ir_proxy DESC
            LIMIT 40
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if not result.empty:
                print(f"   ✅ MV'den {len(result)} aktif fon adayı yüklendi")
                
                for _, fund in result.iterrows():
                    fcode = fund['fcode']
                    
                    # Risk değerlendirmesi
                    risk_data = {
                        'fcode': fcode,
                        'price_vs_sma20': float(fund['price_vs_sma20']),
                        'rsi_14': float(fund['rsi_14']),
                        'stochastic_14': float(fund['stochastic_14']),
                        'days_since_last_trade': int(fund['days_since_last_trade']),
                        'investorcount': int(fund['investorcount'])
                    }
                    
                    risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                    risk_level = risk_assessment['risk_level']
                    
                    # Tracking error tahmini (aktif fonlar için genelde %5-20 arası)
                    tracking_error_estimate = max(5, min(20, float(fund['annual_volatility_pct']) * 0.7))
                    
                    fund_result = {
                        'fcode': fcode,
                        'information_ratio': float(fund['ir_proxy']),
                        'active_return': float(fund['active_return_estimate']),
                        'tracking_error': tracking_error_estimate,
                        'annual_return': float(fund['annual_return_pct']),
                        'volatility': float(fund['annual_volatility_pct']),
                        'sharpe_ratio': float(fund['sharpe_ratio']),
                        'calmar_ratio': float(fund['calmar_ratio_approx']) if pd.notna(fund['calmar_ratio_approx']) else 0,
                        'win_rate': float(fund['win_rate_pct']),
                        'macd_line': float(fund['macd_line']),
                        'current_price': float(fund['current_price']),
                        'fund_name': fund['fund_name'],
                        'risk_level': risk_level,
                        'risk_factors': risk_assessment['risk_factors'],
                        'risk_score': risk_assessment['risk_score']
                    }
                    
                    # Risk seviyesine göre kategorize et
                    if risk_level == 'EXTREME':
                        blocked_extreme_funds.append(fund_result)
                    elif risk_level in ['HIGH']:
                        high_risk_funds.append(fund_result)
                        ir_results.append(fund_result)
                    else:
                        ir_results.append(fund_result)
                
                print(f"   📊 {len(ir_results)} güvenli/orta riskli aktif fon bulundu")
                print(f"   ⚠️ {len(high_risk_funds)} yüksek riskli fon tespit edildi")
                print(f"   🚫 {len(blocked_extreme_funds)} extreme riskli fon engellendi")
                
            else:
                print("   ⚠️ MV'de uygun aktif fon bulunamadı")
                return "❌ Information ratio hesaplanabilir aktif fon bulunamadı."
                
        except Exception as e:
            print(f"   ❌ MV sorgu hatası: {e}")
            return self._handle_information_ratio_fallback(question)
        
        # Information ratio'ya göre sırala (yüksekten düşüğe)
        ir_results.sort(key=lambda x: x['information_ratio'], reverse=True)
        
        if not ir_results and not blocked_extreme_funds:
            return "❌ Information ratio hesaplanabilir güvenli aktif fon bulunamadı."
        
        # Sonuçları göster
        response += f"🏆 EN YÜKSEK INFORMATION RATIO'LU AKTİF FONLAR (Risk-Filtreli):\n\n"
        
        for i, fund in enumerate(ir_results[:10], 1):
            # IR kalitesi
            ir = fund['information_ratio']
            if ir > 1.0:
                quality = "🌟 ÜSTÜN"
            elif ir > 0.5:
                quality = "🟢 ÇOK İYİ"
            elif ir > 0:
                quality = "🟡 İYİ"
            else:
                quality = "🔴 ZAYIF"
            
            # Risk göstergesi
            risk_indicator = self._get_risk_indicator(fund['risk_level'])
            
            response += f"{i:2d}. {fund['fcode']} - {quality} {risk_indicator}\n"
            response += f"    📊 Information Ratio: {ir:.3f}\n"
            response += f"    📈 Aktif Getiri: %{fund['active_return']:.2f} (yıllık)\n"
            response += f"    📉 Tracking Error: %{fund['tracking_error']:.2f} (tahmini)\n"
            response += f"    💰 Toplam Getiri: %{fund['annual_return']:.1f}\n"
            response += f"    ⚡ Sharpe: {fund['sharpe_ratio']:.3f}\n"
            if fund['calmar_ratio'] > 0:
                response += f"    📊 Calmar: {fund['calmar_ratio']:.3f}\n"
            response += f"    🎯 Kazanma Oranı: %{fund['win_rate']:.1f}\n"
            response += f"    📊 MACD: {fund['macd_line']:.3f}\n"
            response += f"    🛡️ Risk Seviyesi: {fund['risk_level']} ({fund['risk_score']}/100)\n"
            response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
            
            # Risk faktörleri
            if fund['risk_factors'] and fund['risk_level'] in ['HIGH', 'EXTREME']:
                critical_risks = [f for f in fund['risk_factors'] if f['severity'] in ['CRITICAL', 'HIGH']]
                if critical_risks:
                    response += f"    ⚠️ Risk: {critical_risks[0]['description']}\n"
                    if 'action' in critical_risks[0]:
                        response += f"    → {critical_risks[0]['action']}\n"
            
            if fund['fund_name']:
                response += f"    📝 {fund['fund_name'][:40]}...\n"
            response += f"\n"
        
        # Risk uyarıları
        if high_risk_funds or blocked_extreme_funds:
            response += self._format_ir_risk_warnings(high_risk_funds, blocked_extreme_funds)
        
        # İstatistikler
        response += self._get_ir_statistics(ir_results, blocked_extreme_funds)
        
        # AI Yorumu
        if hasattr(self.coordinator, 'ai_provider') and self.coordinator.ai_provider.is_available():
            response += self._get_ai_commentary_for_ir_with_risk(ir_results, blocked_extreme_funds)
        
        return response
    
    def handle_sharpe_ratio_analysis(self, question):
        """Sharpe Oranı analizi - MV'den direkt okuma + RİSK KONTROLÜ"""
        print("📊 Sharpe oranı analiz ediliyor (MV + risk kontrolü ile)...")
        
        # Sharpe threshold belirleme
        threshold_match = re.search(r'(\d+\.?\d*)', question)
        sharpe_threshold = float(threshold_match.group(1)) if threshold_match else 0.5
        
        response = f"\n📊 SHARPE ORANI ANALİZİ (MV + RİSK KONTROLÜ)\n"
        response += f"{'='*60}\n\n"
        response += f"🎯 Sharpe oranı > {sharpe_threshold} olan fonlar aranıyor...\n"
        response += f"🛡️ Risk değerlendirmesi aktif\n"
        response += f"⚡ Materialized View'dan direkt okuma\n\n"
        
        sharpe_results = []
        high_risk_funds = []
        blocked_extreme_funds = []
        
        try:
            # MV'den direkt Sharpe oranı oku
            query = f"""
            SELECT 
                pm.fcode,
                pm.current_price,
                pm.annual_return * 100 as annual_return_pct,
                pm.annual_volatility * 100 as annual_volatility_pct,
                pm.sharpe_ratio,
                pm.calmar_ratio_approx,
                pm.win_rate * 100 as win_rate_pct,
                pm.worst_daily_return * 100 as worst_daily_return_pct,
                pm.best_daily_return * 100 as best_daily_return_pct,
                pm.trading_days,
                ti.rsi_14,
                ti.stochastic_14,
                ti.price_vs_sma20,
                ti.bb_position,
                ti.days_since_last_trade,
                ti.investorcount,
                ti.fcapacity,
                lf.ftitle as fund_name
            FROM mv_fund_performance_metrics pm
            JOIN mv_fund_technical_indicators ti ON pm.fcode = ti.fcode
            JOIN mv_latest_fund_data lf ON pm.fcode = lf.fcode
            WHERE pm.sharpe_ratio > {sharpe_threshold}
            AND pm.trading_days >= 60
            ORDER BY pm.sharpe_ratio DESC
            LIMIT 50
            """
            
            result = self.coordinator.db.execute_query(query)
            
            if not result.empty:
                print(f"   ✅ MV'den {len(result)} fon yüklendi (Sharpe > {sharpe_threshold})")
                
                for _, fund in result.iterrows():
                    fcode = fund['fcode']
                    
                    # Risk değerlendirmesi
                    risk_data = {
                        'fcode': fcode,
                        'price_vs_sma20': float(fund['price_vs_sma20']),
                        'rsi_14': float(fund['rsi_14']),
                        'stochastic_14': float(fund['stochastic_14']),
                        'days_since_last_trade': int(fund['days_since_last_trade']),
                        'investorcount': int(fund['investorcount'])
                    }
                    
                    risk_assessment = RiskAssessment.assess_fund_risk(risk_data)
                    risk_level = risk_assessment['risk_level']
                    
                    fund_result = {
                        'fcode': fcode,
                        'sharpe_ratio': float(fund['sharpe_ratio']),
                        'annual_return': float(fund['annual_return_pct']),
                        'volatility': float(fund['annual_volatility_pct']),
                        'calmar_ratio': float(fund['calmar_ratio_approx']) if pd.notna(fund['calmar_ratio_approx']) else 0,
                        'win_rate': float(fund['win_rate_pct']),
                        'worst_daily_return': float(fund['worst_daily_return_pct']),
                        'best_daily_return': float(fund['best_daily_return_pct']),
                        'bb_position': float(fund['bb_position']),
                        'current_price': float(fund['current_price']),
                        'investors': int(fund['investorcount']),
                        'capacity': float(fund['fcapacity']) if pd.notna(fund['fcapacity']) else 0,
                        'fund_name': fund['fund_name'],
                        'risk_level': risk_level,
                        'risk_factors': risk_assessment['risk_factors'],
                        'risk_score': risk_assessment['risk_score'],
                        'tradeable': risk_assessment.get('tradeable', True),
                        'requires_research': risk_assessment.get('requires_research', False)
                    }
                    
                    # Risk seviyesine göre kategorize et
                    if risk_level == 'EXTREME' or not fund_result['tradeable']:
                        blocked_extreme_funds.append(fund_result)
                    elif risk_level in ['HIGH']:
                        high_risk_funds.append(fund_result)
                        sharpe_results.append(fund_result)
                    else:
                        sharpe_results.append(fund_result)
                
                print(f"   📊 {len(sharpe_results)} güvenli/orta riskli fon bulundu")
                print(f"   ⚠️ {len(high_risk_funds)} yüksek riskli fon tespit edildi")
                print(f"   🚫 {len(blocked_extreme_funds)} extreme riskli/trade edilemez fon engellendi")
                
            else:
                return f"❌ Sharpe oranı > {sharpe_threshold} olan fon bulunamadı."
                
        except Exception as e:
            print(f"   ❌ MV sorgu hatası: {e}")
            return "❌ Sharpe oranı analizi yapılamadı."
        
        if not sharpe_results and not blocked_extreme_funds:
            return f"❌ Sharpe oranı > {sharpe_threshold} olan güvenli fon bulunamadı."
        
        # Sonuçları göster
        response += f"🏆 EN YÜKSEK SHARPE ORANLI FONLAR (Risk-Filtreli):\n\n"
        
        for i, fund in enumerate(sharpe_results[:10], 1):
            # Sharpe kalitesi
            sharpe = fund['sharpe_ratio']
            if sharpe > 2.0:
                quality = "🌟 EFSANE"
            elif sharpe > 1.5:
                quality = "⭐ MÜKEMMEL"
            elif sharpe > 1.0:
                quality = "🟢 ÇOK İYİ"
            elif sharpe > 0.5:
                quality = "🟡 İYİ"
            else:
                quality = "🟠 ORTA"
            
            # Risk göstergesi
            risk_indicator = self._get_risk_indicator(fund['risk_level'])
            
            response += f"{i:2d}. {fund['fcode']} - {quality} {risk_indicator}\n"
            response += f"    ⚡ Sharpe Oranı: {sharpe:.3f}\n"
            response += f"    📈 Yıllık Getiri: %{fund['annual_return']:.1f}\n"
            response += f"    📉 Volatilite: %{fund['volatility']:.1f}\n"
            if fund['calmar_ratio'] > 0:
                response += f"    📊 Calmar: {fund['calmar_ratio']:.3f}\n"
            response += f"    🎯 Kazanma Oranı: %{fund['win_rate']:.1f}\n"
            response += f"    📊 En Kötü/İyi Gün: %{fund['worst_daily_return']:.1f} / %{fund['best_daily_return']:.1f}\n"
            response += f"    📊 BB Pozisyon: {fund['bb_position']:.2f}\n"
            response += f"    🛡️ Risk Seviyesi: {fund['risk_level']} ({fund['risk_score']}/100)\n"
            
            if fund['requires_research']:
                response += f"    ⚠️ Yatırım öncesi araştırma önerilir!\n"
            
            response += f"    💰 Büyüklük: {fund['capacity']/1e9:.1f} Milyar TL\n"
            response += f"    👥 Yatırımcı: {fund['investors']:,} kişi\n"
            response += f"    💲 Fiyat: {fund['current_price']:.4f} TL\n"
            
            # Risk faktörleri
            if fund['risk_factors']:
                critical_risks = [f for f in fund['risk_factors'] if f['severity'] in ['CRITICAL', 'HIGH']]
                if critical_risks:
                    response += f"    ⚠️ Risk: {critical_risks[0]['description']}\n"
                    if 'action' in critical_risks[0]:
                        response += f"    → {critical_risks[0]['action']}\n"
                    if 'opportunity' in critical_risks[0]:
                        response += f"    💡 {critical_risks[0]['opportunity']}\n"
            
            if fund['fund_name']:
                response += f"    📝 {fund['fund_name'][:40]}...\n"
            response += f"\n"
        
        # Risk uyarıları
        if high_risk_funds or blocked_extreme_funds:
            response += self._format_sharpe_risk_warnings(high_risk_funds, blocked_extreme_funds)
        
        # İstatistikler
        response += self._get_sharpe_statistics(sharpe_results, blocked_extreme_funds, sharpe_threshold)
        
        return response
    
    # === YARDIMCI METODLAR ===
    
    def _get_fund_risk_data(self, fcode):
        """Fonun risk verilerini MV'den çek"""
        try:
            query = f"""
            SELECT 
                price_vs_sma20,
                rsi_14,
                stochastic_14,
                days_since_last_trade,
                investorcount
            FROM mv_fund_technical_indicators
            WHERE fcode = '{fcode}'
            """
            
            result = self.coordinator.db.execute_query(query)
            
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
    
    def _check_beta_condition(self, beta, threshold, comparison):
        """Beta koşulunu kontrol et"""
        if comparison == "<":
            return beta < threshold
        elif comparison == ">":
            return beta > threshold
        elif comparison == "<=":
            return beta <= threshold
        elif comparison == ">=":
            return beta >= threshold
        else:
            return beta == threshold
    
    # Mevcut yardımcı metodlar aynen kalacak...
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
    
    # === FALLBACK METODLARI ===
    
    def _handle_beta_analysis_fallback(self, question, beta_threshold, comparison):
        """Beta analizi fallback metodu - MV olmadan"""
        print("   🔄 Fallback: Klasik beta analizi...")
        
        # Mevcut implementasyondan kısaltılmış versiyon
        response = f"\n📊 BETA KATSAYISI ANALİZİ (Klasik Yöntem)\n"
        response += f"{'='*60}\n\n"
        response += f"⚠️ MV kullanılamadı, sınırlı analiz yapılıyor...\n\n"
        
        # Sadece ilk 20 fon için hesapla
        beta_results = []
        benchmark_data = self._get_benchmark_data()
        
        if benchmark_data is None:
            return "❌ Benchmark verisi alınamadı. Beta hesaplaması yapılamıyor."
        
        for fcode in self.active_funds[:20]:
            try:
                fund_data = self.coordinator.db.get_fund_price_history(fcode, 120)
                if len(fund_data) >= 30:
                    beta = self._calculate_beta(fund_data, benchmark_data)
                    if beta and self._check_beta_condition(beta, beta_threshold, comparison):
                        beta_results.append({
                            'fcode': fcode,
                            'beta': beta,
                            'current_price': fund_data['price'].iloc[-1]
                        })
            except:
                continue
        
        if not beta_results:
            return f"❌ Beta {comparison} {beta_threshold} olan fon bulunamadı."
        
        response += f"🏆 İLK {len(beta_results)} FON:\n\n"
        for i, fund in enumerate(beta_results[:5], 1):
            response += f"{i}. {fund['fcode']} - Beta: {fund['beta']:.3f}\n"
        
        return response
    
    def _handle_alpha_analysis_fallback(self, question, is_positive):
        """Alpha analizi fallback metodu"""
        return "❌ Alpha analizi şu anda yapılamıyor. Lütfen daha sonra tekrar deneyin."
    
    def _handle_tracking_error_fallback(self, question):
        """Tracking error fallback metodu"""
        return "❌ Tracking error analizi şu anda yapılamıyor."
    
    def _handle_information_ratio_fallback(self, question):
        """Information ratio fallback metodu"""
        return "❌ Information ratio analizi şu anda yapılamıyor."
    
    # === FORMATLAMA METODLARI ===
    
    def _get_beta_statistics(self, beta_results, blocked_funds, comparison, threshold):
        """Beta istatistikleri"""
        safe_funds = [f for f in beta_results if f['risk_level'] in ['LOW', 'MEDIUM']]
        
        if not beta_results:
            return ""
        
        avg_beta = sum(f['beta'] for f in beta_results) / len(beta_results)
        avg_return = sum(f['annual_return'] for f in beta_results) / len(beta_results)
        
        response = f"\n📊 BETA İSTATİSTİKLERİ (Risk-Filtreli):\n"
        response += f"   🔢 Toplam Bulunan: {len(beta_results) + len(blocked_funds)} fon\n"
        response += f"   ✅ Güvenli/Orta: {len(safe_funds)} fon\n"
        response += f"   🔴 Extreme (Engellenen): {len(blocked_funds)} fon\n"
        response += f"   📊 Ortalama Beta: {avg_beta:.3f}\n"
        response += f"   📈 Ortalama Getiri: %{avg_return:.1f}\n"
        
        if safe_funds:
            safest_beta = min(safe_funds, key=lambda x: abs(x['beta'] - 1))
            response += f"   🛡️ En Güvenli: {safest_beta['fcode']} (Beta: {safest_beta['beta']:.3f}, {safest_beta['risk_level']})\n"
        
        return response
    
    def _format_high_risk_alpha_funds(self, high_risk_funds):
        """Yüksek riskli alpha fonları formatla"""
        response = f"\n🟠 YÜKSEK RİSKLİ ALPHA FONLARI ({len(high_risk_funds)} adet):\n"
        response += f"   ⚠️ Yüksek alpha ama aynı zamanda yüksek risk!\n\n"
        
        for i, fund in enumerate(high_risk_funds[:3], 1):
            risk_factors = [f['description'] for f in fund['risk_factors'][:2]]
            response += f"   {i}. {fund['fcode']} - Alpha: %{fund['alpha']:.2f}\n"
            response += f"      ⚠️ Riskler: {', '.join(risk_factors)}\n"
        response += f"\n"
        
        return response
    
    def _format_extreme_risk_alpha_funds(self, blocked_funds):
        """Extreme riskli alpha fonları formatla"""
        response = f"\n🔴 EXTREME RİSKLİ ALPHA FONLARI - ÖNERİLMİYOR ({len(blocked_funds)} adet):\n"
        response += f"   ❌ Yüksek alpha olsa bile extreme risk nedeniyle önerilmiyor!\n\n"
        
        for i, fund in enumerate(blocked_funds[:3], 1):
            response += f"   {i}. {fund['fcode']} - Alpha: %{fund['alpha']:.2f} - ENGELLENEN\n"
            if fund.get('risk_factors'):
                critical = [f for f in fund['risk_factors'] if f['severity'] == 'CRITICAL']
                if critical:
                    response += f"      🚨 {critical[0]['description']}\n"
        response += f"\n"
        
        return response
    
    def _get_alpha_statistics(self, alpha_results, blocked_funds, is_positive):
        """Alpha istatistikleri"""
        safe_funds = [f for f in alpha_results if f['risk_level'] in ['LOW', 'MEDIUM']]
        
        if not alpha_results:
            return ""
        
        avg_alpha = sum(f['alpha'] for f in alpha_results) / len(alpha_results)
        positive_alpha_count = sum(1 for f in alpha_results if f['alpha'] > 0)
        
        response = f"\n📊 ALPHA İSTATİSTİKLERİ (Risk-Filtreli):\n"
        response += f"   🔢 Toplam Bulunan: {len(alpha_results) + len(blocked_funds)} fon\n"
        response += f"   ✅ Güvenli Pozitif Alpha: {len([f for f in safe_funds if f['alpha'] > 0])} fon\n"
        response += f"   🔴 Extreme (Engellenen): {len(blocked_funds)} fon\n"
        response += f"   📊 Ortalama Alpha: %{avg_alpha:.2f}\n"
        response += f"   📈 Pozitif Alpha: {positive_alpha_count} fon\n"
        
        if safe_funds and any(f['alpha'] > 0 for f in safe_funds):
            best_safe = max([f for f in safe_funds if f['alpha'] > 0], key=lambda x: x['alpha'])
            response += f"   🛡️ En Güvenli Pozitif: {best_safe['fcode']} (Alpha: %{best_safe['alpha']:.2f}, {best_safe['risk_level']})\n"
        
        return response
    
    def _format_tracking_error_risk_warnings(self, high_risk_funds, blocked_funds):
        """Tracking error risk uyarıları"""
        response = ""
        
        if high_risk_funds:
            response += f"\n🟠 YÜKSEK RİSKLİ INDEX FONLARI ({len(high_risk_funds)} adet):\n"
            response += f"   ⚠️ Düşük tracking error ama yüksek risk!\n\n"
            
            for i, fund in enumerate(high_risk_funds[:3], 1):
                response += f"   {i}. {fund['fcode']} - TE: %{fund['tracking_error']:.2f}\n"
            response += f"\n"
        
        if blocked_funds:
            response += f"\n🔴 EXTREME RİSKLİ INDEX FONLARI - ÖNERİLMİYOR ({len(blocked_funds)} adet):\n"
            response += f"   ❌ Index fon olsa bile extreme risk nedeniyle önerilmiyor!\n\n"
            
            for i, fund in enumerate(blocked_funds[:3], 1):
                response += f"   {i}. {fund['fcode']} - TE: %{fund['tracking_error']:.2f} - ENGELLENEN\n"
                if fund.get('risk_factors'):
                    critical = [f for f in fund['risk_factors'] if f['severity'] == 'CRITICAL']
                    if critical and 'action' in critical[0]:
                        response += f"      → {critical[0]['action']}\n"
            response += f"\n"
        
        return response
    
    def _get_tracking_error_statistics(self, te_results, blocked_funds):
        """Tracking error istatistikleri"""
        safe_funds = [f for f in te_results if f['risk_level'] in ['LOW', 'MEDIUM']]
        
        if not te_results:
            return ""
        
        avg_te = sum(f['tracking_error'] for f in te_results) / len(te_results)
        avg_correlation = sum(f['correlation'] for f in te_results) / len(te_results)
        
        response = f"\n📊 TRACKING ERROR İSTATİSTİKLERİ (Risk-Filtreli):\n"
        response += f"   🔢 Analiz Edilen: {len(te_results) + len(blocked_funds)} index fon\n"
        response += f"   ✅ Güvenli Index: {len(safe_funds)} fon\n"
        response += f"   🔴 Extreme (Engellenen): {len(blocked_funds)} fon\n"
        response += f"   📊 Ortalama Tracking Error: %{avg_te:.2f}\n"
        response += f"   🔗 Ortalama Korelasyon: {avg_correlation:.3f}\n"
        
        if safe_funds:
            best_safe = min(safe_funds, key=lambda x: x['tracking_error'])
            response += f"   🛡️ En Güvenli En İyi: {best_safe['fcode']} (TE: %{best_safe['tracking_error']:.2f}, {best_safe['risk_level']})\n"
        
        return response
    
    def _format_ir_risk_warnings(self, high_risk_funds, blocked_funds):
        """Information ratio risk uyarıları"""
        response = ""
        
        if high_risk_funds:
            response += f"\n🟠 YÜKSEK RİSKLİ IR FONLARI ({len(high_risk_funds)} adet):\n"
            response += f"   ⚠️ Yüksek IR ama aynı zamanda yüksek risk!\n\n"
            
            for i, fund in enumerate(high_risk_funds[:3], 1):
                response += f"   {i}. {fund['fcode']} - IR: {fund['information_ratio']:.3f}\n"
                if fund.get('risk_factors'):
                    risks = [f['description'] for f in fund['risk_factors'][:1]]
                    response += f"      ⚠️ {risks[0]}\n"
            response += f"\n"
        
        if blocked_funds:
            response += f"\n🔴 EXTREME RİSKLİ IR FONLARI - ÖNERİLMİYOR ({len(blocked_funds)} adet):\n"
            response += f"   ❌ Yüksek IR olsa bile extreme risk nedeniyle önerilmiyor!\n\n"
            
            for i, fund in enumerate(blocked_funds[:3], 1):
                response += f"   {i}. {fund['fcode']} - IR: {fund['information_ratio']:.3f} - ENGELLENEN\n"
                if fund.get('risk_factors'):
                    critical = [f for f in fund['risk_factors'] if f['severity'] == 'CRITICAL']
                    if critical:
                        response += f"      🚨 {critical[0]['description']}\n"
            response += f"\n"
        
        return response
    
    def _get_ir_statistics(self, ir_results, blocked_funds):
        """Information ratio istatistikleri"""
        safe_funds = [f for f in ir_results if f['risk_level'] in ['LOW', 'MEDIUM']]
        
        if not ir_results:
            return ""
        
        avg_ir = sum(f['information_ratio'] for f in ir_results) / len(ir_results)
        positive_ir_count = sum(1 for f in ir_results if f['information_ratio'] > 0)
        
        response = f"\n📊 INFORMATION RATIO İSTATİSTİKLERİ (Risk-Filtreli):\n"
        response += f"   🔢 Analiz Edilen: {len(ir_results) + len(blocked_funds)} aktif fon\n"
        response += f"   ✅ Güvenli Pozitif IR: {len([f for f in safe_funds if f['information_ratio'] > 0])} fon\n"
        response += f"   🔴 Extreme (Engellenen): {len(blocked_funds)} fon\n"
        response += f"   📊 Ortalama IR: {avg_ir:.3f}\n"
        response += f"   📈 Pozitif IR: {positive_ir_count} fon\n"
        
        if safe_funds and any(f['information_ratio'] > 0 for f in safe_funds):
            best_safe = max([f for f in safe_funds if f['information_ratio'] > 0], key=lambda x: x['information_ratio'])
            response += f"   🛡️ En Güvenli En İyi: {best_safe['fcode']} (IR: {best_safe['information_ratio']:.3f}, {best_safe['risk_level']})\n"
        
        return response
    
    def _format_sharpe_risk_warnings(self, high_risk_funds, blocked_funds):
        """Sharpe risk uyarıları"""
        response = ""
        
        if high_risk_funds:
            response += f"\n🟠 YÜKSEK RİSKLİ SHARPE FONLARI ({len(high_risk_funds)} adet):\n"
            response += f"   ⚠️ Yüksek Sharpe ama aynı zamanda yüksek risk!\n\n"
            
            for i, fund in enumerate(high_risk_funds[:3], 1):
                response += f"   {i}. {fund['fcode']} - Sharpe: {fund['sharpe_ratio']:.3f}\n"
                if fund.get('risk_factors'):
                    risks = [f['description'] for f in fund['risk_factors'][:1]]
                    response += f"      ⚠️ {risks[0]}\n"
            response += f"\n"
        
        if blocked_funds:
            response += f"\n🔴 EXTREME RİSKLİ SHARPE FONLARI - ÖNERİLMİYOR ({len(blocked_funds)} adet):\n"
            response += f"   ❌ Yüksek Sharpe olsa bile extreme risk nedeniyle önerilmiyor!\n"
            response += f"   🚨 Bu fonlar trade edilemez durumda olabilir!\n\n"
            
            for i, fund in enumerate(blocked_funds[:3], 1):
                response += f"   {i}. {fund['fcode']} - Sharpe: {fund['sharpe_ratio']:.3f} - ENGELLENEN\n"
                if fund.get('risk_factors'):
                    critical = [f for f in fund['risk_factors'] if f['severity'] == 'CRITICAL']
                    if critical:
                        response += f"      🚨 {critical[0]['description']}\n"
                        if 'action' in critical[0]:
                            response += f"      → {critical[0]['action']}\n"
            response += f"\n"
        
        return response
    
    def _get_sharpe_statistics(self, sharpe_results, blocked_funds, threshold):
        """Sharpe istatistikleri"""
        safe_funds = [f for f in sharpe_results if f['risk_level'] in ['LOW', 'MEDIUM']]
        tradeable_funds = [f for f in sharpe_results if f.get('tradeable', True)]
        
        if not sharpe_results:
            return ""
        
        avg_sharpe = sum(f['sharpe_ratio'] for f in sharpe_results) / len(sharpe_results)
        
        response = f"\n📊 SHARPE ORANI İSTATİSTİKLERİ (Risk-Filtreli):\n"
        response += f"   🔢 Toplam Bulunan: {len(sharpe_results) + len(blocked_funds)} fon\n"
        response += f"   ✅ Güvenli Yüksek Sharpe: {len(safe_funds)} fon\n"
        response += f"   💼 Trade Edilebilir: {len(tradeable_funds)} fon\n"
        response += f"   🔴 Extreme/Trade Edilemez: {len(blocked_funds)} fon\n"
        response += f"   📊 Ortalama Sharpe: {avg_sharpe:.3f}\n"
        
        if safe_funds:
            best_safe = max(safe_funds, key=lambda x: x['sharpe_ratio'])
            response += f"   🛡️ En Güvenli En İyi: {best_safe['fcode']} (Sharpe: {best_safe['sharpe_ratio']:.3f}, {best_safe['risk_level']})\n"
        
        return response
    
    # === AI YORUM METODLARI ===
    
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

# =============================================================
# DEMO VE TEST FONKSİYONLARI
# =============================================================

def demo_advanced_metrics_analysis():
    """Demo fonksiyon - Advanced metrics testleri"""
    print("\n" + "="*70)
    print("ADVANCED METRICS ANALYZER DEMO (MV + Risk Assessment)")
    print("="*70 + "\n")
    
    # Dummy coordinator ve data
    class DummyCoordinator:
        class db:
            @staticmethod
            def execute_query(query):
                return pd.DataFrame()
            
            @staticmethod
            def get_fund_price_history(fcode, days):
                return pd.DataFrame({
                    'pdate': pd.date_range(end=pd.Timestamp.now(), periods=days),
                    'price': np.random.randn(days).cumsum() + 100
                })
    
    coordinator = DummyCoordinator()
    active_funds = ['TI2', 'TKF', 'GAF', 'AAK', 'AES']
    ai_status = {'available': False}
    
    analyzer = AdvancedMetricsAnalyzer(coordinator, active_funds, ai_status)
    
    # Test soruları
    test_questions = [
        ("Beta katsayısı 1'den düşük fonlar", analyzer.handle_beta_analysis),
        ("Alpha değeri pozitif olan fonlar", analyzer.handle_alpha_analysis),
        ("Sharpe oranı 0.7'den yüksek fonlar", analyzer.handle_sharpe_ratio_analysis),
        ("Tracking error düşük index fonlar", analyzer.handle_tracking_error_analysis),
        ("Information ratio yüksek aktif fonlar", analyzer.handle_information_ratio_analysis)
    ]
    
    for i, (question, handler) in enumerate(test_questions, 1):
        print(f"\n[TEST {i}/5] {question}")
        print("-" * 50)
        
        try:
            # Sadece ilk 200 karakteri göster
            result = handler(question)
            preview = result[:200] + "..." if len(result) > 200 else result
            print(preview)
            print("✅ Test başarılı")
        except Exception as e:
            print(f"❌ Test hatası: {e}")
    
    print("\n🎉 Advanced Metrics Analyzer demo tamamlandı!")

# =============================================================
# CONFIGURATION
# =============================================================

ADVANCED_METRICS_CONFIG = {
    'beta': {
        'min_data_points': 30,
        'max_beta_value': 5.0,
        'benchmark_funds': ['TI2', 'TKF', 'GAF'],
        'default_threshold': 1.0
    },
    'alpha': {
        'risk_free_rate': 0.15,  # %15
        'min_r_squared': 0.3,
        'confidence_level': 0.95
    },
    'sharpe': {
        'risk_free_rate': 0.15,
        'annualization_factor': 252,
        'min_threshold': 0.0
    },
    'tracking_error': {
        'max_acceptable_te': 10.0,  # %10
        'index_keywords': ['index', 'endeks', 'bist', 'xu100'],
        'correlation_threshold': 0.8
    },
    'information_ratio': {
        'min_active_return': 0.0,
        'max_tracking_error': 50.0,
        'exclude_index_funds': True
    },
    'risk_assessment': {
        'use_mv_data': True,
        'fallback_on_error': True,
        'cache_duration': 3600  # 1 saat
    }
}

# =============================================================
# HELPER FUNCTIONS
# =============================================================

def calculate_maximum_drawdown(returns):
    """Maximum drawdown hesapla"""
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    return abs(drawdown.min())

def calculate_sortino_ratio(returns, risk_free_rate=0.15):
    """Sortino ratio hesapla (sadece downside risk)"""
    excess_returns = returns - risk_free_rate/252
    downside_returns = excess_returns[excess_returns < 0]
    
    if len(downside_returns) == 0:
        return 0
    
    downside_deviation = np.sqrt(np.mean(downside_returns**2))
    
    if downside_deviation == 0:
        return 0
    
    return (returns.mean() - risk_free_rate/252) * np.sqrt(252) / downside_deviation

def calculate_calmar_ratio(returns, period_years=3):
    """Calmar ratio hesapla (return / max drawdown)"""
    annualized_return = (1 + returns.mean()) ** 252 - 1
    max_dd = calculate_maximum_drawdown(returns)
    
    if max_dd == 0:
        return 0
    
    return annualized_return / max_dd

# =============================================================
# EXPORT
# =============================================================

__all__ = [
    'AdvancedMetricsAnalyzer',
    'demo_advanced_metrics_analysis',
    'ADVANCED_METRICS_CONFIG',
    'calculate_maximum_drawdown',
    'calculate_sortino_ratio',
    'calculate_calmar_ratio'
]

if __name__ == "__main__":
    demo_advanced_metrics_analysis()