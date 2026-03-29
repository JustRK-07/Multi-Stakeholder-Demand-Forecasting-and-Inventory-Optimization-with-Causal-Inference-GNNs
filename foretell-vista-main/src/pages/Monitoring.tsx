import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, History, ShieldAlert } from "lucide-react";
import { MonitoringPanel } from "@/components/Monitoring/MonitoringPanel";
import { useAuth } from "@/components/AuthProvider";
import { Button } from "@/components/ui/button";
import { fetchAuditLog, fetchDriftHistory, qk, runDriftScan } from "@/api/queries";
import { useToast } from "@/hooks/use-toast";

const severityTone: Record<string, string> = {
  low: "text-emerald-400",
  medium: "text-amber-400",
  high: "text-orange-400",
  critical: "text-red-400",
};

const Monitoring = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { data: history } = useQuery({ queryKey: qk.driftHistory, queryFn: () => fetchDriftHistory(20) });
  const { data: audit } = useQuery({ queryKey: qk.auditLog, queryFn: () => fetchAuditLog(20), enabled: user?.role === "admin" });
  const scanMutation = useMutation({
    mutationFn: runDriftScan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qk.monitoringStatus });
      queryClient.invalidateQueries({ queryKey: qk.driftReport });
      queryClient.invalidateQueries({ queryKey: qk.driftHistory });
      toast({ title: "Drift scan recorded" });
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-foreground">Monitoring</h2>
          <p className="text-xs text-muted-foreground">Historical drift scans, alerts, and platform audit activity.</p>
        </div>
        <Button onClick={() => scanMutation.mutate()} disabled={scanMutation.isPending}>
          {scanMutation.isPending ? "Scanning..." : "Run Drift Scan"}
        </Button>
      </div>

      <MonitoringPanel />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <History className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">Drift History</h3>
          </div>
          <div className="space-y-3">
            {history?.items?.length ? history.items.map((entry) => (
              <div key={entry.scannedAt} className="rounded-lg border border-border bg-secondary/20 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm text-foreground">{new Date(entry.scannedAt).toLocaleString()}</p>
                  <span className={`text-xs font-medium uppercase ${severityTone[entry.severity] ?? ""}`}>{entry.severity}</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {entry.featureCount} features scanned · {entry.observationCount} observations
                </p>
                {entry.target ? (
                  <p className="text-xs text-muted-foreground mt-1">
                    Target drift: {entry.target.meanShiftPct}% shift, PSI {entry.target.psi}
                  </p>
                ) : null}
              </div>
            )) : (
              <p className="text-xs text-muted-foreground">No recorded scans yet.</p>
            )}
          </div>
        </div>

        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <ShieldAlert className="h-4 w-4 text-accent" />
            <h3 className="text-sm font-semibold text-foreground">Audit Log</h3>
          </div>
          <div className="space-y-3">
            {user?.role !== "admin" ? (
              <p className="text-xs text-muted-foreground">Audit history is only available to admin users.</p>
            ) : audit?.items?.length ? audit.items.map((event) => (
              <div key={`${event.timestamp}-${event.action}-${event.target ?? ""}`} className="rounded-lg border border-border bg-secondary/20 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm text-foreground">{event.action}</p>
                  <span className="text-[11px] text-muted-foreground">{new Date(event.timestamp).toLocaleString()}</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Actor: {event.actor || "system"} {event.target ? `· Target: ${event.target}` : ""}
                </p>
              </div>
            )) : (
              <p className="text-xs text-muted-foreground">No audit events recorded.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Monitoring;
