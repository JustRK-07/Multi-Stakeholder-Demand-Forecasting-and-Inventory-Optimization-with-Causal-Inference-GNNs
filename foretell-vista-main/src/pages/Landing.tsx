import { Link } from "react-router-dom";
import { BarChart3, TrendingUp, Package, Megaphone, Network, ArrowRight, Zap, Shield, Brain } from "lucide-react";
import { Button } from "@/components/ui/button";

const features = [
  {
    icon: TrendingUp,
    title: "Instant Demand Forecasting",
    description: "Get AI-powered predictions immediately - no data upload needed. Pre-trained models for Grocery, Fashion & Electronics.",
  },
  {
    icon: Package,
    title: "Inventory Optimization",
    description: "Smart reorder recommendations with stockout risk alerts and days-of-supply monitoring.",
  },
  {
    icon: Megaphone,
    title: "Promotion Impact Analysis",
    description: "Causal inference to measure true promotion lift with counterfactual baselines.",
  },
  {
    icon: Network,
    title: "Product Relationship Insights",
    description: "Graph neural network visualization of complements, substitutes, and cross-sell opportunities.",
  },
  {
    icon: Zap,
    title: "Live Data Integrations",
    description: "Connect Shopify, Square, or custom webhooks for automatic daily syncing and forecast updates.",
  },
  {
    icon: Shield,
    title: "Privacy-First ML",
    description: "Federated learning across store locations without sharing raw customer data.",
  },
];

const Landing = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="container mx-auto flex items-center justify-between h-16 px-4">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-7 w-7 text-primary" />
            <span className="text-lg font-bold text-foreground tracking-tight">RetailCast AI</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login">
              <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                Log in
              </Button>
            </Link>
            <Link to="/signup">
              <Button size="sm" className="bg-primary text-primary-foreground hover:bg-primary/90">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent" />
        <div className="container mx-auto px-4 py-24 md:py-36 relative">
          <div className="max-w-3xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-primary/20 bg-primary/5 text-primary text-xs font-medium mb-6">
              <Brain className="h-3.5 w-3.5" />
              AI-Powered Analytics
            </div>
            <h1 className="text-4xl md:text-6xl font-bold text-foreground tracking-tight leading-tight mb-6">
              Retail Demand Forecasting
              <span className="block text-primary">&amp; Inventory Intelligence</span>
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
              Get accurate demand forecasts instantly with pre-trained AI models. No data upload needed. Optimize inventory, measure promotions, and uncover hidden product relationships — all in one platform.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/signup">
                <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 px-8 gap-2">
                  Get Started Free <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link to="/login">
                <Button size="lg" variant="outline" className="border-border text-foreground hover:bg-secondary px-8">
                  View Demo Dashboard
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center mb-14">
          <h2 className="text-2xl md:text-3xl font-bold text-foreground mb-3">Everything You Need</h2>
          <p className="text-muted-foreground max-w-lg mx-auto">
            End-to-end retail analytics from instant forecasts to actionable insights.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f) => (
            <div key={f.title} className="glass-card p-6 hover:border-primary/30 transition-colors group">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                <f.icon className="h-5 w-5 text-primary" />
              </div>
              <h3 className="text-foreground font-semibold mb-2">{f.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="container mx-auto px-4 py-16 mb-10">
        <div className="glass-card glow-border p-10 md:p-16 text-center">
          <h2 className="text-2xl md:text-3xl font-bold text-foreground mb-4">Ready to Forecast Smarter?</h2>
          <p className="text-muted-foreground max-w-lg mx-auto mb-8">
            Select your store type and get AI-powered demand forecasts in minutes. No data upload needed.
          </p>
          <Link to="/signup">
            <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 px-10 gap-2">
              Get Started Free <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-10">
        <div className="container mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            <span className="text-sm font-semibold text-foreground">RetailCast AI</span>
          </div>
          <div className="flex items-center gap-6 text-xs text-muted-foreground">
            <span>Documentation</span>
            <span>Contact</span>
            <span>About</span>
          </div>
          <p className="text-xs text-muted-foreground">© 2026 RetailCast AI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
