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

export function Template2Preview() {
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
            <InfoField label="Xếp hạng tín dụng" value="[BBB+]" />
            <InfoField label="Ngành" value="[Bán lẻ]" />
            <InfoField label="Phân nhóm rủi ro" value="[Thấp]" />
            <InfoField label="Loại khoản vay" value="[SXKD]" />
            <InfoField label="Tổng giá trị cấp TD" value="[5,000,000,000 VND]" />
        </div>
        
        {/* Ghi chú */}
        <div className="mt-6 p-4 bg-green-50 rounded-md border border-green-200">
          <p className="text-sm text-green-800">
            📋 <strong>Template2:</strong> Mẫu thẩm định tín dụng mới với cấu trúc chi tiết và phân tích đa chiều.
          </p>
        </div>
    </div>
  )
}
