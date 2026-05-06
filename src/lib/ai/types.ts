export interface AIMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface AIRequest {
  messages: AIMessage[]
  maxTokens?: number
  temperature?: number
}

export interface AIResponse {
  text: string
  provider: string
  model: string
}

export interface AIProvider {
  name: string
  models: string[]
  call(req: AIRequest): Promise<AIResponse>
}
