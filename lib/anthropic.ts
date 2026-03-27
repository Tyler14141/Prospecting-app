import Anthropic from '@anthropic-ai/sdk'

export const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
})

export function extractJSON<T>(text: string): T {
  // Strip markdown fences
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
    // Attempt salvage of truncated JSON
    const lastComma = jsonStr.lastIndexOf('},')
    if (lastComma > 0) {
      try {
        return JSON.parse(jsonStr.slice(0, lastComma + 1) + ']') as T
      } catch {}
    }
    throw new Error('JSON parse failed. Try again.')
  }
}
