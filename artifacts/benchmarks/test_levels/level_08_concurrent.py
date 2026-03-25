#!/usr/bin/env python3
"""
LEVEL 8: CONCURRENT PROGRAMMING - THREAD-SAFE DATA PROCESSING
=============================================================
Difficulty: Very Hard
Time Limit: 25 minutes

TASK:
Implement a thread-safe task processor in 'implement_concurrent.py'.
Multiple worker threads process tasks from a shared queue.
Results must be collected without race conditions or deadlocks.

REQUIREMENTS:
- Producer-consumer pattern with worker threads
- Thread-safe result collection
- Proper shutdown mechanism (no hanging threads)
- Handle task failures gracefully
- Tasks must be processed in parallel (not sequentially)
"""
import os
import sys
import time

STUB_CODE = '''
import threading
import queue
import time
from typing import List, Callable, Any, Dict
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import traceback


@dataclass
class Task:
    """A task to be processed."""
    task_id: int
    data: Any
    

@dataclass 
class TaskResult:
    """Result of processing a task."""
    task_id: int
    success: bool
    result: Any = None
    error: str = None


class ThreadSafeTaskProcessor:
    """
    A thread-safe task processor using producer-consumer pattern.
    
    IMPLEMENT THIS CLASS.
    """
    
    def __init__(self, num_workers: int = 4):
        """
        Initialize with specified number of worker threads.
        
        Args:
            num_workers: Number of worker threads to spawn
        """
        self.num_workers = num_workers
        # TODO: Initialize thread-safe data structures
        # - Task queue
        # - Results storage
        # - Synchronization primitives (locks, events, etc.)
        pass
    
    def submit_task(self, task: Task) -> None:
        """
        Submit a task for processing. Must be thread-safe.
        """
        # TODO: Add task to queue
        pass
    
    def process_task(self, task: Task, processor: Callable[[Any], Any]) -> TaskResult:
        """
        Process a single task with the given processor function.
        
        Args:
            task: The task to process
            processor: Function that transforms task.data
        
        Returns:
            TaskResult with success status and result/error
        """
        # TODO: Process task and handle exceptions
        pass
    
    def start_workers(self, processor: Callable[[Any], Any]) -> None:
        """
        Start worker threads that process tasks from the queue.
        
        Args:
            processor: Function to apply to each task's data
        """
        # TODO: Start worker threads
        pass
    
    def wait_for_completion(self, timeout: float = None) -> bool:
        """
        Wait for all submitted tasks to complete.
        
        Args:
            timeout: Maximum seconds to wait (None = wait forever)
        
        Returns:
            True if all tasks completed, False if timeout
        """
        # TODO: Wait for all tasks to be processed
        pass
    
    def shutdown(self) -> None:
        """
        Shutdown all worker threads gracefully.
        Workers should finish current task then exit.
        """
        # TODO: Signal workers to stop and wait for them
        pass
    
    def get_results(self) -> List[TaskResult]:
        """
        Get all collected results. Must be thread-safe.
        
        Returns:
            List of TaskResult objects
        """
        # TODO: Return collected results
        pass
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get processing statistics.
        
        Returns:
            Dict with keys: 'submitted', 'completed', 'failed', 'pending'
        """
        # TODO: Return stats
        pass


# TESTS - Do not modify
def run_tests():
    import random
    
    def slow_double(x):
        """Simulates slow processing."""
        time.sleep(random.uniform(0.01, 0.05))
        return x * 2
    
    def sometimes_fails(x):
        """Sometimes raises an exception."""
        time.sleep(0.01)
        if x % 5 == 0:
            raise ValueError(f"Bad value: {x}")
        return x * 3
    
    # Test 1: Basic parallel processing
    print("Test 1: Basic parallel processing...")
    processor = ThreadSafeTaskProcessor(num_workers=4)
    
    tasks = [Task(i, i) for i in range(20)]
    for task in tasks:
        processor.submit_task(task)
    
    start_time = time.time()
    processor.start_workers(slow_double)
    completed = processor.wait_for_completion(timeout=10)
    elapsed = time.time() - start_time
    
    assert completed, "Tasks should complete within timeout"
    
    results = processor.get_results()
    assert len(results) == 20, f"Should have 20 results, got {len(results)}"
    
    # Verify parallel execution (should be much faster than sequential)
    # 20 tasks * 0.03s avg = 0.6s sequential, but parallel should be ~0.15s
    assert elapsed < 1.0, f"Should be parallel, took {elapsed}s"
    
    # Verify results
    for r in results:
        assert r.success, f"Task {r.task_id} failed unexpectedly"
        assert r.result == r.task_id * 2, f"Wrong result for task {r.task_id}"
    
    processor.shutdown()
    
    # Test 2: Handle failures
    print("Test 2: Handle failures...")
    processor2 = ThreadSafeTaskProcessor(num_workers=2)
    
    tasks2 = [Task(i, i) for i in range(15)]
    for task in tasks2:
        processor2.submit_task(task)
    
    processor2.start_workers(sometimes_fails)
    processor2.wait_for_completion(timeout=10)
    
    results2 = processor2.get_results()
    stats = processor2.get_stats()
    
    # Tasks 0, 5, 10 should fail (x % 5 == 0)
    failed_count = sum(1 for r in results2 if not r.success)
    assert failed_count == 3, f"Expected 3 failures, got {failed_count}"
    assert stats['failed'] == 3, f"Stats should show 3 failed"
    assert stats['completed'] == 15, f"All 15 should be completed (success or fail)"
    
    processor2.shutdown()
    
    # Test 3: Concurrent submission and processing
    print("Test 3: Concurrent submission...")
    processor3 = ThreadSafeTaskProcessor(num_workers=4)
    processor3.start_workers(slow_double)
    
    # Submit tasks from multiple threads
    def submit_batch(start, count):
        for i in range(start, start + count):
            processor3.submit_task(Task(i, i))
            time.sleep(0.001)
    
    threads = [
        threading.Thread(target=submit_batch, args=(0, 25)),
        threading.Thread(target=submit_batch, args=(100, 25)),
        threading.Thread(target=submit_batch, args=(200, 25)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Wait for processing
    time.sleep(0.5)  # Give time for tasks to be processed
    processor3.wait_for_completion(timeout=10)
    
    results3 = processor3.get_results()
    assert len(results3) == 75, f"Should have 75 results, got {len(results3)}"
    
    processor3.shutdown()
    
    # Test 4: Clean shutdown
    print("Test 4: Clean shutdown...")
    processor4 = ThreadSafeTaskProcessor(num_workers=4)
    processor4.start_workers(slow_double)
    
    # Submit some tasks but don't wait
    for i in range(10):
        processor4.submit_task(Task(i, i))
    
    # Immediate shutdown should not hang
    shutdown_start = time.time()
    processor4.shutdown()
    shutdown_time = time.time() - shutdown_start
    
    assert shutdown_time < 5.0, f"Shutdown took too long: {shutdown_time}s"
    
    print("ALL TESTS PASSED!")
    return True


if __name__ == "__main__":
    run_tests()
'''

def setup():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(script_dir, "implement_concurrent.py")
    
    if not os.path.exists(target):
        with open(target, 'w') as f:
            f.write(STUB_CODE)
        print(f"Created stub file: {target}")
        print("IMPLEMENT ThreadSafeTaskProcessor class, then run this script again.")
        return False
    return True

def verify():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(script_dir, "implement_concurrent.py")
    
    if not os.path.exists(target):
        setup()
        return False
    
    import subprocess
    try:
        result = subprocess.run([sys.executable, target], capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        print("FAIL: Timeout - probable deadlock or hanging threads")
        return False
    
    if result.returncode != 0:
        print(f"FAIL: Tests failed")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False
    
    if "ALL TESTS PASSED!" not in result.stdout:
        print(f"FAIL: Tests did not pass")
        print(f"Output: {result.stdout}")
        return False
    
    print("LEVEL 8 PASSED")
    return True

if __name__ == "__main__":
    if not setup():
        sys.exit(1)
    sys.exit(0 if verify() else 1)
