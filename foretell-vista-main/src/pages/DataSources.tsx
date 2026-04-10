import React, { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, CheckCircle2, Plus } from "lucide-react";

interface DataSource {
  id: string;
  name: string;
  provider: string;
  icon: string;
  description: string;
  status: "connected" | "disconnected";
  lastSync?: string;
  features: string[];
}

export default function DataSources() {
  const [dataSources, setDataSources] = useState<DataSource[]>([
    {
      id: "shopify",
      name: "Shopify",
      provider: "shopify",
      icon: "🛒",
      description: "Connect your Shopify store to automatically fetch sales data",
      status: "disconnected",
      features: ["Real-time sales", "Inventory sync", "Product data"],
    },
    {
      id: "square",
      name: "Square POS",
      provider: "square",
      icon: "🏪",
      description: "Sync sales data from your Square point-of-sale system",
      status: "disconnected",
      features: ["Daily sales", "Transaction details", "Inventory"],
    },
    {
      id: "webhook",
      name: "Custom API Webhook",
      provider: "webhook",
      icon: "🔌",
      description: "Send custom sales data via webhook for maximum flexibility",
      status: "disconnected",
      features: ["Custom fields", "Scheduled sync", "Data validation"],
    },
  ]);

  const handleConnect = (sourceId: string) => {
    // UI-only: show connection modal (no backend yet)
    alert(`Connect ${sourceId.toUpperCase()}\n\nThis feature will be available in Phase 3.\nFor now, you can upload sample data to test forecasts.`);
  };

  const handleDisconnect = (sourceId: string) => {
    setDataSources(
      dataSources.map((ds) =>
        ds.id === sourceId ? { ...ds, status: "disconnected" } : ds
      )
    );
  };

  return (
    <div className="w-full h-full overflow-auto bg-slate-50 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2">
            Data Sources & Integrations
          </h1>
          <p className="text-slate-600">
            Connect your sales channels to automatically fetch data and improve forecasts
          </p>
        </div>

        {/* Info Alert */}
        <Alert className="bg-blue-50 border-blue-200">
          <AlertCircle className="h-4 w-4 text-blue-600" />
          <AlertDescription className="text-blue-800 ml-2">
            <strong>Phase 2 Preview:</strong> Integration UI is ready. Live syncing will be available in Phase 3. Currently, you can use the pre-trained model with sample forecasts.
          </AlertDescription>
        </Alert>

        {/* Data Sources Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {dataSources.map((source) => (
            <Card key={source.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between mb-2">
                  <div className="text-4xl">{source.icon}</div>
                  <Badge
                    variant={source.status === "connected" ? "default" : "outline"}
                    className={
                      source.status === "connected"
                        ? "bg-green-100 text-green-800"
                        : "text-slate-600"
                    }
                  >
                    {source.status === "connected" ? (
                      <CheckCircle2 className="w-3 h-3 mr-1 inline" />
                    ) : null}
                    {source.status === "connected" ? "Connected" : "Not Connected"}
                  </Badge>
                </div>
                <CardTitle className="text-xl">{source.name}</CardTitle>
                <CardDescription>{source.description}</CardDescription>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Features */}
                <div>
                  <h4 className="font-semibold text-sm mb-2 text-slate-700">
                    Features:
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {source.features.map((feature) => (
                      <Badge key={feature} variant="secondary" className="bg-slate-100">
                        {feature}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Last Sync */}
                {source.lastSync && (
                  <div className="text-xs text-slate-500">
                    Last synced: {source.lastSync}
                  </div>
                )}

                {/* Action Button */}
                {source.status === "disconnected" ? (
                  <Button
                    onClick={() => handleConnect(source.id)}
                    className="w-full bg-blue-600 hover:bg-blue-700"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Connect
                  </Button>
                ) : (
                  <Button
                    onClick={() => handleDisconnect(source.id)}
                    variant="destructive"
                    className="w-full"
                  >
                    Disconnect
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Coming Soon Section */}
        <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
          <CardHeader>
            <CardTitle className="text-slate-900">Coming Soon</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-semibold text-slate-900 mb-1">🎯 Phase 3</h4>
                <p className="text-sm text-slate-700">
                  Live integration backends for Shopify, Square, and custom webhooks
                </p>
              </div>
              <div>
                <h4 className="font-semibold text-slate-900 mb-1">📈 Auto-sync</h4>
                <p className="text-sm text-slate-700">
                  Automatic daily data sync and model updates as new sales flow in
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* For Now Section */}
        <Card className="bg-amber-50 border-amber-200">
          <CardHeader>
            <CardTitle className="text-amber-900">For Now</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-amber-800 mb-3">
              While integrations are being built, you can:
            </p>
            <ul className="text-sm text-amber-800 space-y-1">
              <li>✓ Use pre-trained models for immediate forecasts</li>
              <li>✓ View sample forecasts based on your store type</li>
              <li>✓ Manually upload sample data to test features</li>
              <li>✓ Explore inventory recommendations and causal insights</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
