import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { api } from "../../api/client";
import { useAPI } from "../../hooks/useAPI";
import { useLanguage } from "../../hooks/useLanguage";

type ReportContent = {
  summary: string;
  issues: string[];
  recommendations: string[];
  observations: Record<string, unknown>;
};

type ReportResponse = {
  id: string;
  event_id: string;
  status: string;
  model: string;
  content: ReportContent | null;
  error: string | null;
  created_at: string;
};

export function ReportDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const { notifyError } = useAPI();
  const { t } = useLanguage();

  const { data, isLoading, error } = useQuery({
    queryKey: ["report", id],
    enabled: Boolean(id),
    queryFn: async () => {
      const res = await api.get<ReportResponse>(`/reports/${id}`);
      return res.data;
    },
  });

  useEffect(() => {
    if (error) {
      notifyError(error, t("report.loadError"));
    }
  }, [error, notifyError, t]);

  if (isLoading) {
    return <p>{t("report.loading")}</p>;
  }

  if (error || !data) {
    return <p className="text-sm text-red-400">{t("report.loadError")}</p>;
  }

  return (
    <div className="space-y-4 max-w-3xl">
      <div>
        <h1 className="text-2xl font-semibold">{t("report.title")}</h1>
        <p className="text-xs text-muted-foreground">
          {new Date(data.created_at).toLocaleString()} • {data.model} •{" "}
          {data.status}
        </p>
      </div>
      {data.content ? (
        <>
          <section className="space-y-2">
            <h2 className="text-lg font-medium">{t("report.summary")}</h2>
            <p className="text-sm whitespace-pre-line">{data.content.summary}</p>
          </section>
          {data.content.issues.length > 0 && (
            <section className="space-y-2">
              <h2 className="text-lg font-medium">{t("report.issues")}</h2>
              <ul className="list-disc list-inside text-sm space-y-1">
                {data.content.issues.map((i, idx) => (
                  <li key={idx}>{i}</li>
                ))}
              </ul>
            </section>
          )}
          {data.content.recommendations.length > 0 && (
            <section className="space-y-2">
              <h2 className="text-lg font-medium">{t("report.recommendations")}</h2>
              <ul className="list-disc list-inside text-sm space-y-1">
                {data.content.recommendations.map((r, idx) => (
                  <li key={idx}>{r}</li>
                ))}
              </ul>
            </section>
          )}
        </>
      ) : (
        <p className="text-sm text-muted-foreground">
          {t("report.notReady")}
        </p>
      )}
      {data.error && (
        <p className="text-xs text-red-400">
          {t("report.generationError")}: {data.error}
        </p>
      )}
    </div>
  );
}
