"use client"
import React from 'react';
import { EditableField } from "@/components/editable-field"; 
import { ReportData } from '@/lib/definitions4';

// --- PROPS ---
interface FullLoanReportTemplateProps {
  data: ReportData; // Sử dụng interface ReportData đã định nghĩa ở trên
  editingField: string | null;
  onEdit: (fieldId: string) => void;
  onStopEdit: () => void;
  onUpdateField: (path: string, value: any) => void;
}

// --- COMPONENT TEMPLATE CHÍNH ---
export function FullLoanReportTemplate({
  data,
  editingField,
  onEdit,
  onStopEdit,
  onUpdateField,
}: FullLoanReportTemplateProps) {
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

  return (
    <div id="document-content" className="p-4 md:p-6 max-w-7xl mx-auto bg-white font-sans text-sm text-black">
      {/* CSS dùng chung cho toàn bộ báo cáo */}
      <style jsx global>{`
        table {
          width: 100%;
          border-collapse: collapse;
          margin-bottom: 20px;
        }
        th, td {
          border: 1px solid #000;
          padding: 6px 8px;
          vertical-align: top;
          text-align: left;
        }
        th {
          font-weight: bold;
        }
        .section-title {
            font-weight: bold;
            font-size: 1.1em;
            padding-left: 0;
            border: none;
            background-color: transparent;
        }
        .header-cell {
            background-color: #f2f2f2; /* Màu nền cho header của bảng con */
        }
        .label-cell {
          font-weight: bold;
          width: 25%;
        }
        .value-cell {
          font-weight: normal;
        }
        .no-border-cell {
            border: none;
            padding: 4px 0;
        }
        .sub-header {
            border: none;
            padding-left: 0;
            font-weight: bold;
            background-color: transparent;
        }
        .image-container {
            padding: 10px;
            border: 1px solid #ccc;
            margin: 16px 0;
        }
        .image-container img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: auto;
        }
        .chart-container {
            display: flex;
            gap: 16px;
            margin: 16px 0;
        }
        .chart-container > div {
            flex: 1;
        }
      `}</style>

      {/* SECTION: THÔNG TIN CHUNG */}
      <table>
        <tbody>
          <tr>
            <th colSpan={4} className="section-title">THÔNG TIN CHUNG</th>
          </tr>
          <tr>
            <td className="label-cell">Tên đầy đủ của khách hàng</td>
            <td colSpan={3} className="value-cell font-bold">
              {renderEditableField('thongTinChung.tenKhachHang', data.thongTinChung.tenKhachHang, { className: 'font-bold' })}
            </td>
          </tr>
          <tr>
            <td className="label-cell">Giấy ĐKKD/GP đầu tư</td>
            <td className="value-cell">{renderEditableField('thongTinChung.giayPhep', data.thongTinChung.giayPhep)}</td>
            <td className="label-cell">ID trên T24</td>
            <td className="value-cell">{renderEditableField('thongTinChung.idT24', data.thongTinChung.idT24)}</td>
          </tr>
          <tr>
            <td className="label-cell">Phân khúc</td>
            <td className="value-cell">{renderEditableField('thongTinChung.phanKhuc', data.thongTinChung.phanKhuc)}</td>
            <td className="label-cell">Loại khách hàng</td>
            <td className="value-cell">{renderEditableField('thongTinChung.loaiKhachHang', data.thongTinChung.loaiKhachHang)}</td>
          </tr>
          <tr>
            <td className="label-cell">Ngành nghề HĐKD theo ĐKKD</td>
            <td className="value-cell">{renderEditableField('thongTinChung.nganhNghe', data.thongTinChung.nganhNghe, { multiline: true })}</td>
            <td className="label-cell">Mục đích báo cáo</td>
            <td className="value-cell">{renderEditableField('thongTinChung.mucDichBaoCao', data.thongTinChung.mucDichBaoCao, { multiline: true })}</td>
          </tr>
           <tr>
            <td className="label-cell">Kết quả phân luồng</td>
            <td className="value-cell font-bold text-red-600">
              {renderEditableField('thongTinChung.ketQuaPhanLuong', data.thongTinChung.ketQuaPhanLuong, { className: "text-red-600 font-bold" })}
            </td>
            <td className="label-cell">XHTD</td>
            <td className="value-cell font-bold text-red-600">
               {renderEditableField('thongTinChung.xhtd', data.thongTinChung.xhtd, { className: "text-red-600 font-bold" })}
            </td>
          </tr>
        </tbody>
      </table>

      {/* SECTION: 1. THÔNG TIN KHÁCH HÀNG */}
      <table>
          <tbody>
              <tr><th colSpan={5} className="section-title">1. THÔNG TIN KHÁCH HÀNG</th></tr>
              <tr><td colSpan={5} className="sub-header">1.1. Pháp lý của doanh nghiệp</td></tr>
          </tbody>
      </table>
      <table>
        <tbody>
          <tr>
            <td className="label-cell" style={{width: '30%'}}>Ngày thành lập</td>
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
           <tr><td colSpan={5} className="sub-header">1.2. Ban lãnh đạo, cơ cấu cổ đông/thành viên góp vốn chính</td></tr>
          <tr>
            <th className="header-cell">Tên thành viên góp vốn/ban lãnh đạo</th>
            <th className="header-cell" style={{width: '12%'}}>Tỷ lệ vốn góp (%)</th>
            <th className="header-cell" style={{width: '15%'}}>Chức vụ</th>
            <th className="header-cell" style={{width: '25%'}}>Mức độ ảnh hưởng tới Khách hàng</th>
            <th className="header-cell">Đánh giá về năng lực, uy tín và kinh nghiệm</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{renderEditableField(`thongTinKhachHang.banLanhDao.ten`, data.thongTinKhachHang?.banLanhDao?.ten || '')}</td>
            <td style={{textAlign: 'center'}}>{renderEditableField(`thongTinKhachHang.banLanhDao.tyLeVon`, data.thongTinKhachHang?.banLanhDao?.tyLeVon || '')}</td>
            <td>{renderEditableField(`thongTinKhachHang.banLanhDao.chucVu`, data.thongTinKhachHang?.banLanhDao?.chucVu || '')}</td>
            <td>{renderEditableField(`thongTinKhachHang.banLanhDao.mucDoAnhHuong`, data.thongTinKhachHang?.banLanhDao?.mucDoAnhHuong || '', { multiline: true })}</td>
            <td>{renderEditableField(`thongTinKhachHang.banLanhDao.danhGia`, data.thongTinKhachHang?.banLanhDao?.danhGia || '', { multiline: true })}</td>
          </tr>
        </tbody>
      </table>
      
      <table>
          <tbody>
            <tr><td className="sub-header">1.3 Nhận xét</td></tr>
            <tr>
              <td className="value-cell" style={{ whiteSpace: 'pre-wrap' }}>
                <b>1. Thông tin khách hàng:</b>
                <div className='pl-4'>
                    {renderEditableField('thongTinKhachHang.nhanXet.thongTinChung', data.thongTinKhachHang.nhanXet.thongTinChung, { multiline: true })}
                </div>
                <b>2. Pháp lý/ GPKD có ĐK</b>
                <div className='pl-4'>
                    {renderEditableField('thongTinKhachHang.nhanXet.phapLyGpkd', data.thongTinKhachHang.nhanXet.phapLyGpkd, { multiline: true })}
                </div>
                <b>3. Chủ doanh nghiệp/Ban lãnh đạo:</b>
                <div className='pl-4'>
                    {renderEditableField('thongTinKhachHang.nhanXet.chuDoanhNghiep', data.thongTinKhachHang.nhanXet.chuDoanhNghiep, { multiline: true })}
                </div>
                <b>4.KYC:</b>
                <div className='pl-4'>
                    {renderEditableField('thongTinKhachHang.nhanXet.kyc', data.thongTinKhachHang.nhanXet.kyc, { multiline: true })}
                </div>
              </td>
            </tr>
          </tbody>
      </table>

      {/* SECTION: 3. HOẠT ĐỘNG KINH DOANH */}
      <table><tbody><tr><th className="section-title">3. HOẠT ĐỘNG KINH DOANH</th></tr></tbody></table>

      <table>
        <thead>
            <tr><td colSpan={4} className="sub-header">3.1 Lĩnh vực kinh doanh và sản phẩm</td></tr>
            <tr>
                <th className="header-cell">Lĩnh vực kinh doanh</th>
                <th className="header-cell">Sản phẩm/Dịch vụ</th>
                <th className="header-cell">Tỷ trọng doanh thu năm N-1 (%)</th>
                <th className="header-cell">Tỷ trọng doanh thu năm N (%)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>{renderEditableField(`hoatDongKinhDoanh.linhVuc.linhVuc`, data.hoatDongKinhDoanh?.linhVuc?.linhVuc || '')}</td>
                <td>{renderEditableField(`hoatDongKinhDoanh.linhVuc.sanPham`, data.hoatDongKinhDoanh?.linhVuc?.sanPham || '')}</td>
                <td style={{textAlign: 'center'}}>{renderEditableField(`hoatDongKinhDoanh.linhVuc.tyTrongN1`, data.hoatDongKinhDoanh?.linhVuc?.tyTrongN1 || '')}</td>
                <td style={{textAlign: 'center'}}>{renderEditableField(`hoatDongKinhDoanh.linhVuc.tyTrongN`, data.hoatDongKinhDoanh?.linhVuc?.tyTrongN || '')}</td>
            </tr>
        </tbody>
      </table>
      
      <table>
        <tbody>
            <tr><td className="sub-header no-border-cell">Nhận xét:</td></tr>
            <tr>
                <td className="sub-header no-border-cell">Tỷ trọng doanh thu theo nhóm mặt hàng:</td>
            </tr>
            <tr>
                <td style={{border: 'none', padding: 0}}>
                    <table style={{marginBottom: 0}}>
                        <thead>
                            <tr style={{backgroundColor: '#fffbe6'}}>
                                <th style={{width: '50%'}}>Nhóm mặt hàng</th>
                                <th>2023</th>
                                <th>10T/2024</th>
                            </tr>
                        </thead>
                        <tbody>
                             <tr>
                                <td>{renderEditableField(`hoatDongKinhDoanh.tyTrongTheoNhomHang.nhomHang`, data.hoatDongKinhDoanh?.tyTrongTheoNhomHang?.nhomHang || '')}</td>
                                <td style={{textAlign: 'center'}}>{renderEditableField(`hoatDongKinhDoanh.tyTrongTheoNhomHang.nam2023`, data.hoatDongKinhDoanh?.tyTrongTheoNhomHang?.nam2023 || '')}</td>
                                <td style={{textAlign: 'center'}}>{renderEditableField(`hoatDongKinhDoanh.tyTrongTheoNhomHang.nam10T2024`, data.hoatDongKinhDoanh?.tyTrongTheoNhomHang?.nam10T2024 || '')}</td>
                            </tr>
                        </tbody>
                    </table>
                </td>
            </tr>
            <tr><td className="sub-header no-border-cell">Mô tả thông tin sản phẩm:</td></tr>
            <tr>
                <td className="value-cell" style={{ whiteSpace: 'pre-wrap', border: 'none', paddingLeft: 0 }}>
                    {renderEditableField(`hoatDongKinhDoanh.moTaSanPham.sanPham`, data.hoatDongKinhDoanh.moTaSanPham.sanPham, {multiline: true})}
                    <br/><br/>
                    {renderEditableField(`hoatDongKinhDoanh.moTaSanPham.loiThe`, data.hoatDongKinhDoanh.moTaSanPham.loiThe, {multiline: true})}
                    <br/><br/>
                    {renderEditableField(`hoatDongKinhDoanh.moTaSanPham.nangLucDauThau`, data.hoatDongKinhDoanh.moTaSanPham.nangLucDauThau, {multiline: true})}
                </td>
            </tr>
        </tbody>
      </table>

      <table>
        <tbody>
            <tr><td className="sub-header">3.2 Quy trình vận hành</td></tr>
            <tr>
                <td>{renderEditableField('hoatDongKinhDoanh.quyTrinhVanHanhText', data.hoatDongKinhDoanh.quyTrinhVanHanhText, {multiline: true})}</td>
            </tr>
        </tbody>
      </table>

      <table>
        <thead>
            <tr><th className="sub-header" colSpan={3}>3.3 Đầu vào</th></tr>
            <tr>
                <th className="header-cell" style={{width: '20%'}}>Mặt hàng</th>
                <th className="header-cell"></th>
                <th className="header-cell" style={{width: '40%'}}>PTTT</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>{renderEditableField(`hoatDongKinhDoanh.dauVao.matHang`, data.hoatDongKinhDoanh?.dauVao?.matHang || '')}</td>
                <td>{renderEditableField(`hoatDongKinhDoanh.dauVao.chiTiet`, data.hoatDongKinhDoanh?.dauVao?.chiTiet || '', {multiline: true})}</td>
                <td>{renderEditableField(`hoatDongKinhDoanh.dauVao.pttt`, data.hoatDongKinhDoanh?.dauVao?.pttt || '', {multiline: true})}</td>
            </tr>
        </tbody>
      </table>

      <table>
        <thead>
            <tr><th className="sub-header" colSpan={3}>3.4 Đầu ra</th></tr>
            <tr>
                <th className="header-cell" style={{width: '20%'}}>Kênh</th>
                <th className="header-cell" style={{width: '10%'}}>Tỷ trọng</th>
                <th className="header-cell">PTTT</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>{renderEditableField(`hoatDongKinhDoanh.dauRa.kenh`, data.hoatDongKinhDoanh?.dauRa?.kenh || '')}</td>
                <td style={{textAlign: 'center'}}>{renderEditableField(`hoatDongKinhDoanh.dauRa.tyTrong`, data.hoatDongKinhDoanh?.dauRa?.tyTrong || '')}</td>
                <td>{renderEditableField(`hoatDongKinhDoanh.dauRa.pttt`, data.hoatDongKinhDoanh?.dauRa?.pttt || '', {multiline: true})}</td>
            </tr>
        </tbody>
      </table>

      <table>
          <tbody>
            <tr><td className="sub-header">3.5 Nhận xét</td></tr>
            <tr>
                <td>{renderEditableField('hoatDongKinhDoanh.nhanXetHoatDong', data.hoatDongKinhDoanh.nhanXetHoatDong, {multiline: true})}</td>
            </tr>
          </tbody>
      </table>
      
      {/* SECTION: 4. THÔNG TIN NGÀNH */}
      <table>
        <tbody>
            <tr><th className="section-title" colSpan={2}>4. THÔNG TIN NGÀNH</th></tr>
            <tr><td className="sub-header" colSpan={2}>4.1 Thông tin ngành</td></tr>
            <tr>
                <td colSpan={2} style={{whiteSpace: 'pre-wrap', border: 'none', paddingLeft: 0}}>
                    <b>- Cung cầu ngành:</b>
                    {renderEditableField(`thongTinNganh.cungCau`, data.thongTinNganh.cungCau, {multiline: true})}
                </td>
            </tr>
            <tr><td className="sub-header no-border-cell" colSpan={2}>- Biến động các yếu tố chính của ngành:</td></tr>
            
            <tr><td className="sub-header" colSpan={2}>4.2 Nhận xét</td></tr>
            <tr>
                <td colSpan={2}>
                    {renderEditableField(`thongTinNganh.nhanXet`, data.thongTinNganh.nhanXet, {multiline: true})}
                </td>
            </tr>
        </tbody>
      </table>

    </div>
  )
}