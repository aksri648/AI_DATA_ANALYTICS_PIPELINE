import { useState } from "react";
import { PageWrapper } from "@/components/layout/page-wrapper";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { usePipelineHistory, useConversations, useMonitorContext } from "@/hooks/use-api";
import { History, MessageSquare, Database, CheckCircle, XCircle, Clock, Bot, User, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

export function AgentMonitorPage() {
  const [activeTab, setActiveTab] = useState<"history" | "conversations" | "context">("history");
  const { data: history, isLoading: historyLoading } = usePipelineHistory();
  const { data: conversations, isLoading: conversationsLoading } = useConversations();
  const { data: context, isLoading: contextLoading } = useMonitorContext();

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
    { id: "history" as const, label: "Pipeline History", icon: History },
    { id: "conversations" as const, label: "Conversation Memory", icon: MessageSquare },
    { id: "context" as const, label: "Workflow State", icon: Database },
  ];

  return (
    <PageWrapper title="Agent Activity Monitor" description="Monitor CrewAI agent activities and workflow steps.">
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
            </Button>
          ))}
        </div>

        {activeTab === "history" && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="size-5" />
                Pipeline History
              </CardTitle>
              <CardDescription>Recent ETL pipeline execution history</CardDescription>
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
                  {history.history.slice().reverse().map((item, i) => (
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
                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                  <History className="size-12 mb-4" />
                  <p>No ETL pipeline history yet.</p>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {activeTab === "conversations" && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="size-5" />
                Conversation Memory
              </CardTitle>
              <CardDescription>Recent chat interactions</CardDescription>
            </CardHeader>
            <CardContent>
              {conversationsLoading ? (
                <div className="space-y-2">
                  {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} className="h-16" />
                  ))}
                </div>
              ) : conversations?.conversations && conversations.conversations.length > 0 ? (
                <div className="space-y-3">
                  {conversations.conversations.slice(-30).map((msg, i) => (
                    <div
                      key={i}
                      className={cn(
                        "flex gap-3 p-3 rounded-lg",
                        msg.role === "user" ? "bg-primary/5" : "bg-muted"
                      )}
                    >
                      <div className="flex-shrink-0">
                        {msg.role === "user" ? (
                          <User className="size-5" />
                        ) : (
                          <Bot className="size-5" />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-sm capitalize">{msg.role}</span>
                          {msg.timestamp && (
                            <span className="text-xs text-muted-foreground">
                              {msg.timestamp}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-3">
                          {msg.content}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                  <MessageSquare className="size-12 mb-4" />
                  <p>No conversation history yet.</p>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {activeTab === "context" && (
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="size-5" />
                  Analytics Context
                </CardTitle>
                <CardDescription>Current analytics state</CardDescription>
              </CardHeader>
              <CardContent>
                {contextLoading ? (
                  <Skeleton className="h-[200px]" />
                ) : context?.analytics_context ? (
                  <pre className="text-xs bg-muted p-4 rounded overflow-auto max-h-[300px]">
                    {JSON.stringify(context.analytics_context, null, 2)}
                  </pre>
                ) : (
                  <p className="text-muted-foreground text-center py-8">
                    No analytics context stored yet.
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="size-5" />
                  Schema Cache
                </CardTitle>
                <CardDescription>Cached table schemas</CardDescription>
              </CardHeader>
              <CardContent>
                {contextLoading ? (
                  <Skeleton className="h-[200px]" />
                ) : context?.schema_cache && Object.keys(context.schema_cache).length > 0 ? (
                  <div className="space-y-2">
                    {Object.entries(context.schema_cache).map(([table, data]) => (
                      <div key={table} className="flex items-center justify-between p-2 bg-muted rounded">
                        <code className="text-sm">{table}</code>
                        <span className="text-xs text-muted-foreground">
                          {(data as Record<string, unknown>).cached_at as string}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-center py-8">
                    No schema cache yet.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </PageWrapper>
  );
}
