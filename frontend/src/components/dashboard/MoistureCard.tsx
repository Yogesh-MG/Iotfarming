import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Droplets } from "lucide-react";

interface MoistureCardProps {
  moisture: number;
}

const MoistureCard = ({ moisture }: MoistureCardProps) => {
  const getMoistureColor = (value: number) => {
    if (value >= 60) return "text-status-on";
    if (value >= 30) return "text-status-warning";
    return "text-status-off";
  };

  return (
    <Card className="shadow-md transition-smooth hover:shadow-lg">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Soil Moisture</CardTitle>
        <Droplets className="h-5 w-5 text-primary" />
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline gap-2">
          <div className={`text-4xl font-bold ${getMoistureColor(moisture)}`}>
            {moisture}%
          </div>
        </div>
        <div className="mt-4 h-2 bg-muted rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              moisture >= 60
                ? "bg-status-on"
                : moisture >= 30
                ? "bg-status-warning"
                : "bg-status-off"
            }`}
            style={{ width: `${Math.min(moisture, 100)}%` }}
          />
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          {moisture >= 60
            ? "Optimal moisture level"
            : moisture >= 30
            ? "Moderate moisture"
            : "Low moisture - consider watering"}
        </p>
      </CardContent>
    </Card>
  );
};

export default MoistureCard;
