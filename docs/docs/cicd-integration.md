---
sidebar_position: 4
---

# CI/CD Integration

CodeQL Wrapper is designed to work seamlessly with various CI/CD platforms. This guide shows how to integrate it into your pipelines.

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
        codeql-wrapper analyze $GITHUB_WORKSPACE \
          --upload-sarif \
          --repository ${{ github.repository }} \
          --commit-sha ${{ github.sha }} \
          --ref ${{ github.ref }}
```

### Monorepo Workflow

For monorepos:

```yaml
    - name: Run CodeQL Analysis (Monorepo)
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        codeql-wrapper analyze $GITHUB_WORKSPACE \
          --monorepo \
          --upload-sarif \
          --repository ${{ github.repository }} \
          --commit-sha ${{ github.sha }} \
          --ref ${{ github.ref }}
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
        codeql-wrapper analyze $GITHUB_WORKSPACE \
          --languages ${{ matrix.language }} \
          --upload-sarif
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
                sh '''
                    codeql-wrapper analyze ${WORKSPACE} \
                      --monorepo \
                      --verbose \
                      --upload-sarif \
                      --repository owner/repository \
                      --commit-sha ${GIT_COMMIT} \
                      --ref ${GIT_BRANCH}
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

### Scripted Pipeline

```groovy
node {
    try {
        stage('Checkout') {
            checkout scm
        }
        
        stage('Install Dependencies') {
            sh 'pip3 install codeql-wrapper'
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
        throw e
    } finally {
        archiveArtifacts artifacts: 'codeql-results/**/*', allowEmptyArchive: true
    }
}
```

## Harness

### Pipeline YAML

```yaml
pipeline:
  name: CodeQL Analysis
  identifier: codeql_analysis
  projectIdentifier: your_project
  orgIdentifier: your_org
  
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
                  name: Install CodeQL Wrapper
                  identifier: install_codeql_wrapper
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
                        --languages java,python \
                        --upload-sarif \
                        --repository owner/repository \
                        --commit-sha <+codebase.commitSha> \
                        --ref <+codebase.branch>
          
          platform:
            os: Linux
            arch: Amd64
          
          runtime:
            type: Cloud
            spec: {}
```

## GitLab CI

### `.gitlab-ci.yml`

```yaml
stages:
  - security

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip/

codeql-analysis:
  stage: security
  image: python:3.11
  before_script:
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
  only:
    - main
    - merge_requests
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
  pythonVersion: '3.11'

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
      --output-dir $(Build.ArtifactStagingDirectory)/codeql-results \
      --verbose
  displayName: 'Run CodeQL Analysis'
  env:
    GITHUB_TOKEN: $(GITHUB_TOKEN)

- task: PublishBuildArtifacts@1
  inputs:
    pathToPublish: '$(Build.ArtifactStagingDirectory)/codeql-results'
    artifactName: 'codeql-results'
  displayName: 'Publish CodeQL Results'
```

## CircleCI

### `.circleci/config.yml`

```yaml
version: 2.1

jobs:
  codeql-analysis:
    docker:
      - image: python:3.11
    steps:
      - checkout
      - run:
          name: Install CodeQL Wrapper
          command: |
            pip install codeql-wrapper
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

workflows:
  security-analysis:
    jobs:
      - codeql-analysis:
          context: github-context
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
4. **Implement retry logic** for network-related failures

### Example with Error Handling

```yaml
- name: Run CodeQL Analysis with Retry
  run: |
    for attempt in 1 2 3; do
      if codeql-wrapper analyze . --upload-sarif --verbose; then
        echo "Analysis successful on attempt $attempt"
        break
      else
        echo "Analysis failed on attempt $attempt"
        if [ $attempt -eq 3 ]; then
          echo "All attempts failed"
          exit 1
        fi
        sleep 30
      fi
    done
```

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
