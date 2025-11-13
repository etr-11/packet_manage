# -*- coding: utf-8 -*-

import os
import sys
import argparse
from collections import deque

try:
    import toml
except ImportError:
    print("ERROR: Library 'toml' is not installed.")
    print("Install it with: pip install toml")
    sys.exit(1)


class ConfigError(Exception):
    pass


class ConfigFileNotFoundError(ConfigError):
    def __init__(self, config_path):
        super().__init__(f"Config file not found: {config_path}")


class CircularDependencyError(Exception):
    def __init__(self, package, path):
        super().__init__(f"Circular dependency: {' -> '.join(path + [package])}")


class DependencyAnalyzer:
    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        
        # Test data with packages A, B, C...
        self.test_dependencies = {
            "A": ["B", "C"],
            "B": ["D", "E"], 
            "C": ["F", "G"],
            "D": ["H"],
            "E": ["H", "I"],
            "F": [],
            "G": ["I"],
            "H": [],
            "I": []
        }
        
        # Data with circular dependencies
        self.cyclic_dependencies = {
            "X": ["Y"],
            "Y": ["Z"], 
            "Z": ["X"]  # Cycle: X->Y->Z->X
        }
    
    def get_complete_dependencies(self, package_name, use_cyclic=False):
        """BFS with recursion to get complete dependency graph"""
        graph = self.cyclic_dependencies if use_cyclic else self.test_dependencies
        
        def bfs_recursive(pkg, visited=None, path=None):
            if visited is None:
                visited = set()
            if path is None:
                path = []
            
            # Check for circular dependency
            if pkg in path:
                raise CircularDependencyError(pkg, path)
            
            if pkg in visited:
                return {}
            
            visited.add(pkg)
            current_path = path + [pkg]
            
            result = {pkg: []}
            if pkg in graph:
                for dep in graph[pkg]:
                    result[pkg].append(dep)
                    # Recursive BFS call
                    sub_deps = bfs_recursive(dep, visited, current_path)
                    result.update(sub_deps)
            
            return result
        
        try:
            return bfs_recursive(package_name)
        except CircularDependencyError as e:
            raise e
    
    def get_all_transitive_deps(self, package_name):
        """Get all transitive dependencies using BFS"""
        if package_name not in self.test_dependencies:
            return []
        
        visited = set()
        queue = deque([package_name])
        all_deps = set()
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            
            if current in self.test_dependencies:
                for dep in self.test_dependencies[current]:
                    if dep not in visited:
                        all_deps.add(dep)
                        queue.append(dep)
        
        return list(all_deps)


class ASCIIVisualizer:
    @staticmethod
    def generate_tree(dependency_graph, root):
        if root not in dependency_graph:
            return root
        
        def build_tree(pkg, prefix="", is_last=True):
            result = []
            connector = "└── " if is_last else "├── "
            result.append(prefix + connector + pkg)
            
            if pkg in dependency_graph and dependency_graph[pkg]:
                children = dependency_graph[pkg]
                new_prefix = prefix + ("    " if is_last else "│   ")
                
                for i, child in enumerate(children):
                    is_last_child = (i == len(children) - 1)
                    result.extend(build_tree(child, new_prefix, is_last_child))
            
            return result
        
        return "\n".join(build_tree(root))


class Config:
    def __init__(self, config_path="config.toml"):
        self.config_path = config_path
        self.package_name = ""
        self.repository_url = ""
        self.test_repository_mode = False
        self.ascii_tree_output = False
        self._load_config()
    
    def _load_config(self):
        if not os.path.exists(self.config_path):
            raise ConfigFileNotFoundError(self.config_path)
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = toml.load(f)
        
        self.package_name = config_data['package_name']
        self.repository_url = config_data['repository_url']
        self.test_repository_mode = config_data['test_repository_mode']
        self.ascii_tree_output = config_data['ascii_tree_output']
    
    def display_parameters(self):
        print("=== Configuration Parameters ===")
        print(f"package_name: {self.package_name}")
        print(f"repository_url: {self.repository_url}")
        print(f"test_repository_mode: {self.test_repository_mode}")
        print(f"ascii_tree_output: {self.ascii_tree_output}")
        print("================================")


def main():
    parser = argparse.ArgumentParser(description='Dependency Graph Visualizer')
    parser.add_argument('--config', '-c', default='config.toml')
    
    args = parser.parse_args()
    
    try:
        config = Config(args.config)
        config.display_parameters()
        
        print(f"\nAnalyzing package: {config.package_name}")
        print(f"Test mode: {'enabled' if config.test_repository_mode else 'disabled'}")
        
        # Stage 3: Complete dependency analysis
        print(f"\n=== Stage 3: Complete Dependency Analysis ===")
        
        analyzer = DependencyAnalyzer(test_mode=config.test_repository_mode)
        
        # Get complete dependency graph
        print(f"\nComplete dependency graph for '{config.package_name}':")
        try:
            complete_graph = analyzer.get_complete_dependencies(config.package_name)
            for pkg, deps in complete_graph.items():
                print(f"  {pkg}: {deps}")
        except CircularDependencyError as e:
            print(f"  ERROR: {e}")
        
        # Get transitive dependencies
        transitive_deps = analyzer.get_all_transitive_deps(config.package_name)
        print(f"\nAll transitive dependencies ({len(transitive_deps)}):")
        for i, dep in enumerate(transitive_deps, 1):
            print(f"  {i}. {dep}")
        
        # ASCII tree visualization
        if config.ascii_tree_output:
            print(f"\n=== ASCII Tree ===")
            try:
                tree = ASCIIVisualizer.generate_tree(
                    analyzer.get_complete_dependencies(config.package_name), 
                    config.package_name
                )
                print(tree)
            except CircularDependencyError:
                print("Cannot generate tree - circular dependencies detected")
        
        # Demonstrate circular dependency handling
        print(f"\n=== Circular Dependency Test ===")
        try:
            analyzer.get_complete_dependencies("X", use_cyclic=True)
            print("ERROR: Circular dependency not detected!")
        except CircularDependencyError as e:
            print(f"✓ Correctly detected: {e}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()