# OpenHands Capability Test Guide

**Purpose:** Systematically test what OpenHands can and cannot do, with ACTUAL execution proof.

---

## Test Tiers

### TIER 1: Basic File Operations (Easy)
| Test # | Task | Pass Criteria |
|--------|------|---------------|
| 1.1 | Create a simple text file | File exists with correct content |
| 1.2 | Create a Python script that prints "Hello World" | Script runs without error |
| 1.3 | Create a JSON configuration file | Valid JSON, parseable |
| 1.4 | Read an existing file and summarize it | Accurate summary |
| 1.5 | Edit an existing file (change one line) | Change applied correctly |

### TIER 2: Code Generation (Medium)
| Test # | Task | Pass Criteria |
|--------|------|---------------|
| 2.1 | Write a Python function to calculate factorial | Correct output for test inputs |
| 2.2 | Write a C++ program that sorts an array | Compiles and runs correctly |
| 2.3 | Create a Bash script with conditionals and loops | Executes correctly |
| 2.4 | Write a simple REST API in Python (FastAPI) | Server starts, endpoint responds |
| 2.5 | Generate a complete Python class with methods | Passes unit tests |

### TIER 3: Debugging (Hard)
| Test # | Task | Pass Criteria |
|--------|------|---------------|
| 3.1 | Fix a Python file with syntax error | Code runs after fix |
| 3.2 | Fix a Python file with logic error (off-by-one) | Correct output after fix |
| 3.3 | Fix a C++ file with segfault | No crash after fix |
| 3.4 | Debug a failing unit test | Test passes after fix |
| 3.5 | Fix a multi-file bug (import error) | All files work together |

### TIER 4: Environment Manipulation (Hard)
| Test # | Task | Pass Criteria |
|--------|------|---------------|
| 4.1 | Install a missing Python package and use it | Package works |
| 4.2 | Install a system package (apt) and use it | Package works |
| 4.3 | Compile and run a program requiring gcc | Executable runs |
| 4.4 | Set up a virtual environment | Venv created and activated |
| 4.5 | Create a systemd service file | Valid syntax |

### TIER 5: Media/Binary Files (Hard)
| Test # | Task | Pass Criteria |
|--------|------|---------------|
| 5.1 | Create an image using ImageMagick | Valid image file created |
| 5.2 | Resize/convert an existing image | Output matches spec |
| 5.3 | Create a video file using ffmpeg | Valid video created |
| 5.4 | Create a ZIP archive with multiple files | Archive valid, contents correct |
| 5.5 | Extract and modify contents of archive | Modified archive works |

### TIER 6: Vision/Image Understanding (CRITICAL - Expected to FAIL)
| Test # | Task | Pass Criteria |
|--------|------|---------------|
| 6.1 | Describe what's in a photograph | Accurate description |
| 6.2 | Read text from a screenshot | Exact text extracted |
| 6.3 | Identify objects in an image | Objects correctly named |
| 6.4 | Read code from a terminal screenshot | Code accurately transcribed |
| 6.5 | Describe a complex diagram/chart | Accurate interpretation |

---

## Test Execution Protocol

For EACH test:
1. Create a new conversation with the task
2. Watch what commands/actions the agent takes
3. Record:
   - Task given
   - Agent's plan/reasoning
   - Commands executed
   - Errors encountered
   - Final result
   - PASS/FAIL determination

---

## Buggy Files for Debugging Tests

### Bug 3.1: Python Syntax Error
```python
# buggy_syntax.py
def calculate_sum(numbers)  # missing colon
    total = 0
    for n in numbers:
        total += n
    return total

print(calculate_sum([1, 2, 3, 4, 5]))
```

### Bug 3.2: Python Logic Error (Off-by-One)
```python
# buggy_logic.py
def get_last_element(lst):
    """Return the last element of a list."""
    return lst[len(lst)]  # Should be len(lst) - 1

print(get_last_element([10, 20, 30, 40]))  # Should print 40
```

### Bug 3.3: C++ Segfault
```cpp
// buggy_segfault.cpp
#include <iostream>
int main() {
    int* ptr = nullptr;
    *ptr = 42;  // Dereferencing null pointer
    std::cout << *ptr << std::endl;
    return 0;
}
```

### Bug 3.4: Failing Unit Test
```python
# buggy_test.py
def reverse_string(s):
    return s  # Bug: should be s[::-1]

# Test
assert reverse_string("hello") == "olleh", "reverse_string failed"
print("All tests passed!")
```

### Bug 3.5: Import Error (Multi-file)
```python
# main.py
from utls import helper_function  # Typo: should be 'utils'
print(helper_function(5))

# utils.py
def helper_function(x):
    return x * 2
```

---

## Test Images for Vision Tests

### Image 6.1: Simple photo
- A photo of a red car in a parking lot

### Image 6.2: Terminal screenshot with text
```
$ python --version
Python 3.12.1
$ pip list | head -5
Package    Version
---------- -------
pip        24.0
setuptools 69.0.2
wheel      0.42.0
```

### Image 6.3: Objects photo
- Photo containing: laptop, coffee mug, notebook, pen

### Image 6.4: Code screenshot
- Screenshot of Python code with a bug (visible syntax error)

### Image 6.5: Architecture diagram
- A flowchart showing: User → API Gateway → Service → Database

---

## Expected Results Summary

| Tier | Expected Pass Rate | Notes |
|------|-------------------|-------|
| Tier 1 | 100% | Basic operations |
| Tier 2 | 90-100% | Code generation is strong |
| Tier 3 | 70-90% | Debugging harder, depends on error clarity |
| Tier 4 | 90-100% | Root access helps |
| Tier 5 | 90-100% | Tool commands well documented |
| **Tier 6** | **0%** | **NO VISION MODEL - WILL FAIL** |

---

## Execution Log Template

```markdown
## Test X.Y: [Name]

**Task Given:**
> [exact prompt sent to OpenHands]

**Agent Actions:**
1. [first action]
2. [second action]
...

**Commands Executed:**
```bash
[actual commands]
```

**Errors/Issues:**
- [any errors]

**Final Output:**
[what was produced]

**Result:** PASS / FAIL

**Notes:**
[observations]
```
