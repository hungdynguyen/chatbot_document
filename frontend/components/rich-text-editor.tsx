"use client"

import type React from "react"

import { useState, useRef, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import {
  Bold,
  Italic,
  Underline,
  Strikethrough,
  Link,
  X,
  AlignLeft,
  AlignCenter,
  AlignRight,
  List,
  ListOrdered,
} from "lucide-react"
import { Input } from "@/components/ui/input"

interface RichTextEditorProps {
  value: string
  onChange: (value: string) => void
  onBlur: () => void
  onKeyDown: (e: React.KeyboardEvent) => void
  className?: string
  placeholder?: string
  autoFocus?: boolean
  multiline?: boolean
  enableFormatting?: boolean
}

export function RichTextEditor({
  value,
  onChange,
  onBlur,
  onKeyDown,
  className = "",
  placeholder = "",
  autoFocus = false,
  multiline = false,
  enableFormatting = true,
}: RichTextEditorProps) {
  const [showToolbar, setShowToolbar] = useState(false)
  const [toolbarPosition, setToolbarPosition] = useState({ top: 0, left: 0 })
  const [linkUrl, setLinkUrl] = useState("")
  const [showLinkInput, setShowLinkInput] = useState(false)
  const [activeFormats, setActiveFormats] = useState<Set<string>>(new Set())
  const [isInitialized, setIsInitialized] = useState(false)
  const editorRef = useRef<HTMLDivElement>(null)
  const toolbarRef = useRef<HTMLDivElement>(null)
  const lastValueRef = useRef(value)

  // Save and restore cursor position
  const saveCursorPosition = useCallback(() => {
    if (!editorRef.current) return null

    const selection = window.getSelection()
    if (!selection || selection.rangeCount === 0) return null

    const range = selection.getRangeAt(0)
    const preCaretRange = range.cloneRange()
    preCaretRange.selectNodeContents(editorRef.current)
    preCaretRange.setEnd(range.endContainer, range.endOffset)

    return preCaretRange.toString().length
  }, [])

  const restoreCursorPosition = useCallback((position: number) => {
    if (!editorRef.current || position === null) return

    const selection = window.getSelection()
    if (!selection) return

    let charIndex = 0
    const walker = document.createTreeWalker(editorRef.current, NodeFilter.SHOW_TEXT, null)

    let node
    while ((node = walker.nextNode())) {
      const nextCharIndex = charIndex + (node.textContent?.length || 0)
      if (position <= nextCharIndex) {
        const range = document.createRange()
        range.setStart(node, position - charIndex)
        range.collapse(true)
        selection.removeAllRanges()
        selection.addRange(range)
        break
      }
      charIndex = nextCharIndex
    }
  }, [])

  // Initialize content properly on first render
  useEffect(() => {
    if (editorRef.current && !isInitialized) {
      if (value && value.trim() !== "") {
        editorRef.current.innerHTML = value
      }
      lastValueRef.current = value
      setIsInitialized(true)

      if (autoFocus) {
        editorRef.current.focus()
        if (enableFormatting) {
          setShowToolbar(true)
          updateToolbarPosition()
        }
        // Place cursor at end of content
        const range = document.createRange()
        const selection = window.getSelection()
        if (editorRef.current.childNodes.length > 0) {
          range.selectNodeContents(editorRef.current)
          range.collapse(false)
          selection?.removeAllRanges()
          selection?.addRange(range)
        }
      }
    }
  }, [autoFocus, value, isInitialized, enableFormatting])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        toolbarRef.current &&
        !toolbarRef.current.contains(event.target as Node) &&
        editorRef.current &&
        !editorRef.current.contains(event.target as Node)
      ) {
        setShowToolbar(false)
        setShowLinkInput(false)
        onBlur()
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [onBlur])

  const updateToolbarPosition = () => {
    if (!editorRef.current) return

    const rect = editorRef.current.getBoundingClientRect()
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop

    setToolbarPosition({
      top: rect.top + scrollTop - 50,
      left: Math.max(10, Math.min(rect.left + rect.width / 2 - 150, window.innerWidth - 310)),
    })
  }

  const updateActiveFormats = () => {
    const formats = new Set<string>()

    try {
      if (document.queryCommandState("bold")) formats.add("bold")
      if (document.queryCommandState("italic")) formats.add("italic")
      if (document.queryCommandState("underline")) formats.add("underline")
      if (document.queryCommandState("strikethrough")) formats.add("strikethrough")
      if (document.queryCommandState("justifyLeft")) formats.add("justifyLeft")
      if (document.queryCommandState("justifyCenter")) formats.add("justifyCenter")
      if (document.queryCommandState("justifyRight")) formats.add("justifyRight")
      if (document.queryCommandState("insertUnorderedList")) formats.add("insertUnorderedList")
      if (document.queryCommandState("insertOrderedList")) formats.add("insertOrderedList")
    } catch (e) {
      // Ignore errors from queryCommandState
    }

    setActiveFormats(formats)
  }

  const handleFocus = () => {
    if (enableFormatting) {
      setShowToolbar(true)
      updateToolbarPosition()
      updateActiveFormats()
    }
  }

  const handleInput = useCallback(
    (e: React.FormEvent<HTMLDivElement>) => {
      if (editorRef.current) {
        const content = editorRef.current.innerHTML
        if (content !== lastValueRef.current) {
          lastValueRef.current = content
          onChange(content)
        }
      }
    },
    [onChange],
  )

  const handleKeyDownInternal = (e: React.KeyboardEvent) => {
    // Handle keyboard shortcuts
    if (e.ctrlKey || e.metaKey) {
      switch (e.key.toLowerCase()) {
        case "b":
          e.preventDefault()
          executeCommand("bold")
          return
        case "i":
          e.preventDefault()
          executeCommand("italic")
          return
        case "u":
          e.preventDefault()
          executeCommand("underline")
          return
      }
    }

    // Handle Enter key
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault()
        if (editorRef.current) {
          const content = editorRef.current.innerHTML
          onChange(content)
        }
        // Gọi onKeyDown trước để xử lý logic Enter trong EditableField
        onKeyDown(e)
        return
    }

    // Handle Escape key
    if (e.key === "Escape") {
      e.preventDefault()
      onBlur()
      return
    }

    onKeyDown(e)
  }

  const executeCommand = (command: string) => {
    if (command === "link") {
      setShowLinkInput(true)
      return
    }

    if (!editorRef.current) return

    editorRef.current.focus()

    try {
      document.execCommand(command, false, undefined)

      const content = editorRef.current.innerHTML
      if (content !== lastValueRef.current) {
        lastValueRef.current = content
        onChange(content)
      }

      setTimeout(() => {
        updateActiveFormats()
      }, 10)
    } catch (error) {
      console.warn(`Command ${command} failed:`, error)
    }
  }

  const handleLinkSubmit = () => {
    if (linkUrl && editorRef.current) {
      const cursorPos = saveCursorPosition()

      editorRef.current.focus()
      document.execCommand("createLink", false, linkUrl)

      const content = editorRef.current.innerHTML
      if (content !== lastValueRef.current) {
        lastValueRef.current = content
        onChange(content)
      }

      setTimeout(() => {
        if (cursorPos !== null) {
          restoreCursorPosition(cursorPos)
        }
      }, 0)
    }
    setLinkUrl("")
    setShowLinkInput(false)
  }

  const handleLinkKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault()
      handleLinkSubmit()
    } else if (e.key === "Escape") {
      setLinkUrl("")
      setShowLinkInput(false)
    }
  }

  return (
    <div className="relative">
      {/* Rich Text Editor */}
      <div
        ref={editorRef}
        contentEditable
        suppressContentEditableWarning
        onFocus={handleFocus}
        onInput={handleInput}
        onKeyDown={handleKeyDownInternal}
        onMouseUp={updateActiveFormats}
        onKeyUp={updateActiveFormats}
        className={`
          outline-none border rounded-md p-3 min-h-[40px] focus:border-red-400 focus:ring-2 focus:ring-red-400 transition-all-smooth
          ${multiline ? "min-h-[100px]" : ""}
          ${className}
        `}
        data-placeholder={placeholder}
        style={{
          ...((!value || value === "") && {
            position: "relative",
          }),
        }}
      />

      {/* Enhanced Formatting Toolbar */}
      {showToolbar && enableFormatting && (
        <div
          ref={toolbarRef}
          className="fixed z-50 bg-gray-900 text-white rounded-lg shadow-xl p-2 flex items-center gap-1 animate-fade-in-scale"
          style={{
            top: toolbarPosition.top,
            left: toolbarPosition.left,
          }}
        >
          {!showLinkInput ? (
            <>
              {/* Text Formatting */}
              <div className="flex items-center gap-0.5 pr-2 border-r border-gray-600">
                <Button
                  variant="ghost"
                  size="sm"
                  className={`h-8 w-8 p-0 text-white hover:bg-gray-700 transition-colors-smooth ${
                    activeFormats.has("bold") ? "bg-gray-700" : ""
                  }`}
                  onClick={() => executeCommand("bold")}
                  title="In đậm (Ctrl+B)"
                >
                  <Bold className="h-4 w-4" />
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  className={`h-8 w-8 p-0 text-white hover:bg-gray-700 transition-colors-smooth ${
                    activeFormats.has("italic") ? "bg-gray-700" : ""
                  }`}
                  onClick={() => executeCommand("italic")}
                  title="In nghiêng (Ctrl+I)"
                >
                  <Italic className="h-4 w-4" />
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  className={`h-8 w-8 p-0 text-white hover:bg-gray-700 transition-colors-smooth ${
                    activeFormats.has("underline") ? "bg-gray-700" : ""
                  }`}
                  onClick={() => executeCommand("underline")}
                  title="Gạch chân (Ctrl+U)"
                >
                  <Underline className="h-4 w-4" />
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  className={`h-8 w-8 p-0 text-white hover:bg-gray-700 transition-colors-smooth ${
                    activeFormats.has("strikethrough") ? "bg-gray-700" : ""
                  }`}
                  onClick={() => executeCommand("strikethrough")}
                  title="Gạch ngang"
                >
                  <Strikethrough className="h-4 w-4" />
                </Button>
              </div>

              {/* Alignment */}
              <div className="flex items-center gap-0.5 pr-2 border-r border-gray-600">
                <Button
                  variant="ghost"
                  size="sm"
                  className={`h-8 w-8 p-0 text-white hover:bg-gray-700 transition-colors-smooth ${
                    activeFormats.has("justifyLeft") ? "bg-gray-700" : ""
                  }`}
                  onClick={() => executeCommand("justifyLeft")}
                  title="Căn trái"
                >
                  <AlignLeft className="h-4 w-4" />
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  className={`h-8 w-8 p-0 text-white hover:bg-gray-700 transition-colors-smooth ${
                    activeFormats.has("justifyCenter") ? "bg-gray-700" : ""
                  }`}
                  onClick={() => executeCommand("justifyCenter")}
                  title="Căn giữa"
                >
                  <AlignCenter className="h-4 w-4" />
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  className={`h-8 w-8 p-0 text-white hover:bg-gray-700 transition-colors-smooth ${
                    activeFormats.has("justifyRight") ? "bg-gray-700" : ""
                  }`}
                  onClick={() => executeCommand("justifyRight")}
                  title="Căn phải"
                >
                  <AlignRight className="h-4 w-4" />
                </Button>
              </div>

              {/* Lists */}
              <div className="flex items-center gap-0.5 pr-2 border-r border-gray-600">
                <Button
                  variant="ghost"
                  size="sm"
                  className={`h-8 w-8 p-0 text-white hover:bg-gray-700 transition-colors-smooth ${
                    activeFormats.has("insertUnorderedList") ? "bg-gray-700" : ""
                  }`}
                  onClick={() => executeCommand("insertUnorderedList")}
                  title="Danh sách không thứ tự"
                >
                  <List className="h-4 w-4" />
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  className={`h-8 w-8 p-0 text-white hover:bg-gray-700 transition-colors-smooth ${
                    activeFormats.has("insertOrderedList") ? "bg-gray-700" : ""
                  }`}
                  onClick={() => executeCommand("insertOrderedList")}
                  title="Danh sách có thứ tự"
                >
                  <ListOrdered className="h-4 w-4" />
                </Button>
              </div>

              {/* Link */}
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 text-white hover:bg-gray-700 transition-colors-smooth"
                onClick={() => executeCommand("link")}
                title="Thêm liên kết"
              >
                <Link className="h-4 w-4" />
              </Button>

              {/* Close */}
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 text-white hover:bg-gray-700 transition-colors-smooth ml-2"
                onClick={() => {
                  setShowToolbar(false)
                  onBlur()
                }}
                title="Đóng"
              >
                <X className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Input
                value={linkUrl}
                onChange={(e) => setLinkUrl(e.target.value)}
                onKeyDown={handleLinkKeyDown}
                placeholder="Nhập URL..."
                className="h-8 w-40 text-xs bg-gray-800 border-gray-600 text-white placeholder-gray-400"
                autoFocus
              />
              <Button
                variant="ghost"
                size="sm"
                className="h-8 px-3 text-xs text-white hover:bg-gray-700 transition-colors-smooth"
                onClick={handleLinkSubmit}
              >
                OK
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 text-white hover:bg-gray-700 transition-colors-smooth"
                onClick={() => {
                  setLinkUrl("")
                  setShowLinkInput(false)
                }}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}