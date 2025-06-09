"""
TEFAS Analysis System - Automated QA Test Script
Sisteme sorulabilecek tüm soru tiplerini test eder ve sonuçları kaydeder
"""

import os
import sys
import time
import json
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import your system
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TEFASAutomatedQATester:
    """
    TEFAS sistemini otomatik test eden QA scripti
    """
    
    def __init__(self):
        self.test_results = []
        self.test_timestamp = datetime.now()
        self.output_file = f"tefas_qa_test_results_{self.test_timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
        self.json_file = f"tefas_qa_test_results_{self.test_timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        self.qa_system = None
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def initialize_system(self):
        """TEFAS sistemini başlat"""
        try:
            print("🚀 TEFAS Q&A sistemi başlatılıyor...")
            from interactive_qa_dual_ai import DualAITefasQA
            self.qa_system = DualAITefasQA()
            print("✅ Sistem başarıyla yüklendi!")
            return True
        except Exception as e:
            print(f"❌ Sistem başlatma hatası: {e}")
            traceback.print_exc()
            return False
    
    def get_all_test_questions(self) -> List[Dict[str, Any]]:
        """
        Sisteminize özel tüm test sorularını içerir
        """
        
        test_questions = []
        
        # 1. PERFORMANCE ANALYZER TESTLERİ
        test_questions.extend([
            # Güvenli fonlar
            {"category": "Performance", "question": "en güvenli fon", "handler": "performance_analyzer", "method": "handle_safest_fund"},
            {"category": "Performance", "question": "en güvenli 5 fon", "handler": "performance_analyzer", "method": "handle_safest_funds_sql_fast"},
            {"category": "Performance", "question": "en güvenli 10 fon listesi", "handler": "performance_analyzer", "method": "handle_safest_funds_sql_fast"},
            {"category": "Performance", "question": "en az riskli fonlar", "handler": "performance_analyzer", "method": "handle_safest_funds_sql_fast"},
            {"category": "Performance", "question": "güvenli fonlar hangileri", "handler": "performance_analyzer", "method": "handle_safest_funds_sql_fast"},
            
            # Riskli fonlar
            {"category": "Performance", "question": "en riskli fon", "handler": "performance_analyzer", "method": "handle_most_risky_fund"},
            {"category": "Performance", "question": "en riskli 10 fon", "handler": "performance_analyzer", "method": "handle_riskiest_funds_list"},
            {"category": "Performance", "question": "yüksek riskli fonlar", "handler": "performance_analyzer", "method": "handle_riskiest_funds_list"},
            
            # Kazandıran fonlar
            {"category": "Performance", "question": "en çok kazandıran fon", "handler": "performance_analyzer", "method": "handle_top_gainer_fund_question"},
            {"category": "Performance", "question": "en çok kazandıran 5 fon", "handler": "performance_analyzer", "method": "handle_top_gainers"},
            {"category": "Performance", "question": "en çok getiri sağlayan fonlar", "handler": "performance_analyzer", "method": "handle_top_gainers"},
            {"category": "Performance", "question": "bu ay en çok kazandıran fonlar", "handler": "performance_analyzer", "method": "handle_top_gainers"},
            
            # Kaybettiren fonlar
            {"category": "Performance", "question": "en çok kaybettiren fon", "handler": "performance_analyzer", "method": "handle_worst_fund"},
            {"category": "Performance", "question": "en çok kaybettiren 10 fon", "handler": "performance_analyzer", "method": "handle_worst_funds_list"},
            {"category": "Performance", "question": "en çok düşen fonlar", "handler": "performance_analyzer", "method": "handle_worst_funds_list"},
            
            # Fon analizi - Çeşitli fon kodları
            {"category": "Performance", "question": "AKB", "handler": "performance_analyzer", "method": "handle_analysis_question_dual"},
            {"category": "Performance", "question": "TYH analiz", "handler": "performance_analyzer", "method": "handle_analysis_question_dual"},
            {"category": "Performance", "question": "YAS fonunu incele", "handler": "performance_analyzer", "method": "handle_analysis_question_dual"},
            {"category": "Performance", "question": "IPB fonu nasıl", "handler": "performance_analyzer", "method": "handle_analysis_question_dual"},
            {"category": "Performance", "question": "GAF fonunu değerlendir", "handler": "performance_analyzer", "method": "handle_analysis_question_dual"},
            {"category": "Performance", "question": "TCD fon analizi yap", "handler": "performance_analyzer", "method": "handle_analysis_question_dual"},
            
            # Karşılaştırmalar
            {"category": "Performance", "question": "AKB vs TYH", "handler": "performance_analyzer", "method": "handle_comparison_question"},
            {"category": "Performance", "question": "YAS ve IPB karşılaştır", "handler": "performance_analyzer", "method": "handle_comparison_question"},
            {"category": "Performance", "question": "GAF ile TCD karşılaştırması", "handler": "performance_analyzer", "method": "handle_comparison_question"},
            
            # 2025 önerileri
            {"category": "Performance", "question": "2025 için hangi fonları önerirsin", "handler": "performance_analyzer", "method": "handle_2025_recommendation_dual"},
            {"category": "Performance", "question": "2025 yılı için en iyi fonlar", "handler": "performance_analyzer", "method": "handle_2025_recommendation_dual"},
            {"category": "Performance", "question": "2025 fon önerileri", "handler": "performance_analyzer", "method": "handle_2025_recommendation_dual"},
            
            # Sharpe oranı
            {"category": "Performance", "question": "sharpe oranı en yüksek fonlar", "handler": "performance_analyzer", "method": "handle_top_sharpe_funds_question"},
            {"category": "Performance", "question": "en yüksek sharpe oranına sahip 5 fon", "handler": "performance_analyzer", "method": "handle_top_sharpe_funds_question"},
            
            # Volatilite
            {"category": "Performance", "question": "volatilite %10 altında fonlar", "handler": "performance_analyzer", "method": "handle_low_volatility_funds_question"},
            {"category": "Performance", "question": "düşük volatiliteli fonlar", "handler": "performance_analyzer", "method": "handle_low_volatility_funds_question"},
            
            # Geçmiş performans
            {"category": "Performance", "question": "AKB son 1 yıl getirisi", "handler": "performance_analyzer", "method": "handle_fund_past_performance_question"},
            {"category": "Performance", "question": "TYH geçtiğimiz yıl kazancı", "handler": "performance_analyzer", "method": "handle_fund_past_performance_question"},
        ])
        
        # 2. TECHNICAL ANALYZER TESTLERİ
        test_questions.extend([
            # MACD
            {"category": "Technical", "question": "MACD sinyali pozitif fonlar", "handler": "technical_analyzer", "method": "handle_macd_signals_sql"},
            {"category": "Technical", "question": "MACD negatif olan fonlar", "handler": "technical_analyzer", "method": "handle_macd_signals_sql"},
            {"category": "Technical", "question": "en güçlü MACD sinyali veren fonlar", "handler": "technical_analyzer", "method": "handle_macd_signals_sql"},
            
            # RSI
            {"category": "Technical", "question": "RSI 30 altında fonlar", "handler": "technical_analyzer", "method": "handle_rsi_signals_sql"},
            {"category": "Technical", "question": "RSI 70 üstünde fonlar", "handler": "technical_analyzer", "method": "handle_rsi_signals_sql"},
            {"category": "Technical", "question": "aşırı satım bölgesindeki fonlar", "handler": "technical_analyzer", "method": "handle_rsi_signals_sql"},
            {"category": "Technical", "question": "aşırı alım bölgesindeki fonlar", "handler": "technical_analyzer", "method": "handle_rsi_signals_sql"},
            
            # Bollinger
            {"category": "Technical", "question": "bollinger alt banda yakın fonlar", "handler": "technical_analyzer", "method": "handle_bollinger_signals_sql"},
            {"category": "Technical", "question": "bollinger üst banda yakın fonlar", "handler": "technical_analyzer", "method": "handle_bollinger_signals_sql"},
            {"category": "Technical", "question": "bollinger bantları daralma gösteren fonlar", "handler": "technical_analyzer", "method": "handle_bollinger_signals_sql"},
            
            # Moving Averages
            {"category": "Technical", "question": "golden cross oluşan fonlar", "handler": "technical_analyzer", "method": "handle_moving_average_signals_sql"},
            {"category": "Technical", "question": "death cross olan fonlar", "handler": "technical_analyzer", "method": "handle_moving_average_signals_sql"},
            {"category": "Technical", "question": "50 günlük hareketli ortalama üstünde fonlar", "handler": "technical_analyzer", "method": "handle_moving_average_signals_sql"},
            
            # AI Pattern
            {"category": "Technical", "question": "AI pattern analizi ile AKB", "handler": "technical_analyzer", "method": "handle_ai_pattern_analysis"},
            {"category": "Technical", "question": "TYH için AI teknik analiz", "handler": "technical_analyzer", "method": "handle_ai_pattern_analysis"},
            {"category": "Technical", "question": "AI pattern ile YAS fonu", "handler": "technical_analyzer", "method": "handle_ai_pattern_analysis"},
            
            # Genel teknik sinyal
            {"category": "Technical", "question": "teknik alım sinyali veren fonlar", "handler": "technical_analyzer", "method": "handle_general_technical_signals_sql"},
            {"category": "Technical", "question": "teknik satım sinyali veren fonlar", "handler": "technical_analyzer", "method": "handle_general_technical_signals_sql"},
        ])
        
        # 3. ADVANCED METRICS ANALYZER TESTLERİ
        test_questions.extend([
            # Beta
            {"category": "Advanced", "question": "beta katsayısı 1 altında fonlar", "handler": "advanced_metrics_analyzer", "method": "handle_beta_analysis"},
            {"category": "Advanced", "question": "beta değeri 0.5 düşük fonlar", "handler": "advanced_metrics_analyzer", "method": "handle_beta_analysis"},
            {"category": "Advanced", "question": "beta 1.5 üstünde agresif fonlar", "handler": "advanced_metrics_analyzer", "method": "handle_beta_analysis"},
            {"category": "Advanced", "question": "düşük beta yüksek getiri fonlar", "handler": "advanced_metrics_analyzer", "method": "handle_beta_analysis"},
            
            # Alpha
            {"category": "Advanced", "question": "alpha değeri pozitif fonlar", "handler": "advanced_metrics_analyzer", "method": "handle_alpha_analysis"},
            {"category": "Advanced", "question": "jensen alpha en yüksek fonlar", "handler": "advanced_metrics_analyzer", "method": "handle_alpha_analysis"},
            {"category": "Advanced", "question": "negatif alpha olan fonlar", "handler": "advanced_metrics_analyzer", "method": "handle_alpha_analysis"},
            
            # Tracking Error
            {"category": "Advanced", "question": "tracking error düşük index fonlar", "handler": "advanced_metrics_analyzer", "method": "handle_tracking_error_analysis"},
            {"category": "Advanced", "question": "takip hatası %2 altında fonlar", "handler": "advanced_metrics_analyzer", "method": "handle_tracking_error_analysis"},
            
            # Information Ratio
            {"category": "Advanced", "question": "information ratio yüksek aktif fonlar", "handler": "advanced_metrics_analyzer", "method": "handle_information_ratio_analysis"},
            {"category": "Advanced", "question": "bilgi oranı 1 üstünde fonlar", "handler": "advanced_metrics_analyzer", "method": "handle_information_ratio_analysis"},
            
            # Kombine metrikler
            {"category": "Advanced", "question": "beta düşük sharpe yüksek fonlar", "handler": "advanced_metrics_analyzer", "method": "handle_combined_metrics_analysis"},
            {"category": "Advanced", "question": "sharpe 1.5 üstü beta 0.8 altı fonlar", "handler": "advanced_metrics_analyzer", "method": "handle_combined_metrics_analysis"},
        ])
        
        # 4. CURRENCY & INFLATION ANALYZER TESTLERİ
        test_questions.extend([
            # Döviz fonları
            {"category": "Currency", "question": "dolar fonları", "handler": "currency_inflation_analyzer", "method": "analyze_currency_funds"},
            {"category": "Currency", "question": "euro fonları listesi", "handler": "currency_inflation_analyzer", "method": "analyze_currency_funds"},
            {"category": "Currency", "question": "en iyi döviz fonları", "handler": "currency_inflation_analyzer", "method": "analyze_currency_funds"},
            {"category": "Currency", "question": "USD bazlı fonlar", "handler": "currency_inflation_analyzer", "method": "analyze_currency_funds"},
            
            # Enflasyon
            {"category": "Currency", "question": "enflasyon korumalı fonlar", "handler": "currency_inflation_analyzer", "method": "analyze_inflation_funds_mv"},
            {"category": "Currency", "question": "enflasyona karşı en iyi fonlar", "handler": "currency_inflation_analyzer", "method": "analyze_inflation_funds_mv"},
            {"category": "Currency", "question": "enflasyon %50 olursa hangi fonlar", "handler": "currency_inflation_analyzer", "method": "analyze_inflation_scenario"},
            {"category": "Currency", "question": "yüksek enflasyonda güvenli fonlar", "handler": "currency_inflation_analyzer", "method": "analyze_inflation_scenario"},
        ])
        
        # 5. SCENARIO ANALYZER TESTLERİ
        test_questions.extend([
            # Enflasyon senaryoları
            {"category": "Scenario", "question": "enflasyon %30 olursa ne olur", "handler": "scenario_analyzer", "method": "analyze_scenario_question"},
            {"category": "Scenario", "question": "enflasyon %100 olursa fonlar nasıl etkilenir", "handler": "scenario_analyzer", "method": "analyze_scenario_question"},
            
            # Borsa senaryoları
            {"category": "Scenario", "question": "borsa %20 düşerse hangi fonlar", "handler": "scenario_analyzer", "method": "analyze_stock_crash_scenario"},
            {"category": "Scenario", "question": "piyasa çökerse güvenli fonlar", "handler": "scenario_analyzer", "method": "analyze_stock_crash_scenario"},
            
            # Döviz senaryoları
            {"category": "Scenario", "question": "dolar 40 TL olursa", "handler": "scenario_analyzer", "method": "analyze_scenario_question"},
            {"category": "Scenario", "question": "euro 50 TL olursa hangi fonlar kazandırır", "handler": "scenario_analyzer", "method": "analyze_scenario_question"},
            
            # Faiz senaryoları
            {"category": "Scenario", "question": "faiz %50 olursa", "handler": "scenario_analyzer", "method": "analyze_scenario_question"},
            {"category": "Scenario", "question": "TCMB faiz indirirse", "handler": "scenario_analyzer", "method": "analyze_scenario_question"},
            
            # Jeopolitik senaryolar
            {"category": "Scenario", "question": "savaş çıkarsa hangi fonlar güvenli", "handler": "scenario_analyzer", "method": "analyze_scenario_question"},
            {"category": "Scenario", "question": "küresel kriz olursa", "handler": "scenario_analyzer", "method": "analyze_scenario_question"},
        ])
        
        # 6. PERSONAL FINANCE ANALYZER TESTLERİ
        test_questions.extend([
            # Emeklilik
            {"category": "Personal", "question": "emeklilik için en iyi fonlar", "handler": "personal_finance_analyzer", "method": "handle_retirement_planning"},
            {"category": "Personal", "question": "emekliliğe 20 yıl var", "handler": "personal_finance_analyzer", "method": "handle_retirement_planning"},
            {"category": "Personal", "question": "45 yaşındayım emeklilik planı", "handler": "personal_finance_analyzer", "method": "handle_retirement_planning"},
            {"category": "Personal", "question": "30 yaşında emeklilik için ayda ne kadar", "handler": "personal_finance_analyzer", "method": "handle_ai_personalized_planning"},
            
            # Eğitim fonları
            {"category": "Personal", "question": "çocuğum için eğitim fonu", "handler": "personal_finance_analyzer", "method": "analyze_personal_finance_question"},
            {"category": "Personal", "question": "10 yıl sonra üniversite masrafı", "handler": "personal_finance_analyzer", "method": "analyze_personal_finance_question"},
            
            # Ev alma
            {"category": "Personal", "question": "ev almak için birikim", "handler": "personal_finance_analyzer", "method": "analyze_personal_finance_question"},
            {"category": "Personal", "question": "5 yıl sonra ev peşinatı", "handler": "personal_finance_analyzer", "method": "analyze_personal_finance_question"},
            
            # Düğün
            {"category": "Personal", "question": "2 yıl sonra düğün için", "handler": "personal_finance_analyzer", "method": "analyze_personal_finance_question"},
            
            # Acil fon
            {"category": "Personal", "question": "acil durum fonu", "handler": "personal_finance_analyzer", "method": "analyze_personal_finance_question"},
        ])
        
        # 7. MATHEMATICAL CALCULATOR TESTLERİ
        test_questions.extend([
            # Portföy dağılımı
            {"category": "Math", "question": "100000 TL'yi 5 fona dağıt", "handler": "mathematical_calculator", "method": "handle_portfolio_distribution"},
            {"category": "Math", "question": "50000 TL ile portföy oluştur", "handler": "mathematical_calculator", "method": "handle_portfolio_distribution"},
            {"category": "Math", "question": "200000 TL'yi en iyi şekilde dağıt", "handler": "mathematical_calculator", "method": "handle_portfolio_distribution"},
            
            # Aylık yatırım
            {"category": "Math", "question": "ayda 5000 TL yatırırsam 10 yıl sonra", "handler": "mathematical_calculator", "method": "handle_monthly_investment_calculation"},
            {"category": "Math", "question": "aylık 2000 TL ile 20 yılda ne birikir", "handler": "mathematical_calculator", "method": "handle_monthly_investment_calculation"},
            
            # Compound faiz
            {"category": "Math", "question": "yıllık %20 getiri ile 5 yıl", "handler": "mathematical_calculator", "method": "analyze_mathematical_question"},
            {"category": "Math", "question": "100000 TL %15 getiri 10 yıl", "handler": "mathematical_calculator", "method": "analyze_mathematical_question"},
        ])
        
        # 8. PORTFOLIO COMPANY ANALYZER TESTLERİ
        test_questions.extend([
            # Şirket analizleri
            {"category": "Company", "question": "İş Portföy analizi", "handler": "portfolio_company_analyzer", "method": "analyze_company_comprehensive"},
            {"category": "Company", "question": "Ak Portföy fonları", "handler": "portfolio_company_analyzer", "method": "analyze_company_comprehensive"},
            {"category": "Company", "question": "Garanti Portföy performansı", "handler": "portfolio_company_analyzer", "method": "analyze_company_comprehensive"},
            {"category": "Company", "question": "QNB Portföy değerlendirmesi", "handler": "portfolio_company_analyzer", "method": "analyze_company_comprehensive"},
            {"category": "Company", "question": "Ata Portföy nasıl", "handler": "portfolio_company_analyzer", "method": "analyze_company_comprehensive"},
            {"category": "Company", "question": "Fiba Portföy fonları", "handler": "portfolio_company_analyzer", "method": "analyze_company_comprehensive"},
            
            # Karşılaştırmalar
            {"category": "Company", "question": "İş Portföy vs Ak Portföy", "handler": "portfolio_company_analyzer", "method": "compare_companies_unlimited"},
            {"category": "Company", "question": "Garanti Portföy karşı QNB Portföy", "handler": "portfolio_company_analyzer", "method": "compare_companies_unlimited"},
            
            # En başarılı
            {"category": "Company", "question": "en başarılı portföy şirketi", "handler": "portfolio_company_analyzer", "method": "find_best_portfolio_company_unlimited"},
            {"category": "Company", "question": "en iyi portföy yönetim şirketi hangisi", "handler": "portfolio_company_analyzer", "method": "find_best_portfolio_company_unlimited"},
        ])
        
        # 9. TIME BASED ANALYZER TESTLERİ
        test_questions.extend([
            # Günlük
            {"category": "Time", "question": "bugün en çok kazanan fonlar", "handler": "time_based_analyzer", "method": "analyze_today_performance"},
            {"category": "Time", "question": "bugünkü fon performansları", "handler": "time_based_analyzer", "method": "analyze_today_performance"},
            
            # Haftalık
            {"category": "Time", "question": "bu hafta en iyi fonlar", "handler": "time_based_analyzer", "method": "analyze_time_based_question"},
            {"category": "Time", "question": "haftalık en çok kazandıran", "handler": "time_based_analyzer", "method": "analyze_time_based_question"},
            
            # Aylık
            {"category": "Time", "question": "bu ay en çok düşen fonlar", "handler": "time_based_analyzer", "method": "analyze_time_based_question"},
            {"category": "Time", "question": "son 30 günde en iyi performans", "handler": "time_based_analyzer", "method": "analyze_time_based_question"},
            
            # Yıllık
            {"category": "Time", "question": "yılbaşından beri en çok kazandıran", "handler": "time_based_analyzer", "method": "analyze_time_based_question"},
            {"category": "Time", "question": "2024 yılı en başarılı fonlar", "handler": "time_based_analyzer", "method": "analyze_time_based_question"},
        ])
        
        # 10. MACROECONOMIC ANALYZER TESTLERİ
        test_questions.extend([
            # Faiz
            {"category": "Macro", "question": "faiz artışı fonları nasıl etkiler", "handler": "macroeconomic_analyzer", "method": "analyze_interest_rate_impact"},
            {"category": "Macro", "question": "TCMB faiz kararı fon piyasası", "handler": "macroeconomic_analyzer", "method": "analyze_interest_rate_impact"},
            
            # Enflasyon makro
            {"category": "Macro", "question": "enflasyon ve fon getirileri", "handler": "macroeconomic_analyzer", "method": "analyze_macroeconomic_impact"},
            {"category": "Macro", "question": "yüksek enflasyonda fon stratejisi", "handler": "macroeconomic_analyzer", "method": "analyze_macroeconomic_impact"},
            
            # Jeopolitik
            {"category": "Macro", "question": "jeopolitik riskler ve fonlar", "handler": "macroeconomic_analyzer", "method": "analyze_macroeconomic_impact"},
            {"category": "Macro", "question": "küresel belirsizlikte güvenli fonlar", "handler": "macroeconomic_analyzer", "method": "analyze_macroeconomic_impact"},
        ])
        
        # 11. THEMATIC ANALYZER TESTLERİ
        test_questions.extend([
            # Sektör fonları
            {"category": "Thematic", "question": "teknoloji fonları", "handler": "thematic_analyzer", "method": "analyze_thematic_question"},
            {"category": "Thematic", "question": "sağlık sektörü fonları", "handler": "thematic_analyzer", "method": "analyze_thematic_question"},
            {"category": "Thematic", "question": "enerji fonları listesi", "handler": "thematic_analyzer", "method": "analyze_thematic_question"},
            {"category": "Thematic", "question": "altın fonları", "handler": "thematic_analyzer", "method": "analyze_thematic_question"},
            {"category": "Thematic", "question": "gayrimenkul fonları", "handler": "thematic_analyzer", "method": "analyze_thematic_question"},
            
            # Tema bazlı
            {"category": "Thematic", "question": "sürdürülebilir yatırım fonları", "handler": "thematic_analyzer", "method": "analyze_thematic_question"},
            {"category": "Thematic", "question": "temiz enerji fonları", "handler": "thematic_analyzer", "method": "analyze_thematic_question"},
            {"category": "Thematic", "question": "yapay zeka temalı fonlar", "handler": "thematic_analyzer", "method": "analyze_thematic_question"},
        ])
        
        # 12. FUNDAMENTAL ANALYZER TESTLERİ
        test_questions.extend([
            # Fon büyüklüğü
            {"category": "Fundamental", "question": "en büyük fonlar", "handler": "fundamental_analyzer", "method": "handle_largest_funds_questions"},
            {"category": "Fundamental", "question": "1 milyar TL üstü fonlar", "handler": "fundamental_analyzer", "method": "handle_capacity_questions"},
            {"category": "Fundamental", "question": "küçük ölçekli fonlar", "handler": "fundamental_analyzer", "method": "handle_capacity_questions"},
            
            # Yatırımcı sayısı
            {"category": "Fundamental", "question": "en popüler fonlar", "handler": "fundamental_analyzer", "method": "handle_investor_count_questions"},
            {"category": "Fundamental", "question": "yatırımcı sayısı en fazla fonlar", "handler": "fundamental_analyzer", "method": "handle_investor_count_questions"},
            
            # Fon yaşı
            {"category": "Fundamental", "question": "en eski fonlar", "handler": "fundamental_analyzer", "method": "handle_fund_age_questions"},
            {"category": "Fundamental", "question": "yeni kurulan fonlar", "handler": "fundamental_analyzer", "method": "handle_new_funds_questions"},
            {"category": "Fundamental", "question": "son 1 yılda kurulan fonlar", "handler": "fundamental_analyzer", "method": "handle_new_funds_questions"},
            
            # Kategori
            {"category": "Fundamental", "question": "hisse senedi fonları", "handler": "fundamental_analyzer", "method": "handle_fund_category_questions"},
            {"category": "Fundamental", "question": "borçlanma araçları fonları", "handler": "fundamental_analyzer", "method": "handle_fund_category_questions"},
            {"category": "Fundamental", "question": "karma fonlar", "handler": "fundamental_analyzer", "method": "handle_fund_category_questions"},
        ])
        
        # 13. PREDICTIVE SCENARIO ANALYZER TESTLERİ (Yeni)
        test_questions.extend([
            # Tahminler
            {"category": "Predictive", "question": "1 ay sonra piyasa tahmini", "handler": "predictive_scenario_analyzer", "method": "analyze_predictive_scenario"},
            {"category": "Predictive", "question": "6 ay sonra hangi fonlar öne çıkar", "handler": "predictive_scenario_analyzer", "method": "analyze_predictive_scenario"},
            {"category": "Predictive", "question": "2025 sonunda fon piyasası", "handler": "predictive_scenario_analyzer", "method": "analyze_predictive_scenario"},
            {"category": "Predictive", "question": "gelecek ay enflasyon fonları", "handler": "predictive_scenario_analyzer", "method": "analyze_predictive_scenario"},
            {"category": "Predictive", "question": "3 ay sonra dolar fonları", "handler": "predictive_scenario_analyzer", "method": "analyze_predictive_scenario"},
        ])
        
        # 14. MULTİ-HANDLER TESTLERİ (Kapsamlı analizler)
        test_questions.extend([
            {"category": "Multi", "question": "kapsamlı piyasa analizi", "handler": "multi", "method": "multi"},
            {"category": "Multi", "question": "AKB fonunun detaylı ve kapsamlı analizi", "handler": "multi", "method": "multi"},
            {"category": "Multi", "question": "tüm yönleriyle TYH fonu", "handler": "multi", "method": "multi"},
            {"category": "Multi", "question": "derinlemesine YAS fon analizi", "handler": "multi", "method": "multi"},
        ])
        
        # 15. ÖZEL DURUMLAR VE EDGE CASE'LER
        test_questions.extend([
            # Yanlış/Geçersiz sorgular
            {"category": "Edge", "question": "XYZ fonu analiz", "handler": "error", "method": "invalid_fund"},
            {"category": "Edge", "question": "en iyi 0 fon", "handler": "error", "method": "invalid_count"},
            {"category": "Edge", "question": "", "handler": "error", "method": "empty_query"},
            {"category": "Edge", "question": "????", "handler": "error", "method": "invalid_chars"},
            
            # Karmaşık sorgular
            {"category": "Edge", "question": "beta 0.8 altı sharpe 1.2 üstü alpha pozitif fonlar", "handler": "advanced_metrics_analyzer", "method": "handle_combined_metrics_analysis"},
            {"category": "Edge", "question": "hem güvenli hem yüksek getirili fonlar", "handler": "performance_analyzer", "method": "handle_safest_funds_sql_fast"},
            
            # Çok uzun sorgular
            {"category": "Edge", "question": "merhaba ben 35 yaşındayım ve emekliliğim için uzun vadeli yatırım yapmak istiyorum risk almak istemiyorum ama enflasyondan da korunmak istiyorum hangi fonları önerirsiniz", "handler": "personal_finance_analyzer", "method": "handle_retirement_planning"},
        ])
        
        # 16. FON DAĞILIMI VE KATEGORİ SORULARI
        test_questions.extend([
            {"category": "Allocation", "question": "AKB yatırım dağılımı", "handler": "general", "method": "_handle_fund_allocation_question"},
            {"category": "Allocation", "question": "TYH fonu içeriği", "handler": "general", "method": "_handle_fund_allocation_question"},
            {"category": "Allocation", "question": "YAS portföy kompozisyonu", "handler": "general", "method": "_handle_fund_allocation_question"},
            {"category": "Allocation", "question": "IPB varlık dağılımı", "handler": "general", "method": "_handle_fund_allocation_question"},
        ])
        
        # 17. AI TEST SORULARI
        test_questions.extend([
            {"category": "AI", "question": "AI test", "handler": "general", "method": "_handle_ai_test_question"},
            {"category": "AI", "question": "yapay zeka durumu", "handler": "general", "method": "_handle_ai_test_question"},
            {"category": "AI", "question": "AI sistemi çalışıyor mu", "handler": "general", "method": "_handle_ai_test_question"},
        ])
        
        # 18. PİYASA DURUMU SORULARI
        test_questions.extend([
            {"category": "Market", "question": "piyasa durumu nasıl", "handler": "general", "method": "_handle_market_question_dual"},
            {"category": "Market", "question": "genel piyasa değerlendirmesi", "handler": "general", "method": "_handle_market_question_dual"},
            {"category": "Market", "question": "fon piyasası genel durum", "handler": "general", "method": "_handle_market_question_dual"},
        ])
        
        return test_questions
    
    def run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Tek bir test senaryosunu çalıştır"""
        result = {
            "category": test_case["category"],
            "question": test_case["question"],
            "expected_handler": test_case["handler"],
            "expected_method": test_case["method"],
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "response": None,
            "error": None,
            "response_time": None
        }
        
        try:
            start_time = time.time()
            
            # Soruyu sisteme sor
            response = self.qa_system.answer_question(test_case["question"])
            
            end_time = time.time()
            result["response_time"] = round(end_time - start_time, 2)
            
            if response:
                result["response"] = response[:500] + "..." if len(response) > 500 else response
                result["success"] = True
                result["response_length"] = len(response)
                
                # Basit validasyon kontrolleri
                if len(response) < 10:
                    result["warning"] = "Çok kısa yanıt"
                elif "hata" in response.lower() or "error" in response.lower():
                    result["warning"] = "Yanıtta hata mesajı var"
                
            else:
                result["error"] = "Boş yanıt alındı"
                
        except Exception as e:
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()
            
        return result
    
    def run_all_tests(self):
        """Tüm testleri çalıştır"""
        print("\n" + "="*80)
        print("🧪 TEFAS AUTOMATED QA TEST BAŞLIYOR")
        print("="*80)
        
        # Sistemi başlat
        if not self.initialize_system():
            print("❌ Sistem başlatılamadı, test iptal edildi!")
            return
        
        # Test sorularını al
        test_questions = self.get_all_test_questions()
        self.total_tests = len(test_questions)
        
        print(f"\n📊 Toplam {self.total_tests} test senaryosu çalıştırılacak")
        print(f"📁 Sonuçlar kaydedilecek: {self.output_file}\n")
        
        # Kategori istatistikleri
        categories = {}
        for test in test_questions:
            cat = test["category"]
            categories[cat] = categories.get(cat, 0) + 1
        
        print("📋 Kategori Dağılımı:")
        for cat, count in sorted(categories.items()):
            print(f"   • {cat}: {count} test")
        print()
        
        # Progress bar için
        print("🔄 Testler çalıştırılıyor...\n")
        
        # Her testi çalıştır
        for i, test_case in enumerate(test_questions, 1):
            # Progress göster
            progress = (i / self.total_tests) * 100
            print(f"\r[{i}/{self.total_tests}] %{progress:.1f} - {test_case['category']}: {test_case['question'][:50]}...", end="", flush=True)
            
            # Testi çalıştır
            result = self.run_single_test(test_case)
            self.test_results.append(result)
            
            # Başarı durumunu güncelle
            if result["success"]:
                self.passed_tests += 1
            else:
                self.failed_tests += 1
            
            # Rate limiting
            time.sleep(0.5)  # API'yi yormamak için
        
        print("\n\n✅ Tüm testler tamamlandı!")
        
        # Sonuçları kaydet
        self.save_results()
        
        # Özet raporu göster
        self.show_summary()
    
    def save_results(self):
        """Test sonuçlarını dosyalara kaydet"""
        # TXT formatında kaydet
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("TEFAS AUTOMATED QA TEST SONUÇLARI\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Test Tarihi: {self.test_timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Toplam Test: {self.total_tests}\n")
            f.write(f"Başarılı: {self.passed_tests}\n")
            f.write(f"Başarısız: {self.failed_tests}\n")
            f.write(f"Başarı Oranı: %{(self.passed_tests/self.total_tests*100):.1f}\n\n")
            
            # Kategori bazlı sonuçlar
            f.write("KATEGORİ BAZLI SONUÇLAR:\n")
            f.write("-"*40 + "\n")
            
            category_stats = {}
            for result in self.test_results:
                cat = result["category"]
                if cat not in category_stats:
                    category_stats[cat] = {"total": 0, "success": 0, "failed": 0}
                
                category_stats[cat]["total"] += 1
                if result["success"]:
                    category_stats[cat]["success"] += 1
                else:
                    category_stats[cat]["failed"] += 1
            
            for cat, stats in sorted(category_stats.items()):
                success_rate = (stats["success"] / stats["total"]) * 100
                f.write(f"{cat:15} : {stats['success']:3}/{stats['total']:3} (%{success_rate:.1f})\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("DETAYLI TEST SONUÇLARI:\n")
            f.write("="*80 + "\n\n")
            
            # Her test için detaylı sonuç
            for i, result in enumerate(self.test_results, 1):
                f.write(f"TEST #{i}\n")
                f.write("-"*40 + "\n")
                f.write(f"Kategori: {result['category']}\n")
                f.write(f"Soru: {result['question']}\n")
                f.write(f"Beklenen Handler: {result['expected_handler']}.{result['expected_method']}\n")
                f.write(f"Durum: {'✅ BAŞARILI' if result['success'] else '❌ BAŞARISIZ'}\n")
                f.write(f"Yanıt Süresi: {result['response_time']}s\n")
                
                if result.get('warning'):
                    f.write(f"⚠️ Uyarı: {result['warning']}\n")
                
                if result['error']:
                    f.write(f"Hata: {result['error']}\n")
                
                if result['response']:
                    f.write(f"Yanıt Önizleme:\n{result['response']}\n")
                
                f.write("\n")
            
            # Başarısız testler özeti
            failed_tests = [r for r in self.test_results if not r["success"]]
            if failed_tests:
                f.write("\n" + "="*80 + "\n")
                f.write("BAŞARISIZ TESTLER ÖZETİ:\n")
                f.write("="*80 + "\n\n")
                
                for result in failed_tests:
                    f.write(f"❌ {result['category']} - {result['question']}\n")
                    f.write(f"   Hata: {result['error']}\n\n")
        
        # JSON formatında da kaydet
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_info": {
                    "timestamp": self.test_timestamp.isoformat(),
                    "total_tests": self.total_tests,
                    "passed": self.passed_tests,
                    "failed": self.failed_tests,
                    "success_rate": round(self.passed_tests/self.total_tests*100, 2)
                },
                "category_stats": category_stats,
                "results": self.test_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Sonuçlar kaydedildi:")
        print(f"   • TXT: {self.output_file}")
        print(f"   • JSON: {self.json_file}")
    
    def show_summary(self):
        """Test özeti göster"""
        print("\n" + "="*60)
        print("📊 TEST ÖZETİ")
        print("="*60)
        
        print(f"\n🎯 Genel Sonuçlar:")
        print(f"   • Toplam Test: {self.total_tests}")
        print(f"   • ✅ Başarılı: {self.passed_tests}")
        print(f"   • ❌ Başarısız: {self.failed_tests}")
        print(f"   • 📈 Başarı Oranı: %{(self.passed_tests/self.total_tests*100):.1f}")
        
        # En yavaş testler
        slowest = sorted(self.test_results, key=lambda x: x.get('response_time', 0), reverse=True)[:5]
        print(f"\n⏱️ En Yavaş 5 Test:")
        for result in slowest:
            if result.get('response_time'):
                print(f"   • {result['response_time']}s - {result['question'][:50]}...")
        
        # Hata istatistikleri
        error_types = {}
        for result in self.test_results:
            if result['error']:
                error_type = result['error'].split(':')[0]
                error_types[error_type] = error_types.get(error_type, 0) + 1
        
        if error_types:
            print(f"\n❌ Hata Türleri:")
            for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {error_type}: {count}")
        
        print("\n" + "="*60)
        print("✅ TEST TAMAMLANDI!")
        print("="*60)


def main():
    """Ana fonksiyon"""
    tester = TEFASAutomatedQATester()
    
    # Argüman kontrolü
    if len(sys.argv) > 1:
        if sys.argv[1] == "--quick":
            # Hızlı test modu - sadece ilk 20 test
            print("⚡ Hızlı test modu - İlk 20 soru")
            tester.test_questions = tester.get_all_test_questions()[:20]
        elif sys.argv[1] == "--category":
            # Belirli kategori testi
            if len(sys.argv) > 2:
                category = sys.argv[2]
                print(f"📁 Sadece {category} kategorisi test ediliyor")
                all_tests = tester.get_all_test_questions()
                tester.test_questions = [t for t in all_tests if t["category"] == category]
            else:
                print("❌ Kategori belirtmelisiniz: python qa_test.py --category Performance")
                return
    
    # Testleri çalıştır
    tester.run_all_tests()


if __name__ == "__main__":
    main()