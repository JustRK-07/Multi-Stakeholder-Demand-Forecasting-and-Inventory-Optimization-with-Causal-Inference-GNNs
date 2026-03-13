import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Calendar, Filter } from "lucide-react";

export function GlobalFilters() {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Filter className="h-3.5 w-3.5" />
        <span className="font-medium">Filters</span>
      </div>
      <Select defaultValue="7d">
        <SelectTrigger className="h-8 w-[130px] text-xs bg-secondary border-border">
          <Calendar className="h-3 w-3 mr-1.5" />
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="1d">Last 24h</SelectItem>
          <SelectItem value="7d">Last 7 days</SelectItem>
          <SelectItem value="30d">Last 30 days</SelectItem>
          <SelectItem value="90d">Last 90 days</SelectItem>
        </SelectContent>
      </Select>
      <Select defaultValue="all">
        <SelectTrigger className="h-8 w-[120px] text-xs bg-secondary border-border">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Stores</SelectItem>
          <SelectItem value="1">Downtown Hub</SelectItem>
          <SelectItem value="2">Westside Mall</SelectItem>
          <SelectItem value="3">Airport Terminal</SelectItem>
        </SelectContent>
      </Select>
      <Select defaultValue="all">
        <SelectTrigger className="h-8 w-[120px] text-xs bg-secondary border-border">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All SKUs</SelectItem>
          <SelectItem value="001">SKU-001</SelectItem>
          <SelectItem value="002">SKU-002</SelectItem>
          <SelectItem value="004">SKU-004</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
