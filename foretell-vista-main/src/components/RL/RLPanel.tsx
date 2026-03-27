import { useMemo, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, BarChart, Bar } from "recharts";
import { Button } from "@/components/ui/button";
import { Zap } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchOrderRecommendations, fetchOrderScenario, fetchRlMetrics, fetchRlRewards, qk } from "@/api/queries";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";

const urgencyColor: Record<string, string> = {
  medium: "text-warning",
  high: "text-chart-4",
  critical: "text-destructive",
};

export function RLPanel() {
  const [useRl, setUseRl] = useState(true);
  const [demandScale, setDemandScale] = useState([1]);
  const { data: recs } = useQuery({
    queryKey: [...qk.orderRecs, useRl],
    queryFn: () => fetchOrderRecommendations(useRl ? "rl" : "baseline"),
  });
  const { data: rewards } = useQuery({ queryKey: qk.rlRewards, queryFn: fetchRlRewards });
  const { data: metrics } = useQuery({ queryKey: qk.rlMetrics, queryFn: fetchRlMetrics });
  const topRec = recs?.recommendations?.[0];
  const { data: scenario } = useQuery({
    queryKey: qk.orderScenario(topRec?.storeId ?? "default", topRec?.sku ?? "default", demandScale[0]),
    queryFn: () => fetchOrderScenario(topRec?.storeId, topRec?.sku, demandScale[0]),
    enabled: Boolean(topRec?.sku),
  });
  const rlRecommendations = recs?.recommendations ?? [];
  const rewardCurveData = rewards?.data ?? [];
  const costComparison = [
    { name: "RL", cost: metrics?.rl_total_cost ?? 0 },
    { name: "Baseline", cost: metrics?.baseline_total_cost ?? 0 },
  ];
  const scenarioDaily = scenario?.daily ?? [];
  const scenarioBars = useMemo(
    () => [
      { name: "RL", cost: scenario?.rl?.total_cost ?? 0 },
      { name: "Baseline", cost: scenario?.baseline?.total_cost ?? 0 },
    ],
    [scenario],
  );

  return (
    <div id="rl" className="space-y-4">
      <div className="glass-card p-5">
        <div className="mb-4">
          <h2 className="panel-header">RL Ordering Recommendations</h2>
          <p className="text-xs text-muted-foreground mt-1">AI-optimized order suggestions based on reinforcement learning</p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground mt-3">
            <Switch checked={useRl} onCheckedChange={setUseRl} />
            {useRl ? "RL Policy" : "Heuristic Baseline"}
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {rlRecommendations.map((rec) => (
            <div key={rec.sku} className="p-4 rounded-lg bg-secondary/40 border border-border hover:border-primary/30 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs text-muted-foreground">{rec.sku}</span>
                <span className={`text-xs font-semibold uppercase ${urgencyColor[rec.urgency]}`}>{rec.urgency}</span>
              </div>
              <p className="text-sm font-medium text-foreground mb-2">{rec.action}</p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-primary rounded-full" style={{ width: `${rec.confidence}%` }} />
                  </div>
                  <span className="text-xs font-mono text-muted-foreground">{rec.confidence}%</span>
                </div>
                <span className="text-xs text-primary font-medium">Save {rec.expectedSaving}</span>
              </div>
              <Button size="sm" variant="outline" className="mt-3 w-full text-xs h-7 border-border hover:bg-primary hover:text-primary-foreground">
                <Zap className="h-3 w-3 mr-1" /> Execute Order
              </Button>
            </div>
          ))}
        </div>
      </div>
      <div className="glass-card p-5">
        <h2 className="panel-header mb-4">Reward Curve</h2>
        <div className="flex flex-wrap gap-4 text-xs text-muted-foreground mb-4">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-primary" />
            RL Total Cost: <span className="text-foreground font-mono">${metrics?.rl_total_cost?.toFixed?.(2) ?? "0.00"}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-muted-foreground" />
            Baseline Total Cost: <span className="text-foreground font-mono">${metrics?.baseline_total_cost?.toFixed?.(2) ?? "0.00"}</span>
          </div>
          <div className="flex items-center gap-2">
            Savings Delta: <span className="text-primary font-mono">${metrics?.cost_delta?.toFixed?.(2) ?? "0.00"}</span>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="h-[200px] md:col-span-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={rewardCurveData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" />
                <XAxis dataKey="episode" tick={{ fontSize: 10, fill: "hsl(215, 15%, 55%)" }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "hsl(215, 15%, 55%)" }} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(220, 18%, 10%)",
                    border: "1px solid hsl(220, 14%, 18%)",
                    borderRadius: "8px",
                    fontSize: "12px",
                    color: "hsl(210, 20%, 92%)",
                  }}
                />
                <Line type="monotone" dataKey="reward" stroke="hsl(160, 70%, 45%)" strokeWidth={2} dot={false} name="RL Agent" />
                <Line type="monotone" dataKey="baseline" stroke="hsl(215, 15%, 55%)" strokeWidth={1} dot={false} strokeDasharray="4 4" name="Baseline" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={costComparison} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: "hsl(215, 15%, 55%)" }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "hsl(215, 15%, 55%)" }} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(220, 18%, 10%)",
                    border: "1px solid hsl(220, 14%, 18%)",
                    borderRadius: "8px",
                    fontSize: "12px",
                    color: "hsl(210, 20%, 92%)",
                  }}
                />
                <Bar dataKey="cost" fill="hsl(200, 80%, 55%)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      <div className="glass-card p-5">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between mb-4">
          <div>
            <h2 className="panel-header">Scenario Simulation</h2>
            <p className="text-xs text-muted-foreground mt-1">Stress-test adaptive vs baseline ordering under demand shocks</p>
          </div>
          <div className="w-full md:w-72">
            <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
              <span>Demand Scale</span>
              <span>{demandScale[0].toFixed(2)}x</span>
            </div>
            <Slider min={0.7} max={1.5} step={0.05} value={demandScale} onValueChange={setDemandScale} />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="p-4 rounded-lg bg-secondary/40 border border-border">
            <p className="data-label">Scenario SKU</p>
            <p className="text-sm font-mono text-foreground">{scenario?.product_id ?? "—"}</p>
          </div>
          <div className="p-4 rounded-lg bg-secondary/40 border border-border">
            <p className="data-label">RL Service Level</p>
            <p className="text-sm font-mono text-primary">{scenario?.rl?.service_level?.toFixed?.(1) ?? "0.0"}%</p>
          </div>
          <div className="p-4 rounded-lg bg-secondary/40 border border-border">
            <p className="data-label">Scenario Savings</p>
            <p className="text-sm font-mono text-primary">${scenario?.savings?.toFixed?.(2) ?? "0.00"}</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="h-[220px] md:col-span-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={scenarioDaily}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" />
                <XAxis dataKey="day" tick={{ fontSize: 10, fill: "hsl(215, 15%, 55%)" }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "hsl(215, 15%, 55%)" }} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(220, 18%, 10%)",
                    border: "1px solid hsl(220, 14%, 18%)",
                    borderRadius: "8px",
                    fontSize: "12px",
                    color: "hsl(210, 20%, 92%)",
                  }}
                />
                <Line type="monotone" dataKey="rlEndingInventory" stroke="hsl(160, 70%, 45%)" strokeWidth={2} dot={false} name="RL Inventory" />
                <Line type="monotone" dataKey="baselineEndingInventory" stroke="hsl(215, 15%, 55%)" strokeWidth={2} dot={false} strokeDasharray="4 4" name="Baseline Inventory" />
                <Line type="monotone" dataKey="demand" stroke="hsl(38, 92%, 50%)" strokeWidth={1.5} dot={false} name="Demand" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scenarioBars}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: "hsl(215, 15%, 55%)" }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "hsl(215, 15%, 55%)" }} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(220, 18%, 10%)",
                    border: "1px solid hsl(220, 14%, 18%)",
                    borderRadius: "8px",
                    fontSize: "12px",
                    color: "hsl(210, 20%, 92%)",
                  }}
                />
                <Bar dataKey="cost" fill="hsl(200, 80%, 55%)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
