import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Eye, EyeOff, Trash2 } from "lucide-react";
import { api } from "../../api/client";
import { useAuthStore } from "../../store/auth";
import { useAPI } from "../../hooks/useAPI";
import { useLanguage } from "../../hooks/useLanguage";

type CLITokenCreateResponse = {
  token: string;
  id: string;
  name: string | null;
  created_at: string;
};

type CLITokenListItem = {
  id: string;
  name: string | null;
  token: string | null;
  created_at: string;
};

export function CLIPage() {
  const { t } = useLanguage();
  const { notifyError, notifySuccess } = useAPI();
  const token = useAuthStore((s) => s.token);
  const [name, setName] = useState("");
  const [createdToken, setCreatedToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [visibleTokens, setVisibleTokens] = useState<Record<string, boolean>>({});

  const { data, error, refetch } = useQuery({
    queryKey: ["cli-tokens"],
    enabled: Boolean(token),
    queryFn: async () => {
      const res = await api.get<CLITokenListItem[]>("/auth/cli-tokens");
      return res.data;
    },
  });

  useEffect(() => {
    if (error) {
      notifyError(error, t("cli.loadError"));
    }
  }, [error, notifyError, t]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.post<CLITokenCreateResponse>("/auth/cli-tokens", {
        name: name.trim() || null,
      });
      setCreatedToken(res.data.token);
      setName("");
      refetch();
      notifySuccess(t("cli.created"));
    } catch (err) {
      notifyError(err, t("cli.createError"));
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!createdToken) return;
    try {
      await navigator.clipboard.writeText(createdToken);
      notifySuccess(t("cli.copySuccess"));
    } catch (err) {
      notifyError(err, t("cli.copyError"));
    }
  };

  const deleteMutation = useMutation({
    mutationFn: async (tokenId: string) => {
      await api.delete(`/auth/cli-tokens/${tokenId}`);
    },
    onSuccess: () => {
      notifySuccess(t("cli.deleteSuccess"));
      refetch();
    },
    onError: (err) => notifyError(err, t("cli.deleteError")),
  });

  if (!token) {
    return <p className="text-sm text-muted-foreground">{t("cli.authRequired")}</p>;
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">{t("cli.title")}</h1>
        <p className="max-w-3xl text-sm text-muted-foreground">{t("cli.description")}</p>
      </div>

      <section className="wt-panel mx-auto max-w-xl rounded-xl p-5 md:p-6">
        <form onSubmit={handleCreate} className="space-y-3">
          <div className="space-y-1">
            <label className="text-sm font-semibold">{t("cli.tokenName")}</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t("cli.tokenNamePlaceholder")}
              className="wt-input w-full rounded-md px-3 py-2 text-sm"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-60"
          >
            {loading ? t("cli.creating") : t("cli.create")}
          </button>
        </form>

        {createdToken && (
          <div className="mt-4 space-y-2">
            <div className="text-sm font-semibold">{t("cli.oneTime")}</div>
            <div className="break-all rounded-md border border-muted bg-background/60 px-2 py-2 font-mono text-xs">
              {createdToken}
            </div>
            <button
              type="button"
              onClick={handleCopy}
              className="rounded-md border border-muted px-3 py-1 text-xs"
            >
              {t("cli.copy")}
            </button>
          </div>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">{t("cli.listTitle")}</h2>
        {data && data.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("cli.empty")}</p>
        ) : (
          <div className="space-y-2">
            {data?.map((item) => (
              <article key={item.id} className="wt-panel rounded-xl p-4 text-sm">
                <div className="font-medium">{item.name || "default"}</div>
                <div className="mt-2 flex items-center gap-2">
                  <div className="min-h-8 flex-1 break-all rounded-md border border-muted bg-background/60 px-2 py-1 font-mono text-xs">
                    {!item.token ? "—" : (visibleTokens[item.id] ? item.token : "****")}
                  </div>
                  <button
                    type="button"
                    disabled={!item.token}
                    onClick={() =>
                      setVisibleTokens((prev) => ({ ...prev, [item.id]: !prev[item.id] }))
                    }
                    className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-muted disabled:opacity-40"
                    title={visibleTokens[item.id] ? t("cli.hide") : t("cli.show")}
                  >
                    {visibleTokens[item.id] ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                  <button
                    type="button"
                    onClick={() => deleteMutation.mutate(item.id)}
                    disabled={deleteMutation.isPending}
                    className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-red-400/40 text-red-300 disabled:opacity-40"
                    title={t("cli.delete")}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
                <div className="text-xs text-muted-foreground">
                  {new Date(item.created_at).toLocaleString()}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
