import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Static data files (zones.json, exchanges.json, world.geojson, mock-data.json)
// produced by web/scripts/generate_web_data.py and generate_real_data.py live in
// web/public/ and are served from the site root (e.g. /zones.json).
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
  },
  preview: {
    host: true,
    port: 4173,
  },
});
