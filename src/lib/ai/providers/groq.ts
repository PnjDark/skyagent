import Groq from 'groq-sdk'
import type { AIProvider, AIRequest, AIResponse } from '../types'

function makeGroqProvider(model: string): AIProvider {
  return {
    name: 'groq',
    models: [model],
    async call(req: AIRequest): Promise<AIResponse> {
      const client = new Groq({ apiKey: process.env.GROQ_API_KEY })
      const res = await client.chat.completions.create({
        model,
        messages: req.messages,
        max_tokens: req.maxTokens ?? 1024,
        temperature: req.temperature ?? 0.7,
      })
      const text = res.choices[0]?.message?.content ?? ''
      return { text, provider: 'groq', model }
    },
  }
}

export const groqLlama70b = makeGroqProvider('llama-3.3-70b-versatile')
export const groqLlama8b = makeGroqProvider('llama3-8b-8192')
export const groqMixtral = makeGroqProvider('mixtral-8x7b-32768')
export const groqGemma = makeGroqProvider('gemma2-9b-it')
