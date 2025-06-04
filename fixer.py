# test.py
from config.config import Config
from analysis.coordinator import AnalysisCoordinator

config = Config()
coordinator = AnalysisCoordinator(config)

# AI Provider test
if hasattr(coordinator, 'ai_provider'):
    print("✅ AI Provider yüklendi")
    status = coordinator.ai_provider.get_status()
    print(f"Provider: {status['provider_type']}")
    print(f"Hazır mı: {status['is_available']}")
    
    # Test query
    response = coordinator.ai_provider.query("TEFAS nedir? (2 cümle)")
    print(f"Test yanıtı: {response[:100]}...")
else:
    print("❌ AI Provider bulunamadı!")