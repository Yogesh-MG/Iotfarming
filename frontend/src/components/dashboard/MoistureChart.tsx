import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { TrendingUp } from "lucide-react";

interface MoistureChartProps {
  data: Array<{ time: string; moisture: number }>;
}

const MoistureChart = ({ data }: MoistureChartProps) => {
  // Format time for XAxis (e.g., "10:30 AM")
  const formatXAxis = (tickItem: string) => new Date(tickItem).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <Card className="shadow-md">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Moisture History</CardTitle>
        <TrendingUp className="h-5 w-5 text-primary" aria-hidden="true" />
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full">
          {data.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="time"
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  tickLine={false}
                  tickFormatter={formatXAxis}
                />
                <YAxis
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  tickLine={false}
                  domain={[0, 100]}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "var(--radius)",
                  }}
                  labelFormatter={formatXAxis}
                />
                <Line
                  type="monotone"
                  dataKey="moisture"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                  dot={{ fill: "hsl(var(--primary))", r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <p>No data available yet. Waiting for sensor readings...</p>
            </div>
          )}
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Last 10 readings (moisture % over time)
        </p>
      </CardContent>
    </Card>
  );
};

export default MoistureChart;