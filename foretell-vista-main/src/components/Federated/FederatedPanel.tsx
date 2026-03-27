import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Shield } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchFederatedRounds, qk } from "@/api/queries";

export function FederatedPanel() {
  const { data } = useQuery({ queryKey: qk.federatedRounds, queryFn: fetchFederatedRounds });
  const federatedRounds = data?.data ?? [];
  const latest = federatedRounds[federatedRounds.length - 1];
  const totalRounds = federatedRounds.length || 1;

  return (
    <div id="federated" className="glass-card p-5">
      <div className="mb-4">
        <h2 className="panel-header">Federated Learning</h2>
        <p className="text-xs text-muted-foreground mt-1">Privacy-preserving distributed training</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={federatedRounds} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" />
              <XAxis dataKey="round" tick={{ fontSize: 10, fill: "hsl(215, 15%, 55%)" }} tickLine={false} axisLine={false} label={{ value: "Round", position: "bottom", fontSize: 10, fill: "hsl(215, 15%, 55%)" }} />
              <YAxis tick={{ fontSize: 10, fill: "hsl(215, 15%, 55%)" }} tickLine={false} axisLine={false} domain={[70, 100]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(220, 18%, 10%)",
                  border: "1px solid hsl(220, 14%, 18%)",
                  borderRadius: "8px",
                  fontSize: "12px",
                  color: "hsl(210, 20%, 92%)",
                }}
              />
              <Line type="monotone" dataKey="globalAccuracy" stroke="hsl(160, 70%, 45%)" strokeWidth={2} dot={{ r: 3, fill: "hsl(160, 70%, 45%)" }} name="Global" />
              <Line type="monotone" dataKey="localAccuracy" stroke="hsl(200, 80%, 55%)" strokeWidth={2} dot={{ r: 3, fill: "hsl(200, 80%, 55%)" }} name="Local" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="space-y-4">
          <div className="p-3 rounded-lg bg-secondary/40 border border-border">
            <p className="data-label">Global Accuracy</p>
            <p className="kpi-value text-primary text-xl">{latest ? `${latest.globalAccuracy}%` : "—"}</p>
          </div>
          <div className="p-3 rounded-lg bg-secondary/40 border border-border">
            <p className="data-label">Rounds Completed</p>
            <p className="kpi-value text-foreground text-xl">{latest ? `${latest.round}/${totalRounds}` : "—"}</p>
            <div className="w-full h-1.5 bg-muted rounded-full mt-2 overflow-hidden">
              <div className="h-full bg-accent rounded-full" style={{ width: `${latest ? (latest.round / totalRounds) * 100 : 0}%` }} />
            </div>
          </div>
          <div className="p-3 rounded-lg bg-secondary/40 border border-border">
            <div className="flex items-center gap-1.5 mb-1">
              <Shield className="h-3 w-3 text-primary" />
              <p className="data-label">Privacy Budget (ε)</p>
            </div>
            <p className="kpi-value text-warning text-xl">{latest ? latest.privacyBudget.toFixed(2) : "—"}</p>
            <p className="text-xs text-muted-foreground mt-2">{latest ? `${latest.participants} store nodes in latest round` : "Waiting for rounds"}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
