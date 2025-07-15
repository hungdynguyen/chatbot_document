// File cấu hình các template có sẵn trong hệ thống
export const AVAILABLE_TEMPLATES = [
  {
    template_id: "template_1",
    template_name: "Template 1",
    description: "Mẫu thẩm định tín dụng cũ"
  },
  {
    template_id: "template_2", 
    template_name: "Template 2",
    description: "Mẫu thẩm định tín dụng mới với cấu trúc chi tiết"
  },
  {
    template_id: "template_3",
    template_name: "Template 3", 
    description: "Mẫu báo cáo thẩm định chi tiết với thông tin khách hàng và quy định TCB"
  }
];

export type Template = {
  template_id: string;
  template_name: string;
  description: string;
};
