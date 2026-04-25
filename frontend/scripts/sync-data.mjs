import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const source = path.resolve(__dirname, "../../data/processed/all_clips.json");
const targetDir = path.resolve(__dirname, "../public/data");
const target = path.resolve(targetDir, "all_clips.json");

if (!existsSync(source)) {
  process.stdout.write(`[sync-data] source file missing: ${source}\n`);
  process.exit(0);
}

mkdirSync(targetDir, { recursive: true });
copyFileSync(source, target);
process.stdout.write(`[sync-data] copied ${source} -> ${target}\n`);
