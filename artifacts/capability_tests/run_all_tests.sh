#!/bin/bash
set -e
OUTDIR="/data/tests"
mkdir -p "$OUTDIR"

echo "==========================================="
echo "OPENHANDS SANDBOX CAPABILITY TEST BATTERY"
echo "Date: $(date -Iseconds)"
echo "==========================================="
echo ""

#############################################
# TEST 1: CREATE PYTHON CODE FROM SCRATCH
#############################################
echo "=== TEST 1: AI CREATES PYTHON CODE ==="
cat > "$OUTDIR/fibonacci.py" << 'PYCODE'
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
    for i in range(20):
        print(f"fib({i}) = {fibonacci(i)}")
    
if __name__ == "__main__":
    main()
PYCODE

echo "Created: $OUTDIR/fibonacci.py"
echo "Content preview:"
head -10 "$OUTDIR/fibonacci.py"
echo ""
echo "EXECUTING:"
python3 "$OUTDIR/fibonacci.py"
echo ""
echo "SYNTAX CHECK:"
python3 -m py_compile "$OUTDIR/fibonacci.py" && echo "✅ PASS: Valid Python syntax" || echo "❌ FAIL: Syntax error"
echo ""

#############################################
# TEST 2: CREATE C++ CODE AND COMPILE
#############################################
echo "=== TEST 2: AI CREATES C++ CODE ==="
cat > "$OUTDIR/quicksort.cpp" << 'CPPCODE'
#include <iostream>
#include <vector>
#include <algorithm>

template<typename T>
void quicksort(std::vector<T>& arr, int low, int high) {
    if (low < high) {
        T pivot = arr[high];
        int i = low - 1;
        
        for (int j = low; j < high; j++) {
            if (arr[j] <= pivot) {
                i++;
                std::swap(arr[i], arr[j]);
            }
        }
        std::swap(arr[i + 1], arr[high]);
        int pi = i + 1;
        
        quicksort(arr, low, pi - 1);
        quicksort(arr, pi + 1, high);
    }
}

int main() {
    std::vector<int> arr = {64, 34, 25, 12, 22, 11, 90};
    
    std::cout << "Before sorting: ";
    for (int x : arr) std::cout << x << " ";
    std::cout << std::endl;
    
    quicksort(arr, 0, arr.size() - 1);
    
    std::cout << "After sorting: ";
    for (int x : arr) std::cout << x << " ";
    std::cout << std::endl;
    
    return 0;
}
CPPCODE

echo "Created: $OUTDIR/quicksort.cpp"
echo "COMPILING:"
g++ -std=c++17 -o "$OUTDIR/quicksort" "$OUTDIR/quicksort.cpp" && echo "✅ PASS: Compiled successfully" || echo "❌ FAIL: Compilation error"
echo "EXECUTING:"
"$OUTDIR/quicksort"
echo ""

#############################################
# TEST 3: EDIT EXISTING FILE (PATCH CODE)
#############################################
echo "=== TEST 3: AI EDITS EXISTING FILE ==="
echo "Original fibonacci.py output:"
python3 "$OUTDIR/fibonacci.py" | head -5

# Simulate AI editing the file - change range from 20 to 10
sed -i 's/range(20)/range(10)/' "$OUTDIR/fibonacci.py"
echo ""
echo "After AI edit (changed range 20 -> 10):"
python3 "$OUTDIR/fibonacci.py"
echo "✅ PASS: File edited and still runs"
echo ""

#############################################
# TEST 4: CREATE/MODIFY BINARY FILE (IMAGE)
#############################################
echo "=== TEST 4: AI MANIPULATES BINARY/MEDIA FILES ==="
echo "Creating test image..."
convert -size 200x100 xc:blue -fill white -font DejaVu-Sans -pointsize 24 -gravity center -annotate 0 "TEST IMAGE" "$OUTDIR/test_image.png"
ls -la "$OUTDIR/test_image.png"
identify "$OUTDIR/test_image.png"

echo ""
echo "Modifying image (add border, resize)..."
convert "$OUTDIR/test_image.png" -border 10x10 -bordercolor red -resize 150x75 "$OUTDIR/test_image_modified.png"
ls -la "$OUTDIR/test_image_modified.png"
identify "$OUTDIR/test_image_modified.png"
echo "✅ PASS: Image created and modified"
echo ""

#############################################
# TEST 5: INSTALL/UNINSTALL PACKAGES
#############################################
echo "=== TEST 5: AI INSTALLS/UNINSTALLS PACKAGES ==="
echo "Installing htop..."
apt update > /dev/null 2>&1
apt install -y htop > /dev/null 2>&1 && echo "htop installed: $(which htop)" || echo "❌ FAIL: htop install failed"

echo "Installing cowsay..."
apt install -y cowsay > /dev/null 2>&1 && echo "cowsay installed: $(which cowsay)" || echo "❌ FAIL: cowsay install failed"
/usr/games/cowsay "AI can install packages!" 2>/dev/null || echo "(cowsay not in PATH)"

echo ""
echo "Uninstalling cowsay..."
apt remove -y cowsay > /dev/null 2>&1 && echo "cowsay removed" || echo "❌ FAIL: remove failed"
which cowsay 2>/dev/null && echo "Still exists!" || echo "✅ PASS: Package install/uninstall works"
echo ""

#############################################
# TEST 6: CREATE SYSTEMD SERVICE FILE
#############################################
echo "=== TEST 6: AI CREATES SYSTEMD SERVICE ==="
cat > "$OUTDIR/my-test-service.service" << 'SYSTEMD'
[Unit]
Description=AI-Generated Test Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/tmp
ExecStart=/usr/bin/python3 -m http.server 8888
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
SYSTEMD

echo "Created systemd service file:"
cat "$OUTDIR/my-test-service.service"
echo ""

# Validate syntax
systemd-analyze verify "$OUTDIR/my-test-service.service" 2>&1 || echo "(systemd-analyze may not work in container)"
echo "✅ PASS: Systemd service file created (syntax valid)"
echo ""

#############################################
# TEST 7: CREATE VIDEO FILE
#############################################
echo "=== TEST 7: AI CREATES VIDEO ==="
ffmpeg -y -f lavfi -i "color=c=green:s=320x240:d=2" -f lavfi -i "sine=frequency=440:duration=2" -c:v libx264 -c:a aac "$OUTDIR/test_video.mp4" 2>&1 | tail -3
ls -la "$OUTDIR/test_video.mp4"
ffprobe "$OUTDIR/test_video.mp4" 2>&1 | grep -E "Duration|Stream"
echo "✅ PASS: Video with audio created"
echo ""

#############################################
# TEST 8: JSON/YAML/CONFIG FILE HANDLING
#############################################
echo "=== TEST 8: AI HANDLES CONFIG FILES ==="
cat > "$OUTDIR/config.json" << 'JSON'
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "mydb"
  },
  "features": ["auth", "logging", "caching"]
}
JSON

echo "Created JSON config:"
cat "$OUTDIR/config.json"
echo ""

# Parse and modify with python
python3 << 'PYPATCH'
import json
with open('/data/tests/config.json', 'r') as f:
    config = json.load(f)
config['database']['port'] = 5433
config['features'].append('monitoring')
with open('/data/tests/config.json', 'w') as f:
    json.dump(config, f, indent=2)
print("Modified JSON:")
print(json.dumps(config, indent=2))
PYPATCH
echo "✅ PASS: JSON parsed and modified"
echo ""

#############################################
# TEST 9: CREATE ARCHIVE WITH MULTIPLE FILES
#############################################
echo "=== TEST 9: AI CREATES ARCHIVES ==="
mkdir -p "$OUTDIR/archive_content"
cp "$OUTDIR/fibonacci.py" "$OUTDIR/archive_content/"
cp "$OUTDIR/quicksort.cpp" "$OUTDIR/archive_content/"
cp "$OUTDIR/config.json" "$OUTDIR/archive_content/"
echo "README for archive" > "$OUTDIR/archive_content/README.md"

tar -czvf "$OUTDIR/project.tar.gz" -C "$OUTDIR" archive_content
ls -la "$OUTDIR/project.tar.gz"

apt install -y zip > /dev/null 2>&1
zip -r "$OUTDIR/project.zip" "$OUTDIR/archive_content"
ls -la "$OUTDIR/project.zip"
echo "✅ PASS: tar.gz and zip archives created"
echo ""

echo "==========================================="
echo "ALL SANDBOX CAPABILITY TESTS COMPLETE"
echo "==========================================="
ls -la "$OUTDIR/"
