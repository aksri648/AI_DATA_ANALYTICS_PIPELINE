import { useState } from "react";
import { PageWrapper } from "@/components/layout/page-wrapper";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import {
  useDatasets,
  useCleanDataset,
  useProfileDataset,
  usePipelineHistory,
} from "@/hooks/use-api";
import { toast } from "sonner";
import { Sparkles, BarChart3, History, CheckCircle, XCircle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

export function ETLPipelinePage() {
  const [activeTab, setActiveTab] = useState<"transform" | "history">("transform");
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const [profileResult, setProfileResult] = useState<Record<string, unknown> | null>(null);
  const { data: datasets } = useDatasets();
  const { data: history, isLoading: historyLoading } = usePipelineHistory();

  const cleanMutation = useCleanDataset();
  const profileMutation = useProfileDataset();

  const handleClean = async () => {
    if (!selectedDataset) return;
    try {
      const result = await cleanMutation.mutateAsync(selectedDataset);
      toast.success("Data cleaned successfully!");
      console.log(result);
    } catch (error) {
      toast.error("Cleaning failed: " + (error as Error).message);
    }
  };

  const handleProfile = async () => {
    if (!selectedDataset) return;
    try {
      const result = await profileMutation.mutateAsync(selectedDataset);
      setProfileResult(result as unknown as Record<string, unknown>);
      toast.success("Profile generated!");
    } catch (error) {
      toast.error("Profiling failed: " + (error as Error).message);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="size-4 text-green-500" />;
      case "failed":
        return <XCircle className="size-4 text-red-500" />;
      default:
        return <Clock className="size-4 text-yellow-500" />;
    }
  };

  const tabs = [
    { id: "transform" as const, label: "Transform", icon: Sparkles },
    { id: "history" as const, label: "Pipeline History", icon: History },
  ];

  return (
    <PageWrapper title="ETL Pipeline" description="Automated data extraction, cleaning, transformation, and loading.">
      <div className="space-y-4">
        <div className="flex gap-1 p-1 bg-muted/50 rounded-lg w-fit">
          {tabs.map((tab) => (
            <Button
              key={tab.id}
              variant={activeTab === tab.id ? "default" : "ghost"}
              size="sm"
              className={cn(
                "gap-2",
                activeTab === tab.id && "shadow-sm"
              )}
              onClick={() => setActiveTab(tab.id)}
            >
              <tab.icon className="size-4" />
              {tab.label}
            </Button>
          ))}
        </div>

        {activeTab === "transform" && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="size-5" />
                Transform Existing Data
              </CardTitle>
              <CardDescription>Select a dataset to clean or profile</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Select value={selectedDataset ?? ""} onValueChange={setSelectedDataset}>
                <SelectTrigger className="w-full md:w-[300px]">
                  <SelectValue placeholder="Select dataset to transform" />
                </SelectTrigger>
                <SelectContent>
                  {datasets?.datasets.map((name) => (
                    <SelectItem key={name} value={name}>{name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {selectedDataset && (
                <div className="flex gap-4">
                  <Button
                    onClick={handleClean}
                    disabled={cleanMutation.isPending}
                  >
                    <Sparkles className="size-4 mr-2" />
                    {cleanMutation.isPending ? "Cleaning..." : "Auto-Clean Data"}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={handleProfile}
                    disabled={profileMutation.isPending}
                  >
                    <BarChart3 className="size-4 mr-2" />
                    {profileMutation.isPending ? "Profiling..." : "Profile Dataset"}
                  </Button>
                </div>
              )}

              {cleanMutation.isSuccess && cleanMutation.data && (
                <Card className="mt-4">
                  <CardHeader>
                    <CardTitle className="text-sm">Cleaning Result</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="text-xs bg-muted p-4 rounded overflow-auto max-h-[300px]">
                      {JSON.stringify(cleanMutation.data.result, null, 2)}
                    </pre>
                  </CardContent>
                </Card>
              )}

              {profileResult && (
                <Card className="mt-4">
                  <CardHeader>
                    <CardTitle className="text-sm">Profile Result</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="text-xs bg-muted p-4 rounded overflow-auto max-h-[300px]">
                      {JSON.stringify(profileResult, null, 2)}
                    </pre>
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        )}

        {activeTab === "history" && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="size-5" />
                Pipeline History
              </CardTitle>
              <CardDescription>Recent ETL pipeline runs</CardDescription>
            </CardHeader>
            <CardContent>
              {historyLoading ? (
                <div className="space-y-2">
                  {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} className="h-16" />
                  ))}
                </div>
              ) : history?.history && history.history.length > 0 ? (
                <Accordion type="multiple" className="w-full">
                  {history.history.slice().reverse().slice(0, 20).map((item, i) => (
                    <AccordionItem key={i} value={`item-${i}`}>
                      <AccordionTrigger>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(item.status)}
                          <span className="font-medium capitalize">{item.step}</span>
                          {item.table_name && (
                            <Badge variant="outline">{item.table_name}</Badge>
                          )}
                          <span className="text-xs text-muted-foreground ml-auto">
                            {item.timestamp}
                          </span>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent>
                        <pre className="text-xs bg-muted p-4 rounded overflow-auto">
                          {JSON.stringify(item, null, 2)}
                        </pre>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              ) : (
                <p className="text-muted-foreground text-center py-8">No pipeline runs yet.</p>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </PageWrapper>
  );
}
