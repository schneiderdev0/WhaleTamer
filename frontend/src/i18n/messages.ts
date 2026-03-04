export type Language = "ru" | "en";

export type MessageKey =
  | "nav.dashboard"
  | "nav.reports"
  | "nav.telegram"
  | "nav.theme"
  | "nav.language"
  | "home.title"
  | "home.description"
  | "home.login"
  | "home.dashboard"
  | "auth.title"
  | "auth.description"
  | "auth.github"
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
  | "reports.loadError"
  | "report.loading"
  | "report.loadError"
  | "report.title"
  | "report.summary"
  | "report.issues"
  | "report.recommendations"
  | "report.notReady"
  | "report.generationError"
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
  "nav.reports": "Reports",
  "nav.telegram": "Telegram",
  "nav.theme": "Тема",
  "nav.language": "Язык",
  "home.title": "Whale Tamer",
  "home.description":
    "Сервис для автоматизации Docker-конфигураций и сборки отчётов о состоянии серверов.",
  "home.login": "Войти через GitHub",
  "home.dashboard": "Перейти в дашборд",
  "auth.title": "Авторизация",
  "auth.description":
    "Войдите через GitHub, чтобы подключить репозиторий и Data Collector.",
  "auth.github": "Войти через GitHub",
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
  "reports.loadError": "Не удалось загрузить список отчётов.",
  "report.loading": "Загрузка отчёта...",
  "report.loadError": "Ошибка загрузки отчёта.",
  "report.title": "Отчёт",
  "report.summary": "Сводка",
  "report.issues": "Проблемы",
  "report.recommendations": "Рекомендации",
  "report.notReady": "Отчёт ещё не сгенерирован или завершился с ошибкой.",
  "report.generationError": "Ошибка генерации",
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
  "nav.reports": "Reports",
  "nav.telegram": "Telegram",
  "nav.theme": "Theme",
  "nav.language": "Language",
  "home.title": "Whale Tamer",
  "home.description":
    "Service for Docker configuration automation and server health reporting.",
  "home.login": "Sign in with GitHub",
  "home.dashboard": "Open dashboard",
  "auth.title": "Authentication",
  "auth.description":
    "Sign in via GitHub to connect your repository and Data Collector.",
  "auth.github": "Sign in with GitHub",
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
  "reports.loadError": "Failed to load report list.",
  "report.loading": "Loading report...",
  "report.loadError": "Failed to load report.",
  "report.title": "Report",
  "report.summary": "Summary",
  "report.issues": "Issues",
  "report.recommendations": "Recommendations",
  "report.notReady": "The report is not ready yet or finished with an error.",
  "report.generationError": "Generation error",
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
