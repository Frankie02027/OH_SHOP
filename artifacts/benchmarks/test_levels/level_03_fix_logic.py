#!/usr/bin/env python3
"""
LEVEL 3: FIX LOGIC ERROR
========================
Difficulty: Easy-Medium
Time Limit: 2 minutes

TASK:
The file 'broken_logic.py' has logic errors. The functions produce wrong results.
Fix ALL logic errors so all tests pass.

BUGS TO FIND:
- Off-by-one errors
- Wrong operators
- Wrong comparisons

SUCCESS CRITERIA:
- All test assertions pass
"""
import os
import sys

BROKEN_CODE = '''
def get_last_element(lst):
    """Return the last element of a list."""
    return lst[len(lst)]  # BUG: Should be len(lst) - 1

def is_even(n):
    """Return True if n is even."""
    return n % 2 == 1  # BUG: Should be == 0

def sum_range(start, end):
    """Sum all numbers from start to end (inclusive)."""
    total = 0
    for i in range(start, end):  # BUG: Should be end + 1
        total += i
    return total

def find_max(numbers):
    """Find the maximum value in a list."""
    if not numbers:
        return None
    max_val = 0  # BUG: Should be numbers[0] or float('-inf')
    for n in numbers:
        if n > max_val:
            max_val = n
    return max_val

# TESTS - These must all pass
def run_tests():
    # Test get_last_element
    assert get_last_element([1, 2, 3]) == 3, "get_last_element failed"
    assert get_last_element(['a', 'b']) == 'b', "get_last_element failed"
    
    # Test is_even
    assert is_even(2) == True, "is_even(2) failed"
    assert is_even(3) == False, "is_even(3) failed"
    assert is_even(0) == True, "is_even(0) failed"
    
    # Test sum_range
    assert sum_range(1, 5) == 15, "sum_range(1,5) failed"  # 1+2+3+4+5=15
    assert sum_range(0, 3) == 6, "sum_range(0,3) failed"   # 0+1+2+3=6
    
    # Test find_max
    assert find_max([1, 5, 3, 9, 2]) == 9, "find_max positive failed"
    assert find_max([-5, -2, -10]) == -2, "find_max negative failed"
    assert find_max([42]) == 42, "find_max single failed"
    
    print("ALL TESTS PASSED!")
    return True

if __name__ == "__main__":
    run_tests()
'''

def setup():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(script_dir, "broken_logic.py")
    
    if not os.path.exists(target):
        with open(target, 'w') as f:
            f.write(BROKEN_CODE)
        print(f"Created broken file: {target}")
        print("FIX THE LOGIC ERRORS, then run this script again to verify.")
        return False
    return True

def verify():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(script_dir, "broken_logic.py")
    
    if not os.path.exists(target):
        setup()
        return False
    
    import subprocess
    result = subprocess.run([sys.executable, target], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"FAIL: Script crashed or tests failed")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False
    
    if "ALL TESTS PASSED!" not in result.stdout:
        print(f"FAIL: Tests did not pass. Output: {result.stdout}")
        return False
    
    print("LEVEL 3 PASSED")
    return True

if __name__ == "__main__":
    if not setup():
        sys.exit(1)
    sys.exit(0 if verify() else 1)
