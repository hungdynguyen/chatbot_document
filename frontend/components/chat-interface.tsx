"use client"

import { useChat } from "ai/react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send, Bot, User, FileText, Loader2, Upload } from "lucide-react"
import { FileUploadProcessor } from "@/components/file-upload-processor"
import { useState } from "react"

interface ChatInterfaceProps {
  onDocumentGenerated: (content: any) => void
  isFullWidth?: boolean
}

export function ChatInterface({ onDocumentGenerated, isFullWidth = true }: ChatInterfaceProps) {
  const [showFileUpload, setShowFileUpload] = useState(false)
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: "/api/chat",
    onFinish: (message) => {
      try {
        const content = message.content
        if (content.includes("DOCUMENT_GENERATED:")) {
          const documentDataString = content.split("DOCUMENT_GENERATED:")[1]
          const documentData = JSON.parse(documentDataString)
          onDocumentGenerated(documentData)
        }
      } catch (error) {
        console.error("Error parsing document data:", error)
      }
    },
  })

  const quickActions = [
    "Tạo báo cáo thẩm định khoản vay 5 tỷ VND",
    "Thẩm định khả năng trả nợ công ty ABC",
    "Đánh giá rủi ro tín dụng doanh nghiệp",
    "Phân tích tài sản đảm bảo khoản vay",
    "Báo cáo thẩm định mở rộng sản xuất",
    "Đánh giá hồ sơ vay vốn lưu động",
  ]


// Trong handleFileProcessComplete trong file chat-interface.tsx

  const handleFileProcessComplete = (result: any) => {
    console.log("File processing complete:", result)
    if (
      result.summary ||
      result.prompt?.toLowerCase().includes("thẩm định") ||
      result.prompt?.toLowerCase().includes("loan")
    ) {
      const extracted = result.extracted_data || {};

      // Hàm tiện ích để định dạng số và thêm đơn vị
      const formatCurrency = (value: any) => {
        if (!value) return null;
        const number = Number(String(value).replace(/[^0-9.-]+/g,""));
        if (isNaN(number)) return value; // Trả về chuỗi gốc nếu không phải số
        return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(number);
      };
      
      const documentData = {
        // --- THÔNG TIN CHUNG ---
        title: `Báo cáo Thẩm định Khoản vay - ${extracted["tên đầy đủ của doanh nghiệp"] || "Chưa xác định"}`,
        company: extracted["tên đầy đủ của doanh nghiệp"],
        loanAmount: formatCurrency(extracted["số tiền đề nghị vay"]),
        reportType: "Thẩm định Khoản vay",
        period: new Date().getFullYear().toString(),
        dataAvailability: 0, // Không còn dùng
        riskScore: 0, // Không còn dùng

        // --- TÓM TẮT ---
        executiveSummary: `Dựa trên phân tích ${
          result.file_ids?.length || 0
        } tài liệu, hệ thống đã trích xuất thông tin chi tiết về doanh nghiệp ${
          extracted["tên đầy đủ của doanh nghiệp"] || ""
        } và khoản vay đề nghị. Báo cáo này tổng hợp các thông tin pháp lý, tài chính, và các yếu tố liên quan để hỗ trợ quá trình ra quyết định.`,

        // --- HỒ SƠ BÊN VAY ---
        borrowerProfile: {
          companyName: extracted["tên đầy đủ của doanh nghiệp"],
          businessType: extracted["mã số doanh nghiệp"],
          mainBusiness: extracted["ngành nghề kinh doanh chính"],
          legalRep: extracted["địa chỉ trụ sở chính"],
          legalRepName: extracted["tên người đại diện theo pháp luật"],
          // Các trường này bạn có thể thêm vào extractor.py nếu cần
          establishedYear: 0, 
          employees: 0,
        },
        
        // --- CHI TIẾT KHOẢN VAY ---
        loanDetails: {
          amount: formatCurrency(extracted["số tiền đề nghị vay"]),
          purpose: extracted["mục đích vay vốn"],
          term: extracted["thời hạn vay (tháng)"] ? `${extracted["thời hạn vay (tháng)"]} tháng` : null,
          requestedRate: extracted["lãi suất cho vay (%/năm)"] ? `${extracted["lãi suất cho vay (%/năm)"]} %/năm` : null,
          repaymentMethod: extracted["phương thức trả nợ"],
        },

        // --- CÁC CHỈ SỐ TÀI CHÍNH ---
        financialHighlights: [
          {
            label: "Vốn điều lệ",
            value: formatCurrency(extracted["vốn điều lệ"]),
            available: !!extracted["vốn điều lệ"],
          },
          {
            label: "Doanh thu năm gần nhất",
            value: formatCurrency(extracted["doanh thu năm gần nhất"]),
            available: !!extracted["doanh thu năm gần nhất"],
          },
          {
            label: "Lợi nhuận ròng năm gần nhất",
            value: formatCurrency(extracted["lợi nhuận ròng năm gần nhất"]),
            available: !!extracted["lợi nhuận ròng năm gần nhất"],
          },
          {
            label: "Tổng tài sản ước tính",
            value: formatCurrency(extracted["tổng tài sản ước tính"]),
            available: !!extracted["tổng tài sản ước tính"],
          },
        ].filter(item => item.available), // Chỉ giữ lại các mục có dữ liệu

        // --- THÔNG TIN CIC ---
        financialRatios: [
            { label: "Điểm tín dụng (CIC)", value: extracted["điểm tín dụng doanh nghiệp (CIC)"], status: "good" },
            { label: "Xếp hạng (CIC)", value: extracted["xếp hạng tín dụng doanh nghiệp (CIC)"], status: "good" },
            { label: "Phân loại nợ (CIC)", value: extracted["phân loại nợ hiện tại của doanh nghiệp (CIC)"], status: "good"},
            { label: "Tổng dư nợ", value: formatCurrency(extracted["tổng dư nợ tại các tổ chức tín dụng khác"]), status: "warning"},
        ].filter(item => item.value), // Chỉ giữ lại các mục có dữ liệu
        
        // --- ĐÁNH GIÁ TÀI SẢN BẢO ĐẢM ---
        collateralEvaluation: {
          realEstateValue: extracted["loại tài sản bảo đảm chính"],
          totalValue: formatCurrency(extracted["giá trị tài sản bảo đảm theo thẩm định"]),
          ltvRatio: extracted["tỷ lệ cho vay tối đa trên tài sản bảo đảm (%)"] ? `${extracted["tỷ lệ cho vay tối đa trên tài sản bảo đảm (%)"]} %` : null,
          // Các trường khác có thể để trống
          equipmentValue: null,
          adequacy: null,
        },
        
        // --- KẾT LUẬN ---
        conclusion: "Báo cáo được tạo tự động. Chuyên viên tín dụng cần xem xét, xác minh lại thông tin và đưa ra kết luận cuối cùng.",
        riskAssessment: "", // Không còn dùng
        riskFactors: [],
        strengths: [],
        weaknesses: [],
        recommendations: [],
      };

      onDocumentGenerated(documentData);
    }
    setShowFileUpload(false);
  }


  return (
    <div className="flex flex-col h-full bg-white shadow-lg">
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && !showFileUpload && (
          <div className="text-center py-12 animate-fade-in-up">
            <div className="w-16 h-16 bg-red-gradient rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse-red">
              <FileText className="h-8 w-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold mb-2 text-gray-800">Loan Assessment Agent</h3>
            <p className="text-gray-600 mb-6">Trợ lý AI chuyên thẩm định khoản vay</p>

            <div className="mb-6 animate-fade-in-scale flex gap-3 justify-center" style={{ animationDelay: "0.2s" }}>
              {/* <Button
                onClick={handleTestDocument}
                variant="outline"
                className="bg-green-50 border-green-200 text-green-700 hover:bg-green-100 transition-all-smooth hover-lift"
              >
                <TestTube className="h-4 w-4 mr-2" />
                Test Loan Assessment
              </Button> */}

              <Button
                onClick={() => setShowFileUpload(!showFileUpload)}
                variant="outline"
                className="bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100 transition-all-smooth hover-lift"
              >
                <Upload className="h-4 w-4 mr-2" />
                Upload Documents
              </Button>
            </div>

            {!showFileUpload && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-3xl mx-auto">
                {quickActions.map((action, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      handleInputChange({ target: { value: action } } as any)
                    }}
                    className="p-3 text-left bg-red-50 hover:bg-red-100 rounded-lg border border-red-200 transition-all-smooth hover-lift animate-fade-in-up"
                    style={{ animationDelay: `${0.3 + index * 0.1}s` }}
                  >
                    <span className="text-sm font-medium text-gray-700">{action}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* File Upload Section */}
        {showFileUpload && (
          <div className="animate-fade-in-up">
            <FileUploadProcessor
              onProcessComplete={handleFileProcessComplete}
              className="bg-gray-50 p-6 rounded-lg border border-gray-200"
            />

            <div className="mt-4 text-center">
              <Button
                variant="ghost"
                onClick={() => setShowFileUpload(false)}
                className="text-gray-600 hover:text-gray-800"
              >
                Back to Chat
              </Button>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={message.id} className="flex gap-3 animate-fade-in-up" style={{ animationDelay: `${index * 0.1}s` }}>
            <div className="flex-shrink-0">
              {message.role === "user" ? (
                <div className="w-8 h-8 bg-gray-400 rounded-full flex items-center justify-center transition-transform-smooth hover:scale-110">
                  <User className="h-4 w-4 text-white" />
                </div>
              ) : (
                <div className="w-8 h-8 bg-red-gradient rounded-full flex items-center justify-center transition-transform-smooth hover:scale-110">
                  <Bot className="h-4 w-4 text-white" />
                </div>
              )}
            </div>
            <div className="flex-1">
              <div className="bg-gray-50 rounded-lg p-4 shadow-sm hover-lift transition-all-smooth">
                <p className="text-sm text-gray-800 leading-relaxed">
                  {message.content.includes("DOCUMENT_GENERATED:")
                    ? message.content.split("DOCUMENT_GENERATED:")[0].trim()
                    : message.content}
                </p>
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3 animate-fade-in-scale">
            <div className="w-8 h-8 bg-red-gradient rounded-full flex items-center justify-center">
              <Loader2 className="h-4 w-4 text-white animate-spin" />
            </div>
            <div className="flex-1">
              <div className="bg-red-50 rounded-lg p-4 shadow-sm border border-red-200 hover-lift">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 text-red-600 animate-spin" />
                  <span className="text-sm text-red-700 font-medium">Đang thẩm định...</span>
                </div>
                <p className="text-xs text-red-600 mt-1">Hệ thống đang phân tích hồ sơ và tạo báo cáo thẩm định</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {!showFileUpload && (
        <div className="border-t border-red-100 p-4 bg-red-gradient-soft">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <div className="flex-1 relative">
              <Input
                value={input}
                onChange={handleInputChange}
                placeholder="Yêu cầu thẩm định khoản vay..."
                className="pr-12 rounded-lg border-red-200 focus:border-red-400 focus:ring-red-400 transition-all-smooth"
                disabled={isLoading}
              />
              <Button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="absolute right-1 top-1/2 -translate-y-1/2 w-8 h-8 rounded-md bg-red-gradient hover:shadow-lg p-0 transition-all-smooth hover-lift"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
