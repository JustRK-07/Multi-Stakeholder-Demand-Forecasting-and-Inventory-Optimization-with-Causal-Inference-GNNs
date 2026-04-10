import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { AppSidebar } from "@/components/AppSidebar";
import { useAuth } from "@/components/AuthProvider";
import { Routes, Route } from "react-router-dom";
import DashboardHome from "./DashboardHome";
import ForecastResults from "./ForecastResults";
import InventoryRecommendations from "./InventoryRecommendations";
import PromotionAnalysis from "./PromotionAnalysis";
import ProductGraph from "./ProductGraph";
import Monitoring from "./Monitoring";
import Datasets from "./Datasets";
import DataSources from "./DataSources";
import Settings from "./Settings";

const Dashboard = () => {
  const { user, logout } = useAuth();

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <header className="h-12 flex items-center justify-between border-b border-border px-4 shrink-0 gap-4">
            <div className="flex items-center min-w-0">
            <SidebarTrigger />
              <h1 className="text-sm font-semibold text-foreground ml-3 hidden sm:block">RetailCast AI</h1>
            </div>
            <div className="flex items-center gap-3">
              <span className="hidden md:block text-xs text-muted-foreground truncate max-w-48">{user?.email}</span>
              <Button variant="outline" size="sm" onClick={() => void logout()}>
                Log out
              </Button>
            </div>
          </header>
          <main className="flex-1 overflow-y-auto scrollbar-thin p-4 md:p-6">
            <Routes>
              <Route index element={<DashboardHome />} />
              <Route path="forecast" element={<ForecastResults />} />
              <Route path="inventory" element={<InventoryRecommendations />} />
              <Route path="promotions" element={<PromotionAnalysis />} />
              <Route path="graph" element={<ProductGraph />} />
              <Route path="monitoring" element={<Monitoring />} />
              <Route path="datasets" element={<Datasets />} />
              <Route path="data-sources" element={<DataSources />} />
              <Route path="settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Dashboard;
