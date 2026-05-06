import { Mistral } from '@mistralai/mistralai'
import type { AIProvider, AIRequest, AIResponse } from '../types'

function makeMistralProvider(model: string): AIProvider {
  return {
    name: 'mistral',
    models: [model],
    async call(req: AIRequest): Promise<AIResponse> {
      const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY })
      const res = await client.chat.complete({
        model,
        messages: req.messages,
        maxTokens: req.maxTokens ?? 1024,
        temperature: req.temperature ?? 0.7,
      })
      const text = res.choices?.[0]?.message?.content ?? ''
      return { text: typeof text === 'string' ? text : '', provider: 'mistral', model }
    },
  }
}

export const mistralLarge = makeMistralProvider('mistral-large-latest')
export const mistralSmall = makeMistralProvider('mistral-small-latest')
export const mistralNemo = makeMistralProvider('open-mistral-nemo')
