"use client"

const InfoField = ({ label, value }: { label: string, value: string }) => (
    <div className="border-b border-gray-200 py-2 px-3">
      <span className="text-xs font-medium text-gray-500 block">{label}</span>
      <span className="text-sm font-semibold text-gray-800">{value}</span>
    </div>
)

const SectionTitle = ({ children }: { children: React.ReactNode }) => (
    <h2 className="col-span-1 md:col-span-2 lg:col-span-3 text-base font-bold text-gray-800 bg-gray-100 p-2 border-l-4 border-red-600 mt-4">
        {children}
    </h2>
);

export function LoanAssessmentNewPreview() {
  return (
    <div className="p-6 bg-white rounded-lg max-w-4xl mx-auto border border-gray-200 font-sans">
        <div className="text-center mb-4">
            <img src="https://inkythuatso.com/uploads/images/2021/09/techcombank-logo-inkythuatso-14-15-51-09.jpg" alt="Techcombank Logo" className="h-8 mx-auto mb-3"/>
            <h1 className="text-xl font-bold text-gray-900">BÁO CÁO THẨM ĐỊNH CHI TIẾT</h1>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-x-4 border-y border-gray-300 py-1 mb-4">
            <InfoField label="BBC" value="[BBC_SAMPLE]" />
            <InfoField label="CBC" value="[CBC_SAMPLE]" />
            <InfoField label="ID đề xuất" value="[12345]" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-4">
            <InfoField label="ID trên T24" value="[T24-ID-001]" />
            <InfoField label="Mục đích thẩm định" value="[Cấp mới]" />
            <InfoField label="Cấp nơi" value="[Hội sở]" />
            <InfoField label="Ngày hoàn thành báo cáo" value="[dd/mm/yyyy]" />
            <InfoField label="Xếp hạng tín dụng" value="[A3]" />
            <InfoField label="Ngành" value="[Sản xuất...]" />

            <SectionTitle>1. Thông tin cơ bản</SectionTitle>
            <InfoField label="Tên đầy đủ của khách hàng" value="[CÔNG TY TNHH ABC PACKAGING]" />
            <InfoField label="Ngày thành lập" value="[dd/mm/yyyy]" />
            <InfoField label="Loại hình công ty" value="[Công ty TNHH]" />
        </div>

        <div className="text-center text-xs text-gray-400 pt-4 mt-4 border-t border-gray-200">
            <p>Đây là bản xem trước. Báo cáo đầy đủ sẽ được tạo sau khi xử lý tài liệu.</p>
        </div>
    </div>
  )
}
