import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
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

type TelegramNotificationSettings = {
  enabled: boolean;
  frequency: "event" | "hourly" | "daily";
  severity: "all" | "critical";
};

type TelegramNotificationSettingsResponse = {
  linked: boolean;
  chat_id: number | null;
  username: string | null;
  settings: TelegramNotificationSettings;
};

export function TelegramSettingsPage() {
  const { notifyError, notifySuccess } = useAPI();
  const { t } = useLanguage();
  const [enabled, setEnabled] = useState(true);
  const [frequency, setFrequency] = useState<"event" | "hourly" | "daily">("event");
  const [severity, setSeverity] = useState<"all" | "critical">("all");

  const { data, refetch, isLoading, error } = useQuery({
    queryKey: ["telegram-me"],
    queryFn: async () => {
      const res = await api.get<TelegramLinkedInfo>("/telegram/me");
      return res.data;
    },
  });

  const settingsQuery = useQuery({
    queryKey: ["telegram-notification-settings"],
    queryFn: async () => {
      const res = await api.get<TelegramNotificationSettingsResponse>(
        "/telegram/notification-settings"
      );
      return res.data;
    },
  });

  useEffect(() => {
    if (error) {
      notifyError(error, t("telegram.statusError"));
    }
  }, [error, notifyError, t]);

  useEffect(() => {
    if (settingsQuery.error) {
      notifyError(settingsQuery.error, t("telegram.settingsLoadError"));
    }
  }, [settingsQuery.error, notifyError, t]);

  useEffect(() => {
    const settings = settingsQuery.data?.settings;
    if (!settings) return;
    setEnabled(settings.enabled);
    setFrequency(settings.frequency);
    setSeverity(settings.severity);
  }, [settingsQuery.data]);

  const linkMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post<TelegramLinkTokenResponse>("/telegram/link-token");
      return res.data;
    },
  });

  const saveSettingsMutation = useMutation({
    mutationFn: async () => {
      const res = await api.put<TelegramNotificationSettingsResponse>(
        "/telegram/notification-settings",
        {
          enabled,
          frequency,
          severity,
        }
      );
      return res.data;
    },
  });

  const handleCreateLink = async () => {
    try {
      const token = await linkMutation.mutateAsync();
      await navigator.clipboard.writeText(token.token);
      notifySuccess(t("telegram.copySuccess"));
      refetch();
      settingsQuery.refetch();
    } catch (error) {
      notifyError(error, t("telegram.tokenError"));
    }
  };

  const handleSaveSettings = async () => {
    try {
      await saveSettingsMutation.mutateAsync();
      notifySuccess(t("telegram.settingsSaved"));
      settingsQuery.refetch();
    } catch (error) {
      notifyError(error, t("telegram.settingsSaveError"));
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
                chat_id: {data.chat_id} {data.username ? `(t.me/${data.username})` : null}
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
      <p className="text-xs text-muted-foreground">{t("telegram.tokenHint")}</p>

      <div className="rounded-md border border-muted p-4 space-y-3 text-sm">
        <div className="font-medium">{t("telegram.settingsTitle")}</div>
        {!settingsQuery.data?.linked ? (
          <p className="text-muted-foreground">{t("telegram.settingsUnavailable")}</p>
        ) : (
          <>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
              />
              {t("telegram.settingsEnabled")}
            </label>

            <label className="space-y-1 block">
              <span>{t("telegram.settingsFrequency")}</span>
              <select
                value={frequency}
                onChange={(e) =>
                  setFrequency(e.target.value as "event" | "hourly" | "daily")
                }
                className="w-full rounded-md border border-muted bg-background px-2 py-1"
              >
                <option value="event">{t("telegram.frequency.event")}</option>
                <option value="hourly">{t("telegram.frequency.hourly")}</option>
                <option value="daily">{t("telegram.frequency.daily")}</option>
              </select>
            </label>

            <label className="space-y-1 block">
              <span>{t("telegram.settingsSeverity")}</span>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value as "all" | "critical")}
                className="w-full rounded-md border border-muted bg-background px-2 py-1"
              >
                <option value="all">{t("telegram.severity.all")}</option>
                <option value="critical">{t("telegram.severity.critical")}</option>
              </select>
            </label>

            <button
              type="button"
              onClick={handleSaveSettings}
              disabled={saveSettingsMutation.isPending || settingsQuery.isLoading}
              className="inline-flex items-center rounded-md border border-muted px-4 py-2 text-sm disabled:opacity-60"
            >
              {saveSettingsMutation.isPending
                ? t("telegram.settingsSaving")
                : t("telegram.settingsSave")}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
