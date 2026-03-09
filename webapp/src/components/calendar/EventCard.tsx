import { useNavigate } from "react-router-dom";
import type { EventInfo } from "../../types/api";
import { formatDate } from "../../lib/formatters";
import { countryFlag } from "../../lib/formatters";
import { CURRENT_SEASON } from "../../lib/constants";

interface EventCardProps {
  event: EventInfo;
  isNext?: boolean;
  isPast?: boolean;
}

export function EventCard({ event, isNext = false, isPast = false }: EventCardProps) {
  const navigate = useNavigate();

  const handleClick = () => {
    if (isPast) {
      navigate(
        `/results/${CURRENT_SEASON}/${encodeURIComponent(event.name)}/R`
      );
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={!isPast}
      className={`w-full text-left rounded-xl p-4 card-press transition-all ${
        isNext
          ? "bg-[var(--f1-accent)] bg-opacity-10 border border-[var(--f1-accent)] border-opacity-30"
          : "bg-[var(--f1-card-bg)]"
      } ${!isPast && !isNext ? "opacity-60" : ""}`}
    >
      <div className="flex items-center gap-3">
        <span className="text-2xl">{countryFlag(event.country)}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm truncate">{event.name}</span>
            {isNext && (
              <span className="text-[10px] px-1.5 py-0.5 bg-[var(--f1-accent)] text-white rounded font-bold uppercase">
                Next
              </span>
            )}
          </div>
          <p className="text-xs text-[var(--f1-text-secondary)] mt-0.5">
            {event.location}, {event.country}
          </p>
        </div>
        <div className="text-right flex-shrink-0">
          <span className="text-xs font-medium block">
            R{event.round}
          </span>
          <span className="text-xs text-[var(--f1-text-secondary)]">
            {formatDate(event.date)}
          </span>
        </div>
      </div>
      {isNext && event.sessions.length > 0 && (
        <div className="mt-3 pt-3 border-t border-[var(--f1-border)] grid grid-cols-2 gap-1.5">
          {event.sessions.map((s) => (
            <div
              key={s.name}
              className="text-[10px] flex justify-between text-[var(--f1-text-secondary)]"
            >
              <span>{s.name}</span>
              <span>{formatDate(s.date)}</span>
            </div>
          ))}
        </div>
      )}
    </button>
  );
}
