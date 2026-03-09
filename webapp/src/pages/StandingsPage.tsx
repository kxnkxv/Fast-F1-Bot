import { useState, useMemo } from "react";
import { PageHeader } from "../components/layout/PageHeader";
import { DriverRow } from "../components/standings/DriverRow";
import { ConstructorRow } from "../components/standings/ConstructorRow";
import { RowSkeleton } from "../components/common/Skeleton";
import { ErrorFallback } from "../components/common/ErrorFallback";
import { useDriverStandings, useConstructorStandings } from "../hooks/useF1Data";
import { CURRENT_SEASON } from "../lib/constants";

type TabType = "drivers" | "constructors";

export function StandingsPage() {
  const [tab, setTab] = useState<TabType>("drivers");

  const driversQuery = useDriverStandings(CURRENT_SEASON);
  const constructorsQuery = useConstructorStandings(CURRENT_SEASON);

  const isLoading = tab === "drivers" ? driversQuery.isLoading : constructorsQuery.isLoading;
  const error = tab === "drivers" ? driversQuery.error : constructorsQuery.error;
  const refetch = tab === "drivers" ? driversQuery.refetch : constructorsQuery.refetch;

  const maxDriverPoints = useMemo(() => {
    const drivers = driversQuery.data?.drivers;
    return drivers && drivers.length > 0 ? drivers[0]!.points : 0;
  }, [driversQuery.data]);

  const maxConstructorPoints = useMemo(() => {
    const constructors = constructorsQuery.data?.constructors;
    return constructors && constructors.length > 0 ? constructors[0]!.points : 0;
  }, [constructorsQuery.data]);

  return (
    <div>
      <PageHeader title={`${CURRENT_SEASON} Standings`} />

      {/* Tab bar */}
      <div className="flex px-4 pt-3 gap-2">
        {(["drivers", "constructors"] as TabType[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 py-2 text-sm font-bold rounded-lg transition-colors ${
              tab === t
                ? "bg-[var(--f1-accent)] text-white"
                : "bg-[var(--f1-card-bg)] text-[var(--f1-text-secondary)]"
            }`}
          >
            {t === "drivers" ? "Drivers" : "Constructors"}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-4 tab-content-enter" key={tab}>
        {isLoading && <RowSkeleton count={10} />}

        {error && (
          <ErrorFallback
            message="Failed to load standings"
            onRetry={() => refetch()}
          />
        )}

        {tab === "drivers" && driversQuery.data && (
          <div className="space-y-2">
            {driversQuery.data.drivers.map((driver) => (
              <DriverRow
                key={driver.driver_code}
                driver={driver}
                maxPoints={maxDriverPoints}
              />
            ))}
          </div>
        )}

        {tab === "constructors" && constructorsQuery.data && (
          <div className="space-y-2">
            {constructorsQuery.data.constructors.map((c) => (
              <ConstructorRow
                key={c.team_slug}
                constructor={c}
                maxPoints={maxConstructorPoints}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
