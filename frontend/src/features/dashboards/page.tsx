import { useState } from "react";
import { PageWrapper } from "@/components/layout/page-wrapper";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useDatasets,
  useGenerateDashboard,
  useDashboards,
  useDashboard,
  useSaveDashboard,
  useDeleteDashboard,
} from "@/hooks/use-api";
import { toast } from "sonner";
import { LayoutDashboard, Save, Trash2, Eye, BarChart3, TrendingUp, FolderOpen } from "lucide-react";
import { cn } from "@/lib/utils";

function KPICard({ title, value, trend }: { title: string; value: string; trend?: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-sm text-muted-foreground">{title}</p>
        <p className="text-2xl font-bold">{value}</p>
        {trend && (
          <div className="flex items-center gap-1 mt-1">
            <TrendingUp className={cn("size-3", trend === "up" ? "text-green-500" : trend === "down" ? "text-red-500 rotate-180" : "")} />
            <span className="text-xs text-muted-foreground">{trend}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function DashboardsPage() {
  const [activeTab, setActiveTab] = useState<"build" | "saved">("build");
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const [dashboardType, setDashboardType] = useState("auto");
  const [saveName, setSaveName] = useState("");
  const [generatedDashboard, setGeneratedDashboard] = useState<{
    kpis: Array<{ title: string; value: string; trend?: string }>;
    charts_html: Record<string, string>;
    dashboard_type: string;
    dataset_name: string;
  } | null>(null);
  const [viewingDashboard, setViewingDashboard] = useState<number | null>(null);

  const { data: datasets } = useDatasets();
  const { data: dashboards } = useDashboards();
  const { data: loadedDashboard } = useDashboard(viewingDashboard);
  const generateMutation = useGenerateDashboard();
  const saveMutation = useSaveDashboard();
  const deleteMutation = useDeleteDashboard();

  const handleGenerate = async () => {
    if (!selectedDataset) return;
    try {
      const result = await generateMutation.mutateAsync({
        dataset_name: selectedDataset,
        dashboard_type: dashboardType,
      });
      setGeneratedDashboard(result);
      toast.success(`Dashboard generated with ${result.chart_count} charts!`);
    } catch (error) {
      toast.error("Generation failed: " + (error as Error).message);
    }
  };

  const handleSave = async () => {
    if (!saveName.trim() || !generatedDashboard) return;
    try {
      await saveMutation.mutateAsync({
        name: saveName.trim(),
        dataset_name: generatedDashboard.dataset_name,
        dashboard_type: generatedDashboard.dashboard_type,
        kpis: generatedDashboard.kpis,
        charts_html: generatedDashboard.charts_html,
      });
      toast.success(`Dashboard "${saveName}" saved!`);
      setSaveName("");
    } catch (error) {
      toast.error("Save failed: " + (error as Error).message);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteMutation.mutateAsync(id);
      toast.success("Dashboard deleted");
    } catch (error) {
      toast.error("Delete failed: " + (error as Error).message);
    }
  };

  const tabs = [
    { id: "build" as const, label: "Build Dashboard", icon: BarChart3 },
    { id: "saved" as const, label: "Saved Dashboards", icon: FolderOpen },
  ];

  return (
    <PageWrapper title="Dashboards" description="Build, save, and load analytics dashboards.">
      <div className="space-y-4">
        <div className="flex gap-1 p-1 bg-muted/50 rounded-lg w-fit">
          {tabs.map((tab) => (
            <Button
              key={tab.id}
              variant={activeTab === tab.id ? "default" : "ghost"}
              size="sm"
              className={cn("gap-2", activeTab === tab.id && "shadow-sm")}
              onClick={() => setActiveTab(tab.id)}
            >
              <tab.icon className="size-4" />
              {tab.label}
              {tab.id === "saved" && dashboards?.dashboards && (
                <Badge variant="secondary" className="ml-1 h-5 px-1.5">
                  {dashboards.dashboards.length}
                </Badge>
              )}
            </Button>
          ))}
        </div>

        {activeTab === "build" && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <LayoutDashboard className="size-5" />
                  Generate Dashboard
                </CardTitle>
                <CardDescription>Select a dataset and dashboard type</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Dataset</Label>
                    <Select value={selectedDataset ?? ""} onValueChange={setSelectedDataset}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select dataset" />
                      </SelectTrigger>
                      <SelectContent>
                        {datasets?.datasets.map((name) => (
                          <SelectItem key={name} value={name}>{name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Dashboard Type</Label>
                    <Select value={dashboardType} onValueChange={setDashboardType}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {["auto", "sales", "finance", "hr", "marketing"].map((type) => (
                          <SelectItem key={type} value={type}>
                            {type.charAt(0).toUpperCase() + type.slice(1)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <Button
                  onClick={handleGenerate}
                  disabled={!selectedDataset || generateMutation.isPending}
                >
                  <BarChart3 className="size-4 mr-2" />
                  {generateMutation.isPending ? "Generating..." : "Generate Dashboard"}
                </Button>
              </CardContent>
            </Card>

            {generateMutation.isPending && (
              <div className="grid gap-4 md:grid-cols-4">
                {[...Array(4)].map((_, i) => (
                  <Skeleton key={i} className="h-24" />
                ))}
              </div>
            )}

            {generatedDashboard && (
              <>
                {generatedDashboard.kpis.length > 0 && (
                  <div>
                    <h3 className="text-lg font-medium mb-3">Key Metrics</h3>
                    <div className="grid gap-4 md:grid-cols-4">
                      {generatedDashboard.kpis.slice(0, 4).map((kpi, i) => (
                        <KPICard key={i} {...kpi} />
                      ))}
                    </div>
                  </div>
                )}

                {Object.keys(generatedDashboard.charts_html).length > 0 && (
                  <div>
                    <h3 className="text-lg font-medium mb-3">Visualizations</h3>
                    <div className="grid gap-4 md:grid-cols-2">
                      {Object.entries(generatedDashboard.charts_html).map(([name, html]) => (
                        <Card key={name}>
                          <CardHeader className="pb-2">
                            <CardTitle className="text-sm capitalize">
                              {name.replace(/_/g, " ")}
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div
                              dangerouslySetInnerHTML={{ __html: html }}
                              className="min-h-[300px]"
                            />
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Save Dashboard</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Dashboard name (e.g. Q1 Sales Overview)"
                        value={saveName}
                        onChange={(e) => setSaveName(e.target.value)}
                      />
                      <Button
                        onClick={handleSave}
                        disabled={!saveName.trim() || saveMutation.isPending}
                      >
                        <Save className="size-4 mr-2" />
                        Save
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        )}

        {activeTab === "saved" && (
          <div className="space-y-4">
            {dashboards?.dashboards && dashboards.dashboards.length > 0 ? (
              <div className="space-y-4">
                {dashboards.dashboards.map((dash) => (
                  <Card key={dash.id}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle>{dash.name}</CardTitle>
                          <CardDescription>
                            {dash.dataset_name} | {dash.dashboard_type} | Updated: {dash.updated_at}
                          </CardDescription>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setViewingDashboard(dash.id)}
                          >
                            <Eye className="size-4 mr-1" />
                            View
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleDelete(dash.id)}
                          >
                            <Trash2 className="size-4" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                  </Card>
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <LayoutDashboard className="size-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">No saved dashboards yet</p>
                  <p className="text-sm text-muted-foreground">Generate and save a dashboard from the Build tab</p>
                </CardContent>
              </Card>
            )}

            {viewingDashboard && loadedDashboard?.dashboard && (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>{loadedDashboard.dashboard.name}</CardTitle>
                      <CardDescription>
                        {loadedDashboard.dashboard.dataset_name} | {loadedDashboard.dashboard.dashboard_type}
                      </CardDescription>
                    </div>
                    <Button variant="outline" onClick={() => setViewingDashboard(null)}>
                      Close
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {loadedDashboard.dashboard.kpis.length > 0 && (
                    <div>
                      <h3 className="text-lg font-medium mb-3">Key Metrics</h3>
                      <div className="grid gap-4 md:grid-cols-4">
                        {loadedDashboard.dashboard.kpis.slice(0, 4).map((kpi, i) => (
                          <KPICard key={i} {...kpi} />
                        ))}
                      </div>
                    </div>
                  )}
                  {Object.keys(loadedDashboard.dashboard.charts_html).length > 0 && (
                    <div>
                      <h3 className="text-lg font-medium mb-3">Visualizations</h3>
                      <div className="grid gap-4 md:grid-cols-2">
                        {Object.entries(loadedDashboard.dashboard.charts_html).map(([name, html]) => (
                          <Card key={name}>
                            <CardHeader className="pb-2">
                              <CardTitle className="text-sm capitalize">
                                {name.replace(/_/g, " ")}
                              </CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div
                                dangerouslySetInnerHTML={{ __html: html }}
                                className="min-h-[300px]"
                              />
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </PageWrapper>
  );
}
