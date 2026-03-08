import { Routes, Route, Link, Navigate, NavLink } from "react-router-dom";
import { Moon, Sun } from "lucide-react";
import { HomePage } from "./pages/home/HomePage";
import { AuthPage } from "./pages/auth/AuthPage";
import { GitHubProjectsPage } from "./pages/projects/GitHubProjectsPage";
import { ReportsPage } from "./pages/reports/ReportsPage";
import { ReportDetailsPage } from "./pages/reports/ReportDetailsPage";
import { CLIPage } from "./pages/cli/CLIPage";
import { ProfilePage } from "./pages/profile/ProfilePage";
import { useTheme } from "./hooks/useTheme";
import { useLanguage } from "./hooks/useLanguage";
import { useAuthStore } from "./store/auth";

function App() {
  const { theme, toggleTheme } = useTheme();
  const { language, setLanguage, t } = useLanguage();
  const token = useAuthStore((s) => s.token);
  const isAuthorized = Boolean(token);

  return (
    <div className="relative flex min-h-screen flex-col overflow-x-hidden wt-grid-bg">
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div className="absolute -left-20 top-10 h-72 w-72 rounded-full bg-cyan-400/15 blur-3xl" />
        <div className="absolute right-0 top-40 h-80 w-80 rounded-full bg-indigo-500/15 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 h-80 w-80 rounded-full bg-blue-500/10 blur-3xl" />
      </div>

      <header className="sticky top-0 z-20 border-b border-muted/60 bg-background/70 backdrop-blur-md">
        <div className="container mx-auto grid grid-cols-2 items-center gap-3 px-4 py-4 md:grid-cols-3">
          <Link to="/" className="justify-self-start text-lg font-bold tracking-tight">
            🐳 Whale Tamer
          </Link>
          <nav className="col-span-2 flex items-center justify-center gap-5 text-sm font-medium md:col-span-1">
            {isAuthorized && (
              <>
                <NavLink
                  to="/projects"
                  className={({ isActive }) =>
                    `px-1 py-1 text-muted-foreground hover:text-foreground hover:underline underline-offset-4 ${isActive ? "text-foreground underline" : ""}`
                  }
                >
                  {t("nav.projects")}
                </NavLink>
                <NavLink
                  to="/reports"
                  className={({ isActive }) =>
                    `px-1 py-1 text-muted-foreground hover:text-foreground hover:underline underline-offset-4 ${isActive ? "text-foreground underline" : ""}`
                  }
                >
                  {t("nav.reports")}
                </NavLink>
                <NavLink
                  to="/cli"
                  className={({ isActive }) =>
                    `px-1 py-1 text-muted-foreground hover:text-foreground hover:underline underline-offset-4 ${isActive ? "text-foreground underline" : ""}`
                  }
                >
                  {t("nav.cli")}
                </NavLink>
                <NavLink
                  to="/profile"
                  className={({ isActive }) =>
                    `px-1 py-1 text-muted-foreground hover:text-foreground hover:underline underline-offset-4 ${isActive ? "text-foreground underline" : ""}`
                  }
                >
                  {t("nav.profile")}
                </NavLink>
              </>
            )}
          </nav>
          <div className="col-span-2 flex items-center justify-end gap-2 md:col-span-1">
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as "ru" | "en")}
              className="rounded-md border border-muted bg-background px-2 py-1"
              title={t("nav.language")}
            >
              <option value="ru">{t("lang.ru")}</option>
              <option value="en">{t("lang.en")}</option>
            </select>
            {!isAuthorized && (
              <Link to="/login" className="rounded-md border border-muted px-3 py-1">
                {t("home.login")}
              </Link>
            )}
            <button
              type="button"
              onClick={toggleTheme}
              className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-muted text-foreground"
              title={t("nav.theme")}
              aria-label={t("nav.theme")}
            >
              {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
            </button>
          </div>
        </div>
      </header>
      <main className="container mx-auto flex-1 px-4 py-8">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<AuthPage />} />
          <Route path="/projects" element={isAuthorized ? <GitHubProjectsPage /> : <Navigate to="/login" replace />} />
          <Route path="/dashboard" element={isAuthorized ? <GitHubProjectsPage /> : <Navigate to="/login" replace />} />
          <Route path="/reports" element={isAuthorized ? <ReportsPage /> : <Navigate to="/login" replace />} />
          <Route path="/reports/:id" element={isAuthorized ? <ReportDetailsPage /> : <Navigate to="/login" replace />} />
          <Route path="/cli" element={isAuthorized ? <CLIPage /> : <Navigate to="/login" replace />} />
          <Route path="/profile" element={isAuthorized ? <ProfilePage /> : <Navigate to="/login" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
