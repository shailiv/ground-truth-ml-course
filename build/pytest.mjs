import { loadPyodide } from "pyodide";
const py = await loadPyodide();
await py.loadPackage(["numpy", "pandas", "scikit-learn"], { messageCallback: () => {} });
console.log(py.runPython(`
import sklearn, pandas, numpy
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
f"sklearn {sklearn.__version__} pandas {pandas.__version__} numpy {numpy.__version__}"
`));
