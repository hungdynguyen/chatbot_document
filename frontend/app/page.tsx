"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Sidebar } from "@/components/sidebar"
import { UploadSection } from "@/components/upload-section"
import { DocumentEditor } from "@/components/document-editor"
import { FileText, Plus, Upload } from "lucide-react"

interface Section {
  id: string
  type: "upload"
}

export default function Page() {
  const [sections, setSections] = useState<Section[]>([
    // Bắt đầu với một upload section mặc định
    { id: `upload-${Date.now()}`, type: "upload" },
  ])
  const [showDocument, setShowDocument] = useState(false)
  const [documentContent, setDocumentContent] = useState<any>(null)

  const addUploadSection = () => {
    const newSection: Section = {
      id: `upload-${Date.now()}`,
      type: "upload"
    }
    setSections(prev => [...prev, newSection])
  }

  const removeSection = (sectionId: string) => {
    setSections(prev => prev.filter(s => s.id !== sectionId))
  }

  const handleDocumentGenerated = (content: any, sectionId: string) => {
    setDocumentContent(content)
    setShowDocument(true)
  }

  const handleExportPDF = () => {
    alert("Xuất PDF thành công!")
  }

  const handleBackToChat = () => {
    setShowDocument(false)
    setDocumentContent(null)
  }

  return (
    <div className="h-screen flex bg-gradient-to-br from-red-50 to-red-100 overflow-hidden">
      {/* Sidebar */}
      <div
        className={`transition-all duration-500 ease-in-out ${
          showDocument ? "w-0 opacity-0 -translate-x-full" : "w-80 opacity-100 translate-x-0"
        }`}
      >
        {!showDocument && (
          <div className="animate-slide-in-left">
            <Sidebar />
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {!showDocument ? (
          <div className="flex-1 p-6 overflow-y-auto">
            {/* Header */}
            <div className="mb-8 text-center">
              <div className="w-16 h-16 bg-red-gradient rounded-full flex items-center justify-center mx-auto mb-4">
                <FileText className="h-8 w-8 text-white" />
              </div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Loan Assessment Agent</h1>
              <p className="text-gray-600 mb-6">Trợ lý AI chuyên thẩm định khoản vay</p>
              
              <Button
                onClick={addUploadSection}
                className="bg-red-gradient hover:shadow-lg"
              >
                <Plus className="h-4 w-4 mr-2" />
                New Upload Section
              </Button>
            </div>

            {/* Empty State */}
            {sections.length === 0 && (
              <div className="text-center py-12">
                <Upload className="h-24 w-24 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-700 mb-2">
                  Start by uploading documents
                </h3>
                <p className="text-gray-500 mb-6">
                  Click "New Upload Section" to begin analyzing loan documents
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                  <div className="p-4 bg-white rounded-lg border border-gray-200 text-left">
                    <h4 className="font-medium text-gray-900 mb-2">📄 Upload Documents</h4>
                    <p className="text-sm text-gray-600">
                      Upload loan application files, financial statements, and supporting documents
                    </p>
                  </div>
                  <div className="p-4 bg-white rounded-lg border border-gray-200 text-left">
                    <h4 className="font-medium text-gray-900 mb-2">🤖 Generate Reports</h4>
                    <p className="text-sm text-gray-600">
                      AI will analyze documents and create professional loan assessment reports
                    </p>
                  </div>
                  <div className="p-4 bg-white rounded-lg border border-gray-200 text-left">
                    <h4 className="font-medium text-gray-900 mb-2">💬 Chat with Documents</h4>
                    <p className="text-sm text-gray-600">
                      Ask questions about specific information in your uploaded documents
                    </p>
                  </div>
                  <div className="p-4 bg-white rounded-lg border border-gray-200 text-left">
                    <h4 className="font-medium text-gray-900 mb-2">📊 Multiple Sessions</h4>
                    <p className="text-sm text-gray-600">
                      Work with multiple document sets simultaneously in separate sections
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Sections */}
            <div className="space-y-6">
              {sections.map(section => (
                <div key={section.id}>
                  {section.type === "upload" && (
                    <UploadSection
                      sectionId={section.id}
                      onDocumentGenerated={handleDocumentGenerated}
                      onRemoveSection={removeSection}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <>
            <div className="w-1/2 p-6 overflow-y-auto border-r border-red-200">
              <div className="mb-4">
                <Button
                  onClick={handleBackToChat}
                  variant="outline"
                  className="mb-4"
                >
                  ← Back to Sections
                </Button>
              </div>
              <div className="space-y-6">
                {sections.map((section) => (
                  <div key={section.id}>
                    {section.type === "upload" && (
                      <UploadSection
                        sectionId={section.id}
                        onDocumentGenerated={handleDocumentGenerated}
                        onRemoveSection={removeSection}
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>
            <div className="w-1/2">
              <DocumentEditor 
                content={documentContent} 
                onExportPDF={handleExportPDF} 
                onBackToChat={handleBackToChat} 
              />
            </div>
          </>
        )}
      </div>
    </div>
  )
}
