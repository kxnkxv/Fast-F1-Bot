import apiClient from "./client";
import type {
  CalendarResponse,
  EventInfo,
  DriversStandingsResponse,
  ConstructorsStandingsResponse,
  SessionResult,
  DriverProfile,
  TelemetryResponse,
} from "../types/api";

export async function fetchCalendar(year: number): Promise<CalendarResponse> {
  const { data } = await apiClient.get<CalendarResponse>(
    `/api/calendar/${year}`
  );
  return data;
}

export async function fetchNextEvent(): Promise<EventInfo> {
  const { data } = await apiClient.get<EventInfo>("/api/calendar/next");
  return data;
}

export async function fetchDriverStandings(
  year: number
): Promise<DriversStandingsResponse> {
  const { data } = await apiClient.get<DriversStandingsResponse>(
    "/api/standings/drivers",
    { params: { year } }
  );
  return data;
}

export async function fetchConstructorStandings(
  year: number
): Promise<ConstructorsStandingsResponse> {
  const { data } = await apiClient.get<ConstructorsStandingsResponse>(
    "/api/standings/constructors",
    { params: { year } }
  );
  return data;
}

export async function fetchStandings(
  year: number,
  type: "drivers" | "constructors"
) {
  if (type === "drivers") {
    return fetchDriverStandings(year);
  }
  return fetchConstructorStandings(year);
}

export async function fetchResults(
  year: number,
  event: string,
  session: string
): Promise<SessionResult> {
  const { data } = await apiClient.get<SessionResult>(
    `/api/results/${year}/${encodeURIComponent(event)}/${encodeURIComponent(session)}`
  );
  return data;
}

export async function fetchDriver(
  year: number,
  abbr: string
): Promise<DriverProfile> {
  const { data } = await apiClient.get<DriverProfile>(
    `/api/drivers/${year}/${encodeURIComponent(abbr)}`
  );
  return data;
}

export async function fetchTelemetry(
  year: number,
  event: string,
  session: string,
  driver: string
): Promise<TelemetryResponse> {
  const { data } = await apiClient.get<TelemetryResponse>(
    `/api/telemetry/${year}/${encodeURIComponent(event)}/${encodeURIComponent(session)}/${encodeURIComponent(driver)}`
  );
  return data;
}
