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


class GraphvizVisualizer:
    @staticmethod
    def generate_dot_graph(dependency_graph, root_package, graph_type="dependencies"):
        dot_lines = []
        
        if graph_type == "dependencies":
            dot_lines.append("digraph Dependencies {")
            dot_lines.append("    rankdir=TB;")
            dot_lines.append("    node [shape=box, style=filled, fillcolor=lightblue];")
            dot_lines.append(f'    "{root_package}" [fillcolor=orange];')
        else:
            dot_lines.append("digraph ReverseDependencies {")
            dot_lines.append("    rankdir=BT;")
            dot_lines.append("    node [shape=ellipse, style=filled, fillcolor=lightgreen];")
            dot_lines.append(f'    "{root_package}" [fillcolor=yellow];')
        
        for package, dependencies in dependency_graph.items():
            for dep in dependencies:
                if graph_type == "dependencies":
                    dot_lines.append(f'    "{package}" -> "{dep}";')
                else:
                    dot_lines.append(f'    "{dep}" -> "{package}";')
        
        dot_lines.append("}")
        return "\n".join(dot_lines)
    
    @staticmethod
    def save_dot_file(dot_content, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(dot_content)


class DependencyAnalyzer:
    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        
        self.test_dependencies = {
            "A": ["B", "C"],
            "B": ["D", "E"], 
            "C": ["F", "G"],
            "D": ["H"],
            "E": ["H", "I"],
            "F": [],
            "G": ["I"],
            "H": [],
            "I": [],
            "J": ["A", "K"],
            "K": ["B"],
            "L": ["C", "M"],
            "M": ["H"],
            "N": ["O", "P"],
            "O": ["Q"],
            "P": ["Q", "R"],
            "Q": [],
            "R": []
        }
        
        self.cyclic_dependencies = {
            "X": ["Y"],
            "Y": ["Z"], 
            "Z": ["X"]
        }
    
    def get_complete_dependencies(self, package_name, use_cyclic=False):
        graph = self.cyclic_dependencies if use_cyclic else self.test_dependencies
        
        def bfs_recursive(pkg, visited=None, path=None):
            if visited is None:
                visited = set()
            if path is None:
                path = []
            
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
                    sub_deps = bfs_recursive(dep, visited, current_path)
                    result.update(sub_deps)
            
            return result
        
        try:
            return bfs_recursive(package_name)
        except CircularDependencyError as e:
            raise e
    
    def get_all_transitive_deps(self, package_name):
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
    
    def get_reverse_dependencies(self, package_name):
        reverse_deps = set()
        
        reverse_graph = {}
        for package, dependencies in self.test_dependencies.items():
            for dep in dependencies:
                if dep not in reverse_graph:
                    reverse_graph[dep] = []
                reverse_graph[dep].append(package)
        
        if package_name in reverse_graph:
            visited = set()
            queue = deque([package_name])
            
            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)
                
                if current in reverse_graph:
                    for reverse_dep in reverse_graph[current]:
                        if reverse_dep not in visited and reverse_dep != package_name:
                            reverse_deps.add(reverse_dep)
                            queue.append(reverse_dep)
        
        return list(reverse_deps)
    
    def get_all_reverse_dependencies(self, package_name):
        reverse_graph = {}
        for package, dependencies in self.test_dependencies.items():
            for dep in dependencies:
                if dep not in reverse_graph:
                    reverse_graph[dep] = []
                reverse_graph[dep].append(package)
        
        def reverse_bfs_recursive(pkg, visited=None, path=None):
            if visited is None:
                visited = set()
            if path is None:
                path = []
            
            if pkg in path:
                raise CircularDependencyError(pkg, path)
            
            if pkg in visited:
                return {}
            
            visited.add(pkg)
            current_path = path + [pkg]
            
            result = {pkg: []}
            if pkg in reverse_graph:
                for reverse_dep in reverse_graph[pkg]:
                    result[pkg].append(reverse_dep)
                    sub_deps = reverse_bfs_recursive(reverse_dep, visited, current_path)
                    result.update(sub_deps)
            
            return result
        
        try:
            return reverse_bfs_recursive(package_name)
        except CircularDependencyError as e:
            raise e


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
        self.reverse_dependencies_mode = False
        self.graphviz_output = False
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
        self.reverse_dependencies_mode = config_data.get('reverse_dependencies_mode', False)
        self.graphviz_output = config_data.get('graphviz_output', False)
    
    def display_parameters(self):
        print("=== Configuration Parameters ===")
        print(f"package_name: {self.package_name}")
        print(f"repository_url: {self.repository_url}")
        print(f"test_repository_mode: {self.test_repository_mode}")
        print(f"ascii_tree_output: {self.ascii_tree_output}")
        print(f"reverse_dependencies_mode: {self.reverse_dependencies_mode}")
        print(f"graphviz_output: {self.graphviz_output}")
        print("================================")


def create_sample_config():
    config_content = """# Dependency analyzer configuration
package_name = "A"
repository_url = ""
test_repository_mode = true
ascii_tree_output = true
reverse_dependencies_mode = false
graphviz_output = true
"""
    with open("config.toml", "w", encoding="utf-8") as f:
        f.write(config_content)
    print("Created sample config file: config.toml")


def main():
    parser = argparse.ArgumentParser(description='Dependency Graph Visualizer')
    parser.add_argument('--config', '-c', default='config.toml')
    parser.add_argument('--create-sample', action='store_true')
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_config()
        return
    
    try:
        config = Config(args.config)
        config.display_parameters()
        
        print(f"\nAnalyzing package: {config.package_name}")
        print(f"Test mode: {'enabled' if config.test_repository_mode else 'disabled'}")
        print(f"Reverse dependencies: {'enabled' if config.reverse_dependencies_mode else 'disabled'}")
        print(f"Graphviz output: {'enabled' if config.graphviz_output else 'disabled'}")
        
        analyzer = DependencyAnalyzer(test_mode=config.test_repository_mode)
        graphviz = GraphvizVisualizer()
        
        if not config.reverse_dependencies_mode:
            print(f"\n=== Dependency Analysis ===")
            
            try:
                complete_graph = analyzer.get_complete_dependencies(config.package_name)
                print(f"\nComplete dependency graph for '{config.package_name}':")
                for pkg, deps in complete_graph.items():
                    print(f"  {pkg}: {deps}")
                
                transitive_deps = analyzer.get_all_transitive_deps(config.package_name)
                print(f"\nAll transitive dependencies ({len(transitive_deps)}):")
                for i, dep in enumerate(transitive_deps, 1):
                    print(f"  {i}. {dep}")
                
                if config.ascii_tree_output:
                    print(f"\n=== ASCII Tree ===")
                    tree = ASCIIVisualizer.generate_tree(complete_graph, config.package_name)
                    print(tree)
                
                if config.graphviz_output:
                    print(f"\n=== Graphviz DOT Code ===")
                    dot_content = graphviz.generate_dot_graph(complete_graph, config.package_name, "dependencies")
                    dot_filename = f"{config.package_name}_dependencies.dot"
                    graphviz.save_dot_file(dot_content, dot_filename)
                    print("DOT code generated successfully")
                    
            except CircularDependencyError as e:
                print(f"  ERROR: {e}")
        
        else:
            print(f"\n=== Reverse Dependencies ===")
            
            reverse_deps = analyzer.get_reverse_dependencies(config.package_name)
            print(f"\nDirect reverse dependencies for '{config.package_name}':")
            if reverse_deps:
                for i, dep in enumerate(reverse_deps, 1):
                    print(f"  {i}. {dep}")
            
            try:
                reverse_graph = analyzer.get_all_reverse_dependencies(config.package_name)
                print(f"\nComplete reverse dependency graph for '{config.package_name}':")
                for pkg, deps in reverse_graph.items():
                    print(f"  {pkg}: {deps}")
                
                if config.ascii_tree_output:
                    print(f"\n=== Reverse ASCII Tree ===")
                    reverse_tree = ASCIIVisualizer.generate_tree(reverse_graph, config.package_name)
                    print(reverse_tree)
                
                if config.graphviz_output:
                    print(f"\n=== Reverse Graphviz DOT Code ===")
                    dot_content = graphviz.generate_dot_graph(reverse_graph, config.package_name, "reverse")
                    dot_filename = f"{config.package_name}_reverse.dot"
                    graphviz.save_dot_file(dot_content, dot_filename)
                    print("DOT code generated successfully")
                    
            except CircularDependencyError as e:
                print(f"  ERROR: {e}")
        
        print(f"\n=== Circular Dependency Test ===")
        try:
            analyzer.get_complete_dependencies("X", use_cyclic=True)
            print("ERROR: Circular dependency not detected!")
        except CircularDependencyError as e:
            print(f"✓ Correctly detected: {e}")
            
        print(f"\n=== Stage 5: Graphviz DOT Examples ===")
        demo_packages = ["A", "H", "N"]
        for pkg in demo_packages:
            if pkg != config.package_name:
                try:
                    demo_graph = analyzer.get_complete_dependencies(pkg)
                    dot_content = graphviz.generate_dot_graph(demo_graph, pkg, "dependencies")
                    dot_filename = f"{pkg}_demo.dot"
                    graphviz.save_dot_file(dot_content, dot_filename)
                    print(f"Generated DOT for package: {pkg}")
                except CircularDependencyError:
                    pass
        
        print(f"\n=== Comparison with APT ===")
        print("Our tool vs APT:")
        print("- Our tool: Complete transitive dependency graph")
        print("- APT: Direct dependencies only")
        print("- Differences: Test data vs real packages")
            
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()