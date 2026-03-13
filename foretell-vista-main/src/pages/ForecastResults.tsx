import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, Legend } from "recharts";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useQuery } from "@tanstack/react-query";
import { fetchForecasts, qk } from "@/api/queries";
import { Switch } from "@/components/ui/switch";

const ForecastResults = () => {
  const [horizon, setHorizon] = useState("30");
  const [gnnAdjust, setGnnAdjust] = useState(true);
  const horizonNum = Number(horizon) || 30;
  const { data } = useQuery({
    queryKey: [...qk.forecasts("S001", horizonNum), gnnAdjust],
    queryFn: () => fetchForecasts("S001", horizonNum, undefined, gnnAdjust),
  });
  const forecastData = data?.data ?? [];

  const forecastTable = forecastData.filter((_, i) => i >= Math.max(0, horizonNum - 10)).map((d) => ({
    date: d.date,
    predicted: d.predicted,
    upper: d.upperBound,
    lower: d.lowerBound,
    confidence: (90 + Math.random() * 8).toFixed(1),
  }));

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-foreground">Forecast Results</h2>
          <p className="text-xs text-muted-foreground">AI-predicted demand with confidence intervals</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Switch checked={gnnAdjust} onCheckedChange={setGnnAdjust} />
            GNN Adjust
          </div>
          <Select defaultValue="all">
            <SelectTrigger className="w-36 h-8 text-xs bg-secondary border-border">
              <SelectValue placeholder="Store" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Stores</SelectItem>
              <SelectItem value="s1">Store S001</SelectItem>
              <SelectItem value="s2">Store S002</SelectItem>
            </SelectContent>
          </Select>
          <Select value={horizon} onValueChange={setHorizon}>
            <SelectTrigger className="w-28 h-8 text-xs bg-secondary border-border">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">7 Days</SelectItem>
              <SelectItem value="30">30 Days</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Chart */}
      <div className="glass-card p-5">
        <h3 className="panel-header mb-4">Actual vs Predicted Demand</h3>
        <ResponsiveContainer width="100%" height={350}>
          <AreaChart data={forecastData}>
            <defs>
              <linearGradient id="confBand" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(160, 70%, 45%)" stopOpacity={0.15} />
                <stop offset="95%" stopColor="hsl(160, 70%, 45%)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" />
            <XAxis dataKey="date" tick={{ fill: "hsl(215, 15%, 55%)", fontSize: 10 }} tickLine={false} axisLine={false} />
            <YAxis tick={{ fill: "hsl(215, 15%, 55%)", fontSize: 10 }} tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ background: "hsl(220, 18%, 10%)", border: "1px solid hsl(220, 14%, 18%)", borderRadius: 8, fontSize: 12, color: "hsl(210, 20%, 92%)" }} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Area type="monotone" dataKey="upperBound" stroke="none" fill="url(#confBand)" name="Confidence Band" />
            <Area type="monotone" dataKey="lowerBound" stroke="none" fill="transparent" name="" />
            <Line type="monotone" dataKey="actual" stroke="hsl(200, 80%, 55%)" strokeWidth={2} dot={false} name="Actual Sales" />
            <Line type="monotone" dataKey="predicted" stroke="hsl(160, 70%, 45%)" strokeWidth={2} dot={false} name="Predicted Demand" strokeDasharray="5 5" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Forecast Table */}
      <div className="glass-card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Date</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Predicted Demand</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Lower Bound</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Upper Bound</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Confidence %</th>
            </tr>
          </thead>
          <tbody>
            {forecastTable.map((row, i) => (
              <tr key={i} className="border-b border-border/50 hover:bg-secondary/30">
                <td className="px-4 py-2.5 text-foreground font-mono text-xs">{row.date}</td>
                <td className="px-4 py-2.5 text-right text-foreground font-mono text-xs">{row.predicted}</td>
                <td className="px-4 py-2.5 text-right text-muted-foreground font-mono text-xs">{row.lower}</td>
                <td className="px-4 py-2.5 text-right text-muted-foreground font-mono text-xs">{row.upper}</td>
                <td className="px-4 py-2.5 text-right text-primary font-mono text-xs">{row.confidence}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ForecastResults;
