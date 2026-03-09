import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { LapTelemetry } from "../../types/api";
import { getTeamColor } from "../../lib/constants";

interface SpeedTraceProps {
  laps: LapTelemetry[];
}

export function SpeedTrace({ laps }: SpeedTraceProps) {
  if (laps.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-[var(--f1-text-secondary)] text-sm">
        No telemetry data available
      </div>
    );
  }

  // Merge telemetry data by distance for all drivers
  const mergedData: Record<string, Record<string, number>>[] = [];
  const maxLen = Math.max(...laps.map((l) => l.telemetry.length));

  for (let i = 0; i < maxLen; i++) {
    const point: Record<string, number> = {};

    for (const lap of laps) {
      const t = lap.telemetry[i];
      if (t) {
        point["distance"] = t.distance;
        point[`speed_${lap.driver_code}`] = t.speed;
      }
    }

    if (point["distance"] !== undefined) {
      mergedData.push(point as never);
    }
  }

  // Downsample for performance (keep every nth point)
  const sampleRate = Math.max(1, Math.floor(mergedData.length / 500));
  const sampledData = mergedData.filter((_, i) => i % sampleRate === 0);

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={sampledData}
          margin={{ top: 5, right: 10, left: -15, bottom: 5 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--f1-border)"
            opacity={0.5}
          />
          <XAxis
            dataKey="distance"
            tick={{ fill: "var(--f1-text-secondary)", fontSize: 10 }}
            tickFormatter={(v: number) => `${Math.round(v)}m`}
            stroke="var(--f1-border)"
          />
          <YAxis
            tick={{ fill: "var(--f1-text-secondary)", fontSize: 10 }}
            tickFormatter={(v: number) => `${v}`}
            stroke="var(--f1-border)"
            domain={["auto", "auto"]}
            label={{
              value: "km/h",
              angle: -90,
              position: "insideLeft",
              offset: 20,
              style: {
                fill: "var(--f1-text-secondary)",
                fontSize: 10,
              },
            }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "var(--f1-card-bg)",
              border: "1px solid var(--f1-border)",
              borderRadius: "8px",
              fontSize: "12px",
              color: "var(--f1-text-primary)",
            }}
            labelFormatter={(v: number) => `Distance: ${Math.round(v)}m`}
            formatter={(value: number, name: string) => [
              `${Math.round(value)} km/h`,
              name.replace("speed_", ""),
            ]}
          />
          <Legend
            wrapperStyle={{ fontSize: "11px" }}
            formatter={(value: string) => value.replace("speed_", "")}
          />
          {laps.map((lap) => (
            <Line
              key={lap.driver_code}
              type="monotone"
              dataKey={`speed_${lap.driver_code}`}
              stroke={getTeamColor(lap.team_slug)}
              dot={false}
              strokeWidth={1.5}
              name={`speed_${lap.driver_code}`}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
