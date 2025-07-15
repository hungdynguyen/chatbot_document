"use client"
import React from 'react';
import { EditableField } from "@/components/editable-field"; 
import { ReportData } from '@/lib/definitions'; // Import cấu trúc dữ liệu từ file riêng

// --- PROPS - Cập nhật để dùng interface mới ---
interface LoanReportTemplateProps {
  data: ReportData;
  editingField: string | null;
  onEdit: (fieldId: string) => void;
  onStopEdit: () => void;
  onUpdateField: (path: string, value: any) => void;
}

// --- COMPONENT CON - Helper để hiển thị text có xuống dòng ---
const MultilineText = ({ text }: { text: string }) => {
  return (
    <>
      {text.split('\n').map((line, index) => (
        <React.Fragment key={index}>
          {line}
          <br />
        </React.Fragment>
      ))}
    </>
  );
};

// --- COMPONENT TEMPLATE CHÍNH ---
export function LoanReportTemplate({
  data,
  editingField,
  onEdit,
  onStopEdit,
  onUpdateField,
}: LoanReportTemplateProps) {
  if (!data) {
    return <div className="p-8 text-center">Đang tải dữ liệu báo cáo...</div>
  }

  const commonProps = { editingField, onEdit, onStopEdit };

  const renderEditableField = (path: string, value: any, options: { multiline?: boolean, className?: string } = {}) => {
    const { multiline = false, className = "" } = options;
    return (
      <EditableField
        value={value}
        fieldId={path}
        onChange={(v: string) => onUpdateField(path, v)}
        displayClassName={`w-full block break-words ${className}`}
        placeholder="Nhập dữ liệu"
        multiline={multiline}
        {...commonProps}
      />
    );
  };
  
  const renderMultilineDisplay = (text: string) => {
     return <MultilineText text={text} />;
  }

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto bg-white font-sans text-sm">
      <style jsx global>{`
        table {
          width: 100%;
          border-collapse: collapse;
          margin-bottom: 16px;
        }
        th, td {
          border: 1px solid #000;
          padding: 6px 8px;
          vertical-align: top;
          text-align: left;
        }
        th {
          font-weight: bold;
          background-color: #f2f2f2;
        }
        .label-cell {
          font-weight: normal;
          width: 25%;
        }
        .value-cell {
          font-weight: normal;
        }
        .section-title {
            font-weight: bold;
            font-size: 1.1em;
            padding-left: 0;
        }
      `}</style>
      
      {/* SECTION: THÔNG TIN CHUNG */}
      <table className="table-fixed">
        <thead>
          <tr>
            <th colSpan={4} className="section-title">THÔNG TIN CHUNG</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className="label-cell">Tên đầy đủ của khách hàng</td>
            <td colSpan={3} className="value-cell font-bold">
              {renderEditableField('thongTinChung.tenKhachHang', data.thongTinChung.tenKhachHang, { className: 'font-bold' })}
            </td>
          </tr>
          <tr>
            <td className="label-cell">Giấy ĐKKD/GP đầu tư</td>
            <td className="value-cell">
              {renderEditableField('thongTinChung.giayPhep', data.thongTinChung.giayPhep)}
            </td>
            <td className="label-cell">ID trên T24</td>
            <td className="value-cell">
              {renderEditableField('thongTinChung.idT24', data.thongTinChung.idT24)}
            </td>
          </tr>
          <tr>
            <td className="label-cell">Phân khúc</td>
            <td className="value-cell">
              {renderEditableField('thongTinChung.phanKhuc', data.thongTinChung.phanKhuc)}
            </td>
            <td className="label-cell">Loại khách hàng</td>
            <td className="value-cell">
              {renderEditableField('thongTinChung.loaiKhachHang', data.thongTinChung.loaiKhachHang)}
            </td>
          </tr>
          <tr>
            <td className="label-cell">Ngành nghề HĐKD theo ĐKKD</td>
            <td className="value-cell">
              {renderEditableField('thongTinChung.nganhNghe', data.thongTinChung.nganhNghe)}
            </td>
            <td className="label-cell">Mục đích báo cáo</td>
            <td className="value-cell">
              {renderEditableField('thongTinChung.mucDichBaoCao', data.thongTinChung.mucDichBaoCao, { multiline: true })}
            </td>
          </tr>
           <tr>
            <td className="label-cell">Kết quả phân luồng</td>
            <td className="value-cell">
              {renderEditableField('thongTinChung.ketQuaPhanLuong', data.thongTinChung.ketQuaPhanLuong, { className: "text-red-600 font-bold" })}
            </td>
            <td className="label-cell font-bold">XHTD</td>
            <td className="value-cell">
               {renderEditableField('thongTinChung.xhtd', data.thongTinChung.xhtd)}
            </td>
          </tr>
        </tbody>
      </table>

      {/* SECTION: 1. THÔNG TIN KHÁCH HÀNG */}
      <table>
        <thead>
          <tr>
            <th colSpan={2} className="section-title">1. THÔNG TIN KHÁCH HÀNG</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td colSpan={2} className='font-bold' style={{border: 'none', paddingLeft: 0}}>1.1 Pháp lý của doanh nghiệp</td>
          </tr>
          <tr>
            <td className="label-cell">Ngày thành lập</td>
            <td className="value-cell">{renderEditableField('thongTinKhachHang.phapLy.ngayThanhLap', data.thongTinKhachHang.phapLy.ngayThanhLap)}</td>
          </tr>
          <tr>
            <td className="label-cell">Địa chỉ trên ĐKKD</td>
            <td className="value-cell">{renderEditableField('thongTinKhachHang.phapLy.diaChi', data.thongTinKhachHang.phapLy.diaChi)}</td>
          </tr>
          <tr>
            <td className="label-cell">Người đại diện theo Pháp luật</td>
            <td className="value-cell">{renderEditableField('thongTinKhachHang.phapLy.nguoiDaiDien', data.thongTinKhachHang.phapLy.nguoiDaiDien)}</td>
          </tr>
          <tr>
            <td className="label-cell">Có kinh doanh Ngành nghề kinh doanh có điều kiện</td>
            <td className="value-cell">{renderEditableField('thongTinKhachHang.phapLy.nganhNgheCoDieuKien', data.thongTinKhachHang.phapLy.nganhNgheCoDieuKien)}</td>
          </tr>
        </tbody>
      </table>

      <table>
        <thead>
           <tr>
            <th colSpan={5} className="font-bold" style={{border: 'none', paddingLeft: 0, backgroundColor: 'transparent'}}>1.2. Ban lãnh đạo, cơ cấu cổ đông/thành viên góp vốn chính</th>
          </tr>
          <tr>
            <th>Tên thành viên góp vốn/ban lãnh đạo</th>
            <th>Tỷ lệ vốn góp (%)</th>
            <th>Chức vụ</th>
            <th>Mức độ ảnh hưởng tới Khách hàng</th>
            <th>Đánh giá về năng lực, uy tín và kinh nghiệm</th>
          </tr>
        </thead>
        <tbody>
          {data.thongTinKhachHang.banLanhDao.map((member, index) => (
            <tr key={index}>
              <td>{renderEditableField(`thongTinKhachHang.banLanhDao[${index}].ten`, member.ten)}</td>
              <td>{renderEditableField(`thongTinKhachHang.banLanhDao[${index}].tyLeVon`, member.tyLeVon)}</td>
              <td>{renderEditableField(`thongTinKhachHang.banLanhDao[${index}].chucVu`, member.chucVu)}</td>
              <td>{renderEditableField(`thongTinKhachHang.banLanhDao[${index}].mucDoAnhHuong`, member.mucDoAnhHuong)}</td>
              <td>{renderEditableField(`thongTinKhachHang.banLanhDao[${index}].danhGia`, member.danhGia, { multiline: true })}</td>
            </tr>
          ))}
        </tbody>
      </table>
      
      <table>
          <tbody>
            <tr>
              <td colSpan={2} className='font-bold' style={{border: 'none', paddingLeft: 0}}>1.3 Nhận xét</td>
            </tr>
            <tr>
              <td className="value-cell" colSpan={2} style={{ whiteSpace: 'pre-wrap' }}>
                <b>1. Thông tin khách hàng:</b>
                {renderEditableField('thongTinKhachHang.nhanXet.thongTinChung', data.thongTinKhachHang.nhanXet.thongTinChung, { multiline: true })}
                <br/><br/>
                <b>2. Pháp lý/ GPKD có ĐK</b>
                {renderEditableField('thongTinKhachHang.nhanXet.phapLyGpkd', data.thongTinKhachHang.nhanXet.phapLyGpkd, { multiline: true })}
                <br/><br/>
                <b>3. Chủ doanh nghiệp/Ban lãnh đạo:</b>
                {renderEditableField('thongTinKhachHang.nhanXet.chuDoanhNghiep', data.thongTinKhachHang.nhanXet.chuDoanhNghiep, { multiline: true })}
                <br/><br/>
                <b>4. KYC:</b>
                {renderEditableField('thongTinKhachHang.nhanXet.kyc', data.thongTinKhachHang.nhanXet.kyc, { multiline: true })}
              </td>
            </tr>
          </tbody>
      </table>


      {/* SECTION: 2. KIỂM TRA QUY ĐỊNH, CHÍNH SÁCH TCB */}
      <table>
        <thead>
          <tr>
            <th colSpan={2} className="section-title">2. KIỂM TRA QUY ĐỊNH, CHÍNH SÁCH TCB</th>
          </tr>
        </thead>
        <tbody>
            <tr>
                <td className="label-cell">Khách hàng có phải là người liên quan của TCB theo quy định Pháp luật</td>
                <td className="value-cell">{renderEditableField('kiemTraQuyDinh.nguoiLienQuan', data.kiemTraQuyDinh.nguoiLienQuan)}</td>
            </tr>
            <tr>
                <td className="label-cell">Mức dư nợ cấp tín dụng của Khách hàng và NLQ của Khách hàng theo quy định Pháp luật</td>
                <td className="value-cell">{renderEditableField('kiemTraQuyDinh.mucDuNo', data.kiemTraQuyDinh.mucDuNo, { multiline: true })}</td>
            </tr>
            <tr>
                <td className="label-cell">Lĩnh vực kinh tế và TPK trọng tâm</td>
                <td className="value-cell">{renderEditableField('kiemTraQuyDinh.linhVucKinhTe', data.kiemTraQuyDinh.linhVucKinhTe, { multiline: true })}</td>
            </tr>
            <tr>
                <td className="label-cell">Định hướng tín dụng</td>
                <td className="value-cell">{renderEditableField('kiemTraQuyDinh.dinhHuongTinDung', data.kiemTraQuyDinh.dinhHuongTinDung)}</td>
            </tr>
            <tr>
                <td className="label-cell">Offering/ CTKD</td>
                <td className="value-cell">{renderEditableField('kiemTraQuyDinh.offering', data.kiemTraQuyDinh.offering, { multiline: true })}</td>
            </tr>
            <tr>
                <td className="label-cell">Đánh giá Rủi ro môi trường xã hội</td>
                <td className="value-cell">{renderEditableField('kiemTraQuyDinh.ruiRoMtxh', data.kiemTraQuyDinh.ruiRoMtxh)}</td>
            </tr>
            <tr>
                <td className="label-cell">Quy định khác (nếu có)</td>
                <td className="value-cell">{renderEditableField('kiemTraQuyDinh.quyDinhKhac', data.kiemTraQuyDinh.quyDinhKhac)}</td>
            </tr>
        </tbody>
      </table>
    </div>
  )
}
