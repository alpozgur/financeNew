import os
import json
from pathlib import Path
from datetime import datetime

class ProjectAnalyzer:
    def __init__(self, project_path="."):
        self.project_path = Path(project_path)
        self.ignore_patterns = {
            '__pycache__', '.git', '.venv', 'venv', 'env', 
            'node_modules', '.idea', '.vscode', '*.pyc', 
            '*.pyo', '.DS_Store', '*.egg-info', 'dist', 
            'build', '.pytest_cache', '.mypy_cache'
        }
        self.text_extensions = {
            '.py', '.txt', '.md', '.json', '.yml', '.yaml',
            '.ini', '.cfg', '.conf', '.sh', '.bat', '.env',
            '.html', '.css', '.js', '.jsx', '.ts', '.tsx',
            '.sql', '.xml', '.toml', '.rst', '.csv'
        }
        self.output = []
        
    def should_ignore(self, path):
        """Check if path should be ignored"""
        path_str = str(path)
        for pattern in self.ignore_patterns:
            if pattern.startswith('*'):
                if path_str.endswith(pattern[1:]):
                    return True
            elif pattern in path_str:
                return True
        return False
    
    def get_file_info(self, file_path):
        """Get file size and line count"""
        try:
            size = os.path.getsize(file_path)
            lines = 0
            if file_path.suffix in self.text_extensions:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = sum(1 for _ in f)
                except:
                    lines = "Error reading"
            return f"{size:,} bytes, {lines} lines"
        except:
            return "Error"
    
    def analyze_directory(self, path=None, level=0):
        """Recursively analyze directory structure"""
        if path is None:
            path = self.project_path
            
        items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
        
        for item in items:
            if self.should_ignore(item):
                continue
                
            indent = "│   " * level
            if item.is_file():
                file_info = self.get_file_info(item)
                self.output.append(f"{indent}├── {item.name} ({file_info})")
                
                # Include file content for important files
                if item.name in ['requirements.txt', 'package.json', 'setup.py', 
                               'pyproject.toml', 'docker-compose.yml', 'Dockerfile']:
                    self.output.append(f"{indent}│   [Content Preview]:")
                    try:
                        with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()[:500]  # First 500 chars
                            for line in content.split('\n')[:10]:  # First 10 lines
                                if line.strip():
                                    self.output.append(f"{indent}│   > {line.strip()}")
                    except:
                        self.output.append(f"{indent}│   > Error reading file")
                    self.output.append("")
                    
            else:  # Directory
                self.output.append(f"{indent}├── {item.name}/")
                self.analyze_directory(item, level + 1)
    
    def extract_python_structure(self):
        """Extract classes and functions from Python files"""
        self.output.append("\n" + "="*60)
        self.output.append("PYTHON CODE STRUCTURE")
        self.output.append("="*60 + "\n")
        
        for py_file in self.project_path.rglob("*.py"):
            if self.should_ignore(py_file):
                continue
                
            relative_path = py_file.relative_to(self.project_path)
            self.output.append(f"\n📄 {relative_path}")
            self.output.append("-" * 40)
            
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                imports = []
                classes = []
                functions = []
                
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    
                    # Imports
                    if stripped.startswith(('import ', 'from ')):
                        imports.append(stripped)
                    
                    # Classes
                    elif stripped.startswith('class '):
                        class_name = stripped.split('(')[0].replace('class ', '').strip(':')
                        classes.append(f"  Class: {class_name}")
                        
                        # Get class methods
                        j = i + 1
                        while j < len(lines):
                            method_line = lines[j].strip()
                            if method_line.startswith('def ') and lines[j].startswith('    '):
                                method_name = method_line.split('(')[0].replace('def ', '')
                                classes.append(f"    └─ {method_name}()")
                            elif not lines[j].startswith((' ', '\t')) and method_line:
                                break
                            j += 1
                    
                    # Functions (top-level)
                    elif stripped.startswith('def ') and not line.startswith((' ', '\t')):
                        func_name = stripped.split('(')[0].replace('def ', '')
                        functions.append(f"  Function: {func_name}()")
                
                if imports:
                    self.output.append("\n🔧 Imports:")
                    for imp in imports[:10]:  # First 10 imports
                        self.output.append(f"  {imp}")
                    if len(imports) > 10:
                        self.output.append(f"  ... and {len(imports) - 10} more imports")
                
                if classes:
                    self.output.append("\n🏗️ Classes and Methods:")
                    for cls in classes:
                        self.output.append(cls)
                
                if functions:
                    self.output.append("\n⚡ Functions:")
                    for func in functions:
                        self.output.append(func)
                        
            except Exception as e:
                self.output.append(f"  Error analyzing file: {e}")
    
    def analyze_project(self):
        """Main analysis function"""
        self.output.append(f"PROJECT STRUCTURE ANALYSIS")
        self.output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.output.append(f"Project Path: {self.project_path.absolute()}")
        self.output.append("="*60)
        self.output.append("\nDIRECTORY STRUCTURE:")
        self.output.append("="*60)
        self.output.append("")
        
        # Directory tree
        self.output.append(f"{self.project_path.name}/")
        self.analyze_directory()
        
        # Python structure
        self.extract_python_structure()
        
        # Project statistics
        self.output.append("\n" + "="*60)
        self.output.append("PROJECT STATISTICS")
        self.output.append("="*60)
        
        total_files = 0
        total_py_files = 0
        total_lines = 0
        
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file() and not self.should_ignore(file_path):
                total_files += 1
                if file_path.suffix == '.py':
                    total_py_files += 1
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            total_lines += sum(1 for _ in f)
                    except:
                        pass
        
        self.output.append(f"\nTotal Files: {total_files}")
        self.output.append(f"Python Files: {total_py_files}")
        self.output.append(f"Total Python Lines: {total_lines:,}")
        
        # Save to file
        output_file = "project_structure.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.output))
        
        print(f"✅ Analysis complete! Output saved to: {output_file}")
        print(f"📊 Found {total_files} files ({total_py_files} Python files)")
        
        return output_file

if __name__ == "__main__":
    # Kullanım: Script'i proje dizininde çalıştırın
    # veya path belirtin:
    # analyzer = ProjectAnalyzer("/path/to/your/project")
    
    analyzer = ProjectAnalyzer(".")  # Mevcut dizin
    analyzer.analyze_project()
    
    print("\n📋 Çıktı dosyası oluşturuldu: project_structure.txt")
    print("Bu dosyayı paylaşarak projenizin yapısını inceleyebilirim!")