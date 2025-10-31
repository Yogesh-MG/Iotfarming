import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Clock } from "lucide-react";
import { toast } from "sonner";  // If needed for future
import type { ActionLog } from "@/pages/Dashboard";

interface ActionHistoryProps {
  actions: ActionLog[];
}

const ActionHistory = ({ actions }: ActionHistoryProps) => {
  // Format timestamp if full ISO (e.g., to "10:30 AM")
  const formatTimestamp = (ts: string) => new Date(ts).toLocaleString();

  return (
    <Card className="shadow-md">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Action History</CardTitle>
        <Clock className="h-5 w-5 text-primary" aria-hidden="true" />
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[300px] w-full pr-4">
          {actions.length > 0 ? (
            <div className="space-y-3">
              {actions.map((action) => (
                <div
                  key={action.id}  // Ensure unique key
                  className="flex items-start gap-3 p-3 bg-accent rounded-lg transition-smooth hover:bg-accent/80"
                >
                  <div className="w-2 h-2 rounded-full bg-primary mt-2 flex-shrink-0" aria-hidden="true" />
                  <div className="flex-1 space-y-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">
                      {action.action}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatTimestamp(action.timestamp)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <p>No actions recorded yet</p>
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

export default ActionHistory;