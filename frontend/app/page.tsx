"use client"

import { useState, useEffect } from "react"
import { Sidebar } from "@/components/sidebar"
import { UploadSection } from "@/components/upload-section"
import { DocumentEditor } from "@/components/document-editor"
import { ChatSection } from "@/components/chat-section"

export default function Page() {
  const [viewMode, setViewMode] = useState<"upload" | "chat">("upload")
  const [documentContent, setDocumentContent] = useState<any>(null)
  const [processedFileIds, setProcessedFileIds] = useState<string[]>([])
  const [collectionName, setCollectionName] = useState<string | null>(null)
  const [selectedTemplate, setSelectedTemplate] = useState<string>("template_1")


  const handleDocumentGenerated = (content: any, fileIds: string[], templateId: string, collectionName: string) => {
    setDocumentContent(content)
    setProcessedFileIds(fileIds)
    setSelectedTemplate(templateId)
    setCollectionName(collectionName) // Lưu collection_name vào state
    setViewMode("chat")
  }

  const handleNewSession = async () => {
    if (collectionName) {
      try {
        await fetch("http://localhost:8000/clear_rag_session", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ collection_name: collectionName }),
        })
      } catch (error) {
        console.error("Failed to clear RAG session:", error)
      }
    }
    setViewMode("upload")
    setDocumentContent(null)
    setProcessedFileIds([])
    setCollectionName(null)
    setSelectedTemplate("template_1")
  }

  const handleExportPDF = () => {
    alert("Xuất PDF thành công!")
  }

  // Effect to clear session on browser tab close
  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (collectionName) {
        // Note: This is a best-effort attempt.
        // Modern browsers may not guarantee the request completes.
        navigator.sendBeacon(
          "http://localhost:8000/clear_rag_session",
          JSON.stringify({ collection_name: collectionName })
        );
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [collectionName]);


  return (
    <div className="h-screen flex bg-gradient-to-br from-red-50 to-red-100 overflow-hidden">
      {/* <div className="hidden lg:block">
        <Sidebar />
      </div> */}

      <main className="flex-1 flex flex-col overflow-y-auto">
        {viewMode === "upload" ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            <div className="w-full max-w-4xl mx-auto">
              <h1 className="text-3xl font-bold text-center text-gray-800 mb-2">
                Bắt đầu một phiên Thẩm định mới
              </h1>
              <p className="text-center text-gray-500 mb-8">
                Tải lên các tài liệu cần thiết để hệ thống phân tích và tạo báo cáo.
              </p>
              <UploadSection
                onDocumentGenerated={handleDocumentGenerated}
              />
            </div>
          </div>
        ) : (
          <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 h-full overflow-hidden">
            <div className="flex flex-col h-full bg-white border-r border-gray-200 overflow-y-auto">
              <ChatSection
                fileIds={processedFileIds}
                onNewSession={handleNewSession}
                collectionName={collectionName}
                setCollectionName={setCollectionName}
              />
            </div>
            <div className="flex flex-col h-full overflow-y-auto">
              <DocumentEditor
                content={documentContent}
                templateId={selectedTemplate}
                onExportPDF={handleExportPDF}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
