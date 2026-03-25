# OpenHands AI Capability Benchmark Suite

**Version:** 1.0  
**Date:** 2026-03-22  
**Methodology:** Inspired by HumanEval, MBPP, SWE-bench, MMLU, and K-12 CS standards

---

## Benchmark Categories

### Category A: Code Synthesis (HumanEval-style)
Function-level code generation from docstrings/specifications.

### Category B: Bug Detection & Repair (SWE-bench-style)
Given buggy code, identify and fix the issue.

### Category C: System Administration
Environment manipulation, package management, service configuration.

### Category D: Multi-file Project Tasks
Create complete projects with multiple interconnected files.

### Category E: Data Processing & Analysis
Parse, transform, and analyze structured data.

### Category F: Vision Understanding (Expected FAIL)
Image description, OCR, diagram interpretation.

---

## GRADE LEVELS

| Level | Equivalent | Description |
|-------|------------|-------------|
| G1 | Elementary (K-5) | Basic operations, simple scripts |
| G2 | Middle School (6-8) | Functions, loops, basic algorithms |
| G3 | High School (9-12) | Data structures, OOP, file I/O |
| G4 | College Freshman | Algorithms, complexity, APIs |
| G5 | College Senior | System design, debugging, optimization |
| G6 | Professional | Production code, multi-service architecture |
| G7 | Expert | Novel problem solving, performance critical |

---

## TEST SUITE

### A. CODE SYNTHESIS TESTS

#### A1-G1: Hello World Variations
```
Task: Write a Python function that takes a name and returns "Hello, {name}!"
Input: "World"
Expected Output: "Hello, World!"
```

#### A2-G2: FizzBuzz
```
Task: Write a function fizzbuzz(n) that returns:
- "Fizz" if n is divisible by 3
- "Buzz" if n is divisible by 5  
- "FizzBuzz" if divisible by both
- str(n) otherwise
Test: fizzbuzz(15) == "FizzBuzz", fizzbuzz(9) == "Fizz"
```

#### A3-G3: Palindrome Checker
```
Task: Write is_palindrome(s) that returns True if string s reads same forwards and backwards (ignore case/spaces)
Test: is_palindrome("A man a plan a canal Panama") == True
```

#### A4-G3: Prime Number Generator
```
Task: Write sieve_of_eratosthenes(n) returning all primes up to n
Test: sieve_of_eratosthenes(20) == [2, 3, 5, 7, 11, 13, 17, 19]
```

#### A5-G4: Binary Search
```
Task: Implement binary_search(arr, target) returning index or -1
Test: binary_search([1,3,5,7,9], 5) == 2
```

#### A6-G4: Merge Sort
```
Task: Implement merge_sort(arr) that sorts array using merge sort algorithm
Test: merge_sort([64, 34, 25, 12, 22, 11, 90]) == [11, 12, 22, 25, 34, 64, 90]
```

#### A7-G5: LRU Cache
```
Task: Implement an LRU Cache class with get(key) and put(key, value) methods
Capacity: 2
Operations: put(1,1), put(2,2), get(1)->1, put(3,3), get(2)->-1 (evicted)
```

#### A8-G5: Tree Traversal
```
Task: Given a binary tree node class, implement inorder, preorder, postorder traversal
Return lists of values in each order
```

#### A9-G6: Rate Limiter
```
Task: Implement a token bucket rate limiter class
- allow(n) returns True if n tokens available, False otherwise
- Refill rate configurable
```

#### A10-G7: Concurrent Web Scraper
```
Task: Write an async function that fetches multiple URLs concurrently 
with configurable concurrency limit and timeout handling
```

---

### B. BUG DETECTION & REPAIR TESTS

#### B1-G1: Missing Colon
```python
# Fix this code
def greet(name)
    return f"Hello, {name}"
```

#### B2-G2: Off-by-One Error
```python
def get_last(lst):
    return lst[len(lst)]  # Bug: Should be len(lst) - 1
```

#### B3-G3: Infinite Loop
```python
def count_down(n):
    while n > 0:
        print(n)
        # Bug: Missing n -= 1
```

#### B4-G3: Wrong Comparison
```python
def find_max(numbers):
    max_val = 0  # Bug: Should be float('-inf') or numbers[0]
    for n in numbers:
        if n < max_val:  # Bug: Should be >
            max_val = n
    return max_val
```

#### B5-G4: Memory Leak Pattern
```python
class Cache:
    _instances = []  # Bug: Class-level list grows forever
    def __init__(self, data):
        self.data = data
        Cache._instances.append(self)
```

#### B6-G4: Race Condition
```python
counter = 0
def increment():
    global counter
    temp = counter  # Bug: Not thread-safe
    temp += 1
    counter = temp
```

#### B7-G5: SQL Injection Vulnerability
```python
def get_user(username):
    query = f"SELECT * FROM users WHERE name = '{username}'"  # Bug: SQL injection
    return db.execute(query)
```

#### B8-G5: Recursive Stack Overflow
```python
def factorial(n):
    return n * factorial(n - 1)  # Bug: No base case
```

#### B9-G6: Deadlock Pattern
```python
lock1 = Lock()
lock2 = Lock()

def func1():
    with lock1:
        with lock2:  # Deadlock risk with func2
            pass

def func2():
    with lock2:
        with lock1:
            pass
```

#### B10-G7: Subtle Floating Point Bug
```python
def calculate_discount(prices):
    total = 0.0
    for p in prices:
        total += p * 0.1  # Floating point accumulation error
    return round(total, 2)  # May still be wrong
```

---

### C. SYSTEM ADMINISTRATION TESTS

#### C1-G2: Create Directory Structure
```
Task: Create the following structure:
project/
  src/
    main.py
  tests/
    test_main.py
  README.md
```

#### C2-G3: Install Package and Use It
```
Task: Install the 'cowsay' package and make it print "Hello AI"
```

#### C3-G4: Create and Run Systemd Service
```
Task: Create a systemd service file for a Python HTTP server on port 8888
```

#### C4-G4: Set Up Virtual Environment
```
Task: Create a Python venv, install requests, verify it works
```

#### C5-G5: Configure Nginx Reverse Proxy
```
Task: Create nginx config to proxy /api to localhost:8000
```

#### C6-G5: Database Setup
```
Task: Install SQLite, create a database with users table, insert 3 records
```

#### C7-G6: Docker Container Management
```
Task: Write Dockerfile for a Python Flask app, build and test it
```

#### C8-G6: Cron Job Setup
```
Task: Create a cron job that runs a cleanup script every day at 3am
```

#### C9-G7: TLS Certificate Generation
```
Task: Generate self-signed TLS certificate using openssl
```

#### C10-G7: Firewall Rules
```
Task: Set up iptables rules to allow only HTTP/HTTPS and SSH
```

---

### D. MULTI-FILE PROJECT TESTS

#### D1-G3: Calculator Module
```
Create:
- calculator.py (add, subtract, multiply, divide functions)
- test_calculator.py (unit tests for all functions)
- Run tests and verify pass
```

#### D2-G4: CLI Todo App
```
Create:
- todo.py (main CLI application)
- storage.py (JSON file persistence)
- models.py (Task dataclass)
Commands: add, list, complete, delete
```

#### D3-G5: REST API
```
Create:
- app.py (FastAPI application)
- models.py (Pydantic models)
- database.py (SQLite operations)
- test_api.py (API tests)
Endpoints: GET/POST/PUT/DELETE /items
```

#### D4-G6: Microservice with Config
```
Create:
- main.py (async service)
- config.py (environment-based config)
- middleware.py (logging, error handling)
- Dockerfile
- docker-compose.yml
- .env.example
```

---

### E. DATA PROCESSING TESTS

#### E1-G2: CSV Parsing
```
Task: Read a CSV file and print the sum of a numeric column
```

#### E2-G3: JSON Transformation
```
Task: Transform nested JSON to flattened structure
Input: {"user": {"name": "John", "address": {"city": "NYC"}}}
Output: {"user.name": "John", "user.address.city": "NYC"}
```

#### E3-G4: Log Analysis
```
Task: Parse Apache log file, count requests per status code
```

#### E4-G5: Data Validation Pipeline
```
Task: Create a data validation pipeline with:
- Schema definition
- Type checking
- Custom validators
- Error reporting
```

#### E5-G6: ETL Pipeline
```
Task: Extract from CSV, transform (clean, normalize), load to SQLite
Include error handling and logging
```

---

### F. VISION UNDERSTANDING TESTS (Expected FAIL - No Vision Model)

#### F1: Simple Object Recognition
```
Image: Photo of a red apple on a white table
Task: "What object is in this image?"
Expected: "apple" or "red apple"
```

#### F2: Text/OCR from Screenshot
```
Image: Terminal screenshot showing:
$ python --version
Python 3.12.1

Task: "What Python version is shown?"
Expected: "3.12.1"
```

#### F3: Code Screenshot Reading
```
Image: Screenshot of code editor with Python function
Task: "What does this function do? Are there any bugs?"
```

#### F4: Diagram Interpretation
```
Image: Flowchart: Start → Decision → Yes/No branches → End
Task: "Describe this flowchart"
```

#### F5: Complex Scene Description
```
Image: Office scene with laptop, coffee mug, notebook, pen, plant
Task: "List all objects visible in this image"
```

#### F6: Handwriting Recognition
```
Image: Handwritten math equation: 2x + 3 = 7
Task: "What equation is written? Solve for x."
```

#### F7: Chart/Graph Reading
```
Image: Bar chart showing sales by month
Task: "Which month had the highest sales?"
```

#### F8: Error Message Screenshot
```
Image: Terminal with Python traceback
Task: "What error occurred and on which line?"
```

---

## SCORING METHODOLOGY

### Per-Test Scoring:
- **PASS (100%)**: Correct solution, runs without error
- **PARTIAL (50%)**: Approach correct but bugs remain
- **FAIL (0%)**: Incorrect or no solution

### Category Weights:
- Code Synthesis: 25%
- Bug Repair: 20%
- System Admin: 15%
- Multi-file: 20%
- Data Processing: 10%
- Vision: 10%

### Expected Results (No Vision Model):
- Categories A-E: 80-95% pass rate
- Category F: 0% (WILL FAIL - no vision capability)

---

## EXECUTION PROTOCOL

For each test:
1. Send exact task prompt to OpenHands
2. Wait for completion (max 5 minutes per test)
3. Verify output matches expected
4. Record all commands executed
5. Document any errors
6. Score and move to next test

---

## TEST DATA FILES NEEDED

1. `test_data/sample.csv` - For CSV tests
2. `test_data/sample.json` - For JSON tests  
3. `test_data/access.log` - For log analysis
4. `test_images/` - For vision tests (will fail)
