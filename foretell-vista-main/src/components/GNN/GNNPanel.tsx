import { Network } from "lucide-react";

// Simple GNN visualization placeholder with product nodes
const nodes = [
  { id: 1, label: "SKU-001", x: 200, y: 80, size: 28 },
  { id: 2, label: "SKU-002", x: 100, y: 180, size: 22 },
  { id: 3, label: "SKU-003", x: 300, y: 180, size: 26 },
  { id: 4, label: "SKU-004", x: 150, y: 280, size: 18 },
  { id: 5, label: "SKU-005", x: 250, y: 280, size: 24 },
  { id: 6, label: "SKU-006", x: 350, y: 100, size: 20 },
];

const edges = [
  { from: 1, to: 2, weight: 0.8 },
  { from: 1, to: 3, weight: 0.9 },
  { from: 2, to: 4, weight: 0.6 },
  { from: 3, to: 5, weight: 0.7 },
  { from: 1, to: 6, weight: 0.4 },
  { from: 3, to: 6, weight: 0.5 },
  { from: 4, to: 5, weight: 0.3 },
];

export function GNNPanel() {
  const getNodePos = (id: number) => nodes.find((n) => n.id === id)!;

  return (
    <div id="gnn" className="glass-card p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="panel-header">GNN Product Network</h2>
          <p className="text-xs text-muted-foreground mt-1">Graph neural network — product relationship mapping</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Network className="h-4 w-4" />
          <span>{nodes.length} nodes · {edges.length} edges</span>
        </div>
      </div>
      <div className="flex justify-center">
        <svg viewBox="0 0 450 340" className="w-full max-w-lg h-[300px]">
          {edges.map((edge, i) => {
            const from = getNodePos(edge.from);
            const to = getNodePos(edge.to);
            return (
              <line
                key={i}
                x1={from.x}
                y1={from.y}
                x2={to.x}
                y2={to.y}
                stroke="hsl(160, 70%, 45%)"
                strokeOpacity={edge.weight * 0.6}
                strokeWidth={edge.weight * 3}
              />
            );
          })}
          {nodes.map((node) => (
            <g key={node.id}>
              <circle
                cx={node.x}
                cy={node.y}
                r={node.size}
                fill="hsl(220, 18%, 12%)"
                stroke="hsl(160, 70%, 45%)"
                strokeWidth={1.5}
                strokeOpacity={0.6}
              />
              <text
                x={node.x}
                y={node.y + 1}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="hsl(210, 20%, 80%)"
                fontSize="9"
                fontFamily="JetBrains Mono, monospace"
              >
                {node.label}
              </text>
            </g>
          ))}
        </svg>
      </div>
    </div>
  );
}
