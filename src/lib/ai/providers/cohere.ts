import { CohereClient } from 'cohere-ai'
import type { AIProvider, AIRequest, AIResponse } from '../types'

function makeCohereProvider(model: string): AIProvider {
  return {
    name: 'cohere',
    models: [model],
    async call(req: AIRequest): Promise<AIResponse> {
      const client = new CohereClient({ token: process.env.COHERE_API_KEY })
      const history = req.messages.slice(0, -1).map(m => ({
        role: m.role === 'assistant' ? ('CHATBOT' as const) : ('USER' as const),
        message: m.content,
      }))
      const last = req.messages[req.messages.length - 1]
      const res = await client.chat({
        model,
        chatHistory: history,
        message: last.content,
        maxTokens: req.maxTokens ?? 1024,
        temperature: req.temperature ?? 0.7,
      })
      return { text: res.text, provider: 'cohere', model }
    },
  }
}

export const cohereCommandRPlus = makeCohereProvider('command-r-plus')
export const cohereCommandR = makeCohereProvider('command-r')
