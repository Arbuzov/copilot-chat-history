import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';
import type { ChatSession } from './types';
import { buildChatMarkdown, sanitizeFileName } from './markdown/chatMarkdown';
import { generateChatHTML } from './renderers/chatRenderer';
import { getChatStyles } from './renderers/styles';
import { showCentralizedError } from './utils/notifications';
import { loadSessionData, resolveAccessibleSessionFilePath, SessionFileError } from './utils/sessionFiles';

interface WorkspaceGroup {
    workspaceName: string;
    workspacePath?: string;
    sessions: ChatSession[];
}

function logSessionFileError(scope: string, error: SessionFileError): void {
    if (error.cause) {
        console.error(`${scope}: ${error.message}`, error.cause);
    } else {
        console.error(`${scope}: ${error.message}`);
    }
}

function handleSessionFileError(scope: string, error: SessionFileError): void {
    logSessionFileError(scope, error);
    showCentralizedError(error.message, error.context);
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
            const isCurrentWorkspace = this.isCurrentWorkspace(element);
            const itemLabel = isCurrentWorkspace ? `$(star-full) ${element.workspaceName}` : element.workspaceName;
            const item = new vscode.TreeItem(itemLabel, vscode.TreeItemCollapsibleState.Collapsed);
            const sessionsDescription = `${element.sessions.length} sessions`;
            item.iconPath = new vscode.ThemeIcon(isCurrentWorkspace ? 'root-folder-opened' : 'folder');
            item.description = isCurrentWorkspace ? `Current • ${sessionsDescription}` : sessionsDescription;
            item.contextValue = 'workspaceGroup';
            item.id = `workspace-${element.workspaceName}`;
            // Добавляем resourceUri если есть путь к workspace
            if (element.workspacePath) {
                item.resourceUri = vscode.Uri.file(element.workspacePath);
            }
            if (isCurrentWorkspace) {
                item.tooltip = element.workspacePath
                    ? `${element.workspacePath}\nCurrent workspace`
                    : 'Current workspace';
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

    private isCurrentWorkspace(group: WorkspaceGroup): boolean {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            return false;
        }

        const targetPath = group.workspacePath ? this.normalizeWorkspacePath(group.workspacePath) : undefined;

        for (const folder of workspaceFolders) {
            const folderPath = this.normalizeWorkspacePath(folder.uri.fsPath);

            if (targetPath) {
                if (folderPath === targetPath) {
                    return true;
                }
            } else if (folder.name === group.workspaceName) {
                return true;
            }
        }

        return false;
    }

    private normalizeWorkspacePath(workspacePath: string): string {
        let normalizedPath = workspacePath;
        if (workspacePath.startsWith('file://')) {
            normalizedPath = vscode.Uri.parse(workspacePath).fsPath;
        }

        normalizedPath = path.normalize(normalizedPath).replace(/[\\/]+$/, '');

        if (process.platform === 'win32') {
            return normalizedPath.toLowerCase();
        }

        return normalizedPath;
    }

    private async scanForChatSessions(): Promise<ChatSession[]> {
        const sessions: ChatSession[] = [];
        
        try {
            const isInsiders = vscode.env.appName.includes('Insiders');
            const codeDir = isInsiders ? 'Code - Insiders' : 'Code';
            const userDataPath = path.join(os.homedir(), 'AppData', 'Roaming', codeDir, 'User', 'workspaceStorage');
            
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
                                messageCount,
                                storageRoot: chatSessionsPath
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
            const isInsiders = vscode.env.appName.includes('Insiders');
            const codeDir = isInsiders ? 'Code - Insiders' : 'Code';
            const userDataPath = path.join(os.homedir(), 'AppData', 'Roaming', codeDir, 'User');
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

// Функция для открытия чата в webview
async function openChatInWebview(session: ChatSession, context: vscode.ExtensionContext) {
    try {
        const sessionInfo = await loadSessionData(session);

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
        panel.webview.html = generateChatHTML(sessionInfo, getChatStyles(), sessionInfo.data.responderUsername || 'Copilot');

    } catch (error) {
        if (error instanceof SessionFileError) {
            handleSessionFileError('openChatInWebview', error);
            return;
        }

        console.error('Error opening chat in webview:', error);
        showCentralizedError('Error opening chat: see logs for details.', 'openChatInWebview:unexpected');
    }
}

async function exportChatToMarkdown(session: ChatSession): Promise<void> {
    try {
        const sessionInfo = await loadSessionData(session);

        const markdown = buildChatMarkdown(sessionInfo.data, session);

        const defaultFileName = sanitizeFileName(session.customTitle || `chat-session-${session.id}`) + '.md';
        const defaultUri = vscode.Uri.file(path.join(os.homedir(), defaultFileName));

        const saveUri = await vscode.window.showSaveDialog({
            defaultUri,
            filters: {
                Markdown: ['md'],
                'All Files': ['*']
            }
        });

        if (!saveUri) {
            return;
        }

        if (saveUri.scheme !== 'file') {
            showCentralizedError(
                'Only file system targets are supported for exporting chat sessions.',
                'exportChatMarkdown:unsupportedScheme'
            );
            return;
        }

        const savePath = path.resolve(saveUri.fsPath);
        let shouldWrite = true;
        try {
            await fs.promises.access(savePath, fs.constants.F_OK);
            const overwrite = await vscode.window.showWarningMessage(
                `File "${path.basename(savePath)}" already exists. Overwrite?`,
                { modal: true },
                'Overwrite'
            );
            if (overwrite !== 'Overwrite') {
                shouldWrite = false;
            }
        } catch {
            // File does not exist; safe to write.
        }

        if (!shouldWrite) {
            vscode.window.showInformationMessage('Export cancelled: file not overwritten.');
            return;
        }

        await fs.promises.writeFile(savePath, markdown, 'utf8');
        vscode.window.showInformationMessage(`Chat exported to ${savePath}`);
    } catch (error) {
        if (error instanceof SessionFileError) {
            handleSessionFileError('exportChatToMarkdown', error);
            return;
        }

        console.error('Error exporting chat to markdown:', error);
        showCentralizedError('Error exporting chat: see logs for details.', 'exportChatMarkdown:unexpected');
    }
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

    const openChatCommand = vscode.commands.registerCommand('copilotChatHistory.openChat', async (session: ChatSession) => {
        // Открываем чат в специальном webview вместо JSON файла
        await openChatInWebview(session, context);
    });

    const openChatJsonCommand = vscode.commands.registerCommand('copilotChatHistory.openChatJson', async (session: ChatSession) => {
        try {
            const sessionFilePath = await resolveAccessibleSessionFilePath(session);
            const document = await vscode.workspace.openTextDocument(sessionFilePath);
            await vscode.window.showTextDocument(document);
        } catch (error) {
            if (error instanceof SessionFileError) {
                handleSessionFileError('openChatJson', error);
                return;
            }

            console.error('Error opening chat JSON document:', error);
            showCentralizedError('Error opening chat JSON: see logs for details.', 'openChatJson:unexpected');
        }
    });

    const exportChatMarkdownCommand = vscode.commands.registerCommand('copilotChatHistory.exportChatMarkdown', async (session: ChatSession) => {
        await exportChatToMarkdown(session);
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
                showCentralizedError(
                    `Workspace path does not exist: ${normalizedPath}`,
                    'openWorkspaceCurrent:missingPath'
                );
            }
        } else {
            // Попробуем найти workspace вручную
            const foundPath = await chatHistoryProvider.searchWorkspaceByName(workspaceGroup.workspaceName);
            if (foundPath && fs.existsSync(foundPath)) {
                const workspaceUri = vscode.Uri.file(foundPath);
                await vscode.commands.executeCommand('vscode.openFolder', workspaceUri, false);
                vscode.window.showInformationMessage(`Found and opened workspace: ${foundPath}`);
            } else {
                showCentralizedError(
                    `Workspace path not found for: ${workspaceGroup.workspaceName}. Please open it manually.`,
                    'openWorkspaceCurrent:notFound'
                );
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
                showCentralizedError(
                    `Workspace path does not exist: ${normalizedPath}`,
                    'openWorkspaceNewWindow:missingPath'
                );
            }
        } else {
            // Попробуем найти workspace вручную
            const foundPath = await chatHistoryProvider.searchWorkspaceByName(workspaceGroup.workspaceName);
            if (foundPath && fs.existsSync(foundPath)) {
                const workspaceUri = vscode.Uri.file(foundPath);
                await vscode.commands.executeCommand('vscode.openFolder', workspaceUri, true);
                vscode.window.showInformationMessage(`Found and opened workspace: ${foundPath}`);
            } else {
                showCentralizedError(
                    `Workspace path not found for: ${workspaceGroup.workspaceName}. Please open it manually.`,
                    'openWorkspaceNewWindow:notFound'
                );
            }
        }
    });

    context.subscriptions.push(refreshCommand, openChatCommand, openChatJsonCommand, helloWorldCommand, searchCommand, clearFilterCommand, openWorkspaceInCurrentWindowCommand, openWorkspaceInNewWindowCommand, exportChatMarkdownCommand);

    // Автоматически обновляем при активации
    chatHistoryProvider.refresh();
    
    // Показываем сообщение о том, что расширение активировано
    console.log('Copilot Chat History extension is now active!');
}

export function deactivate() {}
