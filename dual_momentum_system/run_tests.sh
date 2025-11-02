#!/bin/bash
# Test runner script for the Dual Momentum Framework

echo "=========================================="
echo "Dual Momentum Framework - Test Suite"
echo "=========================================="
echo ""

# Ensure the script runs from the dual_momentum_system directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Run pytest with coverage (use python module to avoid PATH issues on CI)
echo "Running tests with coverage..."
echo ""

PYTEST_CMD=(python3 -m pytest tests/ \
    --verbose \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html \
    --tb=short)

"${PYTEST_CMD[@]}"

TEST_EXIT_CODE=$?

echo ""
echo "=========================================="

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Coverage report generated in: htmlcov/index.html"
else
    echo -e "${RED}✗ Some tests failed${NC}"
fi

echo "=========================================="

exit $TEST_EXIT_CODE
