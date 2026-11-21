// Runs build/analysis.py and build/analysis2.py under Pyodide (scikit-learn compiled to
// WebAssembly) and writes the facts every lesson quotes plus the downloadable datasets.
import { loadPyodide } from "pyodide";
import fs from "node:fs";

const py = await loadPyodide({ stderr: () => {} });
await py.loadPackage(["numpy", "pandas", "scikit-learn"], { messageCallback: () => {} });
const t0 = Date.now();
const run = (f) => {
  try {
    py.runPython(fs.readFileSync(new URL(f, import.meta.url), "utf8"));
  } catch (e) {
    console.error(String(e.message || e).split("\n").slice(-12).join("\n"));
    process.exit(1);
  }
};
run("./analysis.py");
const [facts, csv, leaky] = py.globals.get("RESULT").toJs();
run("./analysis2.py");
const [facts2, daily] = py.globals.get("RESULT2").toJs();
run("./analysis3.py");
run("./analysis4.py");
const F = { ...JSON.parse(facts), ...JSON.parse(facts2), ...JSON.parse(py.globals.get("RESULT3")), ...JSON.parse(py.globals.get("RESULT4")) };
// text facts (support tickets) are produced separately by build/tickets.py and merged if present
if (fs.existsSync("data/tickets_facts.json")) F.tickets = JSON.parse(fs.readFileSync("data/tickets_facts.json", "utf8"));
fs.mkdirSync("data", { recursive: true });
fs.mkdirSync("site/public/data", { recursive: true });
fs.writeFileSync("data/facts_full.json", JSON.stringify(F));    // everything; build/split_facts.py turns it into facts.json + widgets.json
fs.writeFileSync("site/public/data/advertisers.csv", csv);
fs.writeFileSync("site/public/data/advertisers_with_trap.csv", leaky);
fs.writeFileSync("site/public/data/daily_spend.csv", daily);
import { execSync } from "node:child_process";
console.log(execSync("python build/split_facts.py").toString().trim());
console.log(`done in ${((Date.now() - t0) / 1000).toFixed(0)}s; facts ${(JSON.stringify(F).length / 1024).toFixed(0)} KB; keys: ${Object.keys(F).join(", ")}`);
