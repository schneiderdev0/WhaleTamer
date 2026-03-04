import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Language } from "../i18n/messages";

export type Theme = "dark" | "light";

type PreferencesState = {
  theme: Theme;
  language: Language;
  setTheme: (theme: Theme) => void;
  setLanguage: (language: Language) => void;
};

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      theme: "dark",
      language: "ru",
      setTheme: (theme) => set({ theme }),
      setLanguage: (language) => set({ language }),
    }),
    {
      name: "wt-preferences",
    }
  )
);
