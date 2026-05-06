import type { AIProvider, AIRequest, AIResponse } from './types'
import { anthropicSonnet, anthropicHaiku } from './providers/anthropic'
import { geminiPro, geminiFlash, geminiFlash8b } from './providers/google'
import { groqLlama70b, groqLlama8b, groqMixtral, groqGemma } from './providers/groq'
import { mistralLarge, mistralSmall, mistralNemo } from './providers/mistral'
import { gpt4o, gpt4oMini } from './providers/openai'
import { cohereCommandRPlus, cohereCommandR } from './providers/cohere'
import { ernie4, ernie35, ernieSpeed } from './providers/ernie'

// Order = priority. First available + working provider wins.
// To add a new provider: create src/lib/ai/providers/yourprovider.ts
// implementing AIProvider, then add it to this list.
const DEFAULT_CHAIN: AIProvider[] = [
  anthropicSonnet,
  geminiPro,
  gpt4o,
  groqLlama70b,
  mistralLarge,
  cohereCommandRPlus,
  ernie4,
  // --- fallbacks ---
  anthropicHaiku,
  geminiFlash,
  gpt4oMini,
  groqMixtral,
  groqLlama8b,
  mistralSmall,
  cohereCommandR,
  ernie35,
  geminiFlash8b,
  groqGemma,
  mistralNemo,
  ernieSpeed,
]

export async function callAI(
  req: AIRequest,
  chain: AIProvider[] = DEFAULT_CHAIN
): Promise<AIResponse> {
  const errors: string[] = []

  for (const provider of chain) {
    try {
      const res = await provider.call(req)
      if (res.text) return res
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      errors.push(`[${provider.name}/${provider.models[0]}] ${msg}`)
      console.warn(`AI fallback: ${errors[errors.length - 1]}`)
    }
  }

  throw new Error(`All AI providers failed:\n${errors.join('\n')}`)
}

// Convenience: call with a single user message
export async function ask(prompt: string, chain?: AIProvider[]): Promise<string> {
  const res = await callAI({ messages: [{ role: 'user', content: prompt }] }, chain)
  return res.text
}

export { DEFAULT_CHAIN }
export type { AIProvider, AIRequest, AIResponse }
