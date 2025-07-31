# Install CodeQL Feature

This feature implements CodeQL CLI installation functionality following Clean Architecture principles.

## Structure

```
install_codeql/
├── commands/
│   ├── __init__.py
│   └── install_codeql_command.py     # Application command
├── use_cases/
│   ├── __init__.py
│   └── install_codeql_use_case.py    # Business logic
└── __init__.py
```

## Components

### Commands
- **InstallCodeQLCommand**: Application command that encapsulates installation parameters with validation

### Use Cases
- **InstallCodeQLUseCase**: Main business logic for CodeQL installation workflow
  - Handles installation process
  - Manages version checking and upgrades
  - Coordinates with infrastructure services

## Usage

The feature is integrated into the CLI through the presentation layer:

```bash
# Install latest version
codeql-wrapper codeql install

# Install specific version
codeql-wrapper codeql install --version 2.22.0

# Force reinstall
codeql-wrapper codeql install --force

# Custom installation directory
codeql-wrapper codeql install --installation-dir /opt/codeql

# With GitHub token for higher rate limits
codeql-wrapper codeql install --github-token ghp_xxxxx
```

## Architecture Flow

1. **Presentation Layer** (`cli/codeql_install_command.py`):
   - Handles CLI input parsing
   - Creates application commands
   - Formats output for users

2. **Application Layer** (`features/install_codeql/`):
   - Encapsulates business rules
   - Orchestrates domain services
   - Handles error scenarios

3. **Infrastructure Layer** (`services/codeql_service.py`):
   - Downloads and installs CodeQL CLI
   - Manages file system operations
   - Handles GitHub API interactions

4. **Domain Layer** (`interfaces/codeql_service.py`):
   - Defines service contracts
   - Contains domain entities and exceptions
   - Business invariants and validation

## Error Handling

The feature provides comprehensive error handling:

- **CodeQLInstallationError**: Installation-specific failures
- **CodeQLError**: General CodeQL operation errors
- **ValidationError**: Command validation failures

## Output Formats

Supports multiple output formats:
- **Human-readable**: Colored, formatted output for interactive use
- **JSON**: Structured output for programmatic consumption

## Dependencies

- Domain interfaces for service contracts
- Infrastructure services for CodeQL operations
- Presentation DTOs for input/output formatting
