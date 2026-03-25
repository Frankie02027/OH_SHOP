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
