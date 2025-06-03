# Hızlı düzeltme dosyası oluştur
"""AIAnalyzer eksik özellik düzeltmesi"""

def fix_ai_analyzer():
    """AIAnalyzer sınıfına eksik özellikleri ekle"""
    
    # analysis/ai_analysis.py dosyasını oku
    try:
        with open('analysis/ai_analysis.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ ai_analysis.py dosyası bulunamadı")
        return False
    
    # Eksik özellikleri kontrol et ve ekle
    fixes_needed = []
    
    # ollama_available özelliği kontrolü
    if 'self.ollama_available' not in content:
        fixes_needed.append('ollama_available')
    
    # openai_available özelliği kontrolü  
    if 'self.openai_available' not in content:
        fixes_needed.append('openai_available')
    
    if not fixes_needed:
        print("✅ AIAnalyzer zaten güncel")
        return True
    
    print(f"🔧 Düzeltilecek özellikler: {fixes_needed}")
    
    # __init__ metodunu bul ve düzelt
    import re
    
    # __init__ metodunun sonunu bul
    init_pattern = r'(def __init__\(self[^:]*:\s*.*?)(def [^_]|\nclass|\n\n\n|\Z)'
    
    def fix_init_method(match):
        init_content = match.group(1)
        next_part = match.group(2)
        
        # Son satırdan önce özellikleri ekle
        lines = init_content.strip().split('\n')
        
        # Son satırın girintisini al
        last_line = lines[-1] if lines else ''
        indent = len(last_line) - len(last_line.lstrip()) if last_line.strip() else 8
        indent_str = ' ' * indent
        
        # Eksik özellikleri ekle
        additions = []
        
        if 'ollama_available' in fixes_needed:
            additions.extend([
                f"{indent_str}# Ollama durumu",
                f"{indent_str}self.ollama_available = self._check_ollama_connection()"
            ])
        
        if 'openai_available' in fixes_needed:
            additions.extend([
                f"{indent_str}# OpenAI durumu", 
                f"{indent_str}if not hasattr(self, 'openai_available'):",
                f"{indent_str}    self.openai_available = bool(config.ai.openai_api_key)"
            ])
        
        # Düzeltilmiş init metodu
        fixed_init = '\n'.join(lines + additions) + '\n\n'
        
        return fixed_init + next_part
    
    # Düzeltmeyi uygula
    content = re.sub(init_pattern, fix_init_method, content, flags=re.DOTALL)
    
    # _check_ollama_connection metodunu ekle (eğer yoksa)
    if '_check_ollama_connection' not in content:
        method_to_add = '''
    def _check_ollama_connection(self) -> bool:
        """Ollama bağlantısını kontrol et"""
        try:
            import requests
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Ollama connection failed: {e}")
            return False
'''
        # Sınıfın sonuna ekle
        content = content.replace('\nclass ', method_to_add + '\nclass ')
        if '\nclass ' not in content:
            content += method_to_add
    
    # Dosyayı kaydet
    try:
        with open('analysis/ai_analysis.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ AIAnalyzer düzeltmesi tamamlandı")
        return True
    except Exception as e:
        print(f"❌ Dosya yazma hatası: {e}")
        return False

if __name__ == "__main__":
    success = fix_ai_analyzer()
    if success:
        print("🚀 Düzeltme tamamlandı - Sistemi tekrar test edin!")
    else:
        print("❌ Düzeltme başarısız")
