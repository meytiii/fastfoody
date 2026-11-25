const PERSIAN_YEH = '\u06cc'
const ARABIC_YEH = '\u064a'
const PERSIAN_KAF = '\u06a9'
const ARABIC_KAF = '\u0643'

const DIGIT_MAP: Record<string, string> = {
  '\u0660': '0',
  '\u0661': '1',
  '\u0662': '2',
  '\u0663': '3',
  '\u0664': '4',
  '\u0665': '5',
  '\u0666': '6',
  '\u0667': '7',
  '\u0668': '8',
  '\u0669': '9',
  '\u06f0': '0',
  '\u06f1': '1',
  '\u06f2': '2',
  '\u06f3': '3',
  '\u06f4': '4',
  '\u06f5': '5',
  '\u06f6': '6',
  '\u06f7': '7',
  '\u06f8': '8',
  '\u06f9': '9',
}

const INVISIBLE_CHARS = /[\u200c\u200d\u200e\u200f\u0640]/g

export const MAX_SEARCH_LENGTH = 100
export const MAX_SEARCH_TOKENS = 8

export const SYNONYM_GROUPS: readonly (readonly string[])[] = [
  ['برگر', 'همبرگر'],
  ['مرغ', 'چیکن', 'جوجه'],
  ['نوشابه', 'نوشیدنی', 'کوکاکولا', 'کوکا', 'پپسی'],
  ['سیبزمینی', 'فرای', 'فریز'],
  ['سوسیس', 'هاتداگ'],
  ['پنیر', 'چیز'],
  ['قارچ', 'ماشروم'],
  ['میگو', 'shrimp'],
]

export function normalizeSearchQuery(raw: string | undefined | null): string {
  if (!raw) return ''
  let text = String(raw).replace(/[\u0660-\u0669\u06f0-\u06f9]/g, ch => DIGIT_MAP[ch] ?? ch)
  text = text.replaceAll(ARABIC_YEH, PERSIAN_YEH).replaceAll(ARABIC_KAF, PERSIAN_KAF)
  text = text.replace(INVISIBLE_CHARS, '')
  text = text.replace(/\s+/g, ' ').trim()
  return text.slice(0, MAX_SEARCH_LENGTH)
}

export function tokenizeSearchQuery(term: string): string[] {
  return term
    .split(' ')
    .map(t => t.trim())
    .filter(Boolean)
    .slice(0, MAX_SEARCH_TOKENS)
}

export function searchVariants(term: string): string[] {
  if (!term) return []
  const variants = new Set<string>([term])
  if (term.includes(PERSIAN_YEH) || term.includes(PERSIAN_KAF)) {
    variants.add(term.replaceAll(PERSIAN_YEH, ARABIC_YEH))
    variants.add(term.replaceAll(PERSIAN_KAF, ARABIC_KAF))
    variants.add(term.replaceAll(PERSIAN_YEH, ARABIC_YEH).replaceAll(PERSIAN_KAF, ARABIC_KAF))
  }
  return Array.from(variants).filter(Boolean).sort()
}

function buildSynonymMap(): Map<string, string[]> {
  const map = new Map<string, Set<string>>()
  for (const group of SYNONYM_GROUPS) {
    const normalized = group.map(m => normalizeSearchQuery(m).toLowerCase()).filter(Boolean)
    for (const member of normalized) {
      if (!map.has(member)) {
        map.set(member, new Set())
      }
      const bucket = map.get(member)!
      for (const peer of normalized) {
        if (peer !== member) bucket.add(peer)
      }
    }
  }
  const result = new Map<string, string[]>()
  for (const [k, v] of map.entries()) {
    result.set(k, Array.from(v).sort())
  }
  return result
}

const SYNONYM_MAP = buildSynonymMap()

function expandToken(token: string): string[] {
  const expanded: string[] = []
  for (const variant of searchVariants(token)) {
    expanded.push(variant)
    const syns = SYNONYM_MAP.get(variant.toLowerCase()) || []
    expanded.push(...syns)
  }
  const seen = new Set<string>()
  const out: string[] = []
  for (const c of expanded) {
    if (c && !seen.has(c)) {
      seen.add(c)
      out.push(c)
    }
  }
  return out.slice(0, 8)
}

export interface SearchableProductRecord {
  name: string
  slug: string
  description: string
  categoryName: string
}

export function matchesSearchTerm(record: SearchableProductRecord, term: string): boolean {
  const tokens = tokenizeSearchQuery(term)
  if (tokens.length === 0) return true

  const haystack = [
    record.name,
    record.slug,
    record.description,
    record.categoryName,
  ].map(s => normalizeSearchQuery(s).toLowerCase())

  return tokens.every(token => {
    const candidates = expandToken(token)
    return candidates.some(candidate => {
      const needle = candidate.toLowerCase()
      return haystack.some(field => field.includes(needle))
    })
  })
}

export function computeRelevanceScore(record: SearchableProductRecord, term: string): number {
  const variants = searchVariants(term)
  const name = normalizeSearchQuery(record.name).toLowerCase()
  const slug = normalizeSearchQuery(record.slug).toLowerCase()
  const desc = normalizeSearchQuery(record.description).toLowerCase()
  const cat = normalizeSearchQuery(record.categoryName).toLowerCase()

  for (const variant of variants) {
    const v = variant.toLowerCase()
    if (name === v) return 5
  }
  for (const variant of variants) {
    const v = variant.toLowerCase()
    if (name.startsWith(v)) return 4
  }
  for (const variant of variants) {
    const v = variant.toLowerCase()
    if (name.includes(v)) return 3
  }
  for (const variant of variants) {
    const v = variant.toLowerCase()
    if (slug.includes(v) || cat.includes(v) || desc.includes(v)) return 2
  }
  return 0
}

function similarityRatio(a: string, b: string): number {
  if (a === b) return 1
  if (!a.length || !b.length) return 0
  const m = a.length
  const n = b.length
  const dp: number[][] = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0))
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (a[i - 1] === b[j - 1]) {
        dp[i]![j] = dp[i - 1]![j - 1]! + 1
      } else {
        dp[i]![j] = Math.max(dp[i - 1]![j]!, dp[i]![j - 1]!)
      }
    }
  }
  const lcs = dp[m]![n]!
  return (2 * lcs) / (m + n)
}

export function suggestCorrectedTerm(
  term: string,
  vocabularyWords: string[],
  cutoff = 0.72
): string | null {
  const tokens = tokenizeSearchQuery(term)
  if (tokens.length === 0) return null

  let changed = false
  const correctedTokens = tokens.map(token => {
    if (token.length < 3) return token
    const lowerToken = token.toLowerCase()
    if (vocabularyWords.some(w => w.toLowerCase() === lowerToken)) return token

    let bestWord = token
    let bestScore = cutoff
    for (const candidate of vocabularyWords) {
      const score = similarityRatio(lowerToken, candidate.toLowerCase())
      if (score >= bestScore) {
        bestScore = score
        bestWord = candidate
      }
    }
    if (bestWord !== token) {
      changed = true
    }
    return bestWord
  })

  return changed ? correctedTokens.join(' ') : null
}
