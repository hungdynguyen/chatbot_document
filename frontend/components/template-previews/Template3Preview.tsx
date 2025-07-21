"use client"

const InfoField = ({ label, value }: { label: string, value: string }) => (
    <tr>
      <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50 w-1/4">{label}</td>
      <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">{value}</td>
    </tr>
)

const SectionTitle = ({ children, colSpan = 2 }: { children: React.ReactNode, colSpan?: number }) => (
    <tr>
      <td colSpan={colSpan} className="border border-gray-300 px-3 py-2 font-bold text-sm text-gray-900 bg-gray-100">
        {children}
      </td>
    </tr>
);

export function Template3Preview() {
  return (
    <div className="p-4 bg-white rounded-lg max-w-4xl mx-auto border border-gray-200 font-sans text-sm">
        <div className="text-center mb-4">
            <h1 className="text-lg font-bold text-gray-900 mb-2">BÁO CÁO THẨM ĐỊNH TÍN DỤNG</h1>
            <p className="text-xs text-gray-500">Template3 - Mẫu báo cáo chi tiết với thông tin khách hàng và quy định TCB</p>
        </div>

        {/* THÔNG TIN CHUNG */}
        <table className="w-full border-collapse mb-4">
          <tbody>
            <SectionTitle colSpan={4}>THÔNG TIN CHUNG</SectionTitle>
            <tr>
              <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50 w-1/4">Tên đầy đủ của khách hàng</td>
              <td colSpan={3} className="border border-gray-300 px-3 py-2 text-sm font-bold text-gray-800">[CÔNG TY TNHH ABC PHARMA]</td>
            </tr>
            <tr>
              <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Giấy ĐKKD/GP đầu tư</td>
              <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[0123456789]</td>
              <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">ID trên T24</td>
              <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[T24001]</td>
            </tr>
            <tr>
              <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Phân khúc</td>
              <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[SME+]</td>
              <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Loại khách hàng</td>
              <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[ETC]</td>
            </tr>
          </tbody>
        </table>

        {/* THÔNG TIN KHÁCH HÀNG */}
        <table className="w-full border-collapse mb-4">
          <tbody>
            <SectionTitle colSpan={4}>THÔNG TIN KHÁCH HÀNG</SectionTitle>
            
            {/* Pháp lý */}
            <SectionTitle colSpan={4}>1. Thông tin pháp lý</SectionTitle>
            <tr>
              <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Ngày thành lập</td>
              <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[15/03/2018]</td>
              <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Địa chỉ trên ĐKKD</td>
              <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[456 Nguyễn Huệ, Q.1, TP.HCM]</td>
            </tr>
            
            {/* Ban lãnh đạo */}
            <SectionTitle colSpan={4}>2. Ban lãnh đạo</SectionTitle>
            <tr>
              <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Tên thành viên</td>
              <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[Trần Thị B]</td>
              <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Chức vụ</td>
              <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[Tổng Giám đốc]</td>
            </tr>

            {/* KYC & Quy định TCB */}
            <SectionTitle colSpan={4}>3. KYC & Quy định TCB</SectionTitle>
            <tr>
              <td colSpan={4} className="border border-gray-300 px-3 py-2 text-sm text-gray-800">
                [Thông tin về KYC và tuân thủ quy định của Techcombank theo pháp luật]
              </td>
            </tr>
          </tbody>
        </table>

        {/* GHI CHÚ */}
        <div className="mt-6 p-3 bg-yellow-50 rounded-md border border-yellow-200">
          <p className="text-xs text-yellow-800 font-medium">
            📋 <strong>Template3:</strong> Mẫu báo cáo thẩm định tín dụng chi tiết với thông tin khách hàng và quy định TCB.
          </p>
        </div>
    </div>
  )
}
