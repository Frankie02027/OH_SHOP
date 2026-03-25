#!/usr/bin/env python3
"""
LEVEL 6: MULTI-FILE REFACTOR WITH DEPENDENCIES
==============================================
Difficulty: Hard
Time Limit: 15 minutes

TASK:
There's a broken multi-file project in the 'level6_project/' directory.
The project has:
- Circular import issues
- Missing functions
- Broken dependencies
- A main.py that must run successfully

You must:
1. Fix the circular imports
2. Implement missing functions
3. Make main.py run and print "PROJECT WORKING"

FILES:
- level6_project/main.py - Entry point (don't modify logic, only imports if needed)
- level6_project/utils.py - Utility functions (has bug)
- level6_project/calculator.py - Calculator class (missing methods)
- level6_project/validator.py - Input validation (circular import issue)
"""
import os
import sys
import shutil

PROJECT_FILES = {
    'main.py': '''
# Main entry point - fix imports and dependencies to make this work
from calculator import Calculator
from validator import validate_input
from utils import format_result

def main():
    calc = Calculator()
    
    # Test 1: Basic operations
    a, b = 10, 5
    if not validate_input(a, b):
        print("Validation failed")
        return False
    
    result = calc.add(a, b)
    print(format_result("add", a, b, result))
    
    result = calc.multiply(a, b)
    print(format_result("multiply", a, b, result))
    
    result = calc.power(2, 10)
    print(format_result("power", 2, 10, result))
    
    # Test 2: Chain operations
    chain_result = calc.chain_operations([1, 2, 3, 4, 5])
    if chain_result != 15:
        print(f"Chain failed: {chain_result}")
        return False
    
    print("PROJECT WORKING")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
''',
    
    'calculator.py': '''
# Calculator class - implement missing methods
from utils import log_operation  # This import might cause issues

class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        log_operation("add", a, b, result)
        self.history.append(("add", a, b, result))
        return result
    
    def multiply(self, a, b):
        # TODO: Implement this method
        # Should log operation and add to history like add()
        pass
    
    def power(self, base, exp):
        # TODO: Implement this method
        # Should log operation and add to history
        pass
    
    def chain_operations(self, numbers):
        # TODO: Sum all numbers using self.add()
        # Returns the total sum
        pass
''',
    
    'utils.py': '''
# Utility functions - has a bug and circular import issue
from validator import is_valid_number  # CIRCULAR IMPORT PROBLEM

_log = []

def log_operation(op, a, b, result):
    """Log an operation."""
    # BUG: Missing validation
    _log.append(f"{op}({a}, {b}) = {result}")

def format_result(op, a, b, result):
    """Format a result for display."""
    return f"{op}({a}, {b}) = {result}"  # BUG: result is not used correctly

def get_log():
    return _log.copy()
''',
    
    'validator.py': '''
# Validator module - circular import with utils
from utils import get_log  # CIRCULAR IMPORT PROBLEM

def is_valid_number(n):
    """Check if n is a valid number for calculations."""
    return isinstance(n, (int, float)) and not isinstance(n, bool)

def validate_input(a, b):
    """Validate two inputs for calculation."""
    return is_valid_number(a) and is_valid_number(b)
'''
}

def setup():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.join(script_dir, "level6_project")
    
    # Check if already fixed (main.py runs)
    main_file = os.path.join(project_dir, "main.py")
    if os.path.exists(main_file):
        import subprocess
        result = subprocess.run([sys.executable, main_file], capture_output=True, text=True, timeout=5, cwd=project_dir)
        if "PROJECT WORKING" in result.stdout:
            return True  # Already fixed
    
    # Create/reset project
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
    os.makedirs(project_dir)
    
    for filename, content in PROJECT_FILES.items():
        filepath = os.path.join(project_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
    
    # Create __init__.py
    with open(os.path.join(project_dir, "__init__.py"), 'w') as f:
        f.write("")
    
    print(f"Created project in: {project_dir}")
    print("FIX the circular imports, implement missing methods, and fix bugs.")
    print("Run this script again to verify.")
    return False

def verify():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.join(script_dir, "level6_project")
    main_file = os.path.join(project_dir, "main.py")
    
    if not os.path.exists(main_file):
        setup()
        return False
    
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, main_file], 
            capture_output=True, 
            text=True, 
            timeout=10,
            cwd=project_dir
        )
    except subprocess.TimeoutExpired:
        print("FAIL: Timeout - possible infinite loop or deadlock")
        return False
    
    if result.returncode != 0:
        print(f"FAIL: Project crashed")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False
    
    if "PROJECT WORKING" not in result.stdout:
        print(f"FAIL: Project did not complete successfully")
        print(f"STDOUT: {result.stdout}")
        return False
    
    print("LEVEL 6 PASSED")
    return True

if __name__ == "__main__":
    if not setup():
        sys.exit(1)
    sys.exit(0 if verify() else 1)
