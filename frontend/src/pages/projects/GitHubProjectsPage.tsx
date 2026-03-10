import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";
import { useAPI } from "../../hooks/useAPI";
import { useLanguage } from "../../hooks/useLanguage";

type GitHubStatusResponse = {
  connected: boolean;
};

type GitHubRepo = {
  id: number;
  name: string;
  full_name: string;
  private: boolean;
  html_url: string;
  default_branch: string;
};

type GitHubBranch = {
  name: string;
};

type Project = {
  id: string;
  github_repo_id: number;
  name: string;
  full_name: string;
  html_url: string;
  default_branch: string;
  selected_branch: string;
  created_at: string;
};

type SyncDockerResponse = {
  project_id: string;
  branch: string;
  committed_files: string[];
};

export function GitHubProjectsPage() {
  const { t } = useLanguage();
  const { notifyError, notifySuccess } = useAPI();
  const [repoId, setRepoId] = useState<number | null>(null);
  const [selectedBranch, setSelectedBranch] = useState("main");
  const [syncInfo, setSyncInfo] = useState<SyncDockerResponse | null>(null);

  const { data: githubStatus, error: githubStatusError } = useQuery({
    queryKey: ["github-status"],
    queryFn: async () => (await api.get<GitHubStatusResponse>("/auth/github/status")).data,
  });

  const githubConnected = Boolean(githubStatus?.connected);

  const { data: repos, error: reposError } = useQuery({
    queryKey: ["github-repositories"],
    enabled: githubConnected,
    queryFn: async () => (await api.get<GitHubRepo[]>("/auth/github/repositories")).data,
  });

  const { data: branches, error: branchesError, isLoading: branchesLoading } = useQuery({
    queryKey: ["github-repository-branches", repoId],
    enabled: githubConnected && repoId !== null,
    queryFn: async () =>
      (await api.get<GitHubBranch[]>(`/auth/github/repositories/${repoId}/branches`)).data,
  });

  const { data: projects, error: projectsError, refetch: refetchProjects } = useQuery({
    queryKey: ["projects"],
    queryFn: async () => (await api.get<Project[]>("/projects")).data,
  });

  useEffect(() => {
    if (githubStatusError) notifyError(githubStatusError, t("projects.githubStatusError"));
    if (reposError) notifyError(reposError, t("projects.reposLoadError"));
    if (branchesError) notifyError(branchesError, t("projects.reposLoadError"));
    if (projectsError) notifyError(projectsError, t("projects.projectsLoadError"));
  }, [githubStatusError, reposError, branchesError, projectsError, notifyError, t]);

  useEffect(() => {
    if (!repos || repos.length === 0) return;
    const first = repos[0];
    if (repoId === null) {
      setRepoId(first.id);
      setSelectedBranch(first.default_branch || "main");
    }
  }, [repos, repoId]);

  useEffect(() => {
    if (!branches || branches.length === 0) return;
    const hasSelectedBranch = branches.some((branch) => branch.name === selectedBranch);
    if (!hasSelectedBranch) {
      setSelectedBranch(branches[0].name);
    }
  }, [branches, selectedBranch]);

  const selectedRepo = useMemo(
    () => repos?.find((r) => r.id === repoId) ?? null,
    [repos, repoId]
  );

  const linkMutation = useMutation({
    mutationFn: async () => {
      if (!selectedRepo) return;
      await api.post("/projects/link", {
        github_repo_id: selectedRepo.id,
        name: selectedRepo.name,
        full_name: selectedRepo.full_name,
        html_url: selectedRepo.html_url,
        default_branch: selectedRepo.default_branch || "main",
        selected_branch: selectedBranch || selectedRepo.default_branch || "main",
      });
    },
    onSuccess: () => {
      notifySuccess(t("projects.linkedSuccess"));
      refetchProjects();
    },
    onError: (error) => notifyError(error, t("projects.linkError")),
  });

  const syncMutation = useMutation({
    mutationFn: async (projectId: string) => {
      const res = await api.post<SyncDockerResponse>(`/projects/${projectId}/sync-docker`);
      return res.data;
    },
    onSuccess: (payload) => {
      setSyncInfo(payload);
      notifySuccess(t("projects.syncSuccess"));
    },
    onError: (error) => notifyError(error, t("projects.syncError")),
  });

  const handleGithubConnect = async () => {
    try {
      const res = await api.get<{ url: string }>("/auth/github/login");
      window.location.href = res.data.url;
    } catch (error) {
      notifyError(error, t("profile.githubLinkError"));
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">{t("projects.title")}</h1>
        <p className="max-w-3xl text-sm text-muted-foreground">{t("projects.description")}</p>
      </div>

      <section className="wt-panel rounded-xl p-5 md:p-6">
        {!githubConnected ? (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">{t("projects.githubConnectRequired")}</p>
            <button
              type="button"
              onClick={handleGithubConnect}
              className="inline-flex items-center rounded-md border border-emerald-300/70 bg-emerald-500 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-400"
            >
              {t("projects.connectGithub")}
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="space-y-1">
              <label className="text-sm font-semibold">{t("projects.repo")}</label>
              <select
                value={repoId ?? ""}
                onChange={(e) => {
                  const next = Number(e.target.value);
                  const repo = repos?.find((r) => r.id === next);
                  setRepoId(next);
                  setSelectedBranch(repo?.default_branch || "main");
                }}
                className="wt-input w-full rounded-md px-3 py-2 text-sm"
              >
                {repos?.map((repo) => (
                  <option key={repo.id} value={repo.id}>
                    {repo.full_name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-sm font-semibold">{t("projects.branch")}</label>
              <select
                value={selectedBranch}
                onChange={(e) => setSelectedBranch(e.target.value)}
                disabled={branchesLoading || !branches || branches.length === 0}
                className="wt-input w-full rounded-md px-3 py-2 text-sm disabled:opacity-60"
              >
                {branchesLoading ? (
                  <option value="">{t("projects.branchLoading")}</option>
                ) : (
                  branches?.map((branch) => (
                    <option key={branch.name} value={branch.name}>
                      {branch.name}
                    </option>
                  ))
                )}
              </select>
            </div>
            <button
              type="button"
              disabled={!selectedRepo || !selectedBranch || linkMutation.isPending}
              onClick={() => linkMutation.mutate()}
              className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-60"
            >
              {linkMutation.isPending ? t("projects.linking") : t("projects.link")}
            </button>
          </div>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">{t("projects.listTitle")}</h2>
        {projects && projects.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("projects.empty")}</p>
        ) : (
          <div className="space-y-2">
            {projects?.map((p) => (
              <article key={p.id} className="wt-panel rounded-xl p-4">
                <div className="font-medium">{p.full_name}</div>
                <div className="text-xs text-muted-foreground">
                  branch: {p.selected_branch} • {new Date(p.created_at).toLocaleString()}
                </div>
                <button
                  type="button"
                  onClick={() => syncMutation.mutate(p.id)}
                  disabled={syncMutation.isPending && syncMutation.variables === p.id}
                  className="mt-3 rounded-md border border-muted px-3 py-1 text-xs font-semibold hover:bg-muted/40 disabled:opacity-60"
                >
                  {syncMutation.isPending && syncMutation.variables === p.id
                    ? t("projects.syncing")
                    : t("projects.sync")}
                </button>
              </article>
            ))}
          </div>
        )}
      </section>

      {syncInfo && (
        <section className="wt-panel max-w-xl rounded-xl p-4 text-sm">
          <div className="font-semibold">{t("projects.syncResult")}</div>
          <div className="text-xs text-muted-foreground">
            branch: {syncInfo.branch}
          </div>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-xs">
            {syncInfo.committed_files.map((path) => (
              <li key={path}>{path}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
