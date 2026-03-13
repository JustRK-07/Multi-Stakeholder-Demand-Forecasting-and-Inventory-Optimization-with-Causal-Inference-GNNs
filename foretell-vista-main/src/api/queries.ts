import { apiGet, apiPostForm } from "./client";

export type KpiCard = { title: string; value: string; change: number; trend: "up" | "down" };

export type ForecastPoint = {
  date: string;
  actual?: number;
  predicted: number;
  upperBound: number;
  lowerBound: number;
};

export type ForecastResponse = { horizon: number; data: ForecastPoint[] };

export type InventoryItem = {
  sku: string;
  name: string;
  stock: number;
  capacity: number;
  reorderPoint: number;
  daysOfSupply: number;
  risk: "low" | "medium" | "high" | "critical";
};

export type InventoryResponse = { items: InventoryItem[] };

export type OrderRecommendation = {
  sku: string;
  action: string;
  confidence: number;
  expectedSaving: string;
  urgency: "low" | "medium" | "high" | "critical";
};

export type OrderRecommendationsResponse = { recommendations: OrderRecommendation[] };

export type Promotion = {
  id: string;
  name: string;
  lift: number;
  confidence: number;
  baseline: number;
  withPromo: number;
};

export type PromotionImpactResponse = { found: boolean; promotion: Promotion | null };

export type ProductNode = { id: number; label: string; x: number; y: number; size: number; category: string };
export type ProductEdge = { from: number; to: number; type: "complement" | "substitute"; weight: number };
export type ProductGraphResponse = { nodes: ProductNode[]; edges: ProductEdge[] };
export type GraphEmbeddingItem = { product_id: string; embedding: number[] };
export type GraphSimilarity = { product_id: string; similarity: number };
export type GraphEmbeddingResponse = { items: GraphEmbeddingItem[]; similar: GraphSimilarity[] };

export type UploadResponse = { datasetId: string; status: string; taskId: string };

export type RlRewardPoint = { episode: number; reward: number; baseline: number };
export type RlRewardsResponse = { data: RlRewardPoint[] };
export type RlMetricsResponse = { rl_total_cost: number; baseline_total_cost: number };

export type CausalFactor = { factor: string; impact: number; direction: "positive" | "negative" };
export type CausalFactorsResponse = { data: CausalFactor[] };

export type FederatedRound = { round: number; globalAccuracy: number; localAccuracy: number; privacyBudget: number };
export type FederatedRoundsResponse = { data: FederatedRound[] };

export type Store = { id: number; name: string; lat: number; lng: number; demand: number; performance: number };
export type StoresResponse = { data: Store[] };

export type ExplainabilityFeature = { feature: string; importance: number; shap: number };
export type ExplainabilityFeaturesResponse = { data: ExplainabilityFeature[] };

export type DashboardSummaryPoint = { day: string; sales: number; demand: number };
export type DashboardInventoryPoint = { day: string; level: number };
export type DashboardAlert = { severity: "high" | "medium" | "low"; message: string };
export type DashboardSummaryResponse = { salesTrend: DashboardSummaryPoint[]; inventoryTrend: DashboardInventoryPoint[]; alerts: DashboardAlert[] };

export const qk = {
  kpis: ["kpis"] as const,
  dashboardSummary: ["dashboardSummary"] as const,
  forecasts: (storeId: string, horizon: number) => ["forecasts", storeId, horizon] as const,
  inventory: ["inventory"] as const,
  orderRecs: ["orderRecs"] as const,
  promotionImpact: (promoId: string) => ["promotionImpact", promoId] as const,
  productGraph: ["productGraph"] as const,
  graphEmbedding: (productId: string) => ["graphEmbedding", productId] as const,
  rlRewards: ["rlRewards"] as const,
  rlMetrics: ["rlMetrics"] as const,
  causalFactors: ["causalFactors"] as const,
  federatedRounds: ["federatedRounds"] as const,
  stores: ["stores"] as const,
  explainability: ["explainability"] as const,
};

export function fetchKpis() {
  return apiGet<KpiCard[]>("/api/v1/kpis");
}

export function fetchDashboardSummary() {
  return apiGet<DashboardSummaryResponse>("/api/v1/dashboard/summary");
}

export function fetchForecasts(storeId: string, horizon: number, productId?: string, gnnAdjust = true) {
  const params = new URLSearchParams({ horizon: String(horizon), gnn_adjust: String(gnnAdjust) });
  if (productId) params.set("product_id", productId);
  return apiGet<ForecastResponse>(`/api/v1/forecasts/${encodeURIComponent(storeId)}?${params.toString()}`);
}

export function fetchInventory() {
  return apiGet<InventoryResponse>("/api/v1/inventory");
}

export function fetchOrderRecommendations(mode: "rl" | "baseline" = "rl") {
  return apiGet<OrderRecommendationsResponse>(`/api/v1/orders/recommend?mode=${mode}`);
}

export function fetchPromotionImpact(promoId: string) {
  return apiGet<PromotionImpactResponse>(`/api/v1/promotions/impact?promo_id=${encodeURIComponent(promoId)}`);
}

export function fetchProductGraph() {
  return apiGet<ProductGraphResponse>("/api/v1/graph/products");
}

export function fetchGraphEmbedding(productId: string) {
  return apiGet<GraphEmbeddingResponse>(`/api/v1/graph/embeddings?product_id=${encodeURIComponent(productId)}`);
}

export function fetchRlRewards() {
  return apiGet<RlRewardsResponse>("/api/v1/rl/rewards");
}

export function fetchRlMetrics() {
  return apiGet<RlMetricsResponse>("/api/v1/rl/metrics");
}

export function fetchCausalFactors() {
  return apiGet<CausalFactorsResponse>("/api/v1/causal/factors");
}

export function fetchFederatedRounds() {
  return apiGet<FederatedRoundsResponse>("/api/v1/federated/rounds");
}

export function fetchStores() {
  return apiGet<StoresResponse>("/api/v1/stores");
}

export function fetchExplainabilityFeatures() {
  return apiGet<ExplainabilityFeaturesResponse>("/api/v1/explainability/features");
}

export function uploadDataset(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  return apiPostForm<UploadResponse>("/api/v1/datasets/upload", fd);
}
