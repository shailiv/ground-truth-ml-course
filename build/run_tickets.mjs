// Computes the text-lesson facts from data/tickets_raw.json under Pyodide.
import { loadPyodide } from "pyodide";
import fs from "node:fs";

const py = await loadPyodide({ stderr: () => {} });
await py.loadPackage(["numpy", "scikit-learn"], { messageCallback: () => {} });
py.globals.set("RAW", fs.readFileSync("data/tickets_raw.json", "utf8"));
try {
  py.runPython(fs.readFileSync(new URL("./tickets_analysis.py", import.meta.url), "utf8"));
} catch (e) {
  console.error(String(e.message || e).split("\n").slice(-12).join("\n"));
  process.exit(1);
}
const F = JSON.parse(py.globals.get("RESULT"));
fs.writeFileSync("data/tickets_facts.json", JSON.stringify(F, null, 1));
console.log(`tickets ${F.n_tickets}: train ${F.n_train}, test ${F.n_test} (${F.n_test_hard} hard); writers`, JSON.stringify(F.writers));
for (const [k, m] of Object.entries(F.methods)) console.log(k.padEnd(38), m.accuracy, JSON.stringify(m.accuracy_95), "f1", m.macro_f1, "ordinary", m.accuracy_on_ordinary_tickets, "hard", m.accuracy_on_hard_tickets, "no answer", m.no_answer);
for (const p of F.paired.rows) console.log("PAIR", p.a, "-", p.b, p.accuracy_a_minus_b_pts, JSON.stringify(p.ci95_pts), "->", p.clear_winner);
console.log("two llms", JSON.stringify(F.two_llms));
console.log("curve", F.learning_curve.rows.map((r) => `${r.labelled_total}: emb ${r.embeddings_accuracy} bow ${r.bag_of_words_accuracy}`).join(" | "));
console.log("clustering", F.clustering.overall_purity, F.clustering.distinct_dominant_categories, F.clustering.clusters.map((c) => `${c.dominant_category}:${c.purity}`).join(" "));
console.log("nearest", F.nearest_example.average_similarity_same_category, F.nearest_example.average_similarity_other_categories);
