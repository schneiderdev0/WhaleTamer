export type Language = "ru" | "en";

export type MessageKey =
  | "nav.dashboard"
  | "nav.projects"
  | "nav.reports"
  | "nav.cli"
  | "nav.profile"
  | "nav.telegram"
  | "nav.theme"
  | "nav.language"
  | "home.title"
  | "home.description"
  | "home.login"
  | "home.dashboard"
  | "home.projects"
  | "home.reports"
  | "home.card.projectsTitle"
  | "home.card.projectsText"
  | "home.card.reportsTitle"
  | "home.card.reportsText"
  | "home.card.cliTitle"
  | "home.card.cliText"
  | "auth.title"
  | "auth.description"
  | "auth.github"
  | "auth.emailLogin"
  | "auth.emailRegister"
  | "auth.email"
  | "auth.password"
  | "auth.repassword"
  | "auth.processing"
  | "auth.emailLoginError"
  | "auth.registerError"
  | "auth.registerSuccess"
  | "auth.loginError"
  | "auth.callbackError"
  | "dashboard.title"
  | "dashboard.description"
  | "dashboard.format"
  | "dashboard.structure"
  | "dashboard.placeholder"
  | "dashboard.run"
  | "dashboard.running"
  | "dashboard.jobCreated"
  | "dashboard.status"
  | "dashboard.refreshStatus"
  | "dashboard.runError"
  | "dashboard.statusError"
  | "dashboard.validationStructure"
  | "reports.title"
  | "reports.loading"
  | "reports.empty"
  | "reports.emptyWithCta"
  | "reports.toProjects"
  | "reports.total"
  | "reports.completed"
  | "reports.failed"
  | "reports.loadError"
  | "report.loading"
  | "report.loadError"
  | "report.title"
  | "report.summary"
  | "report.issues"
  | "report.recommendations"
  | "report.notReady"
  | "report.generationError"
  | "projects.title"
  | "projects.description"
  | "projects.githubHint"
  | "projects.repo"
  | "projects.branch"
  | "projects.link"
  | "projects.linking"
  | "projects.linkedSuccess"
  | "projects.linkError"
  | "projects.sync"
  | "projects.syncing"
  | "projects.syncSuccess"
  | "projects.syncError"
  | "projects.syncResult"
  | "projects.listTitle"
  | "projects.empty"
  | "projects.githubConnectRequired"
  | "projects.githubStatusError"
  | "projects.reposLoadError"
  | "projects.projectsLoadError"
  | "cli.title"
  | "cli.description"
  | "cli.authRequired"
  | "cli.tokenName"
  | "cli.tokenNamePlaceholder"
  | "cli.create"
  | "cli.creating"
  | "cli.created"
  | "cli.createError"
  | "cli.oneTime"
  | "cli.copy"
  | "cli.copySuccess"
  | "cli.copyError"
  | "cli.show"
  | "cli.hide"
  | "cli.delete"
  | "cli.deleteSuccess"
  | "cli.deleteError"
  | "cli.loadError"
  | "cli.listTitle"
  | "cli.empty"
  | "profile.title"
  | "profile.description"
  | "profile.userId"
  | "profile.email"
  | "profile.authType"
  | "profile.githubStatus"
  | "profile.connected"
  | "profile.notConnected"
  | "profile.logout"
  | "profile.loggedOut"
  | "profile.linkGithub"
  | "profile.unlinkGithub"
  | "profile.unlinking"
  | "profile.loadError"
  | "profile.githubLinkError"
  | "profile.githubUnlinkError"
  | "profile.githubUnlinked"
  | "telegram.title"
  | "telegram.description"
  | "telegram.status"
  | "telegram.loadingStatus"
  | "telegram.linked"
  | "telegram.notLinked"
  | "telegram.createToken"
  | "telegram.creatingToken"
  | "telegram.tokenHint"
  | "telegram.copySuccess"
  | "telegram.copyError"
  | "telegram.statusError"
  | "telegram.tokenError"
  | "telegram.settingsTitle"
  | "telegram.settingsUnavailable"
  | "telegram.settingsEnabled"
  | "telegram.settingsFrequency"
  | "telegram.settingsSeverity"
  | "telegram.settingsSave"
  | "telegram.settingsSaving"
  | "telegram.settingsSaved"
  | "telegram.settingsLoadError"
  | "telegram.settingsSaveError"
  | "telegram.frequency.event"
  | "telegram.frequency.hourly"
  | "telegram.frequency.daily"
  | "telegram.severity.all"
  | "telegram.severity.critical"
  | "theme.dark"
  | "theme.light"
  | "lang.ru"
  | "lang.en";

type Messages = Record<MessageKey, string>;

const ru: Messages = {
  "nav.dashboard": "Dashboard",
  "nav.projects": "Projects",
  "nav.reports": "Reports",
  "nav.cli": "CLI",
  "nav.profile": "Профиль",
  "nav.telegram": "Telegram",
  "nav.theme": "Тема",
  "nav.language": "Язык",
  "home.title": "Whale Tamer",
  "home.description":
    "Сервис для автоматизации Docker-конфигураций и сборки отчётов о состоянии серверов.",
  "home.login": "Авторизоваться",
  "home.dashboard": "Перейти в дашборд",
  "home.projects": "GitHub Projects",
  "home.reports": "Statistics & Reports",
  "home.card.projectsTitle": "GitHub Projects",
  "home.card.projectsText": "Привяжите репозиторий и ветку для автоматической интеграции.",
  "home.card.reportsTitle": "Statistics & Reports",
  "home.card.reportsText": "Смотрите статистику сервера и отчеты, сформированные Gemini.",
  "home.card.cliTitle": "CLI",
  "home.card.cliText": "Создавайте токены доступа для использования CLI-инструмента.",
  "auth.title": "Авторизация",
  "auth.description":
    "Войдите через GitHub, чтобы подключить репозиторий и Data Collector.",
  "auth.github": "Войти в GitHub",
  "auth.emailLogin": "Вход",
  "auth.emailRegister": "Регистрация",
  "auth.email": "Email",
  "auth.password": "Пароль",
  "auth.repassword": "Повторите пароль",
  "auth.processing": "Обработка...",
  "auth.emailLoginError": "Не удалось выполнить вход по почте.",
  "auth.registerError": "Не удалось зарегистрировать пользователя.",
  "auth.registerSuccess": "Регистрация выполнена. Выполняем вход.",
  "auth.loginError": "Не удалось начать авторизацию через GitHub.",
  "auth.callbackError": "Некорректный callback авторизации.",
  "dashboard.title": "Генерация Docker-конфигураций",
  "dashboard.description":
    "Вставьте структуру проекта (tree/markdown), чтобы запустить генерацию Dockerfile и docker-compose через Whale Tamer.",
  "dashboard.format": "Формат",
  "dashboard.structure": "Структура проекта",
  "dashboard.placeholder": "Вставьте вывод tree или markdown c файлами проекта...",
  "dashboard.run": "Запустить генерацию",
  "dashboard.running": "Запуск...",
  "dashboard.jobCreated": "Создана задача генерации",
  "dashboard.status": "Статус",
  "dashboard.refreshStatus": "Обновить статус",
  "dashboard.runError": "Не удалось запустить генерацию.",
  "dashboard.statusError": "Не удалось получить статус задачи.",
  "dashboard.validationStructure": "Добавьте структуру проекта перед запуском.",
  "reports.title": "Отчёты",
  "reports.loading": "Загрузка отчётов...",
  "reports.empty": "Отчётов пока нет.",
  "reports.emptyWithCta": "Добавьте проект, чтобы видеть статистику и отчеты",
  "reports.toProjects": "Перейти к GitHub Projects",
  "reports.total": "Всего отчётов",
  "reports.completed": "Успешные",
  "reports.failed": "С ошибкой",
  "reports.loadError": "Не удалось загрузить список отчётов.",
  "report.loading": "Загрузка отчёта...",
  "report.loadError": "Ошибка загрузки отчёта.",
  "report.title": "Отчёт",
  "report.summary": "Сводка",
  "report.issues": "Проблемы",
  "report.recommendations": "Рекомендации",
  "report.notReady": "Отчёт ещё не сгенерирован или завершился с ошибкой.",
  "report.generationError": "Ошибка генерации",
  "projects.title": "GitHub Projects",
  "projects.description":
    "Проекты пользователя и привязка репозитория из GitHub. После привязки backend или CLI запускает автоматический процесс.",
  "projects.githubHint": "Введите URL репозитория GitHub и ветку для привязки проекта.",
  "projects.repo": "Репозиторий",
  "projects.branch": "Ветка",
  "projects.link": "Привязать репозиторий",
  "projects.linking": "Привязка...",
  "projects.linkedSuccess": "Проект успешно добавлен.",
  "projects.linkError": "Не удалось добавить проект.",
  "projects.sync": "Создать/обновить Docker-файлы",
  "projects.syncing": "Синхронизация...",
  "projects.syncSuccess": "Изменения успешно отправлены в GitHub.",
  "projects.syncError": "Не удалось внести изменения в репозиторий.",
  "projects.syncResult": "Коммитнутые файлы",
  "projects.listTitle": "Привязанные проекты",
  "projects.empty": "Пока нет привязанных репозиториев.",
  "projects.githubConnectRequired": "Подключите GitHub для автоматического создания Docker файлов",
  "projects.githubStatusError": "Не удалось получить статус подключения GitHub.",
  "projects.reposLoadError": "Не удалось загрузить репозитории GitHub.",
  "projects.projectsLoadError": "Не удалось загрузить список проектов.",
  "cli.title": "CLI Access Tokens",
  "cli.description":
    "Генерируйте токены доступа для CLI. Токен показывается только один раз после создания.",
  "cli.authRequired": "Сначала авторизуйтесь, чтобы управлять CLI токенами.",
  "cli.tokenName": "Название токена (опционально)",
  "cli.tokenNamePlaceholder": "например: local-macbook",
  "cli.create": "Создать токен",
  "cli.creating": "Создание...",
  "cli.created": "CLI токен создан.",
  "cli.createError": "Не удалось создать CLI токен.",
  "cli.oneTime": "Токен (показывается один раз)",
  "cli.copy": "Скопировать токен",
  "cli.copySuccess": "Токен скопирован в буфер обмена.",
  "cli.copyError": "Не удалось скопировать токен.",
  "cli.show": "Показать токен",
  "cli.hide": "Скрыть токен",
  "cli.delete": "Удалить токен",
  "cli.deleteSuccess": "Токен удалён.",
  "cli.deleteError": "Не удалось удалить токен.",
  "cli.loadError": "Не удалось загрузить список CLI токенов.",
  "cli.listTitle": "Ваши CLI токены",
  "cli.empty": "У вас пока нет CLI токенов.",
  "profile.title": "Профиль",
  "profile.description": "Данные пользователя и управление подключением GitHub.",
  "profile.userId": "ID пользователя",
  "profile.email": "Email",
  "profile.authType": "Тип авторизации",
  "profile.githubStatus": "GitHub",
  "profile.connected": "подключен",
  "profile.notConnected": "не подключен",
  "profile.logout": "Выйти из аккаунта",
  "profile.loggedOut": "Вы вышли из аккаунта.",
  "profile.linkGithub": "Привязать GitHub",
  "profile.unlinkGithub": "Отвязать GitHub",
  "profile.unlinking": "Отвязка...",
  "profile.loadError": "Не удалось загрузить профиль.",
  "profile.githubLinkError": "Не удалось начать привязку GitHub.",
  "profile.githubUnlinkError": "Не удалось отвязать GitHub.",
  "profile.githubUnlinked": "GitHub успешно отвязан.",
  "telegram.title": "Интеграция с Telegram",
  "telegram.description":
    "Подключите Telegram бота, чтобы получать уведомления об отчётах прямо в чат.",
  "telegram.status": "Статус",
  "telegram.loadingStatus": "Загрузка статуса...",
  "telegram.linked": "Чат привязан.",
  "telegram.notLinked": "Чат ещё не привязан.",
  "telegram.createToken": "Создать токен привязки",
  "telegram.creatingToken": "Создание токена...",
  "telegram.tokenHint":
    "Токен вида tg_... нужно отправить боту командой /start <token>.",
  "telegram.copySuccess":
    "Токен скопирован в буфер. Отправьте его боту: /start <token>.",
  "telegram.copyError": "Не удалось скопировать токен в буфер обмена.",
  "telegram.statusError": "Не удалось получить статус Telegram интеграции.",
  "telegram.tokenError": "Не удалось создать токен привязки.",
  "telegram.settingsTitle": "Настройки уведомлений",
  "telegram.settingsUnavailable": "Сначала привяжите Telegram-чат.",
  "telegram.settingsEnabled": "Уведомления включены",
  "telegram.settingsFrequency": "Частота",
  "telegram.settingsSeverity": "Критичность",
  "telegram.settingsSave": "Сохранить настройки",
  "telegram.settingsSaving": "Сохранение...",
  "telegram.settingsSaved": "Настройки Telegram обновлены.",
  "telegram.settingsLoadError": "Не удалось загрузить настройки уведомлений.",
  "telegram.settingsSaveError": "Не удалось сохранить настройки уведомлений.",
  "telegram.frequency.event": "По событию",
  "telegram.frequency.hourly": "Раз в час",
  "telegram.frequency.daily": "Раз в день",
  "telegram.severity.all": "Все",
  "telegram.severity.critical": "Только критичные",
  "theme.dark": "Тёмная",
  "theme.light": "Светлая",
  "lang.ru": "Русский",
  "lang.en": "English",
};

const en: Messages = {
  "nav.dashboard": "Dashboard",
  "nav.projects": "Projects",
  "nav.reports": "Reports",
  "nav.cli": "CLI",
  "nav.profile": "Profile",
  "nav.telegram": "Telegram",
  "nav.theme": "Theme",
  "nav.language": "Language",
  "home.title": "Whale Tamer",
  "home.description":
    "Service for Docker configuration automation and server health reporting.",
  "home.login": "Sign in with GitHub",
  "home.dashboard": "Open dashboard",
  "home.projects": "GitHub Projects",
  "home.reports": "Statistics & Reports",
  "home.card.projectsTitle": "GitHub Projects",
  "home.card.projectsText": "Link repository and branch for automated project integration.",
  "home.card.reportsTitle": "Statistics & Reports",
  "home.card.reportsText": "View server statistics and Gemini-generated health reports.",
  "home.card.cliTitle": "CLI",
  "home.card.cliText": "Generate access tokens for the CLI tool.",
  "auth.title": "Authentication",
  "auth.description":
    "Sign in via GitHub to connect your repository and Data Collector.",
  "auth.github": "Sign in with GitHub",
  "auth.emailLogin": "Sign in with Email",
  "auth.emailRegister": "Register",
  "auth.email": "Email",
  "auth.password": "Password",
  "auth.repassword": "Repeat password",
  "auth.processing": "Processing...",
  "auth.emailLoginError": "Failed to sign in with email.",
  "auth.registerError": "Failed to register user.",
  "auth.registerSuccess": "Registration completed. Signing in.",
  "auth.loginError": "Failed to start GitHub authentication.",
  "auth.callbackError": "Invalid authentication callback.",
  "dashboard.title": "Docker Configuration Generation",
  "dashboard.description":
    "Paste the project structure (tree/markdown) to run Dockerfile and docker-compose generation via Whale Tamer.",
  "dashboard.format": "Format",
  "dashboard.structure": "Project structure",
  "dashboard.placeholder": "Paste tree output or markdown with project files...",
  "dashboard.run": "Run generation",
  "dashboard.running": "Running...",
  "dashboard.jobCreated": "Generation job created",
  "dashboard.status": "Status",
  "dashboard.refreshStatus": "Refresh status",
  "dashboard.runError": "Failed to start generation.",
  "dashboard.statusError": "Failed to fetch job status.",
  "dashboard.validationStructure": "Provide a project structure before running.",
  "reports.title": "Reports",
  "reports.loading": "Loading reports...",
  "reports.empty": "No reports yet.",
  "reports.emptyWithCta": "Add a project to see statistics and reports",
  "reports.toProjects": "Go to GitHub Projects",
  "reports.total": "Total reports",
  "reports.completed": "Completed",
  "reports.failed": "Failed",
  "reports.loadError": "Failed to load report list.",
  "report.loading": "Loading report...",
  "report.loadError": "Failed to load report.",
  "report.title": "Report",
  "report.summary": "Summary",
  "report.issues": "Issues",
  "report.recommendations": "Recommendations",
  "report.notReady": "The report is not ready yet or finished with an error.",
  "report.generationError": "Generation error",
  "projects.title": "GitHub Projects",
  "projects.description":
    "User projects and GitHub repository linking. After linking, backend or CLI will trigger automated flow.",
  "projects.githubHint": "Provide GitHub repository URL and branch to link the project.",
  "projects.repo": "Repository",
  "projects.branch": "Branch",
  "projects.link": "Link repository",
  "projects.linking": "Linking...",
  "projects.linkedSuccess": "Project linked successfully.",
  "projects.linkError": "Failed to link project.",
  "projects.sync": "Create/update Docker files",
  "projects.syncing": "Syncing...",
  "projects.syncSuccess": "Changes were pushed to GitHub.",
  "projects.syncError": "Failed to apply changes to repository.",
  "projects.syncResult": "Committed files",
  "projects.listTitle": "Linked projects",
  "projects.empty": "No linked repositories yet.",
  "projects.githubConnectRequired": "Connect GitHub for automatic Docker file generation",
  "projects.githubStatusError": "Failed to get GitHub connection status.",
  "projects.reposLoadError": "Failed to load GitHub repositories.",
  "projects.projectsLoadError": "Failed to load projects list.",
  "cli.title": "CLI Access Tokens",
  "cli.description": "Generate access tokens for CLI. A token is shown only once after creation.",
  "cli.authRequired": "Please sign in first to manage CLI tokens.",
  "cli.tokenName": "Token name (optional)",
  "cli.tokenNamePlaceholder": "e.g. local-macbook",
  "cli.create": "Create token",
  "cli.creating": "Creating...",
  "cli.created": "CLI token created.",
  "cli.createError": "Failed to create CLI token.",
  "cli.oneTime": "Token (shown only once)",
  "cli.copy": "Copy token",
  "cli.copySuccess": "Token copied to clipboard.",
  "cli.copyError": "Failed to copy token.",
  "cli.show": "Show token",
  "cli.hide": "Hide token",
  "cli.delete": "Delete token",
  "cli.deleteSuccess": "Token deleted.",
  "cli.deleteError": "Failed to delete token.",
  "cli.loadError": "Failed to load CLI token list.",
  "cli.listTitle": "Your CLI tokens",
  "cli.empty": "You do not have CLI tokens yet.",
  "profile.title": "Profile",
  "profile.description": "User information and GitHub connection management.",
  "profile.userId": "User ID",
  "profile.email": "Email",
  "profile.authType": "Auth type",
  "profile.githubStatus": "GitHub",
  "profile.connected": "connected",
  "profile.notConnected": "not connected",
  "profile.logout": "Log out",
  "profile.loggedOut": "You have been logged out.",
  "profile.linkGithub": "Link GitHub",
  "profile.unlinkGithub": "Unlink GitHub",
  "profile.unlinking": "Unlinking...",
  "profile.loadError": "Failed to load profile.",
  "profile.githubLinkError": "Failed to start GitHub linking.",
  "profile.githubUnlinkError": "Failed to unlink GitHub.",
  "profile.githubUnlinked": "GitHub unlinked successfully.",
  "telegram.title": "Telegram Integration",
  "telegram.description":
    "Connect a Telegram bot to receive report notifications in chat.",
  "telegram.status": "Status",
  "telegram.loadingStatus": "Loading status...",
  "telegram.linked": "Chat is linked.",
  "telegram.notLinked": "Chat is not linked yet.",
  "telegram.createToken": "Create link token",
  "telegram.creatingToken": "Creating token...",
  "telegram.tokenHint": "Send tg_... token to bot with /start <token>.",
  "telegram.copySuccess":
    "Token copied to clipboard. Send it to bot: /start <token>.",
  "telegram.copyError": "Failed to copy token to clipboard.",
  "telegram.statusError": "Failed to load Telegram integration status.",
  "telegram.tokenError": "Failed to create link token.",
  "telegram.settingsTitle": "Notification settings",
  "telegram.settingsUnavailable": "Link your Telegram chat first.",
  "telegram.settingsEnabled": "Notifications enabled",
  "telegram.settingsFrequency": "Frequency",
  "telegram.settingsSeverity": "Severity",
  "telegram.settingsSave": "Save settings",
  "telegram.settingsSaving": "Saving...",
  "telegram.settingsSaved": "Telegram settings updated.",
  "telegram.settingsLoadError": "Failed to load notification settings.",
  "telegram.settingsSaveError": "Failed to save notification settings.",
  "telegram.frequency.event": "By event",
  "telegram.frequency.hourly": "Hourly",
  "telegram.frequency.daily": "Daily",
  "telegram.severity.all": "All",
  "telegram.severity.critical": "Critical only",
  "theme.dark": "Dark",
  "theme.light": "Light",
  "lang.ru": "Russian",
  "lang.en": "English",
};

export const messages: Record<Language, Messages> = {
  ru,
  en,
};
