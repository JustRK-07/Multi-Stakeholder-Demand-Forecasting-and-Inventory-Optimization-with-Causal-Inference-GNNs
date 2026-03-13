import { TrendingUp, TrendingDown } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchKpis, qk } from "@/api/queries";

export function KPIPanel() {
  const { data: kpiData = [], isLoading } = useQuery({ queryKey: qk.kpis, queryFn: fetchKpis });

  return (
    <div id="overview" className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {isLoading && kpiData.length === 0 ? (
        Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="glass-card p-4 animate-slide-up">
            <p className="data-label mb-1">Loading…</p>
            <p className="kpi-value text-foreground">—</p>
            <div className="flex items-center gap-1 mt-2 text-xs font-medium text-muted-foreground">
              <span>—</span>
            </div>
          </div>
        ))
      ) : (
        kpiData.map((kpi) => {
        const isPositive = kpi.trend === "up";
        return (
          <div key={kpi.title} className="glass-card p-4 animate-slide-up">
            <p className="data-label mb-1">{kpi.title}</p>
            <p className="kpi-value text-foreground">{kpi.value}</p>
            <div className={`flex items-center gap-1 mt-2 text-xs font-medium ${isPositive ? "text-primary" : "text-destructive"}`}>
              {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              <span>{Math.abs(kpi.change)}%</span>
            </div>
          </div>
        );
      })
      )}
    </div>
  );
}
