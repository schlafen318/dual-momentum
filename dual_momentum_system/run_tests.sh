#!/bin/bash
# Test runner script for the Dual Momentum Framework

echo "=========================================="
echo "Dual Momentum Framework - Test Suite"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Run pytest with coverage
echo "Running tests with coverage..."
echo ""

pytest tests/ \
    --verbose \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html \
    --tb=short

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
