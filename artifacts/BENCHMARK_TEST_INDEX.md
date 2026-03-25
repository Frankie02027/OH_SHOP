# AI Model Benchmark Test Index

> Created: 2026-03-22  
> Purpose: REAL downloadable tests for grading AI coding agents

---

## 1. CODE GENERATION BENCHMARKS

### A. HumanEval (OpenAI)
- **Source**: https://github.com/openai/human-eval
- **What**: 164 hand-written Python programming problems
- **Format**: JSONL with function signatures + docstrings + unit tests
- **File**: `HumanEval.jsonl.gz`
- **Status**: [ ] TO DOWNLOAD

### B. MBPP (Google)
- **Source**: https://github.com/google-research/google-research/tree/master/mbpp
- **What**: 974 Python programming problems (Mostly Basic Python Problems)
- **Format**: JSONL with task descriptions + code solutions + tests
- **File**: `mbpp.jsonl`
- **Status**: [ ] TO DOWNLOAD

### C. HumanEval+ / MBPP+ (BigCode)
- **Source**: https://github.com/bigcode-project/bigcode-evaluation-harness
- **What**: Extended versions with more test cases
- **Status**: [ ] TO DOWNLOAD

---

## 2. SOFTWARE ENGINEERING BENCHMARKS

### D. SWE-bench
- **Source**: https://github.com/princeton-nlp/SWE-bench
- **What**: 2,294 real GitHub issues with patches
- **Format**: JSON with repo, issue, patch, test commands
- **Files**: `swe-bench.json`, individual repo tarballs
- **Status**: [ ] TO DOWNLOAD

### E. SWE-bench Lite
- **Source**: Same repo, filtered subset
- **What**: 300 issues (easier subset)
- **Status**: [ ] TO DOWNLOAD

---

## 3. MULTI-TASK / KNOWLEDGE BENCHMARKS

### F. MMLU (Massive Multitask Language Understanding)
- **Source**: https://github.com/hendrycks/test
- **What**: 57 subjects, 15,908 questions
- **Format**: CSV files per subject
- **Status**: [ ] TO DOWNLOAD

### G. ARC (AI2 Reasoning Challenge)
- **Source**: https://allenai.org/data/arc
- **What**: Grade-school science questions
- **Format**: JSONL
- **Status**: [ ] TO DOWNLOAD

---

## 4. VISION BENCHMARKS (Expected to FAIL - no vision model)

### H. Sample Test Images
- Random photos for "describe this image" tests
- Charts/graphs for data extraction
- Screenshots for UI understanding
- **Status**: [ ] TO DOWNLOAD

---

## 5. FILE HANDLING TESTS

### I. Archive Tests
- `.zip` files to extract
- `.tar.gz` files to extract  
- `.7z` files (if tools available)
- **Status**: [ ] TO CREATE/DOWNLOAD

### J. Data Processing Tests
- CSV files for pandas operations
- JSON files for transformation
- XML files for parsing
- **Status**: [ ] TO CREATE

---

## 6. DOWNLOAD PLAN

```
/home/dev/OH_SHOP/artifacts/benchmarks/
├── humaneval/
│   └── HumanEval.jsonl.gz
├── mbpp/
│   └── mbpp.jsonl
├── swe-bench/
│   └── swe-bench-lite.json
├── mmlu/
│   └── (csv files per subject)
├── images/
│   └── (test images)
└── archives/
    └── (zip/tar test files)
```

---

## 7. REAL URLs TO FETCH

| Benchmark | Direct Download URL |
|-----------|---------------------|
| HumanEval | https://github.com/openai/human-eval/raw/master/data/HumanEval.jsonl.gz |
| MBPP | https://raw.githubusercontent.com/google-research/google-research/master/mbpp/mbpp.jsonl |
| SWE-bench | https://raw.githubusercontent.com/princeton-nlp/SWE-bench/main/swebench/test.json |

---

## NEXT: ACTUALLY DOWNLOAD THESE FILES
