"use client"
import { Badge } from "@/components/ui/badge"
import { EditableField } from "@/components/editable-field"

// --- INTERFACE MỚI - ĐỊNH NGHĨA THEO MẪU BÁO CÁO MỚI ---
interface LoanAssessmentDataNew {
  headerInfo: {
    bbc: string;
    cbc: string;
    idDeXuat: string;
    ngayBaoCao: string;
    ngayCapNhat: string;
    mucDichThamDinh: string;
    capNoi: string;
  };
  creditInfo: {
    idT24: string;
    xepHangTinDung: string;
    ngayXepHang: string;
    ketQuaPhanNhomTiepCan: string;
    nganh: string;
    phanNhomRuiRo: string;
    phanNhomUngXu: string;
    khacBietHDTD: string;
    ketQuaPhanLuong: string;
    loaiKhoanVay: string;
    tongGiaTriCapTD: string;
    tongGiaTriCoBPHD: string;
    xepHangRuiRo: string;
    ruiRoNganh: string;
    mucDoPhucTap: string;
    tieuChiTaiChinh: string;
    mucDoRuiRo: string;
  };
  businessInfo: {
    tenDayDu: string;
    ngayThanhLap: string;
    loaiHinhCongTy: string;
    hoatDongKinhDoanh: Array<{
      linhVuc: string;
      sanPham: string;
      tyLe: number;
    }>;
    hoatDongKinhDoanhMoTa: string;
    tienDoVanXuat: string;
    khaNangLapKeHoach: string;
  };
  legalInfo: {
    tinhHinhPhapLy: string;
    kinhNghiemChuSoHuu: string;
  };
  tcbRelationship: {
    chatLuongQuanHeTD: string;
    khongViPham: boolean;
    chiTietViPham: string;
    soThangTuongTacT24: string;
    soDuTienGui12Thang: string;
    soLanPhatSinhGiaoDich: string;
    tiLeCoSuDungSPDVKhac: string;
  };
  management: {
    members: Array<{
      ten: string;
      giayToTuyThan: string;
      chucVu: string;
      thanhVienHDQT: string;
      coQuanHeTD: string;
      hoanThanhKiemTraKYC: string;
    }>
  },
  financialStatus: {
    pnl: Array<{
      chiTieu: string;
      period1: string | number;
      period2: string | number;
      growth: string;
    }>;
    businessPlan: Array<{
      chiTieu: string;
      value: string | number;
    }>
  };
}


// --- PROPS - Giữ nguyên để tương thích với logic cha ---
interface LoanAssessmentTemplateProps {
  data: LoanAssessmentDataNew;
  editingField: string | null
  onEdit: (fieldId: string) => void
  onStopEdit: () => void
  onUpdateField: (path: string, value: any) => void
}

// --- COMPONENT CON - Giữ nguyên nhưng tùy chỉnh style một chút ---
const InfoField = ({ label, value, fieldId, onChange, multiline = false, ...props }: any) => {
  const displayValue = value || "N/A"
  const placeholderText = `Nhập ${label.toLowerCase()}`

  return (
    <div className={`border-b border-gray-200 py-2 px-3 ${multiline ? 'col-span-2' : ''}`}>
      <span className="text-xs font-medium text-gray-500 block">{label}</span>
      <EditableField
        value={displayValue}
        fieldId={fieldId}
        onChange={onChange}
        displayClassName={`text-sm font-semibold w-full block break-words mt-1 ${!value ? 'text-gray-400 italic' : 'text-gray-800'}`}
        placeholder={placeholderText}
        multiline={multiline}
        {...props}
      />
    </div>
  )
}

// --- COMPONENT MỚI - Để hiển thị các bảng ---
const ReportTable = ({ headers, rows, fieldPath, onUpdateField, ...props }: any) => {
  return (
    <div className="overflow-x-auto col-span-1 md:col-span-2 lg:col-span-3">
        <table className="min-w-full border border-gray-300 text-sm">
            <thead className="bg-gray-100">
                <tr>
                    {headers.map((header: string, index: number) => (
                        <th key={index} className="py-2 px-3 border-b border-gray-300 text-left font-semibold text-gray-700">{header}</th>
                    ))}
                </tr>
            </thead>
            <tbody>
                {rows.map((row: any, rowIndex: number) => (
                    <tr key={rowIndex} className="hover:bg-gray-50">
                        {Object.keys(row).map((key, cellIndex) => (
                            <td key={cellIndex} className="py-2 px-3 border-b border-gray-200 align-top">
                                <EditableField
                                    value={row[key] || ''}
                                    fieldId={`${fieldPath}[${rowIndex}].${key}`}
                                    onChange={(value: string) => onUpdateField(`${fieldPath}[${rowIndex}].${key}`, value)}
                                    placeholder={`Nhập ${headers[cellIndex]?.toLowerCase() || 'dữ liệu'}`}
                                    displayClassName="text-sm w-full block"
                                    {...props}
                                />
                            </td>
                        ))}
                    </tr>
                ))}
            </tbody>
        </table>
    </div>
  )
}


const SectionTitle = ({ children }: { children: React.ReactNode }) => (
    <h2 className="col-span-1 md:col-span-2 lg:col-span-3 text-base font-bold text-gray-800 bg-gray-100 p-2 border-l-4 border-red-600 mb-2 mt-4">
        {children}
    </h2>
);

// --- COMPONENT TEMPLATE CHÍNH ---
export function LoanAssessmentTemplateNew({
  data,
  editingField,
  onEdit,
  onStopEdit,
  onUpdateField,
}: LoanAssessmentTemplateProps) {
  if (!data) {
    return <div className="p-8 text-center">Đang tải dữ liệu báo cáo...</div>
  }
  
  // Helper để giảm lặp code
  const commonProps = { editingField, onEdit, onStopEdit };

  return (
    <div id="document-content" className="p-4 md:p-8 max-w-7xl mx-auto bg-white shadow-lg animate-fade-in-up font-sans">
      {/* --- HEADER --- */}
      <div className="text-center mb-6">
          <img src="https://inkythuatso.com/uploads/images/2021/09/techcombank-logo-inkythuatso-14-15-51-09.jpg" alt="Techcombank Logo" className="h-10 mx-auto mb-4"/>
          <h1 className="text-xl font-bold text-gray-900">BÁO CÁO THẨM ĐỊNH CHI TIẾT</h1>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-x-4 border-y border-gray-300 py-2 mb-6">
        <InfoField label="BBC" value={data.headerInfo?.bbc} fieldId="headerInfo.bbc" onChange={(v: string) => onUpdateField("headerInfo.bbc", v)} {...commonProps} />
        <InfoField label="CBC" value={data.headerInfo?.cbc} fieldId="headerInfo.cbc" onChange={(v: string) => onUpdateField("headerInfo.cbc", v)} {...commonProps} />
        <InfoField label="ID đề xuất" value={data.headerInfo?.idDeXuat} fieldId="headerInfo.idDeXuat" onChange={(v: string) => onUpdateField("headerInfo.idDeXuat", v)} {...commonProps} />
      </div>

      {/* --- MAIN CONTENT GRID --- */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <InfoField label="ID trên T24" value={data.creditInfo?.idT24} fieldId="creditInfo.idT24" onChange={(v: string) => onUpdateField("creditInfo.idT24", v)} {...commonProps} />
          <InfoField label="Mục đích thẩm định" value={data.headerInfo?.mucDichThamDinh} fieldId="headerInfo.mucDichThamDinh" onChange={(v: string) => onUpdateField("headerInfo.mucDichThamDinh", v)} {...commonProps} />
          <InfoField label="Cấp nơi" value={data.headerInfo?.capNoi} fieldId="headerInfo.capNoi" onChange={(v: string) => onUpdateField("headerInfo.capNoi", v)} {...commonProps} />

          <InfoField label="Ngày hoàn thành báo cáo" value={data.headerInfo?.ngayBaoCao} fieldId="headerInfo.ngayBaoCao" onChange={(v: string) => onUpdateField("headerInfo.ngayBaoCao", v)} {...commonProps} />
          <InfoField label="Ngày cập nhật" value={data.headerInfo?.ngayCapNhat} fieldId="headerInfo.ngayCapNhat" onChange={(v: string) => onUpdateField("headerInfo.ngayCapNhat", v)} {...commonProps} />
          <InfoField label="Xếp hạng tín dụng được phê duyệt" value={data.creditInfo?.xepHangTinDung} fieldId="creditInfo.xepHangTinDung" onChange={(v: string) => onUpdateField("creditInfo.xepHangTinDung", v)} {...commonProps} />
          
          <InfoField label="Ngày xếp hạng tín dụng" value={data.creditInfo?.ngayXepHang} fieldId="creditInfo.ngayXepHang" onChange={(v: string) => onUpdateField("creditInfo.ngayXepHang", v)} {...commonProps} />
          <InfoField label="Kết quả phân nhóm tiếp cận" value={data.creditInfo?.ketQuaPhanNhomTiepCan} fieldId="creditInfo.ketQuaPhanNhomTiepCan" onChange={(v: string) => onUpdateField("creditInfo.ketQuaPhanNhomTiepCan", v)} {...commonProps} />
          <InfoField label="Ngành" value={data.creditInfo?.nganh} fieldId="creditInfo.nganh" onChange={(v: string) => onUpdateField("creditInfo.nganh", v)} {...commonProps} />

          <InfoField label="Phân nhóm rủi ro" value={data.creditInfo?.phanNhomRuiRo} fieldId="creditInfo.phanNhomRuiRo" onChange={(v: string) => onUpdateField("creditInfo.phanNhomRuiRo", v)} {...commonProps} />
          <InfoField label="Phân nhóm ứng xử khách hàng" value={data.creditInfo?.phanNhomUngXu} fieldId="creditInfo.phanNhomUngXu" onChange={(v: string) => onUpdateField("creditInfo.phanNhomUngXu", v)} {...commonProps} />
          <InfoField label="Khác biệt HĐTD" value={data.creditInfo?.khacBietHDTD} fieldId="creditInfo.khacBietHDTD" onChange={(v: string) => onUpdateField("creditInfo.khacBietHDTD", v)} {...commonProps} />

          <InfoField label="Kết quả phân luồng tín dụng" value={data.creditInfo?.ketQuaPhanLuong} fieldId="creditInfo.ketQuaPhanLuong" onChange={(v: string) => onUpdateField("creditInfo.ketQuaPhanLuong", v)} {...commonProps} />
          <InfoField label="Loại khoản vay" value={data.creditInfo?.loaiKhoanVay} fieldId="creditInfo.loaiKhoanVay" onChange={(v: string) => onUpdateField("creditInfo.loaiKhoanVay", v)} {...commonProps} />
          <div />

          <InfoField label="Tổng giá trị cấp tín dụng đề xuất" value={data.creditInfo?.tongGiaTriCapTD} fieldId="creditInfo.tongGiaTriCapTD" onChange={(v: string) => onUpdateField("creditInfo.tongGiaTriCapTD", v)} {...commonProps} />
          <InfoField label="Tổng giá trị có BPHĐ trên tồng dư nợ TCB" value={data.creditInfo?.tongGiaTriCoBPHD} fieldId="creditInfo.tongGiaTriCoBPHD" onChange={(v: string) => onUpdateField("creditInfo.tongGiaTriCoBPHD", v)} {...commonProps} />
          <InfoField label="Xếp hạng rủi ro được phê duyệt" value={data.creditInfo?.xepHangRuiRo} fieldId="creditInfo.xepHangRuiRo" onChange={(v: string) => onUpdateField("creditInfo.xepHangRuiRo", v)} {...commonProps} />

          <InfoField label="Rủi ro ngành" value={data.creditInfo?.ruiRoNganh} fieldId="creditInfo.ruiRoNganh" onChange={(v: string) => onUpdateField("creditInfo.ruiRoNganh", v)} {...commonProps} />
          <InfoField label="Mức độ phức tạp" value={data.creditInfo?.mucDoPhucTap} fieldId="creditInfo.mucDoPhucTap" onChange={(v: string) => onUpdateField("creditInfo.mucDoPhucTap", v)} {...commonProps} />
          <InfoField label="Tiêu chí tài chính" value={data.creditInfo?.tieuChiTaiChinh} fieldId="creditInfo.tieuChiTaiChinh" onChange={(v: string) => onUpdateField("creditInfo.tieuChiTaiChinh", v)} {...commonProps} />
          <InfoField label="Mức độ rủi ro" value={data.creditInfo?.mucDoRuiRo} fieldId="creditInfo.mucDoRuiRo" onChange={(v: string) => onUpdateField("creditInfo.mucDoRuiRo", v)} {...commonProps} />

          <SectionTitle>1. Thông tin cơ bản</SectionTitle>
          <InfoField label="Tên đầy đủ của khách hàng" value={data.businessInfo?.tenDayDu} fieldId="businessInfo.tenDayDu" onChange={(v: string) => onUpdateField("businessInfo.tenDayDu", v)} {...commonProps} multiline />
          <InfoField label="Ngày thành lập" value={data.businessInfo?.ngayThanhLap} fieldId="businessInfo.ngayThanhLap" onChange={(v: string) => onUpdateField("businessInfo.ngayThanhLap", v)} {...commonProps} />
          <InfoField label="Loại hình công ty" value={data.businessInfo?.loaiHinhCongTy} fieldId="businessInfo.loaiHinhCongTy" onChange={(v: string) => onUpdateField("businessInfo.loaiHinhCongTy", v)} {...commonProps} />
          
          <SectionTitle>Hoạt động kinh doanh</SectionTitle>
          <ReportTable
            headers={["Lĩnh vực kinh doanh", "Sản phẩm", "Tỷ lệ doanh thu (%)"]}
            rows={data.businessInfo?.hoatDongKinhDoanh || []}
            fieldPath="businessInfo.hoatDongKinhDoanh"
            onUpdateField={onUpdateField}
            {...commonProps}
          />

          <SectionTitle>Tình hình pháp lý</SectionTitle>
           <InfoField label="Ghi chú" value={data.legalInfo?.tinhHinhPhapLy} fieldId="legalInfo.tinhHinhPhapLy" onChange={(v: string) => onUpdateField("legalInfo.tinhHinhPhapLy", v)} {...commonProps} multiline />

          <SectionTitle>Kinh nghiệm chủ sở hữu</SectionTitle>
           <InfoField label="Ghi chú" value={data.legalInfo?.kinhNghiemChuSoHuu} fieldId="legalInfo.kinhNghiemChuSoHuu" onChange={(v: string) => onUpdateField("legalInfo.kinhNghiemChuSoHuu", v)} {...commonProps} multiline />

          <SectionTitle>Hoạt động kinh doanh của khách hàng</SectionTitle>
           <InfoField label="Mô tả" value={data.businessInfo?.hoatDongKinhDoanhMoTa} fieldId="businessInfo.hoatDongKinhDoanhMoTa" onChange={(v: string) => onUpdateField("businessInfo.hoatDongKinhDoanhMoTa", v)} {...commonProps} multiline />
          
          <SectionTitle>Tiến độ vận xuất</SectionTitle>
           <InfoField label="Mô tả" value={data.businessInfo?.tienDoVanXuat} fieldId="businessInfo.tienDoVanXuat" onChange={(v: string) => onUpdateField("businessInfo.tienDoVanXuat", v)} {...commonProps} multiline />

          <SectionTitle>Khả năng lập và thực hiện kế hoạch</SectionTitle>
           <InfoField label="Mô tả" value={data.businessInfo?.khaNangLapKeHoach} fieldId="businessInfo.khaNangLapKeHoach" onChange={(v: string) => onUpdateField("businessInfo.khaNangLapKeHoach", v)} {...commonProps} multiline />

          <SectionTitle>2. Mối quan hệ với TCB</SectionTitle>
          <InfoField label="Chất lượng quan hệ tín dụng" value={data.tcbRelationship?.chatLuongQuanHeTD} fieldId="tcbRelationship.chatLuongQuanHeTD" onChange={(v: string) => onUpdateField("tcbRelationship.chatLuongQuanHeTD", v)} {...commonProps} />
          <InfoField label="Chi tiết vi phạm" value={data.tcbRelationship?.chiTietViPham} fieldId="tcbRelationship.chiTietViPham" onChange={(v: string) => onUpdateField("tcbRelationship.chiTietViPham", v)} {...commonProps} />
          <InfoField label="Số tháng xem xét trên T24" value={data.tcbRelationship?.soThangTuongTacT24} fieldId="tcbRelationship.soThangTuongTacT24" onChange={(v: string) => onUpdateField("tcbRelationship.soThangTuongTacT24", v)} {...commonProps} />
          <InfoField label="Số dư tiền gửi BQ trong 12 tháng gần nhất" value={data.tcbRelationship?.soDuTienGui12Thang} fieldId="tcbRelationship.soDuTienGui12Thang" onChange={(v: string) => onUpdateField("tcbRelationship.soDuTienGui12Thang", v)} {...commonProps} />

          <SectionTitle>Ban điều hành</SectionTitle>
          <ReportTable
            headers={["Tên", "Giấy tờ tùy thân", "Chức vụ", "Thành viên HĐQT/Chủ sở hữu", "Có quan hệ tín dụng với TCB", "Hoàn thành KYC"]}
            rows={data.management?.members || []}
            fieldPath="management.members"
            onUpdateField={onUpdateField}
            {...commonProps}
          />

          <SectionTitle>Tình hình hoạt động kinh doanh - Kết quả kinh doanh (Đơn vị: Triệu VND)</SectionTitle>
          <ReportTable
            headers={["Tiêu chí", "Năm 2022", "Năm 2023", "Tăng trưởng"]}
            rows={data.financialStatus?.pnl || []}
            fieldPath="financialStatus.pnl"
            onUpdateField={onUpdateField}
            {...commonProps}
          />

          <SectionTitle>Tình hình thực hiện kế hoạch kinh doanh theo hạn mức đã cấp (Đơn vị: Triệu VND)</SectionTitle>
          <ReportTable
            headers={["Tiêu chí", "Giá trị"]}
            rows={data.financialStatus?.businessPlan || []}
            fieldPath="financialStatus.businessPlan"
            onUpdateField={onUpdateField}
            {...commonProps}
          />

      </div>

      {/* --- FOOTER --- */}
      <div className="text-center text-xs text-gray-500 border-t border-gray-200 pt-4 mt-8">
        <p>Báo cáo được tạo tự động bởi Loan Assessment AI • {new Date().toLocaleDateString("vi-VN")}</p>
        <p>Techcombank - Confidential</p>
      </div>
    </div>
  )
}


/*
// --- VÍ DỤ VỀ CẤU TRÚC DỮ LIỆU (ĐỂ TEST) ---
const sampleData: LoanAssessmentDataNew = {
  headerInfo: {
    bbc: 'BBC_SAMPLE',
    cbc: 'CBC_SAMPLE',
    idDeXuat: '12345',
    ngayBaoCao: '07/10/2024',
    ngayCapNhat: '06/09/2024',
    mucDichThamDinh: 'Cấp mới',
    capNoi: 'Hội sở',
  },
  creditInfo: {
    idT24: 'T24-ID-001',
    xepHangTinDung: 'A3',
    ngayXepHang: '06/09/2024',
    ketQuaPhanNhomTiepCan: 'Hạn chế',
    nganh: '17022 - Sản xuất giấy nhăn và bìa nhăn',
    phanNhomRuiRo: 'Rủi ro thấp',
    phanNhomUngXu: 'Nhóm 3',
    khacBietHDTD: 'Có',
    ketQuaPhanLuong: 'Luồng chuyên sâu',
    loaiKhoanVay: 'Vay vốn lưu động',
    tongGiaTriCapTD: '200,000',
    tongGiaTriCoBPHD: '200,000',
    xepHangRuiRo: 'A3',
    ruiRoNganh: 'Cao',
    mucDoPhucTap: 'Thấp',
    tieuChiTaiChinh: 'N/A',
    mucDoRuiRo: 'Cao',
  },
  businessInfo: {
    tenDayDu: 'CÔNG TY TNHH ABC PACKAGING',
    ngayThanhLap: '01/01/2020',
    loaiHinhCongTy: 'Công ty TNHH',
    hoatDongKinhDoanh: [
      { linhVuc: 'Sản xuất bao bì giấy', sanPham: 'Bao bì, vật liệu đóng gói, thùng carton', tyLe: 100 },
    ],
    hoatDongKinhDoanhMoTa: 'Công ty hoạt động trong lĩnh vực sản xuất thùng carton, gia công giấy bìa cứng và hộp giấy, xốp trắng EPS... Tổng giá trị tài sản cố định theo thiết kế là 30 triệu USD. Công suất 2023 - 30% thiết kế, sản tháng 6/2024 đã đạt 50% công suất thiết kế.',
    tienDoVanXuat: 'Quý 02/2021: Khởi công xây dựng. Quý 02/2022: Công ty hoàn thiện lắp đặt hệ thống MMTB. Quý 04/2022: Công ty bắt đầu đi vào sản xuất thử. Doanh thu 2022 đạt 106 tỷ đồng.',
    khaNangLapKeHoach: 'Doanh thu cập nhật 07 tháng đầu năm 2024 đạt 175.2 tỷ, tăng 70% so với cùng kỳ 2023. Doanh thu kế hoạch 2024 là 350 tỷ và 2025 là 438 tỷ đồng.',
  },
  legalInfo: {
    tinhHinhPhapLy: 'Công ty là doanh nghiệp 100% vốn FDI. Vốn điều lệ của công ty: 14.2tr USD, 338 tỷ đồng. Theo thông tin SKY C ngày 14/08/2024 công ty thuộc phân luồng xanh, không có thông tin bất thường.',
    kinhNghiemChuSoHuu: 'Chủ sở hữu hưởng lợi sau cùng của công ty là Tập đoàn A, thành lập năm 1999. Đây là doanh nghiệp lớn, có 30 công ty con hoạt động tại 8 quốc gia.',
  },
  tcbRelationship: {
    chatLuongQuanHeTD: 'Không vi phạm',
    khongViPham: true,
    chiTietViPham: 'Số lượng điểm vi phạm: 0',
    soThangTuongTacT24: 'Chỉ tiết xem tại bàn "Lịch sử đánh giá tuân thủ điều kiện tín dụng"',
    soDuTienGui12Thang: 'Nhóm 1',
    soLanPhatSinhGiaoDich: 'N/A',
    tiLeCoSuDungSPDVKhac: 'N/A',
  },
  management: {
    members: [
      { ten: 'Nguyễn Văn A', giayToTuyThan: '0123456789', chucVu: 'Giám đốc', thanhVienHDQT: 'Không', coQuanHeTD: 'Không', hoanThanhKiemTraKYC: 'Đã hoàn thành' },
    ],
  },
  financialStatus: {
    pnl: [
      { chiTieu: 'Tổng doanh thu', period1: 106513, period2: 223435, growth: '209.77%' },
      { chiTieu: 'Lợi nhuận ròng sau thuế', period1: -37907, period2: -57253, growth: '151.04%' },
      { chiTieu: 'Tổng nợ', period1: 437524, period2: 376088, growth: '85.96%' },
      { chiTieu: 'Tổng vốn chủ sở hữu', period1: 17795, period2: 189228, growth: '1,063.38%' },
    ],
    businessPlan: [
      { chiTieu: 'Doanh thu hàng năm', value: 223435 },
      { chiTieu: 'Lợi nhuận gộp', value: 28575 },
      { chiTieu: 'Lợi nhuận ròng', value: -57253 },
    ],
  },
};
*/