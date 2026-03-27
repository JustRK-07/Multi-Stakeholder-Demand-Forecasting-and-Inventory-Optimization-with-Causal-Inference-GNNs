import { useState } from "react";
import { Network, ZoomIn, ZoomOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useQuery } from "@tanstack/react-query";
import { fetchGraphEmbedding, fetchGraphMeta, fetchProductGraph, qk } from "@/api/queries";
import { Switch } from "@/components/ui/switch";

const categoryColor: Record<string, string> = {
  Anchor: "hsl(38, 92%, 50%)",
  Core: "hsl(200, 80%, 55%)",
  Growth: "hsl(160, 70%, 45%)",
  Niche: "hsl(0, 72%, 55%)",
};

const ProductGraph = () => {
  const { data } = useQuery({ queryKey: qk.productGraph, queryFn: fetchProductGraph });
  const { data: meta } = useQuery({ queryKey: qk.graphMeta, queryFn: fetchGraphMeta });
  const products = data?.nodes ?? [];
  const relationships = data?.edges ?? [];
  const [selectedNode, setSelectedNode] = useState<number | null>(null);
  const [zoom, setZoom] = useState(1);
  const [showSimilar, setShowSimilar] = useState(true);
  const selectedProduct = selectedNode ? products.find((n) => n.id === selectedNode)?.label : null;
  const { data: embeddingData } = useQuery({
    queryKey: selectedProduct ? qk.graphEmbedding(selectedProduct) : ["graphEmbedding", "none"],
    queryFn: () => fetchGraphEmbedding(selectedProduct ?? ""),
    enabled: Boolean(selectedProduct && showSimilar),
  });

  const getNode = (id: number) => products.find((n) => n.id === id)!;
  const connectedIds = selectedNode
    ? relationships.filter((r) => r.from === selectedNode || r.to === selectedNode).flatMap((r) => [r.from, r.to])
    : [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-foreground">Product Relationship Graph</h2>
          <p className="text-xs text-muted-foreground">Learned graph structure plus generated product embeddings</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Switch checked={showSimilar} onCheckedChange={setShowSimilar} />
            GNN Similarity
          </div>
          <Button variant="outline" size="icon" className="h-8 w-8 border-border" onClick={() => setZoom((z) => Math.min(z + 0.2, 2))}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" className="h-8 w-8 border-border" onClick={() => setZoom((z) => Math.max(z - 0.2, 0.5))}>
            <ZoomOut className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card p-4">
          <p className="data-label">Nodes</p>
          <p className="kpi-value text-foreground">{meta?.graph_stats?.nodes ?? 0}</p>
        </div>
        <div className="glass-card p-4">
          <p className="data-label">Edges</p>
          <p className="kpi-value text-foreground">{meta?.graph_stats?.edges ?? 0}</p>
        </div>
        <div className="glass-card p-4">
          <p className="data-label">Embedding Dim</p>
          <p className="kpi-value text-foreground">{meta?.embedding_dim ?? 0}</p>
        </div>
        <div className="glass-card p-4">
          <p className="data-label">Min Corr</p>
          <p className="kpi-value text-foreground">{meta?.min_corr ?? 0}</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-4">
        {Object.entries(categoryColor).map(([cat, color]) => (
          <div key={cat} className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="w-3 h-3 rounded-full" style={{ background: color }} />
            {cat}
          </div>
        ))}
        <div className="flex items-center gap-2 text-xs text-muted-foreground ml-4">
          <span className="w-6 h-0.5 bg-primary inline-block" /> Complement
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="w-6 h-0.5 inline-block" style={{ background: "hsl(38, 92%, 50%)", borderTop: "2px dashed hsl(38, 92%, 50%)" }} /> Substitute
        </div>
      </div>

      <div className="glass-card p-4 overflow-hidden">
        <svg viewBox="0 0 700 500" className="w-full h-[480px]" style={{ transform: `scale(${zoom})`, transformOrigin: "center" }}>
          {relationships.map((rel, i) => {
            const from = getNode(rel.from);
            const to = getNode(rel.to);
            const isHighlighted = selectedNode && (rel.from === selectedNode || rel.to === selectedNode);
            const opacity = selectedNode ? (isHighlighted ? 0.9 : 0.1) : rel.weight * 0.6;
            return (
              <line
                key={i}
                x1={from.x}
                y1={from.y}
                x2={to.x}
                y2={to.y}
                stroke={rel.type === "substitute" ? "hsl(38, 92%, 50%)" : "hsl(160, 70%, 45%)"}
                strokeOpacity={opacity}
                strokeWidth={rel.weight * 3}
                strokeDasharray={rel.type === "substitute" ? "6 4" : "none"}
              />
            );
          })}
          {products.map((node) => {
            const isSelected = node.id === selectedNode;
            const isConnected = connectedIds.includes(node.id);
            const opacity = selectedNode ? (isSelected || isConnected ? 1 : 0.2) : 1;
            return (
              <g key={node.id} onClick={() => setSelectedNode(isSelected ? null : node.id)} className="cursor-pointer" opacity={opacity}>
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={node.size}
                  fill="hsl(220, 18%, 12%)"
                  stroke={categoryColor[node.category] ?? "hsl(160, 70%, 45%)"}
                  strokeWidth={isSelected ? 3 : 1.5}
                />
                {isSelected && (
                  <circle cx={node.x} cy={node.y} r={node.size + 6} fill="none" stroke={categoryColor[node.category] ?? "hsl(160, 70%, 45%)"} strokeWidth={1} strokeOpacity={0.4} />
                )}
                <text x={node.x} y={node.y - 2} textAnchor="middle" dominantBaseline="middle" fill="hsl(210, 20%, 92%)" fontSize="10" fontWeight="600">
                  {node.label}
                </text>
                <text x={node.x} y={node.y + 11} textAnchor="middle" fill="hsl(215, 15%, 55%)" fontSize="7">
                  {node.category}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {selectedNode && (
        <div className="glass-card p-5 space-y-5">
          <div>
            <h3 className="text-sm font-semibold text-foreground mb-1">
              {getNode(selectedNode).label} — Related Products
            </h3>
            <p className="text-xs text-muted-foreground">Feature columns used in embedding generation: {(meta?.feature_columns ?? []).join(", ") || "—"}</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {relationships
              .filter((r) => r.from === selectedNode || r.to === selectedNode)
              .map((r, i) => {
                const otherId = r.from === selectedNode ? r.to : r.from;
                const other = getNode(otherId);
                return (
                  <div key={i} className="flex items-center justify-between p-3 rounded-md bg-secondary/50">
                    <div>
                      <span className="text-sm text-foreground font-medium">{other.label}</span>
                      <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${r.type === "complement" ? "bg-primary/15 text-primary" : "bg-warning/15 text-warning"}`}>
                        {r.type}
                      </span>
                    </div>
                    <span className="text-xs text-muted-foreground font-mono">weight: {r.weight}</span>
                  </div>
                );
              })}
          </div>

          {showSimilar && embeddingData?.similar?.length ? (
            <div>
              <div className="text-xs uppercase tracking-wide text-muted-foreground mb-2">Embedding Similarity</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {embeddingData.similar.map((s) => (
                  <div key={s.product_id} className="flex items-center justify-between rounded-md border border-border/60 bg-background/40 px-3 py-2">
                    <span className="text-sm text-foreground">{s.product_id}</span>
                    <span className="text-xs font-mono text-muted-foreground">{s.similarity.toFixed(3)}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};

export default ProductGraph;
