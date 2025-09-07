# Changelog

All notable changes to the "copilot-chat-history" extension will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-09-06

### ✨ Enhanced Chat Renderer

- **Authentic VS Code Styling**: Updated webview chat renderer with authentic CSS styles based on the official VS Code Copilot Chat repository
- **Professional Icons**: Replaced emoji avatars with professional SVG icons matching VS Code's design language
- **Improved Message Layout**: Restructured message layout to match official VS Code chat interface
- **Better Typography**: Enhanced font rendering and sizing for improved readability
- **Advanced Markdown Support**: 
  - Support for four-backtick code blocks (like official Copilot)
  - Improved inline code formatting
  - Better list and quote handling
  - Link detection and formatting
  - Proper table rendering
- **Responsive Design**: Added mobile-friendly responsive breakpoints
- **Theme Integration**: Full integration with VS Code color themes

### 🎨 Visual Improvements

- **Native Look & Feel**: Chat display now closely matches the official VS Code Copilot Chat interface
- **Proper Spacing**: Adjusted margins, padding, and line heights to match VS Code standards
- **Color Consistency**: All colors now use VS Code's CSS variables for perfect theme integration
- **Avatar Redesign**: Professional user and Copilot icons instead of emoji
- **Message Bubbles**: Cleaner message container styling with proper borders and backgrounds

### 🐛 Bug Fixes

- Fixed markdown formatting edge cases
- Improved code block language detection
- Better handling of special characters in content
- Fixed responsive design issues on smaller screens

## [1.0.1] - 2025-09-06

### Fixed
- Updated Node.js version requirement to 20.x for compatibility with latest vsce and dependencies
- Fixed CI/CD pipeline to use @vscode/vsce instead of deprecated vsce package
- Updated GitHub Actions to use modern actions (softprops/action-gh-release@v1)

## [1.0.0] - 2025-09-06 Log

All notable changes to the "Copilot Chat History" extension will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-06

### Added
- Initial release of Copilot Chat History extension
- Workspace-based organization of Copilot chat sessions
- Tree view in Activity Bar for easy navigation
- Search and filter functionality for chat sessions
- Inline buttons for opening workspaces (current/new window)
- Smart title generation from chat content
- Automatic workspace path resolution
- Support for collapsed/expanded workspace groups
- Refresh functionality to reload chat data

### Features
- **Chat Organization**: Groups chat sessions by workspace for better organization
- **Search**: Filter chat sessions by title with case-insensitive search
- **Workspace Navigation**: Direct workspace opening from chat history
- **Smart Titles**: Automatically generates meaningful titles from first message if no custom title exists
- **Performance**: Efficient scanning of VS Code workspace storage
- **User Experience**: Clean, intuitive tree interface

### Technical Details
- Compatible with VS Code 1.103.0+
- TypeScript implementation with full type safety
- Efficient file system scanning and caching
- URI path resolution for cross-platform compatibility
- Error handling for missing or moved workspaces

## [Unreleased]

### Planned Features
- Export chat history to various formats
- Advanced search with content filtering
- Chat session tagging and categories
- Statistics and insights
- Backup and restore functionality