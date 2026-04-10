import { KPIPanel } from "@/components/KPI/KPIPanel";
import { ForecastPanel } from "@/components/Forecast/ForecastPanel";
import { InventoryPanel } from "@/components/Inventory/InventoryPanel";
import { RLPanel } from "@/components/RL/RLPanel";
import { CausalPanel } from "@/components/Causal/CausalPanel";
import { ExplainabilityPanel } from "@/components/Explainability/ExplainabilityPanel";
import { MonitoringPanel } from "@/components/Monitoring/MonitoringPanel";
import { StorePanel } from "@/components/Store/StorePanel";
import { FederatedPanel } from "@/components/Federated/FederatedPanel";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts";
import { useQuery } from "@tanstack/react-query";
import { fetchDashboardSummary, qk } from "@/api/queries";
import { useAuth } from "@/components/AuthProvider";
import { AlertCircle } from "lucide-react";

const DashboardHome = () => {
  const { user } = useAuth();
  const { data } = useQuery({ queryKey: qk.dashboardSummary, queryFn: fetchDashboardSummary });
  const salesTrend = data?.salesTrend ?? [];
  const inventoryLevels = data?.inventoryTrend ?? [];

  const getStoreTypeName = (storeType?: string) => {
    const names: Record<string, string> = {
      grocery: "Grocery & Supermarkets",
      fashion: "Fashion & Apparel",
      electronics: "Electronics & Tech",
    };
    return names[storeType || ""] || storeType || "Unknown";
  };

  return (
    <div className="space-y-4">
      {user?.storeType && user?.assignedModelId && (
        <div className="glass-card p-4 border border-primary/20 bg-primary/5">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-foreground text-sm">Your Pre-trained Model</h3>
              <p className="text-xs text-muted-foreground mt-1">
                <strong>{getStoreTypeName(user.storeType)}</strong> • Model {user.assignedModelId.split("-").pop()}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                No data upload needed! Your forecasts are powered by a pre-trained model optimized for your store type. 
              </p>
            </div>
          </div>
        </div>
      )}

      <KPIPanel />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Sales Trend */}
        <div className="glass-card p-5">
          <h3 className="panel-header mb-4">Sales Trend</h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={salesTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" />
              <XAxis dataKey="day" tick={{ fill: "hsl(215, 15%, 55%)", fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "hsl(215, 15%, 55%)", fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: "hsl(220, 18%, 10%)", border: "1px solid hsl(220, 14%, 18%)", borderRadius: 8, fontSize: 12, color: "hsl(210, 20%, 92%)" }} />
              <Line type="monotone" dataKey="sales" stroke="hsl(200, 80%, 55%)" strokeWidth={2} dot={false} name="Sales" />
              <Line type="monotone" dataKey="demand" stroke="hsl(160, 70%, 45%)" strokeWidth={2} dot={false} name="Demand Forecast" strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Inventory Levels */}
        <div className="glass-card p-5">
          <h3 className="panel-header mb-4">Inventory Levels</h3>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={inventoryLevels}>
              <defs>
                <linearGradient id="invGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(38, 92%, 50%)" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="hsl(38, 92%, 50%)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" />
              <XAxis dataKey="day" tick={{ fill: "hsl(215, 15%, 55%)", fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "hsl(215, 15%, 55%)", fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: "hsl(220, 18%, 10%)", border: "1px solid hsl(220, 14%, 18%)", borderRadius: 8, fontSize: 12, color: "hsl(210, 20%, 92%)" }} />
              <Area type="monotone" dataKey="level" stroke="hsl(38, 92%, 50%)" fill="url(#invGrad)" strokeWidth={2} name="Stock Level" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      <ForecastPanel />
      <InventoryPanel />

      <RLPanel />
      <CausalPanel />
      <MonitoringPanel />
      <ExplainabilityPanel />
      <StorePanel />
      <FederatedPanel />
    </div>
  );
};

export default DashboardHome;
