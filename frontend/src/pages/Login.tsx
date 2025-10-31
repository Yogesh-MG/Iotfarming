import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios, { AxiosError } from "axios";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { toast } from "sonner";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Droplets, Lock, Mail, Loader2 } from "lucide-react";
import { baseUrl } from "@/utils/apiconfig"; // Adjust path if needed, e.g., "../utils/apiconfig"

const loginSchema = z.object({
  email: z.string().email({ message: "Invalid email address" }),
  password: z.string().min(6, { message: "Password must be at least 6 characters" }),
});

type LoginFormValues = z.infer<typeof loginSchema>;

interface UserData {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  full_name: string;
  role: string | null;
  type: "admin" | "user" | null;
  // Add any irrigation-specific fields if needed, e.g., farm_id
}

const Login: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (data: LoginFormValues) => {
    setLoading(true);
    try {
      const instanceKey = localStorage.getItem("instanceKey") || "shared";

      const loginResponse = await axios.post<{ access: string; refresh: string }>(`${baseUrl}/api/token/`, {
        username: data.email,
        password: data.password,
      });

      const { access, refresh } = loginResponse.data;
      localStorage.setItem("token", access);
      localStorage.setItem("refreshToken", refresh);
      localStorage.setItem("instanceKey", instanceKey);

      // Decode token to get user info (basic, or fetch full profile)
      const tokenPayload = JSON.parse(atob(access.split('.')[1]));
      const userFullName = `${tokenPayload.first_name || ''} ${tokenPayload.last_name || ''}`.trim() || data.email;

      // Fetch full user data if needed (adjust endpoint to your Django /api/user/ or similar)
      const userResponse = await axios.get<UserData>(`${baseUrl}/api/me/`, {
        headers: { Authorization: `Bearer ${access}` },
      });
      const user = userResponse.data;

      // Simulate 2-second delay (remove for production to match API time)
      await new Promise(resolve => setTimeout(resolve, 2000));

      toast.success("Login Successful", {
        description: `Welcome back, ${user.full_name || userFullName}!`,
      });

      // Navigate based on user type (adapt to your roles, e.g., admin vs user)
      if (user.type === "admin") {
        navigate("/admin-dashboard"); // Adjust if you have an admin route
      } else {
        navigate("/dashboard");
      }
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      toast.error("Login Failed", {
        description: axiosError.response?.data?.detail || "Invalid credentials. Please check your email and password.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-accent/10" />
      <div className="flex justify-center w-full">
        <Card className="w-full max-w-md relative shadow-lg">
          <CardHeader className="space-y-1 text-center">
            <div className="mx-auto w-16 h-16 bg-primary rounded-full flex items-center justify-center mb-2">
              <Droplets className="w-8 h-8 text-primary-foreground" />
            </div>
            <CardTitle className="text-2xl font-bold">Smart Irrigation Control</CardTitle>
            <CardDescription>
              Enter your credentials to access the system
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Email</FormLabel>
                      <FormControl>
                        <div className="relative">
                          <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                          <Input 
                            placeholder="farmer@example.com" 
                            type="email" 
                            className="pl-10 transition-smooth" 
                            {...field} 
                          />
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Password</FormLabel>
                      <FormControl>
                        <div className="relative">
                          <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                          <Input 
                            placeholder="••••••••" 
                            type="password" 
                            className="pl-10 transition-smooth" 
                            {...field}
                            pattern="^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d!@#$%^&*]{6,}$"  
                            title="Password must be at least 6 characters, including letters and numbers"
                          />
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button type="submit" className="w-full transition-smooth" disabled={loading}>
                  {loading ? (
                    <div className="flex items-center justify-center">
                      <Loader2 className="h-5 w-5 animate-spin mr-2" />
                      Logging In...
                    </div>
                  ) : (
                    "Log In"
                  )}
                </Button>
              </form>
            </Form>
          </CardContent>
          <CardFooter className="flex flex-col">
            <div className="text-center space-y-2 pt-2">
              <button
                type="button"
                className="text-sm text-muted-foreground hover:text-primary transition-smooth"
              >
                Forgot password?
              </button>
              <p className="text-sm text-muted-foreground">
                Don't have an account?{" "}
                <button
                  type="button"
                  className="text-primary hover:underline transition-smooth"
                >
                  Sign up
                </button>
              </p>
            </div>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};

export default Login;