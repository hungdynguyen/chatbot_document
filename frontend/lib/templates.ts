// File cấu hình các template có sẵn trong hệ thống
export const AVAILABLE_TEMPLATES = [
  {
    template_id: "template4",
    template_name: "Template4",
    description: "Mẫu báo cáo thẩm định mục 1,3,4."
  },
  {
    template_id: "template_mvp1",
    template_name: "template_mvp1",
    description: "Mẫu báo cáo thẩm định có các text + bảng fix"
  },

];

export type Template = {
  template_id: string;
  template_name: string;
  description: string;
};
