import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";
import path from "path";

export default defineConfig({
  plugins: [tailwindcss(), tsconfigPaths()],
  // Explicitly set the project root
  root: path.resolve(__dirname),
  // Configure the dev server
  server: {
    // The base URL for assets during development
    base: "/static/frontend/",
    // The port for the Vite dev server
    port: 5173,
    // Enable strict port checking
    strictPort: true,
  },
  build: {
    // Set the output directory for the build
    outDir: path.resolve(__dirname, "../sylvan_library/frontend/static"),
    // Ensure the output directory is emptied before each build
    emptyOutDir: true,
    // The base URL for assets in the production build
    base: "/static/frontend/",
    rollupOptions: {
      // Specify the entry point of your React application
      input: path.resolve(__dirname, "app/index.tsx"),
      output: {
        // Define the name of the output file to match the Django template
        entryFileNames: "main.js",
        // Define the names for any additional chunks (if any)
        chunkFileNames: "[name].js",
        // Define the names for any assets
        assetFileNames: "[name].[ext]",
      },
    },
  },
});
