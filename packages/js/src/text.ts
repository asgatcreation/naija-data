// Text matching shared by lookups and fuzzy search. Same rules as the Python and Go packages
// (see fixtures/README.md); only integer arithmetic is used so scores are identical everywhere.

const DROP_TRAILING = new Set(["state", "lga"]);

/** Comparison key: "Akwa-Ibom State" -> "akwaibom", "Ikeja LGA" -> "ikeja". */
export function norm(text: string): string {
  const ascii = text.normalize("NFKD").replace(/[^\x00-\x7f]/g, "").toLowerCase().replace(/&/g, " and ");
  const words = ascii.split(/[^a-z0-9]+/).filter(Boolean);
  while (words.length > 1 && DROP_TRAILING.has(words[words.length - 1])) words.pop();
  return words.join("");
}

/** Optimal string alignment distance (insert, delete, substitute, swap neighbours). */
export function distance(a: string, b: string): number {
  if (a === b) return 0;
  const la = a.length;
  const lb = b.length;
  if (la === 0 || lb === 0) return Math.max(la, lb);
  let prev2: number[] = [];
  let prev = Array.from({ length: lb + 1 }, (_, j) => j);
  for (let i = 1; i <= la; i++) {
    const cur = new Array<number>(lb + 1).fill(0);
    cur[0] = i;
    for (let j = 1; j <= lb; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
        cur[j] = Math.min(cur[j], prev2[j - 2] + 1);
      }
    }
    prev2 = prev;
    prev = cur;
  }
  return prev[lb];
}

/** Similarity of two normalised strings, 0..1000. */
export function score(query: string, term: string): number {
  if (!query || !term) return 0;
  if (query === term) return 1000;
  if (query.length >= 2 && term.startsWith(query)) return 900 + Math.floor((99 * query.length) / term.length);
  const longest = Math.max(query.length, term.length);
  return Math.floor(((longest - distance(query, term)) * 800) / longest);
}

/** Code-point string comparison (same order as Python and Go). */
export function cmp(a: string, b: string): number {
  return a < b ? -1 : a > b ? 1 : 0;
}
