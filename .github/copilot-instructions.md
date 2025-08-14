# GitHub Copilot Instructions for CodeQL Wrapper

## Project Overview
This is a Python CLI application that provides a universal wrapper for CodeQL analysis across different project architectures (monorepos, single repos) and CI/CD platforms. The project follows Clean Architecture principles with domain-driven design patterns.

**Current Implementation**: The project has two implementations:
- `src/codeql_wrapper/` - Legacy implementation
- `src/codeql_wrapper_v2/` - **Current active development** following Clean Architecture

## codeql-wrapper-v2 Architecture

The v2 implementation strictly follows Clean Architecture with this proven structure:

### Current Project Structure
```
src/codeql_wrapper_v2/
├── domain/                    # Core business logic (no external dependencies)
│   ├── constants/            # System-wide constant values
│   ├── entities/             # Core business objects with identity
│   ├── enumerators/          # Enums for categorization
│   ├── exceptions/           # Custom domain-level exceptions
│   ├── interfaces/           # Interfaces to abstract data access
│   └── shared/               # Common domain models/utilities
├── application/              # Use cases and business workflows
│   └── features/             # Feature-based organization
│       ├── install_codeql/   # CodeQL installation feature
│       │   └── use_cases/    # Business logic orchestration
│       ├── analyze_repository/ # Repository analysis feature
│       └── detect_projects/  # Project detection feature
├── infrastructure/           # External integrations
│   ├── exceptions/           # Infrastructure-specific exceptions
│   ├── external_tools/       # CLI tool wrappers (CodeQL, Git)
│   ├── file_system/          # File and directory operations
│   ├── logging/              # Logging implementations
│   └── services/             # External service implementations
└── presentation/             # User interface layer
    ├── cli/                  # CLI command handlers
    ├── dto/                  # Data Transfer Objects for CLI I/O
    ├── formatters/           # Output formatters (JSON, human-readable)
    └── middlewares/          # Cross-cutting concerns

### CLI Entry Points
The v2 implementation provides CLI access through:
```toml
# pyproject.toml
[tool.poetry.scripts]
codeql-wrapper-v2 = "codeql_wrapper_v2.presentation.cli.codeql_install_command:codeql"
```

**Available Commands:**
- `codeql-wrapper-v2 install` - Install CodeQL CLI with version management
- `codeql-wrapper-v2 install --help` - Show installation options
- `codeql-wrapper-v2 --help` - Show main help

### Testing Strategy
The project implements comprehensive E2E testing:

```
tests/e2e/
└── test_client_install_e2e.py    # Real client-side E2E tests
```

**Test Configuration** (in `pyproject.toml`):
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["-v", "--strict-markers", "--strict-config", "-n", "auto"]
markers = [
    "slow: Slow tests that take several minutes",
    "e2e: End-to-end tests",
    "unit: Unit tests",
    "integration: Integration tests"
]
```

**Testing Approach:**
- **Real E2E Tests**: No mocking, actual CodeQL downloads and installations
- **Parallel Execution**: Tests run in parallel by default (`-n auto`)
- **Platform-Specific**: Tests adapt to macOS/Windows/Linux environments
- **Client-Side Testing**: Tests use `poetry run codeql-wrapper-v2` like real users

## Current Implementation Patterns

### Command Pattern (Install Feature)
The install feature follows command-query separation:

```python
# Example: Install Command Structure
# application/features/install_codeql/commands/install_command.py
@dataclass(frozen=True)
class InstallCodeQLCommand:
    """Command to install CodeQL CLI."""
    version: Optional[str] = None
    installation_dir: Optional[str] = None
    force: bool = False
    github_token: Optional[str] = None

# application/features/install_codeql/use_cases/install_use_case.py
class InstallCodeQLUseCase:
    """Use case for installing CodeQL CLI."""
    
    def __init__(
        self,
        installer_service: CodeQLInstallerService,
        path_manager: PathManagerService
    ) -> None:
        self._installer = installer_service
        self._path_manager = path_manager
    
    async def execute(self, command: InstallCodeQLCommand) -> InstallationResult:
        """Execute CodeQL installation workflow."""
        # Business logic orchestration
        pass
```

### CLI Implementation Pattern
The presentation layer uses Click for CLI handling:

```python
# presentation/cli/codeql_install_command.py
import click
from ...application.features.install_codeql.commands.install_command import InstallCodeQLCommand
from ...application.features.install_codeql.use_cases.install_use_case import InstallCodeQLUseCase

@click.group()
def codeql():
    """CodeQL CLI management commands."""
    pass

@codeql.command()
@click.option('--version', help='CodeQL version to install')
@click.option('--installation-dir', help='Installation directory')
@click.option('--force', is_flag=True, help='Force reinstallation')
@click.option('--format', type=click.Choice(['json', 'human']), default='human')
def install(version: str, installation_dir: str, force: bool, format: str):
    """Install CodeQL CLI."""
    # Thin adapter layer - delegates to use cases
    command = InstallCodeQLCommand(
        version=version,
        installation_dir=installation_dir,
        force=force
    )
    
    # Execute use case
    use_case = get_install_use_case()  # Dependency injection
    result = use_case.execute(command)
    
    # Format and display results
    formatter = get_formatter(format)
    click.echo(formatter.format(result))
```

### Infrastructure Services Pattern
External integrations are wrapped in infrastructure services:

```python
# infrastructure/external_tools/codeql_cli.py
class CodeQLCLIService:
    """Service for interacting with CodeQL CLI binary."""
    
    def __init__(self, executable_path: str):
        self._executable_path = executable_path
    
    def get_version(self) -> str:
        """Get CodeQL version by running --version command."""
        pass
    
    def validate_installation(self) -> bool:
        """Validate CodeQL installation."""
        pass

# infrastructure/services/github_service.py
class GitHubReleaseService:
    """Service for downloading CodeQL from GitHub releases."""
    
    def __init__(self, token: Optional[str] = None):
        self._token = token
    
    async def get_latest_version(self) -> str:
        """Get latest CodeQL version from GitHub."""
        pass
    
    async def download_release(self, version: str, target_dir: str) -> None:
        """Download and extract CodeQL release."""
        pass
```

## Clean Code Best Practices

### 2. Naming Conventions
- Use **descriptive, intention-revealing names** for variables, functions, and classes
- Prefer `calculate_analysis_duration()` over `calc_time()`
- Use **verb-noun pattern** for functions: `validate_codeql_database()`, `extract_language_info()`
- Use **noun phrases** for classes: `CodeQLAnalysisResult`, `LanguageDetector`
- Avoid abbreviations unless they're domain-specific: `codeql`, `sarif`, `cicd`
- Use **boolean prefixes**: `is_valid`, `has_results`, `can_execute`, `should_retry`

### 3. Function Design
- **Single Responsibility Principle**: Each function should do one thing well
- **Keep functions small**: Aim for 10-20 lines maximum
- **Minimize parameters**: Use 3 or fewer parameters; consider parameter objects for more
- **Pure functions when possible**: Avoid side effects, make dependencies explicit
- **Return early**: Use guard clauses to reduce nesting
- **Prefer composition over inheritance**

### 4. Error Handling
- **Use specific exception types**: Create custom exceptions for domain errors
- **Fail fast**: Validate inputs early and explicitly
- **Meaningful error messages**: Include context about what went wrong and how to fix it
- **Log appropriately**: Use structured logging with appropriate levels
- **Don't catch and ignore**: Always handle exceptions meaningfully

### 5. Type Annotations
- **Use comprehensive type hints**: All public methods and complex private methods
- **Leverage Union types**: `Optional[T]`, `Union[T, U]` for clarity
- **Use dataclasses and Pydantic**: For structured data validation
- **Protocol types**: For defining interfaces and contracts
- **Generic types**: When building reusable components

### 6. Testing Strategy
- **Test-Driven Development**: Write tests before implementation when possible
- **Unit tests**: Focus on domain logic and business rules
- **Integration tests**: Test infrastructure components and external integrations
- **E2E tests**: Real client-side testing without mocking using `poetry run codeql-wrapper-v2`
- **Parallel testing**: Default parallel execution with `-n auto` for faster test runs
- **Test naming**: Use descriptive names that explain the scenario being tested
- **Given-When-Then pattern**: Structure test methods clearly
- **Mock external dependencies**: Use dependency injection for testability
- **Platform-specific tests**: Use `@pytest.mark.skipif` for OS-specific features

### 7. Documentation
- **Docstrings**: Use Google or NumPy style for all public methods and classes
- **Type hints as documentation**: Let types explain parameter and return expectations
- **README updates**: Keep documentation current with code changes
- **Code comments**: Explain "why" not "what" - focus on business context and decisions

### 8. Dependency Management
- **Dependency Inversion**: Depend on abstractions, not concrete implementations
- **Explicit dependencies**: Make all dependencies clear in constructors/function parameters
- **Minimal external dependencies**: Evaluate necessity of each new dependency
- **Version pinning**: Use Poetry for reproducible builds

### 9. Performance Considerations
- **Lazy loading**: Load resources only when needed
- **Async operations**: Use async/await for I/O-bound operations
- **Resource cleanup**: Use context managers for file handling and external resources
- **Caching**: Implement intelligent caching for expensive operations
- **Memory efficiency**: Avoid loading large files entirely into memory when possible

### 10. Security Best Practices
- **Input validation**: Sanitize all external inputs
- **Command injection prevention**: Use subprocess safely with shell=False
- **File path validation**: Prevent directory traversal attacks
- **Secure defaults**: Fail securely when configuration is missing
- **Secrets management**: Never hardcode secrets, use environment variables or secret management

## Specific Implementation Patterns

### Entity Design
```python
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from ..enumerators.analysis_status import AnalysisStatus
from ..enumerators.severity import Severity
from ..value_objects.finding import Finding

@dataclass(frozen=True)
class CodeQLAnalysis:
    """Represents a CodeQL analysis with immutable state and rich behavior."""
    id: str
    project_path: str
    status: AnalysisStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    findings: List[Finding] = None
    
    def is_completed(self) -> bool:
        """Check if analysis has completed successfully."""
        return self.status == AnalysisStatus.COMPLETED and self.completed_at is not None
    
    def get_critical_findings(self) -> List[Finding]:
        """Extract high-severity security findings."""
        if not self.findings:
            return []
        return [f for f in self.findings if f.severity == Severity.CRITICAL]
    
    def calculate_duration(self) -> Optional[int]:
        """Calculate analysis duration in seconds."""
        if not self.completed_at:
            return None
        return int((self.completed_at - self.started_at).total_seconds())
```

### Value Object Design
```python
from dataclasses import dataclass
from ..enumerators.severity import Severity

@dataclass(frozen=True)
class Finding:
    """Represents a security finding from CodeQL analysis."""
    rule_id: str
    message: str
    severity: Severity
    file_path: str
    line_number: int
    
    def is_high_priority(self) -> bool:
        """Check if finding requires immediate attention."""
        return self.severity in [Severity.CRITICAL, Severity.HIGH]
```

### Repository Interface Design
```python
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.codeql_analysis import CodeQLAnalysis

class AnalysisRepository(ABC):
    """Abstract repository for CodeQL analysis persistence."""
    
    @abstractmethod
    async def save(self, analysis: CodeQLAnalysis) -> None:
        """Save analysis results."""
        pass
    
    @abstractmethod
    async def find_by_id(self, analysis_id: str) -> Optional[CodeQLAnalysis]:
        """Find analysis by ID."""
        pass
    
    @abstractmethod
    async def find_by_project(self, project_path: str) -> List[CodeQLAnalysis]:
        """Find all analyses for a project."""
        pass
```

### Use Case Design
```python
from dataclasses import dataclass
from typing import Protocol
from ...domain.entities.codeql_analysis import CodeQLAnalysis
from ...domain.repositories.analysis_repository import AnalysisRepository
from ..abstractions.services.codeql_service import CodeQLService

@dataclass(frozen=True)
class RunAnalysisCommand:
    """Command to run CodeQL analysis."""
    project_path: str
    languages: List[str]
    output_format: str = "sarif"

class RunCodeQLAnalysisUseCase:
    """Use case for executing end-to-end CodeQL analysis."""
    
    def __init__(
        self, 
        analysis_repository: AnalysisRepository,
        codeql_service: CodeQLService
    ) -> None:
        self._analysis_repository = analysis_repository
        self._codeql_service = codeql_service
    
    async def execute(self, command: RunAnalysisCommand) -> CodeQLAnalysis:
        """Execute the complete analysis workflow."""
        # Create analysis entity
        analysis = await self._codeql_service.create_analysis(
            command.project_path, 
            command.languages
        )
        
        # Run analysis
        completed_analysis = await self._codeql_service.run_analysis(analysis)
        
        # Save results
        await self._analysis_repository.save(completed_analysis)
        
        return completed_analysis
```

### CLI Command Design
```python
import click
from typing import Optional
from ...application.features.analysis.commands.run_analysis_command import RunAnalysisCommand
from ...application.features.analysis.use_cases.run_codeql_analysis_use_case import RunCodeQLAnalysisUseCase

@click.command()
@click.option('--project-path', type=click.Path(exists=True), required=True,
              help='Path to the project to analyze')
@click.option('--languages', multiple=True, 
              help='Programming languages to analyze')
@click.option('--output-format', default='sarif', 
              type=click.Choice(['sarif', 'json', 'csv']),
              help='Output format for results')
async def analyze(project_path: str, languages: tuple, output_format: str) -> None:
    """Run CodeQL analysis on the specified project."""
    # Thin layer that delegates to use cases
    command = RunAnalysisCommand(
        project_path=project_path,
        languages=list(languages) if languages else [],
        output_format=output_format
    )
    
    # Dependency injection would happen here in real implementation
    use_case = get_analysis_use_case()  # From DI container
    
    try:
        result = await use_case.execute(command)
        click.echo(f"Analysis completed successfully: {result.id}")
    except Exception as e:
        click.echo(f"Analysis failed: {str(e)}", err=True)
        raise click.Abort()
```

### Service Abstraction Design
```python
from abc import ABC, abstractmethod
from typing import List
from ...domain.entities.codeql_analysis import CodeQLAnalysis

class CodeQLService(ABC):
    """Abstract service for CodeQL operations."""
    
    @abstractmethod
    async def create_analysis(self, project_path: str, languages: List[str]) -> CodeQLAnalysis:
        """Create a new analysis instance."""
        pass
    
    @abstractmethod
    async def run_analysis(self, analysis: CodeQLAnalysis) -> CodeQLAnalysis:
        """Execute the CodeQL analysis."""
        pass
    
    @abstractmethod
    async def validate_environment(self) -> bool:
        """Validate that CodeQL environment is properly configured."""
        pass
```

## Code Review Checklist
When reviewing or generating code, ensure:

- [ ] **Business logic is in the domain layer**
- [ ] **External dependencies are injected, not hardcoded**
- [ ] **Functions have single responsibility**
- [ ] **Error handling is explicit and meaningful**
- [ ] **Type hints are comprehensive**
- [ ] **Tests cover the critical business logic**
- [ ] **Names reveal intention clearly**
- [ ] **No code duplication (DRY principle)**
- [ ] **Performance considerations are addressed**
- [ ] **Security best practices are followed**

## Anti-Patterns to Avoid
- **God classes**: Classes that do too many things
- **Anemic domain models**: Entities with only getters/setters
- **Feature envy**: Classes accessing too much data from other classes
- **Primitive obsession**: Using primitives instead of domain-specific types
- **Long parameter lists**: More than 3-4 parameters without parameter objects
- **Deep nesting**: More than 2-3 levels of indentation
- **Global state**: Relying on global variables or singletons
- **Magic numbers/strings**: Use named constants instead

## Refactoring Priorities
When refactoring existing code, focus on:

1. **Extract business logic** from infrastructure concerns
2. **Introduce proper error handling** and validation
3. **Add comprehensive type hints** for better IDE support
4. **Break down large functions** into smaller, focused ones
5. **Eliminate code duplication** through abstraction
6. **Improve test coverage** especially for domain logic
7. **Add missing documentation** for public APIs
8. **Optimize performance bottlenecks** with profiling data

## Integration Guidelines
- **External tools**: Wrap CLI tools in infrastructure adapters
- **File system operations**: Use dependency injection for testability
- **CI/CD platforms**: Create platform-specific implementations behind common interfaces
- **Configuration**: Use environment-specific configuration with sensible defaults
- **Logging**: Implement structured logging with correlation IDs for traceability

Remember: **Code is read more often than it's written.** Prioritize clarity and maintainability over cleverness.
