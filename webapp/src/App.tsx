import { Routes, Route } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { CalendarPage } from "./pages/CalendarPage";
import { StandingsPage } from "./pages/StandingsPage";
import { RaceResultsPage } from "./pages/RaceResultsPage";
import { DriverProfilePage } from "./pages/DriverProfilePage";
import { TelemetryPage } from "./pages/TelemetryPage";
import { useTheme } from "./hooks/useTheme";
import { useTelegram } from "./hooks/useTelegram";

export default function App() {
  // Initialize Telegram WebApp and theme
  useTelegram();
  useTheme();

  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<CalendarPage />} />
        <Route path="/standings" element={<StandingsPage />} />
        <Route
          path="/results/:year/:event/:session"
          element={<RaceResultsPage />}
        />
        <Route path="/driver/:year/:abbr" element={<DriverProfilePage />} />
        <Route
          path="/telemetry/:year/:event/:session"
          element={<TelemetryPage />}
        />
      </Routes>
    </AppShell>
  );
}
