import type { DriverResult } from "../../types/api";
import { driverPhoto } from "../../lib/f1-assets";
import { getTeamColor, CURRENT_SEASON } from "../../lib/constants";
import { formatTime, formatGap } from "../../lib/formatters";

interface PodiumDisplayProps {
  results: DriverResult[];
}

export function PodiumDisplay({ results }: PodiumDisplayProps) {
  const top3 = results.slice(0, 3);
  if (top3.length < 3) return null;

  // Order: P2, P1, P3 for visual layout
  const podiumOrder = [top3[1]!, top3[0]!, top3[2]!];
  const heights = ["h-24", "h-32", "h-20"];
  const delays = ["0.2s", "0.1s", "0.3s"];
  const medals = ["\u{1F948}", "\u{1F947}", "\u{1F949}"];

  return (
    <div className="flex items-end justify-center gap-2 px-4 pt-4 pb-2">
      {podiumOrder.map((driver, i) => {
        const teamColor = getTeamColor(driver.team_slug);
        return (
          <div
            key={driver.driver_code}
            className="flex flex-col items-center flex-1 animate-rise"
            style={{ animationDelay: delays[i] }}
          >
            <div className="relative mb-2">
              <img
                src={driverPhoto(CURRENT_SEASON, driver.team_slug, driver.driver_code, 220)}
                alt={driver.driver_name}
                className="w-16 h-16 rounded-full object-cover object-top bg-[var(--f1-border)]"
                loading="eager"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = "none";
                }}
              />
              <span className="absolute -bottom-1 -right-1 text-lg">
                {medals[i]}
              </span>
            </div>
            <span className="text-xs font-bold text-center truncate w-full">
              {driver.driver_code}
            </span>
            <span className="text-[10px] text-[var(--f1-text-secondary)] truncate w-full text-center">
              {driver.position === 1
                ? formatTime(driver.time)
                : formatGap(driver.gap)}
            </span>
            <div
              className={`w-full ${heights[i]} rounded-t-lg mt-1 flex items-center justify-center`}
              style={{
                backgroundColor: teamColor,
                opacity: 0.8,
              }}
            >
              <span className="text-2xl font-black text-white/90">
                {driver.position}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
