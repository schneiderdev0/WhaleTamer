import { FormEvent, useState } from "react";
import { api } from "../../api/client";
import { useAPI } from "../../hooks/useAPI";
import { useLanguage } from "../../hooks/useLanguage";

type GenerateJobCreateResponse = {
  job_id: string;
  status: string;
};

type GenerateJobStatusResponse = {
  job_id: string;
  status: string;
  error: string | null;
};

export function DashboardPage() {
  const { notifyError } = useAPI();
  const { t } = useLanguage();
  const [projectStructure, setProjectStructure] = useState("");
  const [format, setFormat] = useState<"tree" | "markdown">("tree");
  const [job, setJob] = useState<GenerateJobCreateResponse | null>(null);
  const [status, setStatus] = useState<GenerateJobStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!projectStructure.trim()) {
      notifyError(null, t("dashboard.validationStructure"));
      return;
    }
    setLoading(true);
    try {
      const res = await api.post<GenerateJobCreateResponse>("/generate/jobs", {
        project_structure: projectStructure,
        format,
        project_context: null,
      });
      setJob(res.data);
      setStatus(null);
    } catch (error) {
      notifyError(error, t("dashboard.runError"));
    } finally {
      setLoading(false);
    }
  };

  const handleCheckStatus = async () => {
    if (!job) return;
    setLoading(true);
    try {
      const res = await api.get<GenerateJobStatusResponse>(
        `/generate/jobs/${job.job_id}`
      );
      setStatus(res.data);
    } catch (error) {
      notifyError(error, t("dashboard.statusError"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          Whale Tamer
        </p>
        <h1 className="text-3xl font-bold tracking-tight">{t("dashboard.title")}</h1>
        <p className="max-w-3xl text-sm text-muted-foreground">{t("dashboard.description")}</p>
      </div>

      <section className="wt-panel rounded-xl p-5 md:p-6">
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="flex flex-wrap items-center gap-3">
            <label className="text-sm font-semibold">{t("dashboard.format")}</label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value as "tree" | "markdown")}
              className="wt-input rounded-md px-3 py-1.5 text-sm"
            >
              <option value="tree">tree</option>
              <option value="markdown">markdown</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold">{t("dashboard.structure")}</label>
            <textarea
              value={projectStructure}
              onChange={(e) => setProjectStructure(e.target.value)}
              rows={10}
              placeholder={t("dashboard.placeholder")}
              className="wt-input w-full rounded-lg px-3 py-2 text-sm font-mono"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-60"
          >
            {loading ? t("dashboard.running") : t("dashboard.run")}
          </button>
        </form>
      </section>

      {job && (
        <section className="wt-panel max-w-xl rounded-xl p-4 text-sm">
          <div className="space-y-2">
            <div className="font-semibold">{t("dashboard.jobCreated")}</div>
            <div className="break-all rounded-md bg-background/60 px-2 py-1 text-xs text-muted-foreground">
              job_id: {job.job_id}
            </div>
          </div>
          <div className="mt-3 flex items-center gap-3">
            <span className="font-medium">
              {t("dashboard.status")}: {status?.status ?? job.status}
            </span>
            <button
              type="button"
              onClick={handleCheckStatus}
              disabled={loading}
              className="rounded-md border border-muted px-3 py-1 text-xs"
            >
              {t("dashboard.refreshStatus")}
            </button>
          </div>
          {status?.error && (
            <div className="mt-3 rounded-md border border-red-400/30 bg-red-400/10 px-2 py-1 text-xs text-red-400">
              Ошибка: {status.error}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
