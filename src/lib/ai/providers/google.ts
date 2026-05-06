import { GoogleGenerativeAI } from '@google/generative-ai'
import type { AIProvider, AIRequest, AIResponse } from '../types'

function makeGeminiProvider(model: string): AIProvider {
  return {
    name: 'google',
    models: [model],
    async call(req: AIRequest): Promise<AIResponse> {
      const genAI = new GoogleGenerativeAI(process.env.GOOGLE_AI_API_KEY!)
      const gemini = genAI.getGenerativeModel({ model })
      const chat = gemini.startChat({
        history: req.messages.slice(0, -1).map(m => ({
          role: m.role === 'assistant' ? 'model' : 'user',
          parts: [{ text: m.content }],
        })),
      })
      const last = req.messages[req.messages.length - 1]
      const result = await chat.sendMessage(last.content)
      return { text: result.response.text(), provider: 'google', model }
    },
  }
}

export const geminiPro = makeGeminiProvider('gemini-1.5-pro')
export const geminiFlash = makeGeminiProvider('gemini-1.5-flash')
export const geminiFlash8b = makeGeminiProvider('gemini-1.5-flash-8b')
