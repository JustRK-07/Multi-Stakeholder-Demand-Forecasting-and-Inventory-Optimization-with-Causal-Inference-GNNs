import { Progress } from "@/components/ui/progress";
import { useQuery } from "@tanstack/react-query";
import { fetchInventory, qk } from "@/api/queries";

const riskColors: Record<string, string> = {
  low: "text-primary",
  medium: "text-warning",
  high: "text-chart-4",
  critical: "text-destructive",
};

const riskDotClass: Record<string, string> = {
  low: "status-dot-success",
  medium: "status-dot-warning",
  high: "status-dot-warning",
  critical: "status-dot-danger",
};

export function InventoryPanel() {
  const { data } = useQuery({ queryKey: qk.inventory, queryFn: fetchInventory });
  const inventoryData = data?.items ?? [];

  return (
    <div id="inventory" className="glass-card p-5">
      <div className="mb-4">
        <h2 className="panel-header">Inventory Status</h2>
        <p className="text-xs text-muted-foreground mt-1">Real-time stock levels and risk assessment</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-2 data-label font-medium">SKU</th>
              <th className="text-left py-2 data-label font-medium">Product</th>
              <th className="text-left py-2 data-label font-medium">Stock Level</th>
              <th className="text-right py-2 data-label font-medium">Days Supply</th>
              <th className="text-right py-2 data-label font-medium">Risk</th>
            </tr>
          </thead>
          <tbody>
            {inventoryData.map((item) => {
              const fillPercent = (item.stock / item.capacity) * 100;
              return (
                <tr key={item.sku} className="border-b border-border/50 hover:bg-secondary/30 transition-colors">
                  <td className="py-3 font-mono text-xs text-muted-foreground">{item.sku}</td>
                  <td className="py-3 text-foreground">{item.name}</td>
                  <td className="py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-24">
                        <Progress value={fillPercent} className="h-1.5" />
                      </div>
                      <span className="font-mono text-xs text-muted-foreground">
                        {item.stock}/{item.capacity}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 text-right font-mono text-xs">{item.daysOfSupply}d</td>
                  <td className="py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <span className={riskDotClass[item.risk]} />
                      <span className={`text-xs font-medium capitalize ${riskColors[item.risk]}`}>
                        {item.risk}
                      </span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
