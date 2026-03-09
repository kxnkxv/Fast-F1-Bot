export const CURRENT_SEASON = 2025;

export const CDN_BASE_URL = "https://media.formula1.com";

export const TEAM_COLORS: Record<string, string> = {
  "red-bull-racing": "#3671C6",
  "mercedes": "#27F4D2",
  "ferrari": "#E8002D",
  "mclaren": "#FF8000",
  "aston-martin": "#229971",
  "alpine": "#0093CC",
  "williams": "#64C4FF",
  "rb": "#6692FF",
  "kick-sauber": "#52E252",
  "haas": "#B6BABD",
  // Fallback / legacy
  "alphatauri": "#5E8FAA",
  "alfa-romeo": "#C92D4B",
  "racing-point": "#F596C8",
  "renault": "#FFF500",
  "toro-rosso": "#469BFF",
};

export const TEAM_DISPLAY_NAMES: Record<string, string> = {
  "red-bull-racing": "Red Bull Racing",
  "mercedes": "Mercedes",
  "ferrari": "Ferrari",
  "mclaren": "McLaren",
  "aston-martin": "Aston Martin",
  "alpine": "Alpine",
  "williams": "Williams",
  "rb": "RB",
  "kick-sauber": "Kick Sauber",
  "haas": "Haas",
};

export function getTeamColor(teamSlug: string): string {
  return TEAM_COLORS[teamSlug] ?? "#888888";
}
