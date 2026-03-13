import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, Legend,
} from "recharts";
import { useQuery } from "@tanstack/react-query";
import { fetchForecasts, qk } from "@/api/queries";
import { Switch } from "@/components/ui/switch";
import { useState } from "react";

export function ForecastPanel() {
  const [gnnAdjust, setGnnAdjust] = useState(true);
  const { data } = useQuery({
    queryKey: [...qk.forecasts("S001", 30), gnnAdjust],
    queryFn: () => fetchForecasts("S001", 30, undefined, gnnAdjust),
  });
  const forecastData = data?.data ?? [];

  return (
    <div id="forecast" className="glass-card p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="panel-header">Demand Forecasting</h2>
          <p className="text-xs text-muted-foreground mt-1">30-day forecast with confidence intervals</p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Switch checked={gnnAdjust} onCheckedChange={setGnnAdjust} />
            GNN Adjust
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-primary rounded" />
            <span className="text-muted-foreground">Predicted</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-accent rounded" />
            <span className="text-muted-foreground">Actual</span>
          </div>
        </div>
      </div>
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={forecastData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
            <defs>
              <linearGradient id="confidenceFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(160, 70%, 45%)" stopOpacity={0.15} />
                <stop offset="95%" stopColor="hsl(160, 70%, 45%)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: "hsl(215, 15%, 55%)" }} tickLine={false} axisLine={false} />
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
            <Area type="monotone" dataKey="upperBound" stroke="none" fill="url(#confidenceFill)" />
            <Area type="monotone" dataKey="lowerBound" stroke="none" fill="transparent" />
            <Line type="monotone" dataKey="predicted" stroke="hsl(160, 70%, 45%)" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="actual" stroke="hsl(200, 80%, 55%)" strokeWidth={2} dot={false} strokeDasharray="4 2" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-border">
        <div>
          <p className="data-label">MAE</p>
          <p className="text-sm font-mono font-semibold text-foreground">24.3</p>
        </div>
        <div>
          <p className="data-label">RMSE</p>
          <p className="text-sm font-mono font-semibold text-foreground">31.7</p>
        </div>
        <div>
          <p className="data-label">MAPE</p>
          <p className="text-sm font-mono font-semibold text-foreground">5.8%</p>
        </div>
      </div>
    </div>
  );
}
