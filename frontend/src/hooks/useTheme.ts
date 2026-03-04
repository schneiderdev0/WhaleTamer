import { useEffect } from "react";
import { usePreferencesStore, type Theme } from "../store/preferences";

export function useTheme() {
  const theme = usePreferencesStore((s) => s.theme);
  const setTheme = usePreferencesStore((s) => s.setTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark");
  };

  return { theme, setTheme: (nextTheme: Theme) => setTheme(nextTheme), toggleTheme };
}
