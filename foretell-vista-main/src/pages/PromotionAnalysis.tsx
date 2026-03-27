import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Megaphone, TrendingUp, Target } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchPromotionImpact, fetchPromotionsSummary, qk } from "@/api/queries";

const PromotionAnalysis = () => {
  const [selectedId, setSelectedId] = useState("all");
  const { data: summary } = useQuery({ queryKey: qk.promotionsSummary, queryFn: fetchPromotionsSummary });
  const { data } = useQuery({
    queryKey: qk.promotionImpact(selectedId),
    queryFn: () => fetchPromotionImpact(selectedId),
  });

  useEffect(() => {
    if (summary?.availablePromotions?.length && !summary.availablePromotions.some((item) => item.id === selectedId)) {
      setSelectedId(summary.availablePromotions[0].id);
    }
  }, [selectedId, summary]);

  const selected = data?.promotion;
  const methodRows = selected?.methods
    ? Object.entries(selected.methods).map(([method, value]) => ({ method: method.toUpperCase(), value }))
    : [];
  const comparisonData = selected
    ? [
        { name: "Without Promo", sales: selected.baseline },
        { name: "With Promo", sales: selected.withPromo },
      ]
    : [];
  const promotions = summary?.availablePromotions ?? [];
  const tableRows = summary?.items ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-foreground">Promotion Impact Analysis</h2>
          <p className="text-xs text-muted-foreground">Causal inference with method diagnostics and cohort summaries</p>
        </div>
        <Select value={selectedId} onValueChange={setSelectedId}>
          <SelectTrigger className="w-48 h-8 text-xs bg-secondary border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {promotions.map((p) => (
              <SelectItem key={p.id} value={p.id} className="text-xs">{p.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="h-4 w-4 text-primary" />
            <span className="text-xs text-muted-foreground">Estimated Sales Lift</span>
          </div>
          <p className="kpi-value text-primary">{selected ? `${selected.lift >= 0 ? "+" : ""}${selected.lift}%` : "—"}</p>
        </div>
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-2">
            <Target className="h-4 w-4 text-accent" />
            <span className="text-xs text-muted-foreground">Confidence</span>
          </div>
          <p className="kpi-value text-foreground">{selected ? `${selected.confidence}%` : "—"}</p>
        </div>
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-2">
            <Megaphone className="h-4 w-4 text-warning" />
            <span className="text-xs text-muted-foreground">Incremental Units</span>
          </div>
          <p className="kpi-value text-foreground">{selected ? `${selected.incrementalUnits ?? 0}` : "—"}</p>
        </div>
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-2">
            <Target className="h-4 w-4 text-chart-3" />
            <span className="text-xs text-muted-foreground">ATE Units</span>
          </div>
          <p className="kpi-value text-foreground">{selected ? `${selected.ateUnits ?? 0}` : "—"}</p>
        </div>
      </div>

      {data?.warning ? (
        <div className="rounded-lg border border-warning/40 bg-warning/10 px-4 py-3 text-xs text-warning">
          {data.warning}
        </div>
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-5">
          <h3 className="panel-header mb-4">Sales With vs Without Promotion</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={comparisonData} barSize={60}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" />
              <XAxis dataKey="name" tick={{ fill: "hsl(215, 15%, 55%)", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "hsl(215, 15%, 55%)", fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: "hsl(220, 18%, 10%)", border: "1px solid hsl(220, 14%, 18%)", borderRadius: 8, fontSize: 12, color: "hsl(210, 20%, 92%)" }} />
              <Bar dataKey="sales" radius={[6, 6, 0, 0]}>
                <Cell fill="hsl(215, 15%, 35%)" />
                <Cell fill="hsl(160, 70%, 45%)" />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card p-5">
          <h3 className="panel-header mb-4">Method Comparison</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={methodRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" />
              <XAxis dataKey="method" tick={{ fill: "hsl(215, 15%, 55%)", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "hsl(215, 15%, 55%)", fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: "hsl(220, 18%, 10%)", border: "1px solid hsl(220, 14%, 18%)", borderRadius: 8, fontSize: 12, color: "hsl(210, 20%, 92%)" }} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {methodRows.map((_, i) => (
                  <Cell key={i} fill="hsl(200, 80%, 55%)" />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-muted-foreground">
            <div className="rounded-lg border border-border/60 bg-background/30 px-3 py-2">
              Treated Share: <span className="text-foreground font-mono">{selected?.diagnostics?.treated_share ?? 0}%</span>
            </div>
            <div className="rounded-lg border border-border/60 bg-background/30 px-3 py-2">
              Sample Size: <span className="text-foreground font-mono">{selected?.diagnostics?.sample_size ?? 0}</span>
            </div>
            <div className="rounded-lg border border-border/60 bg-background/30 px-3 py-2">
              Spread %: <span className="text-foreground font-mono">{selected?.diagnostics?.spread_pct ?? 0}%</span>
            </div>
            <div className="rounded-lg border border-border/60 bg-background/30 px-3 py-2">
              Cohort SKU: <span className="text-foreground font-mono">{String(selected?.cohort?.sku ?? "all")}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="glass-card overflow-x-auto">
        <div className="p-4 border-b border-border">
          <h3 className="panel-header">Promotion Summary</h3>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              {["Promotion", "Baseline Sales", "With Promo", "Lift", "Confidence", "Incremental Units"].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tableRows.map((p) => (
              <tr key={p.id} className={`border-b border-border/50 hover:bg-secondary/30 ${p.id === selected?.id ? "bg-primary/5" : ""}`}>
                <td className="px-4 py-3 text-xs text-foreground font-medium">{p.name}</td>
                <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{p.baseline}</td>
                <td className="px-4 py-3 font-mono text-xs text-foreground">{p.withPromo}</td>
                <td className="px-4 py-3 font-mono text-xs text-primary">{p.lift >= 0 ? "+" : ""}{p.lift}%</td>
                <td className="px-4 py-3 font-mono text-xs text-foreground">{p.confidence}%</td>
                <td className="px-4 py-3 font-mono text-xs text-foreground">{p.incrementalUnits}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PromotionAnalysis;
