// Default to local dev if no env variable is set
const getBaseUrl = (): string => {
  // For Vite: use import.meta.env
  const apiUrl = import.meta.env?.VITE_API_URL;

  // For Create React App: use process.env
  // const apiUrl = process.env.REACT_APP_API_URL;

  // Check instanceKey for local multi-tenant setup, fallback to env or local
  const instanceKey = localStorage.getItem("instanceKey") || "shared";
  
  // If env variable exists (cloud deployment), use it
  if (apiUrl) {
    return apiUrl; // e.g., "https://your-api.cloud-provider.com"
  }

  // Local dev fallback with instanceKey
  return instanceKey === "shared" 
    ? "https://iotagri.pythonanywhere.com" 
    : `https://${instanceKey}.twistar.pythonanywhere.com/`;
};

export const baseUrl = getBaseUrl();