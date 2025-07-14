"use client"

import type React from "react"

import { useState, useRef, useCallback } from "react"
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

interface FileUploadProcessorProps {
  onProcessComplete?: (result: any) => void
  className?: string
}

export function FileUploadProcessor({ onProcessComplete, className = "" }: FileUploadProcessorProps) {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [prompt, setPrompt] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

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

      // Simulate upload progress
      const updateProgress = (progress: number) => {
        setFiles((prev) => prev.map((f) => (f.id === fileId ? { ...f, progress } : f)))
      }

      // Simulate progress updates
      let currentProgress = 0
      const progressInterval = setInterval(() => {
        currentProgress = Math.min(90, currentProgress + Math.random() * 20)
        updateProgress(currentProgress)
      }, 200)

      // Call your FastAPI backend
      const response = await fetch("http://localhost:8000/upload_file", {
        method: "POST",
        body: formData,
      })

      clearInterval(progressInterval)

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const result = await response.json()

      setFiles((prev) =>
        prev.map((f) =>
          f.id === fileId
            ? {
                ...f,
                status: "uploaded",
                progress: 100,
                file_id: result.file_id, // Use the UUID from your backend
              }
            : f,
        ),
      )

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

  const handleFileSelect = useCallback(async (selectedFiles: FileList | File[]) => {
    const fileArray = Array.from(selectedFiles)

    // Upload files one by one
    for (const file of fileArray) {
      await uploadFile(file)
    }
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragOver(false)

      const droppedFiles = e.dataTransfer.files
      if (droppedFiles.length > 0) {
        handleFileSelect(droppedFiles)
      }
    },
    [handleFileSelect],
  )

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const removeFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId))
  }

  const retryUpload = async (fileId: string) => {
    const fileToRetry = files.find((f) => f.id === fileId)
    if (!fileToRetry) return

    // We need to get the original file again - in a real app, you'd store it
    // For now, we'll just reset the status
    setFiles((prev) =>
      prev.map((f) => (f.id === fileId ? { ...f, status: "uploading", progress: 0, error: undefined } : f)),
    )

    // Simulate retry logic here
    setTimeout(() => {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === fileId ? { ...f, status: "uploaded", progress: 100, file_id: `retry-${Date.now()}` } : f,
        ),
      )
    }, 2000)
  }

  const handlePromptSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!prompt.trim()) return

    const uploadedFileIds = files.filter((f) => f.status === "uploaded" && f.file_id).map((f) => f.file_id!)

    setIsProcessing(true)

    try {
      // Call your FastAPI backend
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

      if (onProcessComplete) {
        onProcessComplete(result)
      }

      // Clear prompt after successful processing
      setPrompt("")
    } catch (error) {
      console.error("Processing error:", error)
      alert(`Processing failed: ${error instanceof Error ? error.message : "Unknown error"}`)
    } finally {
      setIsProcessing(false)
    }
  }

  const isUploading = files.some((f) => f.status === "uploading")
  const canSubmit = prompt.trim() && !isUploading && !isProcessing

  return (
    <div className={`space-y-6 ${className}`}>
      {/* File Upload Area */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Upload className="h-5 w-5 text-red-500" />
          Upload Documents
        </h3>

        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-all-smooth ${
            isDragOver ? "border-red-400 bg-red-50" : "border-gray-300 hover:border-red-300 hover:bg-red-50"
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-700 mb-2">Drop files here or click to browse</p>
          <p className="text-sm text-gray-500 mb-4">Supports PDF, DOCX, XLSX, and image files</p>
          <Button
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
            className="hover:bg-red-50 border-red-200 transition-all-smooth"
          >
            <Paperclip className="h-4 w-4 mr-2" />
            Choose Files
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            accept=".pdf,.docx,.xlsx,.xls,.doc,.png,.jpg,.jpeg,.gif"
            onChange={(e) => {
              if (e.target.files) {
                handleFileSelect(e.target.files)
              }
            }}
          />
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-medium text-gray-700">Uploaded Files ({files.length})</h4>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {files.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border hover:bg-gray-100 transition-all-smooth"
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
                    <div className="space-y-1">
                      <span className="text-xs text-red-600">{file.error || "Upload failed"}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => retryUpload(file.id)}
                        className="h-6 px-2 text-xs text-red-600 hover:bg-red-50"
                      >
                        Retry
                      </Button>
                    </div>
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
                    className="h-8 w-8 p-0 text-gray-400 hover:text-red-500 hover:bg-red-50"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Prompt Input */}
      <div className="space-y-3">
        <h4 className="font-medium text-gray-700">Processing Instructions</h4>
        <form onSubmit={handlePromptSubmit} className="space-y-3">
          <div className="relative">
            <Input
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your processing instructions (e.g., 'Create a loan assessment report from these documents')"
              className="pr-12 min-h-[80px] resize-none"
              disabled={isUploading || isProcessing}
            />
            <Button
              type="submit"
              disabled={!canSubmit}
              className="absolute right-2 top-2 w-8 h-8 p-0 bg-red-gradient hover:shadow-lg transition-all-smooth"
            >
              {isProcessing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </div>

          {isUploading && (
            <p className="text-sm text-yellow-600 flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Please wait for all files to finish uploading...
            </p>
          )}

          {isProcessing && (
            <p className="text-sm text-blue-600 flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Processing your request...
            </p>
          )}
        </form>
      </div>

      {/* Status Summary */}
      {files.length > 0 && (
        <div className="flex items-center gap-4 text-sm text-gray-600 pt-4 border-t border-gray-200">
          <span>
            Total files: <strong>{files.length}</strong>
          </span>
          <span>
            Uploaded: <strong className="text-green-600">{files.filter((f) => f.status === "uploaded").length}</strong>
          </span>
          <span>
            Uploading: <strong className="text-blue-600">{files.filter((f) => f.status === "uploading").length}</strong>
          </span>
          {files.filter((f) => f.status === "error").length > 0 && (
            <span>
              Errors: <strong className="text-red-600">{files.filter((f) => f.status === "error").length}</strong>
            </span>
          )}
        </div>
      )}
    </div>
  )
}
