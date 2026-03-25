#!/usr/bin/env python3
"""
LEVEL 2: FIX SYNTAX ERROR
=========================
Difficulty: Easy
Time Limit: 1 minute

TASK:
The file 'broken_syntax.py' has a syntax error that prevents it from running.
Fix the syntax error so the file runs and prints "Syntax Fixed!"

SUCCESS CRITERIA:
- broken_syntax.py must be valid Python
- Running it must print "Syntax Fixed!"
"""
import os
import sys
import subprocess

BROKEN_CODE = '''
def greet(name)
    message = f"Hello, {name}!"
    return message

def main():
    result = greet("World")
    print("Syntax Fixed!")

if __name__ == "__main__":
    main()
'''

def setup():
    """Create the broken file if it doesn't exist."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(script_dir, "broken_syntax.py")
    
    if not os.path.exists(target):
        with open(target, 'w') as f:
            f.write(BROKEN_CODE)
        print(f"Created broken file: {target}")
        print("FIX THE SYNTAX ERROR, then run this script again to verify.")
        return False
    return True

def verify():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(script_dir, "broken_syntax.py")
    
    if not os.path.exists(target):
        setup()
        return False
    
    # Try to compile it
    try:
        with open(target, 'r') as f:
            code = f.read()
        compile(code, target, 'exec')
    except SyntaxError as e:
        print(f"FAIL: Syntax error still exists: {e}")
        return False
    
    # Try to run it
    result = subprocess.run([sys.executable, target], capture_output=True, text=True)
    
    if "Syntax Fixed!" not in result.stdout:
        print(f"FAIL: Expected output 'Syntax Fixed!', got: {result.stdout}")
        return False
    
    print("LEVEL 2 PASSED")
    return True

if __name__ == "__main__":
    if not setup():
        sys.exit(1)
    sys.exit(0 if verify() else 1)
