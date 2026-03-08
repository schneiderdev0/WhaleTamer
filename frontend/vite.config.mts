import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/auth": "http://localhost:8000",
      "/generate": "http://localhost:8000",
      "/collector": "http://localhost:8000",
      "/projects": "http://localhost:8000",
      "/reports": "http://localhost:8000",
      "/telegram": "http://localhost:8000"
    }
  }
});
