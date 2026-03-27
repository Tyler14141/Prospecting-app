export function extractJSON<T>(text: string): T {
  const cleaned = text.replace(/```(?:json)?\s*/gi, '').replace(/```/g, '').trim()
  const start = cleaned.indexOf('[')
  const end = cleaned.lastIndexOf(']')
  if (start === -1 || end === -1 || end <= start) {
    throw new Error('No JSON array found in model response.')
  }
  const jsonStr = cleaned.slice(start, end + 1)
  try {
    return JSON.parse(jsonStr) as T
  } catch {
    const lastComma = jsonStr.lastIndexOf('},')
    if (lastComma > 0) {
      try { return JSON.parse(jsonStr.slice(0, lastComma + 1) + ']') as T } catch { /* fall through */ }
    }
    throw new Error('JSON parse failed — try again.')
  }
}
