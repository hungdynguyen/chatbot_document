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

export function Template1Preview() {
  return (
    <div className="p-6 bg-white rounded-lg max-w-4xl mx-auto border border-gray-200">
        <div className="text-center mb-6 pb-4 border-b border-red-100">
            <h1 className="text-xl font-bold text-gray-900 mb-2">Báo cáo Thẩm định Khoản vay - [Tên Công ty]</h1>
            <div className="flex justify-center gap-6 text-xs text-gray-500 mb-3">
                <span>Ngày báo cáo: {new Date().toLocaleDateString()}</span>
                <span>•</span>
                <span>Template1 - Mẫu thẩm định cơ bản</span>
            </div>
        </div>

        {/* Thông tin Doanh nghiệp */}
        <ReportSection icon={<Briefcase className="h-4 w-4 text-blue-600" />} title="1. Thông tin Doanh nghiệp">
            <InfoField label="Tên đầy đủ của doanh nghiệp" value="[Công ty TNHH ABC]" />
            <InfoField label="Mã số doanh nghiệp" value="[0123456789]" />
            <InfoField label="Ngày cấp giấy CNĐKKD" value="[01/01/2020]" />
            <InfoField label="Nơi cấp giấy CNĐKKD" value="[Sở KH & ĐT TP.HCM]" />
            <InfoField label="Địa chỉ trụ sở chính" value="[123 Lê Lợi, Q.1, TP.HCM]" />
            <InfoField label="Ngành nghề kinh doanh chính" value="[Thương mại bán lẻ]" />
            <InfoField label="Vốn điều lệ" value="[5,000,000,000 VND]" />
            <InfoField label="Người đại diện theo pháp luật" value="[Nguyễn Văn A]" />
        </ReportSection>

        {/* Thông tin Khoản vay */}
        <ReportSection icon={<DollarSign className="h-4 w-4 text-green-600" />} title="2. Thông tin Khoản vay">
            <InfoField label="Số tiền đề nghị vay" value="[2,000,000,000 VND]" />
            <InfoField label="Thời hạn vay (tháng)" value="[24 tháng]" />
            <InfoField label="Mục đích vay vốn" value="[Mở rộng kinh doanh]" />
            <InfoField label="Sản phẩm tín dụng đăng ký" value="[Vay sản xuất kinh doanh]" />
            <InfoField label="Lãi suất cho vay (%/năm)" value="[8.5%]" />
            <InfoField label="Phương thức trả nợ" value="[Trả đều hàng tháng]" />
        </ReportSection>

        {/* Ghi chú */}
        <div className="mt-6 p-4 bg-blue-50 rounded-md border border-blue-200">
          <p className="text-sm text-blue-800">
            📋 <strong>Template1:</strong> Mẫu thẩm định tín dụng cơ bản với các trường thông tin cần thiết cho đánh giá khoản vay.
          </p>
        </div>
    </div>
  )
}
