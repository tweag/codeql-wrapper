---
sidebar_position: 4
---

# CI/CD Integration

CodeQL Wrapper is designed to work seamlessly with various CI/CD platforms. This guide shows how to integrate it into your pipelines for automated security analysis.

## Prerequisites

Before integrating CodeQL Wrapper into your CI/CD pipeline, ensure you have:

1. **Python 3.8.1+** available in your CI environment
2. **GitHub token** with `security-events` permissions (for SARIF upload)
3. **Git repository** properly configured with remote origin

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
        python-version: '3.12'
    
    - name: Install CodeQL Wrapper
      run: pip install codeql-wrapper
    
    - name: Run CodeQL Analysis
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        codeql-wrapper analyze . --upload-sarif --verbose
```

### Advanced Workflow with Auto-Detection

CodeQL Wrapper automatically detects Git repository information, so you can simplify the command:

```yaml
    - name: Run CodeQL Analysis (Auto-Detection)
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        codeql-wrapper analyze . --upload-sarif --verbose
```

### Monorepo Workflow

For monorepos, enable monorepo analysis:

```yaml
    - name: Run CodeQL Analysis (Monorepo)
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        codeql-wrapper analyze . --monorepo --upload-sarif --verbose
```

### Matrix Strategy for Multiple Languages

Analyze different languages in parallel:

```yaml
jobs:
  codeql-analysis:
    strategy:
      matrix:
        language: [python, javascript, java, csharp]
    name: CodeQL Analysis (${{ matrix.language }})
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
        python-version: '3.12'
    
    - name: Install CodeQL Wrapper
      run: pip install codeql-wrapper
    
    - name: Run CodeQL Analysis
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        codeql-wrapper analyze . \
          --languages ${{ matrix.language }} \
          --upload-sarif \
          --verbose
```

### Caching CodeQL Installation

Optimize performance by caching CodeQL installation:

```yaml
    - name: Cache CodeQL
      uses: actions/cache@v3
      with:
        path: ~/.codeql
        key: codeql-${{ runner.os }}-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          codeql-${{ runner.os }}-
    
    - name: Install CodeQL Wrapper
      run: pip install codeql-wrapper
    
    - name: Run CodeQL Analysis
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        codeql-wrapper analyze . --upload-sarif --verbose
```

## Jenkins

### Declarative Pipeline

```groovy
pipeline {
    agent any
    
    environment {
        GITHUB_TOKEN = credentials('github-token')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup Python') {
            steps {
                sh '''
                    python3 -m pip install --upgrade pip
                    pip3 install codeql-wrapper
                '''
            }
        }
        
        stage('CodeQL Analysis') {
            steps {
                script {
                    try {
                        sh '''
                            codeql-wrapper analyze . \
                              --upload-sarif \
                              --verbose
                        '''
                    } catch (Exception e) {
                        echo "CodeQL analysis failed: ${e.getMessage()}"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'codeql-results/**/*', allowEmptyArchive: true
        }
        failure {
            echo 'Pipeline failed - check CodeQL analysis logs'
        }
    }
}
```

### Scripted Pipeline

```groovy
node {
    try {
        stage('Checkout') {
            checkout scm
        }
        
        stage('Install Dependencies') {
            sh '''
                python3 -m pip install --upgrade pip
                pip3 install codeql-wrapper
            '''
        }
        
        stage('CodeQL Analysis') {
            withCredentials([string(credentialsId: 'github-token', variable: 'GITHUB_TOKEN')]) {
                sh '''
                    codeql-wrapper analyze . \
                      --output-dir codeql-results \
                      --upload-sarif \
                      --verbose
                '''
            }
        }
    } catch (Exception e) {
        currentBuild.result = 'FAILURE'
        echo "Pipeline failed: ${e.getMessage()}"
        throw e
    } finally {
        archiveArtifacts artifacts: 'codeql-results/**/*', allowEmptyArchive: true
    }
}
```

### Jenkins with Docker

```groovy
pipeline {
    agent {
        docker {
            image 'python:3.12-slim'
            args '-u root:root'
        }
    }
    
    environment {
        GITHUB_TOKEN = credentials('github-token')
    }
    
    stages {
        stage('Install Dependencies') {
            steps {
                sh '''
                    apt-get update && apt-get install -y git
                    pip install codeql-wrapper
                '''
            }
        }
        
        stage('CodeQL Analysis') {
            steps {
                sh '''
                    codeql-wrapper analyze . \
                      --output-dir codeql-results \
                      --upload-sarif \
                      --verbose
                '''
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'codeql-results/**/*', allowEmptyArchive: true
        }
    }
}
```

## Harness CI/CD

### Pipeline YAML

```yaml
pipeline:
  name: CodeQL Security Analysis
  identifier: codeql_security_analysis
  projectIdentifier: your_project
  orgIdentifier: your_org
  tags: {}
  
  stages:
    - stage:
        name: Security Analysis
        identifier: security_analysis
        type: CI
        spec:
          cloneCodebase: true
          platform:
            os: Linux
            arch: Amd64
          runtime:
            type: Cloud
            spec: {}
          execution:
            steps:
              - step:
                  type: Run
                  name: Setup Environment
                  identifier: setup_environment
                  spec:
                    shell: Sh
                    command: |
                      python3 -m pip install --upgrade pip
                      pip install codeql-wrapper
              
              - step:
                  type: Run
                  name: Run CodeQL Analysis
                  identifier: run_codeql_analysis
                  spec:
                    shell: Sh
                    envVariables:
                      GITHUB_TOKEN: <+secrets.getValue("github_token")>
                    command: |
                      codeql-wrapper analyze /harness \
                        --output-dir codeql-results \
                        --upload-sarif \
                        --verbose
                  
              - step:
                  type: Run
                  name: Archive Results
                  identifier: archive_results
                  spec:
                    shell: Sh
                    command: |
                      tar -czf codeql-results.tar.gz codeql-results/
                      echo "CodeQL analysis completed"
                  when:
                    stageStatus: All
  
  properties:
    ci:
      codebase:
        connectorRef: <+input>
        repoName: <+input>
        build: <+input>
```

### Harness with Multi-Language Support

```yaml
pipeline:
  name: CodeQL Multi-Language Analysis
  identifier: codeql_multi_language
  
  stages:
    - stage:
        name: Security Analysis
        identifier: security_analysis
        type: CI
        spec:
          cloneCodebase: true
          execution:
            steps:
              - step:
                  type: Run
                  name: Install Dependencies
                  identifier: install_dependencies
                  spec:
                    shell: Sh
                    command: |
                      python3 -m pip install --upgrade pip
                      pip install codeql-wrapper
              
              - parallel:
                  - step:
                      type: Run
                      name: Analyze Python
                      identifier: analyze_python
                      spec:
                        shell: Sh
                        envVariables:
                          GITHUB_TOKEN: <+secrets.getValue("github_token")>
                        command: |
                          codeql-wrapper analyze /harness \
                            --languages python \
                            --output-dir codeql-results-python \
                            --verbose
                  
                  - step:
                      type: Run
                      name: Analyze JavaScript
                      identifier: analyze_javascript
                      spec:
                        shell: Sh
                        envVariables:
                          GITHUB_TOKEN: <+secrets.getValue("github_token")>
                        command: |
                          codeql-wrapper analyze /harness \
                            --languages javascript \
                            --output-dir codeql-results-js \
                            --verbose
              
              - step:
                  type: Run
                  name: Combine Results
                  identifier: combine_results
                  spec:
                    shell: Sh
                    command: |
                      mkdir -p combined-results
                      cp -r codeql-results-*/* combined-results/ || true
                      echo "Results combined successfully"
```

## GitLab CI

### `.gitlab-ci.yml`

```yaml
stages:
  - security

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
  PYTHON_VERSION: "3.12"

cache:
  paths:
    - .cache/pip/

codeql-analysis:
  stage: security
  image: python:${PYTHON_VERSION}
  before_script:
    - python -m pip install --upgrade pip
    - pip install codeql-wrapper
  script:
    - |
      codeql-wrapper analyze $CI_PROJECT_DIR \
        --output-dir codeql-results \
        --verbose
  artifacts:
    reports:
      sast: codeql-results/**/*.sarif
    paths:
      - codeql-results/
    expire_in: 1 week
    when: always
  only:
    - main
    - merge_requests
  allow_failure: true

# Separate job for uploading results to GitHub (if needed)
codeql-upload:
  stage: security
  image: python:${PYTHON_VERSION}
  dependencies:
    - codeql-analysis
  before_script:
    - pip install codeql-wrapper
  script:
    - |
      for sarif_file in codeql-results/**/*.sarif; do
        if [ -f "$sarif_file" ]; then
          codeql-wrapper upload-sarif "$sarif_file" --verbose
        fi
      done
  only:
    - main
  when: manual
  allow_failure: true
```

### GitLab CI with Docker-in-Docker

```yaml
codeql-analysis:
  stage: security
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - docker run --rm -v $PWD:/workspace -w /workspace python:3.12 /bin/bash -c "
        pip install codeql-wrapper &&
        codeql-wrapper analyze . --output-dir codeql-results --verbose
      "
  script:
    - echo "CodeQL analysis completed"
  artifacts:
    paths:
      - codeql-results/
    expire_in: 1 week
```

## Azure DevOps

### Azure Pipelines YAML

```yaml
trigger:
  branches:
    include:
      - main
      - develop

pool:
  vmImage: 'ubuntu-latest'

variables:
  pythonVersion: '3.12'
  outputDir: '$(Build.ArtifactStagingDirectory)/codeql-results'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '$(pythonVersion)'
  displayName: 'Use Python $(pythonVersion)'

- script: |
    python -m pip install --upgrade pip
    pip install codeql-wrapper
  displayName: 'Install CodeQL Wrapper'

- script: |
    codeql-wrapper analyze $(Build.SourcesDirectory) \
      --output-dir $(outputDir) \
      --verbose
  displayName: 'Run CodeQL Analysis'
  env:
    GITHUB_TOKEN: $(GITHUB_TOKEN)
  continueOnError: true

- task: PublishBuildArtifacts@1
  inputs:
    pathToPublish: '$(outputDir)'
    artifactName: 'codeql-results'
  displayName: 'Publish CodeQL Results'
  condition: always()

- task: PublishTestResults@2
  inputs:
    testResultsFormat: 'NUnit'
    testResultsFiles: '$(outputDir)/**/*.xml'
    failTaskOnFailedTests: false
  displayName: 'Publish Test Results'
  condition: always()
```

### Azure DevOps with Multiple Languages

```yaml
strategy:
  matrix:
    Python:
      language: 'python'
    JavaScript:
      language: 'javascript'
    Java:
      language: 'java'
    CSharp:
      language: 'csharp'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.12'

- script: |
    pip install codeql-wrapper
  displayName: 'Install CodeQL Wrapper'

- script: |
    codeql-wrapper analyze $(Build.SourcesDirectory) \
      --languages $(language) \
      --output-dir $(Build.ArtifactStagingDirectory)/codeql-results-$(language) \
      --verbose
  displayName: 'Run CodeQL Analysis for $(language)'
  env:
    GITHUB_TOKEN: $(GITHUB_TOKEN)
```

## CircleCI

### `.circleci/config.yml`

```yaml
version: 2.1

executors:
  python-executor:
    docker:
      - image: cimg/python:3.12
    working_directory: ~/project

jobs:
  codeql-analysis:
    executor: python-executor
    steps:
      - checkout
      - restore_cache:
          keys:
            - pip-cache-v1-{{ checksum "requirements.txt" }}
            - pip-cache-v1-
      - run:
          name: Install CodeQL Wrapper
          command: |
            python -m pip install --upgrade pip
            pip install codeql-wrapper
      - save_cache:
          key: pip-cache-v1-{{ checksum "requirements.txt" }}
          paths:
            - ~/.cache/pip
      - run:
          name: Run CodeQL Analysis
          command: |
            codeql-wrapper analyze . \
              --output-dir codeql-results \
              --upload-sarif \
              --verbose
          environment:
            GITHUB_TOKEN: $GITHUB_TOKEN
      - store_artifacts:
          path: codeql-results
          destination: codeql-results
      - store_test_results:
          path: codeql-results

workflows:
  security-analysis:
    jobs:
      - codeql-analysis:
          context: 
            - github-context
          filters:
            branches:
              only:
                - main
                - develop
```

### CircleCI with Matrix Strategy

```yaml
version: 2.1

executors:
  python-executor:
    docker:
      - image: cimg/python:3.12

jobs:
  codeql-analysis:
    executor: python-executor
    parameters:
      language:
        type: string
    steps:
      - checkout
      - run:
          name: Install CodeQL Wrapper
          command: pip install codeql-wrapper
      - run:
          name: Run CodeQL Analysis for << parameters.language >>
          command: |
            codeql-wrapper analyze . \
              --languages << parameters.language >> \
              --output-dir codeql-results-<< parameters.language >> \
              --verbose
          environment:
            GITHUB_TOKEN: $GITHUB_TOKEN
      - store_artifacts:
          path: codeql-results-<< parameters.language >>
          destination: codeql-results-<< parameters.language >>

workflows:
  security-analysis:
    jobs:
      - codeql-analysis:
          name: codeql-python
          language: python
          context: github-context
      - codeql-analysis:
          name: codeql-javascript
          language: javascript
          context: github-context
      - codeql-analysis:
          name: codeql-java
          language: java
          context: github-context
```

## Best Practices

### Security Configuration

1. **Token Management**
   - Use secure credential storage for GitHub tokens
   - Limit token permissions to `security-events` and `contents:read`
   - Use separate tokens for different repositories when needed
   - Rotate tokens regularly and monitor usage

2. **Repository Access**
   - Ensure CI/CD service accounts have minimal required permissions
   - Use repository-specific tokens rather than organization-wide tokens
   - Configure branch protection rules appropriately

3. **Secrets Management**
   ```yaml
   # GitHub Actions - Use repository or organization secrets
   env:
     GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
   
   # Jenkins - Use credentials plugin
   environment {
     GITHUB_TOKEN = credentials('github-token-id')
   }
   
   # GitLab CI - Use CI/CD variables
   variables:
     GITHUB_TOKEN: $GITHUB_TOKEN  # Set in GitLab CI/CD settings
   ```

### Performance Optimization

1. **Caching Strategies**
   - Cache CodeQL CLI installation between builds
   - Cache Python dependencies and virtual environments
   - Use build artifacts for subsequent stages

2. **Resource Management**
   - Allocate sufficient memory for large codebases (minimum 4GB recommended)
   - Use appropriate timeout values for different repository sizes
   - Consider using faster disk storage for temporary files

3. **Analysis Optimization**
   ```bash
   # Analyze specific languages only
   codeql-wrapper analyze . --languages python,javascript
   
   # Use monorepo mode for better performance on large repositories
   codeql-wrapper analyze . --monorepo
   
   # Force latest CodeQL version for performance improvements
   codeql-wrapper analyze . --force-install
   ```

### Error Handling and Monitoring

1. **Robust Pipeline Configuration**
   ```yaml
   # GitHub Actions - Continue on error but mark as failed
   - name: Run CodeQL Analysis
     run: codeql-wrapper analyze . --upload-sarif --verbose
     continue-on-error: true
     
   # Jenkins - Catch exceptions and set build status
   script {
     try {
       sh 'codeql-wrapper analyze . --upload-sarif --verbose'
     } catch (Exception e) {
       currentBuild.result = 'UNSTABLE'
       echo "CodeQL analysis failed: ${e.getMessage()}"
     }
   }
   ```

2. **Logging and Debugging**
   - Always use `--verbose` flag for detailed logging
   - Archive analysis results for debugging
   - Set up notifications for failed analyses

3. **Retry Logic**
   ```yaml
   # GitHub Actions - Retry on failure
   - name: Run CodeQL Analysis
     uses: nick-invision/retry@v2
     with:
       timeout_minutes: 60
       max_attempts: 3
       command: codeql-wrapper analyze . --upload-sarif --verbose
   ```

### Multi-Platform Support

1. **Cross-Platform Compatibility**
   ```yaml
   # Test on multiple operating systems
   strategy:
     matrix:
       os: [ubuntu-latest, windows-latest, macos-latest]
       python-version: ['3.8', '3.12']
   ```

2. **Container-Based Workflows**
   ```yaml
   # Use consistent container environment
   container:
     image: python:3.12-slim
     options: --user root
   ```

### Compliance and Governance

1. **Audit Trail**
   - Log all analysis attempts and results
   - Track which versions of CodeQL and wrapper are used
   - Monitor analysis coverage and success rates

2. **Policy Enforcement**
   - Require CodeQL analysis for all pull requests
   - Set up required status checks
   - Configure automatic security policy violations

3. **Reporting**
   - Generate analysis summary reports
   - Track metrics over time
   - Integrate with security dashboards

## Troubleshooting

### Common Issues and Solutions

1. **Authentication Problems**
   ```bash
   # Issue: GitHub token authentication failed
   # Solution: Verify token has security-events permission
   curl -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        https://api.github.com/user
   ```

2. **Memory Issues**
   ```bash
   # Issue: Out of memory during analysis
   # Solution: Increase available memory or analyze specific languages
   codeql-wrapper analyze . --languages python --verbose
   ```

3. **Network Connectivity**
   ```bash
   # Issue: Cannot download CodeQL CLI
   # Solution: Check firewall settings and proxy configuration
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080
   codeql-wrapper analyze . --force-install --verbose
   ```

4. **Git Repository Issues**
   ```bash
   # Issue: Cannot auto-detect repository information
   # Solution: Explicitly specify repository details
   codeql-wrapper analyze . \
     --upload-sarif \
     --repository owner/repo \
     --commit-sha $(git rev-parse HEAD) \
     --ref $(git rev-parse --abbrev-ref HEAD)
   ```

### Debug Mode

Enable comprehensive debugging:

```bash
# Enable maximum verbosity
codeql-wrapper analyze . --verbose 2>&1 | tee codeql-debug.log

# Check CodeQL installation
codeql-wrapper install --verbose

# Test SARIF upload separately
codeql-wrapper upload-sarif path/to/results.sarif --verbose
```

### Performance Monitoring

Monitor analysis performance:

```bash
# Time the analysis
time codeql-wrapper analyze . --verbose

# Monitor resource usage
/usr/bin/time -v codeql-wrapper analyze . --verbose

# Check disk usage
du -sh ~/.codeql codeql-results/
```

For additional support and advanced troubleshooting, check the [GitHub Issues](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/issues) page.
