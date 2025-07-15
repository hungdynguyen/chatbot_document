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

export function LoanAssessmentReportPreview() {
  return (
    <div className="p-4 bg-white rounded-lg max-w-4xl mx-auto border border-gray-200 font-sans text-sm">
        <div className="text-center mb-4">
            <h1 className="text-lg font-bold text-gray-900 mb-2">BÁO CÁO THẨM ĐỊNH TÍN DỤNG</h1>
            <p className="text-xs text-gray-500">Mẫu báo cáo chi tiết với thông tin khách hàng và quy định TCB</p>
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
            <SectionTitle colSpan={2}>1. THÔNG TIN KHÁCH HÀNG</SectionTitle>
            <tr>
              <td colSpan={2} className="border-0 px-0 py-2 font-bold text-sm">1.1 Pháp lý của doanh nghiệp</td>
            </tr>
            <InfoField label="Ngày thành lập" value="[15/03/2018]" />
            <InfoField label="Địa chỉ trên ĐKKD" value="[Số 123, Đường ABC, Phường XYZ, Quận 1, TP.HCM]" />
            <InfoField label="Người đại diện theo Pháp luật" value="[Nguyễn Văn A]" />
          </tbody>
        </table>

        {/* BAN LÃNH ĐẠO */}
        <table className="w-full border-collapse mb-4">
          <tbody>
            <tr>
              <td colSpan={5} className="border-0 px-0 py-2 font-bold text-sm">1.2. Ban lãnh đạo, cơ cấu cổ đông/thành viên góp vốn chính</td>
            </tr>
            <tr>
              <th className="border border-gray-300 px-2 py-2 text-xs bg-gray-100">Tên thành viên</th>
              <th className="border border-gray-300 px-2 py-2 text-xs bg-gray-100">Tỷ lệ vốn (%)</th>
              <th className="border border-gray-300 px-2 py-2 text-xs bg-gray-100">Chức vụ</th>
              <th className="border border-gray-300 px-2 py-2 text-xs bg-gray-100">Mức độ ảnh hưởng</th>
              <th className="border border-gray-300 px-2 py-2 text-xs bg-gray-100">Đánh giá</th>
            </tr>
            <tr>
              <td className="border border-gray-300 px-2 py-2 text-sm">[Nguyễn Văn A]</td>
              <td className="border border-gray-300 px-2 py-2 text-sm">[60%]</td>
              <td className="border border-gray-300 px-2 py-2 text-sm">[Giám đốc]</td>
              <td className="border border-gray-300 px-2 py-2 text-sm">[Cao]</td>
              <td className="border border-gray-300 px-2 py-2 text-sm">[Có kinh nghiệm...]</td>
            </tr>
          </tbody>
        </table>

        {/* KIỂM TRA QUY ĐỊNH */}
        <table className="w-full border-collapse">
          <tbody>
            <SectionTitle colSpan={2}>2. KIỂM TRA QUY ĐỊNH, CHÍNH SÁCH TCB</SectionTitle>
            <InfoField label="Khách hàng có phải là người liên quan của TCB" value="[Không]" />
            <InfoField label="Lĩnh vực kinh tế và TPK trọng tâm" value="[FMCG, Retails & Logistics]" />
            <InfoField label="Định hướng tín dụng" value="[Không có khác biệt]" />
          </tbody>
        </table>

        <div className="text-center text-xs text-gray-400 pt-4 mt-4 border-t border-gray-200">
            <p>Đây là bản xem trước. Báo cáo đầy đủ sẽ được tạo sau khi xử lý tài liệu.</p>
        </div>
    </div>
  );
}
