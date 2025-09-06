# Contributing to Copilot Chat History

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

- Node.js 18.x or higher
- Visual Studio Code 1.103.0 or higher
- Git

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/copilot-chat-history.git
   cd copilot-chat-history
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Build the project**
   ```bash
   npm run compile
   ```

4. **Run in development mode**
   - Press `F5` in VS Code to open Extension Development Host
   - The extension will be loaded and ready for testing

## Development Workflow

### Building

- `npm run compile` - Compile TypeScript and bundle with esbuild
- `npm run watch` - Watch for changes and auto-rebuild
- `npm run package` - Build production version

### Testing

- `npm test` - Run all tests
- `npm run lint` - Run ESLint
- `npm run check-types` - Run TypeScript type checking

### Package Management

- `npm run vsce:package` - Create VSIX package
- `npm run vsce:publish` - Publish to VS Code Marketplace
- `npm run ovsx:publish` - Publish to Open VSX Registry

## Project Structure

```
copilot-chat-history/
├── src/
│   └── extension.ts          # Main extension code
├── resources/
│   ├── icon.png             # Extension icon (128x128)
│   └── icon.svg             # Source SVG icon
├── .github/
│   └── workflows/           # GitHub Actions
├── dist/                    # Compiled output
├── package.json             # Extension manifest
├── README.md               # User documentation
├── CHANGELOG.md            # Version history
└── LICENSE                 # MIT License
```

## Code Guidelines

### TypeScript

- Use strict TypeScript configuration
- Prefer explicit types over `any`
- Use async/await over Promises
- Follow VS Code API patterns

### Code Style

- Use ESLint configuration provided
- 2-space indentation
- Single quotes for strings
- Trailing commas in multiline objects

### Naming Conventions

- Use camelCase for variables and functions
- Use PascalCase for classes and interfaces
- Use UPPER_CASE for constants
- Use descriptive names

## VS Code Extension Guidelines

### Performance

- Minimize startup time
- Use lazy loading where possible
- Cache expensive operations
- Handle errors gracefully

### User Experience

- Provide clear error messages
- Use consistent icons and naming
- Follow VS Code UI patterns
- Support keyboard navigation

### API Usage

- Use stable VS Code APIs only
- Handle API deprecations
- Test across VS Code versions
- Follow extension best practices

## Testing

### Test Types

- Unit tests for core functionality
- Integration tests for VS Code API
- Manual testing in Extension Development Host

### Test Guidelines

- Write tests for new features
- Test error conditions
- Verify cross-platform compatibility
- Test with different workspace configurations

## Publishing

### Pre-release Checklist

- [ ] Update version in `package.json`
- [ ] Update `CHANGELOG.md`
- [ ] Run all tests
- [ ] Test in Extension Development Host
- [ ] Verify package contents with `vsce package`

### Release Process

1. Create and push version tag: `git tag v1.0.0 && git push origin v1.0.0`
2. GitHub Actions will automatically:
   - Run tests
   - Build package
   - Publish to VS Code Marketplace
   - Publish to Open VSX Registry
   - Create GitHub Release

### Manual Publishing

If needed, you can publish manually:

```bash
# Install tools
npm install -g @vscode/vsce ovsx

# Package
vsce package

# Publish to VS Code Marketplace
vsce publish -p <token>

# Publish to Open VSX
ovsx publish -p <token>
```

## Issue Reporting

### Bug Reports

Please include:
- VS Code version
- Extension version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Console errors (if any)

### Feature Requests

Please describe:
- Use case and motivation
- Proposed solution
- Alternative solutions considered
- Implementation ideas (optional)

## Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/my-feature`
3. **Make** your changes
4. **Test** thoroughly
5. **Commit** with clear messages
6. **Push** to your fork
7. **Create** a pull request

### PR Requirements

- [ ] Tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG.md updated
- [ ] No breaking changes (unless major version)

## Getting Help

- Check existing issues on GitHub
- Read VS Code extension documentation
- Ask questions in discussions
- Contact maintainers

Thank you for contributing! 🚀
