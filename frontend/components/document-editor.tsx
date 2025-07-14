// Trong file: components/document-editor.tsx

"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Download, Edit, FileText, ArrowLeft } from "lucide-react"
import { LoanAssessmentTemplate } from "@/templates/loan-assessment-template"
import { set } from 'lodash'; // Cần cài đặt lodash


interface DocumentEditorProps {
  content?: any
  onExportPDF: () => void
  onBackToChat?: () => void
}

export function DocumentEditor({ content, onExportPDF, onBackToChat }: DocumentEditorProps) {
  // documentData sẽ là nguồn chân lý duy nhất cho template
  const [documentData, setDocumentData] = useState<any | null>(null) 
  const [editingField, setEditingField] = useState<string | null>(null)

  useEffect(() => {
    // Chỉ cập nhật state khi prop `content` thực sự thay đổi
    if (content) {
      setDocumentData(content)
    }
  }, [content])

  const handleEdit = (fieldId: string) => {
    setEditingField(fieldId)
  }

  const handleStopEdit = () => {
    setEditingField(null)
  }

  // --- HÀM CẬP NHẬT QUAN TRỌNG NHẤT ---
  // Sử dụng lodash.set để dễ dàng cập nhật các trường lồng nhau
  const handleUpdateField = (path: string, value: string) => {
    if (!documentData) return

    // Tạo một bản sao sâu của object để tránh thay đổi trực tiếp state
    const updatedData = JSON.parse(JSON.stringify(documentData)); 

    // Sử dụng lodash.set để cập nhật giá trị tại đường dẫn đã cho
    // Ví dụ: path = "loanDetails.amount"
    set(updatedData, path, value);

    // Cập nhật state với object mới
    setDocumentData(updatedData);
  }

  if (!documentData) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-500 mx-auto mb-4"></div>
        <p className="text-gray-600">Đang tải báo cáo...</p>
      </div>
    )
  }
  
  const getAvailabilityColor = (percentage: number) => {
    if (percentage >= 80) return "text-green-600 bg-green-50"
    if (percentage >= 60) return "text-yellow-600 bg-yellow-50"
    return "text-red-600 bg-red-50"
  }


  return (
    <div className="h-full overflow-y-auto bg-white shadow-lg">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-red-200 p-4 flex justify-between items-center z-10 shadow-sm">
        <div className="flex items-center gap-3 animate-fade-in-scale">
          {onBackToChat && (
            <Button variant="ghost" size="sm" onClick={onBackToChat} className="hover:bg-red-50 transition-all-smooth">
              <ArrowLeft className="h-4 w-4 mr-2 text-red-500" />
              Quay lại
            </Button>
          )}
          <FileText className="h-5 w-5 text-red-600" />
          <h2 className="text-lg font-semibold text-gray-800">Báo cáo Thẩm định</h2>
          {documentData.dataAvailability > 0 && 
            <Badge className={`${getAvailabilityColor(documentData.dataAvailability)} transition-all-smooth`}>
              {documentData.dataAvailability}% dữ liệu
            </Badge>
          }
        </div>
        <div className="flex gap-2">
          {/* Nút chỉnh sửa này có thể không cần thiết nữa */}
          {/* <Button
            variant="outline"
            size="sm"
            className="hover:bg-red-50 border-red-200 transition-all-smooth hover-lift bg-transparent"
          >
            <Edit className="h-4 w-4 mr-2 text-red-500" />
            Chỉnh sửa
          </Button> */}
          <Button
            size="sm"
            onClick={onExportPDF}
            className="bg-red-gradient hover:shadow-lg transition-all-smooth hover-lift"
          >
            <Download className="h-4 w-4 mr-2" />
            Xuất PDF
          </Button>
        </div>
      </div>

      {/* Template Content */}
      <LoanAssessmentTemplate
        data={documentData}
        editingField={editingField}
        onEdit={handleEdit}
        onStopEdit={handleStopEdit}
        onUpdateField={handleUpdateField} // Truyền hàm cập nhật mới xuống
        // Các hàm update riêng lẻ không cần nữa
        // onUpdateRecommendation={...}
        // onUpdateFinancialHighlight={...}
      />
    </div>
  )
}