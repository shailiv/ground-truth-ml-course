"""Bring a script and a transcript of its recording to one spelling, so that only real differences remain.

"88 and a half percent" and "88.5%", "the thirties" and "the 30s", "a hundred thousand" and "100,000",
"point nine eight" and "0.98", "here's" and "here is" must all compare equal.
"""
import re

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
DECADES = {"twenties": "20s", "thirties": "30s", "forties": "40s", "fifties": "50s", "sixties": "60s", "seventies": "70s", "eighties": "80s", "nineties": "90s", "teens": "10s"}
ORD = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10}
SCALE = {"hundred": 100, "thousand": 1000, "million": 1000000}
CONTR = {"it's": "it is", "that's": "that is", "here's": "here is", "there's": "there is", "what's": "what is", "you're": "you are", "they're": "they are",
         "we're": "we are", "i'm": "i am", "don't": "do not", "doesn't": "does not", "didn't": "did not", "isn't": "is not", "aren't": "are not", "wasn't": "was not",
         "weren't": "were not", "can't": "can not", "cannot": "can not", "won't": "will not", "wouldn't": "would not", "couldn't": "could not", "shouldn't": "should not",
         "you'll": "you will", "it'll": "it will", "you've": "you have", "we've": "we have", "i've": "i have", "you'd": "you would", "let's": "let us", "who's": "who is",
         "'em": "them", "'bout": "about", "hasn't": "has not", "haven't": "have not", "they've": "they have", "that'll": "that will", "we'll": "we will", "gonna": "going to"}

def _num(tok):
    return re.fullmatch(r"\d+(\.\d+)?", tok) is not None

def words(text):
    t = text.lower().replace("’", "'").replace("%", " percent ").replace("$", " dollars ").replace("&", " and ").replace("−", " minus ")
    t = re.sub(r"(?<=\d),(?=\d{3})", "", t)                       # 4,000 -> 4000
    for a, b in CONTR.items(): t = re.sub(r"(?<![\w'])" + re.escape(a) + r"(?![\w'])", b, t)
    t = re.sub(r"(\d)\s*[-–]\s*(\d)", r"\1 to \2", t)        # 20-30 -> 20 to 30
    t = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", t)                 # 1st -> 1
    t = re.sub(r"(?<![\d])\.(\d)", r"0.\1", t)                    # .98 -> 0.98
    t = re.sub(r"[^a-z0-9.' ]+", " ", t)
    t = re.sub(r"(?<!\d)\.(?!\d)", " ", t)
    t = re.sub(r"'s\b", "", t).replace("'", "")
    toks, out, i = t.split(), [], 0
    while i < len(toks):                                         # number words to digits
        w = toks[i].rstrip(".")
        if w in TENS and i + 1 < len(toks) and toks[i + 1] in ONES[1:10]: out.append(str(TENS[w] + ONES.index(toks[i + 1]))); i += 2; continue
        if w in TENS: out.append(str(TENS[w]))
        elif w in ONES: out.append(str(ONES.index(w)))
        elif w in DECADES: out.append(DECADES[w])
        elif w in ORD: out.append(str(ORD[w]))
        elif w == "a" and i + 1 < len(toks) and toks[i + 1] in SCALE: out.append("1")
        elif re.fullmatch(r"\d+\.0+", w): out.append(w.split(".")[0])
        else: out.append(w)
        i += 1
    res, j = [], 0
    while j < len(out):                                          # "5 hundred 27", "1 hundred thousand", "point 9 8", "3 and a half"
        w = out[j]
        if w == "point" and j + 1 < len(out) and out[j + 1].isdigit():
            k, digits = j + 1, ""
            while k < len(out) and out[k].isdigit() and len(out[k]) == 1: digits += out[k]; k += 1
            if not digits: digits, k = out[j + 1], j + 2
            if res and res[-1].isdigit(): res[-1] = res[-1] + "." + digits
            else: res.append("0." + digits)
            j = k; continue
        if w.isdigit() and j + 1 < len(out) and out[j + 1] in SCALE:      # "6 thousand 7 hundred and 34" -> 6734
            total, cur, k, last = 0, int(w), j + 1, "digit"
            while k < len(out):
                x = out[k]
                if x == "hundred" and last == "digit": cur *= 100; last = "scale"
                elif x in ("thousand", "million") and last in ("digit", "scale"): total += (cur or 1) * SCALE[x]; cur = 0; last = "scale"
                elif x == "and" and last == "scale" and k + 1 < len(out) and out[k + 1].isdigit(): k += 1; continue
                elif x.isdigit() and last == "scale" and int(x) < 1000: cur += int(x); last = "digit"
                else: break
                k += 1
            res.append(str(total + cur)); j = k; continue
        if _num(w) and out[j + 1: j + 4] == ["and", "a", "half"]: res.append(str(float(w) + 0.5).rstrip("0").rstrip(".") if "." in w else w + ".5"); j += 4; continue
        if w in ("a", "1") and j + 1 < len(out) and out[j + 1] in ("half", "quarter"): res.extend(["a", out[j + 1]]); j += 2; continue
        res.append(w); j += 1
    return [w for w in res if w]

if __name__ == "__main__":
    tests = [("88 and a half percent", "88.5%"), ("in the thirties", "in the 30s"), ("a hundred thousand rows", "100,000 rows"), ("an AUC of point nine eight", "an AUC of 0.98"),
             ("five hundred twenty-seven of them", "527 of them"), ("here's why", "here is why"), ("three and a half points", "3.5 points"), ("the first of March", "the 1st of March"),
             ("four thousand advertisers", "4,000 advertisers"), ("two hundred of two hundred", "200 of 200"), ("about 1,300", "about thirteen hundred"), ("0.845", "zero point eight four five"),
             ("six thousand seven hundred and thirty four", "6,734"), ("twenty to thirty percent", "20-30%")]
    bad = 0
    for a, b in tests:
        x, y = words(a), words(b)
        ok = x == y; bad += not ok
        print("ok " if ok else "DIFF", a, "|", b, "" if ok else f"-> {x} vs {y}")
    raise SystemExit(1 if bad else 0)
