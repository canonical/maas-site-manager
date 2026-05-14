# AI Coding Agent Guidelines

This document provides guidelines for AI coding agents (such as GitHub Copilot, Cursor, Cline, etc.) working on the MAAS Site Manager project. These rules help ensure consistency, quality, and security across the codebase.

## Table of Contents

- [General Principles](#general-principles)
- [Backend Guidelines](#backend-guidelines)
- [Frontend Guidelines](#frontend-guidelines)
- [Security Requirements](#security-requirements)
- [Documentation Standards](#documentation-standards)
- [Collaboration Practices](#collaboration-practices)

## General Principles

- Prefer clear, descriptive variable and function names
- Avoid abbreviations unless they are widely understood
- Write code that is modular and testable
- Prefer explicit over implicit code
- Follow the project's established patterns and idioms
- Suggest refactoring when code duplication is detected
- Avoid generating large boilerplate unless explicitly requested

## Backend Guidelines

**Scope:** All code within the `backend/` directory

### Code Style & Quality

- **Follow PEP8** for Python code style and formatting
- **Use type hints** for all function signatures
- **Write docstrings** for all public functions, classes, and modules
- **Handle exceptions gracefully** and log errors where appropriate
- **Validate and sanitize** all user inputs
- **Use parameterized queries** for database access
- **Write unit tests** for new features and bug fixes

### Tooling & Workflow

Execute all formatting, linting, and testing commands from the `backend/` directory:

```bash
# Format code
tox -e format

# Run linters
tox -e lint

# Run static checkers
tox -e check

# Run all unit tests
tox -e test-unit

# Run specific unit test file
tox -e test-unit -- $file

# Run full test suite with coverage report
tox -e test

# Pass additional pytest arguments after the -- separator
tox -e test-unit -- -v -k test_specific_function
```

### Security Best Practices

- **Never suggest hardcoded credentials, secrets, or tokens**
- **Use environment variables** for secrets and configuration
- Avoid use of deprecated or insecure libraries
- Ensure compatibility with the current Python version in use

### Documentation

- Update relevant documentation with every code or API change
- Ensure README and inline comments are kept up to date
- Reference related issues and link to documentation in pull requests

## Frontend Guidelines

**Scope:** All code within the `frontend/` directory

*Frontend-specific guidelines will be populated as the frontend development standards are established.*

## Security Requirements

Across all parts of the codebase:

- Never hardcode credentials, secrets, or tokens
- Validate and sanitize all user inputs
- Use parameterized queries for database access
- Avoid deprecated or insecure libraries
- Follow security best practices for the specific technology stack

## Documentation Standards

- Maintain up-to-date inline comments for complex logic
- Update README files when functionality changes
- Document API changes immediately
- Keep architecture documentation synchronized with code changes

## Collaboration Practices

- Follow the project's code review and pull request process
- Tag relevant team members for specialized reviews
- Reference related issues in commits and pull requests
- Link to relevant documentation when making architectural changes
- Ensure code is compatible with the project's current dependency versions
