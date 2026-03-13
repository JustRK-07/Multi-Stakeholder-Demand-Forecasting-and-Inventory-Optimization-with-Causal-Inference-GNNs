import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import { Routes, Route } from "react-router-dom";
import DashboardHome from "./DashboardHome";
import Upload from "./Upload";
import ForecastResults from "./ForecastResults";
import InventoryRecommendations from "./InventoryRecommendations";
import PromotionAnalysis from "./PromotionAnalysis";
import ProductGraph from "./ProductGraph";
import Settings from "./Settings";

const Dashboard = () => {
  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <header className="h-12 flex items-center border-b border-border px-4 shrink-0">
            <SidebarTrigger />
            <h1 className="text-sm font-semibold text-foreground ml-3 hidden sm:block">RetailCast AI</h1>
          </header>
          <main className="flex-1 overflow-y-auto scrollbar-thin p-4 md:p-6">
            <Routes>
              <Route index element={<DashboardHome />} />
              <Route path="upload" element={<Upload />} />
              <Route path="forecast" element={<ForecastResults />} />
              <Route path="inventory" element={<InventoryRecommendations />} />
              <Route path="promotions" element={<PromotionAnalysis />} />
              <Route path="graph" element={<ProductGraph />} />
              <Route path="settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Dashboard;
