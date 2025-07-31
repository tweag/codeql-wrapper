"""CI/CD platform enumeration for integration support."""

from enum import Enum, auto
from typing import Optional


class Platform(Enum):
    """Supported CI/CD and development platforms."""
    
    GITHUB_ACTIONS = auto()
    GITLAB_CI = auto()
    AZURE_DEVOPS = auto()
    JENKINS = auto()
    BITBUCKET_PIPELINES = auto()
    CIRCLECI = auto()
    TRAVIS_CI = auto()
    LOCAL = auto()
    
    def get_display_name(self) -> str:
        """Get human-readable platform name."""
        display_names = {
            Platform.GITHUB_ACTIONS: "GitHub Actions",
            Platform.GITLAB_CI: "GitLab CI/CD",
            Platform.AZURE_DEVOPS: "Azure DevOps",
            Platform.JENKINS: "Jenkins",
            Platform.BITBUCKET_PIPELINES: "Bitbucket Pipelines",
            Platform.CIRCLECI: "CircleCI",
            Platform.TRAVIS_CI: "Travis CI",
            Platform.LOCAL: "Local Development"
        }
        return display_names[self]
    
    def supports_sarif_upload(self) -> bool:
        """Check if platform supports SARIF result upload."""
        return self in {
            Platform.GITHUB_ACTIONS
        }
    
    def get_environment_indicator(self) -> Optional[str]:
        """Get environment variable that indicates this platform."""
        indicators = {
            Platform.GITHUB_ACTIONS: "GITHUB_ACTIONS",
            Platform.GITLAB_CI: "GITLAB_CI",
            Platform.AZURE_DEVOPS: "AZURE_HTTP_USER_AGENT",
            Platform.JENKINS: "JENKINS_URL",
            Platform.BITBUCKET_PIPELINES: "BITBUCKET_BUILD_NUMBER",
            Platform.CIRCLECI: "CIRCLECI",
            Platform.TRAVIS_CI: "TRAVIS"
        }
        return indicators.get(self)
    
    @classmethod
    def detect_current_platform(cls) -> 'Platform':
        """Detect the current CI/CD platform from environment variables."""
        import os
        
        for platform in cls:
            if platform == Platform.LOCAL:
                continue
            
            indicator = platform.get_environment_indicator()
            if indicator and os.getenv(indicator):
                return platform
        
        return Platform.LOCAL