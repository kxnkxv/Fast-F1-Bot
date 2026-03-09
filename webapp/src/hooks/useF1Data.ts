import { useQuery } from "@tanstack/react-query";
import {
  fetchCalendar,
  fetchNextEvent,
  fetchDriverStandings,
  fetchConstructorStandings,
  fetchResults,
  fetchDriver,
  fetchTelemetry,
} from "../api/endpoints";
import type {
  DriversStandingsResponse,
  ConstructorsStandingsResponse,
} from "../types/api";

export function useCalendar(year: number) {
  return useQuery({
    queryKey: ["calendar", year],
    queryFn: () => fetchCalendar(year),
    staleTime: 5 * 60 * 1000,
  });
}

export function useNextEvent() {
  return useQuery({
    queryKey: ["calendar", "next"],
    queryFn: fetchNextEvent,
    staleTime: 60 * 1000,
  });
}

export function useDriverStandings(year: number) {
  return useQuery({
    queryKey: ["standings", year, "drivers"],
    queryFn: () => fetchDriverStandings(year),
    staleTime: 5 * 60 * 1000,
  });
}

export function useConstructorStandings(year: number) {
  return useQuery({
    queryKey: ["standings", year, "constructors"],
    queryFn: () => fetchConstructorStandings(year),
    staleTime: 5 * 60 * 1000,
  });
}

export function useStandings(year: number, type: "drivers" | "constructors") {
  return useQuery<DriversStandingsResponse | ConstructorsStandingsResponse>({
    queryKey: ["standings", year, type],
    queryFn: () =>
      type === "drivers"
        ? fetchDriverStandings(year)
        : fetchConstructorStandings(year),
    staleTime: 5 * 60 * 1000,
  });
}

export function useResults(
  year: number,
  event: string,
  session: string
) {
  return useQuery({
    queryKey: ["results", year, event, session],
    queryFn: () => fetchResults(year, event, session),
    enabled: !!year && !!event && !!session,
    staleTime: 10 * 60 * 1000,
  });
}

export function useDriver(year: number, abbr: string) {
  return useQuery({
    queryKey: ["driver", year, abbr],
    queryFn: () => fetchDriver(year, abbr),
    enabled: !!year && !!abbr,
    staleTime: 5 * 60 * 1000,
  });
}

export function useTelemetry(
  year: number,
  event: string,
  session: string,
  driver: string
) {
  return useQuery({
    queryKey: ["telemetry", year, event, session, driver],
    queryFn: () => fetchTelemetry(year, event, session, driver),
    enabled: !!year && !!event && !!session && !!driver,
    staleTime: 10 * 60 * 1000,
  });
}
