export interface DriverResult {
  position: number;
  driver_code: string;
  driver_name: string;
  team: string;
  team_slug: string;
  time: string | null;
  gap: string | null;
  laps: number;
  points: number;
  grid_position: number;
  status: string;
}

export interface SessionResult {
  year: number;
  event: string;
  session: string;
  results: DriverResult[];
}

export interface DriverStanding {
  position: number;
  driver_code: string;
  driver_name: string;
  team: string;
  team_slug: string;
  points: number;
  wins: number;
}

export interface ConstructorStanding {
  position: number;
  team: string;
  team_slug: string;
  points: number;
  wins: number;
}

export interface DriversStandingsResponse {
  year: number;
  drivers: DriverStanding[];
}

export interface ConstructorsStandingsResponse {
  year: number;
  constructors: ConstructorStanding[];
}

export type StandingsResponse = DriversStandingsResponse | ConstructorsStandingsResponse;

export interface SessionInfo {
  name: string;
  date: string;
}

export interface EventInfo {
  round: number;
  name: string;
  country: string;
  location: string;
  date: string;
  sessions: SessionInfo[];
}

export interface CalendarResponse {
  year: number;
  events: EventInfo[];
  next_event: EventInfo | null;
}

export interface DriverProfileResult {
  round: number;
  event: string;
  position: number;
  points: number;
  grid: number;
  status: string;
}

export interface DriverProfile {
  code: string;
  first_name: string;
  last_name: string;
  number: number;
  team: string;
  team_slug: string;
  country: string;
  season_points: number;
  season_wins: number;
  season_podiums: number;
  season_position: number;
  results: DriverProfileResult[];
}

export interface TelemetryPoint {
  distance: number;
  speed: number;
  throttle: number;
  brake: number;
  gear: number;
  drs: number;
}

export interface LapTelemetry {
  driver_code: string;
  team: string;
  team_slug: string;
  lap_time: string;
  telemetry: TelemetryPoint[];
}

export interface TelemetryResponse {
  year: number;
  event: string;
  session: string;
  laps: LapTelemetry[];
  available_drivers: string[];
}

export interface TireStint {
  stint: number;
  compound: string;
  laps: number;
  start_lap: number;
  end_lap: number;
}

export interface StrategyResponse {
  year: number;
  event: string;
  drivers: {
    driver_code: string;
    team: string;
    team_slug: string;
    stints: TireStint[];
  }[];
}
