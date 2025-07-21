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
    banLanhDao: {
      ten: string;
      tyLeVon: number;
      chucVu: string;
      mucDoAnhHuong: string;
      danhGia: string;
    };
    nhanXet: {
      thongTinChung: string;
      phapLyGpkd: string;
      chuDoanhNghiep: string;
      kyc: string;
    };
  };
  hoatDongKinhDoanh: {
    linhVuc: {
      linhVuc: string;
      sanPham: string;
      tyTrongN1: string;
      tyTrongN: string;
    };
    tyTrongTheoNhomHang: {
      nhomHang: string;
      nam2023: string;
      nam10T2024: string;
    };
    moTaSanPham: {
      sanPham: string;
      loiThe: string;
      nangLucDauThau: string;
    };
    quyTrinhVanHanhText: string;
    dauVao: {
      matHang: string;
      chiTiet: string;
      pttt: string;
    };
    dauRa: {
      kenh: string;
      tyTrong: string;
      pttt: string;
    };
    nhanXetHoatDong: string;
  };
  thongTinNganh: {
    cungCau: string;
    nhanXet: string;
  };
}