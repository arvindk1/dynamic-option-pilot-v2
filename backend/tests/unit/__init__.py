"""
Unit tests for individual components and functions.

Test Structure:
- test_models/ - Database model tests
- test_services/ - Business logic tests  
- test_api/ - API endpoint tests
- test_utils/ - Utility function tests
- test_plugins/ - Plugin system tests
"""

import os
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Test configuration
TEST_DATABASE_URL = "sqlite:///./test.db"
TEST_ENVIRONMENT = "testing"