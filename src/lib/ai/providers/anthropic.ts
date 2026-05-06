import Anthropic from '@anthropic-ai/sdk'
import type { AIProvider, AIRequest, AIResponse } from '../types'

function makeAnthropicProvider(model: string): AIProvider {
  return {
    name: 'anthropic',
    models: [model],
    async call(req: AIRequest): Promise<AIResponse> {
      const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })
      const res = await client.messages.create({
        model,
        max_tokens: req.maxTokens ?? 1024,
        messages: req.messages,
      })
      const text = res.content[0].type === 'text' ? res.content[0].text : ''
      return { text, provider: 'anthropic', model }
    },
  }
}

export const anthropicSonnet = makeAnthropicProvider('claude-3-5-sonnet-20241022')
export const anthropicHaiku = makeAnthropicProvider('claude-3-haiku-20240307')
