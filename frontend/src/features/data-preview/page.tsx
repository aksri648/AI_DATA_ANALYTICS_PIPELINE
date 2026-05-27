import { useState } from "react";
import { PageWrapper } from "@/components/layout/page-wrapper";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import {
  useDatasets,
  useDataset,
  useDatasetProfile,
  useDatasetValidation,
  useDatasetStatistics,
  useCleanDataset,
  useProfileDataset,
} from "@/hooks/use-api";
import { toast } from "sonner";
import { Database, Columns, BarChart3, Activity, Sparkles } from "lucide-react";

export function DataPreviewPage() {
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const { data: datasets } = useDatasets();
  const { data: dataset, isLoading: datasetLoading } = useDataset(selectedDataset);
  const { data: profile } = useDatasetProfile(selectedDataset);
  const { data: validation } = useDatasetValidation(selectedDataset);
  const { data: statistics } = useDatasetStatistics(selectedDataset);

  const cleanMutation = useCleanDataset();
  const profileMutation = useProfileDataset();

  const handleClean = async () => {
    if (!selectedDataset) return;
    try {
      await cleanMutation.mutateAsync(selectedDataset);
      toast.success("Data cleaned successfully!");
    } catch (error) {
      toast.error("Cleaning failed: " + (error as Error).message);
    }
  };

  const handleProfile = async () => {
    if (!selectedDataset) return;
    try {
      await profileMutation.mutateAsync(selectedDataset);
      toast.success("Profile generated!");
    } catch (error) {
      toast.error("Profiling failed: " + (error as Error).message);
    }
  };

  return (
    <PageWrapper title="Data Preview" description="Browse and inspect loaded datasets.">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="size-5" />
              Select Dataset
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Select value={selectedDataset ?? ""} onValueChange={setSelectedDataset}>
              <SelectTrigger className="w-full md:w-[300px]">
                <SelectValue placeholder="Select a dataset to view" />
              </SelectTrigger>
              <SelectContent>
                {datasets?.datasets.map((name) => (
                  <SelectItem key={name} value={name}>{name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        {selectedDataset && (
          <Tabs defaultValue="preview" className="space-y-4">
            <TabsList>
              <TabsTrigger value="preview">Preview</TabsTrigger>
              <TabsTrigger value="schema">Schema</TabsTrigger>
              <TabsTrigger value="statistics">Statistics</TabsTrigger>
              <TabsTrigger value="quality">Quality Report</TabsTrigger>
            </TabsList>

            <TabsContent value="preview">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <Table className="size-5" />
                      Data Preview
                    </span>
                    {dataset && (
                      <div className="flex gap-2">
                        <Badge variant="outline">{dataset.total_rows} rows</Badge>
                        <Badge variant="outline">{dataset.total_columns} columns</Badge>
                      </div>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {datasetLoading ? (
                    <Skeleton className="h-[400px]" />
                  ) : dataset ? (
                    <div className="overflow-auto max-h-[500px]">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            {dataset.columns.map((col) => (
                              <TableHead key={col} className="whitespace-nowrap">
                                {col}
                                <span className="block text-xs text-muted-foreground">
                                  {dataset.dtypes[col]}
                                </span>
                              </TableHead>
                            ))}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {dataset.preview.map((row, i) => (
                            <TableRow key={i}>
                              {dataset.columns.map((col) => (
                                <TableCell key={col} className="text-xs">
                                  {String(row[col] ?? "")}
                                </TableCell>
                              ))}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  ) : (
                    <p className="text-muted-foreground">No data available</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="schema">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Columns className="size-5" />
                    Column Details
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {dataset ? (
                    <Accordion type="multiple" className="w-full">
                      {dataset.columns.map((col) => (
                        <AccordionItem key={col} value={col}>
                          <AccordionTrigger>
                            <div className="flex items-center gap-2">
                              <span>{col}</span>
                              <Badge variant="secondary">{dataset.dtypes[col]}</Badge>
                            </div>
                          </AccordionTrigger>
                          <AccordionContent>
                            <pre className="text-xs bg-muted p-2 rounded overflow-auto">
                              {JSON.stringify(
                                (profile?.profile as Record<string, unknown>)?.[col] ?? {},
                                null,
                                2
                              )}
                            </pre>
                          </AccordionContent>
                        </AccordionItem>
                      ))}
                    </Accordion>
                  ) : (
                    <p className="text-muted-foreground">Select a dataset</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="statistics">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="size-5" />
                    Descriptive Statistics
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {statistics?.statistics && Object.keys(statistics.statistics).length > 0 ? (
                    <pre className="text-xs bg-muted p-4 rounded overflow-auto max-h-[400px]">
                      {JSON.stringify(statistics.statistics, null, 2)}
                    </pre>
                  ) : (
                    <p className="text-muted-foreground">No numeric columns to compute statistics.</p>
                  )}
                  <div className="my-4 border-t" />
                  <h4 className="font-medium mb-2">Missing Values</h4>
                  {statistics?.missing && Object.keys(statistics.missing).length > 0 ? (
                    <pre className="text-xs bg-muted p-4 rounded overflow-auto max-h-[200px]">
                      {JSON.stringify(statistics.missing, null, 2)}
                    </pre>
                  ) : (
                    <p className="text-muted-foreground">No missing values found.</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="quality">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <Activity className="size-5" />
                      Data Quality Report
                    </span>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={handleClean}
                        disabled={cleanMutation.isPending}
                      >
                        <Sparkles className="size-4 mr-1" />
                        {cleanMutation.isPending ? "Cleaning..." : "Auto-Clean"}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={handleProfile}
                        disabled={profileMutation.isPending}
                      >
                        <BarChart3 className="size-4 mr-1" />
                        {profileMutation.isPending ? "Profiling..." : "Profile"}
                      </Button>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {validation?.validation ? (
                    <pre className="text-xs bg-muted p-4 rounded overflow-auto max-h-[400px]">
                      {JSON.stringify(validation.validation, null, 2)}
                    </pre>
                  ) : (
                    <p className="text-muted-foreground">No validation data available.</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        )}

        {!selectedDataset && (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Database className="size-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">Select a dataset to preview</p>
            </CardContent>
          </Card>
        )}
      </div>
    </PageWrapper>
  );
}
