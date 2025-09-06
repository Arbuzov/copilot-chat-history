# Настройка публикации в Open VSX Registry

## Проблема
Публикация в Open VSX Registry не происходит, хотя VS Code Marketplace работает.

## Возможные причины

### 1. Секрет OVSX_TOKEN не настроен
**Решение**: Настройте секрет в GitHub репозитории.

1. **Создайте аккаунт в Open VSX Registry**:
   - Перейдите на https://open-vsx.org/
   - Войдите через GitHub аккаунт

2. **Получите Access Token**:
   - После входа перейдите в User Settings
   - Создайте новый Access Token
   - Сохраните токен (он показывается только один раз!)

3. **Добавьте секрет в GitHub**:
   - В репозитории: Settings → Secrets and variables → Actions
   - Добавьте новый secret: `OVSX_TOKEN`
   - Вставьте ваш Access Token

### 2. Publisher не зарегистрирован в Open VSX
**Решение**: Зарегистрируйте namespace.

1. **Проверьте, зарегистрирован ли publisher "arbuzov"**:
   - Перейдите на https://open-vsx.org/namespace/arbuzov
   - Если страница не существует, нужно зарегистрировать namespace

2. **Зарегистрируйте namespace**:
   - Перейдите на https://open-vsx.org/admin
   - Создайте новый namespace "arbuzov"
   - Или измените publisher в package.json на существующий

### 3. Расширение уже опубликовано
**Решение**: Увеличьте версию в package.json.

```bash
# Обновите версию
npm version patch  # Увеличивает последнюю цифру: 1.0.1 → 1.0.2
# или
npm version minor  # 1.0.1 → 1.1.0
# или
npm version major  # 1.0.1 → 2.0.0

# Создайте новый тег
git push origin main
git push --tags
```

## Ручная публикация для тестирования

```bash
# Установите ovsx локально
npm install -g ovsx

# Войдите в систему (потребуется Access Token)
npx ovsx create-namespace arbuzov  # Если нужно создать namespace

# Опубликуйте расширение
npx ovsx publish --pat YOUR_OVSX_TOKEN

# Или опубликуйте готовый VSIX файл
npx ovsx publish copilot-chat-history-1.0.1.vsix --pat YOUR_OVSX_TOKEN
```

## Проверка статуса

После успешной публикации расширение появится здесь:
- **Open VSX**: https://open-vsx.org/extension/arbuzov/copilot-chat-history
- **VS Code Marketplace**: https://marketplace.visualstudio.com/items?itemName=arbuzov.copilot-chat-history

## Отладка GitHub Actions

1. **Запустите workflow вручную**:
   - В GitHub: Actions → Publish Extension → Run workflow
   
2. **Проверьте логи**:
   - Найдите step "Publish to Open VSX Registry"
   - Посмотрите на ошибки

3. **Типичные ошибки**:
   ```
   Error: Namespace 'arbuzov' not found
   → Нужно зарегистрировать namespace
   
   Error: Extension arbuzov.copilot-chat-history version 1.0.1 already exists
   → Нужно увеличить версию
   
   Error: Invalid access token
   → Проверьте OVSX_TOKEN в секретах
   ```

## Следующие шаги

1. ✅ Проверьте, настроен ли OVSX_TOKEN в GitHub Secrets
2. ✅ Зарегистрируйте namespace "arbuzov" в Open VSX Registry
3. ✅ Увеличьте версию в package.json
4. ✅ Создайте новый тег и запустите публикацию
5. ✅ Проверьте результат в логах GitHub Actions
