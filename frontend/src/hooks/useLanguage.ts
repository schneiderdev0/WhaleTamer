import { messages, type Language, type MessageKey } from "../i18n/messages";
import { usePreferencesStore } from "../store/preferences";

export function useLanguage() {
  const language = usePreferencesStore((s) => s.language);
  const setLanguage = usePreferencesStore((s) => s.setLanguage);

  const t = (key: MessageKey): string => messages[language][key];

  return { language, setLanguage: (nextLanguage: Language) => setLanguage(nextLanguage), t };
}
