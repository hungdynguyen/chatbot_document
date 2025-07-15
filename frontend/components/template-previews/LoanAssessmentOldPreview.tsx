"use client"
import { Badge } from "@/components/ui/badge"
import {
  DollarSign,
  Briefcase,
} from "lucide-react"

const ReportSection = ({ icon, title, children }: any) => (
    <section className="mb-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
            {icon}
            {title}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">{children}</div>
    </section>
)

const InfoField = ({ label, value }: { label: string, value: string }) => (
    <div className="p-3 bg-gray-50 rounded-md">
        <span className="text-xs font-medium text-gray-500 block">{label}</span>
        <span className="text-sm font-semibold text-gray-800">{value}</span>
    </div>
)

export function LoanAssessmentOldPreview() {
  return (
    <div className="p-6 bg-white rounded-lg max-w-4xl mx-auto border border-gray-200">
        <div className="text-center mb-6 pb-4 border-b border-red-100">
            <h1 className="text-xl font-bold text-gray-900 mb-2">Báo cáo Thẩm định Khoản vay - [Tên Công ty]</h1>
            <div className="flex justify-center gap-6 text-xs text-gray-500 mb-3">
                <span>Công ty: <strong className="text-red-600">[Tên Công ty]</strong></span>
                <span>Số tiền vay: <strong className="text-red-600">[Số tiền]</strong></span>
            </div>
            <Badge variant="outline" className="text-red-600 border-red-200 bg-red-50">
                Thẩm định Khoản vay
            </Badge>
        </div>

        <section className="mb-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">1. Tóm tắt Thẩm định</h2>
            <div className="text-sm text-gray-600 bg-red-50 p-3 rounded-md">
                <p>Dựa trên phân tích các tài liệu được cung cấp, báo cáo này tóm tắt các thông tin chi tiết về doanh nghiệp và khoản vay đề nghị...</p>
            </div>
        </section>

        <ReportSection icon={<Briefcase className="h-5 w-5 text-red-500" />} title="Thông tin Doanh nghiệp">
            <InfoField label="Tên đầy đủ" value="[Tên công ty TNHH ABC]" />
            <InfoField label="Mã số doanh nghiệp" value="[0102030405]" />
            <InfoField label="Ngành nghề KD chính" value="[Sản xuất/Thương mại...]" />
            <InfoField label="Địa chỉ trụ sở" value="[Địa chỉ chi tiết...]" />
        </ReportSection>

        <ReportSection icon={<DollarSign className="h-5 w-5 text-red-500" />} title="Thông tin Khoản vay Đề xuất">
            <InfoField label="Số tiền đề nghị" value="[1,000,000,000 VND]" />
            <InfoField label="Thời hạn" value="[12 tháng]" />
            <InfoField label="Mục đích" value="[Bổ sung vốn lưu động...]" />
        </ReportSection>
        
        <div className="text-center text-xs text-gray-400 pt-4 mt-4 border-t border-red-100">
            <p>Đây là bản xem trước. Báo cáo đầy đủ sẽ được tạo sau khi xử lý tài liệu.</p>
        </div>
    </div>
  )
}
