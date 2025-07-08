#!/usr/bin/env python3
"""Test script to verify error handling in CodeQL installer."""

from unittest.mock import patch
from urllib.error import URLError

from codeql_wrapper.infrastructure.codeql_installer import CodeQLInstaller

def test_get_latest_version_exception():
    """Test that get_latest_version raises proper exceptions."""
    installer = CodeQLInstaller()
    
    # Test with network error
    with patch("codeql_wrapper.infrastructure.codeql_installer.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = URLError("Network error")
        
        try:
            installer.get_latest_version()
            print("❌ FAIL: Expected exception but none was raised")
            return False
        except Exception as e:
            if "Unable to fetch latest CodeQL version" in str(e):
                print("✅ PASS: Correct exception raised for network error")
            else:
                print(f"❌ FAIL: Wrong exception message: {e}")
                return False
    
    # Test with HTTP error
    from unittest.mock import Mock
    with patch("codeql_wrapper.infrastructure.codeql_installer.urlopen") as mock_urlopen:
        mock_response = Mock()
        mock_response.status = 404
        mock_urlopen.return_value.__enter__ = Mock(return_value=mock_response)
        mock_urlopen.return_value.__exit__ = Mock(return_value=None)
        
        try:
            installer.get_latest_version()
            print("❌ FAIL: Expected exception but none was raised")
            return False
        except Exception as e:
            if "GitHub API returned status 404" in str(e):
                print("✅ PASS: Correct exception raised for HTTP error")
            else:
                print(f"❌ FAIL: Wrong exception message: {e}")
                return False
    
    return True

def test_install_propagates_exception():
    """Test that install() propagates exceptions correctly."""
    installer = CodeQLInstaller()
    
    # Test with network error during version fetch
    with patch("codeql_wrapper.infrastructure.codeql_installer.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = URLError("Network error")
        
        try:
            installer.install(version=None)  # This should trigger get_latest_version
            print("❌ FAIL: Expected exception but none was raised")
            return False
        except Exception as e:
            if "Unable to fetch latest CodeQL version" in str(e):
                print("✅ PASS: Install correctly propagates version fetch exception")
            else:
                print(f"❌ FAIL: Wrong exception message: {e}")
                return False
    
    return True

def main():
    """Run all tests."""
    print("Testing CodeQL installer error handling...")
    
    tests = [
        test_get_latest_version_exception,
        test_install_propagates_exception,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{total} tests passed")
    return passed == total

if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
