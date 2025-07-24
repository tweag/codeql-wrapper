---
sidebar_position: 4
---

# CI/CD Integration

CodeQL Wrapper is designed to work seamlessly with various CI/CD platforms. This guide shows how to integrate it into your pipelines.

> **Working Examples Available**: Complete implementation examples for all CI/CD platforms can be found at:  
> [https://github.com/ModusCreate-fernandomatsuo-GHAS/poc-codeql-wrapper](https://github.com/ModusCreate-fernandomatsuo-GHAS/poc-codeql-wrapper)

## GitHub Actions

### Basic Workflow

Create `.github/workflows/codeql-analysis.yml`:

```yaml
name: CodeQL Analysis

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday at 2 AM

jobs:
  codeql-analysis:
    name: CodeQL Analysis
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      contents: read
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install CodeQL Wrapper
      run: pip install codeql-wrapper
    
    - name: Run CodeQL Analysis
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        codeql-wrapper analyze ./project-folder --upload-sarif
```

### Monorepo Workflow

For monorepos:

```yaml
    - name: Run CodeQL Analysis (Monorepo)
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        codeql-wrapper analyze ./monorepo-folder \
          --monorepo \
          --upload-sarif \
```

### Matrix Strategy

Analyze different languages separately:

```yaml
jobs:
  codeql-analysis:
    strategy:
      matrix:
        language: [python, javascript, java]
    
    steps:
    # ... setup steps ...
    
    - name: Run CodeQL Analysis
      run: |
        codeql-wrapper analyze ./project-folder \
          --languages ${{ matrix.language }} \
          --upload-sarif
```

## Harness

### Pipeline YAML

```yaml
pipeline:
  name: Monorepo CodeQL Analysis
  identifier: codeql_analysis
  projectIdentifier: default_project
  orgIdentifier: default
  properties:
    ci:
      codebase:
        build: <+input>
        connectorRef: monorepo
        repoName: poc-codeql-wrapper
  stages:
    - stage:
        name: CodeQL
        identifier: security_analysis
        type: CI
        spec:
          cloneCodebase: true
          execution:
            steps:
              - step:
                  type: Run
                  name: Install Python
                  identifier: install_python
                  spec:
                    shell: Bash
                    command: |
                      chmod +x ./install_python.sh
                      ./install_python.sh
              - step:
                  type: Run
                  name: Install CodeQL Wrapper
                  identifier: install_codeql_wrapper
                  spec:
                    shell: Bash
                    command: |
                      # https://test.pypi.org/project/codeql-wrapper/
                      pip install -i https://test.pypi.org/simple/ codeql-wrapper
                      codeql-wrapper --version
              - step:
                  type: Run
                  name: Run CodeQL Analysis
                  identifier: run_codeql_analysis
                  spec:
                    shell: Bash
                    envVariables:
                      GITHUB_TOKEN: <+secrets.getValue("PAT")>
                    command: |
                      curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
                      codeql-wrapper --verbose analyze ./monorepo --monorepo --upload-sarif
          platform:
            os: Linux
            arch: Amd64
          runtime:
            type: Cloud
            spec: {}
```
## Azure DevOps

### CodeQL Analysis (Manual Trigger)

This pipeline is designed for manual execution to perform a full CodeQL analysis on the `monorepo` directory.

```yaml
# This pipeline is manually triggered
trigger: none
pr: none

pool:
  vmImage: ubuntu-latest

steps:
  - script: |
      chmod +x ./install_python.sh
      ./install_python.sh
    displayName: "Install Python"

  - script: |
      # https://test.pypi.org/project/codeql-wrapper/
      pip install -i https://test.pypi.org/simple/ codeql-wrapper
      codeql-wrapper --version
    displayName: "Install CodeQL Wrapper"

  - script: |
      curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
      codeql-wrapper --verbose analyze ./monorepo --monorepo --upload-sarif
    displayName: "Run CodeQL Analysis"
    env:
      GITHUB_TOKEN: $(PAT) # Define this secret in Azure Pipeline variables
```

### CodeQL Analysis for Pull Requests

This pipeline is triggered on pull requests and performs a CodeQL analysis focusing only on changed files within the `monorepo`.

```yaml
# This pipeline is manually triggered
trigger:
  branches:
    include:
      - "*"
pr:
  branches:
    include:
      - "*"

pool:
  vmImage: ubuntu-latest

steps:
  - checkout: self
    fetchDepth: 0

  - script: |
      chmod +x ./install_python.sh
      ./install_python.sh
    displayName: "Install Python"

  - script: |
      # https://test.pypi.org/project/codeql-wrapper/
      pip install -i https://test.pypi.org/simple/ codeql-wrapper
      codeql-wrapper --version
    displayName: "Install CodeQL Wrapper"

  - script: |
      curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
      codeql-wrapper --verbose analyze ./monorepo \
        --monorepo \
        --upload-sarif \
        --only-changed-files

    displayName: "Run CodeQL Analysis"
    env:
      GITHUB_TOKEN: $(PAT) # Define this secret in Azure Pipeline variables
```

## CircleCI

### `.circleci/config.yml`

```yaml
version: 2.1

jobs:
  codeql-analysis:
    docker:
      - image: cimg/python:3.13 # Use a suitable image for your Python & Linux environment

    steps:
      - checkout

      - run:
          name: Install Python (if needed)
          command: |
            chmod +x ./install_python.sh
            ./install_python.sh

      - run:
          name: Install CodeQL Wrapper
          command: |
            # https://test.pypi.org/project/codeql-wrapper/
            pip install -i https://test.pypi.org/simple/ codeql-wrapper
            codeql-wrapper --version

      - run:
          name: Run CodeQL Analysis
          command: |
            export GITHUB_TOKEN=${PAT} # Set PAT as environment variable in CircleCI project settings
            curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
            codeql-wrapper --verbose analyze ./monorepo --monorepo --upload-sarif

workflows:
  version: 2
  codeql-workflow:
    jobs:
      - codeql-analysis
```

## Best Practices

### Security Considerations

1. **Use secure credential storage** for GitHub tokens
2. **Limit token permissions** to `security_events` scope
3. **Use separate tokens** for different repositories if needed
4. **Rotate tokens regularly**

### Performance Optimization

1. **Use caching** for CodeQL installation
2. **Run analysis on schedule** for large repositories
3. **Use matrix strategies** for parallel language analysis
4. **Cache dependencies** where possible

### Error Handling

1. **Set appropriate timeouts** for long-running analyses
2. **Archive results** even on failure for debugging
3. **Use verbose logging** for troubleshooting

## Troubleshooting

### Common Issues

1. **Permission denied**: Ensure proper GitHub token permissions
2. **Rate limiting**: Use GitHub token for higher rate limits
3. **Large repositories**: Consider using `--languages` to limit scope
4. **Memory issues**: Use smaller CI/CD instances or break down analysis

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
codeql-wrapper analyze . --verbose 2>&1 | tee codeql-debug.log
```


