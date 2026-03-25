#!/usr/bin/env python3
"""
LEVEL 7: IMPLEMENT COMPLETE ALGORITHM - DIJKSTRA'S SHORTEST PATH
================================================================
Difficulty: Hard
Time Limit: 20 minutes

TASK:
Implement Dijkstra's algorithm in 'implement_dijkstra.py'.
The algorithm must find the shortest paths from a source node to all other nodes
in a weighted directed graph.

REQUIREMENTS:
- Handle disconnected nodes (return infinity for unreachable)
- Handle graphs with cycles
- Return both distances and the actual paths
- Use a proper priority queue for efficiency
"""
import os
import sys

STUB_CODE = '''
import heapq
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

class Graph:
    """Weighted directed graph."""
    
    def __init__(self):
        # adjacency list: node -> [(neighbor, weight), ...]
        self.edges = defaultdict(list)
        self.nodes = set()
    
    def add_edge(self, from_node: str, to_node: str, weight: int):
        """Add a directed edge with weight."""
        self.edges[from_node].append((to_node, weight))
        self.nodes.add(from_node)
        self.nodes.add(to_node)
    
    def get_neighbors(self, node: str) -> List[Tuple[str, int]]:
        """Get neighbors and edge weights for a node."""
        return self.edges[node]


def dijkstra(graph: Graph, start: str) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """
    Implement Dijkstra's shortest path algorithm.
    
    Args:
        graph: A weighted directed graph
        start: The starting node
    
    Returns:
        A tuple of (distances, predecessors) where:
        - distances: dict mapping each node to its shortest distance from start
        - predecessors: dict mapping each node to its predecessor in shortest path
                       (None for start node and unreachable nodes)
    
    Notes:
        - Use float('inf') for unreachable nodes
        - Use a min-heap (heapq) for efficiency
    
    IMPLEMENT THIS FUNCTION.
    """
    # TODO: Implement Dijkstra's algorithm
    pass


def get_path(predecessors: Dict[str, Optional[str]], start: str, end: str) -> Optional[List[str]]:
    """
    Reconstruct the path from start to end using predecessors dict.
    
    Returns:
        List of nodes from start to end, or None if no path exists.
    
    IMPLEMENT THIS FUNCTION.
    """
    # TODO: Implement path reconstruction
    pass


# TESTS - Do not modify
def run_tests():
    # Test 1: Simple linear graph
    g1 = Graph()
    g1.add_edge('A', 'B', 1)
    g1.add_edge('B', 'C', 2)
    g1.add_edge('C', 'D', 3)
    
    dist, pred = dijkstra(g1, 'A')
    assert dist['A'] == 0, "Distance to self should be 0"
    assert dist['B'] == 1, "A->B distance wrong"
    assert dist['C'] == 3, "A->C distance wrong"
    assert dist['D'] == 6, "A->D distance wrong"
    
    path = get_path(pred, 'A', 'D')
    assert path == ['A', 'B', 'C', 'D'], f"Path wrong: {path}"
    
    # Test 2: Graph with multiple paths (should find shortest)
    g2 = Graph()
    g2.add_edge('A', 'B', 4)
    g2.add_edge('A', 'C', 2)
    g2.add_edge('B', 'D', 3)
    g2.add_edge('C', 'B', 1)  # Shorter path: A->C->B (cost 3) vs A->B (cost 4)
    g2.add_edge('C', 'D', 5)
    
    dist2, pred2 = dijkstra(g2, 'A')
    assert dist2['B'] == 3, f"Should find shorter path A->C->B: {dist2['B']}"
    assert dist2['D'] == 6, f"Shortest to D is A->C->B->D: {dist2['D']}"
    
    # Test 3: Unreachable node
    g3 = Graph()
    g3.add_edge('A', 'B', 1)
    g3.nodes.add('C')  # C has no incoming edges
    
    dist3, pred3 = dijkstra(g3, 'A')
    assert dist3['C'] == float('inf'), "Unreachable should be infinity"
    assert get_path(pred3, 'A', 'C') is None, "No path to unreachable"
    
    # Test 4: Graph with cycle
    g4 = Graph()
    g4.add_edge('A', 'B', 1)
    g4.add_edge('B', 'C', 2)
    g4.add_edge('C', 'A', 3)  # Cycle back
    g4.add_edge('B', 'D', 10)
    
    dist4, pred4 = dijkstra(g4, 'A')
    assert dist4['D'] == 11, "Should handle cycle correctly"
    
    # Test 5: Larger graph
    g5 = Graph()
    edges = [
        ('S', 'A', 7), ('S', 'B', 2), ('S', 'C', 3),
        ('A', 'D', 4), ('A', 'B', 3),
        ('B', 'D', 4), ('B', 'H', 1),
        ('C', 'L', 2),
        ('D', 'F', 5),
        ('H', 'F', 3), ('H', 'G', 2),
        ('F', 'G', 2),
        ('G', 'E', 2),
        ('E', 'K', 5),
        ('K', 'I', 4), ('K', 'J', 4),
        ('I', 'J', 6), ('I', 'L', 4),
        ('J', 'L', 4),
        ('L', 'J', 4),
    ]
    for src, dst, w in edges:
        g5.add_edge(src, dst, w)
    
    dist5, pred5 = dijkstra(g5, 'S')
    assert dist5['G'] == 7, f"S->B->H->G should be 7: {dist5['G']}"
    assert dist5['E'] == 9, f"S->B->H->G->E should be 9: {dist5['E']}"
    
    print("ALL TESTS PASSED!")
    return True

if __name__ == "__main__":
    run_tests()
'''

def setup():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(script_dir, "implement_dijkstra.py")
    
    if not os.path.exists(target):
        with open(target, 'w') as f:
            f.write(STUB_CODE)
        print(f"Created stub file: {target}")
        print("IMPLEMENT dijkstra() and get_path(), then run this script again.")
        return False
    return True

def verify():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(script_dir, "implement_dijkstra.py")
    
    if not os.path.exists(target):
        setup()
        return False
    
    import subprocess
    try:
        result = subprocess.run([sys.executable, target], capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        print("FAIL: Timeout - algorithm too slow or infinite loop")
        return False
    
    if result.returncode != 0:
        print(f"FAIL: Tests failed")
        print(f"STDERR: {result.stderr}")
        return False
    
    if "ALL TESTS PASSED!" not in result.stdout:
        print(f"FAIL: Tests did not pass")
        print(f"STDOUT: {result.stdout}")
        return False
    
    print("LEVEL 7 PASSED")
    return True

if __name__ == "__main__":
    if not setup():
        sys.exit(1)
    sys.exit(0 if verify() else 1)
