"""Numbers for the text lessons. Runs under Pyodide; RAW (json text of data/tickets_raw.json) is injected.
Five ways of sorting support tickets into six categories, scored on 450 tickets none of them trained on:
  hand-written keyword rules -> bag-of-words model -> embeddings + simple model -> zero-shot LLM (cheap) -> zero-shot LLM (stronger)
Every score carries an interval, and every neighbouring pair is compared on the same tickets.
"""
import json
import re
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline

D = json.loads(RAW)  # noqa: F821 - injected by the runner
rows = D["rows"]
CATS = ["billing", "tracking_setup", "ad_review", "performance", "account_access", "feature_request"]
tr = [r for r in rows if r["split"] == "train"]
te = [r for r in rows if r["split"] == "test"]
ytr = np.array([CATS.index(r["label"]) for r in tr])
yte = np.array([CATS.index(r["label"]) for r in te])
hard = np.array([r["style"] == "hard" for r in te])
Etr, Ete = np.array([r["emb"] for r in tr]), np.array([r["emb"] for r in te])
rr = lambda x, n=3: round(float(x), n)
rs = np.random.default_rng(0)

# the rule an analyst would write by hand - keyword lists fixed BEFORE looking at any ticket, never tuned
KW = {
    "billing": ["invoice", "charge", "charged", "refund", "payment", "billing", "credit card", "receipt", "vat", "bill"],
    "tracking_setup": ["pixel", "tracking", "tag", "conversion event", "conversions not", "not firing", "gtm", "postback", "events"],
    "ad_review": ["rejected", "disapproved", "approval", "in review", "under review", "policy", "pending review", "flagged"],
    "performance": ["cpa", "performance", "ctr", "roas", "results", "expensive", "dropped", "not delivering", "conversions are", "clicks"],
    "account_access": ["login", "log in", "password", "locked", "access", "2fa", "verification code", "sign in", "permission"],
    "feature_request": ["feature", "would be great", "would love", "request", "suggestion", "any plans", "ability to", "wish"],
}


def by_rules(text):
    t = text.lower()
    hits = [sum(len(re.findall(re.escape(k), t)) for k in KW[c]) for c in CATS]
    return int(np.argmax(hits)) if max(hits) > 0 else -1


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [rr(c - h), rr(c + h)]


PRED = {}


def report(key, pred, name):
    pred = np.asarray(pred)
    PRED[key] = pred
    ok = pred == yte
    cm = confusion_matrix(yte, np.where(pred < 0, len(CATS), pred), labels=list(range(len(CATS) + 1)))[:len(CATS)]
    per = {}
    for i, c in enumerate(CATS):
        tp = int(((pred == i) & (yte == i)).sum())
        per[c] = {"precision": (rr(tp / (pred == i).sum()) if (pred == i).sum() else None), "recall": rr(tp / (yte == i).sum()), "n": int((yte == i).sum())}
    worst = sorted(((int(cm[i, j]), CATS[i], (CATS[j] if j < len(CATS) else "no match")) for i in range(len(CATS)) for j in range(len(CATS) + 1) if i != j and cm[i, j] > 0), reverse=True)[:4]
    return {"method": name, "accuracy": rr(ok.mean()), "correct": int(ok.sum()), "n": int(len(yte)), "accuracy_95": wilson(int(ok.sum()), len(yte)),
            "macro_f1": rr(f1_score(yte, np.where(pred < 0, len(CATS), pred), labels=list(range(len(CATS))), average="macro", zero_division=0)),
            "accuracy_on_ordinary_tickets": rr(ok[~hard].mean()), "accuracy_on_hard_tickets": rr(ok[hard].mean()), "no_answer": int((pred < 0).sum()),
            "per_category": per, "most_common_confusions": [{"count": n, "actual": a, "predicted_as": b} for n, a, b in worst]}


def paired(a, b):
    d = (PRED[a] == yte).astype(float) - (PRED[b] == yte).astype(float)
    bs = [d[rs.integers(0, len(d), len(d))].mean() for _ in range(2000)]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return {"a": a, "b": b, "accuracy_a_minus_b_pts": rr(100 * d.mean(), 1), "ci95_pts": [rr(100 * lo, 1), rr(100 * hi, 1)],
            "tickets_only_a_got_right": int((d > 0).sum()), "tickets_only_b_got_right": int((d < 0).sum()),
            "clear_winner": (a if lo > 0 else b if hi < 0 else None)}


F = {"what": "synthetic advertiser support tickets, written to order by Gemini models (the true category is known because it was requested). Some are deliberately hard (two tangled issues, vague wording): about a quarter of the training tickets and two thirds of the test tickets.",
     "honest_limits": ["a real inbox is messier than this, and real labels are disputed: two people often disagree about the main issue, which caps what any method can score",
                       "the test tickets were written by a different model from the training tickets, but both writers and both LLM classifiers are from the same model family, so the LLM scores are optimistic",
                       "the keyword rules were written once and never tuned; a person iterating on real tickets would do better",
                       "the two trained methods learned from tickets by one writer, a quarter of them hard, and are tested on tickets by another writer, two thirds of them hard - a handicap the instruction-only LLMs do not carry, and a realistic one: training data rarely matches what arrives later"],
     "n_tickets": len(rows), "n_train": len(tr), "n_test": len(te), "n_test_hard": int(hard.sum()), "categories": CATS,
     "per_category_test": {c: int((yte == i).sum()) for i, c in enumerate(CATS)},
     "writers": {"training_tickets": sorted({r["writer"] for r in tr}), "test_tickets": sorted({r["writer"] for r in te})},
     "embedding_model": D.get("embedding_model"), "embedding_dim": D.get("embedding_dim"),
     "examples": [{"label": c, "text": min((r["text"] for r in rows if r["label"] == c and r["style"] == "normal" and len(r["text"]) > 60), key=len)} for c in CATS],
     "hard_examples": [{"label": r["label"], "text": r["text"][:300]} for r in [min((x for x in te if x["style"] == "hard" and x["label"] == c), key=lambda x: len(x["text"])) for c in CATS[:3]]],
     "majority_baseline_accuracy": rr(np.bincount(yte).max() / len(yte))}

bow = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True), LogisticRegression(max_iter=3000, C=10)).fit([r["text"] for r in tr], ytr)
clf = LogisticRegression(max_iter=3000, C=10).fit(Etr, ytr)
llm = lambda key: [CATS.index(r[key]) if r.get(key) in CATS else -1 for r in te]
F["methods"] = {
    "keyword_rules": report("keyword_rules", [by_rules(r["text"]) for r in te], "hand-written keyword rules (never tuned)"),
    "bag_of_words_model": report("bag_of_words_model", bow.predict([r["text"] for r in te]), f"word-and-phrase counts + logistic regression, trained on {len(tr)} labelled tickets"),
    "embeddings_plus_logistic_regression": report("embeddings_plus_logistic_regression", clf.predict(Ete), f"embeddings + logistic regression, trained on {len(tr)} labelled tickets"),
    "llm_zero_shot_cheap": report("llm_zero_shot_cheap", llm("llm_cheap"), f"zero-shot LLM, {D.get('llm_cheap_model')}, no training tickets"),
    "llm_zero_shot_stronger": report("llm_zero_shot_stronger", llm("llm_default"), f"zero-shot LLM, {D.get('llm_default_model')}, no training tickets"),
}
F["models"] = {"cheap": D.get("llm_cheap_model"), "stronger": D.get("llm_default_model")}
F["paired"] = {"method": f"same {len(te)} test tickets, bootstrap interval on the difference in accuracy; an interval that includes 0 is a tie",
               "rows": [paired("bag_of_words_model", "keyword_rules"), paired("embeddings_plus_logistic_regression", "bag_of_words_model"),
                        paired("llm_zero_shot_cheap", "embeddings_plus_logistic_regression"), paired("llm_zero_shot_stronger", "llm_zero_shot_cheap"),
                        paired("llm_zero_shot_stronger", "embeddings_plus_logistic_regression")]}
agree = PRED["llm_zero_shot_cheap"] == PRED["llm_zero_shot_stronger"]
F["two_llms"] = {"what": "where the two LLMs give the same label vs where they differ - disagreement as a cheap flag for human review",
                 "share_agreeing": rr(agree.mean()), "accuracy_when_they_agree": rr((PRED["llm_zero_shot_stronger"] == yte)[agree].mean()),
                 "tickets_where_they_disagree": int((~agree).sum()), "stronger_model_accuracy_when_they_disagree": (rr((PRED["llm_zero_shot_stronger"] == yte)[~agree].mean()) if (~agree).any() else None),
                 "share_of_disagreements_that_are_hard_tickets": (rr(hard[~agree].mean()) if (~agree).any() else None)}

# how many labelled examples does each trained route need?
curve = []
for per_cat in (2, 5, 10, 20, 50, 100):
    a_e, a_b = [], []
    for _ in range(20):
        idx = np.concatenate([rs.choice(np.where(ytr == i)[0], min(per_cat, (ytr == i).sum()), replace=False) for i in range(len(CATS))])
        a_e.append((LogisticRegression(max_iter=3000, C=10).fit(Etr[idx], ytr[idx]).predict(Ete) == yte).mean())
        txt = [tr[j]["text"] for j in idx]
        a_b.append((make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True), LogisticRegression(max_iter=3000, C=10)).fit(txt, ytr[idx]).predict([r["text"] for r in te]) == yte).mean())
    curve.append({"labelled_per_category": per_cat, "labelled_total": per_cat * len(CATS), "embeddings_accuracy": rr(np.mean(a_e)), "embeddings_min": rr(np.min(a_e)), "embeddings_max": rr(np.max(a_e)),
                  "bag_of_words_accuracy": rr(np.mean(a_b)), "bag_of_words_min": rr(np.min(a_b)), "bag_of_words_max": rr(np.max(a_b))})
F["learning_curve"] = {"how": f"train on a random handful of labelled tickets per category, score on the {len(te)} test tickets, 20 repeats each", "rows": curve}

# no labels at all: cluster the embeddings and see whether the topics fall out
Eall = np.vstack([Etr, Ete])
yall = np.concatenate([ytr, yte])
km = KMeans(len(CATS), n_init=10, random_state=0).fit(Eall)
clusters = []
for k in range(len(CATS)):
    mk = km.labels_ == k
    top = np.bincount(yall[mk], minlength=len(CATS))
    clusters.append({"size": int(mk.sum()), "dominant_category": CATS[int(top.argmax())], "purity": rr(top.max() / mk.sum())})
F["clustering"] = {"how": "k-means with k=6 on the embeddings; the category labels were not used", "clusters": sorted(clusters, key=lambda c: -c["size"]),
                   "overall_purity": rr(sum(c["purity"] * c["size"] for c in clusters) / len(yall)),
                   "distinct_dominant_categories": len({c["dominant_category"] for c in clusters}),
                   "caveat": "we asked for six clusters because we knew there were six categories; on a real inbox you would not know the number"}
P = PCA(2, random_state=0).fit_transform(Eall)
pick = rs.choice(len(P), min(360, len(P)), replace=False)
F["map"] = {"how": "each ticket's 256 embedding numbers squashed to 2 so they can be drawn; nearby dots are tickets the model considers similar",
            "x": [rr(P[i, 0], 3) for i in pick], "y": [rr(P[i, 1], 3) for i in pick], "category": [CATS[yall[i]] for i in pick]}
cand = [i for i, r in enumerate(te) if r["label"] == "tracking_setup" and r["style"] == "normal"]
q = min(cand, key=lambda i: abs(len(te[i]["text"]) - 130))          # a short, ordinary ticket to use as the example
sim = Etr @ Ete[q] / (np.linalg.norm(Etr, axis=1) * np.linalg.norm(Ete[q]))
F["nearest_example"] = {"query": te[q]["text"], "query_label": te[q]["label"],
                        "nearest": [{"similarity": rr(sim[i], 3), "label": tr[i]["label"], "text": tr[i]["text"][:170]} for i in np.argsort(-sim)[:3]],
                        "average_similarity_same_category": rr(sim[ytr == yte[q]].mean(), 3), "average_similarity_other_categories": rr(sim[ytr != yte[q]].mean(), 3)}
dis = [r for r in te if r.get("llm_default") != r["label"]][:4]
F["llm_misses"] = [{"text": r["text"][:260], "requested_category": r["label"], "llm_said": r.get("llm_default"), "hard": r["style"] == "hard"} for r in dis]
RESULT = json.dumps(F)
