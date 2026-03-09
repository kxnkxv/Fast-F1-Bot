import { useMemo } from "react";
import { PageHeader } from "../components/layout/PageHeader";
import { EventCard } from "../components/calendar/EventCard";
import { CountdownTimer } from "../components/calendar/CountdownTimer";
import { CardSkeleton } from "../components/common/Skeleton";
import { ErrorFallback } from "../components/common/ErrorFallback";
import { useCalendar } from "../hooks/useF1Data";
import { CURRENT_SEASON } from "../lib/constants";

export function CalendarPage() {
  const { data, isLoading, error, refetch } = useCalendar(CURRENT_SEASON);

  const { pastEvents, futureEvents, nextEvent } = useMemo(() => {
    if (!data) return { pastEvents: [], futureEvents: [], nextEvent: null };

    const now = new Date();
    const past = data.events.filter((e) => new Date(e.date) < now);
    const future = data.events.filter((e) => new Date(e.date) >= now);

    return {
      pastEvents: past.reverse(),
      futureEvents: future,
      nextEvent: data.next_event,
    };
  }, [data]);

  if (isLoading) {
    return (
      <div>
        <PageHeader title={`${CURRENT_SEASON} Calendar`} />
        <div className="p-4 space-y-3">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <PageHeader title={`${CURRENT_SEASON} Calendar`} />
        <ErrorFallback
          message="Failed to load calendar"
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  return (
    <div>
      <PageHeader title={`${CURRENT_SEASON} Calendar`} />

      {/* Next event highlight */}
      {nextEvent && (
        <div className="px-4 pt-4">
          <h2 className="text-xs uppercase tracking-wider text-[var(--f1-text-secondary)] font-bold mb-2">
            Next Race
          </h2>
          <div className="bg-[var(--f1-card-bg)] rounded-xl overflow-hidden border border-[var(--f1-accent)] border-opacity-30">
            <CountdownTimer targetDate={nextEvent.date} />
            <EventCard event={nextEvent} isNext />
          </div>
        </div>
      )}

      {/* Upcoming events */}
      {futureEvents.length > 0 && (
        <div className="px-4 pt-6">
          <h2 className="text-xs uppercase tracking-wider text-[var(--f1-text-secondary)] font-bold mb-2">
            Upcoming
          </h2>
          <div className="space-y-2">
            {futureEvents
              .filter((e) => e.round !== nextEvent?.round)
              .map((event) => (
                <EventCard key={event.round} event={event} />
              ))}
          </div>
        </div>
      )}

      {/* Past events */}
      {pastEvents.length > 0 && (
        <div className="px-4 pt-6 pb-4">
          <h2 className="text-xs uppercase tracking-wider text-[var(--f1-text-secondary)] font-bold mb-2">
            Completed
          </h2>
          <div className="space-y-2">
            {pastEvents.map((event) => (
              <EventCard key={event.round} event={event} isPast />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
