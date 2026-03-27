export function extractJSON<T = unknown>(text: string): T {
  // Strip all markdown code fences
  const cleaned = text.replace(/```(?:json)?\s*/gi, '').replace(/```/g, '').trim()
  const start = cleaned.indexOf('[')
  const end = cleaned.lastIndexOf(']')
  if (start === -1 || end === -1 || end <= start) {
    throw new Error('No JSON array found in response.')
  }
  const jsonStr = cleaned.slice(start, end + 1)
  try {
    return JSON.parse(jsonStr) as T
  } catch {
    // Salvage truncated JSON
    const lastComma = jsonStr.lastIndexOf('},')
    if (lastComma > 0) {
      try { return JSON.parse(jsonStr.slice(0, lastComma + 1) + ']') as T } catch {}
    }
    throw new Error('JSON parse failed — please retry.')
  }
}
