// Trong file: components/templates/credit-analysis-template.tsx

"use client"
import React from 'react';
import { EditableField } from "@/components/editable-field";

// --- Định nghĩa kiểu dữ liệu (tùy chọn nhưng khuyến khích) ---
// Định nghĩa một kiểu chung cho các bảng trong JSON
interface TableData {
  columns: string[];
  data: Record<string, any>[];
}

// Định nghĩa cấu trúc dữ liệu chính mà component mong đợi
interface ReportData {
  ten_khach_hang?: string;
  so_giay_phep_kinh_doanh?: string;
  id_khach_hang?: string;
  phan_khuc_khach_hang?: string;
  xep_hang_tin_dung?: string;
  ngay_thanh_lap?: string;
  dia_chi_dang_ky_kinh_doanh?: string;
  nguoi_dai_dien_phap_luat?: string;
  kinh_doanh_nganh_nghe_co_dieu_kien?: string;
  linh_vuc_kinh_doanh?: string;
  san_pham_dich_vu?: string;
  // ... các trường text khác
  
  // Các trường dạng bảng
  ban_lanh_dao?: TableData;
  xu_huong_no_12_thang?: TableData;
  so_sanh_doanh_nghiep_cung_nganh?: TableData;
  bao_cao_luu_chuyen_tien_te?: TableData;
  cac_khoan_phai_thu?: TableData;
  
  [key: string]: any; // Cho phép các key khác không được định nghĩa
}


// --- PROPS ---
interface CreditAnalysisReportTemplateProps {
  data: ReportData;
  editingField: string | null;
  onEdit: (fieldId: string) => void;
  onStopEdit: () => void;
  onUpdateField: (path: string, value: any) => void;
}

// --- COMPONENT TEMPLATE CHÍNH ---
export function CreditAnalysisReportTemplate({
  data,
  editingField,
  onEdit,
  onStopEdit,
  onUpdateField,
}: CreditAnalysisReportTemplateProps) {
  
  // --- CÁC HÀM HELPER ---

  // 1. Helper để render một trường có thể chỉnh sửa (giống template4)
  const renderEditableField = (path: string, value: any, options: { multiline?: boolean, className?: string } = {}) => {
    const { multiline = false, className = "" } = options;
    return (
      <EditableField
        value={value || ''} // Đảm bảo value không phải là null/undefined
        fieldId={path}
        onChange={(v: string) => onUpdateField(path, v)}
        displayClassName={`w-full block break-words ${className}`}
        placeholder="Chưa có dữ liệu"
        multiline={multiline}
        editingField={editingField}
        onEdit={onEdit}
        onStopEdit={onStopEdit}
      />
    );
  };

  // 2. Helper để kiểm tra xem dữ liệu bảng có hợp lệ để hiển thị không
  const isValidTable = (table: any): table is TableData => {
    return table && Array.isArray(table.columns) && table.columns.length > 0 && Array.isArray(table.data);
  };

  // 3. Helper ĐA NĂNG để render BẤT KỲ bảng nào theo cấu trúc {columns, data}
  const renderDynamicTable = (tableData: TableData, tablePath: string, title: string) => {
    return (
      <div className="mb-6">
        <h3 className="sub-header font-semibold text-base mb-2">{title}</h3>
        <div className="overflow-x-auto">
            <table>
                <thead>
                    <tr>
                        {tableData.columns.map((colName) => (
                            <th key={colName} className="header-cell">{colName}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {tableData.data.length > 0 ? (
                        tableData.data.map((row, rowIndex) => (
                            <tr key={rowIndex}>
                                {tableData.columns.map((colName) => (
                                    <td key={`${rowIndex}-${colName}`}>
                                        {renderEditableField(
                                            `${tablePath}.data[${rowIndex}].${colName}`,
                                            row[colName],
                                            { multiline: true } // Cho phép multiline để hiển thị nội dung dài
                                        )}
                                    </td>
                                ))}
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td colSpan={tableData.columns.length} className="text-center text-gray-500 py-4">
                                Không có dữ liệu
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
      </div>
    );
  };

  if (!data) {
    return <div className="p-8 text-center">Đang tải dữ liệu báo cáo...</div>
  }

  // --- PHẦN RENDER GIAO DIỆN CHÍNH ---
  return (
    <div id="document-content" className="p-4 md:p-6 max-w-7xl mx-auto bg-white font-sans text-sm text-black">
      {/* CSS dùng chung (giống template4) */}
      <style jsx global>{`
        /* ... Dán toàn bộ CSS từ template4 của bạn vào đây ... */
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { border: 1px solid #000; padding: 6px 8px; vertical-align: top; text-align: left; }
        th { font-weight: bold; }
        .section-title { font-weight: bold; font-size: 1.1em; padding-left: 0; border: none; background-color: transparent; }
        .header-cell { background-color: #f2f2f2; }
        .label-cell { font-weight: bold; width: 25%; }
        .value-cell { font-weight: normal; }
        .sub-header { border: none; padding-left: 0; font-weight: bold; background-color: transparent; }
      `}</style>
      
      {/* SECTION: THÔNG TIN CHUNG (Text fields) */}
      <table>
        <tbody>
          <tr><th colSpan={4} className="section-title">THÔNG TIN CHUNG</th></tr>
          <tr>
            <td className="label-cell">Tên khách hàng</td>
            <td colSpan={3} className="value-cell font-bold">{renderEditableField('ten_khach_hang', data.ten_khach_hang, {className: 'font-bold'})}</td>
          </tr>
          <tr>
            <td className="label-cell">Số GCNĐKDN</td>
            <td className="value-cell">{renderEditableField('so_giay_phep_kinh_doanh', data.so_giay_phep_kinh_doanh)}</td>
            <td className="label-cell">ID Khách hàng</td>
            <td className="value-cell">{renderEditableField('id_khach_hang', data.id_khach_hang)}</td>
          </tr>
          <tr>
            <td className="label-cell">Phân khúc</td>
            <td className="value-cell">{renderEditableField('phan_khuc_khach_hang', data.phan_khuc_khach_hang)}</td>
            <td className="label-cell">XHTD</td>
            <td className="value-cell">{renderEditableField('xep_hang_tin_dung', data.xep_hang_tin_dung)}</td>
          </tr>
        </tbody>
      </table>

      {/* SECTION: THÔNG TIN KHÁCH HÀNG (Text + Table) */}
       <table>
        <tbody>
          <tr><th colSpan={2} className="section-title">1. THÔNG TIN KHÁCH HÀNG</th></tr>
          <tr>
            <td className="label-cell" style={{width: '30%'}}>Ngày thành lập</td>
            <td className="value-cell">{renderEditableField('ngay_thanh_lap', data.ngay_thanh_lap)}</td>
          </tr>
           <tr>
            <td className="label-cell">Địa chỉ ĐKKD</td>
            <td className="value-cell">{renderEditableField('dia_chi_dang_ky_kinh_doanh', data.dia_chi_dang_ky_kinh_doanh, {multiline: true})}</td>
          </tr>
           <tr>
            <td className="label-cell">Người đại diện</td>
            <td className="value-cell">{renderEditableField('nguoi_dai_dien_phap_luat', data.nguoi_dai_dien_phap_luat)}</td>
          </tr>
        </tbody>
      </table>
      {/* Hiển thị bảng Ban lãnh đạo nếu có dữ liệu hợp lệ */}
      {isValidTable(data.ban_lanh_dao) && renderDynamicTable(data.ban_lanh_dao, 'ban_lanh_dao', '1.1 Ban lãnh đạo')}


      {/* SECTION: HOẠT ĐỘNG KINH DOANH */}
      <table>
        <tbody>
          <tr><th colSpan={2} className="section-title">2. HOẠT ĐỘNG KINH DOANH</th></tr>
          <tr>
            <td className="label-cell">Lĩnh vực kinh doanh</td>
            <td className="value-cell">{renderEditableField('linh_vuc_kinh_doanh', data.linh_vuc_kinh_doanh, {multiline: true})}</td>
          </tr>
           <tr>
            <td className="label-cell">Sản phẩm/Dịch vụ</td>
            <td className="value-cell">{renderEditableField('san_pham_dich_vu', data.san_pham_dich_vu, {multiline: true})}</td>
          </tr>
        </tbody>
      </table>

      {/* SECTION: THÔNG TIN NGÀNH */}
      <table><tbody><tr><th className="section-title">3. THÔNG TIN NGÀNH</th></tr></tbody></table>
      {/* Hiển thị bảng so sánh nếu có dữ liệu hợp lệ */}
      {isValidTable(data.so_sanh_doanh_nghiep_cung_nganh) && renderDynamicTable(data.so_sanh_doanh_nghiep_cung_nganh, 'so_sanh_doanh_nghiep_cung_nganh', '3.1 So sánh các doanh nghiệp cùng ngành')}


      {/* SECTION: QUAN HỆ TÍN DỤNG (MỤC MỚI) */}
      <table><tbody><tr><th className="section-title">4. QUAN HỆ TÍN DỤNG</th></tr></tbody></table>
      {/* Hiển thị bảng xu hướng nợ nếu có dữ liệu hợp lệ */}
      {isValidTable(data.xu_huong_no_12_thang) && renderDynamicTable(data.xu_huong_no_12_thang, 'xu_huong_no_12_thang', '4.1 Xu hướng dư nợ 12 tháng gần nhất (ĐVT: triệu VND)')}
      

      {/* SECTION: PHÂN TÍCH TÀI CHÍNH (MỤC MỚI) */}
      <table><tbody><tr><th className="section-title">5. PHÂN TÍCH TÀI CHÍNH</th></tr></tbody></table>
      {/* Hiển thị các bảng tài chính nếu có dữ liệu hợp lệ */}
      {isValidTable(data.bao_cao_luu_chuyen_tien_te) && renderDynamicTable(data.bao_cao_luu_chuyen_tien_te, 'bao_cao_luu_chuyen_tien_te', '5.1 Báo cáo lưu chuyển tiền tệ (gián tiếp)')}
      {isValidTable(data.cac_khoan_phai_thu) && renderDynamicTable(data.cac_khoan_phai_thu, 'cac_khoan_phai_thu', '5.2 Chi tiết các khoản phải thu khách hàng')}

    </div>
  )
}