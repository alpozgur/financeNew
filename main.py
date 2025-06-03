import logging
import sys
from pathlib import Path

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/tefas_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Log dizinini oluştur
Path('logs').mkdir(exist_ok=True)

# main.py - İngilizce mesajlarla
def main():
    """Main startup function"""
    logger = logging.getLogger(__name__)
    logger.info("TEFAS Analysis System starting...")
    
    try:
        # Konfigürasyon yükle
        from config.config import Config
        config = Config()
        
        # Veritabanı bağlantısını test et
        from database.connection import DatabaseManager
        db = DatabaseManager(config)
        
        # Basit test sorgusu
        result = db.execute_query("SELECT COUNT(*) as total_records FROM tefasfunds")
        logger.info(f"Database contains {result.iloc[0]['total_records']} fund records")
        
        # Fon kodlarını listele
        fund_codes = db.get_all_fund_codes()
        logger.info(f"Found {len(fund_codes)} unique fund codes")
        
        print("✅ TEFAS Analysis System started successfully!")
        print(f"📊 Database connection: OK")
        print(f"📈 Total funds: {len(fund_codes)}")
        
        return True
        
    except Exception as e:
        logger.error(f"System startup error: {e}")
        print(f"❌ Error: {e}")
        return False
if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)