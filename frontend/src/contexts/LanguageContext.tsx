import { createContext, useContext, useState, ReactNode } from 'react';
import { translations, Lang } from '@/infrastructure/i18n/translations';

interface LanguageContextValue {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextValue>({
  lang: 'ru',
  setLang: () => {},
  t: (k) => k,
});

const LANGS: Lang[] = ['ru', 'en', 'sk', 'pl'];

export const LanguageProvider = ({ children }: { children: ReactNode }) => {
  const [lang, setLangState] = useState<Lang>(() => {
    const saved = localStorage.getItem('lang');
    return saved && LANGS.indexOf(saved as Lang) >= 0 ? (saved as Lang) : 'ru';
  });

  const setLang = (l: Lang) => {
    setLangState(l);
    localStorage.setItem('lang', l);
  };

  const t = (key: string) => {
    const dict = translations[lang] || translations.ru;
    return dict[key] || translations.ru[key] || key;
  };

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => useContext(LanguageContext);
