import { useParams } from "react-router-dom";
import { PageHeader } from "../components/layout/PageHeader";
import { PodiumDisplay } from "../components/results/PodiumDisplay";
import { ResultRow } from "../components/results/ResultRow";
import { RowSkeleton } from "../components/common/Skeleton";
import { ErrorFallback } from "../components/common/ErrorFallback";
import { useResults } from "../hooks/useF1Data";
import { formatSessionName } from "../lib/formatters";

export function RaceResultsPage() {
  const { year, event, session } = useParams<{
    year: string;
    event: string;
    session: string;
  }>();

  const yearNum = Number(year) || 2025;
  const eventName = decodeURIComponent(event || "");
  const sessionName = session || "R";

  const { data, isLoading, error, refetch } = useResults(
    yearNum,
    eventName,
    sessionName
  );

  return (
    <div>
      <PageHeader
        title={eventName || "Race Results"}
        subtitle={`${yearNum} - ${formatSessionName(sessionName)}`}
        showBack
      />

      {isLoading && (
        <div className="p-4">
          <RowSkeleton count={10} />
        </div>
      )}

      {error && (
        <ErrorFallback
          message="Failed to load results"
          onRetry={() => refetch()}
        />
      )}

      {data && (
        <>
          {/* Podium */}
          {data.results.length >= 3 && (
            <PodiumDisplay results={data.results} />
          )}

          {/* Full results */}
          <div className="p-4 space-y-2">
            {data.results.map((result) => (
              <ResultRow key={result.driver_code} result={result} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
