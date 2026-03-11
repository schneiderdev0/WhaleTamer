import { Link } from "react-router-dom";
import { useLanguage } from "../../hooks/useLanguage";

export function HomePage() {
  const { t } = useLanguage();

  return (
    <div className="mx-auto flex max-w-5xl flex-col items-center space-y-8 text-center">
      <section className="wt-panel w-full max-w-4xl rounded-2xl px-6 py-12 md:px-10 md:py-16">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-muted-foreground">
          Docker Automation Platform
        </p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight md:text-5xl">{t("home.title")}</h1>
        <p className="mx-auto mt-4 max-w-2xl text-base text-muted-foreground md:text-lg">
          {t("home.description")}
        </p>
        <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
          <Link
            to="/login"
            className="inline-flex items-center rounded-md bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-400"
          >
            {t("home.login")}
          </Link>
        </div>
      </section>
      <div className="grid w-full max-w-4xl gap-3 md:grid-cols-2">
        <article className="wt-panel rounded-xl p-5 text-left text-sm">
          <h2 className="font-semibold">{t("home.card.projectsTitle")}</h2>
          <p className="mt-1 text-muted-foreground">{t("home.card.projectsText")}</p>
        </article>
        <article className="wt-panel rounded-xl p-5 text-left text-sm">
          <h2 className="font-semibold">{t("home.card.cliTitle")}</h2>
          <p className="mt-1 text-muted-foreground">{t("home.card.cliText")}</p>
        </article>
      </div>
    </div>
  );
}
