# Contributing to Flexberry MarkItDown MCP

Thank you for your interest in contributing to the Flexberry MarkItDown MCP project! This document contains instructions for contributing to the project.

## Contribution Rules

We welcome contributions from everyone! To make the process of making changes as simple and efficient as possible, please follow these recommendations.

## How to Start

1. **Fork the repository** - Click the "Fork" button on GitHub to create a copy of the repository in your account.

2. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_GITHUB_USERNAME/flexberry-markitdown-mcp.git
   cd flexberry-markitdown-mcp
   ```

3. **Create a branch for your feature or fix**:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-fix-name
   ```

## Code Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code.
- Use meaningful variable and function names.
- Add comments where necessary, especially for complex logic.

## Submitting Changes

1. **Check your code** - Make sure your code passes all tests:
   ```bash
   pytest
   ```

2. **Commit** - Commits should be clear and contain a description of changes:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

3. **Push changes**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a Pull Request** - Go to GitHub and create a Pull Request from your branch to the `main` branch of the main repository.

## Commit Message Conventions

We use commit message conventions:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code formatting changes (spaces, indentation, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or modifying tests
- `chore:` - Project maintenance (dependency updates, etc.)

Example:
```
feat: added PDF conversion support
fix: fixed Cyrillic character handling issue
docs: updated README with new instructions
```

## Bug Reports

If you find a bug, please create an issue on GitHub including:

1. Brief description of the bug
2. Steps to reproduce
3. Expected behavior
4. Actual behavior
5. Environment (OS, Python version, etc.)
6. Logs or screenshots if applicable

## Questions and Suggestions

If you have questions or suggestions, please create an issue on GitHub with the label `question` or `enhancement`.

## License

By contributing, you agree that your changes will be licensed under the same license as the project (MIT).

Thank you for your contribution!
