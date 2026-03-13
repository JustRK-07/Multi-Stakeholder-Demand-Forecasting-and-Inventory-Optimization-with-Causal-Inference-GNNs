import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { useQuery } from "@tanstack/react-query";
import { fetchCausalFactors, qk } from "@/api/queries";

export function CausalPanel() {
  const { data } = useQuery({ queryKey: qk.causalFactors, queryFn: fetchCausalFactors });
  const causalFactors = data?.data ?? [];

  return (
    <div id="causal" className="glass-card p-5">
      <div className="mb-4">
        <h2 className="panel-header">Causal Impact Analysis</h2>
        <p className="text-xs text-muted-foreground mt-1">Factor contributions to demand changes</p>
      </div>
      <div className="h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={causalFactors} layout="vertical" margin={{ top: 5, right: 20, left: 80, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 10, fill: "hsl(215, 15%, 55%)" }} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} />
            <YAxis type="category" dataKey="factor" tick={{ fontSize: 11, fill: "hsl(210, 20%, 80%)" }} tickLine={false} axisLine={false} width={80} />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(220, 18%, 10%)",
                border: "1px solid hsl(220, 14%, 18%)",
                borderRadius: "8px",
                fontSize: "12px",
                color: "hsl(210, 20%, 92%)",
              }}
              formatter={(value: number) => [`${value}%`, "Impact"]}
            />
            <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
              {causalFactors.map((entry, i) => (
                <Cell key={i} fill={entry.direction === "positive" ? "hsl(160, 70%, 45%)" : "hsl(0, 72%, 55%)"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
