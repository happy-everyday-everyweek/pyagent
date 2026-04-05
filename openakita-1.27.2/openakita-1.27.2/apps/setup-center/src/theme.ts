export type Theme = "light" | "dark" | "system";

export function initTheme() {
  const pref = (localStorage.getItem("openakita-theme-pref") as Theme) || "system";
  applyTheme(pref);

  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
  const listener = (e: MediaQueryListEvent) => {
    const currentPref = localStorage.getItem("openakita-theme-pref") as Theme | null;
    if (!currentPref || currentPref === "system") {
      document.documentElement.setAttribute("data-theme", e.matches ? "dark" : "light");
    }
  };

  // Modern browsers support addEventListener
  if (mediaQuery.addEventListener) {
    mediaQuery.addEventListener("change", listener);
  } else if (mediaQuery.addListener) {
    // Fallback for older Safari
    mediaQuery.addListener(listener);
  }
}

export function applyTheme(theme: Theme) {
  let activeTheme = theme;
  if (theme === "system") {
    activeTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  document.documentElement.setAttribute("data-theme", activeTheme);

  // Sync native window theme in Tauri
  if (typeof window !== "undefined" && "__TAURI_INTERNALS__" in window) {
    import("@tauri-apps/api/window").then(({ getCurrentWindow }) => {
      const win = getCurrentWindow();
      win.setTheme(theme === "system" ? null : theme);
    }).catch(() => {});
  }
}

export const THEME_CHANGE_EVENT = "openakita-theme-change";

export function setThemePref(theme: Theme) {
  localStorage.setItem("openakita-theme-pref", theme);
  applyTheme(theme);
  window.dispatchEvent(new CustomEvent(THEME_CHANGE_EVENT, { detail: theme }));
}

export function getThemePref(): Theme {
  return (localStorage.getItem("openakita-theme-pref") as Theme) || "system";
}
