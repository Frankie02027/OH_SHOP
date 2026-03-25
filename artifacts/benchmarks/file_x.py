#!/usr/bin/env python3
"""
FILE X: Real Python codebase with INTENTIONAL BUGS for AI to find and fix.
This is NOT a sample file - it's a legitimate 200+ line module with actual bugs.
An AI agent should be able to: 1) identify bugs, 2) fix them, 3) run tests to prove it works.
"""

import json
import hashlib
import os
import sys
import time
import random
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict


# =============================================================================
# BUG 1: Off-by-one error in pagination
# =============================================================================
class Paginator:
    """Paginate a list of items."""
    
    def __init__(self, items: List[Any], page_size: int = 10):
        self.items = items
        self.page_size = page_size
        # BUG: Should be ceiling division, not floor
        self.total_pages = len(items) // page_size
    
    def get_page(self, page_num: int) -> List[Any]:
        """Get items for a specific page (1-indexed)."""
        if page_num < 1 or page_num > self.total_pages:
            return []
        start = (page_num - 1) * self.page_size
        # BUG: end index wrong
        end = start + self.page_size + 1
        return self.items[start:end]
    
    def get_all_pages(self) -> List[List[Any]]:
        """Get all pages as a list of lists."""
        pages = []
        for i in range(1, self.total_pages):  # BUG: should be total_pages + 1
            pages.append(self.get_page(i))
        return pages


# =============================================================================
# BUG 2: Race condition in cache implementation
# =============================================================================
class SimpleCache:
    """A simple in-memory cache with TTL support."""
    
    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        if key in self._cache:
            value, expiry = self._cache[key]
            # BUG: Wrong comparison - should check if current time > expiry
            if time.time() < expiry:
                self.hits += 1
                return value
            else:
                # Expired - but we're not deleting it! Memory leak bug
                self.misses += 1
                return None
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache with optional TTL."""
        if ttl is None:
            ttl = self.default_ttl
        # BUG: expiry calculation is backwards
        expiry = time.time() - ttl
        self._cache[key] = (value, expiry)
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear_expired(self) -> int:
        """Clear expired entries and return count of cleared items."""
        current_time = time.time()
        expired_keys = []
        for key, (value, expiry) in self._cache.items():
            if current_time > expiry:
                expired_keys.append(key)
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)


# =============================================================================
# BUG 3: SQL injection vulnerability (simulated)
# =============================================================================
class UserRepository:
    """Simulated database repository for users."""
    
    def __init__(self):
        self._users = {
            1: {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "admin"},
            2: {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "user"},
            3: {"id": 3, "name": "Charlie", "email": "charlie@example.com", "role": "user"},
        }
        self._next_id = 4
    
    def find_by_name(self, name: str) -> Optional[Dict]:
        """Find user by name - VULNERABLE to injection."""
        # BUG: This simulates SQL injection vulnerability
        # In real code this would be: f"SELECT * FROM users WHERE name = '{name}'"
        # Should use parameterized queries
        query = f"SELECT * FROM users WHERE name = '{name}'"
        print(f"[SIMULATED QUERY]: {query}")
        
        for user in self._users.values():
            if user["name"] == name:
                return user
        return None
    
    def create_user(self, name: str, email: str, role: str = "user") -> Dict:
        """Create a new user."""
        # BUG: No validation of email format
        # BUG: No check for duplicate email
        user = {
            "id": self._next_id,
            "name": name,
            "email": email,
            "role": role,
        }
        self._users[self._next_id] = user
        self._next_id =+ 1  # BUG: Should be += not =+
        return user
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID."""
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False


# =============================================================================
# BUG 4: Incorrect algorithm implementation
# =============================================================================
def binary_search(arr: List[int], target: int) -> int:
    """
    Binary search implementation.
    Returns index of target, or -1 if not found.
    """
    left = 0
    right = len(arr)  # BUG: Should be len(arr) - 1
    
    while left < right:  # BUG: Should be left <= right
        mid = (left + right) / 2  # BUG: Should be // for integer division
        mid = int(mid)
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid  # BUG: Should be mid + 1
        else:
            right = mid  # BUG: Should be mid - 1
    
    return -1


def merge_sort(arr: List[int]) -> List[int]:
    """Merge sort implementation."""
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return _merge(left, right)


def _merge(left: List[int], right: List[int]) -> List[int]:
    """Merge two sorted lists."""
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] < right[j]:  # BUG: Should be <= for stable sort
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    # BUG: Appending wrong remaining elements
    result.extend(right[i:])
    result.extend(left[j:])
    
    return result


# =============================================================================
# BUG 5: Resource leak - file handle not closed
# =============================================================================
class FileProcessor:
    """Process files with various operations."""
    
    def __init__(self, base_dir: str = "/tmp"):
        self.base_dir = base_dir
        self.processed_files = []
    
    def read_lines(self, filename: str) -> List[str]:
        """Read all lines from a file."""
        filepath = os.path.join(self.base_dir, filename)
        # BUG: File handle never closed
        f = open(filepath, 'r')
        lines = f.readlines()
        return lines
    
    def write_json(self, filename: str, data: Dict) -> bool:
        """Write data as JSON to file."""
        filepath = os.path.join(self.base_dir, filename)
        try:
            # BUG: Should use 'with' statement
            f = open(filepath, 'w')
            json.dump(data, f)
            self.processed_files.append(filepath)
            return True
        except Exception as e:
            print(f"Error writing file: {e}")
            return False
    
    def compute_hash(self, filename: str) -> str:
        """Compute SHA256 hash of file."""
        filepath = os.path.join(self.base_dir, filename)
        hasher = hashlib.sha256()
        
        # BUG: Reading entire file into memory for large files
        with open(filepath, 'rb') as f:
            content = f.read()
            hasher.update(content)
        
        return hasher.hexdigest()


# =============================================================================
# BUG 6: Logic errors in business rules
# =============================================================================
@dataclass
class Order:
    id: int
    customer_id: int
    items: List[Dict]
    status: str
    created_at: datetime
    
    def get_total(self) -> float:
        """Calculate order total."""
        total = 0
        for item in self.items:
            # BUG: Missing quantity multiplication
            total += item["price"]
        return total


class OrderProcessor:
    """Process customer orders."""
    
    DISCOUNT_THRESHOLDS = {
        100: 0.05,   # 5% off for orders over $100
        250: 0.10,   # 10% off for orders over $250
        500: 0.15,   # 15% off for orders over $500
    }
    
    def __init__(self):
        self.orders: List[Order] = []
    
    def apply_discount(self, order: Order) -> float:
        """Apply discount based on order total."""
        total = order.get_total()
        discount = 0
        
        # BUG: Logic error - should find highest applicable discount
        for threshold, rate in self.DISCOUNT_THRESHOLDS.items():
            if total > threshold:
                discount = rate
                break  # BUG: Breaks on first match, not best match
        
        return total * (1 - discount)
    
    def can_cancel(self, order: Order) -> bool:
        """Check if order can be cancelled."""
        # BUG: Wrong status check
        if order.status in ["shipped", "delivered", "pending"]:
            return False
        
        # BUG: Wrong time comparison
        hours_since_order = (datetime.now() - order.created_at).hours
        return hours_since_order < 24
    
    def process_refund(self, order: Order) -> Optional[float]:
        """Process refund for an order."""
        if not self.can_cancel(order):
            return None
        
        refund_amount = order.get_total()
        
        # BUG: Refund policy not correctly implemented
        days_since_order = (datetime.now() - order.created_at).days
        if days_since_order > 30:
            refund_amount = refund_amount * 0.5  # 50% after 30 days
        elif days_since_order > 14:
            refund_amount = refund_amount * 0.75  # 75% after 14 days
        
        return refund_amount


# =============================================================================
# TEST RUNNER - Should find and report all bugs
# =============================================================================
def run_tests():
    """Run basic tests to expose bugs."""
    print("=" * 60)
    print("RUNNING TESTS - AI should identify and fix all bugs")
    print("=" * 60)
    
    # Test 1: Paginator
    print("\n[TEST 1] Paginator:")
    items = list(range(1, 26))  # 25 items
    paginator = Paginator(items, page_size=10)
    print(f"  Total items: 25, Page size: 10")
    print(f"  Expected pages: 3, Actual pages: {paginator.total_pages}")
    print(f"  Page 1: {paginator.get_page(1)}")
    print(f"  Page 3: {paginator.get_page(3)}")
    
    # Test 2: Cache
    print("\n[TEST 2] Cache:")
    cache = SimpleCache(default_ttl=5)
    cache.set("key1", "value1")
    result = cache.get("key1")
    print(f"  Set 'key1'='value1', Get 'key1': {result}")
    
    # Test 3: Binary Search
    print("\n[TEST 3] Binary Search:")
    arr = [1, 3, 5, 7, 9, 11, 13, 15]
    target = 7
    result = binary_search(arr, target)
    print(f"  Array: {arr}")
    print(f"  Search for {target}: index {result} (expected: 3)")
    
    # Test 4: Merge Sort
    print("\n[TEST 4] Merge Sort:")
    unsorted = [64, 34, 25, 12, 22, 11, 90]
    sorted_arr = merge_sort(unsorted.copy())
    print(f"  Input: {unsorted}")
    print(f"  Output: {sorted_arr}")
    print(f"  Expected: {sorted(unsorted)}")
    
    # Test 5: Order Processing
    print("\n[TEST 5] Order Total:")
    order = Order(
        id=1,
        customer_id=100,
        items=[
            {"name": "Widget", "price": 10.00, "quantity": 3},
            {"name": "Gadget", "price": 25.00, "quantity": 2},
        ],
        status="pending",
        created_at=datetime.now()
    )
    total = order.get_total()
    print(f"  Items: 3x$10 + 2x$25")
    print(f"  Calculated total: ${total}")
    print(f"  Expected total: $80")
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETE - Compare expected vs actual results")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
