import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { api } from "../../api/client";
import { useAPI } from "../../hooks/useAPI";
import { useLanguage } from "../../hooks/useLanguage";

type TelegramLinkedInfo = {
  linked: boolean;
  chat_id: number | null;
  username: string | null;
};

type TelegramLinkTokenResponse = {
  token: string;
};

export function TelegramSettingsPage() {
  const { notifyError, notifySuccess } = useAPI();
  const { t } = useLanguage();
  const { data, refetch, isLoading, error } = useQuery({
    queryKey: ["telegram-me"],
    queryFn: async () => {
      const res = await api.get<TelegramLinkedInfo>("/telegram/me");
      return res.data;
    },
  });

  const linkMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post<TelegramLinkTokenResponse>("/telegram/link-token");
      return res.data;
    },
  });

  useEffect(() => {
    if (error) {
      notifyError(error, t("telegram.statusError"));
    }
  }, [error, notifyError, t]);

  const handleCreateLink = async () => {
    try {
      const token = await linkMutation.mutateAsync();
      await navigator.clipboard.writeText(token.token);
      notifySuccess(t("telegram.copySuccess"));
      refetch();
    } catch (error) {
      notifyError(error, t("telegram.tokenError"));
    }
  };

  return (
    <div className="space-y-4 max-w-xl">
      <h1 className="text-2xl font-semibold">{t("telegram.title")}</h1>
      <p className="text-sm text-muted-foreground">{t("telegram.description")}</p>

      {isLoading ? (
        <p className="text-sm">{t("telegram.loadingStatus")}</p>
      ) : (
        <div className="rounded-md border border-muted p-4 space-y-2 text-sm">
          <div className="font-medium">{t("telegram.status")}</div>
          {data?.linked ? (
            <>
              <div>{t("telegram.linked")}</div>
              <div className="text-xs text-muted-foreground">
                chat_id: {data.chat_id}{" "}
                {data.username ? `(t.me/${data.username})` : null}
              </div>
            </>
          ) : (
            <div className="text-muted-foreground">{t("telegram.notLinked")}</div>
          )}
        </div>
      )}

      <button
        type="button"
        onClick={handleCreateLink}
        disabled={linkMutation.isPending}
        className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-60"
      >
        {linkMutation.isPending ? t("telegram.creatingToken") : t("telegram.createToken")}
      </button>
      <p className="text-xs text-muted-foreground">
        {t("telegram.tokenHint")}
      </p>
    </div>
  );
}
