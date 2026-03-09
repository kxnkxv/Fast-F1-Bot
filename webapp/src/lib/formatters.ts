export function formatTime(time: string | null): string {
  if (!time) return "DNF";
  return time;
}

export function formatPoints(points: number): string {
  return points % 1 === 0 ? points.toString() : points.toFixed(1);
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
  });
}

export function formatDateFull(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function formatGap(gap: string | null): string {
  if (!gap) return "—";
  return gap;
}

export function formatCountdown(targetDate: string): {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  isPast: boolean;
} {
  const now = new Date().getTime();
  const target = new Date(targetDate).getTime();
  const diff = target - now;

  if (diff <= 0) {
    return { days: 0, hours: 0, minutes: 0, seconds: 0, isPast: true };
  }

  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((diff % (1000 * 60)) / 1000);

  return { days, hours, minutes, seconds, isPast: false };
}

export function formatSessionName(session: string): string {
  const map: Record<string, string> = {
    R: "Race",
    Q: "Qualifying",
    S: "Sprint",
    SQ: "Sprint Qualifying",
    FP1: "Practice 1",
    FP2: "Practice 2",
    FP3: "Practice 3",
  };
  return map[session] ?? session;
}

export function countryFlag(country: string): string {
  const flags: Record<string, string> = {
    Bahrain: "\u{1F1E7}\u{1F1ED}",
    "Saudi Arabia": "\u{1F1F8}\u{1F1E6}",
    Australia: "\u{1F1E6}\u{1F1FA}",
    Japan: "\u{1F1EF}\u{1F1F5}",
    China: "\u{1F1E8}\u{1F1F3}",
    USA: "\u{1F1FA}\u{1F1F8}",
    "United States": "\u{1F1FA}\u{1F1F8}",
    Italy: "\u{1F1EE}\u{1F1F9}",
    Monaco: "\u{1F1F2}\u{1F1E8}",
    Canada: "\u{1F1E8}\u{1F1E6}",
    Spain: "\u{1F1EA}\u{1F1F8}",
    Austria: "\u{1F1E6}\u{1F1F9}",
    UK: "\u{1F1EC}\u{1F1E7}",
    "Great Britain": "\u{1F1EC}\u{1F1E7}",
    Hungary: "\u{1F1ED}\u{1F1FA}",
    Belgium: "\u{1F1E7}\u{1F1EA}",
    Netherlands: "\u{1F1F3}\u{1F1F1}",
    Singapore: "\u{1F1F8}\u{1F1EC}",
    Azerbaijan: "\u{1F1E6}\u{1F1FF}",
    Mexico: "\u{1F1F2}\u{1F1FD}",
    Brazil: "\u{1F1E7}\u{1F1F7}",
    "Las Vegas": "\u{1F1FA}\u{1F1F8}",
    Qatar: "\u{1F1F6}\u{1F1E6}",
    "Abu Dhabi": "\u{1F1E6}\u{1F1EA}",
    UAE: "\u{1F1E6}\u{1F1EA}",
    Portugal: "\u{1F1F5}\u{1F1F9}",
    France: "\u{1F1EB}\u{1F1F7}",
    Germany: "\u{1F1E9}\u{1F1EA}",
    Russia: "\u{1F1F7}\u{1F1FA}",
    Turkey: "\u{1F1F9}\u{1F1F7}",
  };
  return flags[country] ?? "\u{1F3C1}";
}
