import React, { createContext, useContext, useEffect, useState, useMemo } from "react";
import translations from "@/i18n";

const LangContext = createContext({ lang: "ru", setLang: () => {}, t: translations.ru });

export const LangProvider = ({ children }) => {
  const [lang, setLang] = useState(() => {
    if (typeof window === "undefined") return "ru";
    const stored = window.localStorage.getItem("innercore.lang");
    if (stored === "ru" || stored === "en") return stored;
    return "ru";
  });

  useEffect(() => {
    window.localStorage.setItem("innercore.lang", lang);
    document.documentElement.setAttribute("lang", lang);
  }, [lang]);

  const value = useMemo(() => ({ lang, setLang, t: translations[lang] }), [lang]);
  return <LangContext.Provider value={value}>{children}</LangContext.Provider>;
};

export const useLang = () => useContext(LangContext);
