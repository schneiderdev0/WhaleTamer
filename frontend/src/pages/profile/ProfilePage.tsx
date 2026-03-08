import { useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";
import { useAuthStore } from "../../store/auth";
import { useAPI } from "../../hooks/useAPI";
import { useLanguage } from "../../hooks/useLanguage";

type ProfileResponse = {
  user_id: string;
  email: string;
  auth_type: string;
  github_connected: boolean;
};

type GithubLoginResponse = {
  url: string;
};

export function ProfilePage() {
  const { t } = useLanguage();
  const { notifyError, notifySuccess } = useAPI();
  const clearAuth = useAuthStore((s) => s.clear);
  const authUser = useAuthStore((s) => s.user);

  const { data, error, refetch } = useQuery({
    queryKey: ["profile"],
    queryFn: async () => (await api.get<ProfileResponse>("/auth/me")).data,
  });

  useEffect(() => {
    if (error) notifyError(error, t("profile.loadError"));
  }, [error, notifyError, t]);

  const unlinkMutation = useMutation({
    mutationFn: async () => {
      await api.delete("/auth/github/unlink");
    },
    onSuccess: () => {
      notifySuccess(t("profile.githubUnlinked"));
      refetch();
    },
    onError: (err) => notifyError(err, t("profile.githubUnlinkError")),
  });

  const linkGithub = async () => {
    try {
      const res = await api.get<GithubLoginResponse>("/auth/github/login");
      window.location.href = res.data.url;
    } catch (err) {
      notifyError(err, t("profile.githubLinkError"));
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">{t("profile.title")}</h1>
        <p className="text-sm text-muted-foreground">{t("profile.description")}</p>
      </div>

      <section className="wt-panel mx-auto max-w-xl rounded-xl p-5 md:p-6">
        <div className="space-y-2 text-sm">
          <div>
            <span className="text-muted-foreground">{t("profile.userId")}:</span>{" "}
            <span className="font-mono">{data?.user_id ?? authUser?.id ?? "—"}</span>
          </div>
          <div>
            <span className="text-muted-foreground">{t("profile.email")}:</span>{" "}
            <span>{data?.email ?? authUser?.email ?? "—"}</span>
          </div>
          <div>
            <span className="text-muted-foreground">{t("profile.githubStatus")}:</span>{" "}
            <span>{data?.github_connected ? t("profile.connected") : t("profile.notConnected")}</span>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => {
              clearAuth();
              notifySuccess(t("profile.loggedOut"));
            }}
            className="rounded-md border border-muted px-4 py-2 text-sm font-semibold"
          >
            {t("profile.logout")}
          </button>

          {!data?.github_connected ? (
            <button
              type="button"
              onClick={linkGithub}
              className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-400"
            >
              {t("profile.linkGithub")}
            </button>
          ) : (
            <button
              type="button"
              onClick={() => unlinkMutation.mutate()}
              disabled={unlinkMutation.isPending}
              className="rounded-md border border-red-400/40 bg-red-400/10 px-4 py-2 text-sm font-semibold text-red-300 disabled:opacity-60"
            >
              {unlinkMutation.isPending ? t("profile.unlinking") : t("profile.unlinkGithub")}
            </button>
          )}
        </div>
      </section>
    </div>
  );
}
