# Copilot Chat History

A Visual Studio Code extension that helps you view and manage your GitHub Copilot chat history organized by workspace.

## 🎨 Enhanced Chat Display (v1.1.0)

The extension now features a completely redesigned chat renderer that closely matches the official VS Code Copilot Chat interface:

### ✨ New Features
- **Authentic VS Code Styling**: CSS styles based on the official VS Code Copilot Chat repository
- **Professional Icons**: SVG icons for user and Copilot avatars instead of emoji
- **Advanced Markdown Support**: 
  - Four-backtick code blocks (like official Copilot)
  - Better formatting for lists, quotes, links, and tables
  - Proper syntax highlighting integration
- **Responsive Design**: Optimized for different screen sizes
- **Theme Integration**: Full VS Code theme support with proper color variables

### 🎯 Improved User Experience
- Native look and feel matching VS Code's design language
- Better typography and spacing
- Enhanced readability with proper contrast ratios
- Professional message layout with improved avatars

## Features

- 📁 **Workspace Organization**: Chat sessions grouped by workspace for easy navigation
- 🔍 **Search & Filter**: Quickly find specific chat sessions by title or content
- 🔗 **Quick Access**: Open workspaces directly from chat history with inline buttons
- 📝 **Smart Titles**: Automatically generates meaningful titles from chat content
- 🌲 **Tree View**: Clean, collapsible interface in the Activity Bar
- ⚡ **Fast Performance**: Efficient scanning and caching of chat data

## Installation

### From VS Code Marketplace

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "Copilot Chat History"
4. Click Install

### From GitHub Releases

1. Download the latest `.vsix` file from [Releases](https://github.com/your-username/copilot-chat-history/releases)
2. Open VS Code
3. Go to Extensions (Ctrl+Shift+X)
4. Click the "..." menu and select "Install from VSIX..."
5. Select the downloaded file

## Usage

### Viewing Chat History

1. Look for the "Copilot Chat History" icon in the Activity Bar (left sidebar)
2. Click to open the panel
3. Browse your chat sessions organized by workspace
4. Expand/collapse workspaces as needed

### Search and Filter

- Click the search icon (🔍) in the panel header
- Enter keywords to filter chat sessions
- Use the clear filter button (🗑️) to reset

### Opening Workspaces

- Use the inline arrow buttons next to workspace names:
  - **→** Open workspace in current window
  - **↗** Open workspace in new window

### Refreshing

- Click the refresh button (🔄) to reload chat history
- Automatically scans for new chat sessions

## How it Works

The extension scans your VS Code workspace storage for Copilot chat sessions:

- **Location**: `%APPDATA%\Code\User\workspaceStorage\[workspace-id]\chatSessions\`
- **Grouping**: Sessions are grouped by their associated workspace
- **Titles**: Uses custom titles or generates them from first message
- **Paths**: Resolves workspace paths from stored configuration

## Requirements

- Visual Studio Code 1.103.0 or higher
- GitHub Copilot extension (for generating chat sessions)

## Extension Settings

This extension contributes the following settings:

Currently, no additional settings are required. The extension works out of the box.

## Known Issues

- Workspace paths may not resolve correctly if projects have been moved
- Search is case-insensitive and searches in session titles only
- Large numbers of chat sessions may impact performance

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Clone this repository
2. Run `npm install` to install dependencies
3. Press `F5` to open a new Extension Development Host window
4. Test your changes

### Building and Packaging

```bash
# Development commands
npm run compile          # Compile TypeScript
npm run watch           # Watch for changes
npm run package         # Build for production

# Create installable package
npm run package:vsix     # Creates .vsix file for installation

# Publishing (requires tokens)
npm run publish:vsce     # Publish to VS Code Marketplace
npm run publish:ovsx     # Publish to Open VSX Registry
npm run publish:both     # Publish to both marketplaces
```

### Local Testing

1. Build VSIX package: `npm run package:vsix`
2. Install locally: `code --install-extension copilot-chat-history-1.0.3.vsix`
3. Reload VS Code and test functionality

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### 1.0.0

- Initial release
- Workspace-based chat organization
- Search and filter functionality
- Inline workspace opening buttons
- Smart title generation

---

**Enjoy managing your Copilot chat history!** 🚀

## Support

If you encounter any issues or have feature requests, please file them in the [GitHub Issues](https://github.com/your-username/copilot-chat-history/issues).
