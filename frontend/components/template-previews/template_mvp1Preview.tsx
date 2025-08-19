"use client"

import React from 'react';
// Import dữ liệu trực tiếp từ file JSON
import reportData from '@/data/template_mvp1.json';

// --- CÁC COMPONENT HELPER ĐỂ GIỮ CODE GỌN GÀNG ---

// Component cho một dòng thông tin (label + value)
const InfoField = ({ label, value }: { label: string; value: React.ReactNode }) => (
  <tr>
    <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50 w-1/4">{label}</td>
    <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800" colSpan={3}>{value || <span className="text-gray-400">N/A</span>}</td>
  </tr>
);

// Component cho tiêu đề của một mục lớn
const SectionTitle = ({ children }: { children: React.ReactNode }) => (
  <tr>
    <td colSpan={4} className="border border-gray-300 px-3 py-2 font-bold text-sm text-gray-900 bg-gray-100">
      {children}
    </td>
  </tr>
);

// Component cho tiêu đề phụ bên trong một mục
const SubHeader = ({ children }: { children: React.ReactNode }) => (
    <h3 className="text-xs font-semibold text-gray-800 mt-3 mb-2 px-1">{children}</h3>
);

// Component để render một bảng động từ dữ liệu { columns, data }
const DynamicTable = ({ tableData, title }: { tableData: any; title: string }) => {
  // Kiểm tra dữ liệu bảng có hợp lệ không
  if (!tableData || !Array.isArray(tableData.columns) || !Array.isArray(tableData.data)) {
    return null; // Không render gì nếu dữ liệu không đúng định dạng
  }

  return (
    <div className="my-4">
      <SubHeader>{title}</SubHeader>
      <div className="overflow-x-auto border border-gray-300 rounded-md">
        <table className="w-full border-collapse">
          <thead className="bg-gray-50">
            <tr>
              {tableData.columns.map((col: string) => (
                <th key={col} className="border-b border-gray-300 px-3 py-2 text-xs font-bold text-gray-600 text-left whitespace-nowrap">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tableData.data.map((row: any, rowIndex: number) => (
              <tr key={rowIndex} className="hover:bg-gray-50 transition-colors">
                {tableData.columns.map((col: string, colIndex: number) => (
                  <td key={colIndex} className="border-t border-gray-200 px-3 py-2 text-sm text-gray-800 whitespace-pre-wrap break-words">
                    {row[col] || <span className="text-gray-400">N/A</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};


// --- COMPONENT PREVIEW CHÍNH ---

export function Template_mvp1_preview() {
  return (
    <div className="p-4 bg-white rounded-lg max-w-5xl mx-auto border border-gray-200 font-sans text-sm">
      <div className="text-center mb-4">
        <h1 className="text-lg font-bold text-gray-900 mb-2">BÁO CÁO PHÂN TÍCH TÍN DỤNG</h1>
        <p className="text-xs text-gray-500">Mẫu báo cáo tổng hợp thông tin khách hàng, quan hệ tín dụng và phân tích tài chính</p>
      </div>

      {/* SECTION: THÔNG TIN CHUNG */}
      <table className="w-full border-collapse mb-4">
        <tbody>
          <SectionTitle>THÔNG TIN CHUNG</SectionTitle>
          <InfoField label="Tên khách hàng" value={<span className="font-bold">{reportData.ten_khach_hang}</span>} />
          <tr>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Số GCNĐKDN</td>
            <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">{reportData.so_giay_phep_kinh_doanh}</td>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">ID Khách hàng</td>
            <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">{reportData.id_khach_hang}</td>
          </tr>
           <tr>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">Phân khúc</td>
            <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">{reportData.phan_khuc_khach_hang}</td>
            <td className="border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50">XHTD</td>
            <td className="border border-gray-300 px-3 py-2 text-sm text-gray-800">{reportData.xep_hang_tin_dung}</td>
          </tr>
        </tbody>
      </table>
      
      {/* SECTION: THÔNG TIN KHÁCH HÀNG */}
      <table className="w-full border-collapse mb-4">
        <tbody>
          <SectionTitle>1. THÔNG TIN KHÁCH HÀNG</SectionTitle>
          <InfoField label="Ngày thành lập" value={reportData.ngay_thanh_lap} />
          <InfoField label="Địa chỉ ĐKKD" value={reportData.dia_chi_dang_ky_kinh_doanh} />
          <InfoField label="Người đại diện" value={reportData.nguoi_dai_dien_phap_luat} />
        </tbody>
      </table>
      <DynamicTable tableData={reportData.ban_lanh_dao} title="1.1 Ban lãnh đạo" />

      {/* SECTION: HOẠT ĐỘNG KINH DOANH */}
       <table className="w-full border-collapse mb-4">
        <tbody>
          <SectionTitle>2. HOẠT ĐỘNG KINH DOANH</SectionTitle>
          <InfoField label="Lĩnh vực kinh doanh" value={reportData.linh_vuc_kinh_doanh} />
          <InfoField label="Sản phẩm/Dịch vụ" value={reportData.san_pham_dich_vu} />
        </tbody>
      </table>

      {/* SECTION: THÔNG TIN NGÀNH */}
      <div className="mb-4">
        <table className="w-full border-collapse">
            <tbody><SectionTitle>3. THÔNG TIN NGÀNH</SectionTitle></tbody>
        </table>
        <DynamicTable tableData={reportData.so_sanh_doanh_nghiep_cung_nganh} title="3.1 So sánh các doanh nghiệp cùng ngành" />
      </div>


      {/* SECTION: QUAN HỆ TÍN DỤNG */}
      <div className="mb-4">
        <table className="w-full border-collapse">
            <tbody><SectionTitle>4. QUAN HỆ TÍN DỤNG</SectionTitle></tbody>
        </table>
        <DynamicTable tableData={reportData.xu_huong_no_12_thang} title="4.1 Xu hướng dư nợ 12 tháng gần nhất (ĐVT: triệu VND)" />
      </div>
      
      {/* SECTION: PHÂN TÍCH TÀI CHÍNH */}
      <div className="mb-4">
        <table className="w-full border-collapse">
            <tbody><SectionTitle>5. PHÂN TÍCH TÀI CHÍNH</SectionTitle></tbody>
        </table>
        <DynamicTable tableData={reportData.bao_cao_luu_chuyen_tien_te} title="5.1 Báo cáo lưu chuyển tiền tệ (gián tiếp)" />
        <DynamicTable tableData={reportData.cac_khoan_phai_thu} title="5.2 Chi tiết các khoản phải thu khách hàng" />
      </div>

      {/* GHI CHÚ */}
      <div className="mt-6 p-3 bg-blue-50 rounded-md border border-blue-200">
        <p className="text-xs text-blue-800 font-medium">
          📋 <strong>Mẫu Phân Tích Tín Dụng:</strong> Template này tập trung vào việc trình bày dữ liệu dạng bảng như thông tin tài chính, so sánh ngành, và lịch sử tín dụng.
        </p>
      </div>
    </div>
  )
}