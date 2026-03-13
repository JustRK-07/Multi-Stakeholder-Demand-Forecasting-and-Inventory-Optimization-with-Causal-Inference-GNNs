import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Brain } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchExplainabilityFeatures, qk } from "@/api/queries";

export function ExplainabilityPanel() {
  const { data } = useQuery({ queryKey: qk.explainability, queryFn: fetchExplainabilityFeatures });
  const explainabilityFeatures = data?.data ?? [];

  return (
    <div id="explainability" className="glass-card p-5">
      <div className="mb-4">
        <h2 className="panel-header">Model Explainability</h2>
        <p className="text-xs text-muted-foreground mt-1">SHAP values and feature importance</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <p className="data-label mb-3">Feature Importance</p>
          <div className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={explainabilityFeatures} layout="vertical" margin={{ top: 0, right: 10, left: 70, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10, fill: "hsl(215, 15%, 55%)" }} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="feature" tick={{ fontSize: 10, fill: "hsl(210, 20%, 80%)" }} tickLine={false} axisLine={false} width={70} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(220, 18%, 10%)",
                    border: "1px solid hsl(220, 14%, 18%)",
                    borderRadius: "8px",
                    fontSize: "12px",
                    color: "hsl(210, 20%, 92%)",
                  }}
                />
                <Bar dataKey="importance" fill="hsl(200, 80%, 55%)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div>
          <p className="data-label mb-3">SHAP Values</p>
          <div className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={explainabilityFeatures} layout="vertical" margin={{ top: 0, right: 10, left: 70, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10, fill: "hsl(215, 15%, 55%)" }} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="feature" tick={{ fontSize: 10, fill: "hsl(210, 20%, 80%)" }} tickLine={false} axisLine={false} width={70} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(220, 18%, 10%)",
                    border: "1px solid hsl(220, 14%, 18%)",
                    borderRadius: "8px",
                    fontSize: "12px",
                    color: "hsl(210, 20%, 92%)",
                  }}
                />
                <Bar dataKey="shap" radius={[0, 4, 4, 0]}>
                  {explainabilityFeatures.map((entry, i) => (
                    <Cell key={i} fill={entry.shap >= 0 ? "hsl(160, 70%, 45%)" : "hsl(0, 72%, 55%)"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      <div className="mt-4 p-3 rounded-lg bg-secondary/40 border border-border">
        <div className="flex items-start gap-2">
          <Brain className="h-4 w-4 text-accent mt-0.5 shrink-0" />
          <p className="text-xs text-secondary-foreground leading-relaxed">
            <span className="font-medium text-foreground">AI Insight:</span> High demand predicted due to: <span className="text-primary">Weekend (+12%)</span>, <span className="text-primary">Rain forecast (+8%)</span>, <span className="text-primary">Promo X (+15%)</span>. Consider increasing stock for SKU-002 and SKU-004.
          </p>
        </div>
      </div>
    </div>
  );
}
