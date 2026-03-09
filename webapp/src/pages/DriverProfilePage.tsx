import { useParams } from "react-router-dom";
import { PageHeader } from "../components/layout/PageHeader";
import { DriverHeader } from "../components/driver/DriverHeader";
import { StatGrid } from "../components/driver/StatGrid";
import { RowSkeleton, Skeleton } from "../components/common/Skeleton";
import { ErrorFallback } from "../components/common/ErrorFallback";
import { useDriver } from "../hooks/useF1Data";

export function DriverProfilePage() {
  const { year, abbr } = useParams<{ year: string; abbr: string }>();
  const yearNum = Number(year) || 2025;
  const driverCode = abbr || "";

  const { data, isLoading, error, refetch } = useDriver(yearNum, driverCode);

  if (isLoading) {
    return (
      <div>
        <PageHeader title="Driver" showBack />
        <div className="p-4 space-y-4">
          <Skeleton className="h-28 w-full" />
          <div className="grid grid-cols-4 gap-2">
            <Skeleton className="h-16" />
            <Skeleton className="h-16" />
            <Skeleton className="h-16" />
            <Skeleton className="h-16" />
          </div>
          <RowSkeleton count={5} />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div>
        <PageHeader title="Driver" showBack />
        <ErrorFallback
          message="Failed to load driver profile"
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title={`${data.first_name} ${data.last_name}`}
        subtitle={data.team}
        showBack
      />

      <DriverHeader driver={data} />

      <div className="py-4">
        <StatGrid
          points={data.season_points}
          wins={data.season_wins}
          podiums={data.season_podiums}
          position={data.season_position}
        />
      </div>

      {/* Recent results */}
      {data.results.length > 0 && (
        <div className="px-4 pb-4">
          <h3 className="text-xs uppercase tracking-wider text-[var(--f1-text-secondary)] font-bold mb-2">
            Recent Results
          </h3>
          <div className="space-y-1.5">
            {data.results.map((result) => (
              <div
                key={result.round}
                className="bg-[var(--f1-card-bg)] rounded-xl p-3 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xs text-[var(--f1-text-secondary)] w-8">
                    R{result.round}
                  </span>
                  <span className="text-sm font-medium truncate max-w-[160px]">
                    {result.event}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span
                    className={`text-sm font-bold ${
                      result.position <= 3
                        ? "text-[var(--f1-accent)]"
                        : ""
                    }`}
                  >
                    P{result.position}
                  </span>
                  {result.points > 0 && (
                    <span className="text-xs text-[var(--f1-text-secondary)]">
                      +{result.points}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
