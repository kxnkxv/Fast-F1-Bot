import { getTeamColor } from "../../lib/constants";

interface TeamBadgeProps {
  teamSlug: string;
  teamName: string;
  size?: "sm" | "md";
}

export function TeamBadge({ teamSlug, teamName, size = "sm" }: TeamBadgeProps) {
  const color = getTeamColor(teamSlug);
  const dotSize = size === "sm" ? "w-2 h-2" : "w-3 h-3";
  const textSize = size === "sm" ? "text-xs" : "text-sm";

  return (
    <div className="flex items-center gap-1.5">
      <span
        className={`${dotSize} rounded-full flex-shrink-0`}
        style={{ backgroundColor: color }}
      />
      <span className={`${textSize} text-[var(--f1-text-secondary)] truncate`}>
        {teamName}
      </span>
    </div>
  );
}
