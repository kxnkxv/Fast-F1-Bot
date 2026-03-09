import { useState, useCallback, useMemo } from "react";
import { useParams } from "react-router-dom";
import { PageHeader } from "../components/layout/PageHeader";
import { SpeedTrace } from "../components/telemetry/SpeedTrace";
import { DriverSelector } from "../components/telemetry/DriverSelector";
import { Skeleton } from "../components/common/Skeleton";
import { ErrorFallback } from "../components/common/ErrorFallback";
import { useTelemetry } from "../hooks/useF1Data";
import { formatSessionName } from "../lib/formatters";

export function TelemetryPage() {
  const { year, event, session } = useParams<{
    year: string;
    event: string;
    session: string;
  }>();

  const yearNum = Number(year) || 2025;
  const eventName = decodeURIComponent(event || "last");
  const sessionName = session || "R";

  const [selectedDrivers, setSelectedDrivers] = useState<string[]>([]);

  // Fetch telemetry for first selected driver (to get available drivers list)
  const firstDriver = selectedDrivers[0] || "";
  const { data, isLoading, refetch } = useTelemetry(
    yearNum,
    eventName,
    sessionName,
    firstDriver
  );

  // Fetch second driver telemetry if selected
  const secondDriver = selectedDrivers[1] || "";
  const { data: data2 } = useTelemetry(
    yearNum,
    eventName,
    sessionName,
    secondDriver
  );

  // We need to first fetch available drivers - use a placeholder request
  const { data: initialData, isLoading: initialLoading, error: initialError } = useTelemetry(
    yearNum,
    eventName,
    sessionName,
    "_available"
  );

  const availableDrivers = useMemo(() => {
    return data?.available_drivers || initialData?.available_drivers || [];
  }, [data, initialData]);

  const handleToggle = useCallback((driver: string) => {
    setSelectedDrivers((prev) => {
      if (prev.includes(driver)) {
        return prev.filter((d) => d !== driver);
      }
      if (prev.length >= 2) return prev;
      return [...prev, driver];
    });
  }, []);

  // Combine laps data from both queries
  const combinedLaps = useMemo(() => {
    const laps = [];
    if (data?.laps) laps.push(...data.laps);
    if (data2?.laps) {
      // Avoid duplicates
      for (const lap of data2.laps) {
        if (!laps.find((l) => l.driver_code === lap.driver_code)) {
          laps.push(lap);
        }
      }
    }
    return laps;
  }, [data, data2]);

  return (
    <div>
      <PageHeader
        title="Telemetry"
        subtitle={`${eventName} - ${formatSessionName(sessionName)}`}
        showBack
      />

      <div className="py-4 space-y-4">
        {/* Driver selector */}
        {initialLoading && !availableDrivers.length && (
          <div className="px-4">
            <Skeleton className="h-8 w-full" />
          </div>
        )}

        {initialError && !availableDrivers.length && (
          <ErrorFallback
            message="Failed to load telemetry data"
            onRetry={() => refetch()}
          />
        )}

        {availableDrivers.length > 0 && (
          <DriverSelector
            availableDrivers={availableDrivers}
            selectedDrivers={selectedDrivers}
            onToggle={handleToggle}
          />
        )}

        {/* Speed trace */}
        {selectedDrivers.length > 0 && (
          <div className="px-4">
            <h3 className="text-xs uppercase tracking-wider text-[var(--f1-text-secondary)] font-bold mb-2">
              Speed Trace (Fastest Lap)
            </h3>

            {isLoading ? (
              <Skeleton className="h-64 w-full" />
            ) : (
              <div className="bg-[var(--f1-card-bg)] rounded-xl p-3 overflow-hidden">
                <SpeedTrace laps={combinedLaps} />
              </div>
            )}

            {/* Lap time comparison */}
            {combinedLaps.length > 0 && (
              <div className="mt-3 space-y-1.5">
                {combinedLaps.map((lap) => (
                  <div
                    key={lap.driver_code}
                    className="bg-[var(--f1-card-bg)] rounded-xl p-3 flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{
                          backgroundColor: `var(--f1-accent)`,
                        }}
                      />
                      <span className="text-sm font-bold">
                        {lap.driver_code}
                      </span>
                      <span className="text-xs text-[var(--f1-text-secondary)]">
                        {lap.team}
                      </span>
                    </div>
                    <span className="text-sm font-mono">{lap.lap_time}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {selectedDrivers.length === 0 && availableDrivers.length > 0 && (
          <div className="flex items-center justify-center h-48 text-[var(--f1-text-secondary)] text-sm">
            Select a driver to view telemetry
          </div>
        )}
      </div>
    </div>
  );
}
