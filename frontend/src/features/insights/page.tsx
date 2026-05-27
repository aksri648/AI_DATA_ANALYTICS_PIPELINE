import { useState } from "react";
import { PageWrapper } from "@/components/layout/page-wrapper";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useDatasets, useGenerateInsights } from "@/hooks/use-api";
import { toast } from "sonner";
import { Lightbulb, Download, TrendingUp } from "lucide-react";

function KPICard({ title, value, trend }: { title: string; value: string; trend?: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-sm text-muted-foreground">{title}</p>
        <p className="text-2xl font-bold">{value}</p>
        {trend && (
          <div className="flex items-center gap-1 mt-1">
            <TrendingUp className={`size-3 ${trend === "up" ? "text-green-500" : trend === "down" ? "text-red-500 rotate-180" : ""}`} />
            <span className="text-xs text-muted-foreground">{trend}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function InsightsPage() {
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const { data: datasets } = useDatasets();
  const insightsMutation = useGenerateInsights();

  const handleGenerate = async () => {
    if (!selectedDataset) return;
    try {
      await insightsMutation.mutateAsync(selectedDataset);
      toast.success("Insights generated!");
    } catch (error) {
      toast.error("Insight generation failed: " + (error as Error).message);
    }
  };

  const handleDownload = () => {
    if (!insightsMutation.data) return;
    const blob = new Blob([insightsMutation.data.insights], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${selectedDataset}_insights.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <PageWrapper title="AI Business Insights" description="Automatically generated insights from your data.">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="size-5" />
              Generate Insights
            </CardTitle>
            <CardDescription>Select a dataset for AI analysis</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-4">
              <Select value={selectedDataset ?? ""} onValueChange={setSelectedDataset}>
                <SelectTrigger className="w-[300px]">
                  <SelectValue placeholder="Select dataset" />
                </SelectTrigger>
                <SelectContent>
                  {datasets?.datasets.map((name) => (
                    <SelectItem key={name} value={name}>{name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                onClick={handleGenerate}
                disabled={!selectedDataset || insightsMutation.isPending}
              >
                <Lightbulb className="size-4 mr-2" />
                {insightsMutation.isPending ? "Generating..." : "Generate Insights"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {insightsMutation.isPending && (
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-4">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-24" />
              ))}
            </div>
            <Skeleton className="h-[400px]" />
          </div>
        )}

        {insightsMutation.data && (
          <>
            {insightsMutation.data.kpis.length > 0 && (
              <div>
                <h3 className="text-lg font-medium mb-3">Key Metrics</h3>
                <div className="grid gap-4 md:grid-cols-4">
                  {insightsMutation.data.kpis.slice(0, 4).map((kpi, i) => (
                    <KPICard key={i} {...kpi} />
                  ))}
                </div>
              </div>
            )}

            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>AI Analysis</CardTitle>
                  <Button variant="outline" size="sm" onClick={handleDownload}>
                    <Download className="size-4 mr-2" />
                    Download Insights
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="prose prose-invert max-w-none">
                  <div className="whitespace-pre-wrap text-sm">
                    {insightsMutation.data.insights}
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </PageWrapper>
  );
}
