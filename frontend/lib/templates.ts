// File cấu hình các template có sẵn trong hệ thống
export const AVAILABLE_TEMPLATES = [
  {
    template_id: "template1",
    template_name: "Template1",
    description: "Mẫu thẩm định tín dụng cũ"
  },
  {
    template_id: "template2", 
    template_name: "Template2",
    description: "Mẫu thẩm định tín dụng mới với cấu trúc chi tiết"
  },
  {
    template_id: "template3",
    template_name: "Template3", 
    description: "Mẫu báo cáo thẩm định chi tiết với thông tin khách hàng và quy định TCB"
  },
  {
    template_id: "template4",
    template_name: "Template4",
    description: "Mẫu báo cáo thẩm định mục 1,3,4."
  }
];

export type Template = {
  template_id: string;
  template_name: string;
  description: string;
};
