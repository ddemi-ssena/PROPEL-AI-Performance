const MOJIBAKE_MARKERS = /[\u00c2-\u00c5\u00d0\u00e2\u00ef\ufffd]/

const TEXT_DECODER = typeof TextDecoder !== 'undefined'
  ? new TextDecoder('utf-8', { fatal: true })
  : null

const TARGETED_REPLACEMENTS: Array<[RegExp, string]> = [
  [/\u00c3[\u2013\u0096]/g, '\u00d6'],
  [/\u00c3[\u0152\u009c]/g, '\u00dc'],
  [/\u00c3[\u00bc\u00c2\u00bc]/g, '\u00fc'],
  [/\u00c3[\u00b6\u00c2\u00b6]/g, '\u00f6'],
  [/\u00c3[\u00a7\u00c2\u00a7]/g, '\u00e7'],
  [/\u00c3[\u2021\u0087]/g, '\u00c7'],
  [/\u00c4[\u00b1\u00c2\u00b1]/g, '\u0131'],
  [/\u00c4[\u00b0\u00c2\u00b0]/g, '\u0130'],
  [/\u00c4[\u0178\u009f]/g, '\u011f'],
  [/\u00c4[\u017d\u009e]/g, '\u011e'],
  [/\u00c5[\u0178\u009f]/g, '\u015f'],
  [/\u00c5[\u017d\u009e]/g, '\u015e'],
  [/\u00e2\u20ac\u2122/g, "'"],
  [/\u00e2\u20ac\u0153/g, '"'],
  [/\u00e2\u20ac\u009d/g, '"'],
]

function decodeUtf8BytesFromLatin1(value: string) {
  if (!TEXT_DECODER) return value

  const bytes: number[] = []
  for (const char of value) {
    const code = char.charCodeAt(0)
    if (code > 255) return value
    bytes.push(code)
  }

  try {
    return TEXT_DECODER.decode(new Uint8Array(bytes))
  } catch {
    return value
  }
}

export function repairMojibakeText(value: string): string
export function repairMojibakeText(value: null): null
export function repairMojibakeText(value: undefined): undefined
export function repairMojibakeText(value: string | null | undefined) {
  if (!value || !MOJIBAKE_MARKERS.test(value)) return value

  let repaired = value
  for (const [pattern, replacement] of TARGETED_REPLACEMENTS) {
    repaired = repaired.replace(pattern, replacement)
  }

  for (let index = 0; index < 3; index += 1) {
    const decoded = decodeUtf8BytesFromLatin1(repaired)
    if (decoded === repaired || !MOJIBAKE_MARKERS.test(decoded)) {
      repaired = decoded
      break
    }
    repaired = decoded
  }

  for (const [pattern, replacement] of TARGETED_REPLACEMENTS) {
    repaired = repaired.replace(pattern, replacement)
  }

  return repaired
}

export function repairMojibakeDeep<T>(value: T, seen = new WeakSet<object>()): T {
  if (typeof value === 'string') {
    return repairMojibakeText(value) as T
  }

  if (!value || typeof value !== 'object') return value

  if (value instanceof Blob || value instanceof ArrayBuffer || value instanceof Date) {
    return value
  }

  if (seen.has(value)) return value
  seen.add(value)

  if (Array.isArray(value)) {
    return value.map((item) => repairMojibakeDeep(item, seen)) as T
  }

  for (const [key, item] of Object.entries(value)) {
    ;(value as Record<string, unknown>)[key] = repairMojibakeDeep(item, seen)
  }

  return value
}
