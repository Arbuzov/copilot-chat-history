# Исправления ошибок публикации

## Проблема
При публикации расширения в GitHub Actions возникла ошибка:
```
ReferenceError: File is not defined
    at /opt/hostedtoolcache/node/18.20.8/x64/lib/node_modules/vsce/node_modules/undici/lib/web/webidl/index.js:512:48
```

## Причины
1. **Устаревшая версия Node.js**: GitHub Actions использовал Node.js 18.20.8, а современные зависимости требуют Node.js >= 20.18.1
2. **Устаревший пакет vsce**: Использовался deprecated пакет `vsce` вместо нового `@vscode/vsce`
3. **Устаревшие GitHub Actions**: Использовались deprecated actions для создания релизов

## Исправления ✅

### 1. Обновили Node.js до версии 20.x
- В `.github/workflows/ci-cd.yml`: `node-version: '20'`
- В `.github/workflows/test.yml`: `node-version: 20.x`
- В `package.json` добавили: `"node": ">=20.18.1"` в engines

### 2. Заменили устаревший vsce на @vscode/vsce
```yaml
# Было:
npm install -g vsce

# Стало:
npm install -g @vscode/vsce
```

### 3. Обновили GitHub Actions
```yaml
# Было:
- uses: actions/create-release@v1
- uses: actions/upload-release-asset@v1

# Стало:
- uses: softprops/action-gh-release@v1
```

### 4. Обновили версию до 1.0.1
- Обновили `package.json` версию
- Создали новый git tag `v1.0.1`
- Обновили CHANGELOG.md

## Результат
Теперь CI/CD pipeline должен работать корректно с:
- ✅ Node.js 20.x
- ✅ Современными зависимостями
- ✅ Актуальными GitHub Actions
- ✅ Правильным пакетом @vscode/vsce

## Команды для ручной публикации
Если нужно опубликовать вручную локально:

```bash
# Установка современного vsce
npm install -g @vscode/vsce

# Публикация (требует токен)
vsce publish -p YOUR_VSCE_TOKEN

# Или через npm скрипт
npm run publish:vsce
```

## Проверка
Теперь тег `v1.0.1` должен успешно запустить GitHub Actions pipeline без ошибок совместимости.
