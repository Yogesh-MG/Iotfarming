import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Power } from "lucide-react";

interface MotorStatusCardProps {
  status: boolean;
}

const MotorStatusCard = ({ status }: MotorStatusCardProps) => {
  return (
    <Card className="shadow-md transition-smooth hover:shadow-lg">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Motor Status</CardTitle>
        <Power 
          className={`h-5 w-5 ${status ? "text-status-on" : "text-status-off"}`} 
          aria-hidden="true"
        />
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-3">
          <div
            className={`w-4 h-4 rounded-full ${
              status ? "bg-status-on" : "bg-status-off"
            } ${status ? "animate-pulse" : ""}`}
            aria-hidden="true"
          />
          <div className={`text-3xl font-bold ${status ? "text-status-on" : "text-status-off"}`}>
            {status ? "ON" : "OFF"}
          </div>
        </div>
        <p className="text-xs text-muted-foreground mt-4" aria-live="polite">
          {status ? "Pump is currently running" : "Pump is currently stopped"}
        </p>
      </CardContent>
    </Card>
  );
};

export default MotorStatusCard;