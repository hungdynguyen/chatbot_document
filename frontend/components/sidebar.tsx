"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Plus, FileText, Settings, User, Clock } from "lucide-react"

const recentDocuments = [
  { id: 1, title: "Báo cáo Thẩm định Khoản vay ABC Corp", type: "loan-assessment", active: true },
  { id: 2, title: "Thẩm định Tín dụng Công ty XYZ", type: "loan-assessment" },
  { id: 3, title: "Đánh giá Khả năng Trả nợ DEF Ltd", type: "loan-assessment" },
  { id: 4, title: "Báo cáo Phân tích Rủi ro Tín dụng", type: "loan-assessment" },
]

export function Sidebar() {
  const [activeDocument, setActiveDocument] = useState(1)

  return (
    <div className="w-80 bg-white border-r border-red-200 flex flex-col shadow-lg">
      {/* Header */}
      <div className="p-6 border-b border-red-100 bg-red-gradient">
        <div className="flex items-center gap-3 mb-6 animate-fade-in-scale">
          <div className="w-8 h-8 bg-white/20 backdrop-blur-sm rounded-lg flex items-center justify-center animate-pulse-red">
            <FileText className="h-5 w-5 text-white" />
          </div>
          <h1 className="text-xl font-bold text-white">Loan Assessment</h1>
        </div>

        <Button className="w-full bg-white/20 backdrop-blur-sm hover:bg-white/30 text-white border-white/30 rounded-lg transition-all-smooth hover-lift">
          <Plus className="h-4 w-4 mr-2" />
          Thẩm định mới
        </Button>
      </div>

      {/* Recent Documents */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="flex justify-between items-center mb-4 animate-fade-in-up">
          <span className="text-sm font-medium text-gray-700">Báo cáo gần đây</span>
          <button className="text-sm text-red-600 hover:text-red-700 transition-colors-smooth">Xem tất cả</button>
        </div>

        <div className="space-y-2 mb-8">
          {recentDocuments.map((doc, index) => (
            <button
              key={doc.id}
              onClick={() => setActiveDocument(doc.id)}
              className={`w-full text-left p-3 rounded-lg text-sm hover:bg-red-50 flex items-start gap-3 transition-all-smooth hover-lift ${
                activeDocument === doc.id ? "bg-red-50 border border-red-200 shadow-sm" : ""
              } ${doc.active ? "text-red-600" : "text-gray-700"}`}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <FileText className="h-4 w-4 flex-shrink-0 mt-0.5 transition-colors-smooth" />
              <div className="flex-1 min-w-0">
                <span className="block truncate font-medium transition-colors-smooth">{doc.title}</span>
                <span className="text-xs text-gray-500">Thẩm định khoản vay</span>
              </div>
            </button>
          ))}
        </div>

        {/* Recent Activity */}
        <div className="animate-fade-in-up" style={{ animationDelay: "0.6s" }}>
          <span className="text-sm font-medium text-gray-700 mb-3 block flex items-center gap-2">
            <Clock className="h-4 w-4 text-red-500" />
            Hoạt động gần đây
          </span>
          <div className="space-y-2 text-xs text-gray-500">
            <p className="transition-colors-smooth hover:text-red-600 cursor-pointer">
              • Đã tạo "Thẩm định ABC Corp" - 2 giờ trước
            </p>
            <p className="transition-colors-smooth hover:text-red-600 cursor-pointer">
              • Đã chỉnh sửa "Đánh giá XYZ" - 1 ngày trước
            </p>
            <p className="transition-colors-smooth hover:text-red-600 cursor-pointer">
              • Đã xuất PDF "Phân tích DEF" - 2 ngày trước
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-6 border-t border-red-100 bg-red-gradient-soft">
        <button className="w-full flex items-center gap-3 p-2 text-sm text-gray-700 hover:bg-red-100 rounded-lg mb-2 transition-all-smooth hover-lift">
          <Settings className="h-4 w-4 text-red-500" />
          Cài đặt
        </button>
        <button className="w-full flex items-center gap-3 p-2 text-sm text-gray-700 hover:bg-red-100 rounded-lg transition-all-smooth hover-lift">
          <User className="h-4 w-4 text-red-500" />
          Tài khoản
        </button>
      </div>
    </div>
  )
}
