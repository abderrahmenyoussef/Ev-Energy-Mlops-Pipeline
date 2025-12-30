"""
Streamlit App Tests
Tests for the Streamlit frontend application
"""
import os
import sys
import ast
import importlib.util

# Add streamlit_app to path
STREAMLIT_APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "streamlit_app"))
sys.path.insert(0, STREAMLIT_APP_PATH)


class TestStreamlitSyntax:
    """Test that all Streamlit app files have valid Python syntax"""
    
    def get_python_files(self):
        """Get all Python files in streamlit_app directory"""
        python_files = []
        for root, dirs, files in os.walk(STREAMLIT_APP_PATH):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files
    
    def test_syntax_validity(self):
        """Check all Python files have valid syntax"""
        errors = []
        for filepath in self.get_python_files():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    source = f.read()
                ast.parse(source)
            except SyntaxError as e:
                errors.append(f"{filepath}: {e}")
        
        assert len(errors) == 0, f"Syntax errors found:\n" + "\n".join(errors)
    
    def test_no_print_statements_in_production(self):
        """Check for debug print statements (warning only)"""
        warnings = []
        for filepath in self.get_python_files():
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for i, line in enumerate(lines, 1):
                # Skip commented lines
                stripped = line.strip()
                if stripped.startswith('#'):
                    continue
                # Check for bare print statements (not st.write or logging)
                if 'print(' in line and 'st.' not in line:
                    warnings.append(f"{filepath}:{i}: {stripped[:50]}")
        
        # This is a soft check - just print warnings
        if warnings:
            print(f"\n⚠️ Found {len(warnings)} print statements (consider using st.write or logging):")
            for w in warnings[:5]:  # Show max 5
                print(f"  - {w}")


class TestStreamlitImports:
    """Test that all imports work correctly"""
    
    def test_config_imports(self):
        """Test config module can be imported"""
        spec = importlib.util.spec_from_file_location(
            "config", 
            os.path.join(STREAMLIT_APP_PATH, "config.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check required config variables exist
        assert hasattr(module, 'APP_TITLE'), "APP_TITLE not defined in config"
        assert hasattr(module, 'APP_ICON'), "APP_ICON not defined in config"
    
    def test_utils_imports(self):
        """Test utils modules exist and are importable"""
        utils_path = os.path.join(STREAMLIT_APP_PATH, "utils")
        required_modules = ['api_client.py', 'auth.py', 'database.py']
        
        for module_name in required_modules:
            module_path = os.path.join(utils_path, module_name)
            assert os.path.exists(module_path), f"Missing required module: {module_name}"
            
            # Check syntax is valid
            with open(module_path, 'r') as f:
                source = f.read()
            ast.parse(source)  # Will raise SyntaxError if invalid


class TestStreamlitPages:
    """Test that all Streamlit pages are valid"""
    
    def test_pages_exist(self):
        """Check that required pages exist"""
        pages_path = os.path.join(STREAMLIT_APP_PATH, "pages")
        assert os.path.isdir(pages_path), "pages directory not found"
        
        pages = [f for f in os.listdir(pages_path) if f.endswith('.py')]
        assert len(pages) >= 1, "No pages found in pages directory"
    
    def test_pages_syntax(self):
        """Check all pages have valid syntax"""
        pages_path = os.path.join(STREAMLIT_APP_PATH, "pages")
        errors = []
        
        for page_file in os.listdir(pages_path):
            if page_file.endswith('.py'):
                filepath = os.path.join(pages_path, page_file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        source = f.read()
                    ast.parse(source)
                except SyntaxError as e:
                    errors.append(f"{page_file}: {e}")
        
        assert len(errors) == 0, f"Page syntax errors:\n" + "\n".join(errors)


class TestStreamlitRequirements:
    """Test requirements.txt validity"""
    
    def test_requirements_file_exists(self):
        """Check requirements.txt exists"""
        req_path = os.path.join(STREAMLIT_APP_PATH, "requirements.txt")
        assert os.path.exists(req_path), "requirements.txt not found in streamlit_app"
    
    def test_requirements_format(self):
        """Check requirements.txt has valid format"""
        req_path = os.path.join(STREAMLIT_APP_PATH, "requirements.txt")
        errors = []
        
        with open(req_path, 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Basic format check: should have package name
            if not any(c.isalpha() for c in line):
                errors.append(f"Line {i}: Invalid format '{line}'")
        
        assert len(errors) == 0, f"Requirements format errors:\n" + "\n".join(errors)
    
    def test_streamlit_in_requirements(self):
        """Check streamlit is in requirements"""
        req_path = os.path.join(STREAMLIT_APP_PATH, "requirements.txt")
        
        with open(req_path, 'r') as f:
            content = f.read().lower()
        
        assert 'streamlit' in content, "streamlit not found in requirements.txt"
