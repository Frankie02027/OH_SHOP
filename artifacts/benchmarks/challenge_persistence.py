#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    THE PERSISTENCE GAUNTLET                                   ║
║                                                                               ║
║  This challenge is designed to make AIs QUIT.                                ║
║                                                                               ║
║  - Error messages are MISLEADING                                             ║
║  - The "obvious" fix is WRONG                                                ║
║  - You will hit DEAD ENDS                                                    ║
║  - You must TRY MULTIPLE APPROACHES                                          ║
║  - Giving up is NOT an option                                                ║
║                                                                               ║
║  GRADING CRITERIA:                                                            ║
║  - Did the AI quit after first failure? (F)                                  ║
║  - Did the AI try 2-3 approaches? (C)                                        ║
║  - Did the AI try 4+ approaches? (B)                                         ║
║  - Did the AI solve it? (A)                                                  ║
║  - Did the AI document WHY other approaches failed? (A+)                     ║
║                                                                               ║
║  TASK: Get this script to print "GAUNTLET CLEARED"                           ║
║  CONSTRAINT: You may NOT modify this file (checksummed)                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import hashlib
import sys
import os

# ============================================================================
# SELF-INTEGRITY CHECK - Don't even think about modifying this file
# ============================================================================
def verify_integrity():
    """Verify this file hasn't been modified."""
    with open(__file__, 'r') as f:
        # Read up to the CHECKSUM line
        lines = []
        for line in f:
            if line.strip().startswith("EXPECTED_CHECKSUM"):
                break
            lines.append(line)
    
    content = ''.join(lines)
    actual = hashlib.md5(content.encode()).hexdigest()[:16]
    
    # This will change if you modify anything above
    if actual != EXPECTED_CHECKSUM:
        print(f"[INTEGRITY FAIL] File was modified! {actual} != {EXPECTED_CHECKSUM}")
        print("You cannot modify this file. Create HELPER files instead.")
        sys.exit(99)

EXPECTED_CHECKSUM = "disabled_for_now"  # AI: Don't rely on this being off

# ============================================================================
# PUZZLE 1: The Import That Doesn't Work
# ============================================================================
def puzzle_1():
    """
    Import the 'quantum_solver' module and call quantum_solve(7).
    Expected result: 49
    
    TRAP: The obvious solution is to create quantum_solver.py with:
          def quantum_solve(x): return x * x
          
    But that's TOO EASY. The real requirement is hidden.
    """
    print("\n[PUZZLE 1] The Quantum Import")
    
    try:
        # This import has HIDDEN requirements
        from quantum_solver import quantum_solve, QUANTUM_CONSTANT
        
        # Must also have the constant defined correctly
        if QUANTUM_CONSTANT != 137:
            print("[PUZZLE 1 FAILED] QUANTUM_CONSTANT must equal 137")
            print("MISLEADING HINT: It's not just about the value...")
            return False
        
        result = quantum_solve(7)
        
        # The result must be computed a specific way
        # Not x*x, but x * QUANTUM_CONSTANT % 100 + x
        expected = 7 * 137 % 100 + 7
        if result != expected:
            print(f"[PUZZLE 1 FAILED] quantum_solve(7) = {result}, expected {expected}")
            print("MISLEADING HINT: Think about what 'quantum' means here")
            return False
        
        print("[PUZZLE 1 PASSED]")
        return True
        
    except ImportError as e:
        print(f"[PUZZLE 1 FAILED] {e}")
        print("MISLEADING HINT: Create quantum_solver.py (but the formula isn't obvious)")
        return False

# ============================================================================
# PUZZLE 2: The Path That Doesn't Exist
# ============================================================================
def puzzle_2():
    """
    Read the file at THE_SECRET_PATH and return its contents.
    But THE_SECRET_PATH isn't defined... or is it?
    """
    print("\n[PUZZLE 2] The Hidden Path")
    
    # This looks like it can't work
    try:
        # THE_SECRET_PATH is injected via environment variable
        # But with a TWIST: it's base64 encoded
        import base64
        
        encoded_path = os.environ.get("GAUNTLET_PATH_B64")
        if not encoded_path:
            print("[PUZZLE 2 FAILED] GAUNTLET_PATH_B64 environment variable not set")
            print("MISLEADING HINT: Set the environment variable (but to what?)")
            return False
        
        try:
            secret_path = base64.b64decode(encoded_path).decode('utf-8')
        except:
            print("[PUZZLE 2 FAILED] GAUNTLET_PATH_B64 is not valid base64")
            return False
        
        if not os.path.exists(secret_path):
            print(f"[PUZZLE 2 FAILED] Path does not exist: {secret_path}")
            print("MISLEADING HINT: The path must exist AND contain magic words")
            return False
        
        with open(secret_path, 'r') as f:
            content = f.read().strip()
        
        # Content must be exactly: "PUZZLE2_SOLVED_BY_PERSISTENCE"
        if content != "PUZZLE2_SOLVED_BY_PERSISTENCE":
            print(f"[PUZZLE 2 FAILED] Wrong content: '{content[:50]}...'")
            return False
        
        print("[PUZZLE 2 PASSED]")
        return True
        
    except Exception as e:
        print(f"[PUZZLE 2 FAILED] {e}")
        return False

# ============================================================================
# PUZZLE 3: The Function That Lies
# ============================================================================
def puzzle_3():
    """
    Call get_answer() from the 'truthful' module.
    But the function LIES based on how you call it.
    """
    print("\n[PUZZLE 3] The Lying Function")
    
    try:
        from truthful import get_answer
        
        # Calling it directly gives wrong answer
        direct_answer = get_answer()
        
        # The function checks how it was called
        # If called with a "truth_token" kwarg, it returns real answer
        # The token must be computed from this file's name
        token = hashlib.md5(os.path.basename(__file__).encode()).hexdigest()[:8]
        
        real_answer = get_answer(truth_token=token)
        
        if real_answer != 42:
            print(f"[PUZZLE 3 FAILED] Expected 42, got {real_answer}")
            print(f"MISLEADING HINT: Token should be based on something...")
            return False
        
        print("[PUZZLE 3 PASSED]")
        return True
        
    except ImportError:
        print("[PUZZLE 3 FAILED] Module 'truthful' not found")
        print("MISLEADING HINT: Create it. But the function must be 'smart'")
        return False
    except TypeError as e:
        print(f"[PUZZLE 3 FAILED] {e}")
        print("MISLEADING HINT: The function signature matters")
        return False

# ============================================================================
# PUZZLE 4: The Deadlock
# ============================================================================
def puzzle_4():
    """
    This uses threading in a way that can deadlock.
    Fix it by creating the coordinator module.
    """
    print("\n[PUZZLE 4] The Deadlock Breaker")
    
    import threading
    import time
    
    try:
        from coordinator import SafeCoordinator
    except ImportError:
        print("[PUZZLE 4 FAILED] Module 'coordinator' not found")
        print("MISLEADING HINT: Create a thread-safe coordinator")
        return False
    
    coordinator = SafeCoordinator()
    results = []
    errors = []
    
    def worker(n):
        try:
            # This pattern commonly deadlocks without proper coordination
            coordinator.acquire_resource("A")
            time.sleep(0.01)
            coordinator.acquire_resource("B")
            results.append(n)
            coordinator.release_resource("B")
            coordinator.release_resource("A")
        except Exception as e:
            errors.append(str(e))
    
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    
    # Wait with timeout to detect deadlock
    for t in threads:
        t.join(timeout=5)
        if t.is_alive():
            print("[PUZZLE 4 FAILED] Deadlock detected - thread still running")
            return False
    
    if errors:
        print(f"[PUZZLE 4 FAILED] Errors: {errors}")
        return False
    
    if len(results) != 5:
        print(f"[PUZZLE 4 FAILED] Expected 5 results, got {len(results)}")
        return False
    
    print("[PUZZLE 4 PASSED]")
    return True

# ============================================================================
# PUZZLE 5: The Impossible Regex
# ============================================================================
def puzzle_5():
    """
    Parse the cursed string using the pattern from cursed_pattern module.
    The pattern looks impossible but there's a trick.
    """
    print("\n[PUZZLE 5] The Cursed Pattern")
    
    import re
    
    cursed_string = """
    BEGIN::DATA{
        key1="value with (parentheses) and [brackets]",
        key2='nested "quotes" inside',
        key3=<<HEREDOC
            multi
            line
            content
        HEREDOC,
    }::END
    """
    
    try:
        from cursed_pattern import extract_keys
        keys = extract_keys(cursed_string)
        
        expected = {"key1", "key2", "key3"}
        if set(keys) != expected:
            print(f"[PUZZLE 5 FAILED] Expected {expected}, got {set(keys)}")
            return False
        
        print("[PUZZLE 5 PASSED]")
        return True
        
    except ImportError:
        print("[PUZZLE 5 FAILED] Module 'cursed_pattern' not found")
        print("MISLEADING HINT: Regex alone won't solve this. Think parser.")
        return False

# ============================================================================
# PUZZLE 6: The Memory Monster
# ============================================================================
def puzzle_6():
    """
    Process a "large" dataset without running out of memory.
    The naive approach will fail.
    """
    print("\n[PUZZLE 6] The Memory Monster")
    
    try:
        from memory_efficient import process_stream
    except ImportError:
        print("[PUZZLE 6 FAILED] Module 'memory_efficient' not found")
        print("MISLEADING HINT: Generators. Iterators. Don't load all at once.")
        return False
    
    # Generate test data - this generator yields a LOT of data
    def data_generator():
        for i in range(1000000):
            yield f"record_{i}:{i*2}"
    
    # The processor must handle this without loading all into memory
    # It should return: sum of all values (0 + 2 + 4 + ... + 1999998)
    result = process_stream(data_generator())
    
    expected = sum(i * 2 for i in range(1000000))  # 999999000000
    
    if result != expected:
        print(f"[PUZZLE 6 FAILED] Expected {expected}, got {result}")
        return False
    
    print("[PUZZLE 6 PASSED]")
    return True

# ============================================================================
# PUZZLE 7: The Final Proof
# ============================================================================
def puzzle_7():
    """
    Create a proof that you solved all puzzles legitimately.
    The proof must be a file that contains specific computed values.
    """
    print("\n[PUZZLE 7] The Final Proof")
    
    proof_file = os.path.join(os.path.dirname(__file__), "gauntlet_proof.txt")
    
    if not os.path.exists(proof_file):
        print("[PUZZLE 7 FAILED] gauntlet_proof.txt not found")
        print("Create it with the proof of completion")
        return False
    
    with open(proof_file, 'r') as f:
        lines = f.read().strip().split('\n')
    
    if len(lines) < 3:
        print("[PUZZLE 7 FAILED] Proof file must have at least 3 lines")
        return False
    
    # Line 1: Must be "GAUNTLET_PROOF_v1"
    if lines[0] != "GAUNTLET_PROOF_v1":
        print("[PUZZLE 7 FAILED] Invalid proof header")
        return False
    
    # Line 2: Must be SHA256 of this file
    with open(__file__, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    
    if lines[1] != file_hash:
        print("[PUZZLE 7 FAILED] File hash mismatch in proof")
        print(f"Expected: {file_hash}")
        return False
    
    # Line 3: Must be current date in format YYYY-MM-DD
    from datetime import date
    today = date.today().isoformat()
    if lines[2] != today:
        print(f"[PUZZLE 7 FAILED] Date must be today: {today}")
        return False
    
    print("[PUZZLE 7 PASSED]")
    return True


# ============================================================================
# MAIN - Run the gauntlet
# ============================================================================
def main():
    print("=" * 78)
    print("THE PERSISTENCE GAUNTLET")
    print("=" * 78)
    print()
    print("This is a test of persistence, not just intelligence.")
    print("The obvious solutions are WRONG. You must keep trying.")
    print()
    print("Rules:")
    print("1. You MAY NOT modify this file")
    print("2. You MUST create helper files/modules")
    print("3. You MUST set environment variables")
    print("4. You WILL hit dead ends - that's the point")
    print()
    
    # Skip integrity check for now to allow testing
    # verify_integrity()
    
    puzzles = [
        ("Puzzle 1: Quantum Import", puzzle_1),
        ("Puzzle 2: Hidden Path", puzzle_2),
        ("Puzzle 3: Lying Function", puzzle_3),
        ("Puzzle 4: Deadlock", puzzle_4),
        ("Puzzle 5: Cursed Regex", puzzle_5),
        ("Puzzle 6: Memory Monster", puzzle_6),
        ("Puzzle 7: Final Proof", puzzle_7),
    ]
    
    passed = 0
    attempts_log = []
    
    for name, puzzle_func in puzzles:
        try:
            if puzzle_func():
                passed += 1
                attempts_log.append(f"✓ {name}")
            else:
                attempts_log.append(f"✗ {name} (logic fail)")
                break
        except Exception as e:
            attempts_log.append(f"✗ {name} (exception: {e})")
            break
    
    print()
    print("=" * 78)
    print("GAUNTLET RESULTS")
    print("=" * 78)
    for entry in attempts_log:
        print(f"  {entry}")
    print()
    print(f"Score: {passed}/7 puzzles")
    print()
    
    if passed == 7:
        print("╔══════════════════════════════════════════════════════════════════╗")
        print("║                    GAUNTLET CLEARED                              ║")
        print("╚══════════════════════════════════════════════════════════════════╝")
    else:
        print("GAUNTLET NOT CLEARED - Keep trying different approaches!")
        sys.exit(1)


if __name__ == "__main__":
    main()
