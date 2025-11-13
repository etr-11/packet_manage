# -*- coding: utf-8 -*-

import os
import sys
import argparse

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


class InvalidConfigError(ConfigError):
    def __init__(self, field, value, reason):
        super().__init__(f"Invalid value '{value}' for field '{field}': {reason}")


class MissingConfigFieldError(ConfigError):
    def __init__(self, field):
        super().__init__(f"Missing required config field: {field}")


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
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = toml.load(f)
        except toml.TomlDecodeError as e:
            raise ConfigError(f"TOML parsing error: {e}")
        except Exception as e:
            raise ConfigError(f"Config file reading error: {e}")
        
        self._validate_and_load(config_data)
    
    def _validate_and_load(self, config_data):
        if 'package_name' not in config_data:
            raise MissingConfigFieldError('package_name')
        
        self.package_name = config_data['package_name']
        if not isinstance(self.package_name, str) or not self.package_name.strip():
            raise InvalidConfigError('package_name', self.package_name, "must be non-empty string")
        
        if 'repository_url' not in config_data:
            raise MissingConfigFieldError('repository_url')
        
        self.repository_url = config_data['repository_url']
        if not isinstance(self.repository_url, str) or not self.repository_url.strip():
            raise InvalidConfigError('repository_url', self.repository_url, "must be non-empty string")
        
        if 'test_repository_mode' not in config_data:
            raise MissingConfigFieldError('test_repository_mode')
        
        test_mode = config_data['test_repository_mode']
        if not isinstance(test_mode, bool):
            raise InvalidConfigError('test_repository_mode', test_mode, "must be boolean value")
        self.test_repository_mode = test_mode
        
        if 'ascii_tree_output' not in config_data:
            raise MissingConfigFieldError('ascii_tree_output')
        
        ascii_output = config_data['ascii_tree_output']
        if not isinstance(ascii_output, bool):
            raise InvalidConfigError('ascii_tree_output', ascii_output, "must be boolean value")
        self.ascii_tree_output = ascii_output
    
    def get_all_parameters(self):
        return {
            'package_name': self.package_name,
            'repository_url': self.repository_url,
            'test_repository_mode': self.test_repository_mode,
            'ascii_tree_output': self.ascii_tree_output
        }
    
    def display_parameters(self):
        params = self.get_all_parameters()
        print("=== Configuration Parameters ===")
        for key, value in params.items():
            print(f"{key}: {value}")
        print("================================")


def create_sample_config():
    config_content = """# Dependency analyzer configuration
package_name = "example-package"
repository_url = "https://github.com/example/repo"
test_repository_mode = false
ascii_tree_output = true
"""
    with open("config.toml", "w", encoding="utf-8") as f:
        f.write(config_content)
    print("Created sample config file: config.toml")


def main():
    parser = argparse.ArgumentParser(description='Package dependency graph visualizer')
    parser.add_argument('--config', '-c', default='config.toml',
                       help='Path to config file (default: config.toml)')
    parser.add_argument('--create-sample', action='store_true',
                       help='Create sample config file')
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_config()
        return
    
    try:
        config = Config(args.config)
        
        config.display_parameters()
        
        print(f"\nAnalyzing package: {config.package_name}")
        print(f"Source: {config.repository_url}")
        print(f"Test mode: {'enabled' if config.test_repository_mode else 'disabled'}")
        print(f"Output format: {'ASCII tree' if config.ascii_tree_output else 'standard'}")
        
        print("\n[INFO] Dependency analysis will be implemented in next stages")
        
    except ConfigFileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("\nTip: use --create-sample to create sample config")
        sys.exit(1)
    except MissingConfigFieldError as e:
        print(f"CONFIG ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except InvalidConfigError as e:
        print(f"CONFIG ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except ConfigError as e:
        print(f"CONFIG ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UNKNOWN ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()