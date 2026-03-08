import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { useAuthStore } from "../../store/auth";
import { useAPI } from "../../hooks/useAPI";
import { useLanguage } from "../../hooks/useLanguage";

type GithubLoginResponse = {
  url: string;
};

type LoginResponse = {
  access_token: string;
};

export function AuthPage() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();
  const { notifyError, notifySuccess } = useAPI();
  const { t } = useLanguage();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [repassword, setRepassword] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");

    if (token) {
      void (async () => {
        try {
          const verifyRes = await api.get<{ user_id: string; email: string }>("/auth/verify", {
            headers: { Authorization: `Bearer ${token}` },
          });
          setAuth(token, {
            id: verifyRes.data.user_id,
            email: verifyRes.data.email,
          });
          navigate("/projects", { replace: true });
        } catch (error) {
          notifyError(error, t("auth.callbackError"));
        }
      })();
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

  const handleEmailLogin = async () => {
    const loginRes = await api.post<LoginResponse>("/auth/login", { email, password });
    const accessToken = loginRes.data.access_token;
    const verifyRes = await api.get<{ user_id: string; email: string }>("/auth/verify", {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    setAuth(accessToken, {
      id: verifyRes.data.user_id,
      email: verifyRes.data.email,
    });
    navigate("/projects", { replace: true });
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode === "register") {
        await api.post("/auth/register", {
          email,
          password,
          repassword,
        });
        notifySuccess(t("auth.registerSuccess"));
      }
      await handleEmailLogin();
    } catch (error) {
      notifyError(error, mode === "login" ? t("auth.emailLoginError") : t("auth.registerError"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-3xl flex-col items-center space-y-6 text-center">
      <div className="max-w-xl space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">{t("auth.title")}</h1>
        <p className="text-sm text-muted-foreground">{t("auth.description")}</p>
      </div>

      <section className="wt-panel w-full max-w-xl rounded-xl p-5 md:p-6">
        <div className="mb-5 rounded-xl bg-muted/40 p-1">
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setMode("login")}
              className={`rounded-md px-3 py-2 text-sm font-semibold transition ${
                mode === "login"
                  ? "bg-background text-foreground shadow-sm ring-1 ring-muted"
                  : "bg-transparent text-muted-foreground hover:bg-background/60 hover:text-foreground"
              }`}
            >
              {t("auth.emailLogin")}
            </button>
            <button
              type="button"
              onClick={() => setMode("register")}
              className={`rounded-md px-3 py-2 text-sm font-semibold transition ${
                mode === "register"
                  ? "bg-background text-foreground shadow-sm ring-1 ring-muted"
                  : "bg-transparent text-muted-foreground hover:bg-background/60 hover:text-foreground"
              }`}
            >
              {t("auth.emailRegister")}
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={t("auth.email")}
            className="wt-input w-full rounded-md px-3 py-2 text-sm text-left"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={t("auth.password")}
            className="wt-input w-full rounded-md px-3 py-2 text-sm text-left"
          />
          {mode === "register" && (
            <input
              type="password"
              value={repassword}
              onChange={(e) => setRepassword(e.target.value)}
              placeholder={t("auth.repassword")}
              className="wt-input w-full rounded-md px-3 py-2 text-sm text-left"
            />
          )}
          <button
            type="submit"
            disabled={loading}
            className="inline-flex w-full items-center justify-center rounded-md border border-primary/50 bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-60"
          >
            {loading
              ? t("auth.processing")
              : mode === "login"
                ? t("auth.emailLogin")
                : t("auth.emailRegister")}
          </button>
        </form>

        <div className="my-4 h-px bg-muted/60" />
        <button
          type="button"
          onClick={handleGithub}
          className="inline-flex w-full items-center justify-center rounded-md border border-emerald-300/70 bg-emerald-500 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-400"
        >
          {t("auth.github")}
        </button>
      </section>
    </div>
  );
}
