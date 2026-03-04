import { Link } from "react-router-dom";
import { useLanguage } from "../../hooks/useLanguage";

export function HomePage() {
  const { t } = useLanguage();

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold">{t("home.title")}</h1>
      <p className="text-muted-foreground">{t("home.description")}</p>
      <div className="flex gap-4">
        <Link
          to="/auth"
          className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
        >
          {t("home.login")}
        </Link>
        <Link
          to="/dashboard"
          className="inline-flex items-center rounded-md border border-muted px-4 py-2 text-sm"
        >
          {t("home.dashboard")}
        </Link>
      </div>
    </div>
  );
}
