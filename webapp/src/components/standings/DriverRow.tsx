import { useNavigate } from "react-router-dom";
import type { DriverStanding } from "../../types/api";
import { TeamBadge } from "../common/TeamBadge";
import { PointsBar } from "./PointsBar";
import { CURRENT_SEASON } from "../../lib/constants";

interface DriverRowProps {
  driver: DriverStanding;
  maxPoints: number;
}

export function DriverRow({ driver, maxPoints }: DriverRowProps) {
  const navigate = useNavigate();

  return (
    <button
      onClick={() =>
        navigate(`/driver/${CURRENT_SEASON}/${driver.driver_code}`)
      }
      className="w-full bg-[var(--f1-card-bg)] rounded-xl p-3 card-press text-left"
    >
      <div className="flex items-center gap-3">
        <span className="text-sm font-bold tabular-nums w-6 text-center text-[var(--f1-text-secondary)]">
          {driver.position}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm truncate">
              {driver.driver_name}
            </span>
            <span className="text-xs font-mono text-[var(--f1-text-secondary)]">
              {driver.driver_code}
            </span>
          </div>
          <TeamBadge teamSlug={driver.team_slug} teamName={driver.team} />
          <PointsBar
            points={driver.points}
            maxPoints={maxPoints}
            teamSlug={driver.team_slug}
          />
        </div>
        {driver.wins > 0 && (
          <span className="text-xs text-[var(--f1-text-secondary)]">
            {driver.wins}W
          </span>
        )}
      </div>
    </button>
  );
}
