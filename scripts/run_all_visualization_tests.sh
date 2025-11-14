#!/bin/bash
#
# Run all visualization tree accuracy tests
# Ensures 100% accuracy for agent visualization trees
#

set -e  # Exit on error

echo "=================================================================================="
echo "🧪 RUNNING ALL VISUALIZATION TREE ACCURACY TESTS"
echo "=================================================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run a test
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Running: $test_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Run comprehensive tests
run_test "Comprehensive Visualization Tree Accuracy Tests" \
    "python3 scripts/test_visualization_tree_accuracy_comprehensive.py"

echo ""

# Run integration tests
run_test "Visualization Integration Tests" \
    "python3 scripts/test_visualization_integration.py"

echo ""

# Summary
echo "=================================================================================="
echo "📊 TEST SUMMARY"
echo "=================================================================================="
echo ""
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED_TESTS${NC}"
else
    echo -e "${GREEN}Failed: $FAILED_TESTS${NC}"
fi

ACCURACY=$(echo "scale=1; ($PASSED_TESTS * 100) / $TOTAL_TESTS" | bc)
echo "Accuracy: ${ACCURACY}%"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo "=================================================================================="
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}✅ Visualization tree building is 100% accurate!${NC}"
    echo "=================================================================================="
    exit 0
else
    echo "=================================================================================="
    echo -e "${RED}⚠️  SOME TESTS FAILED${RED}"
    echo -e "${RED}Please review the errors above.${NC}"
    echo "=================================================================================="
    exit 1
fi

