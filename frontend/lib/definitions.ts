// @/lib/definitions.ts

// Định nghĩa cấu trúc dữ liệu cho mẫu báo cáo thẩm định mới.
// Việc tách ra file riêng giúp tái sử dụng và quản lý các kiểu dữ liệu dễ dàng hơn.

export interface ReportData {
  thongTinChung: {
    tenKhachHang: string;
    giayPhep: string;
    idT24: string;
    phanKhuc: string;
    loaiKhachHang: string;
    nganhNghe: string;
    mucDichBaoCao: string;
    ketQuaPhanLuong: string;
    xhtd: string;
  };
  thongTinKhachHang: {
    phapLy: {
      ngayThanhLap: string;
      diaChi: string;
      nguoiDaiDien: string;
      nganhNgheCoDieuKien: string;
    };
    banLanhDao: Array<{
      ten: string;
      tyLeVon: string;
      chucVu: string;
      mucDoAnhHuong: string;
      danhGia: string;
    }>;
    nhanXet: {
      thongTinChung: string;
      phapLyGpkd: string;
      chuDoanhNghiep: string;
      kyc: string;
    };
  };
  kiemTraQuyDinh: {
    nguoiLienQuan: string;
    mucDuNo: string;
    linhVucKinhTe: string;
    dinhHuongTinDung: string;
    offering: string;
    ruiRoMtxh: string;
    quyDinhKhac: string;
  };
}
