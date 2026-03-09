import { useMemo, useEffect } from "react";

export function useTelegram() {
  const webApp = useMemo(() => {
    try {
      return window.Telegram?.WebApp;
    } catch {
      return undefined;
    }
  }, []);

  const user = useMemo(() => webApp?.initDataUnsafe?.user, [webApp]);

  const colorScheme = useMemo(
    () => webApp?.colorScheme ?? "dark",
    [webApp]
  );

  const themeParams = useMemo(() => webApp?.themeParams ?? {}, [webApp]);

  useEffect(() => {
    if (webApp) {
      webApp.ready();
      webApp.expand();
      webApp.setHeaderColor("#15151E");
      webApp.setBackgroundColor("#15151E");
    }
  }, [webApp]);

  return {
    webApp,
    user,
    colorScheme,
    themeParams,
    ready: () => webApp?.ready(),
  };
}
