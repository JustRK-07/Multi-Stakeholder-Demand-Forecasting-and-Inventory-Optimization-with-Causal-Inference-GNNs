import { Package, AlertTriangle, TrendingDown, ShieldCheck } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchInventory, fetchOrderRecommendations, qk } from "@/api/queries";

const riskCards = [
  // counts computed at runtime
  { label: "Overstock Risk", icon: TrendingDown, color: "text-warning" },
  { label: "Stockout Risk", icon: AlertTriangle, color: "text-destructive" },
  { label: "Recommended Orders", icon: Package, color: "text-accent" },
  { label: "Safe Items", icon: ShieldCheck, color: "text-primary" },
];

const riskColor = (risk: string) => {
  switch (risk) {
    case "critical": return "bg-destructive/20 text-destructive";
    case "high": return "bg-destructive/15 text-destructive";
    case "medium": return "bg-warning/15 text-warning";
    default: return "bg-primary/15 text-primary";
  }
};

const InventoryRecommendations = () => {
  const { data: inv } = useQuery({ queryKey: qk.inventory, queryFn: fetchInventory });
  const { data: recs } = useQuery({ queryKey: qk.orderRecs, queryFn: fetchOrderRecommendations });

  const inventoryData = inv?.items ?? [];
  const rlRecommendations = recs?.recommendations ?? [];

  const counts = {
    overstock: inventoryData.filter((d) => d.daysOfSupply > 25).length,
    stockout: inventoryData.filter((d) => d.risk === "critical" || d.risk === "high").length,
    recommended: rlRecommendations.length,
    safe: inventoryData.filter((d) => d.risk === "low").length,
  };

  const riskCardsWithCounts = [
    { ...riskCards[0], count: counts.overstock },
    { ...riskCards[1], count: counts.stockout },
    { ...riskCards[2], count: counts.recommended },
    { ...riskCards[3], count: counts.safe },
  ];

  return (
    <div className="space-y-6">
    <div>
      <h2 className="text-lg font-bold text-foreground">Inventory Recommendations</h2>
      <p className="text-xs text-muted-foreground">AI-powered ordering suggestions and risk monitoring</p>
    </div>

    {/* Risk Cards */}
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {riskCardsWithCounts.map((c) => (
        <div key={c.label} className="glass-card p-5">
          <div className="flex items-center gap-2 mb-2">
            <c.icon className={`h-4 w-4 ${c.color}`} />
            <span className="text-xs text-muted-foreground">{c.label}</span>
          </div>
          <p className="kpi-value text-foreground">{c.count}</p>
        </div>
      ))}
    </div>

    {/* Recommendations Table */}
    <div className="glass-card overflow-x-auto">
      <div className="p-4 border-b border-border">
        <h3 className="panel-header">Recommended Orders</h3>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            {["SKU", "Action", "Confidence", "Expected Saving", "Urgency"].map((h) => (
              <th key={h} className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rlRecommendations.map((r) => (
            <tr key={r.sku} className="border-b border-border/50 hover:bg-secondary/30">
              <td className="px-4 py-3 font-mono text-xs text-foreground">{r.sku}</td>
              <td className="px-4 py-3 text-xs text-foreground">{r.action}</td>
              <td className="px-4 py-3 text-xs text-primary font-mono">{r.confidence}%</td>
              <td className="px-4 py-3 text-xs text-foreground font-mono">{r.expectedSaving}</td>
              <td className="px-4 py-3">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${riskColor(r.urgency)}`}>{r.urgency}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>

    {/* Inventory Status Table */}
    <div className="glass-card overflow-x-auto">
      <div className="p-4 border-b border-border">
        <h3 className="panel-header">Inventory Status</h3>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            {["SKU", "Product", "Current Stock", "Capacity", "Days of Supply", "Risk"].map((h) => (
              <th key={h} className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {inventoryData.map((item) => (
            <tr key={item.sku} className="border-b border-border/50 hover:bg-secondary/30">
              <td className="px-4 py-3 font-mono text-xs text-foreground">{item.sku}</td>
              <td className="px-4 py-3 text-xs text-foreground">{item.name}</td>
              <td className="px-4 py-3 text-xs font-mono text-foreground">{item.stock.toLocaleString()}</td>
              <td className="px-4 py-3 text-xs font-mono text-muted-foreground">{item.capacity.toLocaleString()}</td>
              <td className="px-4 py-3 text-xs font-mono text-foreground">{item.daysOfSupply}d</td>
              <td className="px-4 py-3">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${riskColor(item.risk)}`}>{item.risk}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
  );
};

export default InventoryRecommendations;
