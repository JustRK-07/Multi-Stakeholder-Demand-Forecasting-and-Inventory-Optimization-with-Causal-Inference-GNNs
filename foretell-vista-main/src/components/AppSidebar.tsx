import {
  BarChart3,
  TrendingUp,
  Package,
  Upload,
  Settings,
  Network,
  Megaphone,
  LayoutDashboard,
  Activity,
} from "lucide-react";
import { NavLink } from "@/components/NavLink";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";

const mainItems = [
  { title: "Dashboard", url: "/dashboard", icon: LayoutDashboard },
  { title: "Upload Dataset", url: "/dashboard/upload", icon: Upload },
];

const analyticsItems = [
  { title: "Forecast Results", url: "/dashboard/forecast", icon: TrendingUp },
  { title: "Inventory", url: "/dashboard/inventory", icon: Package },
  { title: "Promotion Analysis", url: "/dashboard/promotions", icon: Megaphone },
  { title: "Product Graph", url: "/dashboard/graph", icon: Network },
];

const systemItems = [
  { title: "Settings", url: "/dashboard/settings", icon: Settings },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";

  const renderGroup = (label: string, items: typeof mainItems) => (
    <SidebarGroup key={label}>
      <SidebarGroupLabel className="text-muted-foreground/60 text-[10px] uppercase tracking-[0.15em]">
        {label}
      </SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          {items.map((item) => (
            <SidebarMenuItem key={item.title}>
              <SidebarMenuButton asChild>
                <NavLink
                  to={item.url}
                  end={item.url === "/dashboard"}
                  className="flex items-center gap-3 px-3 py-2 rounded-md text-sidebar-foreground hover:text-foreground hover:bg-sidebar-accent transition-colors"
                  activeClassName="bg-sidebar-accent text-foreground font-medium"
                >
                  <item.icon className="h-4 w-4 shrink-0" />
                  {!collapsed && <span className="text-sm">{item.title}</span>}
                </NavLink>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );

  return (
    <Sidebar collapsible="icon" className="border-r border-border">
      <SidebarContent className="pt-4">
        <div className="px-4 pb-4 mb-2 border-b border-border">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-primary shrink-0" />
            {!collapsed && (
              <div>
                <h1 className="text-sm font-bold text-foreground tracking-tight">RetailCast AI</h1>
                <p className="text-[10px] text-muted-foreground">Forecasting Platform</p>
              </div>
            )}
          </div>
        </div>
        {renderGroup("Main", mainItems)}
        {renderGroup("Analytics", analyticsItems)}
        {renderGroup("System", systemItems)}
      </SidebarContent>
    </Sidebar>
  );
}
