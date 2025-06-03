"""
TEFAS Analysis System kurulum scripti
"""
from pathlib import Path
import subprocess
import sys

def install_requirements():
    """Gerekli paketleri yükle"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if requirements_file.exists():
        print("📦 Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
        print("✅ Packages installed successfully")
    else:
        print("❌ requirements.txt file not found")

def create_directories():
    """Gerekli dizinleri oluştur"""
    directories = ['logs', 'reports', 'data', 'config']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")

def create_env_template():
    """Environment template dosyası oluştur"""
    env_template = """# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tefas_db
DB_USER=postgres
DB_PASSWORD=your_password

# AI Configuration
OPENAI_API_KEY=your_openai_api_key
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Analysis Configuration
RISK_FREE_RATE=0.15
"""
    
    env_file = Path(".env.example")
    with open(env_file, 'w') as f:
        f.write(env_template)
    
    print("📝 Created .env.example file")
    print("   Please copy this to .env and update with your settings")

def main():
    """Ana kurulum fonksiyonu"""
    print("🚀 TEFAS Analysis System Setup")
    print("=" * 40)
    
    try:
        create_directories()
        install_requirements()
        create_env_template()
        
        print("\n✅ Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Copy .env.example to .env and configure your settings")
        print("2. Set up your PostgreSQL database")
        print("3. Configure OpenAI API key (optional)")
        print("4. Set up Ollama (optional)")
        print("5. Run: python main.py")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()