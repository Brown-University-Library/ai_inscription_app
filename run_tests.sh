#!/bin/bash
# Script to run tests with various options

set -e

echo "Running AI Inscription App Tests"
echo "================================="
echo ""

# Function to show usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -a, --all        Run all tests (default)"
    echo "  -u, --unit       Run only unit tests"
    echo "  -i, --integration Run only integration tests"
    echo "  -c, --coverage   Run tests with coverage report"
    echo "  -v, --verbose    Run tests with verbose output"
    echo "  -h, --help       Show this help message"
    echo ""
    exit 0
}

# Default options
MARKERS=""
VERBOSE=""
COVERAGE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--all)
            MARKERS=""
            shift
            ;;
        -u|--unit)
            MARKERS="-m unit"
            shift
            ;;
        -i|--integration)
            MARKERS="-m integration"
            shift
            ;;
        -c|--coverage)
            COVERAGE="--cov=. --cov-report=html --cov-report=term"
            shift
            ;;
        -v|--verbose)
            VERBOSE="-vv"
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Run pytest with the specified options
echo "Running: pytest tests/ $MARKERS $VERBOSE $COVERAGE"
echo ""
python3 -m pytest tests/ $MARKERS $VERBOSE $COVERAGE

# If coverage was run, show report location
if [[ -n "$COVERAGE" ]]; then
    echo ""
    echo "Coverage report generated in htmlcov/index.html"
fi
