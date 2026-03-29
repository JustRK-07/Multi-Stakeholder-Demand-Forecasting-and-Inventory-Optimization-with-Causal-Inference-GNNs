import { apiGet, apiPostForm, apiSendJson } from "./client";

export type KpiCard = { title: string; value: string; change: number; trend: "up" | "down" };

export type ForecastPoint = {
  date: string;
  actual?: number;
  predicted: number;
  upperBound: number;
  lowerBound: number;
};

export type ForecastMetrics = { mae: number; rmse: number; mape: number; val_resid_std: number; train_rows: number; val_rows: number };
export type ForecastModelInfo = {
  trained_at: string;
  dataset_rows: number;
  store_count: number;
  product_count: number;
  feature_count: number;
  supports_mapie: boolean;
};
export type ForecastResponse = {
  horizon: number;
  storeId: string;
  productId?: string;
  gnnAdjust: boolean;
  data: ForecastPoint[];
  actuals?: { date: string; actual: number }[];
  metrics: ForecastMetrics;
  modelInfo: ForecastModelInfo;
};
export type ForecastMetaResponse = {
  metrics: ForecastMetrics;
  modelInfo: ForecastModelInfo;
  stores: string[];
  products: string[];
  activeDatasetId?: string | null;
};

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
  storeId?: string;
  recommendedQty?: number;
  baselineQty?: number;
  rlQty?: number;
};

export type OrderRecommendationsResponse = { recommendations: OrderRecommendation[] };

export type Promotion = {
  id: string;
  name: string;
  lift: number;
  confidence: number;
  baseline: number;
  withPromo: number;
  incrementalUnits?: number;
  ateUnits?: number;
  methods?: Record<string, number>;
  diagnostics?: Record<string, number>;
  cohort?: Record<string, unknown>;
};
export type PromotionSegment = { id: string; name: string };
export type PromotionImpactResponse = { found: boolean; promotion: Promotion | null; availablePromotions: PromotionSegment[]; warning?: string };
export type PromotionSummaryItem = {
  id: string;
  name: string;
  lift: number;
  confidence: number;
  baseline: number;
  withPromo: number;
  incrementalUnits: number;
  warning?: string | null;
};
export type PromotionsSummaryResponse = { items: PromotionSummaryItem[]; availablePromotions: PromotionSegment[] };

export type ProductNode = { id: number; label: string; x: number; y: number; size: number; category: string };
export type ProductEdge = { from: number; to: number; type: "complement" | "substitute"; weight: number; from_product?: string; to_product?: string };
export type ProductGraphResponse = { nodes: ProductNode[]; edges: ProductEdge[] };
export type GraphEmbeddingItem = { product_id: string; embedding: number[] };
export type GraphSimilarity = { product_id: string; similarity: number };
export type GraphEmbeddingResponse = { items: GraphEmbeddingItem[]; similar: GraphSimilarity[] };
export type GraphMetaResponse = {
  top_n?: number;
  min_corr?: number;
  embedding_dim: number;
  graph_stats: { nodes: number; edges: number };
  feature_columns: string[];
};

export type DatasetValidation = {
  requiredColumns?: string[];
  optionalColumns?: string[];
  missingRequired?: string[];
  unmappedColumns?: string[];
  isValid?: boolean;
};

export type DatasetRecord = {
  datasetId: string;
  taskId: string;
  filename: string;
  storedPath: string;
  status: "completed" | "failed";
  progressPct: number;
  uploadedAt: string;
  rowCount: number;
  columns: string[];
  preview: Record<string, unknown>[];
  suggestedMapping: Record<string, string>;
  normalizedPath?: string | null;
  isActive?: boolean;
  isArchived?: boolean;
  archivedAt?: string | null;
  error?: string | null;
  validation?: DatasetValidation;
};

export type UploadResponse = DatasetRecord;
export type DatasetStatusResponse = DatasetRecord;
export type DatasetListResponse = { items: DatasetRecord[]; activeDatasetId?: string | null; page: number; pageSize: number; total: number; includeArchived: boolean };
export type DeleteDatasetResponse = { deleted: boolean; dataset: DatasetRecord; activeDatasetId?: string | null };

export type RlRewardPoint = { episode: number; reward: number; baseline: number };
export type RlRewardsResponse = { data: RlRewardPoint[] };
export type RlSeriesComparison = {
  store_id: string;
  product_id: string;
  rl_total_cost: number;
  baseline_total_cost: number;
  savings: number;
  service_level_rl: number;
  service_level_baseline: number;
};
export type RlMetricsResponse = {
  rl_total_cost: number;
  baseline_total_cost: number;
  cost_delta: number;
  service_level_rl: number;
  service_level_baseline: number;
  average_inventory_rl: number;
  average_inventory_baseline: number;
  series: RlSeriesComparison[];
};
export type ScenarioDay = {
  day: number;
  demand: number;
  rlOrdered: number;
  baselineOrdered: number;
  rlStockout: number;
  baselineStockout: number;
  rlEndingInventory: number;
  baselineEndingInventory: number;
};
export type ScenarioSummary = {
  total_cost: number;
  holding_cost: number;
  stockout_cost: number;
  service_level: number;
  average_inventory: number;
  total_orders: number;
};
export type OrderScenarioResponse = {
  store_id: string;
  product_id: string;
  rl: ScenarioSummary;
  baseline: ScenarioSummary;
  daily: ScenarioDay[];
  savings: number;
};

export type CausalFactor = { factor: string; impact: number; direction: "positive" | "negative" };
export type CausalFactorsResponse = { data: CausalFactor[] };

export type FederatedRound = { round: number; globalAccuracy: number; localAccuracy: number; privacyBudget: number; participants: number };
export type FederatedRoundsResponse = { data: FederatedRound[] };

export type Store = { id: number; code: string; name: string; lat: number; lng: number; demand: number; performance: number };
export type StoresResponse = { data: Store[] };

export type ExplainabilityFeature = { feature: string; importance: number; shap: number };
export type ExplainabilityFeaturesResponse = { data: ExplainabilityFeature[] };
export type ExplainabilityDriver = ExplainabilityFeature & { label: string; impactDirection: "positive" | "negative" };
export type ExplainabilitySummaryResponse = {
  headline: string;
  narrative: string;
  drivers: ExplainabilityDriver[];
  recommendations: string[];
  focus: { storeId?: string | null; productId?: string | null };
};
export type DriftFeature = {
  feature: string;
  baselineMean: number;
  recentMean: number;
  meanShiftPct: number;
  psi: number;
  severity: "low" | "medium" | "high" | "critical";
};
export type MonitoringAlert = { severity: "low" | "medium" | "high" | "critical"; title: string; message: string };
export type DriftReportResponse = {
  baselineWindowDays: number;
  recentWindowDays: number;
  baselineStart: string;
  baselineEnd: string;
  recentStart: string;
  recentEnd: string;
  features: DriftFeature[];
  alerts: MonitoringAlert[];
  target?: DriftFeature | null;
  summary: { severity: "low" | "medium" | "high" | "critical"; featureCount: number; observationCount: number };
};
export type MonitoringStatusResponse = {
  status: "healthy" | "watch" | "warning" | "critical";
  activeDatasetId?: string | null;
  dataPath: string;
  trainedAt?: string | null;
  daysSinceTraining?: number | null;
  observationEndDate?: string | null;
  dataSpanDays: number;
  storeCount: number;
  productCount: number;
  metrics: ForecastMetrics;
  driftSeverity: "low" | "medium" | "high" | "critical";
  topDriftFeatures: DriftFeature[];
  alerts: MonitoringAlert[];
  history: DriftHistoryEntry[];
};
export type Settings = { forecastHorizon: number; holdingCost: number; stockoutCost: number; notifications: boolean };
export type UpdateSettingsResponse = { updated: boolean; settings: Settings };
export type AuthUser = { name: string; email: string; role?: string; createdAt?: string | null; lastLoginAt?: string | null };
export type AuthSessionResponse = { token: string; user: AuthUser; createdAt?: string };
export type AuthPasswordResponse = { updated: boolean; user: AuthUser };
export type AuthProfileResponse = { updated: boolean; user: AuthUser };
export type ProductSummary = { store_id: string; product_id: string; units_sold: number };
export type ProductsResponse = { items: ProductSummary[] };
export type DriftHistoryEntry = {
  scannedAt: string;
  severity: "low" | "medium" | "high" | "critical";
  featureCount: number;
  observationCount: number;
  target?: DriftFeature | null;
  alerts: MonitoringAlert[];
};
export type DriftHistoryResponse = { items: DriftHistoryEntry[] };
export type DriftScanResponse = { report: DriftReportResponse; entry: DriftHistoryEntry };
export type AuditEvent = { timestamp: string; action: string; actor?: string | null; target?: string | null; details: Record<string, unknown> };
export type AuditLogResponse = { items: AuditEvent[] };

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
  promotionsSummary: ["promotionsSummary"] as const,
  productGraph: ["productGraph"] as const,
  graphMeta: ["graphMeta"] as const,
  graphEmbedding: (productId: string) => ["graphEmbedding", productId] as const,
  rlRewards: ["rlRewards"] as const,
  rlMetrics: ["rlMetrics"] as const,
  causalFactors: ["causalFactors"] as const,
  federatedRounds: ["federatedRounds"] as const,
  stores: ["stores"] as const,
  products: (storeId?: string) => ["products", storeId ?? "all"] as const,
  explainability: ["explainability"] as const,
  explainabilitySummary: ["explainabilitySummary"] as const,
  datasetStatus: (datasetId: string) => ["datasetStatus", datasetId] as const,
  datasets: ["datasets"] as const,
  datasetsList: (page = 1, pageSize = 50, includeArchived = false) => ["datasets", page, pageSize, includeArchived] as const,
  settings: ["settings"] as const,
  authSession: ["authSession"] as const,
  forecastMeta: ["forecastMeta"] as const,
  orderScenario: (storeId: string, productId: string, demandScale: number) => ["orderScenario", storeId, productId, demandScale] as const,
  driftReport: ["driftReport"] as const,
  monitoringStatus: ["monitoringStatus"] as const,
  driftHistory: ["driftHistory"] as const,
  auditLog: ["auditLog"] as const,
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

export function fetchForecastMeta() {
  return apiGet<ForecastMetaResponse>("/api/v1/forecast/meta");
}

export function fetchInventory() {
  return apiGet<InventoryResponse>("/api/v1/inventory");
}

export function fetchOrderRecommendations(mode: "rl" | "baseline" = "rl") {
  return apiGet<OrderRecommendationsResponse>(`/api/v1/orders/recommend?mode=${mode}`);
}

export function fetchOrderScenario(storeId?: string, productId?: string, demandScale = 1) {
  const params = new URLSearchParams({ demand_scale: String(demandScale) });
  if (storeId) params.set("store_id", storeId);
  if (productId) params.set("product_id", productId);
  return apiGet<OrderScenarioResponse>(`/api/v1/orders/scenario?${params.toString()}`);
}

export function fetchPromotionImpact(promoId: string) {
  return apiGet<PromotionImpactResponse>(`/api/v1/promotions/impact?promo_id=${encodeURIComponent(promoId)}`);
}

export function fetchPromotionsSummary() {
  return apiGet<PromotionsSummaryResponse>("/api/v1/promotions/summary");
}

export function fetchProductGraph() {
  return apiGet<ProductGraphResponse>("/api/v1/graph/products");
}

export function fetchGraphMeta() {
  return apiGet<GraphMetaResponse>("/api/v1/graph/meta");
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

export function fetchProducts(storeId?: string) {
  const suffix = storeId ? `?store_id=${encodeURIComponent(storeId)}` : "";
  return apiGet<ProductsResponse>(`/api/v1/products${suffix}`);
}

export function fetchExplainabilityFeatures() {
  return apiGet<ExplainabilityFeaturesResponse>("/api/v1/explainability/features");
}

export function fetchExplainabilitySummary() {
  return apiGet<ExplainabilitySummaryResponse>("/api/v1/explainability/summary");
}

export function fetchDriftReport() {
  return apiGet<DriftReportResponse>("/api/v1/drift/report");
}

export function fetchMonitoringStatus() {
  return apiGet<MonitoringStatusResponse>("/api/v1/monitoring/status");
}

export function fetchDriftHistory(limit = 20) {
  return apiGet<DriftHistoryResponse>(`/api/v1/drift/history?limit=${limit}`);
}

export function runDriftScan() {
  return apiSendJson<DriftScanResponse>("/api/v1/drift/scan", "POST");
}

export function fetchAuditLog(limit = 50) {
  return apiGet<AuditLogResponse>(`/api/v1/audit/logs?limit=${limit}`);
}

export function uploadDataset(file: File, columnMapping?: Record<string, string>) {
  const fd = new FormData();
  fd.append("file", file);
  if (columnMapping && Object.keys(columnMapping).length > 0) {
    fd.append("column_mapping", JSON.stringify(columnMapping));
  }
  return apiPostForm<UploadResponse>("/api/v1/datasets/upload", fd);
}

export function fetchDatasetStatus(datasetId: string) {
  return apiGet<DatasetStatusResponse>(`/api/v1/datasets/${encodeURIComponent(datasetId)}/status`);
}

export function fetchDatasets(page = 1, pageSize = 50, includeArchived = false) {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize), include_archived: String(includeArchived) });
  return apiGet<DatasetListResponse>(`/api/v1/datasets?${params.toString()}`);
}

export async function activateDataset(datasetId: string) {
  return apiSendJson<DatasetRecord>(`/api/v1/datasets/${encodeURIComponent(datasetId)}/activate`, "POST");
}

export function deleteDataset(datasetId: string) {
  return apiSendJson<DeleteDatasetResponse>(`/api/v1/datasets/${encodeURIComponent(datasetId)}`, "DELETE");
}

export function archiveDataset(datasetId: string, archived = true) {
  const suffix = archived ? "" : "?archived=false";
  return apiSendJson<DatasetRecord>(`/api/v1/datasets/${encodeURIComponent(datasetId)}/archive${suffix}`, "POST");
}

export function fetchSettings() {
  return apiGet<Settings>("/api/v1/settings");
}

export async function updateSettings(payload: Settings) {
  return apiSendJson<UpdateSettingsResponse>("/api/v1/settings", "PUT", payload);
}

export function signUp(name: string, email: string, password: string) {
  return apiSendJson<AuthSessionResponse>("/api/v1/auth/signup", "POST", { name, email, password });
}

export function logIn(email: string, password: string) {
  return apiSendJson<AuthSessionResponse>("/api/v1/auth/login", "POST", { email, password });
}

export function fetchAuthSession() {
  return apiGet<AuthSessionResponse>("/api/v1/auth/session");
}

export function logOut() {
  return apiSendJson<{ loggedOut: boolean }>("/api/v1/auth/logout", "POST");
}

export function updatePassword(currentPassword: string, newPassword: string) {
  return apiSendJson<AuthPasswordResponse>("/api/v1/auth/password", "PUT", { currentPassword, newPassword });
}

export function updateProfile(name: string) {
  return apiSendJson<AuthProfileResponse>("/api/v1/auth/profile", "PUT", { name });
}
