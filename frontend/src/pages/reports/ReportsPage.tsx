import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { useAPI } from "../../hooks/useAPI";
import { useLanguage } from "../../hooks/useLanguage";

type ReportListItem = {
  id: string;
  created_at: string;
  status: string;
  model: string;
};

export function ReportsPage() {
  const navigate = useNavigate();
  const { notifyError } = useAPI();
  const { t } = useLanguage();
  const { data, isLoading, error } = useQuery({
    queryKey: ["reports"],
    queryFn: async () => {
      const res = await api.get<ReportListItem[]>("/reports");
      return res.data;
    },
  });

  useEffect(() => {
    if (error) {
      notifyError(error, t("reports.loadError"));
    }
  }, [error, notifyError, t]);

  if (isLoading) {
    return <p>{t("reports.loading")}</p>;
  }

  const completed = data?.filter((r) => r.status === "completed").length ?? 0;
  const failed = data?.filter((r) => r.status === "failed").length ?? 0;

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold tracking-tight">{t("reports.title")}</h1>
      <div className="grid gap-2 sm:grid-cols-3">
        <div className="wt-panel rounded-xl p-4 text-sm">
          <div className="text-muted-foreground">{t("reports.total")}</div>
          <div className="text-2xl font-bold">{data?.length ?? 0}</div>
        </div>
        <div className="wt-panel rounded-xl p-4 text-sm">
          <div className="text-muted-foreground">{t("reports.completed")}</div>
          <div className="text-2xl font-bold">{completed}</div>
        </div>
        <div className="wt-panel rounded-xl p-4 text-sm">
          <div className="text-muted-foreground">{t("reports.failed")}</div>
          <div className="text-2xl font-bold">{failed}</div>
        </div>
      </div>
      {data && data.length === 0 && (
        <div className="wt-panel rounded-xl p-5 text-sm">
          <p className="text-muted-foreground">{t("reports.emptyWithCta")}</p>
          <Link
            to="/projects"
            className="mt-3 inline-flex items-center rounded-md bg-primary px-4 py-2 font-semibold text-primary-foreground"
          >
            {t("reports.toProjects")}
          </Link>
        </div>
      )}
      <div className="space-y-2">
        {data?.map((r) => (
          <button
            key={r.id}
            className="wt-panel w-full rounded-md px-4 py-3 text-left text-sm flex items-center justify-between cursor-pointer hover:bg-muted/40"
            onClick={() => navigate(`/reports/${r.id}`)}
          >
            <div>
              <div className="font-medium">{r.model}</div>
              <div className="text-xs text-muted-foreground">
                {new Date(r.created_at).toLocaleString()} • {r.status}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
