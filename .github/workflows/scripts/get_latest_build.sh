#!/bin/bash

# Script to get the latest build version from TestPyPI and create a new build version
# Location: .github/workflows/scripts/get_latest_build.sh
# Usage: ./.github/workflows/scripts/get_latest_build.sh
# 
# This script:
# 1. Gets the base version from pyproject.toml
# 2. Queries TestPyPI for existing build versions
# 3. Determines the next build number
# 4. Outputs the new version and build information
#
# Outputs (via GitHub Actions output format):
# - new_version: The new build version to use (e.g., "0.1.12.dev3")
# - latest_build_number: The build number for the new version
# - latest_build_filename: The filename of the most recent build (if any)
# - build_count: Total number of existing builds for this base version

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
PACKAGE="codeql-wrapper"

# Get base version from pyproject.toml
RAW_VERSION=$(poetry version --short)
echo "Detected raw version from pyproject.toml: $RAW_VERSION"

# Extract base version (remove any existing .dev suffix)
if [[ "$RAW_VERSION" =~ ^([0-9]+\.[0-9]+\.[0-9]+)(\.dev[0-9]+)?$ ]]; then
  BASE_VERSION="${BASH_REMATCH[1]}"
  echo "Extracted base version: $BASE_VERSION"
else
  echo "Error: Invalid version format in pyproject.toml: $RAW_VERSION"
  echo "Expected format: MAJOR.MINOR.PATCH or MAJOR.MINOR.PATCH.devN"
  exit 1
fi
echo "Looking for existing builds of $PACKAGE with pattern ${BASE_VERSION}.dev* on TestPyPI..."

# Query TestPyPI JSON API for the package with error handling
JSON_URL="https://test.pypi.org/pypi/${PACKAGE}/json"
echo "Querying TestPyPI API: $JSON_URL"

if ! RESPONSE=$(curl -s -f "$JSON_URL" 2>/dev/null); then
  echo "Failed to query TestPyPI API or package not found"
  NEW_VERSION="${BASE_VERSION}.dev1"
  
  # Set outputs for GitHub Actions (if running in GitHub Actions)
  if [ -n "${GITHUB_OUTPUT:-}" ]; then
    echo "new_version=$NEW_VERSION" >> "$GITHUB_OUTPUT"
    echo "latest_build_number=1" >> "$GITHUB_OUTPUT"
    echo "latest_build_filename=" >> "$GITHUB_OUTPUT"
    echo "build_count=0" >> "$GITHUB_OUTPUT"
  else
    echo "Not running in GitHub Actions - outputs:"
    echo "  new_version=$NEW_VERSION"
    echo "  latest_build_number=1"
    echo "  latest_build_filename="
    echo "  build_count=0"
  fi
  exit 0
fi

# Extract all release versions from the package
ALL_VERSIONS=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); [print(v) for v in data.get('releases', {}).keys()]" 2>/dev/null || echo "")

if [ -z "$ALL_VERSIONS" ]; then
  echo "No versions found for $PACKAGE on TestPyPI."
  NEW_VERSION="${BASE_VERSION}.dev1"
  
  # Set outputs for GitHub Actions (if running in GitHub Actions)
  if [ -n "${GITHUB_OUTPUT:-}" ]; then
    echo "new_version=$NEW_VERSION" >> "$GITHUB_OUTPUT"
    echo "latest_build_number=1" >> "$GITHUB_OUTPUT"
    echo "latest_build_filename=" >> "$GITHUB_OUTPUT"
    echo "build_count=0" >> "$GITHUB_OUTPUT"
  else
    echo "Not running in GitHub Actions - outputs:"
    echo "  new_version=$NEW_VERSION"
    echo "  latest_build_number=1"
    echo "  latest_build_filename="
    echo "  build_count=0"
  fi
  exit 0
fi

echo "All versions found for $PACKAGE on TestPyPI:"
echo "$ALL_VERSIONS"

# Filter versions that match our base version with build pattern: {BASE_VERSION}.dev{N}
BUILD_VERSIONS=$(echo "$ALL_VERSIONS" | grep "^${BASE_VERSION}\.dev" | sort -V || echo "")

if [ -z "$BUILD_VERSIONS" ]; then
  echo "No build versions found for base version $BASE_VERSION."
  NEW_VERSION="${BASE_VERSION}.dev1"
  BUILD_NUMBER=1
  BUILD_COUNT=0
  LATEST_BUILD_FILENAME=""
else
  echo "Build versions found for $BASE_VERSION:"
  echo "$BUILD_VERSIONS"
  
  # Extract build numbers from versions using a more compatible approach
  BUILD_NUMBERS=""
  for version in $BUILD_VERSIONS; do
    if [[ "$version" =~ ^${BASE_VERSION}\.dev([0-9]+)$ ]]; then
      BUILD_NUMBERS="$BUILD_NUMBERS ${BASH_REMATCH[1]}"
    fi
  done
  BUILD_NUMBERS=$(echo $BUILD_NUMBERS | tr ' ' '\n' | sort -n)
  
  if [ -n "$BUILD_NUMBERS" ]; then
    LATEST_BUILD_NUMBER=$(echo "$BUILD_NUMBERS" | tail -n 1)
    BUILD_NUMBER=$((LATEST_BUILD_NUMBER + 1))
    echo "Found build numbers: $(echo $BUILD_NUMBERS | tr '\n' ' ')"
    echo "Latest build number: $LATEST_BUILD_NUMBER"
  else
    BUILD_NUMBER=1
    echo "Could not extract build numbers, starting with 1"
  fi
  
  NEW_VERSION="${BASE_VERSION}.dev${BUILD_NUMBER}"
  BUILD_COUNT=$(echo "$BUILD_VERSIONS" | wc -l | xargs)
  
  # Get the latest build version and its filename
  LATEST_BUILD_VERSION=$(echo "$BUILD_VERSIONS" | tail -n 1)
  LATEST_BUILD_FILES=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); [print(f['filename']) for f in data.get('releases', {}).get(\"$LATEST_BUILD_VERSION\", [])]" 2>/dev/null || echo "")
  LATEST_BUILD_FILENAME=$(echo "$LATEST_BUILD_FILES" | tail -n 1)
fi

echo "New version will be: $NEW_VERSION"
echo "Build number: $BUILD_NUMBER"
echo "Latest build filename: $LATEST_BUILD_FILENAME"

# Set outputs for GitHub Actions (if running in GitHub Actions)
if [ -n "${GITHUB_OUTPUT:-}" ]; then
  echo "new_version=$NEW_VERSION" >> "$GITHUB_OUTPUT"
  echo "latest_build_number=$BUILD_NUMBER" >> "$GITHUB_OUTPUT"
  echo "latest_build_filename=$LATEST_BUILD_FILENAME" >> "$GITHUB_OUTPUT"
  echo "build_count=$BUILD_COUNT" >> "$GITHUB_OUTPUT"
  echo "GitHub Actions outputs set."
else
  echo "Not running in GitHub Actions - outputs:"
  echo "  new_version=$NEW_VERSION"
  echo "  latest_build_number=$BUILD_NUMBER"
  echo "  latest_build_filename=$LATEST_BUILD_FILENAME"
  echo "  build_count=$BUILD_COUNT"
fi

echo "Build version detection completed successfully."
