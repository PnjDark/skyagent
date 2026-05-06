import OpenAI from 'openai'
import type { AIProvider, AIRequest, AIResponse } from '../types'

function makeOpenAIProvider(model: string): AIProvider {
  return {
    name: 'openai',
    models: [model],
    async call(req: AIRequest): Promise<AIResponse> {
      const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })
      const res = await client.chat.completions.create({
        model,
        messages: req.messages,
        max_tokens: req.maxTokens ?? 1024,
        temperature: req.temperature ?? 0.7,
      })
      const text = res.choices[0]?.message?.content ?? ''
      return { text, provider: 'openai', model }
    },
  }
}

export const gpt4o = makeOpenAIProvider('gpt-4o')
export const gpt4oMini = makeOpenAIProvider('gpt-4o-mini')
