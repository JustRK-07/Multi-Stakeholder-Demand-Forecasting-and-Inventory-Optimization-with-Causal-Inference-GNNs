import { MapPin } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchStores, qk } from "@/api/queries";

export function StorePanel() {
  const { data } = useQuery({ queryKey: qk.stores, queryFn: fetchStores });
  const storeData = data?.data ?? [];

  return (
    <div id="store" className="glass-card p-5">
      <div className="mb-4">
        <h2 className="panel-header">Store Intelligence</h2>
        <p className="text-xs text-muted-foreground mt-1">Performance metrics across locations</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {storeData.map((store) => (
          <div key={store.id} className="p-4 rounded-lg bg-secondary/40 border border-border hover:border-primary/30 transition-colors">
            <div className="flex items-center gap-2 mb-3">
              <MapPin className="h-4 w-4 text-accent" />
              <span className="text-sm font-medium text-foreground">{store.name}</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="data-label">Daily Demand</p>
                <p className="text-sm font-mono font-semibold text-foreground">{store.demand}</p>
              </div>
              <div>
                <p className="data-label">Performance</p>
                <p className={`text-sm font-mono font-semibold ${store.performance >= 95 ? "text-primary" : store.performance >= 90 ? "text-warning" : "text-destructive"}`}>
                  {store.performance}%
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
