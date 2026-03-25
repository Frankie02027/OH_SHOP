#!/usr/bin/env python3
"""
LEVEL 1: FILE CREATION
======================
Difficulty: Trivial
Time Limit: 30 seconds

TASK:
Create a file called 'hello.txt' in the same directory as this script.
The file must contain exactly: "Hello, World!"

SUCCESS CRITERIA:
- File exists
- Content matches exactly
"""
import os
import sys

def verify():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(script_dir, "hello.txt")
    
    if not os.path.exists(target):
        print(f"FAIL: File not found: {target}")
        return False
    
    with open(target, 'r') as f:
        content = f.read().strip()
    
    if content != "Hello, World!":
        print(f"FAIL: Content mismatch. Got: '{content}'")
        return False
    
    print("LEVEL 1 PASSED")
    return True

if __name__ == "__main__":
    sys.exit(0 if verify() else 1)
