import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "@/lib/api-client";
import type {
  HealthResponse,
  SettingsResponse,
  DatasetListResponse,
  DatasetResponse,
  DatasetProfileResponse,
  DatasetValidationResponse,
  DatasetStatisticsResponse,
  IngestResponse,
  ETLResponse,
  PipelineHistoryResponse,
  ChatResponse,
  InsightsResponse,
  DashboardGenerateResponse,
  DashboardListResponse,
  DashboardResponse,
  ReportResponse,
  ConversationsResponse,
  MonitorContextResponse,
} from "@/types/api";

export const useHealth = () =>
  useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: () => apiClient.get("/api/health").then((r) => r.data),
    refetchInterval: 30000,
  });

export const useSettings = () =>
  useQuery<SettingsResponse>({
    queryKey: ["settings"],
    queryFn: () => apiClient.get("/api/settings").then((r) => r.data),
  });

export const useDatasets = () =>
  useQuery<DatasetListResponse>({
    queryKey: ["datasets"],
    queryFn: () => apiClient.get("/api/datasets").then((r) => r.data),
  });

export const useDataset = (name: string | null) =>
  useQuery<DatasetResponse>({
    queryKey: ["datasets", name],
    queryFn: () => apiClient.get(`/api/datasets/${name}`).then((r) => r.data),
    enabled: !!name,
  });

export const useDatasetProfile = (name: string | null) =>
  useQuery<DatasetProfileResponse>({
    queryKey: ["datasets", name, "profile"],
    queryFn: () =>
      apiClient.get(`/api/datasets/${name}/profile`).then((r) => r.data),
    enabled: !!name,
  });

export const useDatasetValidation = (name: string | null) =>
  useQuery<DatasetValidationResponse>({
    queryKey: ["datasets", name, "validation"],
    queryFn: () =>
      apiClient.get(`/api/datasets/${name}/validate`).then((r) => r.data),
    enabled: !!name,
  });

export const useDatasetStatistics = (name: string | null) =>
  useQuery<DatasetStatisticsResponse>({
    queryKey: ["datasets", name, "statistics"],
    queryFn: () =>
      apiClient.get(`/api/datasets/${name}/statistics`).then((r) => r.data),
    enabled: !!name,
  });

export const useIngestFile = () => {
  const queryClient = useQueryClient();
  return useMutation<IngestResponse, Error, FormData>({
    mutationFn: (formData: FormData) =>
      apiClient
        .post("/api/etl/ingest", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        })
        .then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      queryClient.invalidateQueries({ queryKey: ["etl-history"] });
    },
  });
};

export const useCleanDataset = () => {
  const queryClient = useQueryClient();
  return useMutation<ETLResponse, Error, string>({
    mutationFn: (name: string) =>
      apiClient.post(`/api/etl/clean/${name}`).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      queryClient.invalidateQueries({ queryKey: ["etl-history"] });
    },
  });
};

export const useProfileDataset = () =>
  useMutation<ETLResponse, Error, string>({
    mutationFn: (name: string) =>
      apiClient.post(`/api/etl/profile/${name}`).then((r) => r.data),
  });

export const usePipelineHistory = () =>
  useQuery<PipelineHistoryResponse>({
    queryKey: ["etl-history"],
    queryFn: () => apiClient.get("/api/etl/history").then((r) => r.data),
  });

export const useChatMutation = () =>
  useMutation<ChatResponse, Error, { question: string; table_name?: string }>({
    mutationFn: (data) =>
      apiClient.post("/api/analytics/chat", data).then((r) => r.data),
  });

export const useGenerateInsights = () =>
  useMutation<InsightsResponse, Error, string>({
    mutationFn: (name: string) =>
      apiClient.post(`/api/analytics/insights/${name}`).then((r) => r.data),
  });

export const useGenerateDashboard = () =>
  useMutation<
    DashboardGenerateResponse,
    Error,
    { dataset_name: string; dashboard_type: string }
  >({
    mutationFn: (data) =>
      apiClient.post("/api/dashboards/generate", data).then((r) => r.data),
  });

export const useDashboards = () =>
  useQuery<DashboardListResponse>({
    queryKey: ["dashboards"],
    queryFn: () => apiClient.get("/api/dashboards").then((r) => r.data),
  });

export const useDashboard = (id: number | null) =>
  useQuery<DashboardResponse>({
    queryKey: ["dashboards", id],
    queryFn: () => apiClient.get(`/api/dashboards/${id}`).then((r) => r.data),
    enabled: id !== null,
  });

export const useSaveDashboard = () => {
  const queryClient = useQueryClient();
  return useMutation<
    { status: string; name: string },
    Error,
    {
      name: string;
      dataset_name: string;
      dashboard_type: string;
      kpis: unknown[];
      charts_html: Record<string, string>;
    }
  >({
    mutationFn: (data) =>
      apiClient.post("/api/dashboards/save", data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboards"] });
    },
  });
};

export const useDeleteDashboard = () => {
  const queryClient = useQueryClient();
  return useMutation<{ status: string }, Error, number>({
    mutationFn: (id: number) =>
      apiClient.delete(`/api/dashboards/${id}`).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboards"] });
    },
  });
};

export const useGenerateReport = () =>
  useMutation<
    ReportResponse,
    Error,
    { dataset_name: string; title: string; format: string }
  >({
    mutationFn: (data) =>
      apiClient.post("/api/reports/generate", data).then((r) => r.data),
  });

export const useConversations = () =>
  useQuery<ConversationsResponse>({
    queryKey: ["conversations"],
    queryFn: () =>
      apiClient.get("/api/monitor/conversations").then((r) => r.data),
  });

export const useMonitorContext = () =>
  useQuery<MonitorContextResponse>({
    queryKey: ["monitor-context"],
    queryFn: () =>
      apiClient.get("/api/monitor/context").then((r) => r.data),
  });
