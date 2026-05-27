export interface HealthResponse {
  status: string;
  ollama: {
    healthy: boolean;
    base_url: string;
    model: string;
  };
  datasets_count: number;
}

export interface SettingsResponse {
  ollama: {
    base_url: string;
    model: string;
    available_models: string[];
  };
  duckdb_path: string;
}

export interface DatasetListResponse {
  datasets: string[];
}

export interface DatasetResponse {
  name: string;
  columns: string[];
  dtypes: Record<string, string>;
  total_rows: number;
  total_columns: number;
  preview: Record<string, unknown>[];
}

export interface DatasetProfileResponse {
  name: string;
  profile: Record<string, unknown>;
}

export interface DatasetValidationResponse {
  name: string;
  validation: Record<string, unknown>;
}

export interface DatasetStatisticsResponse {
  name: string;
  statistics: Record<string, unknown>;
  missing: Record<string, unknown>;
}

export interface IngestResponse {
  status: string;
  table_name: string;
  is_pdf: boolean;
  metadata?: Record<string, unknown>;
  result?: Record<string, unknown>;
}

export interface ETLResponse {
  status: string;
  result: Record<string, unknown>;
}

export interface PipelineHistoryResponse {
  history: Array<{
    step: string;
    table_name?: string;
    timestamp: string;
    status: string;
    [key: string]: unknown;
  }>;
}

export interface ChatResponse {
  intent: string;
  analysis?: string;
  insights?: string;
  message?: string;
  chart?: string;
  kpis?: Array<{ title: string; value: string; trend?: string }>;
  dashboard?: Record<string, string>;
  sql?: string;
  result?: Record<string, unknown>[];
  error?: string;
  table_name?: string;
  requires_file?: boolean;
  report?: string;
}

export interface InsightsResponse {
  status: string;
  table_name: string;
  kpis: Array<{ title: string; value: string; trend?: string }>;
  insights: string;
  profile: Record<string, unknown>;
}

export interface DashboardGenerateResponse {
  status: string;
  kpis: Array<{ title: string; value: string; trend?: string }>;
  charts_html: Record<string, string>;
  chart_count: number;
  dashboard_type: string;
  dataset_name: string;
}

export interface DashboardListResponse {
  dashboards: Array<{
    id: number;
    name: string;
    dataset_name: string;
    dashboard_type: string;
    created_at: string;
    updated_at: string;
  }>;
}

export interface DashboardResponse {
  dashboard: {
    id: number;
    name: string;
    dataset_name: string;
    dashboard_type: string;
    kpis: Array<{ title: string; value: string; trend?: string }>;
    charts_html: Record<string, string>;
    created_at: string;
    updated_at: string;
  };
}

export interface ReportResponse {
  status: string;
  report: string;
  format: string;
  chart_count: number;
  title: string;
}

export interface ConversationsResponse {
  conversations: Array<{
    role: string;
    content: string;
    timestamp?: string;
  }>;
}

export interface MonitorContextResponse {
  analytics_context: Record<string, unknown> | null;
  schema_cache: Record<string, unknown>;
}
