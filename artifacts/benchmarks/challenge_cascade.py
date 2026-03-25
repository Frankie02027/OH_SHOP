#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     CASCADING NIGHTMARE CHALLENGE                             ║
║                                                                               ║
║  This is NOT a simple bug fix. This is a GAUNTLET.                           ║
║                                                                               ║
║  RULES:                                                                       ║
║  1. Run this file. It will fail.                                             ║
║  2. Fix the error. Run again.                                                ║
║  3. A NEW error will appear. Fix that too.                                   ║
║  4. Keep going until ALL 7 STAGES pass.                                      ║
║  5. Each stage unlocks the next.                                             ║
║  6. Some fixes will BREAK things you already fixed.                          ║
║  7. You MUST read error messages carefully - some are LIES.                  ║
║                                                                               ║
║  EXPECTED BEHAVIOR FROM AI:                                                   ║
║  - Weak AI: Quits after 1-2 failures                                         ║
║  - Decent AI: Gets to stage 3-4, gives up                                    ║
║  - Strong AI: Pushes through, tries multiple approaches                      ║
║  - Elite AI: Completes all 7 stages, documents the journey                   ║
║                                                                               ║
║  SUCCESS = Print "ALL 7 STAGES COMPLETE" at the end                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import os

# ============================================================================
# STAGE 0: THE IMPORT TRAP
# This looks like it should work but doesn't. Why?
# ============================================================================
try:
    from cascading_deps import validate_environment
except ImportError as e:
    print(f"[STAGE 0 FAILED] Import error: {e}")
    print("HINT: The dependency file doesn't exist. You need to CREATE it.")
    print("      But what should it contain? Read the code carefully...")
    sys.exit(1)

# ============================================================================
# STAGE 1: THE ENVIRONMENT CHECK (but it's lying to you)
# ============================================================================
def stage_1():
    print("\n[STAGE 1] Environment Validation...")
    result = validate_environment()
    
    # This comparison looks correct but isn't
    if result == True:
        print("[STAGE 1 PASSED]")
        return True
    elif result == "True":
        print("[STAGE 1 PASSED]")
        return True
    else:
        print(f"[STAGE 1 FAILED] validate_environment() returned: {result} (type: {type(result)})")
        print("HINT: The function exists but returns something unexpected.")
        print("      Did you look at WHAT the function should return?")
        return False

# ============================================================================
# STAGE 2: THE DATA CORRUPTION PUZZLE
# The data file exists but is "corrupted" - can the AI figure out how?
# ============================================================================
def stage_2():
    print("\n[STAGE 2] Data Integrity Check...")
    
    data_file = os.path.join(os.path.dirname(__file__), "stage2_data.dat")
    
    if not os.path.exists(data_file):
        print(f"[STAGE 2 FAILED] Data file missing: {data_file}")
        print("HINT: Create the data file. But what format? Check stage_2_validate()")
        return False
    
    with open(data_file, 'r') as f:
        content = f.read()
    
    # The validation is... peculiar
    if not stage_2_validate(content):
        print("[STAGE 2 FAILED] Data validation failed")
        print("HINT: The data must pass stage_2_validate(). What does it check?")
        return False
    
    print("[STAGE 2 PASSED]")
    return True

def stage_2_validate(content: str) -> bool:
    """
    Validates the data file content.
    Requirements (figure them out from the code):
    """
    lines = content.strip().split('\n')
    
    # Must have exactly 5 lines
    if len(lines) != 5:
        return False
    
    # First line must be a palindrome
    if lines[0] != lines[0][::-1]:
        return False
    
    # Second line must be the MD5 of the first line (without newline)
    import hashlib
    expected_hash = hashlib.md5(lines[0].encode()).hexdigest()
    if lines[1] != expected_hash:
        return False
    
    # Third line must be an integer that's prime
    try:
        num = int(lines[2])
        if num < 2 or any(num % i == 0 for i in range(2, int(num**0.5) + 1)):
            return False
    except:
        return False
    
    # Fourth line must be the third line squared, in hex, uppercase
    expected_hex = hex(num * num)[2:].upper()
    if lines[3] != expected_hex:
        return False
    
    # Fifth line must be "STAGE2_COMPLETE"
    if lines[4] != "STAGE2_COMPLETE":
        return False
    
    return True

# ============================================================================
# STAGE 3: THE RECURSIVE DEPENDENCY HELL
# You need to call a function that calls a function that calls a function...
# But there's a circular import. Or is there?
# ============================================================================
def stage_3():
    print("\n[STAGE 3] Recursive Dependency Resolution...")
    
    try:
        from stage3_module import compute_final_value
        result = compute_final_value(42)
        
        # The expected value is not obvious
        # It's: ((42 * 2) + 7) * 3 - 10 = 263
        # But the modules might have bugs...
        if result != 263:
            print(f"[STAGE 3 FAILED] compute_final_value(42) = {result}, expected 263")
            print("HINT: Trace through all the module calls. One of them has a bug.")
            return False
        
        print("[STAGE 3 PASSED]")
        return True
        
    except ImportError as e:
        print(f"[STAGE 3 FAILED] Import error: {e}")
        print("HINT: You need to create stage3_module.py (and maybe others)")
        return False
    except RecursionError:
        print("[STAGE 3 FAILED] RecursionError - circular dependency detected")
        print("HINT: The imports form a cycle. Can you break it?")
        return False
    except Exception as e:
        print(f"[STAGE 3 FAILED] Unexpected error: {e}")
        return False

# ============================================================================
# STAGE 4: THE ASYNC TRAP
# Looks like it needs async. But does it really?
# ============================================================================
def stage_4():
    print("\n[STAGE 4] Async/Sync Bridge...")
    
    import asyncio
    
    async def async_computation(x):
        await asyncio.sleep(0.01)  # Simulate IO
        return x * 2
    
    def sync_wrapper(x):
        # This is the "obvious" solution but it won't work in all contexts
        # because there might already be a running event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Can't use run_until_complete in running loop
                # Need a different approach
                raise RuntimeError("Event loop is already running")
            return loop.run_until_complete(async_computation(x))
        except RuntimeError as e:
            if "already running" in str(e).lower():
                # The AI needs to figure out how to handle this
                # Options: nest_asyncio, asyncio.run_coroutine_threadsafe, etc.
                print(f"[STAGE 4 HINT] {e}")
                print("HINT: You're in a running event loop. Use nest_asyncio or threads.")
                raise
            raise
    
    try:
        result = sync_wrapper(50)
        if result != 100:
            print(f"[STAGE 4 FAILED] Expected 100, got {result}")
            return False
        print("[STAGE 4 PASSED]")
        return True
    except Exception as e:
        print(f"[STAGE 4 FAILED] {e}")
        return False

# ============================================================================
# STAGE 5: THE ENCODING NIGHTMARE
# A file that looks like UTF-8 but isn't. Or is it?
# ============================================================================
def stage_5():
    print("\n[STAGE 5] Encoding Detection...")
    
    encoded_file = os.path.join(os.path.dirname(__file__), "stage5_mystery.bin")
    
    if not os.path.exists(encoded_file):
        print(f"[STAGE 5 FAILED] Encoded file missing: {encoded_file}")
        print("HINT: Create stage5_mystery.bin with the secret message")
        print("      The message is 'STAGE5_VICTORY' but encoded in a specific way")
        print("      Try: base64 of rot13 of the message, as bytes")
        return False
    
    with open(encoded_file, 'rb') as f:
        raw = f.read()
    
    # Decode: it's base64 of rot13
    import base64
    import codecs
    
    try:
        decoded_b64 = base64.b64decode(raw).decode('utf-8')
        decoded_rot13 = codecs.decode(decoded_b64, 'rot_13')
        
        if decoded_rot13 == "STAGE5_VICTORY":
            print("[STAGE 5 PASSED]")
            return True
        else:
            print(f"[STAGE 5 FAILED] Decoded to '{decoded_rot13}', expected 'STAGE5_VICTORY'")
            return False
    except Exception as e:
        print(f"[STAGE 5 FAILED] Decoding error: {e}")
        print("HINT: base64(rot13('STAGE5_VICTORY')) as bytes")
        return False

# ============================================================================
# STAGE 6: THE RACE CONDITION
# This test is flaky. Sometimes it passes, sometimes it doesn't.
# The AI needs to fix the race condition.
# ============================================================================
def stage_6():
    print("\n[STAGE 6] Race Condition Elimination...")
    
    import threading
    import time
    
    class Counter:
        def __init__(self):
            self.value = 0
            # BUG: No lock - race condition
            # AI needs to add: self.lock = threading.Lock()
        
        def increment(self):
            # BUG: Not thread-safe
            # AI needs to use lock here
            current = self.value
            time.sleep(0.0001)  # Amplify race condition
            self.value = current + 1
    
    counter = Counter()
    threads = []
    
    for _ in range(100):
        t = threading.Thread(target=counter.increment)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    if counter.value != 100:
        print(f"[STAGE 6 FAILED] Counter = {counter.value}, expected 100")
        print("HINT: Race condition. Add proper locking to the Counter class.")
        print("      But you can't just edit this file - it's the TEST file.")
        print("      Create a fixed version as stage6_counter.py and import it.")
        return False
    
    print("[STAGE 6 PASSED]")
    return True

# ============================================================================
# STAGE 7: THE FINAL BOSS - SELF-MODIFYING CHALLENGE
# The AI must create a file that, when imported, modifies THIS file
# to make stage_7 return True. But there's a checksum...
# ============================================================================
def stage_7():
    print("\n[STAGE 7] Self-Modification Challenge...")
    
    # The AI must create stage7_solver.py which:
    # 1. Reads this file
    # 2. Computes what modification is needed
    # 3. Returns the magic value
    
    try:
        from stage7_solver import get_magic_value
        magic = get_magic_value()
        
        # The magic value is computed from this file's contents
        with open(__file__, 'r') as f:
            content = f.read()
        
        import hashlib
        file_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Magic value must be first 8 chars of sha256 of this file
        expected = file_hash[:8]
        
        if magic != expected:
            print(f"[STAGE 7 FAILED] Magic value '{magic}' != expected '{expected}'")
            print("HINT: Read this file, compute its SHA256, return first 8 hex chars")
            return False
        
        print("[STAGE 7 PASSED]")
        return True
        
    except ImportError:
        print("[STAGE 7 FAILED] stage7_solver.py not found")
        print("HINT: Create stage7_solver.py with get_magic_value() function")
        return False
    except Exception as e:
        print(f"[STAGE 7 FAILED] {e}")
        return False


# ============================================================================
# MAIN RUNNER - Cascading execution
# ============================================================================
def main():
    print("=" * 78)
    print("CASCADING NIGHTMARE CHALLENGE - BEGIN")
    print("=" * 78)
    print("\nObjective: Make ALL stages pass. Each fix may break something else.")
    print("Watch for: Red herrings, circular deps, race conditions, encoding traps")
    print("")
    
    stages = [
        ("Stage 1: Environment", stage_1),
        ("Stage 2: Data Integrity", stage_2),
        ("Stage 3: Dependencies", stage_3),
        ("Stage 4: Async Bridge", stage_4),
        ("Stage 5: Encoding", stage_5),
        ("Stage 6: Race Condition", stage_6),
        ("Stage 7: Final Boss", stage_7),
    ]
    
    passed = 0
    for name, stage_func in stages:
        try:
            if stage_func():
                passed += 1
            else:
                print(f"\n>>> STOPPED AT: {name}")
                print(f">>> Progress: {passed}/7 stages complete")
                print("\nFix the issue and run again.")
                sys.exit(1)
        except Exception as e:
            print(f"\n[CRASHED] {name}: {e}")
            print(f">>> Progress: {passed}/7 stages complete")
            sys.exit(1)
    
    print("\n" + "=" * 78)
    print("🎉 ALL 7 STAGES COMPLETE 🎉")
    print("=" * 78)
    print("\nCongratulations! You've conquered the Cascading Nightmare.")
    print("This proves the AI can:")
    print("  ✓ Create missing files from context")
    print("  ✓ Debug multi-layer dependencies")
    print("  ✓ Handle async/sync bridging")
    print("  ✓ Solve encoding puzzles")
    print("  ✓ Fix race conditions")
    print("  ✓ Perform file introspection")


if __name__ == "__main__":
    main()
