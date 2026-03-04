import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { useAuthStore } from "../../store/auth";
import { useAPI } from "../../hooks/useAPI";
import { useLanguage } from "../../hooks/useLanguage";

type GithubLoginResponse = {
  url: string;
};

export function AuthPage() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();
  const { notifyError } = useAPI();
  const { t } = useLanguage();

  useEffect(() => {
    // Если на нас вернулись с ?token=...&user_id=...&email=...
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    const userId = params.get("user_id");
    const email = params.get("email");
    if (token && userId && email) {
      setAuth(token, { id: userId, email });
      navigate("/dashboard", { replace: true });
      return;
    }
    if (params.size > 0) {
      notifyError(null, t("auth.callbackError"));
    }
  }, [setAuth, navigate, notifyError, t]);

  const handleGithub = async () => {
    try {
      const res = await api.get<GithubLoginResponse>("/auth/github/login");
      window.location.href = res.data.url;
    } catch (error) {
      notifyError(error, t("auth.loginError"));
    }
  };

  return (
    <div className="space-y-4 max-w-md">
      <h1 className="text-2xl font-semibold">{t("auth.title")}</h1>
      <p className="text-muted-foreground text-sm">{t("auth.description")}</p>
      <button
        type="button"
        onClick={handleGithub}
        className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
      >
        {t("auth.github")}
      </button>
    </div>
  );
}
