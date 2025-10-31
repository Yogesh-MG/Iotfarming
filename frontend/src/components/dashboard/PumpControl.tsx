import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Settings } from "lucide-react";
import { useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { baseUrl } from "@/utils/apiconfig";

interface PumpControlProps {
  currentStatus: boolean;
  onToggle: (state: boolean) => void;
}

const PumpControl = ({ currentStatus, onToggle }: PumpControlProps) => {
  const [isAutoMode, setIsAutoMode] = useState(false);  // New: Track auto mode

  const token = localStorage.getItem("token");
  const instanceKey = localStorage.getItem("instanceKey");
  const headers = { 
    Authorization: `Bearer ${token}`, 
    ...(instanceKey && { 'X-Instance-Key': instanceKey }) 
  };

  const handleAutoToggle = async (autoEnabled: boolean) => {
    if (!token) {
      toast.error("No authentication token found");
      return;
    }
    try {
      const response = await axios.post(`${baseUrl}/api/auto-mode/`, { enabled: autoEnabled }, { headers });
      
      if (response.status !== 200) throw new Error("Failed to update auto mode");

      setIsAutoMode(autoEnabled);
      toast.success(autoEnabled ? "Auto mode enabled" : "Manual mode enabled");
    } catch (error: any) {
      toast.error("Failed to update auto mode", {
        description: error.response?.data?.detail || "Please try again.",
      });
      console.error("Error updating auto mode:", error.response?.data || error);
    }
  };

  return (
    <Card className="shadow-md transition-smooth hover:shadow-lg">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Pump Control</CardTitle>
        <Settings className="h-5 w-5 text-primary" aria-hidden="true" />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Manual Toggle */}
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="pump-switch" className="text-base font-medium">
                Manual Control
              </Label>
              <p className="text-xs text-muted-foreground">Toggle pump on/off</p>
            </div>
            <Switch
              id="pump-switch"
              checked={currentStatus}
              onCheckedChange={onToggle}
              disabled={isAutoMode}  // Disable in auto mode
              className="data-[state=checked]:bg-status-on"
              aria-label="Toggle pump manually"
            />
          </div>
          {/* Auto Mode Toggle */}
          <div className="flex items-center justify-between pt-2 border-t">
            <div className="space-y-1">
              <Label htmlFor="auto-switch" className="text-base font-medium">
                Auto Mode
              </Label>
              <p className="text-xs text-muted-foreground">
                Automatically control based on moisture levels
              </p>
            </div>
            <Switch
              id="auto-switch"
              checked={isAutoMode}
              onCheckedChange={handleAutoToggle}
              className="data-[state=checked]:bg-status-on"
              aria-label="Enable auto mode"
            />
          </div>
        </div>
        <div className="mt-4 p-3 bg-accent rounded-lg">
          <p className="text-xs text-accent-foreground">
            💡 Auto mode turns the pump ON if moisture less than 30% and OFF if more than 60%
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default PumpControl;