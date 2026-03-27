import { useQuery } from "@tanstack/react-query";
import { Activity, AlertTriangle, Clock3, Database } from "lucide-react";
import { fetchDriftReport, fetchMonitoringStatus, qk } from "@/api/queries";

const severityTone: Record<string, string> = {
  low: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10",
  medium: "text-amber-400 border-amber-500/30 bg-amber-500/10",
  high: "text-orange-400 border-orange-500/30 bg-orange-500/10",
  critical: "text-red-400 border-red-500/30 bg-red-500/10",
};

export function MonitoringPanel() {
  const { data: status } = useQuery({ queryKey: qk.monitoringStatus, queryFn: fetchMonitoringStatus });
  const { data: drift } = useQuery({ queryKey: qk.driftReport, queryFn: fetchDriftReport });

  const alerts = status?.alerts ?? [];
  const topFeatures = drift?.features?.slice(0, 3) ?? [];
  const statusTone = severityTone[status?.driftSeverity ?? "low"] ?? severityTone.low;

  return (
    <div className="glass-card p-5">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <h2 className="panel-header">Model Monitoring</h2>
          <p className="text-xs text-muted-foreground mt-1">Freshness, drift, and operational warnings</p>
        </div>
        <div className={`rounded-full border px-3 py-1 text-xs font-medium capitalize ${statusTone}`}>
          {status?.status ?? "healthy"} / drift {status?.driftSeverity ?? "low"}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
        <div className="rounded-xl border border-border bg-secondary/30 p-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
            <Clock3 className="h-4 w-4" />
            Model age
          </div>
          <div className="text-xl font-semibold text-foreground">{status?.daysSinceTraining ?? 0}d</div>
          <p className="text-xs text-muted-foreground mt-1">{status?.trainedAt ? new Date(status.trainedAt).toLocaleString() : "Unavailable"}</p>
        </div>
        <div className="rounded-xl border border-border bg-secondary/30 p-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
            <Activity className="h-4 w-4" />
            Validation MAPE
          </div>
          <div className="text-xl font-semibold text-foreground">{status?.metrics?.mape?.toFixed(1) ?? "0.0"}%</div>
          <p className="text-xs text-muted-foreground mt-1">{status?.storeCount ?? 0} stores, {status?.productCount ?? 0} products</p>
        </div>
        <div className="rounded-xl border border-border bg-secondary/30 p-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
            <Database className="h-4 w-4" />
            Observation window
          </div>
          <div className="text-xl font-semibold text-foreground">{status?.dataSpanDays ?? 0}d</div>
          <p className="text-xs text-muted-foreground mt-1">Last data point: {status?.observationEndDate ?? "Unavailable"}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-xl border border-border bg-secondary/20 p-4">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="h-4 w-4 text-amber-400" />
            <p className="text-sm font-medium text-foreground">Active alerts</p>
          </div>
          <div className="space-y-2">
            {alerts.length === 0 ? (
              <p className="text-xs text-muted-foreground">No active model health alerts.</p>
            ) : (
              alerts.slice(0, 4).map((alert) => (
                <div key={`${alert.title}-${alert.message}`} className={`rounded-lg border px-3 py-2 text-xs ${severityTone[alert.severity] ?? severityTone.low}`}>
                  <p className="font-medium">{alert.title}</p>
                  <p className="mt-1 opacity-90">{alert.message}</p>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-secondary/20 p-4">
          <p className="text-sm font-medium text-foreground mb-3">Top drift features</p>
          <div className="space-y-2">
            {topFeatures.length === 0 ? (
              <p className="text-xs text-muted-foreground">No drift report available.</p>
            ) : (
              topFeatures.map((feature) => (
                <div key={feature.feature} className="rounded-lg border border-border bg-background/30 px-3 py-2">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm text-foreground">{feature.feature}</p>
                    <span className={`rounded-full border px-2 py-0.5 text-[10px] uppercase ${severityTone[feature.severity] ?? severityTone.low}`}>
                      {feature.severity}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Shift {feature.meanShiftPct}% • PSI {feature.psi}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
