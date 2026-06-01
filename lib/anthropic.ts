import Anthropic from '@anthropic-ai/sdk'

// Single shared client. The API key is read from the environment on the server
// and never reaches the browser — all model calls go through /app/api/*.
export const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
})

export const hasApiKey = () => Boolean(process.env.ANTHROPIC_API_KEY)
