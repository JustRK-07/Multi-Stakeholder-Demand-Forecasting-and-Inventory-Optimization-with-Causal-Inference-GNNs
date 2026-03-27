import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart,
} from "recharts";
import { useQuery } from "@tanstack/react-query";
import { fetchForecasts, fetchProducts, fetchStores, qk } from "@/api/queries";
import { Switch } from "@/components/ui/switch";
import { useEffect, useMemo, useState } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export function ForecastPanel() {
  const [gnnAdjust, setGnnAdjust] = useState(true);
  const [storeId, setStoreId] = useState("");
  const [productId, setProductId] = useState("");
  const { data: stores } = useQuery({ queryKey: qk.stores, queryFn: fetchStores });
  const { data: products } = useQuery({
    queryKey: qk.products(storeId),
    queryFn: () => fetchProducts(storeId || undefined),
  });

  useEffect(() => {
    if (!storeId && stores?.data?.length) {
      setStoreId(stores.data[0].code || "S001");
    }
  }, [storeId, stores]);

  const productOptions = useMemo(() => {
    const items = products?.items ?? [];
    return items.filter((item) => !storeId || item.store_id === storeId).slice(0, 20);
  }, [products, storeId]);

  useEffect(() => {
    if ((!productId || !productOptions.some((item) => item.product_id === productId)) && productOptions.length) {
      setProductId(productOptions[0].product_id);
    }
  }, [productId, productOptions]);

  const { data } = useQuery({
    queryKey: [...qk.forecasts(storeId || "S001", 30), productId || "default", gnnAdjust],
    queryFn: () => fetchForecasts(storeId || "S001", 30, productId || undefined, gnnAdjust),
    enabled: Boolean(storeId || stores?.data?.length),
  });

  const forecastData = [
    ...(data?.actuals ?? []).map((item) => ({
      date: item.date,
      actual: item.actual,
      predicted: undefined,
      upperBound: undefined,
      lowerBound: undefined,
    })),
    ...((data?.data ?? []).map((point) => ({
      ...point,
      actual: undefined,
    }))),
  ];
  const metrics = data?.metrics;

  return (
    <div id="forecast" className="glass-card p-5">
      <div className="flex flex-col gap-3 mb-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="panel-header">Demand Forecasting</h2>
          <p className="text-xs text-muted-foreground mt-1">30-day forecast with confidence intervals</p>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <Select value={storeId} onValueChange={setStoreId}>
            <SelectTrigger className="w-32 h-8 text-xs bg-secondary border-border">
              <SelectValue placeholder="Store" />
            </SelectTrigger>
            <SelectContent>
              {(stores?.data ?? []).map((store) => (
                <SelectItem key={store.id} value={store.code}>{store.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={productId} onValueChange={setProductId}>
            <SelectTrigger className="w-36 h-8 text-xs bg-secondary border-border">
              <SelectValue placeholder="Product" />
            </SelectTrigger>
            <SelectContent>
              {productOptions.map((product) => (
                <SelectItem key={product.product_id} value={product.product_id}>{product.product_id}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Switch checked={gnnAdjust} onCheckedChange={setGnnAdjust} />
            GNN Adjust
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
          <p className="text-sm font-mono font-semibold text-foreground">{metrics ? metrics.mae.toFixed(1) : "—"}</p>
        </div>
        <div>
          <p className="data-label">RMSE</p>
          <p className="text-sm font-mono font-semibold text-foreground">{metrics ? metrics.rmse.toFixed(1) : "—"}</p>
        </div>
        <div>
          <p className="data-label">MAPE</p>
          <p className="text-sm font-mono font-semibold text-foreground">{metrics ? `${metrics.mape.toFixed(1)}%` : "—"}</p>
        </div>
      </div>
    </div>
  );
}
