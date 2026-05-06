import type { AIProvider, AIRequest, AIResponse } from '../types'

async function getErnieToken(): Promise<string> {
  const res = await fetch(
    `https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=${process.env.ERNIE_API_KEY}&client_secret=${process.env.ERNIE_SECRET_KEY}`,
    { method: 'POST' }
  )
  const data = await res.json()
  return data.access_token
}

function makeErnieProvider(model: string, endpoint: string): AIProvider {
  return {
    name: 'ernie',
    models: [model],
    async call(req: AIRequest): Promise<AIResponse> {
      const token = await getErnieToken()
      const res = await fetch(
        `https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/${endpoint}?access_token=${token}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: req.messages,
            max_output_tokens: req.maxTokens ?? 1024,
            temperature: req.temperature ?? 0.7,
          }),
        }
      )
      const data = await res.json()
      return { text: data.result ?? '', provider: 'ernie', model }
    },
  }
}

export const ernie4 = makeErnieProvider('ernie-4.0', 'completions_pro')
export const ernie35 = makeErnieProvider('ernie-3.5', 'completions')
export const ernieSpeed = makeErnieProvider('ernie-speed', 'ernie_speed')
