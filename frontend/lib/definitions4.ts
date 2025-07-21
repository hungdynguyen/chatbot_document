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
      tyLeVon: number;
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
  hoatDongKinhDoanh: {
    moHinhUrl: string; // URL tới ảnh mô hình kinh doanh
    linhVuc: Array<{
      linhVuc: string;
      sanPham: string;
      tyTrongN1: string;
      tyTrongN: string;
    }>;
    tyTrongTheoNhomHang: Array<{
      nhomHang: string;
      nam2023: string;
      nam10T2024: string;
    }>;
    moTaSanPham: {
      sanPham: string;
      loiThe: string;
      nangLucDauThau: string;
      bieuDoTieuChiUrl: string; // URL tới ảnh biểu đồ 1
      bieuDoKetQuaUrl: string; // URL tới ảnh biểu đồ 2
    };
    quyTrinhVanHanhText: string;
    dauVao: Array<{
      matHang: string;
      chiTiet: string;
      pttt: string;
    }>;
    dauRa: Array<{
      kenh: string;
      tyTrong: string;
      pttt: string;
    }>;
    nhanXetHoatDong: string;
  };
  thongTinNganh: {
    cungCau: string;
    chartUrl: string; 
    nhanXet: string;
  };
}