import { useState, useEffect } from "react";
import { formatCountdown } from "../../lib/formatters";

interface CountdownTimerProps {
  targetDate: string;
}

export function CountdownTimer({ targetDate }: CountdownTimerProps) {
  const [countdown, setCountdown] = useState(() =>
    formatCountdown(targetDate)
  );

  useEffect(() => {
    const interval = setInterval(() => {
      setCountdown(formatCountdown(targetDate));
    }, 1000);

    return () => clearInterval(interval);
  }, [targetDate]);

  if (countdown.isPast) {
    return (
      <div className="text-center py-2">
        <span className="text-sm text-[var(--f1-accent)] font-bold">
          Race in progress or completed
        </span>
      </div>
    );
  }

  const units = [
    { value: countdown.days, label: "DAYS" },
    { value: countdown.hours, label: "HRS" },
    { value: countdown.minutes, label: "MIN" },
    { value: countdown.seconds, label: "SEC" },
  ];

  return (
    <div className="flex items-center justify-center gap-3 py-3">
      {units.map((unit, i) => (
        <div key={unit.label} className="flex items-center gap-3">
          <div className="flex flex-col items-center">
            <span className="text-2xl font-black tabular-nums text-[var(--f1-accent)]">
              {String(unit.value).padStart(2, "0")}
            </span>
            <span className="text-[9px] font-bold text-[var(--f1-text-secondary)] tracking-wider">
              {unit.label}
            </span>
          </div>
          {i < units.length - 1 && (
            <span className="text-xl font-bold text-[var(--f1-text-secondary)] -mt-3">
              :
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
