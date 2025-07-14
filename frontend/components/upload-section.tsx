"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import {
  Upload,
  File,
  X,
  Send,
  CheckCircle,
  AlertCircle,
  Loader2,
  FileText,
  FileSpreadsheet,
  FileImage,
  Paperclip,
  MessageSquare,
  FileTextIcon as Document,
  ChevronDown,
  ChevronUp,
} from "lucide-react"

interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
  status: "uploading" | "uploaded" | "error"
  progress: number
  file_id?: string
  error?: string
}

interface UploadSectionProps {
  sectionId: string
  onDocumentGenerated?: (content: any, sectionId:string) => void
  onRemoveSection?: (sectionId: string) => void
  onUploadSuccess?: (fileIds: string[]) => void
}

export function UploadSection({
  sectionId,
  onDocumentGenerated,
  onRemoveSection,
  onUploadSuccess,
}: UploadSectionProps) {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [prompt, setPrompt] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [showActions, setShowActions] = useState(false)
  const router = useRouter()

  const getFileIcon = (type: string) => {
    if (type.includes("pdf")) return <FileText className="h-4 w-4 text-red-500" />
    if (type.includes("sheet") || type.includes("excel")) return <FileSpreadsheet className="h-4 w-4 text-green-500" />
    if (type.includes("word")) return <FileText className="h-4 w-4 text-blue-500" />
    if (type.includes("image")) return <FileImage className="h-4 w-4 text-purple-500" />
    return <File className="h-4 w-4 text-gray-500" />
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  const uploadFile = async (file: File): Promise<string | null> => {
    const fileId = `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

    const newFile: UploadedFile = {
      id: fileId,
      name: file.name,
      size: file.size,
      type: file.type,
      status: "uploading",
      progress: 0,
    }

    setFiles((prev) => [...prev, newFile])

    try {
      const formData = new FormData()
      formData.append("file", file)

      const updateProgress = (progress: number) => {
        setFiles((prev) => prev.map((f) => (f.id === fileId ? { ...f, progress } : f)))
      }

      let currentProgress = 0
      const progressInterval = setInterval(() => {
        currentProgress = Math.min(90, currentProgress + Math.random() * 20)
        updateProgress(currentProgress)
      }, 200)

      const response = await fetch("http://localhost:8000/upload_file", {
        method: "POST",
        body: formData,
      })

      clearInterval(progressInterval)

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const result = await response.json()

      setFiles(prev => {
        const updatedFiles = prev.map(f =>
          f.id === fileId
            ? {
                ...f,
                status: "uploaded",
                progress: 100,
                file_id: result.file_id,
              }
            : f,
        )
        
        const uploadedFileIds = updatedFiles
          .filter(f => f.status === "uploaded" && f.file_id)
          .map(f => f.file_id!)

        if (onUploadSuccess && uploadedFileIds.length > 0) {
          onUploadSuccess(uploadedFileIds)
        }
        
        return updatedFiles
      })

      // Show actions when first file is uploaded
      if (!showActions) {
        setShowActions(true)
      }

      return result.file_id
    } catch (error) {
      console.error("Upload error:", error)
      setFiles((prev) =>
        prev.map((f) =>
          f.id === fileId
            ? {
                ...f,
                status: "error",
                progress: 0,
                error: error instanceof Error ? error.message : "Upload failed",
              }
            : f,
        ),
      )
      return null
    }
  }

  const handleFileSelect = async (selectedFiles: FileList | File[]) => {
    const fileArray = Array.from(selectedFiles)
    for (const file of fileArray) {
      await uploadFile(file)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    const droppedFiles = e.dataTransfer.files
    if (droppedFiles.length > 0) {
      handleFileSelect(droppedFiles)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const removeFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId))
    // Hide actions if no files left
    if (files.length <= 1) {
      setShowActions(false)
    }
  }

  const handleGenerateDocument = async () => {
    if (!prompt.trim()) {
      alert("Vui lòng nhập prompt để tạo tài liệu")
      return
    }

    const uploadedFileIds = files.filter((f) => f.status === "uploaded" && f.file_id).map((f) => f.file_id!)

    if (uploadedFileIds.length === 0) {
      alert("Không có file nào để xử lý")
      return
    }

    setIsProcessing(true)

    try {
      const response = await fetch("http://localhost:8000/process_prompt", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt: prompt.trim(),
          file_ids: uploadedFileIds,
        }),
      })

      if (!response.ok) {
        throw new Error(`Processing failed: ${response.statusText}`)
      }

      const result = await response.json()

      if (onDocumentGenerated) {
        // Transform result to document format similar to chat-interface
        const extracted = result.extracted_data || {}
        
        const formatCurrency = (value: any) => {
          if (!value) return null;
          const number = Number(String(value).replace(/[^0-9.-]+/g,""));
          if (isNaN(number)) return value;
          return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(number);
        };

        const documentData = {
          title: `Báo cáo Thẩm định Khoản vay - ${extracted["tên đầy đủ của doanh nghiệp"] || "Chưa xác định"}`,
          company: extracted["tên đầy đủ của doanh nghiệp"],
          loanAmount: formatCurrency(extracted["số tiền đề nghị vay"]),
          reportType: "Thẩm định Khoản vay",
          period: new Date().getFullYear().toString(),
          executiveSummary: `Dựa trên phân tích ${uploadedFileIds.length} tài liệu, hệ thống đã trích xuất thông tin chi tiết về doanh nghiệp ${extracted["tên đầy đủ của doanh nghiệp"] || ""} và khoản vay đề nghị.`,
          borrowerProfile: {
            companyName: extracted["tên đầy đủ của doanh nghiệp"],
            businessType: extracted["mã số doanh nghiệp"],
            mainBusiness: extracted["ngành nghề kinh doanh chính"],
            legalRep: extracted["địa chỉ trụ sở chính"],
            legalRepName: extracted["tên người đại diện theo pháp luật"],
            establishedYear: 0,
            employees: 0,
          },
          loanDetails: {
            amount: formatCurrency(extracted["số tiền đề nghị vay"]),
            purpose: extracted["mục đích vay vốn"],
            term: extracted["thời hạn vay (tháng)"] ? `${extracted["thời hạn vay (tháng)"]} tháng` : null,
            requestedRate: extracted["lãi suất cho vay (%/năm)"] ? `${extracted["lãi suất cho vay (%/năm)"]} %/năm` : null,
            repaymentMethod: extracted["phương thức trả nợ"],
          },
          financialHighlights: [
            { label: "Vốn điều lệ", value: formatCurrency(extracted["vốn điều lệ"]), available: !!extracted["vốn điều lệ"] },
            { label: "Doanh thu năm gần nhất", value: formatCurrency(extracted["doanh thu năm gần nhất"]), available: !!extracted["doanh thu năm gần nhất"] },
            { label: "Lợi nhuận ròng năm gần nhất", value: formatCurrency(extracted["lợi nhuận ròng năm gần nhất"]), available: !!extracted["lợi nhuận ròng năm gần nhất"] },
            { label: "Tổng tài sản ước tính", value: formatCurrency(extracted["tổng tài sản ước tính"]), available: !!extracted["tổng tài sản ước tính"] },
          ].filter(item => item.available),
          financialRatios: [
            { label: "Điểm tín dụng (CIC)", value: extracted["điểm tín dụng doanh nghiệp (CIC)"], status: "good" },
            { label: "Xếp hạng (CIC)", value: extracted["xếp hạng tín dụng doanh nghiệp (CIC)"], status: "good" },
            { label: "Phân loại nợ (CIC)", value: extracted["phân loại nợ hiện tại của doanh nghiệp (CIC)"], status: "good"},
            { label: "Tổng dư nợ", value: formatCurrency(extracted["tổng dư nợ tại các tổ chức tín dụng khác"]), status: "warning"},
          ].filter(item => item.value),
          collateralEvaluation: {
            realEstateValue: extracted["loại tài sản bảo đảm chính"],
            totalValue: formatCurrency(extracted["giá trị tài sản bảo đảm theo thẩm định"]),
            ltvRatio: extracted["tỷ lệ cho vay tối đa trên tài sản bảo đảm (%)"] ? `${extracted["tỷ lệ cho vay tối đa trên tài sản bảo đảm (%)"]} %` : null,
            equipmentValue: null,
            adequacy: null,
          },
          conclusion: "Báo cáo được tạo tự động. Chuyên viên tín dụng cần xem xét, xác minh lại thông tin và đưa ra kết luận cuối cùng.",
        }

        onDocumentGenerated(documentData, sectionId)
      }

      setPrompt("")
    } catch (error) {
      console.error("Processing error:", error)
      alert(`Processing failed: ${error instanceof Error ? error.message : "Unknown error"}`)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleStartChat = () => {
    const uploadedFileIds = files
      .filter(f => f.status === "uploaded" && f.file_id)
      .map(f => f.file_id!)

    if (uploadedFileIds.length === 0) {
      alert("Vui lòng tải lên và chờ xử lý file trước khi chat.")
      return
    }

    // Lưu file_ids vào localStorage để trang /chat có thể truy cập
    localStorage.setItem("ragFileIds", JSON.stringify(uploadedFileIds))

    // Chuyển hướng sang trang /chat bằng Next.js router
    router.push("/chat")
  }

  const uploadedFiles = files.filter(f => f.status === "uploaded")
  const isUploading = files.some(f => f.status === "uploading")

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1 hover:bg-gray-100 rounded"
          >
            {isCollapsed ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
          </button>
          <h3 className="font-semibold text-gray-900">
            Upload Section ({uploadedFiles.length} files)
          </h3>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onRemoveSection?.(sectionId)}
          className="text-gray-400 hover:text-red-500"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Content */}
      {!isCollapsed && (
        <div className="p-4 space-y-4">
          {/* Upload Area */}
          <div
            className={`border-2 border-dashed rounded-lg p-6 text-center transition-all ${
              isDragOver ? "border-red-400 bg-red-50" : "border-gray-300 hover:border-red-300 hover:bg-red-50"
            }`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm font-medium text-gray-700 mb-1">Drop files here or click to browse</p>
            <p className="text-xs text-gray-500 mb-3">PDF, DOCX, XLSX, images</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const input = document.createElement('input')
                input.type = 'file'
                input.multiple = true
                input.accept = '.pdf,.docx,.xlsx,.xls,.doc,.png,.jpg,.jpeg,.gif'
                input.onchange = (e) => {
                  const target = e.target as HTMLInputElement
                  if (target.files) {
                    handleFileSelect(target.files)
                  }
                }
                input.click()
              }}
            >
              <Paperclip className="h-4 w-4 mr-2" />
              Choose Files
            </Button>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="space-y-2">
              {files.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border"
                >
                  {getFileIcon(file.type)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-gray-700 truncate">{file.name}</span>
                      <span className="text-xs text-gray-500">{formatFileSize(file.size)}</span>
                    </div>
                    {file.status === "uploading" && (
                      <div className="space-y-1">
                        <Progress value={file.progress} className="h-2" />
                        <span className="text-xs text-gray-500">Uploading... {Math.round(file.progress)}%</span>
                      </div>
                    )}
                    {file.status === "error" && (
                      <span className="text-xs text-red-600">{file.error || "Upload failed"}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {file.status === "uploaded" && (
                      <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Uploaded
                      </Badge>
                    )}
                    {file.status === "uploading" && (
                      <Badge variant="outline" className="text-blue-600 border-blue-200 bg-blue-50">
                        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                        Uploading
                      </Badge>
                    )}
                    {file.status === "error" && (
                      <Badge variant="outline" className="text-red-600 border-red-200 bg-red-50">
                        <AlertCircle className="h-3 w-3 mr-1" />
                        Error
                      </Badge>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFile(file.id)}
                      className="h-8 w-8 p-0 text-gray-400 hover:text-red-500"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Actions */}
          {showActions && uploadedFiles.length > 0 && (
            <div className="space-y-4 pt-4 border-t border-gray-200">
              {/* Prompt Input */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">
                  Prompt (for document generation)
                </label>
                <Input
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Nhập yêu cầu xử lý (ví dụ: 'Tạo báo cáo thẩm định khoản vay từ các tài liệu này')"
                  disabled={isUploading || isProcessing}
                />
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <Button
                  onClick={handleGenerateDocument}
                  disabled={!prompt.trim() || isUploading || isProcessing}
                  className="flex-1 bg-red-600 hover:bg-red-700"
                >
                  {isProcessing ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Document className="h-4 w-4 mr-2" />
                  )}
                  Generate Document
                </Button>
                
                <Button
                  onClick={handleStartChat}
                  disabled={isUploading}
                  variant="outline"
                  className="flex-1 border-blue-200 text-blue-700 hover:bg-blue-50"
                >
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Start Chat
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
