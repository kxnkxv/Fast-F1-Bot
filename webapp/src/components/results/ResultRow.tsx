import type { DriverResult } from "../../types/api";
import { TeamBadge } from "../common/TeamBadge";
import { formatTime, formatGap } from "../../lib/formatters";
import { getTeamColor } from "../../lib/constants";

interface ResultRowProps {
  result: DriverResult;
}

function PositionBadge({ position }: { position: number }) {
  const colors: Record<number, string> = {
    1: "var(--f1-gold)",
    2: "var(--f1-silver)",
    3: "var(--f1-bronze)",
  };
  const color = colors[position];

  if (color) {
    return (
      <span
        className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-black"
        style={{ backgroundColor: color }}
      >
        {position}
      </span>
    );
  }

  return (
    <span className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-[var(--f1-text-secondary)] bg-[var(--f1-border)]">
      {position}
    </span>
  );
}

export function ResultRow({ result }: ResultRowProps) {
  const teamColor = getTeamColor(result.team_slug);

  return (
    <div className="bg-[var(--f1-card-bg)] rounded-xl p-3">
      <div className="flex items-center gap-3">
        <PositionBadge position={result.position} />
        <div
          className="w-0.5 h-8 rounded-full flex-shrink-0"
          style={{ backgroundColor: teamColor }}
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm truncate">
              {result.driver_name}
            </span>
            <span className="text-xs font-mono text-[var(--f1-text-secondary)]">
              {result.driver_code}
            </span>
          </div>
          <TeamBadge teamSlug={result.team_slug} teamName={result.team} />
        </div>
        <div className="text-right">
          <span className="text-xs font-mono block">
            {result.position === 1
              ? formatTime(result.time)
              : formatGap(result.gap)}
          </span>
          {result.points > 0 && (
            <span className="text-[10px] text-[var(--f1-text-secondary)]">
              +{result.points} pts
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
