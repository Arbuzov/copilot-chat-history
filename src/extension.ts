import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';

// Interface для данных чата
interface ChatSession {
    id: string;
    customTitle?: string;
    workspaceName: string;
    workspacePath?: string;
    lastModified: Date;
    filePath: string;
    messageCount: number;
}

interface WorkspaceGroup {
    workspaceName: string;
    workspacePath?: string;
    sessions: ChatSession[];
}

// Tree Data Provider для отображения истории чатов
class CopilotChatHistoryProvider implements vscode.TreeDataProvider<ChatSession | WorkspaceGroup> {
    private _onDidChangeTreeData: vscode.EventEmitter<ChatSession | WorkspaceGroup | undefined | null | void> = new vscode.EventEmitter<ChatSession | WorkspaceGroup | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<ChatSession | WorkspaceGroup | undefined | null | void> = this._onDidChangeTreeData.event;
    private _searchFilter: string = '';

    constructor() {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    setSearchFilter(filter: string): void {
        this._searchFilter = filter.toLowerCase();
        this.refresh();
    }

    clearFilter(): void {
        this._searchFilter = '';
        this.refresh();
    }

    private matchesFilter(session: ChatSession): boolean {
        if (!this._searchFilter) {
            return true;
        }
        
        const title = session.customTitle || 'Untitled Session';
        return title.toLowerCase().includes(this._searchFilter);
    }

    getTreeItem(element: ChatSession | WorkspaceGroup): vscode.TreeItem {
        if ('sessions' in element) {
            // Это группа workspace
            const item = new vscode.TreeItem(element.workspaceName, vscode.TreeItemCollapsibleState.Collapsed);
            item.iconPath = new vscode.ThemeIcon('folder');
            item.description = `${element.sessions.length} sessions`;
            item.contextValue = 'workspaceGroup';
            item.id = `workspace-${element.workspaceName}`;
            // Добавляем resourceUri если есть путь к workspace
            if (element.workspacePath) {
                item.resourceUri = vscode.Uri.file(element.workspacePath);
            }
            console.log('Created workspace TreeItem:', item.label, 'contextValue:', item.contextValue);
            return item;
        } else {
            // Это отдельная сессия чата
            const displayName = element.customTitle || element.id;
            const item = new vscode.TreeItem(displayName, vscode.TreeItemCollapsibleState.None);
            item.iconPath = new vscode.ThemeIcon('comment-discussion');
            item.description = `${element.messageCount} messages`;
            item.tooltip = `Last modified: ${element.lastModified.toLocaleString()}`;
            item.contextValue = 'chatSession';
            item.command = {
                command: 'copilotChatHistory.openChat',
                title: 'Open Chat',
                arguments: [element]
            };
            return item;
        }
    }

    getChildren(element?: ChatSession | WorkspaceGroup): Thenable<(ChatSession | WorkspaceGroup)[]> {
        if (!element) {
            // Root level - возвращаем группы workspace
            return Promise.resolve(this.getChatSessions());
        } else if ('sessions' in element) {
            // Возвращаем отфильтрованные сессии для данного workspace
            const filteredSessions = element.sessions.filter(session => this.matchesFilter(session));
            return Promise.resolve(filteredSessions);
        } else {
            // Leaf node - нет детей
            return Promise.resolve([]);
        }
    }

    private async getChatSessions(): Promise<WorkspaceGroup[]> {
        const chatSessions = await this.scanForChatSessions();
        
        // Группируем по workspace
        const workspaceMap = new Map<string, ChatSession[]>();
        
        chatSessions.forEach(session => {
            const existing = workspaceMap.get(session.workspaceName) || [];
            existing.push(session);
            workspaceMap.set(session.workspaceName, existing);
        });

        // Конвертируем в массив групп, исключая пустые после фильтрации
        const groups: WorkspaceGroup[] = [];
        workspaceMap.forEach((sessions, workspaceName) => {
            const filteredSessions = sessions.filter(session => this.matchesFilter(session));
            if (filteredSessions.length > 0) {
                // Берем workspacePath из первой сессии (все сессии в группе имеют одинаковый workspace)
                const workspacePath = sessions.length > 0 ? sessions[0].workspacePath : undefined;
                groups.push({
                    workspaceName,
                    workspacePath,
                    sessions: sessions.sort((a, b) => b.lastModified.getTime() - a.lastModified.getTime())
                });
            }
        });

        return groups.sort((a, b) => a.workspaceName.localeCompare(b.workspaceName));
    }

    private async scanForChatSessions(): Promise<ChatSession[]> {
        const sessions: ChatSession[] = [];
        
        try {
            const userDataPath = path.join(os.homedir(), 'AppData', 'Roaming', 'Code', 'User', 'workspaceStorage');
            
            if (!fs.existsSync(userDataPath)) {
                return sessions;
            }

            const workspaceDirs = fs.readdirSync(userDataPath, { withFileTypes: true })
                .filter(dirent => dirent.isDirectory())
                .map(dirent => dirent.name);

            for (const workspaceDir of workspaceDirs) {
                const chatSessionsPath = path.join(userDataPath, workspaceDir, 'chatSessions');
                
                if (fs.existsSync(chatSessionsPath)) {
                    const workspaceJsonPath = path.join(userDataPath, workspaceDir, 'workspace.json');
                    let workspaceName = workspaceDir.substring(0, 8) + '...'; // Default name
                    
                    // Попробуем получить имя workspace из файла
                    let workspacePath: string | undefined;
                    if (fs.existsSync(workspaceJsonPath)) {
                        try {
                            const workspaceData = JSON.parse(fs.readFileSync(workspaceJsonPath, 'utf8'));
                            if (workspaceData.folder) {
                                // Конвертируем URI в нормальный путь
                                workspacePath = this.uriToPath(workspaceData.folder);
                                if (workspacePath) {
                                    workspaceName = path.basename(workspacePath);
                                    console.log(`Found workspace from workspace.json: ${workspaceName} -> ${workspacePath}`);
                                }
                            }
                        } catch (error) {
                            console.error('Error reading workspace.json:', error);
                        }
                    }
                    
                    // Если не нашли путь в workspace.json, попробуем найти в recent workspaces
                    if (!workspacePath) {
                        workspacePath = await this.findWorkspaceInRecentList(workspaceName);
                        if (workspacePath) {
                            console.log(`Found workspace from recent list: ${workspaceName} -> ${workspacePath}`);
                        }
                    }
                    
                    // Если всё ещё не нашли, попробуем по названию найти в стандартных местах
                    if (!workspacePath) {
                        workspacePath = await this.searchWorkspaceByName(workspaceName);
                        if (workspacePath) {
                            console.log(`Found workspace by search: ${workspaceName} -> ${workspacePath}`);
                        } else {
                            console.log(`Could not find workspace path for: ${workspaceName}`);
                        }
                    }

                    const sessionFiles = fs.readdirSync(chatSessionsPath)
                        .filter(file => file.endsWith('.json'));

                    for (const sessionFile of sessionFiles) {
                        const sessionPath = path.join(chatSessionsPath, sessionFile);
                        const stats = fs.statSync(sessionPath);
                        
                        try {
                            const sessionData = JSON.parse(fs.readFileSync(sessionPath, 'utf8'));
                            const messageCount = sessionData.requests ? sessionData.requests.length : 0;
                            
                            // Пропускаем сессии без requests или с пустым массивом requests
                            if (!sessionData.requests || sessionData.requests.length === 0) {
                                continue;
                            }
                            
                            let customTitle = sessionData.customTitle;
                            
                            // Если нет customTitle, берем первое сообщение из requests
                            if (!customTitle && sessionData.requests && sessionData.requests.length > 0) {
                                const firstRequest = sessionData.requests[0];
                                if (firstRequest && firstRequest.message && firstRequest.message.text) {
                                    // Обрезаем длинные сообщения и убираем переносы строк
                                    customTitle = firstRequest.message.text
                                        .replace(/\n/g, ' ')
                                        .trim()
                                        .substring(0, 50);
                                    if (firstRequest.message.text.length > 50) {
                                        customTitle += '...';
                                    }
                                }
                            }
                            
                            sessions.push({
                                id: path.basename(sessionFile, '.json'),
                                customTitle,
                                workspaceName,
                                workspacePath,
                                lastModified: stats.mtime,
                                filePath: sessionPath,
                                messageCount
                            });
                        } catch (error) {
                            console.error(`Error reading session file ${sessionPath}:`, error);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Error scanning chat sessions:', error);
        }

        return sessions;
    }

    private uriToPath(uri: string): string {
        try {
            // Если это URI, конвертируем в путь
            if (uri.startsWith('file://')) {
                return vscode.Uri.parse(uri).fsPath;
            }
            // Если это уже путь, возвращаем как есть
            return uri;
        } catch (error) {
            console.error('Error converting URI to path:', error);
            return uri;
        }
    }

    private async findWorkspaceInRecentList(workspaceName: string): Promise<string | undefined> {
        try {
            // Попробуем найти в recent workspaces VS Code
            const userDataPath = path.join(os.homedir(), 'AppData', 'Roaming', 'Code', 'User');
            const recentWorkspacesPath = path.join(userDataPath, 'globalStorage', 'state.vscdb');
            
            // VS Code хранит recent workspaces в разных местах, попробуем основные
            const possiblePaths = [
                path.join(userDataPath, 'workspaceStorage'),
                path.join(userDataPath, 'globalStorage'),
            ];
            
            // Поищем в текущих открытых workspaces VS Code
            if (vscode.workspace.workspaceFolders) {
                for (const folder of vscode.workspace.workspaceFolders) {
                    if (path.basename(folder.uri.fsPath) === workspaceName || 
                        folder.name === workspaceName) {
                        return folder.uri.fsPath;
                    }
                }
            }
            
        } catch (error) {
            console.error('Error searching in recent workspaces:', error);
        }
        return undefined;
    }

    public async searchWorkspaceByName(workspaceName: string): Promise<string | undefined> {
        try {
            // Поищем в стандартных местах разработки
            const searchPaths = [
                path.join(os.homedir(), 'Documents'),
                path.join(os.homedir(), 'Documents', 'git'),
                path.join(os.homedir(), 'Projects'),
                path.join(os.homedir(), 'Development'),
                path.join('C:', 'Projects'),
                path.join('C:', 'Dev'),
                path.join('C:', 'Source'),
            ];

            for (const searchPath of searchPaths) {
                if (fs.existsSync(searchPath)) {
                    try {
                        const items = fs.readdirSync(searchPath, { withFileTypes: true });
                        for (const item of items) {
                            if (item.isDirectory() && item.name === workspaceName) {
                                const fullPath = path.join(searchPath, item.name);
                                // Проверим, что это действительно проект (есть хотя бы один из стандартных файлов)
                                const projectFiles = ['.git', '.vscode', 'package.json', '.gitignore', 'README.md'];
                                for (const projectFile of projectFiles) {
                                    if (fs.existsSync(path.join(fullPath, projectFile))) {
                                        return fullPath;
                                    }
                                }
                            }
                        }
                    } catch (error) {
                        // Игнорируем ошибки доступа к папкам
                        continue;
                    }
                }
            }
        } catch (error) {
            console.error('Error searching workspace by name:', error);
        }
        return undefined;
    }
}

// Интерфейсы для структуры чата
interface ChatMessage {
    message: {
        text: string;
    };
    response: Array<{
        value: string;
    }>;
    timestamp?: number;
}

interface ChatSessionData {
    version: number;
    requesterUsername: string;
    responderUsername: string;
    requests: ChatMessage[];
    customTitle?: string;
    creationDate?: number;
    lastMessageDate?: number;
}

// Функция для открытия чата в webview
function openChatInWebview(session: ChatSession, context: vscode.ExtensionContext) {
    try {
        // Читаем данные сессии
        if (!fs.existsSync(session.filePath)) {
            vscode.window.showErrorMessage(`Chat session file not found: ${session.filePath}`);
            return;
        }

        const sessionData: ChatSessionData = JSON.parse(fs.readFileSync(session.filePath, 'utf8'));
        
        // Создаем webview panel
        const panel = vscode.window.createWebviewPanel(
            'copilotChatViewer',
            session.customTitle || `Chat Session ${session.id}`,
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                enableForms: false,
                localResourceRoots: [context.extensionUri]
            }
        );

        // Генерируем HTML контент
        panel.webview.html = generateChatHTML(sessionData, session);

    } catch (error) {
        console.error('Error opening chat in webview:', error);
        vscode.window.showErrorMessage(`Error opening chat: ${error}`);
    }
}

// Функция для генерации HTML контента чата
function generateChatHTML(sessionData: ChatSessionData, session: ChatSession): string {
    const messages = sessionData.requests || [];
    
    let messagesHtml = '';
    
    messages.forEach((request, index) => {
        // Сообщение пользователя
        if (request.message && request.message.text) {
            messagesHtml += `
                <div class="message user-message">
                    <div class="message-header">
                        <div class="avatar user-avatar">👤</div>
                        <div class="username">${sessionData.requesterUsername || 'User'}</div>
                    </div>
                    <div class="message-content">${escapeHtml(request.message.text)}</div>
                </div>
            `;
        }
        
        // Ответ Copilot
        if (request.response && request.response.length > 0) {
            const responseText = request.response.map(r => r.value).join('\n');
            messagesHtml += `
                <div class="message copilot-message">
                    <div class="message-header">
                        <div class="avatar copilot-avatar">🤖</div>
                        <div class="username">${sessionData.responderUsername || 'GitHub Copilot'}</div>
                    </div>
                    <div class="message-content">${formatCodeContent(responseText)}</div>
                </div>
            `;
        }
    });

    return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Chat Session</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: var(--vscode-editor-background);
                    color: var(--vscode-editor-foreground);
                    line-height: 1.6;
                }
                
                .chat-container {
                    max-width: 800px;
                    margin: 0 auto;
                }
                
                .chat-header {
                    border-bottom: 1px solid var(--vscode-panel-border);
                    padding-bottom: 15px;
                    margin-bottom: 20px;
                }
                
                .chat-title {
                    font-size: 1.4em;
                    font-weight: 600;
                    margin: 0 0 5px 0;
                }
                
                .chat-meta {
                    color: var(--vscode-descriptionForeground);
                    font-size: 0.9em;
                }
                
                .message {
                    margin-bottom: 20px;
                    padding: 15px;
                    border-radius: 8px;
                    border: 1px solid var(--vscode-panel-border);
                }
                
                .user-message {
                    background-color: var(--vscode-input-background);
                    border-left: 4px solid var(--vscode-charts-blue);
                }
                
                .copilot-message {
                    background-color: var(--vscode-textBlockQuote-background);
                    border-left: 4px solid var(--vscode-charts-green);
                }
                
                .message-header {
                    display: flex;
                    align-items: center;
                    margin-bottom: 10px;
                }
                
                .avatar {
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-right: 8px;
                    font-size: 14px;
                }
                
                .user-avatar {
                    background-color: var(--vscode-charts-blue);
                }
                
                .copilot-avatar {
                    background-color: var(--vscode-charts-green);
                }
                
                .username {
                    font-weight: 600;
                    font-size: 0.9em;
                }
                
                .message-content {
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }
                
                .message-content h1, .message-content h2, .message-content h3 {
                    margin: 10px 0;
                    color: var(--vscode-editor-foreground);
                }
                
                .message-content h1 { font-size: 1.3em; }
                .message-content h2 { font-size: 1.2em; }
                .message-content h3 { font-size: 1.1em; }
                
                .message-content p {
                    margin: 8px 0;
                }
                
                .message-content ul {
                    margin: 8px 0;
                    padding-left: 20px;
                }
                
                .message-content li {
                    margin: 4px 0;
                }
                
                .message-content strong {
                    font-weight: 600;
                }
                
                .message-content em {
                    font-style: italic;
                    color: var(--vscode-descriptionForeground);
                }
                
                .message-content pre {
                    background-color: var(--vscode-textPreformat-background);
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 4px;
                    padding: 12px;
                    overflow-x: auto;
                    margin: 10px 0;
                    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
                }
                
                .message-content code {
                    background-color: var(--vscode-textPreformat-background);
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
                    font-size: 0.9em;
                }
                
                .empty-chat {
                    text-align: center;
                    color: var(--vscode-descriptionForeground);
                    padding: 40px;
                    font-style: italic;
                }
            </style>
        </head>
        <body>
            <div class="chat-container">
                <div class="chat-header">
                    <h1 class="chat-title">${escapeHtml(session.customTitle || 'Chat Session')}</h1>
                    <div class="chat-meta">
                        Workspace: ${escapeHtml(session.workspaceName)} • 
                        Messages: ${messages.length} • 
                        Last modified: ${session.lastModified.toLocaleString()}
                    </div>
                </div>
                
                <div class="messages">
                    ${messages.length > 0 ? messagesHtml : '<div class="empty-chat">No messages in this chat session</div>'}
                </div>
            </div>
        </body>
        </html>
    `;
}

// Вспомогательные функции
function escapeHtml(text: string): string {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function formatCodeContent(text: string): string {
    // Простое форматирование для кода и markdown
    let formatted = escapeHtml(text);
    
    // Блоки кода с языком
    formatted = formatted.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre><code class="language-${lang}">${code.trim()}</code></pre>`;
    });
    
    // Inline код
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Жирный текст
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Курсив
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Заголовки
    formatted = formatted.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    formatted = formatted.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    formatted = formatted.replace(/^# (.*$)/gm, '<h1>$1</h1>');
    
    // Списки
    formatted = formatted.replace(/^[\s]*[-*] (.*$)/gm, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
    
    // Переносы строк
    formatted = formatted.replace(/\n\n/g, '</p><p>');
    formatted = '<p>' + formatted + '</p>';
    
    return formatted;
}

export function activate(context: vscode.ExtensionContext) {
    // Создаем провайдер данных
    const chatHistoryProvider = new CopilotChatHistoryProvider();
    
    // Регистрируем tree view
    vscode.window.createTreeView('copilotChatHistoryView', {
        treeDataProvider: chatHistoryProvider,
        showCollapseAll: true
    });

    // Регистрируем команды
    const refreshCommand = vscode.commands.registerCommand('copilotChatHistory.refresh', () => {
        chatHistoryProvider.refresh();
    });

    const openChatCommand = vscode.commands.registerCommand('copilotChatHistory.openChat', (session: ChatSession) => {
        // Открываем чат в специальном webview вместо JSON файла
        openChatInWebview(session, context);
    });

    const openChatJsonCommand = vscode.commands.registerCommand('copilotChatHistory.openChatJson', (session: ChatSession) => {
        // Открываем JSON файл сессии чата
        if (fs.existsSync(session.filePath)) {
            vscode.workspace.openTextDocument(session.filePath).then(doc => {
                vscode.window.showTextDocument(doc);
            });
        } else {
            vscode.window.showErrorMessage(`Chat session file not found: ${session.filePath}`);
        }
    });

    const helloWorldCommand = vscode.commands.registerCommand('copilotChatHistory.helloWorld', () => {
        vscode.window.showInformationMessage('Hello World from Copilot Chat History extension!');
    });

    const searchCommand = vscode.commands.registerCommand('copilotChatHistory.search', async () => {
        const searchText = await vscode.window.showInputBox({
            placeHolder: 'Enter search text...',
            prompt: 'Search chat sessions by title'
        });
        
        if (searchText !== undefined) {
            chatHistoryProvider.setSearchFilter(searchText);
            if (searchText.trim()) {
                vscode.window.showInformationMessage(`Filtered by: "${searchText}"`);
            }
        }
    });

    const clearFilterCommand = vscode.commands.registerCommand('copilotChatHistory.clearFilter', () => {
        chatHistoryProvider.clearFilter();
        vscode.window.showInformationMessage('Filter cleared');
    });

    const openWorkspaceInCurrentWindowCommand = vscode.commands.registerCommand('copilotChatHistory.openWorkspaceInCurrentWindow', async (workspaceGroup: WorkspaceGroup) => {
        console.log('Opening workspace:', workspaceGroup.workspaceName, 'Path:', workspaceGroup.workspacePath);
        
        if (workspaceGroup.workspacePath) {
            // Убеждаемся, что путь конвертирован из URI
            const normalizedPath = workspaceGroup.workspacePath.startsWith('file://') 
                ? vscode.Uri.parse(workspaceGroup.workspacePath).fsPath 
                : workspaceGroup.workspacePath;
                
            if (fs.existsSync(normalizedPath)) {
                const workspaceUri = vscode.Uri.file(normalizedPath);
                await vscode.commands.executeCommand('vscode.openFolder', workspaceUri, false);
            } else {
                vscode.window.showErrorMessage(`Workspace path does not exist: ${normalizedPath}`);
            }
        } else {
            // Попробуем найти workspace вручную
            const foundPath = await chatHistoryProvider.searchWorkspaceByName(workspaceGroup.workspaceName);
            if (foundPath && fs.existsSync(foundPath)) {
                const workspaceUri = vscode.Uri.file(foundPath);
                await vscode.commands.executeCommand('vscode.openFolder', workspaceUri, false);
                vscode.window.showInformationMessage(`Found and opened workspace: ${foundPath}`);
            } else {
                vscode.window.showErrorMessage(`Workspace path not found for: ${workspaceGroup.workspaceName}. Please open it manually.`);
            }
        }
    });

    const openWorkspaceInNewWindowCommand = vscode.commands.registerCommand('copilotChatHistory.openWorkspaceInNewWindow', async (workspaceGroup: WorkspaceGroup) => {
        console.log('Opening workspace in new window:', workspaceGroup.workspaceName, 'Path:', workspaceGroup.workspacePath);
        
        if (workspaceGroup.workspacePath) {
            // Убеждаемся, что путь конвертирован из URI
            const normalizedPath = workspaceGroup.workspacePath.startsWith('file://') 
                ? vscode.Uri.parse(workspaceGroup.workspacePath).fsPath 
                : workspaceGroup.workspacePath;
                
            if (fs.existsSync(normalizedPath)) {
                const workspaceUri = vscode.Uri.file(normalizedPath);
                await vscode.commands.executeCommand('vscode.openFolder', workspaceUri, true);
            } else {
                vscode.window.showErrorMessage(`Workspace path does not exist: ${normalizedPath}`);
            }
        } else {
            // Попробуем найти workspace вручную
            const foundPath = await chatHistoryProvider.searchWorkspaceByName(workspaceGroup.workspaceName);
            if (foundPath && fs.existsSync(foundPath)) {
                const workspaceUri = vscode.Uri.file(foundPath);
                await vscode.commands.executeCommand('vscode.openFolder', workspaceUri, true);
                vscode.window.showInformationMessage(`Found and opened workspace: ${foundPath}`);
            } else {
                vscode.window.showErrorMessage(`Workspace path not found for: ${workspaceGroup.workspaceName}. Please open it manually.`);
            }
        }
    });

    context.subscriptions.push(refreshCommand, openChatCommand, openChatJsonCommand, helloWorldCommand, searchCommand, clearFilterCommand, openWorkspaceInCurrentWindowCommand, openWorkspaceInNewWindowCommand);

    // Автоматически обновляем при активации
    chatHistoryProvider.refresh();
    
    // Показываем сообщение о том, что расширение активировано
    console.log('Copilot Chat History extension is now active!');
}

export function deactivate() {}
