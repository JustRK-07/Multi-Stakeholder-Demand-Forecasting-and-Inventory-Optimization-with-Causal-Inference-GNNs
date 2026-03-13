import { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from "recharts";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Megaphone, TrendingUp, Target } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchPromotionImpact, qk } from "@/api/queries";

const promotions = [
  { id: "festival", name: "Festival Discount", lift: 18, confidence: 91, baseline: 450, withPromo: 531 },
  { id: "bogo", name: "Buy 1 Get 1", lift: 24, confidence: 88, baseline: 380, withPromo: 471 },
  { id: "seasonal", name: "Seasonal Offer", lift: 11, confidence: 94, baseline: 520, withPromo: 577 },
  { id: "flash", name: "Flash Sale", lift: 32, confidence: 82, baseline: 290, withPromo: 383 },
];

const comparisonData = (promo: typeof promotions[0]) => [
  { name: "Without Promo", sales: promo.baseline },
  { name: "With Promo", sales: promo.withPromo },
];

const PromotionAnalysis = () => {
  const [selectedId, setSelectedId] = useState(promotions[0].id);
  const fallback = promotions.find((p) => p.id === selectedId) ?? promotions[0];
  const { data } = useQuery({
    queryKey: qk.promotionImpact(selectedId),
    queryFn: () => fetchPromotionImpact(selectedId),
  });
  const selected = data?.promotion ?? fallback;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-foreground">Promotion Impact Analysis</h2>
          <p className="text-xs text-muted-foreground">Causal inference — measure true promotion effectiveness</p>
        </div>
        <Select value={selectedId} onValueChange={setSelectedId}>
          <SelectTrigger className="w-44 h-8 text-xs bg-secondary border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {promotions.map((p) => (
              <SelectItem key={p.id} value={p.id} className="text-xs">{p.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Result Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="h-4 w-4 text-primary" />
            <span className="text-xs text-muted-foreground">Estimated Sales Lift</span>
          </div>
          <p className="kpi-value text-primary">+{selected.lift}%</p>
        </div>
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-2">
            <Target className="h-4 w-4 text-accent" />
            <span className="text-xs text-muted-foreground">Confidence</span>
          </div>
          <p className="kpi-value text-foreground">{selected.confidence}%</p>
        </div>
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-2">
            <Megaphone className="h-4 w-4 text-warning" />
            <span className="text-xs text-muted-foreground">Incremental Units</span>
          </div>
          <p className="kpi-value text-foreground">+{selected.withPromo - selected.baseline}</p>
        </div>
      </div>

      {/* Comparison Chart */}
      <div className="glass-card p-5">
        <h3 className="panel-header mb-4">Sales With vs Without Promotion</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={comparisonData(selected)} barSize={60}>
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

      {/* All Promotions Table */}
      <div className="glass-card overflow-x-auto">
        <div className="p-4 border-b border-border">
          <h3 className="panel-header">All Promotions Summary</h3>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              {["Promotion", "Baseline Sales", "With Promo", "Lift", "Confidence"].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {promotions.map((p) => (
              <tr key={p.id} className={`border-b border-border/50 hover:bg-secondary/30 ${p.id === selected.id ? "bg-primary/5" : ""}`}>
                <td className="px-4 py-3 text-xs text-foreground font-medium">{p.name}</td>
                <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{p.baseline}</td>
                <td className="px-4 py-3 font-mono text-xs text-foreground">{p.withPromo}</td>
                <td className="px-4 py-3 font-mono text-xs text-primary">+{p.lift}%</td>
                <td className="px-4 py-3 font-mono text-xs text-foreground">{p.confidence}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PromotionAnalysis;
