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
)

export function Template4Preview() {
  return (
    <div className="p-4 bg-white rounded-lg max-w-4xl mx-auto border border-gray-200 font-sans text-sm">
      <div className="text-center mb-4">
        <h1 className="text-lg font-bold text-gray-900 mb-2">BÁO CÁO THẨM ĐỊNH TÍN DỤNG ĐẦY ĐỦ</h1>
        <p className="text-xs text-gray-500">Template4 - Mẫu báo cáo đầy đủ bao gồm thông tin chung, thông tin khách hàng, phân tích chi tiết hoạt động kinh doanh, và thông tin ngành</p>
      </div>

      {/* THÔNG TIN CHUNG */}
      <table className="w-full border-collapse mb-4">
        <tbody>
          <SectionTitle colSpan={4}>THÔNG TIN CHUNG</SectionTitle>
          <tr>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50 w-1/4">Tên đầy đủ của khách hàng</td>
            <td colSpan={3} className="border border-gray-300 px-3 py-2 text-sm font-bold text-gray-800">[CÔNG TY TNHH XYZ TRADING]</td>
          </tr>
          <tr>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Giấy ĐKKD/GP đầu tư</td>
            <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[0987654321]</td>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">ID trên T24</td>
            <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[T24004]</td>
          </tr>
          <tr>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Phân khúc</td>
            <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[COR]</td>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Loại khách hàng</td>
            <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[ETC]</td>
          </tr>
          <tr>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Ngành nghề HĐKD theo ĐKKD</td>
            <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[Thương mại điện tử]</td>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Mục đích báo cáo</td>
            <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[Cấp tín dụng mới]</td>
          </tr>
        </tbody>
      </table>

      {/* THÔNG TIN KHÁCH HÀNG */}
      <table className="w-full border-collapse mb-4">
        <tbody>
          <SectionTitle colSpan={4}>THÔNG TIN KHÁCH HÀNG</SectionTitle>
          <SectionTitle colSpan={4}>1. Thông tin pháp lý</SectionTitle>
          <tr>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Ngày thành lập</td>
            <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[15/03/2020]</td>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Địa chỉ trên ĐKKD</td>
            <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[123 Lê Lợi, Q.1, TP.HCM]</td>
          </tr>
          <SectionTitle colSpan={4}>2. Ban lãnh đạo</SectionTitle>
          <tr>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Tên thành viên</td>
            <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[Nguyễn Văn A]</td>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Chức vụ</td>
            <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[Giám đốc]</td>
          </tr>
        </tbody>
      </table>

      {/* HOẠT ĐỘNG KINH DOANH */}
      <table className="w-full border-collapse mb-4">
        <tbody>
          <SectionTitle colSpan={4}>HOẠT ĐỘNG KINH DOANH</SectionTitle>
          <SectionTitle colSpan={4}>1. Lĩnh vực kinh doanh</SectionTitle>
          <tr>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Lĩnh vực</td>
            <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[Thương mại điện tử]</td>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Sản phẩm/Dịch vụ</td>
            <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[Bán hàng online]</td>
          </tr>
          <SectionTitle colSpan={4}>2. Mô tả sản phẩm</SectionTitle>
          <tr>
            <td colSpan={4} className="border border-gray-300 px-3 py-2 text-sm text-gray-800">
              <strong>Mô tả chung:</strong> [Mô tả chi tiết về sản phẩm/dịch vụ]<br/>
              <strong>Lợi thế cạnh tranh:</strong> [Những lợi thế vượt trội so với đối thủ]<br/>
              <strong>Năng lực đấu thầu:</strong> [Kinh nghiệm và năng lực trong việc đấu thầu]
            </td>
          </tr>
          <SectionTitle colSpan={4}>3. Quy trình vận hành</SectionTitle>
          <tr>
            <td colSpan={4} className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[Mô tả quy trình vận hành từ đặt hàng đến giao hàng]</td>
          </tr>
          <SectionTitle colSpan={4}>4. Phân tích đầu vào - đầu ra</SectionTitle>
          <tr>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Đầu vào - Mặt hàng</td>
            <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[Hàng tiêu dùng]</td>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Đầu ra - Kênh phân phối</td>
            <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">[Online, Offline]</td>
          </tr>
        </tbody>
      </table>

      {/* THÔNG TIN NGÀNH */}
      <table className="w-full border-collapse mb-4">
        <tbody>
          <SectionTitle colSpan={4}>THÔNG TIN NGÀNH</SectionTitle>
          <tr>
            <td colSpan={4} className="border border-gray-300 px-3 py-2 text-sm text-gray-800">
              <strong>Phân tích cung cầu ngành:</strong><br/>
              [Phân tích cung cầu ngành thương mại điện tử, triển vọng phát triển và các yếu tố rủi ro]
              <br/><br/>
              <strong>Nhận xét:</strong><br/>
              [Nhận xét tổng quan về tình hình và triển vọng ngành]
            </td>
          </tr>
        </tbody>
      </table>

      {/* GHI CHÚ */}
      <div className="mt-6 p-3 bg-blue-50 rounded-md border border-blue-200">
        <p className="text-xs text-blue-800 font-medium">
          📋 <strong>Template4:</strong> Mẫu báo cáo thẩm định tín dụng đầy đủ với cấu trúc chi tiết bao gồm tất cả các thông tin về khách hàng, hoạt động kinh doanh và phân tích ngành (không bao gồm biểu đồ).
        </p>
      </div>
    </div>
  )
}
