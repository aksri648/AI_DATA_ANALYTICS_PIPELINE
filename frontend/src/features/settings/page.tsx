import { useState } from "react";
import { PageWrapper } from "@/components/layout/page-wrapper";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { useSettings, useHealth } from "@/hooks/use-api";
import { toast } from "sonner";
import { CheckCircle, XCircle, Database, Bot, Plug, RefreshCw } from "lucide-react";

export function SettingsPage() {
  const { data: settings, isLoading: settingsLoading, refetch: refetchSettings } = useSettings();
  const { data: health, isLoading: healthLoading, refetch: refetchHealth } = useHealth();
  const [ollamaUrl, setOllamaUrl] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);

  const handleConnect = async () => {
    if (!ollamaUrl.trim()) {
      toast.error("Please enter an Ollama URL");
      return;
    }
    setIsConnecting(true);
    try {
      const response = await fetch(`/api/settings/ollama-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: ollamaUrl.trim() }),
      });
      if (response.ok) {
        toast.success("Ollama URL updated! Refreshing connection...");
        await refetchSettings();
        await refetchHealth();
      } else {
        toast.error("Failed to update Ollama URL");
      }
    } catch {
      toast.error("Could not connect to server");
    } finally {
      setIsConnecting(false);
    }
  };

  if (settingsLoading || healthLoading) {
    return (
      <PageWrapper title="Settings" description="Configure the AI Analytics & ETL Copilot.">
        <div className="grid gap-4">
          <Skeleton className="h-[200px]" />
          <Skeleton className="h-[150px]" />
          <Skeleton className="h-[200px]" />
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper title="Settings" description="Configure the AI Analytics & ETL Copilot.">
      <div className="grid gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bot className="size-5" />
              Ollama Configuration
            </CardTitle>
            <CardDescription>Local LLM inference settings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <Label>Connection Status</Label>
              <Badge variant={health?.ollama.healthy ? "default" : "destructive"} className="flex items-center gap-1">
                {health?.ollama.healthy ? (
                  <CheckCircle className="size-3" />
                ) : (
                  <XCircle className="size-3" />
                )}
                {health?.ollama.healthy ? "Connected" : "Disconnected"}
              </Badge>
            </div>
            <Separator />
            <div className="space-y-2">
              <Label htmlFor="ollama-url">Ollama Server URL</Label>
              <div className="flex gap-2">
                <Input
                  id="ollama-url"
                  placeholder="http://localhost:11434"
                  value={ollamaUrl}
                  onChange={(e) => setOllamaUrl(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleConnect()}
                />
                <Button onClick={handleConnect} disabled={isConnecting}>
                  {isConnecting ? (
                    <RefreshCw className="size-4 mr-2 animate-spin" />
                  ) : (
                    <Plug className="size-4 mr-2" />
                  )}
                  Connect
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Enter the URL of your Ollama server and click Connect to verify the connection.
              </p>
            </div>
            <Separator />
            <div className="space-y-2">
              <Label htmlFor="model">Active Model</Label>
              <Input id="model" value={settings?.ollama.model ?? ""} disabled />
            </div>
            <div className="space-y-2">
              <Label>Available Models</Label>
              <div className="flex flex-wrap gap-2">
                {settings?.ollama.available_models.map((model) => (
                  <Badge key={model} variant="outline">{model}</Badge>
                ))}
                {(!settings?.ollama.available_models || settings.ollama.available_models.length === 0) && (
                  <p className="text-sm text-muted-foreground">No models available</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="size-5" />
              Database Configuration
            </CardTitle>
            <CardDescription>DuckDB analytics engine settings</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Label>DuckDB Path</Label>
              <Input value={settings?.duckdb_path ?? ""} disabled />
              <p className="text-xs text-muted-foreground">
                DuckDB is used as the local analytics engine. Data is cleared on each restart.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>About</CardTitle>
            <CardDescription>AI Analytics & ETL Copilot v1.0</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              A production-grade local AI-native ETL + Analytics platform.
            </p>
            <div className="space-y-2">
              <Label>Tech Stack</Label>
              <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                <li>CrewAI Multi-Agent Orchestration</li>
                <li>Ollama Local LLMs</li>
                <li>DuckDB Analytics Engine</li>
                <li>React + shadcn/ui Frontend</li>
                <li>MCP Tools Integration</li>
              </ul>
            </div>
            <Separator className="my-4" />
            <div className="space-y-2">
              <Label>Agents</Label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  "Data Ingestion Agent",
                  "ETL Agent",
                  "SQL Analyst Agent",
                  "Visualization Agent",
                  "Business Insights Agent",
                  "Report Generation Agent",
                  "MCP Tool Agent",
                  "QA Validation Agent",
                ].map((agent) => (
                  <Badge key={agent} variant="secondary">{agent}</Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageWrapper>
  );
}
