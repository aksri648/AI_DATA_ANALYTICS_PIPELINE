import { useState, useRef } from "react";
import { PageWrapper } from "@/components/layout/page-wrapper";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { useIngestFile, useDatasets } from "@/hooks/use-api";
import { toast } from "sonner";
import { Upload, FileUp, CheckCircle, AlertCircle } from "lucide-react";

export function DataUploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [tableName, setTableName] = useState("");
  const [runEtl, setRunEtl] = useState(true);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const ingestMutation = useIngestFile();
  const { data: datasets } = useDatasets();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      const name = selectedFile.name.replace(/\.[^/.]+$/, "").replace(/[^a-zA-Z0-9_]/g, "_");
      setTableName(name);
      setResult(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      const name = droppedFile.name.replace(/\.[^/.]+$/, "").replace(/[^a-zA-Z0-9_]/g, "_");
      setTableName(name);
      setResult(null);
    }
  };

  const handleIngest = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    if (tableName) formData.append("table_name", tableName);
    formData.append("run_etl", String(runEtl));

    try {
      const data = await ingestMutation.mutateAsync(formData);
      setResult(data as unknown as Record<string, unknown>);
      toast.success("Data ingested successfully!");
    } catch (error) {
      toast.error("Ingestion failed: " + (error as Error).message);
    }
  };

  return (
    <PageWrapper title="Data Upload & Ingestion" description="Upload files for ETL processing and analysis.">
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="size-5" />
              Upload File
            </CardTitle>
            <CardDescription>
              Supports CSV, Excel, JSON, Parquet, and PDF files
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div
              className="border-2 border-dashed rounded-lg p-8 text-center hover:border-primary/50 transition-colors cursor-pointer"
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".csv,.xlsx,.xls,.json,.parquet,.pdf"
                onChange={handleFileChange}
              />
              <FileUp className="size-10 mx-auto mb-4 text-muted-foreground" />
              {file ? (
                <div>
                  <p className="font-medium">{file.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {(file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-muted-foreground">Drag and drop or click to select</p>
                </div>
              )}
            </div>

            {file && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="table-name">Table Name</Label>
                  <Input
                    id="table-name"
                    value={tableName}
                    onChange={(e) => setTableName(e.target.value)}
                    placeholder="Enter table name"
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="run-etl"
                    checked={runEtl}
                    onCheckedChange={(checked: boolean) => setRunEtl(checked)}
                    disabled={file.name.toLowerCase().endsWith(".pdf")}
                  />
                  <Label htmlFor="run-etl">
                    Run full ETL (clean + transform + features)
                  </Label>
                </div>

                <Button
                  onClick={handleIngest}
                  disabled={ingestMutation.isPending}
                  className="w-full"
                >
                  {ingestMutation.isPending ? "Ingesting..." : "Ingest Data"}
                </Button>

                {ingestMutation.isPending && <Progress className="w-full" />}
              </>
            )}
          </CardContent>
        </Card>

        <div className="space-y-4">
          {result && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="size-5 text-green-500" />
                  Ingestion Result
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Table Name</span>
                    <Badge>{String(result.table_name)}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Status</span>
                    <Badge variant="default">Success</Badge>
                  </div>
                  {(result.is_pdf as boolean) && (result.metadata as Record<string, unknown>) && (
                    <Accordion type="single" collapsible className="w-full">
                      <AccordionItem value="metadata">
                        <AccordionTrigger>PDF Extraction Details</AccordionTrigger>
                        <AccordionContent>
                          <pre className="text-xs overflow-auto p-2 bg-muted rounded">
                            {JSON.stringify(result.metadata as Record<string, unknown>, null, 2)}
                          </pre>
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {ingestMutation.isError && (
            <Card className="border-destructive">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-destructive">
                  <AlertCircle className="size-5" />
                  Error
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">{ingestMutation.error.message}</p>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Available Datasets</CardTitle>
              <CardDescription>
                {datasets?.datasets.length ?? 0} datasets loaded
              </CardDescription>
            </CardHeader>
            <CardContent>
              {datasets?.datasets && datasets.datasets.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {datasets.datasets.map((name) => (
                    <Badge key={name} variant="outline">{name}</Badge>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No datasets loaded yet</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </PageWrapper>
  );
}
