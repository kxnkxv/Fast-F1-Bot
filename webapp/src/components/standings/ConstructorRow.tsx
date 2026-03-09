import type { ConstructorStanding } from "../../types/api";
import { PointsBar } from "./PointsBar";
import { getTeamColor } from "../../lib/constants";

interface ConstructorRowProps {
  constructor: ConstructorStanding;
  maxPoints: number;
}

export function ConstructorRow({ constructor: c, maxPoints }: ConstructorRowProps) {
  const color = getTeamColor(c.team_slug);

  return (
    <div className="bg-[var(--f1-card-bg)] rounded-xl p-3">
      <div className="flex items-center gap-3">
        <span className="text-sm font-bold tabular-nums w-6 text-center text-[var(--f1-text-secondary)]">
          {c.position}
        </span>
        <div
          className="w-1 h-8 rounded-full flex-shrink-0"
          style={{ backgroundColor: color }}
        />
        <div className="flex-1 min-w-0">
          <span className="font-semibold text-sm truncate block">
            {c.team}
          </span>
          <PointsBar
            points={c.points}
            maxPoints={maxPoints}
            teamSlug={c.team_slug}
          />
        </div>
        {c.wins > 0 && (
          <span className="text-xs text-[var(--f1-text-secondary)]">
            {c.wins}W
          </span>
        )}
      </div>
    </div>
  );
}
