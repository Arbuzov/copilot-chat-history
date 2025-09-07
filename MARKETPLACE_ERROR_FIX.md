# Исправление ошибки "Value cannot be null. Parameter name: v1"

## Проблема
Ошибка `Value cannot be null. Parameter name: v1` при публикации в VS Code Marketplace.

## Возможные причины и решения

### 1. ✅ Исправлены отсутствующие поля в package.json

**Проблема**: Некоторые команды не имели обязательного поля `icon`
```json
// Было:
{
  "command": "copilotChatHistory.openChat",
  "title": "Open Chat Session"  // <- отсутствует icon
}

// Стало:
{
  "command": "copilotChatHistory.openChat", 
  "title": "Open Chat Session",
  "icon": "$(file-text)"  // <- добавлена иконка
}
```

### 2. ✅ Добавлено поле author

```json
"author": {
  "name": "Arbuzov",
  "url": "https://github.com/arbuzov"
}
```

### 3. ✅ Улучшены команды публикации

```json
"publish:vsce": "npm run package && npx @vscode/vsce publish --no-dependencies",
"publish:ovsx": "npm run package && npx ovsx publish --no-dependencies",
"verify": "npx @vscode/vsce ls && npx @vscode/vsce package --allow-missing-repository"
```

## Диагностика перед публикацией

### 1. Проверьте package.json:
```bash
npm run verify
```

### 2. Проверьте токен VSCE:
```bash
# В PowerShell проверьте переменную среды
echo $env:VSCE_TOKEN

# Или попробуйте логин
npx @vscode/vsce login arbuzov
```

### 3. Попробуйте публикацию с флагами:
```bash
# Публикация с дополнительными флагами
npx @vscode/vsce publish --no-dependencies --allow-missing-repository
```

## Пошаговая публикация

### Способ 1: Безопасная публикация
```bash
# 1. Убедитесь, что сборка проходит
npm run package:vsix

# 2. Проверьте содержимое
npm run verify  

# 3. Опубликуйте с флагами
npm run publish:vsce
```

### Способ 2: Ручная публикация
```bash
# 1. Создайте VSIX
npx @vscode/vsce package --allow-missing-repository

# 2. Опубликуйте готовый файл
npx @vscode/vsce publish --packagePath copilot-chat-history-1.0.3.vsix --pat YOUR_TOKEN
```

## Если ошибка повторяется

### 1. Проверьте токен на marketplace.visualstudio.com:
- Зайдите в Manage Publishers
- Проверьте, что токен действителен
- Создайте новый токен если нужно

### 2. Проверьте namespace "arbuzov":
- Убедитесь, что publisher зарегистрирован
- Или измените на другой publisher

### 3. Альтернативная публикация:
```bash
# Опубликуйте только в Open VSX (для тестирования)
npm run publish:ovsx
```

## Результат
После этих исправлений ошибка "Value cannot be null" должна быть устранена.

## Команды для проверки:
- `npm run verify` - проверка перед публикацией
- `npm run package:vsix` - создание VSIX
- `npm run publish:vsce` - публикация в VS Code Marketplace  
- `npm run publish:ovsx` - публикация в Open VSX Registry
