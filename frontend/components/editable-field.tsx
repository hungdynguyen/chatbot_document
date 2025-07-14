"use client"

import type React from "react"
import { RichTextEditor } from "./rich-text-editor"

interface EditableFieldProps {
  value: string | number | null | undefined // Mở rộng kiểu dữ liệu cho phép
  onChange: (value: string) => void
  fieldId: string
  editingField: string | null
  onEdit: (fieldId: string) => void
  onStopEdit: () => void
  className?: string
  placeholder?: string
  multiline?: boolean
  displayClassName?: string
  inline?: boolean
  enableFormatting?: boolean
}

export function EditableField({
  value,
  onChange,
  fieldId,
  editingField,
  onEdit,
  onStopEdit,
  className = "",
  placeholder = "",
  multiline = false,
  displayClassName = "",
  inline = false,
  enableFormatting = true,
}: EditableFieldProps) {
  const isEditing = editingField === fieldId

  // --- SỬA LỖI: Chuyển đổi giá trị sang chuỗi một cách an toàn ---
  // Sử dụng String() và toán tử ?? để xử lý null/undefined
  const stringValue = String(value ?? "")

  const handleDoubleClick = () => {
    onEdit(fieldId)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey && !multiline) {
      e.preventDefault()
      onStopEdit()
    } else if (e.key === "Escape") {
      onStopEdit()
    }
  }

  const handleBlur = () => {
    onStopEdit()
  }

  const getDisplayContent = () => {
    // --- SỬA LỖI: Sử dụng stringValue đã được chuyển đổi ---
    if (!stringValue || stringValue.trim() === "") {
      return `<span class="text-gray-400 italic">${placeholder || "Nhấp đúp để chỉnh sửa"}</span>`
    }

    // Trả về nội dung đã là chuỗi để bảo toàn định dạng
    return stringValue
  }

  if (isEditing) {
    return (
      <RichTextEditor
        // --- SỬA LỖI: Luôn truyền một chuỗi vào RichTextEditor ---
        value={stringValue}
        onChange={onChange}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        className={className}
        placeholder={placeholder}
        autoFocus
        multiline={multiline}
        enableFormatting={enableFormatting}
      />
    )
  }

  const DisplayComponent = inline ? "span" : "div"

  return (
    <DisplayComponent
      className={`cursor-pointer hover:bg-red-50 hover:border hover:border-red-200 px-2 py-1 rounded transition-all-smooth editable-display ${
        inline ? "inline-block" : "min-h-[32px] flex items-center"
      } ${displayClassName}`}
      onDoubleClick={handleDoubleClick}
      dangerouslySetInnerHTML={{
        __html: getDisplayContent(),
      }}
      title="Nhấp đúp để chỉnh sửa và định dạng"
    />
  )
}