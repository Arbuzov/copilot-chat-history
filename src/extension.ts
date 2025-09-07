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
                    <div class="avatar user-avatar">
                        <svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" fill="currentColor">
                            <path d="M16 7.992C16 3.58 12.416 0 8 0S0 3.58 0 7.992c0 2.43 1.104 4.62 2.832 6.09.016.016.032.016.032.032.144.112.288.224.448.336.08.048.144.111.224.175A7.98 7.98 0 0 0 8.016 16a7.98 7.98 0 0 0 4.48-1.375c.08-.048.144-.111.224-.16.144-.111.304-.223.448-.335.016-.016.032-.016.032-.032 1.696-1.487 2.8-3.676 2.8-6.106zm-8 7.001c-1.504 0-2.88-.48-4.016-1.279.016-.128.048-.255.08-.383a4.17 4.17 0 0 1 .416-.991c.176-.304.384-.576.64-.816.24-.24.528-.463.816-.639.304-.176.624-.304.976-.4A4.15 4.15 0 0 1 8 10.342a4.185 4.185 0 0 1 2.928 1.166c.368.368.656.8.864 1.295.112.288.192.592.24.911A7.03 7.03 0 0 1 8 15.993zm4.928-2.272A5.03 5.03 0 0 0 8 9.297c-1.311 0-2.513.541-3.584 1.406-.08-.48-.336-.927-.65-1.25a2.97 2.97 0 0 0-.88-.687 3.99 3.99 0 0 1-.04-5.483c.48-.48 1.072-.816 1.712-1.02C4.9 2.034 5.472 1.917 6.08 1.917a3.99 3.99 0 0 1 3.904 3.304c.016.111.048.209.048.329 0 .662-.336 1.243-.864 1.59-.528.346-.864.927-.864 1.589 0 .662.336 1.243.864 1.59.528.346.864.927.864 1.589z"/>
                        </svg>
                    </div>
                    <div class="message-body">
                        <div class="message-header">
                            <div class="username">${sessionData.requesterUsername || 'User'}</div>
                        </div>
                        <div class="message-content">${escapeHtml(request.message.text)}</div>
                    </div>
                </div>
            `;
        }
        
        // Ответ Copilot
        if (request.response && request.response.length > 0) {
            const responseText = request.response.map(r => r.value).join('\n');
            messagesHtml += `
                <div class="message copilot-message">
                    <div class="avatar copilot-avatar">
                        <svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" fill="currentColor">
                            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
                        </svg>
                    </div>
                    <div class="message-body">
                        <div class="message-header">
                            <div class="username">${sessionData.responderUsername || 'GitHub Copilot'}</div>
                        </div>
                        <div class="message-content">${formatCodeContent(responseText)}</div>
                    </div>
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
                /* Базовые стили, основанные на официальном VS Code Copilot Chat */
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                    margin: 0;
                    padding: 16px;
                    background-color: var(--vscode-editor-background);
                    color: var(--vscode-editor-foreground);
                    line-height: 1.4;
                    font-size: 13px;
                }
                
                .chat-container {
                    max-width: 900px;
                    margin: 0 auto;
                }
                
                .chat-header {
                    border-bottom: 1px solid var(--vscode-panel-border);
                    padding-bottom: 12px;
                    margin-bottom: 16px;
                }
                
                .chat-title {
                    font-size: 16px;
                    font-weight: 600;
                    margin: 0 0 4px 0;
                    color: var(--vscode-editor-foreground);
                }
                
                .chat-meta {
                    color: var(--vscode-descriptionForeground);
                    font-size: 11px;
                }
                
                /* Стили сообщений, основанные на .interactive-item-container */
                .message {
                    display: flex;
                    margin-bottom: 16px;
                    padding: 8px 16px;
                    gap: 8px;
                    border-radius: 3px;
                    position: relative;
                }
                
                .user-message {
                    background-color: transparent;
                }
                
                .copilot-message {
                    background-color: var(--vscode-chat-requestBackground, transparent);
                }
                
                /* Стили для аватаров, основанные на .header .avatar */
                .avatar {
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                    margin-top: 1px;
                    font-size: 12px;
                    outline: 1px solid var(--vscode-contrastBorder, transparent);
                    outline-offset: -1px;
                }
                
                .user-avatar {
                    background-color: var(--vscode-testing-iconPassed);
                    color: var(--vscode-button-foreground);
                }
                
                .copilot-avatar {
                    background-color: var(--vscode-button-secondaryBackground);
                    color: var(--vscode-button-secondaryForeground);
                }
                
                /* Контент сообщения */
                .message-body {
                    flex: 1;
                    min-width: 0;
                }
                
                .message-header {
                    display: flex;
                    align-items: center;
                    margin-bottom: 4px;
                    gap: 6px;
                }
                
                .username {
                    font-weight: 600;
                    font-size: 11px;
                    color: var(--vscode-editor-foreground);
                }
                
                /* Стили контента, основанные на .chatMessageContent */
                .message-content {
                    color: var(--vscode-editor-foreground);
                    font-size: 13px;
                    line-height: 1.4;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    -webkit-user-select: text;
                    user-select: text;
                }
                
                /* Markdown стили */
                .message-content h1, .message-content h2, .message-content h3 {
                    margin: 16px 0 8px 0;
                    color: var(--vscode-editor-foreground);
                    font-weight: 600;
                }
                
                .message-content h1 { font-size: 18px; }
                .message-content h2 { font-size: 16px; }
                .message-content h3 { font-size: 14px; }
                
                .message-content p {
                    margin: 8px 0;
                }
                
                .message-content ul, .message-content ol {
                    margin: 8px 0;
                    padding-left: 20px;
                }
                
                .message-content li {
                    margin: 2px 0;
                }
                
                .message-content strong {
                    font-weight: 600;
                }
                
                .message-content em {
                    font-style: italic;
                }
                
                /* Код блоки, стили основанные на VS Code */
                .message-content pre {
                    background-color: var(--vscode-textCodeBlock-background);
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 3px;
                    padding: 8px 12px;
                    margin: 8px 0;
                    overflow-x: auto;
                    font-family: var(--vscode-editor-font-family, 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace);
                    font-size: 12px;
                    line-height: 1.357;
                }
                
                .message-content code {
                    background-color: var(--vscode-textPreformat-background);
                    color: var(--vscode-textPreformat-foreground);
                    padding: 1px 3px;
                    border-radius: 3px;
                    font-family: var(--vscode-editor-font-family, 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace);
                    font-size: 12px;
                }
                
                .message-content pre code {
                    background: transparent;
                    padding: 0;
                    color: var(--vscode-editor-foreground);
                }
                
                /* Блок цитат */
                .message-content blockquote {
                    margin: 8px 0;
                    padding: 0 12px;
                    border-left: 4px solid var(--vscode-textBlockQuote-border);
                    background-color: var(--vscode-textBlockQuote-background);
                    color: var(--vscode-textBlockQuote-foreground);
                }
                
                /* Таблицы */
                .message-content table {
                    border-collapse: collapse;
                    margin: 8px 0;
                    width: 100%;
                }
                
                .message-content th, .message-content td {
                    border: 1px solid var(--vscode-panel-border);
                    padding: 6px 8px;
                    text-align: left;
                }
                
                .message-content th {
                    background-color: var(--vscode-keybindingTable-headerBackground);
                    font-weight: 600;
                }
                
                /* Ссылки */
                .message-content a {
                    color: var(--vscode-textLink-foreground);
                    text-decoration: none;
                }
                
                .message-content a:hover {
                    color: var(--vscode-textLink-activeForeground);
                    text-decoration: underline;
                }
                
                /* Пустой чат */
                .empty-chat {
                    text-align: center;
                    color: var(--vscode-descriptionForeground);
                    padding: 40px 20px;
                    font-style: italic;
                    font-size: 13px;
                }
                
                /* Responsive design */
                @media (max-width: 600px) {
                    body {
                        padding: 8px;
                    }
                    
                    .message {
                        padding: 6px 12px;
                        gap: 6px;
                    }
                    
                    .avatar {
                        width: 18px;
                        height: 18px;
                        font-size: 10px;
                    }
                    
                    .message-content {
                        font-size: 12px;
                    }
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
    // Улучшенное форматирование markdown для аутентичного отображения
    let formatted = escapeHtml(text);
    
    // Блоки кода с четырьмя обратными кавычками (как в VS Code Copilot)
    formatted = formatted.replace(/````(\w*)\n?([\s\S]*?)````/g, (match, lang, code) => {
        return `<pre><code class="language-${lang}">${code.trim()}</code></pre>`;
    });
    
    // Обычные блоки кода с тремя обратными кавычками
    formatted = formatted.replace(/```(\w*)\n?([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre><code class="language-${lang}">${code.trim()}</code></pre>`;
    });
    
    // Inline код
    formatted = formatted.replace(/`([^`\n]+)`/g, '<code>$1</code>');
    
    // Жирный текст
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Курсив
    formatted = formatted.replace(/(?<!\*)\*([^\*\n]+)\*(?!\*)/g, '<em>$1</em>');
    
    // Заголовки
    formatted = formatted.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    formatted = formatted.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    formatted = formatted.replace(/^# (.*$)/gm, '<h1>$1</h1>');
    
    // Цитаты
    formatted = formatted.replace(/^> (.*$)/gm, '<blockquote>$1</blockquote>');
    
    // Нумерованные списки
    formatted = formatted.replace(/^\d+\.\s+(.*$)/gm, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>)/gs, (match) => {
        if (!match.includes('<ol>')) {
            return '<ol>' + match + '</ol>';
        }
        return match;
    });
    
    // Маркированные списки  
    formatted = formatted.replace(/^[\s]*[-*+]\s+(.*$)/gm, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>)/gs, (match) => {
        if (!match.includes('<ul>') && !match.includes('<ol>')) {
            return '<ul>' + match + '</ul>';
        }
        return match;
    });
    
    // Ссылки
    formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // Простые URL
    formatted = formatted.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank">$1</a>');
    
    // Разделители
    formatted = formatted.replace(/^---$/gm, '<hr>');
    
    // Переносы строк - два пробела в конце строки
    formatted = formatted.replace(/  \n/g, '<br>\n');
    
    // Абзацы
    formatted = formatted.replace(/\n\s*\n/g, '</p><p>');
    
    // Обернуть в абзац, если еще не обернуто
    if (!formatted.startsWith('<') && formatted.trim() !== '') {
        formatted = '<p>' + formatted + '</p>';
    }
    
    // Очистка пустых абзацев
    formatted = formatted.replace(/<p>\s*<\/p>/g, '');
    
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
