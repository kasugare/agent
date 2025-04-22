#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Graph:
    def __init__(self, logger=None):
        self._graph = {}

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
            self.l = []
            return self.l

    def get_grape(self):
        return self._graph

    def find_start_nodes(self):
        """시작 노드들을 찾는 함수
        시작 노드 = 들어오는 간선이 없는 노드
        """
        # 모든 노드들의 집합
        all_nodes = set(self._graph.keys())

        # 다른 노드로부터 도달 가능한 노드들의 집합
        reachable_nodes = set()
        for node in self._graph:
            reachable_nodes.update(self._graph[node])

        # 도달 가능한 노드가 아닌 노드들이 시작 노드
        start_nodes = all_nodes - reachable_nodes
        return sorted(list(start_nodes))  # 정렬된 리스트로 반환

    def find_start_nodes_with_details(self):
        """시작 노드들을 찾고 각 노드의 진출 차수(outdegree)도 함께 반환"""
        start_nodes = self.find_start_nodes()
        result = {}

        for node in start_nodes:
            result[node] = {
                'outdegree': len(self._graph[node]),  # 진출 차수
                'next_nodes': self._graph[node]  # 다음 노드들
            }

        return result

    def verify_start_node(self, node):
        """특정 노드가 시작 노드인지 확인"""
        if node not in self._graph:
            return False, "노드가 그래프에 존재하지 않습니다"

        for source in self._graph:
            if node in self._graph[source] and source != node:  # 자기 자신으로의 간선은 제외
                return False, f"노드 {node}는 노드 {source}로부터 들어오는 간선이 있습니다"

        return True, f"노드 {node}는 시작 노드입니다"


class GraphGenerator(Graph):
    def __init__(self, logger):
        super().__init__(logger)

    def set_nodes_meta_to_graph(self, nodes_meta):
        for node_id, next_nodes in nodes_meta.items():
            for next_node_id in next_nodes:
                self.add_edge(node_id, next_node_id)
        return self.get_grape()




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



