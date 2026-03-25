#!/usr/bin/env python3
"""
LEVEL 4: IMPLEMENT FUNCTION FROM SCRATCH
========================================
Difficulty: Medium
Time Limit: 5 minutes

TASK:
Implement the function `binary_search` in 'implement_search.py'.
The function stub exists but returns None.
You must implement it correctly.

REQUIREMENTS:
- Must use binary search algorithm (not linear search)
- Must handle edge cases (empty list, element not found)
- Must return the index of the target, or -1 if not found
"""
import os
import sys

STUB_CODE = '''
def binary_search(sorted_list, target):
    """
    Perform binary search on a sorted list.
    
    Args:
        sorted_list: A list sorted in ascending order
        target: The value to search for
    
    Returns:
        The index of target if found, -1 otherwise
    
    IMPLEMENT THIS FUNCTION.
    """
    # TODO: Implement binary search
    pass


# TESTS - Do not modify
def run_tests():
    # Basic tests
    assert binary_search([1, 2, 3, 4, 5], 3) == 2, "Basic search failed"
    assert binary_search([1, 2, 3, 4, 5], 1) == 0, "First element failed"
    assert binary_search([1, 2, 3, 4, 5], 5) == 4, "Last element failed"
    assert binary_search([1, 2, 3, 4, 5], 6) == -1, "Not found failed"
    assert binary_search([1, 2, 3, 4, 5], 0) == -1, "Not found (low) failed"
    
    # Edge cases
    assert binary_search([], 5) == -1, "Empty list failed"
    assert binary_search([42], 42) == 0, "Single element found failed"
    assert binary_search([42], 99) == -1, "Single element not found failed"
    
    # Larger list
    big_list = list(range(0, 10000, 2))  # [0, 2, 4, ..., 9998]
    assert binary_search(big_list, 5000) == 2500, "Large list failed"
    assert binary_search(big_list, 5001) == -1, "Large list not found failed"
    
    print("ALL TESTS PASSED!")
    return True

if __name__ == "__main__":
    run_tests()
'''

def setup():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(script_dir, "implement_search.py")
    
    if not os.path.exists(target):
        with open(target, 'w') as f:
            f.write(STUB_CODE)
        print(f"Created stub file: {target}")
        print("IMPLEMENT binary_search(), then run this script again to verify.")
        return False
    return True

def verify():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(script_dir, "implement_search.py")
    
    if not os.path.exists(target):
        setup()
        return False
    
    import subprocess
    result = subprocess.run([sys.executable, target], capture_output=True, text=True, timeout=10)
    
    if result.returncode != 0:
        print(f"FAIL: Script crashed or tests failed")
        print(f"STDERR: {result.stderr}")
        return False
    
    if "ALL TESTS PASSED!" not in result.stdout:
        print(f"FAIL: Tests did not pass. Output: {result.stdout}")
        return False
    
    print("LEVEL 4 PASSED")
    return True

if __name__ == "__main__":
    if not setup():
        sys.exit(1)
    sys.exit(0 if verify() else 1)
