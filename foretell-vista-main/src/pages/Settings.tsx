import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { User, Bell, Brain, Database, Trash2 } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchDatasets, fetchSettings, qk, updateSettings } from "@/api/queries";

const Settings = () => {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { data: settings } = useQuery({ queryKey: qk.settings, queryFn: fetchSettings });
  const { data: datasets } = useQuery({ queryKey: qk.datasets, queryFn: fetchDatasets });
  const [notifications, setNotifications] = useState(true);
  const [horizon, setHorizon] = useState("30");
  const [holdingCost, setHoldingCost] = useState("0.15");
  const [stockoutCost, setStockoutCost] = useState("1.5");
  const saveMutation = useMutation({
    mutationFn: updateSettings,
    onSuccess: (res) => {
      queryClient.setQueryData(qk.settings, res.settings);
      toast({ title: "Settings updated" });
    },
  });

  useEffect(() => {
    if (settings) {
      setNotifications(settings.notifications);
      setHorizon(String(settings.forecastHorizon));
      setHoldingCost(String(settings.holdingCost));
      setStockoutCost(String(settings.stockoutCost));
    }
  }, [settings]);

  const handleSave = () => {
    saveMutation.mutate({
      forecastHorizon: Number(horizon) || 30,
      holdingCost: Number(holdingCost) || 0.15,
      stockoutCost: Number(stockoutCost) || 1.5,
      notifications,
    });
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="text-lg font-bold text-foreground">Settings</h2>
        <p className="text-xs text-muted-foreground">Manage your account, models, and data</p>
      </div>

      {/* User Settings */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <User className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold text-foreground">User Settings</h3>
        </div>
        <div className="space-y-2">
          <Label className="text-foreground text-sm">Email</Label>
          <Input defaultValue="analyst@company.com" className="bg-secondary border-border text-foreground" disabled />
        </div>
        <div className="space-y-2">
          <Label className="text-foreground text-sm">New Password</Label>
          <Input type="password" placeholder="••••••••" className="bg-secondary border-border text-foreground" />
        </div>
        <Button size="sm" className="bg-primary text-primary-foreground hover:bg-primary/90" onClick={() => toast({ title: "Password updated" })}>
          Update Password
        </Button>
      </div>

      {/* Notifications */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Bell className="h-4 w-4 text-accent" />
          <h3 className="text-sm font-semibold text-foreground">Notifications</h3>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-foreground">Stockout alerts</p>
            <p className="text-xs text-muted-foreground">Get notified when items reach critical stock levels</p>
          </div>
          <Switch checked={notifications} onCheckedChange={setNotifications} />
        </div>
      </div>

      {/* Model Settings */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Brain className="h-4 w-4 text-chart-3" />
          <h3 className="text-sm font-semibold text-foreground">Model Settings</h3>
        </div>
        <div className="space-y-2">
          <Label className="text-foreground text-sm">Forecast Horizon</Label>
          <Select value={horizon} onValueChange={setHorizon}>
            <SelectTrigger className="w-40 bg-secondary border-border text-foreground">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">7 Days</SelectItem>
              <SelectItem value="14">14 Days</SelectItem>
              <SelectItem value="30">30 Days</SelectItem>
              <SelectItem value="90">90 Days</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label className="text-foreground text-sm">Holding Cost ($/unit/day)</Label>
          <Input type="number" value={holdingCost} onChange={(e) => setHoldingCost(e.target.value)} className="bg-secondary border-border text-foreground w-40" />
        </div>
        <div className="space-y-2">
          <Label className="text-foreground text-sm">Stockout Cost ($/unit)</Label>
          <Input type="number" value={stockoutCost} onChange={(e) => setStockoutCost(e.target.value)} className="bg-secondary border-border text-foreground w-40" />
        </div>
        <Button size="sm" className="bg-primary text-primary-foreground hover:bg-primary/90" onClick={handleSave} disabled={saveMutation.isPending}>
          {saveMutation.isPending ? "Saving..." : "Save Model Settings"}
        </Button>
      </div>

      {/* Data Management */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Database className="h-4 w-4 text-warning" />
          <h3 className="text-sm font-semibold text-foreground">Data Management</h3>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-foreground">Uploaded Datasets</p>
            <p className="text-xs text-muted-foreground">
              {datasets?.items?.length
                ? `${datasets.items.find((item) => item.datasetId === datasets.activeDatasetId)?.filename ?? datasets.items[0].filename} — ${datasets.items.find((item) => item.datasetId === datasets.activeDatasetId)?.rowCount ?? datasets.items[0].rowCount} rows`
                : "No datasets uploaded yet"}
            </p>
          </div>
          <Button variant="outline" size="sm" className="border-destructive/50 text-destructive hover:bg-destructive/10 gap-1" disabled>
            <Trash2 className="h-3.5 w-3.5" /> Delete
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Settings;
