import type { DriverProfile } from "../../types/api";
import { driverPhoto } from "../../lib/f1-assets";
import { getTeamColor, CURRENT_SEASON } from "../../lib/constants";

interface DriverHeaderProps {
  driver: DriverProfile;
}

export function DriverHeader({ driver }: DriverHeaderProps) {
  const teamColor = getTeamColor(driver.team_slug);
  const year = CURRENT_SEASON;

  return (
    <div className="relative overflow-hidden">
      {/* Background gradient with team color */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          background: `linear-gradient(135deg, ${teamColor} 0%, transparent 60%)`,
        }}
      />
      <div className="relative flex items-center gap-4 p-4">
        <div className="relative">
          <img
            src={driverPhoto(year, driver.team_slug, driver.code, 300)}
            alt={`${driver.first_name} ${driver.last_name}`}
            className="w-24 h-24 rounded-2xl object-cover object-top bg-[var(--f1-card-bg)]"
            onError={(e) => {
              const img = e.target as HTMLImageElement;
              img.style.display = "none";
            }}
          />
          <span
            className="absolute -bottom-2 -right-2 text-2xl font-black px-2 py-0.5 rounded-lg"
            style={{ backgroundColor: teamColor, color: "#fff" }}
          >
            {driver.number}
          </span>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-[var(--f1-text-secondary)]">
            {driver.first_name}
          </p>
          <h2 className="text-2xl font-black uppercase tracking-tight truncate">
            {driver.last_name}
          </h2>
          <div className="flex items-center gap-2 mt-1">
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: teamColor }}
            />
            <span className="text-sm text-[var(--f1-text-secondary)]">
              {driver.team}
            </span>
          </div>
          <p className="text-xs text-[var(--f1-text-secondary)] mt-0.5">
            {driver.country}
          </p>
        </div>
      </div>
    </div>
  );
}
