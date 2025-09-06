# Change Log

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