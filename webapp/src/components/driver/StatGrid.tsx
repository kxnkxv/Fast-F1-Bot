interface StatGridProps {
  points: number;
  wins: number;
  podiums: number;
  position: number;
}

interface StatCardProps {
  label: string;
  value: string | number;
  highlight?: boolean;
}

function StatCard({ label, value, highlight = false }: StatCardProps) {
  return (
    <div className="bg-[var(--f1-card-bg)] rounded-xl p-3 text-center">
      <span
        className={`text-xl font-black block ${
          highlight ? "text-[var(--f1-accent)]" : ""
        }`}
      >
        {value}
      </span>
      <span className="text-[10px] uppercase tracking-wider text-[var(--f1-text-secondary)] font-bold">
        {label}
      </span>
    </div>
  );
}

export function StatGrid({ points, wins, podiums, position }: StatGridProps) {
  return (
    <div className="grid grid-cols-4 gap-2 px-4">
      <StatCard label="Position" value={`P${position}`} highlight />
      <StatCard label="Points" value={points} />
      <StatCard label="Wins" value={wins} />
      <StatCard label="Podiums" value={podiums} />
    </div>
  );
}
