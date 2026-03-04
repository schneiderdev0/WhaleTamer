import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
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

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">{t("reports.title")}</h1>
      {data && data.length === 0 && (
        <p className="text-muted-foreground text-sm">{t("reports.empty")}</p>
      )}
      <div className="space-y-2">
        {data?.map((r) => (
          <div
            key={r.id}
            className="rounded-md border border-muted px-4 py-3 text-sm flex items-center justify-between cursor-pointer hover:bg-muted/40"
            onClick={() => navigate(`/reports/${r.id}`)}
          >
            <div>
              <div className="font-medium">{r.model}</div>
              <div className="text-xs text-muted-foreground">
                {new Date(r.created_at).toLocaleString()} • {r.status}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
