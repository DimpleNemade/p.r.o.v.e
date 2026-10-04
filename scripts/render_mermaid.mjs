import { mkdirSync, readFileSync, unlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, join, relative, resolve } from "node:path";
import { spawnSync } from "node:child_process";

const root = resolve(import.meta.dirname, "..");
const files = process.argv.slice(2);
const out = join(root, "docs", "generated", "mermaid");
mkdirSync(out, { recursive: true });

// CI containers typically run as root with unprivileged user namespaces
// restricted, which Chromium's own sandbox refuses to start under. Disable
// just the browser sandbox there; a local developer run keeps it enabled.
let puppeteerConfigArgs = [];
if (process.env.CI) {
  const config = join(tmpdir(), "prove-mermaid-puppeteer-config.json");
  writeFileSync(
    config,
    JSON.stringify({ args: ["--no-sandbox", "--disable-setuid-sandbox"] }),
  );
  puppeteerConfigArgs = ["--puppeteerConfigFile", config];
}

let rendered = 0;
for (const file of files) {
  const text = readFileSync(file, "utf8");
  const blocks = [...text.matchAll(/```mermaid\s*\n([\s\S]*?)```/g)];
  for (const [index, match] of blocks.entries()) {
    const stem = `${basename(file, ".md")}-${String(index + 1).padStart(2, "0")}`;
    const source = join(out, `${stem}.mmd`);
    const target = join(out, `${stem}.svg`);
    const preview = join(out, `${stem}.png`);
    writeFileSync(source, match[1]);
    const mermaidCli = join(
      root,
      "apps",
      "web",
      "node_modules",
      "@mermaid-js",
      "mermaid-cli",
      "src",
      "cli.js",
    );
    const result = spawnSync(
      process.execPath,
      [mermaidCli, "--input", source, "--output", target, "--quiet", ...puppeteerConfigArgs],
      {
        cwd: join(root, "apps", "web"),
        encoding: "utf8",
      },
    );
    if (result.status !== 0) {
      process.stderr.write(
        `${relative(root, file)} block ${index + 1}: ${result.error || result.stderr || result.stdout}`,
      );
      process.exit(1);
    }
    const previewResult = spawnSync(
      process.execPath,
      [mermaidCli, "--input", source, "--output", preview, "--quiet", "--scale", "1", ...puppeteerConfigArgs],
      { cwd: join(root, "apps", "web"), encoding: "utf8" },
    );
    if (previewResult.status !== 0) {
      process.stderr.write(
        `${relative(root, file)} preview ${index + 1}: ${previewResult.error || previewResult.stderr || previewResult.stdout}`,
      );
      process.exit(1);
    }
    unlinkSync(source);
    rendered += 1;
  }
}
console.log(`Parsed and rendered ${rendered} Mermaid diagrams.`);
