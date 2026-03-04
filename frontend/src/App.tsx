import { Routes, Route, Link } from "react-router-dom";
import { HomePage } from "./pages/home/HomePage";
import { AuthPage } from "./pages/auth/AuthPage";
import { DashboardPage } from "./pages/dashboard/DashboardPage";
import { ReportsPage } from "./pages/reports/ReportsPage";
import { ReportDetailsPage } from "./pages/reports/ReportDetailsPage";
import { TelegramSettingsPage } from "./pages/settings/TelegramSettingsPage";
import { useTheme } from "./hooks/useTheme";
import { useLanguage } from "./hooks/useLanguage";

function App() {
  const { theme, toggleTheme } = useTheme();
  const { language, setLanguage, t } = useLanguage();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-muted bg-primary text-primary-foreground">
        <div className="container mx-auto flex flex-wrap items-center justify-between gap-3 py-3 px-4">
          <Link to="/" className="font-semibold">
            Whale Tamer
          </Link>
          <nav className="flex items-center gap-3 text-sm">
            <Link to="/dashboard">{t("nav.dashboard")}</Link>
            <Link to="/reports">{t("nav.reports")}</Link>
            <Link to="/settings/telegram">{t("nav.telegram")}</Link>
            <button
              type="button"
              onClick={toggleTheme}
              className="rounded-md border border-primary-foreground/40 px-2 py-1"
              title={t("nav.theme")}
            >
              {theme === "dark" ? t("theme.light") : t("theme.dark")}
            </button>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as "ru" | "en")}
              className="rounded-md border border-primary-foreground/40 bg-primary px-2 py-1"
              title={t("nav.language")}
            >
              <option value="ru">{t("lang.ru")}</option>
              <option value="en">{t("lang.en")}</option>
            </select>
          </nav>
        </div>
      </header>
      <main className="flex-1 container mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/reports/:id" element={<ReportDetailsPage />} />
          <Route path="/settings/telegram" element={<TelegramSettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
