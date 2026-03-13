import { useState, useCallback } from "react";
import { Upload as UploadIcon, FileSpreadsheet, X, Check, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { useMutation } from "@tanstack/react-query";
import { uploadDataset } from "@/api/queries";
import { ApiRequestError } from "@/api/client";

type SampleRow = { date: string; store_id: string; product_id: string; sales: number; price: number };

const sampleData: SampleRow[] = [
  { date: "2026-01-01", store_id: "S001", product_id: "P101", sales: 142, price: 9.99 },
  { date: "2026-01-02", store_id: "S001", product_id: "P101", sales: 158, price: 9.99 },
  { date: "2026-01-03", store_id: "S002", product_id: "P203", sales: 89, price: 14.5 },
  { date: "2026-01-04", store_id: "S002", product_id: "P203", sales: 95, price: 13.0 },
  { date: "2026-01-05", store_id: "S003", product_id: "P305", sales: 210, price: 7.25 },
];

const targetColumns = ["date", "store_id", "product_id", "sales_qty", "price", "promotion", "category"];

const Upload = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const { toast } = useToast();
  const upload = useMutation({
    mutationFn: (f: File) => uploadDataset(f),
    onSuccess: (res) => {
      toast({
        title: "Dataset uploaded",
        description: `Processing started (datasetId=${res.datasetId}).`,
      });
    },
    onError: (e: unknown) => {
      const message =
        e instanceof ApiRequestError ? e.message :
        e instanceof Error ? e.message :
        "Unexpected error";
      toast({
        title: "Upload failed",
        description: message,
        variant: "destructive",
      });
    },
  });

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && (dropped.name.endsWith(".csv") || dropped.name.endsWith(".xlsx") || dropped.name.endsWith(".json"))) {
      setFile(dropped);
    } else {
      toast({ title: "Unsupported format", description: "Please upload CSV, Excel, or JSON files.", variant: "destructive" });
    }
  }, [toast]);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) setFile(e.target.files[0]);
  };

  const detectedColumns = file ? (Object.keys(sampleData[0]) as Array<keyof SampleRow>) : [];

  const handleProcess = () => {
    if (!file) return;
    upload.mutate(file);
  };

  return (
    <div className="min-h-screen bg-background p-6 md:p-10">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-foreground mb-1">Upload Dataset</h1>
        <p className="text-sm text-muted-foreground mb-8">Upload your sales, inventory, and product datasets.</p>

        {/* Drag & Drop */}
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`glass-card border-2 border-dashed p-12 text-center transition-colors cursor-pointer ${
            isDragging ? "border-primary bg-primary/5" : "border-border hover:border-muted-foreground/40"
          }`}
          onClick={() => document.getElementById("file-input")?.click()}
        >
          <input id="file-input" type="file" accept=".csv,.xlsx,.xls,.json" className="hidden" onChange={handleFileInput} />
          {file ? (
            <div className="flex items-center justify-center gap-3">
              <FileSpreadsheet className="h-8 w-8 text-primary" />
              <div className="text-left">
                <p className="text-foreground font-medium">{file.name}</p>
                <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
              <button onClick={(e) => { e.stopPropagation(); setFile(null); setColumnMapping({}); }} className="ml-4 text-muted-foreground hover:text-destructive">
                <X className="h-5 w-5" />
              </button>
            </div>
          ) : (
            <>
              <UploadIcon className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
              <p className="text-foreground font-medium mb-1">Drag & drop your file here</p>
              <p className="text-xs text-muted-foreground">Supports CSV, Excel, JSON · Max 20MB</p>
            </>
          )}
        </div>

        {/* Preview Table */}
        {file && (
          <div className="mt-8">
            <h2 className="text-sm font-semibold text-foreground mb-3">Data Preview</h2>
            <div className="glass-card overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    {detectedColumns.map((col) => (
                      <th key={col} className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sampleData.map((row, i) => (
                    <tr key={i} className="border-b border-border/50 hover:bg-secondary/30">
                      {detectedColumns.map((col) => (
                        <td key={col} className="px-4 py-2.5 text-foreground font-mono text-xs">
                          {String(row[col])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Column Mapping */}
        {file && (
          <div className="mt-8">
            <h2 className="text-sm font-semibold text-foreground mb-3">Column Mapping</h2>
            <p className="text-xs text-muted-foreground mb-4">Map your dataset columns to the expected schema.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {detectedColumns.map((col) => (
                <div key={col} className="glass-card p-4 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-xs font-mono text-foreground truncate">{col}</span>
                    <ArrowRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  </div>
                  <Select value={columnMapping[col] || ""} onValueChange={(v) => setColumnMapping((prev) => ({ ...prev, [col]: v }))}>
                    <SelectTrigger className="w-40 h-8 text-xs bg-secondary border-border">
                      <SelectValue placeholder="Map to..." />
                    </SelectTrigger>
                    <SelectContent>
                      {targetColumns.map((tc) => (
                        <SelectItem key={tc} value={tc} className="text-xs">{tc}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {columnMapping[col] && <Check className="h-4 w-4 text-primary shrink-0" />}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Process Button */}
        {file && (
          <div className="mt-8 flex justify-end">
            <Button onClick={handleProcess} disabled={upload.isPending} className="bg-primary text-primary-foreground hover:bg-primary/90 gap-2">
              Process Dataset <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Upload;
