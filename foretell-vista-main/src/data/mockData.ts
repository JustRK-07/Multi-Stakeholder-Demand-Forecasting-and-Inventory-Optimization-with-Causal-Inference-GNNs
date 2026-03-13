// Mock data for the supply chain dashboard

export const kpiData = [
  { title: "Forecast Accuracy", value: "94.2%", change: +2.1, trend: "up" as const },
  { title: "Service Level", value: "97.8%", change: +0.5, trend: "up" as const },
  { title: "Inventory Turnover", value: "12.4x", change: -0.3, trend: "down" as const },
  { title: "Stockout Rate", value: "1.2%", change: -0.8, trend: "up" as const },
  { title: "Order Fill Rate", value: "98.5%", change: +1.2, trend: "up" as const },
  { title: "MAPE", value: "5.8%", change: -1.4, trend: "up" as const },
];

export const forecastData = Array.from({ length: 30 }, (_, i) => {
  const base = 800 + Math.sin(i / 5) * 200 + Math.random() * 50;
  return {
    date: `Mar ${i + 1}`,
    actual: i < 20 ? Math.round(base + Math.random() * 40 - 20) : undefined,
    predicted: Math.round(base),
    upperBound: Math.round(base + 80 + Math.random() * 30),
    lowerBound: Math.round(base - 80 - Math.random() * 30),
  };
});

export const inventoryData = [
  { sku: "SKU-001", name: "Premium Widgets", stock: 1240, capacity: 2000, reorderPoint: 500, daysOfSupply: 18, risk: "low" as const },
  { sku: "SKU-002", name: "Standard Bolts", stock: 320, capacity: 1500, reorderPoint: 400, daysOfSupply: 5, risk: "high" as const },
  { sku: "SKU-003", name: "Deluxe Gaskets", stock: 890, capacity: 1200, reorderPoint: 300, daysOfSupply: 22, risk: "low" as const },
  { sku: "SKU-004", name: "Micro Sensors", stock: 150, capacity: 800, reorderPoint: 200, daysOfSupply: 3, risk: "critical" as const },
  { sku: "SKU-005", name: "Copper Cables", stock: 2100, capacity: 3000, reorderPoint: 700, daysOfSupply: 30, risk: "low" as const },
  { sku: "SKU-006", name: "LED Modules", stock: 450, capacity: 1000, reorderPoint: 350, daysOfSupply: 8, risk: "medium" as const },
  { sku: "SKU-007", name: "Steel Frames", stock: 680, capacity: 1500, reorderPoint: 500, daysOfSupply: 12, risk: "medium" as const },
  { sku: "SKU-008", name: "Circuit Boards", stock: 95, capacity: 600, reorderPoint: 150, daysOfSupply: 2, risk: "critical" as const },
];

export const rlRecommendations = [
  { sku: "SKU-002", action: "Order 800 units", confidence: 92, expectedSaving: "$2,340", urgency: "high" as const },
  { sku: "SKU-004", action: "Order 500 units", confidence: 97, expectedSaving: "$1,890", urgency: "critical" as const },
  { sku: "SKU-008", action: "Order 350 units", confidence: 88, expectedSaving: "$980", urgency: "critical" as const },
  { sku: "SKU-006", action: "Order 200 units", confidence: 75, expectedSaving: "$540", urgency: "medium" as const },
];

export const rewardCurveData = Array.from({ length: 50 }, (_, i) => ({
  episode: i + 1,
  reward: -500 + (450 * (1 - Math.exp(-i / 15))) + Math.random() * 30,
  baseline: -500 + (300 * (1 - Math.exp(-i / 20))),
}));

export const causalFactors = [
  { factor: "Weekend Effect", impact: 12, direction: "positive" as const },
  { factor: "Promotion X", impact: 15, direction: "positive" as const },
  { factor: "Rain Forecast", impact: 8, direction: "positive" as const },
  { factor: "Competitor Price Drop", impact: -6, direction: "negative" as const },
  { factor: "Supply Delay", impact: -4, direction: "negative" as const },
  { factor: "Holiday Season", impact: 22, direction: "positive" as const },
];

export const explainabilityFeatures = [
  { feature: "Day of Week", importance: 0.23, shap: 0.18 },
  { feature: "Promotion Active", importance: 0.19, shap: 0.15 },
  { feature: "Weather", importance: 0.15, shap: 0.12 },
  { feature: "Price", importance: 0.13, shap: -0.08 },
  { feature: "Competitor Price", importance: 0.11, shap: -0.06 },
  { feature: "Season", importance: 0.09, shap: 0.07 },
  { feature: "Stock Level", importance: 0.06, shap: -0.04 },
  { feature: "Trend", importance: 0.04, shap: 0.03 },
];

export const storeData = [
  { id: 1, name: "Downtown Hub", lat: 40.7128, lng: -74.006, demand: 920, performance: 96 },
  { id: 2, name: "Westside Mall", lat: 40.7589, lng: -73.9851, demand: 750, performance: 91 },
  { id: 3, name: "Airport Terminal", lat: 40.6413, lng: -73.7781, demand: 1100, performance: 98 },
  { id: 4, name: "Harbor Point", lat: 40.6892, lng: -74.0445, demand: 430, performance: 87 },
  { id: 5, name: "Midtown Center", lat: 40.7549, lng: -73.984, demand: 1340, performance: 94 },
];

export const federatedRounds = [
  { round: 1, globalAccuracy: 78.2, localAccuracy: 80.1, privacyBudget: 0.95 },
  { round: 2, globalAccuracy: 82.5, localAccuracy: 83.8, privacyBudget: 0.88 },
  { round: 3, globalAccuracy: 86.1, localAccuracy: 86.9, privacyBudget: 0.82 },
  { round: 4, globalAccuracy: 89.3, localAccuracy: 89.0, privacyBudget: 0.75 },
  { round: 5, globalAccuracy: 91.8, localAccuracy: 91.2, privacyBudget: 0.69 },
  { round: 6, globalAccuracy: 93.1, localAccuracy: 92.8, privacyBudget: 0.63 },
  { round: 7, globalAccuracy: 94.2, localAccuracy: 93.5, privacyBudget: 0.58 },
];
