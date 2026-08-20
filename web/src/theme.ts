// Preferências de aparência: tema (cores) e layout (densidade de recursos).
// Persistidas em localStorage e aplicadas em <html> via data-attributes, para
// que o CSS troque só os tokens. Sem backend — é escolha do dispositivo.

export type Theme = "tatico" | "coyote" | "urbano";
export type Layout = "full" | "light";

export const THEMES: Array<{ id: Theme; label: string; swatch: string }> = [
  { id: "tatico", label: "Tático", swatch: "#3b82f6" },
  { id: "coyote", label: "Coyote", swatch: "#c08a4f" },
  { id: "urbano", label: "Urbano", swatch: "#7c8ea6" },
];

export const LAYOUTS: Array<{ id: Layout; label: string; hint: string }> = [
  { id: "full", label: "Completo", hint: "Todas as abas, inclusive balística e recarga." },
  { id: "light", label: "Essencial", hint: "Só o dia a dia do CAC — esconde as abas técnicas." },
];

const THEME_KEY = "bp.theme";
const LAYOUT_KEY = "bp.layout";

export function getTheme(): Theme {
  const v = localStorage.getItem(THEME_KEY);
  return v === "coyote" || v === "urbano" ? v : "tatico";
}

export function getLayout(): Layout {
  return localStorage.getItem(LAYOUT_KEY) === "light" ? "light" : "full";
}

export function applyTheme(t: Theme) {
  const root = document.documentElement;
  if (t === "tatico") root.removeAttribute("data-theme");
  else root.setAttribute("data-theme", t);
  localStorage.setItem(THEME_KEY, t);
}

export function applyLayout(l: Layout) {
  document.documentElement.setAttribute("data-layout", l);
  localStorage.setItem(LAYOUT_KEY, l);
}

// Chamado uma vez no boot, antes de renderizar, para não “piscar” o tema.
export function initAppearance() {
  applyTheme(getTheme());
  applyLayout(getLayout());
}
