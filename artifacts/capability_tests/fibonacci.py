#!/usr/bin/env python3
"""
AI-Generated: Fibonacci sequence with memoization
"""
from functools import lru_cache

@lru_cache(maxsize=None)
def fibonacci(n: int) -> int:
    """Calculate nth Fibonacci number."""
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

def main():
    print("First 20 Fibonacci numbers:")
    for i in range(10):
        print(f"fib({i}) = {fibonacci(i)}")
    
if __name__ == "__main__":
    main()
