"""CodeQL-specific constants and configuration values."""

from typing import Dict, List


class CodeQLConstants:
    """Constants related to CodeQL tool and analysis."""
    
    # Application Configuration
    APPLICATION_NAME = "CodeQL"
    
    # CodeQL CLI Configuration
    DEFAULT_CLI_VERSION = "2.22.2" #Jul 30, 2025
    MIN_SUPPORTED_VERSION = "2.10.1" #Jul 19, 2022
    CLI_BUNDLE_DOWNLOAD_URL = "https://github.com/github/codeql-action/releases/download/{version}/codeql-bundle-{platform}.tar.gz"
    
    # GitHub API Configuration
    GITHUB_API_BASE_URL = "https://api.github.com"
    GITHUB_CODEQL_REPO = "github/codeql-action"
    GITHUB_RELEASES_LATEST_URL = f"{GITHUB_API_BASE_URL}/repos/{GITHUB_CODEQL_REPO}/releases/latest"
    GITHUB_RELEASES_TAG_URL = f"{GITHUB_API_BASE_URL}/repos/{GITHUB_CODEQL_REPO}/releases/tags"
    
    # Database Configuration
    DEFAULT_DATABASE_NAME = "{language}-db"
    DATABASE_CREATION_TIMEOUT_MINUTES = 30
    QUERY_EXECUTION_TIMEOUT_MINUTES = 60
    
    # Query Suites
    DEFAULT_QUERY_SUITES: Dict[str, str] = {
        "security": "security-extended.qls",
        "quality": "code-scanning.qls",
        "security-and-quality": "security-and-quality.qls"
    }
    
    # SARIF Configuration
    SARIF_VERSION = "2.1.0"
    SARIF_SCHEMA_URL = "https://json.schemastore.org/sarif-2.1.0.json"
    
    # File and Directory Names
    CODEQL_CONFIG_FILE = ".codeql.yml"
    RESULTS_DIRECTORY = "codeql-results"
    DATABASE_DIRECTORY = "codeql-{language}-db"
    TEMP_DIRECTORY = ".codeql-temp"
    
    # Query Pack Names
    STANDARD_QUERY_PACKS: Dict[str, List[str]] = {
        "javascript": ["codeql/javascript-queries"],
        "python": ["codeql/python-queries"],
        "java": ["codeql/java-queries"],
        "csharp": ["codeql/csharp-queries"],
        "cpp": ["codeql/cpp-queries"],
        "go": ["codeql/go-queries"],
        "ruby": ["codeql/ruby-queries"],
        "swift": ["codeql/swift-queries"]
    }