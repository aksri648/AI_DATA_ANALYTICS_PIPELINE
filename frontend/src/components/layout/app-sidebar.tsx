import {
  Upload,
  Table,
  MessageSquare,
  LayoutDashboard,
  Lightbulb,
  FileText,
  Activity,
  Settings,
  Bot,
  Database,
  CheckCircle,
  XCircle,
  Workflow,
} from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarHeader,
  SidebarFooter,
  SidebarSeparator,
} from "@/components/ui/sidebar";
import { Badge } from "@/components/ui/badge";
import { useHealth, useDatasets } from "@/hooks/use-api";

const navItems = [
  { title: "Data Upload", icon: Upload, path: "/" },
  { title: "ETL Pipeline", icon: Workflow, path: "/etl" },
  { title: "Data Preview", icon: Table, path: "/preview" },
  { title: "Analytics", icon: MessageSquare, path: "/analytics" },
  { title: "Dashboards", icon: LayoutDashboard, path: "/dashboards" },
  { title: "AI Insights", icon: Lightbulb, path: "/insights" },
  { title: "Reports", icon: FileText, path: "/reports" },
  { title: "Agent Monitor", icon: Activity, path: "/monitor" },
  { title: "Settings", icon: Settings, path: "/settings" },
];

export function AppSidebar() {
  const location = useLocation();
  const { data: health } = useHealth();
  const { data: datasets } = useDatasets();

  return (
    <Sidebar>
      <SidebarHeader>
        <div className="flex items-center gap-2 px-2 py-2">
          <Bot className="size-6" />
          <span className="text-lg font-semibold">AI Analytics</span>
        </div>
      </SidebarHeader>
      <SidebarSeparator />
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarMenu className="gap-1">
            {navItems.map((item) => (
              <SidebarMenuItem key={item.path}>
                <SidebarMenuButton
                  asChild
                  isActive={location.pathname === item.path}
                  className="h-9"
                >
                  <NavLink to={item.path}>
                    <item.icon />
                    <span>{item.title}</span>
                  </NavLink>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroup>
        <SidebarSeparator />
        <SidebarGroup>
          <SidebarGroupLabel>System Status</SidebarGroupLabel>
          <div className="px-2 space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-1.5">
                {health?.ollama.healthy ? (
                  <CheckCircle className="size-3.5 text-green-500" />
                ) : (
                  <XCircle className="size-3.5 text-red-500" />
                )}
                Ollama
              </span>
              <Badge variant={health?.ollama.healthy ? "default" : "destructive"}>
                {health?.ollama.healthy ? "Online" : "Offline"}
              </Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-1.5">
                <Database className="size-3.5" />
                Datasets
              </span>
              <Badge variant="secondary">
                {datasets?.datasets.length ?? 0}
              </Badge>
            </div>
          </div>
        </SidebarGroup>
      </SidebarContent>
      <SidebarSeparator />
      <SidebarFooter>
        <div className="px-2 py-2 text-xs text-muted-foreground">
          <p>AI Analytics & ETL Copilot v1.0</p>
          <p>CrewAI + Ollama + DuckDB</p>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
