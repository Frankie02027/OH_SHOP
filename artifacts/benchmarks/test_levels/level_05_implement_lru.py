#!/usr/bin/env python3
"""
LEVEL 5: IMPLEMENT DATA STRUCTURE
=================================
Difficulty: Medium-Hard
Time Limit: 10 minutes

TASK:
Implement a complete LRU (Least Recently Used) Cache in 'implement_lru.py'.
The cache has a maximum capacity and evicts the least recently used item when full.

REQUIREMENTS:
- get(key): Return value if exists, -1 otherwise. Mark as recently used.
- put(key, value): Insert or update. Evict LRU if at capacity.
- O(1) time complexity for both operations
"""
import os
import sys

STUB_CODE = '''
class LRUCache:
    """
    Implement an LRU Cache with O(1) get and put operations.
    
    Hint: Use a combination of a dictionary and a doubly-linked list,
    or use collections.OrderedDict.
    """
    
    def __init__(self, capacity: int):
        """Initialize cache with given capacity."""
        # TODO: Implement
        pass
    
    def get(self, key: int) -> int:
        """
        Get value for key. Return -1 if not found.
        Mark key as recently used.
        """
        # TODO: Implement
        pass
    
    def put(self, key: int, value: int) -> None:
        """
        Put key-value pair. If at capacity, evict LRU item first.
        """
        # TODO: Implement
        pass


# TESTS - Do not modify
def run_tests():
    # Basic operations
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    assert cache.get(1) == 1, "Get existing key failed"
    
    cache.put(3, 3)  # Evicts key 2 (LRU)
    assert cache.get(2) == -1, "Should have evicted key 2"
    
    cache.put(4, 4)  # Evicts key 1
    assert cache.get(1) == -1, "Should have evicted key 1"
    assert cache.get(3) == 3, "Key 3 should exist"
    assert cache.get(4) == 4, "Key 4 should exist"
    
    # Update existing key
    cache2 = LRUCache(2)
    cache2.put(1, 1)
    cache2.put(2, 2)
    cache2.put(1, 10)  # Update, should not evict
    assert cache2.get(1) == 10, "Update failed"
    assert cache2.get(2) == 2, "Key 2 should still exist"
    
    # Access pattern affects eviction
    cache3 = LRUCache(2)
    cache3.put(1, 1)
    cache3.put(2, 2)
    cache3.get(1)  # Access 1, so 2 becomes LRU
    cache3.put(3, 3)  # Should evict 2, not 1
    assert cache3.get(2) == -1, "Key 2 should be evicted"
    assert cache3.get(1) == 1, "Key 1 should exist after access"
    
    # Capacity 1
    cache4 = LRUCache(1)
    cache4.put(1, 1)
    cache4.put(2, 2)
    assert cache4.get(1) == -1, "Capacity 1: key 1 should be evicted"
    assert cache4.get(2) == 2, "Capacity 1: key 2 should exist"
    
    print("ALL TESTS PASSED!")
    return True

if __name__ == "__main__":
    run_tests()
'''

def setup():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(script_dir, "implement_lru.py")
    
    if not os.path.exists(target):
        with open(target, 'w') as f:
            f.write(STUB_CODE)
        print(f"Created stub file: {target}")
        print("IMPLEMENT LRUCache class, then run this script again to verify.")
        return False
    return True

def verify():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(script_dir, "implement_lru.py")
    
    if not os.path.exists(target):
        setup()
        return False
    
    import subprocess
    result = subprocess.run([sys.executable, target], capture_output=True, text=True, timeout=10)
    
    if result.returncode != 0:
        print(f"FAIL: Tests failed")
        print(f"STDERR: {result.stderr}")
        return False
    
    if "ALL TESTS PASSED!" not in result.stdout:
        print(f"FAIL: Tests did not pass. Output: {result.stdout}")
        return False
    
    print("LEVEL 5 PASSED")
    return True

if __name__ == "__main__":
    if not setup():
        sys.exit(1)
    sys.exit(0 if verify() else 1)
