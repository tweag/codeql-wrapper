#!/bin/bash

# Script to automatically determine the next release version
# Location: .github/workflows/scripts/get_next_release_version.sh
# Usage: ./.github/workflows/scripts/get_next_release_version.sh [patch|minor|major]
# 
# This script:
# 1. Gets the latest release version from PyPI
# 2. Determines the next version based on increment type
# 3. Validates against existing tags
# 4. Outputs the new version information
#
# Outputs (via GitHub Actions output format):
# - new_version: The new release version to use (e.g., "0.2.0")
# - current_version: The current latest version
# - increment_type: The type of increment applied
# - is_initial_release: Whether this is the first release

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
PACKAGE_NAME="codeql-wrapper"

# Get increment type from command line argument (default to patch)
INCREMENT_TYPE="${1:-patch}"

# Validate increment type
if [[ ! "$INCREMENT_TYPE" =~ ^(patch|minor|major)$ ]]; then
  echo "Invalid increment type: $INCREMENT_TYPE"
  echo "Valid options: patch, minor, major"
  exit 1
fi

echo "Increment type: $INCREMENT_TYPE"
echo "Getting latest release version from PyPI..."

# Get the latest release version from PyPI API
LATEST_RELEASE_VERSION=""
if PYPI_DATA=$(curl -s -f "https://pypi.org/pypi/${PACKAGE_NAME}/json" 2>/dev/null); then
  LATEST_RELEASE_VERSION=$(echo "$PYPI_DATA" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('info', {}).get('version', ''))" 2>/dev/null || echo "")
  if [ -n "$LATEST_RELEASE_VERSION" ]; then
    echo "Found latest version from PyPI: $LATEST_RELEASE_VERSION"
  fi
fi

# If no release found, check git tags for latest semantic version
if [ -z "$LATEST_RELEASE_VERSION" ]; then
  echo "No PyPI releases found, checking git tags..."
  
  # Get all tags that look like semantic versions (v1.2.3 or 1.2.3)
  if command -v git >/dev/null 2>&1; then
    LATEST_TAG=$(git tag -l | grep -E '^v?[0-9]+\.[0-9]+\.[0-9]+$' | sed 's/^v//' | sort -V | tail -n 1 || echo "")
    if [ -n "$LATEST_TAG" ]; then
      LATEST_RELEASE_VERSION="$LATEST_TAG"
      echo "Found latest version from git tags: $LATEST_RELEASE_VERSION"
    fi
  fi
fi

# If still no version found, start with 0.1.0
if [ -z "$LATEST_RELEASE_VERSION" ]; then
  echo "No existing versions found, starting with initial release"
  NEW_VERSION="0.1.0"
  IS_INITIAL_RELEASE="true"
  CURRENT_VERSION="none"
else
  echo "Current latest version: $LATEST_RELEASE_VERSION"
  IS_INITIAL_RELEASE="false"
  CURRENT_VERSION="$LATEST_RELEASE_VERSION"
  
  # Parse the semantic version
  if [[ "$LATEST_RELEASE_VERSION" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
    MAJOR="${BASH_REMATCH[1]}"
    MINOR="${BASH_REMATCH[2]}"
    PATCH="${BASH_REMATCH[3]}"
    
    echo "Parsed version - Major: $MAJOR, Minor: $MINOR, Patch: $PATCH"
    
    # Calculate new version based on increment type
    case "$INCREMENT_TYPE" in
      "major")
        NEW_MAJOR=$((MAJOR + 1))
        NEW_VERSION="${NEW_MAJOR}.0.0"
        ;;
      "minor")
        NEW_MINOR=$((MINOR + 1))
        NEW_VERSION="${MAJOR}.${NEW_MINOR}.0"
        ;;
      "patch")
        NEW_PATCH=$((PATCH + 1))
        NEW_VERSION="${MAJOR}.${MINOR}.${NEW_PATCH}"
        ;;
    esac
  else
    echo "Invalid semantic version format: $LATEST_RELEASE_VERSION"
    echo "Expected format: MAJOR.MINOR.PATCH"
    exit 1
  fi
fi

echo "New version will be: $NEW_VERSION"

# Check if the new version already exists as a tag
if command -v git >/dev/null 2>&1; then
  if git tag -l | grep -q "^v\?${NEW_VERSION}$"; then
    echo "Error: Version $NEW_VERSION already exists as a git tag"
    exit 1
  fi
fi

# Set outputs for GitHub Actions (if running in GitHub Actions)
if [ -n "${GITHUB_OUTPUT:-}" ]; then
  echo "new_version=$NEW_VERSION" >> "$GITHUB_OUTPUT"
  echo "current_version=$CURRENT_VERSION" >> "$GITHUB_OUTPUT"
  echo "increment_type=$INCREMENT_TYPE" >> "$GITHUB_OUTPUT"
  echo "is_initial_release=$IS_INITIAL_RELEASE" >> "$GITHUB_OUTPUT"
  echo "GitHub Actions outputs set."
else
  echo "Not running in GitHub Actions - outputs:"
  echo "  new_version=$NEW_VERSION"
  echo "  current_version=$CURRENT_VERSION"
  echo "  increment_type=$INCREMENT_TYPE"
  echo "  is_initial_release=$IS_INITIAL_RELEASE"
fi

echo "Version determination completed successfully."
