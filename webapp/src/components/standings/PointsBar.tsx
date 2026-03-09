import { getTeamColor } from "../../lib/constants";

interface PointsBarProps {
  points: number;
  maxPoints: number;
  teamSlug: string;
}

export function PointsBar({ points, maxPoints, teamSlug }: PointsBarProps) {
  const color = getTeamColor(teamSlug);
  const percentage = maxPoints > 0 ? (points / maxPoints) * 100 : 0;

  return (
    <div className="flex items-center gap-2 mt-1">
      <div className="flex-1 h-1.5 bg-[var(--f1-border)] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full animate-grow"
          style={{
            width: `${percentage}%`,
            backgroundColor: color,
          }}
        />
      </div>
      <span className="text-xs font-bold tabular-nums min-w-[40px] text-right">
        {points}
      </span>
    </div>
  );
}
