import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { LogOut, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";
import MoistureCard from "@/components/dashboard/MoistureCard";
import MotorStatusCard from "@/components/dashboard/MotorStatusCard";
import PumpControl from "@/components/dashboard/PumpControl";
import MoistureChart from "@/components/dashboard/MoistureChart";
import ActionHistory from "@/components/dashboard/ActionHistory";
import { baseUrl } from "@/utils/apiconfig";

export interface SystemStatus {
  soil_moisture: number;
  motor_status: boolean;
  timestamp: string;
  history?: Array<{ id: number; moisture_level: number; timestamp: string }>;
  actions?: Array<{ id: number; action: string; action_display: string; triggered_by: string; timestamp: string }>;
}

export interface ActionLog {
  id: string;
  action: string;
  timestamp: string;
}

export interface MoistureHistoryItem {
  time: string;
  moisture: number;
}

const Dashboard = () => {
  const navigate = useNavigate();
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [moistureHistory, setMoistureHistory] = useState<Array<MoistureHistoryItem>>([]);
  const [actionHistory, setActionHistory] = useState<ActionLog[]>([]);
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);

  // Check authentication on mount
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/");
    }
  }, [navigate]);

  // Get auth values (re-run on changes)
  const token = localStorage.getItem("token");
  const instanceKey = localStorage.getItem("instanceKey");
  const headers = { 
    Authorization: `Bearer ${token}`,  // Fixed: Added back
  };

  const fetchSystemStatus = async () => {
    if (!token) return;  // Guard
    setIsLoading(true);
    try {
      const response = await axios.get(`${baseUrl}/api/status/`, { headers });
      
      const data = response.data;
      setSystemStatus(data);
      setLastUpdated(new Date().toLocaleTimeString());
      
      // Update moisture history for chart
      if (data.history) {
        setMoistureHistory(
          data.history.slice(-10).map((h: any) => ({
            time: h.timestamp,
            moisture: h.moisture_level,
          }))
        );
      } else {
        setMoistureHistory([]);
      }
      
      // Update action history
      if (data.actions) {
        setActionHistory(
          data.actions.slice(-10).map((a: any) => ({
            id: a.id.toString(),
            action: a.action_display,
            timestamp: a.timestamp,
          }))
        );
      } else {
        setActionHistory([]);
      }
      
      // Low moisture alert
      if (data.soil_moisture < 30) {
        toast.warning("Soil is dry – consider watering!", {
          description: `Current moisture level: ${data.soil_moisture}%`,
        });
      }
    } catch (error: any) {
      toast.error("Failed to fetch system status", {
        description: "Please check your connection and try again.",
      });
      console.error("Error fetching status:", error.response?.data || error);
    } finally {
      setIsLoading(false);
    }
  };

  const updatePumpState = async (state: boolean) => {
    if (!token) return;
    try {
      const response = await axios.post(`${baseUrl}/api/update/`, { pump_state: state }, { headers });

      if (response.status !== 200) throw new Error("Failed to update pump state");

      toast.success(`Pump turned ${state ? "ON" : "OFF"}`);
      
      // Refresh status to update history and everything
      fetchSystemStatus();
    } catch (error: any) {
      toast.error("Failed to update pump state", {
        description: "Please try again.",
      });
      console.error("Error updating pump:", error.response?.data || error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("instanceKey");
    toast.success("Logged out successfully");
    navigate("/");
  };

  // Initial fetch + polling
  useEffect(() => {
    if (token) {
      fetchSystemStatus();
      const interval = setInterval(fetchSystemStatus, 30000);
      return () => clearInterval(interval);
    }
  }, [token]);  // Fixed: Depends on token

  // Refetch on window focus (for app backgrounding in mobile)
  useEffect(() => {
    const handleFocus = () => fetchSystemStatus();
    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, [token]);

  if (!token) return null;  // Guard render

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card border-b border-border shadow-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-primary">Smart Irrigation Control</h1>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={fetchSystemStatus}
              disabled={isLoading}
              className="transition-smooth"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
              className="transition-smooth"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {lastUpdated && (
          <p className="text-sm text-muted-foreground mb-4">
            Last updated: {lastUpdated}
          </p>
        )}

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 mb-6">
          <MoistureCard moisture={systemStatus?.soil_moisture ?? 0} />
          <MotorStatusCard status={systemStatus?.motor_status ?? false} />
          <PumpControl
            currentStatus={systemStatus?.motor_status ?? false}
            onToggle={updatePumpState}
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <MoistureChart data={moistureHistory} />
          <ActionHistory actions={actionHistory} />
        </div>
      </main>
    </div>
  );
};

export default Dashboard;