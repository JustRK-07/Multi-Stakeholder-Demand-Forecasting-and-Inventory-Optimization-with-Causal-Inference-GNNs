import { useEffect, useMemo, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, Legend } from "recharts";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useQuery } from "@tanstack/react-query";
import { fetchForecasts, fetchForecastMeta, fetchProducts, fetchStores, qk } from "@/api/queries";
import { Switch } from "@/components/ui/switch";

const ForecastResults = () => {
  const [horizon, setHorizon] = useState("30");
  const [gnnAdjust, setGnnAdjust] = useState(true);
  const [storeId, setStoreId] = useState("");
  const [productId, setProductId] = useState("");
  const horizonNum = Number(horizon) || 30;

  const { data: stores } = useQuery({ queryKey: qk.stores, queryFn: fetchStores });
  const { data: meta } = useQuery({ queryKey: qk.forecastMeta, queryFn: fetchForecastMeta });
  const { data: products } = useQuery({
    queryKey: qk.products(storeId),
    queryFn: () => fetchProducts(storeId || undefined),
  });

  useEffect(() => {
    if (!storeId && stores?.data?.length) {
      setStoreId(stores.data[0].code);
    }
  }, [storeId, stores]);

  const productOptions = useMemo(() => {
    const items = products?.items ?? [];
    return items.filter((item) => !storeId || item.store_id === storeId).slice(0, 50);
  }, [products, storeId]);

  useEffect(() => {
    if ((!productId || !productOptions.some((item) => item.product_id === productId)) && productOptions.length) {
      setProductId(productOptions[0].product_id);
    }
  }, [productId, productOptions]);

  const { data } = useQuery({
    queryKey: [...qk.forecasts(storeId || "S001", horizonNum), productId || "default", gnnAdjust],
    queryFn: () => fetchForecasts(storeId || "S001", horizonNum, productId || undefined, gnnAdjust),
    enabled: Boolean(storeId || stores?.data?.length),
  });

  const forecastFutureData = (data?.data ?? []).map((point) => ({
    ...point,
    actual: undefined,
    confidence: point.upperBound > 0 ? (((point.predicted - point.lowerBound) / Math.max(point.upperBound - point.lowerBound, 1)) * 100).toFixed(1) : "0.0",
  }));
  const forecastData = [
    ...(data?.actuals ?? []).map((item) => ({
      date: item.date,
      actual: item.actual,
      predicted: undefined,
      upperBound: undefined,
      lowerBound: undefined,
      confidence: "0.0",
    })),
    ...forecastFutureData,
  ];

  const forecastTable = forecastFutureData.slice(-10).map((d) => ({
    date: d.date,
    predicted: d.predicted,
    upper: d.upperBound,
    lower: d.lowerBound,
    confidence: d.confidence,
  }));

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-foreground">Forecast Results</h2>
          <p className="text-xs text-muted-foreground">AI-predicted demand with confidence intervals</p>
          <p className="text-xs text-muted-foreground mt-1">
            Model trained: {data?.modelInfo?.trained_at ? new Date(data.modelInfo.trained_at).toLocaleString() : "—"}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Switch checked={gnnAdjust} onCheckedChange={setGnnAdjust} />
            GNN Adjust
          </div>
          <Select value={storeId} onValueChange={setStoreId}>
            <SelectTrigger className="w-36 h-8 text-xs bg-secondary border-border">
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
          <Select value={horizon} onValueChange={setHorizon}>
            <SelectTrigger className="w-28 h-8 text-xs bg-secondary border-border">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">7 Days</SelectItem>
              <SelectItem value="14">14 Days</SelectItem>
              <SelectItem value="30">30 Days</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card p-4">
          <p className="data-label">MAE</p>
          <p className="kpi-value text-foreground text-xl">{data?.metrics ? data.metrics.mae.toFixed(1) : "—"}</p>
        </div>
        <div className="glass-card p-4">
          <p className="data-label">RMSE</p>
          <p className="kpi-value text-foreground text-xl">{data?.metrics ? data.metrics.rmse.toFixed(1) : "—"}</p>
        </div>
        <div className="glass-card p-4">
          <p className="data-label">MAPE</p>
          <p className="kpi-value text-foreground text-xl">{data?.metrics ? `${data.metrics.mape.toFixed(1)}%` : "—"}</p>
        </div>
        <div className="glass-card p-4">
          <p className="data-label">Active Dataset</p>
          <p className="kpi-value text-foreground text-base break-all">{meta?.activeDatasetId ?? "Bundled default"}</p>
        </div>
      </div>

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

      <div className="glass-card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Date</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Predicted Demand</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Lower Bound</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Upper Bound</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Band Position %</th>
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
