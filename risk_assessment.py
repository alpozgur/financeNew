# utils.py veya yeni bir risk_assessment.py dosyasına ekleyin

class RiskAssessment:
    """Ekstrem durum ve risk değerlendirmesi"""
    
    @staticmethod
    def assess_fund_risk(fund_data):
        """
        Fon risk değerlendirmesi
        
        Args:
            fund_data: Dict containing fund metrics from MV
            
        Returns:
            Dict with risk assessment
        """
        risk_factors = []
        risk_score = 0
        
        # 1. Ekstrem fiyat düşüşü kontrolü (DNO durumu)
        price_vs_sma20 = fund_data.get('price_vs_sma20', 0)
        if price_vs_sma20 < -70:
            risk_factors.append({
                'factor': 'EXTREME_PRICE_DROP',
                'severity': 'CRITICAL',
                'description': f'Fiyat SMA20\'nin %{abs(price_vs_sma20):.1f} altında',
                'action': 'Manuel araştırma gerekli - İflas/delisting riski'
            })
            risk_score += 40  # Daha yüksek ağırlık
        elif price_vs_sma20 < -30:
            risk_factors.append({
                'factor': 'SIGNIFICANT_PRICE_DROP',
                'severity': 'HIGH',
                'description': f'Fiyat SMA20\'nin %{abs(price_vs_sma20):.1f} altında'
            })
            risk_score += 25  # Daha yüksek ağırlık
            
        # 2. RSI/Stochastic uyumsuzluğu
        rsi = fund_data.get('rsi_14', 50)
        stoch = fund_data.get('stochastic_14', 50)
        
        if abs(rsi - stoch) > 80:
            if stoch > 90 and rsi < 10:
                risk_factors.append({
                    'factor': 'POST_CRASH_RECOVERY',
                    'severity': 'HIGH',
                    'description': 'Büyük düşüş sonrası toparlanma başlangıcı',
                    'opportunity': 'Spekülatif alım fırsatı olabilir'
                })
                risk_score += 30  # Daha yüksek ağırlık
            elif stoch < 10 and rsi > 90:
                risk_factors.append({
                    'factor': 'OVERBOUGHT_CONSOLIDATION',
                    'severity': 'MEDIUM',
                    'description': 'Hızlı yükseliş sonrası konsolidasyon'
                })
                risk_score += 20  # Daha yüksek ağırlık
                
        # 3. İşlem aktivitesi kontrolü - Daha sıkı
        days_inactive = fund_data.get('days_since_last_trade', 0)
        if days_inactive > 20:  # 30'dan 20'ye düşürüldü
            risk_factors.append({
                'factor': 'INACTIVE_FUND',
                'severity': 'HIGH',
                'description': f'{days_inactive} gündür işlem görmemiş',
                'action': 'Likidite riski - Alım/satım zor olabilir'
            })
            risk_score += 35  # Daha yüksek ağırlık
        elif days_inactive > 10:  # 14'ten 10'a düşürüldü
            risk_factors.append({
                'factor': 'LOW_ACTIVITY',
                'severity': 'MEDIUM',
                'description': f'{days_inactive} gündür işlem görmemiş'
            })
            risk_score += 15  # Daha yüksek ağırlık
            
        # 4. Yatırımcı sayısı kontrolü - Daha sıkı
        investors = fund_data.get('investorcount', 0)
        if investors < 50:  # 10'dan 50'ye yükseltildi
            risk_factors.append({
                'factor': 'LOW_INVESTOR_COUNT',
                'severity': 'HIGH',
                'description': f'Sadece {investors} yatırımcı',
                'action': 'Yüksek likidite riski'
            })
            risk_score += 30  # Daha yüksek ağırlık
        elif investors < 100:  # Yeni eşik
            risk_factors.append({
                'factor': 'MEDIUM_INVESTOR_COUNT',
                'severity': 'MEDIUM',
                'description': f'Düşük yatırımcı sayısı: {investors}'
            })
            risk_score += 15
            
        # 5. Volatilite kontrolü - Yeni faktör
        volatility = fund_data.get('volatility', 0)
        if volatility > 40:  # Yüksek volatilite
            risk_factors.append({
                'factor': 'HIGH_VOLATILITY',
                'severity': 'HIGH',
                'description': f'Yüksek volatilite: %{volatility:.1f}'
            })
            risk_score += 25
        elif volatility > 25:  # Orta volatilite
            risk_factors.append({
                'factor': 'MEDIUM_VOLATILITY',
                'severity': 'MEDIUM',
                'description': f'Orta volatilite: %{volatility:.1f}'
            })
            risk_score += 15
            
        # Risk seviyesi belirleme - Daha sıkı eşikler
        if risk_score >= 40:  # 50'den 40'a düşürüldü
            risk_level = "EXTREME"
        elif risk_score >= 25:  # 30'dan 25'e düşürüldü
            risk_level = "HIGH"
        elif risk_score >= 15:  # Aynı kaldı
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'tradeable': risk_score < 40,  # 50'den 40'a düşürüldü
            'requires_research': risk_score >= 25  # 30'dan 25'e düşürüldü
        }
    
    @staticmethod
    def format_risk_warning(risk_assessment):
        """Risk uyarısını formatla"""
        if not risk_assessment['risk_factors']:
            return ""
            
        warning = "\n⚠️ RİSK UYARILARI:\n"
        warning += "="*40 + "\n"
        
        for factor in risk_assessment['risk_factors']:
            icon = "🔴" if factor['severity'] == 'CRITICAL' else "🟠" if factor['severity'] == 'HIGH' else "🟡"
            warning += f"{icon} {factor['description']}\n"
            
            if 'action' in factor:
                warning += f"   → {factor['action']}\n"
            if 'opportunity' in factor:
                warning += f"   💡 {factor['opportunity']}\n"
                
        warning += f"\n📊 Risk Skoru: {risk_assessment['risk_score']}/100"
        warning += f"\n🎯 Risk Seviyesi: {risk_assessment['risk_level']}"
        
        if not risk_assessment['tradeable']:
            warning += "\n\n❌ BU FON ŞU ANDA TRADE EDİLMEMELİ!"
        elif risk_assessment['requires_research']:
            warning += "\n\n⚠️ Yatırım öncesi detaylı araştırma yapın!"
            
        return warning