import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Database, Archive, Trash2 } from "lucide-react";
import { useAuth } from "@/components/AuthProvider";
import { activateDataset, archiveDataset, deleteDataset, fetchDatasets, qk } from "@/api/queries";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";

const pageSize = 10;

const Datasets = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [includeArchived, setIncludeArchived] = useState(false);

  const canManage = user?.role === "admin";

  const { data } = useQuery({
    queryKey: qk.datasetsList(page, pageSize, includeArchived),
    queryFn: () => fetchDatasets(page, pageSize, includeArchived),
  });

  const activateMutation = useMutation({
    mutationFn: activateDataset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qk.datasets });
      queryClient.invalidateQueries({ queryKey: qk.forecastMeta });
      toast({ title: "Active dataset updated" });
    },
  });
  const archiveMutation = useMutation({
    mutationFn: ({ datasetId, archived }: { datasetId: string; archived: boolean }) => archiveDataset(datasetId, archived),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: qk.datasets });
      toast({ title: variables.archived ? "Dataset archived" : "Dataset restored" });
    },
  });
  const deleteMutation = useMutation({
    mutationFn: deleteDataset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qk.datasets });
      queryClient.invalidateQueries({ queryKey: qk.forecastMeta });
      toast({ title: "Dataset deleted" });
    },
  });

  const totalPages = Math.max(1, Math.ceil((data?.total ?? 0) / pageSize));

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-foreground">Dataset History</h2>
          <p className="text-xs text-muted-foreground">Activate, archive, restore, and delete uploaded datasets.</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>Show archived</span>
          <Switch checked={includeArchived} onCheckedChange={setIncludeArchived} />
        </div>
      </div>

      <div className="glass-card p-5 space-y-4">
        {data?.items?.length ? data.items.map((item) => (
          <div key={item.datasetId} className="rounded-xl border border-border bg-secondary/20 p-4">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-primary" />
                  <p className="text-sm font-medium text-foreground">{item.filename}</p>
                  {item.isActive ? <span className="rounded-full bg-primary/15 px-2 py-0.5 text-[10px] text-primary">ACTIVE</span> : null}
                  {item.isArchived ? <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">ARCHIVED</span> : null}
                </div>
                <p className="text-xs text-muted-foreground">
                  Uploaded {new Date(item.uploadedAt).toLocaleString()} · {item.rowCount} rows · {item.status}
                </p>
                <p className="text-xs text-muted-foreground break-all">{item.datasetId}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" size="sm" disabled={!canManage || item.isActive || item.isArchived || activateMutation.isPending} onClick={() => activateMutation.mutate(item.datasetId)}>
                  {item.isActive ? "Active" : "Activate"}
                </Button>
                <Button variant="outline" size="sm" disabled={!canManage || archiveMutation.isPending} onClick={() => archiveMutation.mutate({ datasetId: item.datasetId, archived: !item.isArchived })}>
                  <Archive className="h-3.5 w-3.5 mr-1" />
                  {item.isArchived ? "Restore" : "Archive"}
                </Button>
                <Button variant="outline" size="sm" className="border-destructive/50 text-destructive hover:bg-destructive/10" disabled={!canManage || deleteMutation.isPending} onClick={() => deleteMutation.mutate(item.datasetId)}>
                  <Trash2 className="h-3.5 w-3.5 mr-1" />
                  Delete
                </Button>
              </div>
            </div>
            {item.validation?.missingRequired?.length ? (
              <div className="mt-3 rounded-lg border border-warning/40 bg-warning/10 px-3 py-2 text-xs text-warning">
                Missing required mappings: {item.validation.missingRequired.join(", ")}
              </div>
            ) : null}
          </div>
        )) : (
          <p className="text-xs text-muted-foreground">No datasets found for the selected filter.</p>
        )}

        <div className="flex items-center justify-between pt-2">
          {!canManage ? <p className="text-xs text-muted-foreground">Read-only for analyst users.</p> : <span />}
          <p className="text-xs text-muted-foreground">Page {page} of {totalPages}</p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>
              Previous
            </Button>
            <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((current) => current + 1)}>
              Next
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Datasets;
