# Testing Guide

This document provides comprehensive information about the testing infrastructure for the AI Inscription App.

## Table of Contents

- [Overview](#overview)
- [Setting Up](#setting-up)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Writing Tests](#writing-tests)
- [Continuous Integration](#continuous-integration)

## Overview

The AI Inscription App uses pytest as its testing framework. The test suite includes:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test how components work together
- **52 total tests** covering core functionality

### Test Coverage

The test suite covers:

- ✅ Configuration management (loading, saving, updating)
- ✅ File operations (loading, Unicode support, error handling)
- ✅ Response parsing (with/without tags, edge cases)
- ✅ Error handling (missing API key, file errors, network issues)
- ✅ Custom prompts and examples
- ✅ Batch file processing
- ✅ Output file naming and collision handling
- ✅ Leiden Convention and EpiDoc validation

## Setting Up

### Install Test Dependencies

```bash
# Using pip
pip install -e ".[test]"

# Or if using uv
uv sync --extra test
```

### Test Dependencies

- `pytest>=8.0.0` - Testing framework
- `pytest-cov>=4.1.0` - Coverage reporting
- `pytest-mock>=3.12.0` - Mocking utilities

## Running Tests

### Basic Usage

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with detailed output on failures
pytest -vv
```

### Using the Test Script

```bash
# Run all tests
./run_tests.sh

# Run only unit tests
./run_tests.sh --unit

# Run only integration tests
./run_tests.sh --integration

# Run with coverage report
./run_tests.sh --coverage

# Run with verbose output
./run_tests.sh --verbose
```

### Running Specific Tests

```bash
# Run a specific test file
pytest tests/test_converter.py

# Run a specific test class
pytest tests/test_converter.py::TestLeidenToEpiDocConverter

# Run a specific test method
pytest tests/test_converter.py::TestLeidenToEpiDocConverter::test_parse_response_with_all_tags

# Run tests matching a pattern
pytest -k "parse_response"
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# Open the report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Generate terminal coverage report
pytest --cov=. --cov-report=term

# Generate XML coverage report (for CI)
pytest --cov=. --cov-report=xml
```

## Test Structure

### Directory Layout

```
tests/
├── __init__.py              # Test package marker
├── conftest.py              # Shared fixtures and configuration
├── test_converter.py        # Tests for LeidenToEpiDocConverter
├── test_file_item.py        # Tests for FileItem class
├── test_prompts.py          # Tests for prompts module
└── test_integration.py      # Integration tests
```

### Test Files

#### `test_converter.py`
Tests for the core converter class:
- Configuration loading/saving
- Response parsing with different tag combinations
- Error handling (missing API key, API failures)
- Custom prompt/examples functionality
- Regex pattern validation

#### `test_file_item.py`
Tests for file handling:
- File initialization
- Content loading (success and failure cases)
- Unicode and multilingual text support
- Empty and large file handling
- Conversion state tracking

#### `test_prompts.py`
Tests for the prompt system:
- System instruction validation
- Examples structure verification
- Leiden Convention coverage
- EpiDoc tag coverage
- Content length validation

#### `test_integration.py`
End-to-end workflow tests:
- Complete conversion workflows
- Configuration update workflows
- Custom prompt/examples workflows
- File naming and collision handling
- Batch processing

### Fixtures

Common fixtures are defined in `conftest.py`:

- `temp_config_file` - Temporary configuration file
- `sample_leiden_text` - Sample Leiden convention text
- `sample_epidoc_response` - Sample AI response with tags
- `sample_epidoc_response_no_tags` - Sample response without tags
- `sample_file_content` - Sample text file
- `mock_anthropic_client` - Mocked Anthropic API client
- `mock_anthropic_response` - Mocked API response

## Writing Tests

### Test Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Example Test

```python
import pytest

@pytest.mark.unit
class TestMyFeature:
    """Test suite for my feature."""
    
    def test_basic_functionality(self):
        """Test that basic functionality works."""
        # Arrange
        input_data = "test input"
        
        # Act
        result = my_function(input_data)
        
        # Assert
        assert result == "expected output"
    
    def test_error_handling(self):
        """Test that errors are handled correctly."""
        with pytest.raises(ValueError):
            my_function(None)
```

### Using Fixtures

```python
def test_with_fixture(sample_leiden_text):
    """Test using a fixture."""
    assert len(sample_leiden_text) > 0
    assert "[" in sample_leiden_text  # Leiden conventions use brackets
```

### Test Markers

Tests can be marked with custom markers:

```python
@pytest.mark.unit
def test_unit_functionality():
    """Unit test."""
    pass

@pytest.mark.integration
def test_integration_workflow():
    """Integration test."""
    pass

@pytest.mark.gui
def test_gui_component():
    """GUI test (requires Qt)."""
    pass
```

Run tests by marker:
```bash
pytest -m unit           # Run only unit tests
pytest -m integration    # Run only integration tests
pytest -m "not gui"      # Run all except GUI tests
```

### Best Practices

1. **One concept per test**: Each test should verify one specific behavior
2. **Clear test names**: Use descriptive names that explain what is being tested
3. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification
4. **Use fixtures**: Share setup code using pytest fixtures
5. **Test edge cases**: Include tests for boundary conditions and error cases
6. **Keep tests fast**: Mock external dependencies to keep tests fast
7. **Independent tests**: Tests should not depend on each other

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

The CI workflow:
1. Sets up Python 3.12
2. Installs dependencies
3. Runs all tests
4. Generates coverage report
5. Uploads coverage to Codecov (if configured)

### Workflow File

See `.github/workflows/test.yml` for the complete CI configuration.

### Local CI Simulation

To simulate CI locally:

```bash
# Install dependencies
pip install -e ".[test]"

# Run tests like CI
pytest tests/ -v --tb=short

# Generate coverage
pytest tests/ --cov=. --cov-report=xml
```

## Troubleshooting

### Tests Fail to Import Modules

Make sure you've installed the package in development mode:
```bash
pip install -e .
pip install -e ".[test]"
```

### Qt Import Errors

The test suite mocks Qt to avoid requiring a display. If you see Qt-related errors:
1. Ensure `pytest-qt` is NOT installed (it's in optional `test-gui` dependencies)
2. Run tests with: `pytest -p no:qt`

### Coverage Shows Low Numbers

The test suite focuses on core logic rather than GUI code. To see coverage for specific modules:
```bash
pytest --cov=leiden_prompts --cov-report=term
```

## Future Enhancements

Potential testing improvements:

- [ ] GUI component tests (requires pytest-qt and display server)
- [ ] Performance benchmarks
- [ ] Mock API response validation
- [ ] Snapshot testing for EpiDoc output
- [ ] Property-based testing with Hypothesis
- [ ] Visual regression testing for UI

## Contributing

When contributing code:

1. Write tests for new features
2. Ensure all tests pass: `pytest`
3. Maintain or improve coverage: `pytest --cov`
4. Follow existing test patterns
5. Update this documentation if adding new test categories

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [pytest markers](https://docs.pytest.org/en/stable/mark.html)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
