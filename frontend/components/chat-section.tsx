"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send, Bot, User, Loader2, RefreshCw, MessageSquare } from "lucide-react"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
}

interface ChatSectionProps {
  fileIds: string[]
  onNewSession: () => void
  collectionName: string | null
  setCollectionName: (name: string | null) => void
}

export function ChatSection({ fileIds, onNewSession, collectionName, setCollectionName }: ChatSectionProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    // Reset chat when fileIds change (new session)
    setMessages([])
  }, [fileIds])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim()
    }

    setMessages(prev => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      const response = await fetch("http://localhost:8000/chat_rag", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: userMessage.content,
          file_ids: fileIds,
          collection_name: collectionName,
          chat_history: messages.map(m => ({
            role: m.role,
            content: m.content
          }))
        }),
      })

      if (!response.ok) {
        throw new Error(`Chat failed: ${response.statusText}`)
      }

      const result = await response.json()

      if (result.collection_name && !collectionName) {
        setCollectionName(result.collection_name)
      }

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: result.answer || "Xin lỗi, tôi không thể trả lời câu hỏi này."
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error("Chat error:", error)
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: "Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại sau."
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="bg-white h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <MessageSquare className="h-5 w-5 text-red-600" />
          <h3 className="font-semibold text-gray-900">
            Hỏi đáp về Tài liệu
          </h3>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={onNewSession}
          className="text-gray-600 hover:text-red-600"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Phiên mới
        </Button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-8 h-full flex flex-col justify-center items-center">
            <div className="bg-red-100 p-4 rounded-full">
              <Bot className="h-10 w-10 text-red-500" />
            </div>
            <h4 className="text-lg font-medium text-gray-700 mt-4 mb-2">Bắt đầu cuộc hội thoại</h4>
            <p className="text-gray-500 text-sm max-w-xs mx-auto">
              Đặt câu hỏi về các tài liệu đã được phân tích để nhận được câu trả lời từ AI.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className="flex gap-3">
            <div className="flex-shrink-0">
              {message.role === "user" ? (
                <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                  <User className="h-4 w-4 text-gray-600" />
                </div>
              ) : (
                <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center">
                  <Bot className="h-4 w-4 text-white" />
                </div>
              )}
            </div>
            <div className="flex-1">
              <div className={`rounded-lg p-3 text-sm ${
                message.role === "user" 
                  ? "bg-gray-100" 
                  : "bg-white border border-gray-200"
              }`}>
                <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                  {message.content}
                </p>
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center">
              <Loader2 className="h-4 w-4 text-white animate-spin" />
            </div>
            <div className="flex-1">
              <div className="bg-white rounded-lg p-3 border border-gray-200">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 text-red-600 animate-spin" />
                  <span className="text-sm text-red-700 font-medium">Đang tìm kiếm thông tin...</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4 bg-white">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <div className="flex-1 relative">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Hỏi về nội dung tài liệu..."
              className="pr-12 h-10"
              disabled={isLoading}
            />
            <Button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="absolute right-1 top-1/2 -translate-y-1/2 w-8 h-8 rounded-md bg-red-600 hover:bg-red-700 p-0"
            >
              <Send className="h-4 w-4 text-white" />
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
