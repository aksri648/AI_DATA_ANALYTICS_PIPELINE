import { useState } from "react";
import { PageWrapper } from "@/components/layout/page-wrapper";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useDatasets, useGenerateReport } from "@/hooks/use-api";
import { toast } from "sonner";
import { FileText, Download, Eye } from "lucide-react";

export function ReportsPage() {
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const [title, setTitle] = useState("Analytics Report");
  const [format, setFormat] = useState("html");
  const [showPreview, setShowPreview] = useState(false);

  const { data: datasets } = useDatasets();
  const reportMutation = useGenerateReport();

  const handleGenerate = async () => {
    if (!selectedDataset) return;
    try {
      await reportMutation.mutateAsync({
        dataset_name: selectedDataset,
        title,
        format,
      });
      toast.success("Report generated!");
    } catch (error) {
      toast.error("Report generation failed: " + (error as Error).message);
    }
  };

  const handleDownload = () => {
    if (!reportMutation.data) return;
    const blob = new Blob([reportMutation.data.report], {
      type: format === "html" ? "text/html" : "text/markdown",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title.toLowerCase().replace(/\s+/g, "_")}.${format === "html" ? "html" : "md"}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <PageWrapper title="Reports" description="Generate comprehensive analytics reports with rich visualizations.">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="size-5" />
              Generate Report
            </CardTitle>
            <CardDescription>Configure and generate your analytics report</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-3">
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
                <Label>Report Title</Label>
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Enter report title"
                />
              </div>
              <div className="space-y-2">
                <Label>Format</Label>
                <Select value={format} onValueChange={setFormat}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="html">HTML</SelectItem>
                    <SelectItem value="markdown">Markdown</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Button
              onClick={handleGenerate}
              disabled={!selectedDataset || reportMutation.isPending}
            >
              <FileText className="size-4 mr-2" />
              {reportMutation.isPending ? "Generating..." : "Generate Report"}
            </Button>
          </CardContent>
        </Card>

        {reportMutation.isPending && (
          <Skeleton className="h-[600px]" />
        )}

        {reportMutation.data && (
          <>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant="outline">{reportMutation.data.chart_count} visualizations</Badge>
                <Badge variant="outline">{reportMutation.data.format.toUpperCase()}</Badge>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setShowPreview(!showPreview)}>
                  <Eye className="size-4 mr-2" />
                  {showPreview ? "Hide Preview" : "Show Preview"}
                </Button>
                <Button onClick={handleDownload}>
                  <Download className="size-4 mr-2" />
                  Download {format.toUpperCase()} Report
                </Button>
              </div>
            </div>

            {showPreview && (
              <Card>
                <CardHeader>
                  <CardTitle>Report Preview</CardTitle>
                </CardHeader>
                <CardContent>
                  {format === "html" ? (
                    <div
                      dangerouslySetInnerHTML={{ __html: reportMutation.data.report }}
                      className="border rounded p-4 min-h-[600px] overflow-auto"
                    />
                  ) : (
                    <pre className="whitespace-pre-wrap text-sm bg-muted p-4 rounded overflow-auto max-h-[600px]">
                      {reportMutation.data.report}
                    </pre>
                  )}
                </CardContent>
              </Card>
            )}
          </>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Example Prompts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {[
                "Create a sales dashboard for revenue trends",
                "Analyze customer churn patterns",
                "Generate executive summary of financial data",
                "Show me top-performing products",
                "Compare quarterly growth rates",
              ].map((prompt) => (
                <Badge
                  key={prompt}
                  variant="outline"
                  className="cursor-pointer hover:bg-muted"
                >
                  {prompt}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </PageWrapper>
  );
}
