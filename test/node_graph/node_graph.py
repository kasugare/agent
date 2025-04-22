#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Graph:
    def __init__(self):
        self._graph = {}
        self._nodes_meta = {}

    def add_edge(self, src, dest):
        if src not in self._graph:
            self._graph[src] = []
        if dest not in self._graph:
            self._graph[dest] = []
        self._graph[src].append(dest)



    def print_graph(self):
        for vertex in self._graph:
            print(f"{vertex} -> {', '.join(self._graph[vertex])}")

    def dfs(self, start, visited=None):
        if visited is None:
            visited = set()
        visited.add(start)
        print(start, end=' ')
        for neighbor in self._graph[start]:
            if neighbor not in visited:
                self.dfs(neighbor, visited)

    def bfs(self, start):
        visited = set()
        queue = []
        visited.add(start)
        queue.append(start)
        while queue:
            vertex = queue.pop(0)
            print(vertex, end=' ')
            for neighbor in self._graph[vertex]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

    def find_all_paths(self, start, end, path=None):
        """시작 노드에서 끝 노드까지의 모든 가능한 경로를 찾는 함수"""
        if path is None:
            path = []
        path = path + [start]

        if start == end:
            return [path]

        if start not in self._graph:
            return []

        paths = []
        for neighbor in self._graph[start]:
            if neighbor not in path:  # 사이클 방지
                new_paths = self.find_all_paths(neighbor, end, path)
                paths.extend(new_paths)
        return paths

    def find_shortest_path(self, start, end, path=None):
        """시작 노드에서 끝 노드까지의 최단 경로를 찾는 함수"""
        if path is None:
            path = []
        path = path + [start]

        if start == end:
            return path

        if start not in self._graph:
            return None

        shortest = None
        for neighbor in self._graph[start]:
            if neighbor not in path:  # 사이클 방지
                new_path = self.find_shortest_path(neighbor, end, path)
                if new_path:
                    if not shortest or len(new_path) < len(shortest):
                        shortest = new_path
        return shortest

    def get_next_nodes(self, node):
        """특정 노드에서 갈 수 있는 다음 노드들의 리스트를 반환하는 함수"""
        if node in self._graph:
            return self._graph[node]
            return []

class GraphMaker:
    def __init__(self):
        self._node_graph = Graph()
        self._set_graph()
    
    def _set_graph(self):
        self._node_graph.add_edge('A', 'B')
        self._node_graph.add_edge('A', 'F')
        self._node_graph.add_edge('B', 'C')
        self._node_graph.add_edge('B', 'D')
        self._node_graph.add_edge('B', 'E')
        self._node_graph.add_edge('F', 'G')
        self._node_graph.add_edge('F', 'H')
        self._node_graph.add_edge('C', 'I')
        self._node_graph.add_edge('D', 'I')
        self._node_graph.add_edge('E', 'I')
        self._node_graph.add_edge('G', 'I')
        self._node_graph.add_edge('I', 'J')
        self._node_graph.add_edge('H', 'J')
        self._node_graph.add_edge('J', 'Z')

    def _get_grape(self):
        print("그래프 구조:")
        self._node_graph.print_graph()

    def _get_all_path(self):
        print("\nA에서 J까지의 모든 경로:")
        all_paths = self._node_graph.find_all_paths('A', 'J')
        for path in all_paths:
            print(" -> ".join(path))

    def _find_shortest_path(self):
        print("\nA에서 J까지의 최단 경로:")
        shortest_path = self._node_graph.find_shortest_path('A', 'J')
        if shortest_path:
            print(" -> ".join(shortest_path))

    def _get_next_nodes(self, node):
        print("\n각 노드에서 갈 수 있는 다음 노드들:")
        next_nodes = self._node_graph.get_next_nodes(node)
        print(f"{node}의 다음 노드들: {next_nodes}")

    def do_process(self):
        self._get_grape()
        self._get_all_path()
        # self._find_shortest_path()
        self._get_next_nodes("A")


if __name__ == "__main__":
    graph = GraphMaker()
    graph.do_process()



