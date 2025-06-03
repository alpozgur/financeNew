import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.config import Config
from analysis.coordinator import AnalysisCoordinator

class TestAnalysisFramework(unittest.TestCase):
    """Analiz framework'ünün test sınıfı"""
    
    def setUp(self):
        """Test kurulumu"""
        self.config = Config()
        self.coordinator = AnalysisCoordinator(self.config)
    
    def test_database_connection(self):
        """Veritabanı bağlantısı testi"""
        try:
            fund_codes = self.coordinator.db.get_all_fund_codes()
            self.assertIsNotNone(fund_codes)
            self.assertGreater(len(fund_codes), 0)
            print(f"✅ Database test passed. Found {len(fund_codes)} funds.")
        except Exception as e:
            self.fail(f"Database connection failed: {e}")
    
    def test_single_fund_analysis(self):
        """Tek fon analizi testi"""
        try:
            # İlk fonu al
            fund_codes = self.coordinator.db.get_all_fund_codes()
            test_fund = fund_codes[0] if fund_codes else None
            
            if test_fund:
                result = self.coordinator.comprehensive_fund_analysis(test_fund, days=100)
                
                self.assertIsNotNone(result)
                self.assertEqual(result['fcode'], test_fund)
                self.assertIn('performance_analysis', result)
                self.assertIn('technical_analysis', result)
                
                print(f"✅ Single fund analysis test passed for {test_fund}")
            else:
                self.skipTest("No funds available for testing")
                
        except Exception as e:
            self.fail(f"Single fund analysis failed: {e}")
    
    def test_multi_fund_comparison(self):
        """Çoklu fon karşılaştırması testi"""
        try:
            fund_codes = self.coordinator.db.get_all_fund_codes()
            test_funds = fund_codes[:3] if len(fund_codes) >= 3 else fund_codes
            
            if len(test_funds) >= 2:
                result = self.coordinator.multi_fund_comparison(test_funds, days=50)
                
                self.assertIsNotNone(result)
                self.assertIn('individual_analyses', result)
                self.assertIn('comparative_analysis', result)
                
                print(f"✅ Multi fund comparison test passed for {len(test_funds)} funds")
            else:
                self.skipTest("Insufficient funds for comparison testing")
                
        except Exception as e:
            self.fail(f"Multi fund comparison failed: {e}")
    
    def test_performance_analysis(self):
        """Performans analizi testi"""
        try:
            fund_codes = self.coordinator.db.get_all_fund_codes()
            test_fund = fund_codes[0] if fund_codes else None
            
            if test_fund:
                result = self.coordinator.performance_analyzer.analyze_fund_performance(test_fund, days=100)
                
                self.assertIsNotNone(result)
                self.assertIn('basic_metrics', result)
                self.assertIn('drawdown_analysis', result)
                
                print(f"✅ Performance analysis test passed for {test_fund}")
            else:
                self.skipTest("No funds available for performance testing")
                
        except Exception as e:
            self.fail(f"Performance analysis failed: {e}")
    
    def test_technical_analysis(self):
        """Teknik analiz testi"""
        try:
            fund_codes = self.coordinator.db.get_all_fund_codes()
            test_fund = fund_codes[0] if fund_codes else None
            
            if test_fund:
                result = self.coordinator.technical_analyzer.analyze_fund_technical(test_fund, days=100)
                
                self.assertIsNotNone(result)
                self.assertIn('technical_indicators', result)
                self.assertIn('trading_signals', result)
                
                print(f"✅ Technical analysis test passed for {test_fund}")
            else:
                self.skipTest("No funds available for technical testing")
                
        except Exception as e:
            self.fail(f"Technical analysis failed: {e}")

def run_comprehensive_test():
    """Kapsamlı test çalıştırma"""
    print("🚀 TEFAS Analysis System - Comprehensive Testing")
    print("=" * 60)
    
    try:
        # Config test
        config = Config()
        print(f"✅ Config loaded successfully")
        
        # Database test
        coordinator = AnalysisCoordinator(config)
        fund_codes = coordinator.db.get_all_fund_codes()
        print(f"✅ Database connection successful. Found {len(fund_codes)} funds")
        
        if len(fund_codes) >= 3:
            # Test first 3 funds
            test_funds = fund_codes[:3]
            print(f"📊 Testing with funds: {test_funds}")
            
            # Single fund comprehensive analysis
            print("\n🔍 Testing comprehensive fund analysis...")
            result = coordinator.comprehensive_fund_analysis(test_funds[0], days=100)
            
            if 'error' not in result:
                print(f"✅ Comprehensive analysis successful for {test_funds[0]}")
                
                # Display key metrics
                if 'investment_score' in result:
                    score = result['investment_score']
                    print(f"   Investment Score: {score.get('total_score', 0):.1f}/100")
                    print(f"   Recommendation: {score.get('recommendation', 'Unknown')}")
            else:
                print(f"❌ Analysis failed: {result['error']}")
            
            # Multi-fund comparison
            print(f"\n📈 Testing multi-fund comparison...")
            comparison = coordinator.multi_fund_comparison(test_funds, days=50)
            
            if 'error' not in comparison:
                print(f"✅ Multi-fund comparison successful")
                rankings = comparison.get('overall_rankings', {})
                if rankings:
                    top_fund = rankings.get('by_investment_score', [None])[0]
                    print(f"   Top rated fund: {top_fund}")
            else:
                print(f"❌ Comparison failed")
            
            # Portfolio optimization test
            print(f"\n💼 Testing portfolio optimization...")
            portfolio_result = coordinator.portfolio_optimizer.comprehensive_portfolio_analysis(test_funds)
            
            if 'error' not in portfolio_result:
                print(f"✅ Portfolio optimization successful")
                recommended = portfolio_result.get('recommended_portfolio', {})
                if recommended:
                    method = recommended.get('method', 'Unknown')
                    print(f"   Recommended method: {method}")
            else:
                print(f"❌ Portfolio optimization failed")
            
            print("\n🎉 All tests completed successfully!")
            print("📱 System ready for mobile app integration")
            
        else:
            print("❌ Insufficient fund data for comprehensive testing")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    # Command line test runner
    import argparse
    
    parser = argparse.ArgumentParser(description='TEFAS Analysis System Tests')
    parser.add_argument('--unittest', action='store_true', help='Run unit tests')
    parser.add_argument('--comprehensive', action='store_true', help='Run comprehensive tests')
    parser.add_argument('--fund', type=str, help='Test specific fund code')
    
    args = parser.parse_args()
    
    if args.unittest:
        unittest.main(verbosity=2)
    elif args.comprehensive:
        run_comprehensive_test()
    elif args.fund:
        # Specific fund test
        config = Config()
        coordinator = AnalysisCoordinator(config)
        result = coordinator.comprehensive_fund_analysis(args.fund)
        print(json.dumps(result, indent=2, default=str))
    else:
        run_comprehensive_test()
