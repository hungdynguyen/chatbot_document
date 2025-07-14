// Trong file: app/chat/page.tsx

"use client"

import { useChat } from "ai/react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send, Bot, User, Loader2, MessageSquare, ArrowLeft } from "lucide-react"
import { useState, useEffect } from "react"
import Link from 'next/link'

// Giao diện chat RAG độc lập
export default function ChatPage() {
  const [fileIdsForRag, setFileIdsForRag] = useState<string[]>([]);
  
  // Lấy file_ids từ localStorage khi component được mount
  useEffect(() => {
    const storedFileIds = localStorage.getItem('ragFileIds');
    if (storedFileIds) {
      setFileIdsForRag(JSON.parse(storedFileIds));
    }
  }, []);

  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: "/api/chat_with_docs", // API RAG
    body: {
      file_ids: fileIdsForRag, // Gửi kèm file_ids
    },
    // Chỉ bắt đầu chat khi đã có file_ids
    initialMessages: fileIdsForRag.length > 0 
      ? [{ id: 'welcome', role: 'assistant', content: 'Bạn có thể hỏi bất cứ điều gì về các tài liệu đã được xử lý.' }]
      : [{ id: 'no-docs', role: 'assistant', content: 'Chưa có tài liệu nào được chọn để hỏi đáp. Vui lòng quay lại trang thẩm định và xử lý tài liệu trước.' }]
  });

  return (
    <div className="flex flex-col h-screen bg-white">
        {/* Header của trang Chat */}
        <header className="p-4 border-b flex items-center justify-between bg-gray-50">
            <h1 className="text-xl font-semibold flex items-center gap-2 text-gray-800">
                <MessageSquare className="text-red-500"/>
                Trợ lý Hỏi-Đáp Tài liệu
            </h1>
            <Button asChild variant="outline">
                <Link href="/">
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Quay lại trang Thẩm định
                </Link>
            </Button>
        </header>

        {/* Khu vực hiển thị tin nhắn */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.map((m) => (
                <div key={m.id} className={`flex items-end gap-3 ${m.role === 'user' ? 'justify-end' : ''}`}>
                   {m.role !== 'user' && <div className="w-8 h-8 bg-red-gradient rounded-full flex items-center justify-center flex-shrink-0"><Bot className="h-4 w-4 text-white"/></div>}
                   <div className={`max-w-xl p-4 rounded-lg shadow-sm ${m.role === 'user' ? 'bg-red-500 text-white' : 'bg-gray-100 text-gray-800'}`}>
                        <p className="text-sm leading-relaxed">{m.content}</p>
                   </div>
                   {m.role === 'user' && <div className="w-8 h-8 bg-gray-400 rounded-full flex items-center justify-center flex-shrink-0"><User className="h-4 w-4 text-white"/></div>}
                </div>
            ))}
             {isLoading && <div className="flex justify-center"><Loader2 className="h-6 w-6 animate-spin text-red-500"/></div>}
        </div>
        
        {/* Ô nhập liệu */}
        <div className="border-t p-4 bg-gray-50">
            <form onSubmit={handleSubmit} className="flex gap-2">
                <Input
                    value={input}
                    onChange={handleInputChange}
                    placeholder={fileIdsForRag.length > 0 ? "Nhập câu hỏi của bạn..." : "Vui lòng xử lý tài liệu trước..."}
                    className="flex-1"
                    disabled={isLoading || fileIdsForRag.length === 0}
                />
                <Button type="submit" disabled={isLoading || !input.trim()}>
                    <Send className="h-4 w-4" />
                </Button>
            </form>
        </div>
    </div>
  )
}