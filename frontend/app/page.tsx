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
  const [selectedTemplate, setSelectedTemplate] = useState<string>("template1")


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
    setSelectedTemplate("template1")
  }

  const handleExportPDF = async () => {
    if (!documentContent) {
      alert("Không có dữ liệu để xuất PDF!")
      return
    }
    
    try {
      // Lấy nội dung để xuất PDF
      const printContent = document.getElementById('document-content')
      if (!printContent) {
        alert("Không tìm thấy nội dung để xuất!")
        return
      }
      
      // Tạo một cửa sổ popup bình thường để in
      const printWindow = window.open('', '_blank', 'width=1024,height=768,scrollbars=yes,resizable=yes')
      if (!printWindow) {
        alert("Vui lòng cho phép popup để xuất PDF.")
        return
      }
      
      // Tạo nội dung HTML tối ưu cho PDF
      const htmlContent = `
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8">
            <title>Báo cáo Thẩm định</title>
            <style>
              @page {
                margin: 0.75in;
                size: A4;
              }
              body { 
                font-family: 'Times New Roman', serif; 
                margin: 0; 
                font-size: 12pt;
                line-height: 1.4;
                color: #000;
                background: white;
              }
              .header {
                text-align: center;
                margin-bottom: 25px;
                page-break-after: avoid;
              }
              .header h1 {
                font-size: 16pt;
                margin: 0;
                font-weight: bold;
              }
              table { 
                width: 100%; 
                border-collapse: collapse; 
                margin-bottom: 15px; 
                page-break-inside: avoid;
              }
              th, td { 
                border: 1px solid #000; 
                padding: 6px; 
                text-align: left; 
                vertical-align: top;
                font-size: 11pt;
              }
              th { 
                background-color: #f0f0f0 !important; 
                font-weight: bold;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
              }
              .section-title { 
                font-weight: bold; 
                margin-top: 15px; 
                margin-bottom: 8px; 
                font-size: 13pt;
                page-break-after: avoid;
              }
              h1, h2, h3 { 
                page-break-after: avoid;
              }
              p { 
                margin-bottom: 8px; 
              }
              @media print {
                body { 
                  print-color-adjust: exact;
                  -webkit-print-color-adjust: exact;
                }
                th { 
                  background-color: #f0f0f0 !important;
                }
              }
            </style>
          </head>
          <body>
            <div class="header">
              <h1>BÁO CÁO THẨM ĐỊNH TÍN DỤNG</h1>
            </div>
            ${printContent.innerHTML}
            <div style="margin-top: 30px; page-break-before: always; text-align: center; font-size: 10pt;">
              <p><strong>Báo cáo được tạo tự động bởi hệ thống Thẩm định Techcombank</strong></p>
              <p>© ${new Date().getFullYear()} Techcombank. All rights reserved.</p>
            </div>
          </body>
        </html>
      `
      
      printWindow.document.write(htmlContent)
      printWindow.document.close()
      
      // Đợi load xong rồi tự động in
      printWindow.onload = () => {
        setTimeout(() => {
          printWindow.focus()
          printWindow.print()
        }, 500)
      }
      
      alert("Cửa sổ in đã mở. Hãy chọn 'Save as PDF' hoặc 'Microsoft Print to PDF' để xuất file PDF.")
      
    } catch (error) {
      console.error("Lỗi khi xuất PDF:", error)
      alert("Có lỗi xảy ra khi xuất PDF! Vui lòng thử lại.")
    }
  }

  const handleExportWord = async () => {
    if (!documentContent) {
      alert("Không có dữ liệu để xuất Word!")
      return
    }
    
    try {
      // Lấy nội dung HTML để chuyển đổi
      const printContent = document.getElementById('document-content')
      if (!printContent) {
        alert("Không tìm thấy nội dung để xuất!")
        return
      }
      
      // Tạo nội dung HTML hoàn chỉnh cho Word với căn giữa chính xác
      const htmlContent = `
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset='utf-8'>
            <title>Báo cáo Thẩm định</title>
            <style>
              @page {
                size: A4;
                margin: 1in;
              }
              body { 
                font-family: 'Times New Roman', serif; 
                margin: 0 auto;
                max-width: 8.5in;
                padding: 0;
                font-size: 12pt;
                line-height: 1.5;
                text-align: left;
              }
              .container {
                width: 100%;
                margin: 0 auto;
                padding: 0;
              }
              table { 
                width: 100%; 
                border-collapse: collapse; 
                margin: 0 auto 20px auto;
                table-layout: fixed;
              }
              th, td { 
                border: 1px solid #000; 
                padding: 8px; 
                text-align: left; 
                vertical-align: top;
                word-wrap: break-word;
              }
              th { 
                background-color: #f0f0f0; 
                font-weight: bold;
              }
              .header { 
                text-align: center; 
                margin-bottom: 30px; 
                width: 100%;
              }
              .section-title { 
                font-weight: bold; 
                margin-top: 20px; 
                margin-bottom: 10px; 
                font-size: 14pt;
              }
              h1 { 
                font-size: 18pt; 
                text-align: center; 
                margin: 0 auto 20px auto; 
                width: 100%;
              }
              h2 { 
                font-size: 14pt; 
                margin-top: 20px; 
                margin-bottom: 10px; 
              }
              p { 
                margin-bottom: 10px; 
                text-align: left;
              }
              .center {
                text-align: center;
                margin: 0 auto;
              }
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header center">
                <h1>BÁO CÁO THẨM ĐỊNH TÍN DỤNG</h1>
              </div>
              ${printContent.innerHTML}
              <div style="margin-top: 40px; page-break-before: always; text-align: center;">
                <p><strong>Báo cáo được tạo tự động bởi hệ thống Thẩm định Techcombank</strong></p>
                <p>© ${new Date().getFullYear()} Techcombank. All rights reserved.</p>
              </div>
            </div>
          </body>
        </html>
      `
      
      // Tạo blob với MIME type cho Word document
      const blob = new Blob([htmlContent], { 
        type: 'application/msword' 
      })
      
      // Tạo URL để download
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `Bao_cao_tham_dinh_${new Date().toISOString().slice(0, 10)}.doc`
      
      // Trigger download
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      alert("Xuất Word thành công! File đã được tải về.")
      
    } catch (error) {
      console.error("Lỗi khi xuất Word:", error)
      alert("Có lỗi xảy ra khi xuất Word!")
    }
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
                onExportWord={handleExportWord}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
