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
        <h1 className="text-2xl font-semibold">{t("dashboard.title")}</h1>
        <p className="text-muted-foreground text-sm">{t("dashboard.description")}</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 max-w-3xl">
        <div className="flex gap-4 items-center">
          <label className="text-sm font-medium">{t("dashboard.format")}</label>
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value as "tree" | "markdown")}
            className="rounded-md border border-muted bg-background px-2 py-1 text-sm"
          >
            <option value="tree">tree</option>
            <option value="markdown">markdown</option>
          </select>
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium">{t("dashboard.structure")}</label>
          <textarea
            value={projectStructure}
            onChange={(e) => setProjectStructure(e.target.value)}
            rows={8}
            placeholder={t("dashboard.placeholder")}
            className="w-full rounded-md border border-muted bg-background px-3 py-2 text-sm font-mono"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-60"
        >
          {loading ? t("dashboard.running") : t("dashboard.run")}
        </button>
      </form>

      {job && (
        <div className="rounded-md border border-muted p-4 space-y-2 max-w-xl text-sm">
          <div className="font-medium">{t("dashboard.jobCreated")}</div>
          <div className="text-xs text-muted-foreground break-all">
            job_id: {job.job_id}
          </div>
          <div className="flex items-center gap-3">
            <span>
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
            <div className="text-xs text-red-400">Ошибка: {status.error}</div>
          )}
        </div>
      )}
    </div>
  );
}
