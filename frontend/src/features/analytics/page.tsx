import { useState, useRef, useEffect } from "react";
import { PageWrapper } from "@/components/layout/page-wrapper";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useDatasets, useChatMutation } from "@/hooks/use-api";
import { useChatStore, type ChatMessage } from "@/stores/chat-store";
import { toast } from "sonner";
import { MessageSquare, Send, Trash2, Bot, User, BarChart3 } from "lucide-react";

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="flex-shrink-0 size-8 rounded-full bg-primary/10 flex items-center justify-center">
          <Bot className="size-4" />
        </div>
      )}
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted"
        }`}
      >
        <div className="text-sm whitespace-pre-wrap">{message.content}</div>
        {message.chart && (
          <div
            className="mt-2 border rounded overflow-hidden"
            dangerouslySetInnerHTML={{ __html: message.chart }}
          />
        )}
        {message.insights && (
          <details className="mt-2">
            <summary className="text-xs cursor-pointer opacity-70">AI Analysis Details</summary>
            <div className="text-xs mt-1 whitespace-pre-wrap">{message.insights}</div>
          </details>
        )}
      </div>
      {isUser && (
        <div className="flex-shrink-0 size-8 rounded-full bg-primary flex items-center justify-center">
          <User className="size-4 text-primary-foreground" />
        </div>
      )}
    </div>
  );
}

export function AnalyticsPage() {
  const [question, setQuestion] = useState("");
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: datasets } = useDatasets();
  const chatMutation = useChatMutation();
  const { messages, addMessage, clearMessages } = useChatStore();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    const userQuestion = question.trim();
    setQuestion("");
    addMessage({ role: "user", content: userQuestion });

    try {
      const result = await chatMutation.mutateAsync({
        question: userQuestion,
        table_name: selectedDataset ?? undefined,
      });

      if (result.requires_file) {
        addMessage({
          role: "assistant",
          content: result.message ?? "Please upload data first.",
        });
      } else if (result.intent === "sql") {
        if (result.error) {
          addMessage({
            role: "assistant",
            content: `**Could not run SQL query.**\n\n${result.error}`,
          });
        } else {
          addMessage({
            role: "assistant",
            content: `**Query Results:**\n${JSON.stringify(result.result, null, 2)}`,
          });
        }
      } else if (result.intent === "visualization") {
        addMessage({
          role: "assistant",
          content: "Charts generated",
          chart: result.chart,
        });
      } else if (result.intent === "insights") {
        addMessage({
          role: "assistant",
          content: result.insights ?? "",
        });
      } else if (result.intent === "report") {
        addMessage({
          role: "assistant",
          content: "**Report generated.** Download from Reports page.",
        });
      } else {
        addMessage({
          role: "assistant",
          content: result.analysis ?? "",
          chart: result.chart,
          insights: result.insights,
        });
      }
    } catch (error) {
      toast.error("Analysis failed: " + (error as Error).message);
      addMessage({
        role: "assistant",
        content: `Error: ${(error as Error).message}`,
      });
    }
  };

  return (
    <PageWrapper title="Conversational Analytics" description="Ask questions about your data in natural language.">
      <div className="grid gap-4 md:grid-cols-[1fr_300px]">
        <Card className="flex flex-col h-[calc(100vh-200px)]">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <div>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="size-5" />
                Chat
              </CardTitle>
              <CardDescription>Ask anything about your data</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {chatMutation.isPending && (
                <Badge variant="secondary" className="animate-pulse">
                  Analyzing...
                </Badge>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={clearMessages}
                disabled={messages.length === 0}
              >
                <Trash2 className="size-4 mr-1" />
                Clear
              </Button>
            </div>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col">
            <ScrollArea className="flex-1 pr-4">
              <div className="space-y-4">
                {messages.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                    <BarChart3 className="size-12 mb-4" />
                    <p>Ask a question to get started</p>
                    <p className="text-xs mt-1">Try: "Show me a sales chart" or "Summarize the data"</p>
                  </div>
                )}
                {messages.map((msg, i) => (
                  <MessageBubble key={i} message={msg} />
                ))}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>
            <form onSubmit={handleSubmit} className="flex gap-2 mt-4">
              <Input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question about your data..."
                disabled={chatMutation.isPending}
              />
              <Button type="submit" disabled={!question.trim() || chatMutation.isPending}>
                <Send className="size-4" />
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Active Dataset</CardTitle>
            </CardHeader>
            <CardContent>
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
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Example Prompts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {[
                  "Show me a bar chart of sales",
                  "What are the top 5 products?",
                  "Summarize the key metrics",
                  "Find trends in the data",
                  "Generate a report",
                ].map((prompt) => (
                  <Button
                    key={prompt}
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start text-left h-auto py-2"
                    onClick={() => setQuestion(prompt)}
                  >
                    {prompt}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </PageWrapper>
  );
}
