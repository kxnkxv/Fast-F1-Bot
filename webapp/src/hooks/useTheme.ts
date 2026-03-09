import { useMemo, useEffect } from "react";
import { useTelegram } from "./useTelegram";

export interface F1Theme {
  bg: string;
  cardBg: string;
  textPrimary: string;
  textSecondary: string;
  accent: string;
  border: string;
}

const DEFAULT_THEME: F1Theme = {
  bg: "#15151E",
  cardBg: "#1F1F2E",
  textPrimary: "#FFFFFF",
  textSecondary: "#9CA3AF",
  accent: "#E10600",
  border: "#2D2D3D",
};

export function useTheme(): F1Theme {
  const { themeParams, colorScheme } = useTelegram();

  const theme = useMemo<F1Theme>(() => {
    if (colorScheme === "light") {
      return {
        bg: themeParams.bg_color ?? "#F5F5F5",
        cardBg: themeParams.secondary_bg_color ?? "#FFFFFF",
        textPrimary: themeParams.text_color ?? "#1A1A1A",
        textSecondary: themeParams.hint_color ?? "#6B7280",
        accent: "#E10600",
        border: "#E5E7EB",
      };
    }
    return {
      ...DEFAULT_THEME,
      bg: themeParams.bg_color ?? DEFAULT_THEME.bg,
      cardBg: themeParams.secondary_bg_color ?? DEFAULT_THEME.cardBg,
      textPrimary: themeParams.text_color ?? DEFAULT_THEME.textPrimary,
      textSecondary: themeParams.hint_color ?? DEFAULT_THEME.textSecondary,
    };
  }, [themeParams, colorScheme]);

  useEffect(() => {
    const root = document.documentElement;
    root.style.setProperty("--f1-bg", theme.bg);
    root.style.setProperty("--f1-card-bg", theme.cardBg);
    root.style.setProperty("--f1-text-primary", theme.textPrimary);
    root.style.setProperty("--f1-text-secondary", theme.textSecondary);
    root.style.setProperty("--f1-accent", theme.accent);
    root.style.setProperty("--f1-border", theme.border);
  }, [theme]);

  return theme;
}
