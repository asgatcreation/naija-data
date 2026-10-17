import { defineConfig } from "tsup";

export default defineConfig([
  {
    entry: { index: "src/index.ts", wards: "src/wards.ts", constituencies: "src/constituencies.ts", zod: "src/zod.ts" },
    format: ["esm", "cjs"],
    dts: true,
    clean: true,
    splitting: true,
    treeshake: true,
    target: "es2020",
  },
  {
    entry: { cli: "src/cli.ts" },
    format: ["esm"],
    banner: { js: "#!/usr/bin/env node" },
    // Use the package's own built entry points at runtime instead of bundling a second copy of the data.
    external: ["./index.js", "./wards.js", "./constituencies.js"],
    target: "node20",
  },
]);
