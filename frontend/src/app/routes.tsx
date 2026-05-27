import { createBrowserRouter } from "react-router-dom";
import { AppLayout } from "./layout";
import { DataUploadPage } from "@/features/data-upload/page";
import { ETLPipelinePage } from "@/features/etl-pipeline/page";
import { DataPreviewPage } from "@/features/data-preview/page";
import { AnalyticsPage } from "@/features/analytics/page";
import { DashboardsPage } from "@/features/dashboards/page";
import { InsightsPage } from "@/features/insights/page";
import { ReportsPage } from "@/features/reports/page";
import { AgentMonitorPage } from "@/features/agent-monitor/page";
import { SettingsPage } from "@/features/settings/page";

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: "/", element: <DataUploadPage /> },
      { path: "/etl", element: <ETLPipelinePage /> },
      { path: "/preview", element: <DataPreviewPage /> },
      { path: "/analytics", element: <AnalyticsPage /> },
      { path: "/dashboards", element: <DashboardsPage /> },
      { path: "/insights", element: <InsightsPage /> },
      { path: "/reports", element: <ReportsPage /> },
      { path: "/monitor", element: <AgentMonitorPage /> },
      { path: "/settings", element: <SettingsPage /> },
    ],
  },
]);
