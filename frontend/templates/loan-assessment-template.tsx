// Trong file: templates/loan-assessment-template.tsx

"use client"
import { Badge } from "@/components/ui/badge"
import {
  FileText,
  DollarSign,
  Landmark,
  ShieldCheck,
  BarChart2,
  Briefcase,
  UserCheck,
} from "lucide-react"
import { EditableField } from "@/components/editable-field"

// --- INTERFACE GIỮ NGUYÊN ---
interface LoanAssessmentData {
  //... (giữ nguyên không thay đổi)
  title: string
  company: string
  loanAmount: string
  period: string
  reportType: string
  dataAvailability: number
  riskScore: number
  executiveSummary: string
  loanDetails: {
    amount: string
    purpose: string
    term: string
    requestedRate: string
    repaymentMethod: string
  }
  borrowerProfile: {
    companyName: string
    businessType: string // mã số doanh nghiệp
    legalRep: string // địa chỉ trụ sở
    establishedYear: number
    employees: number
    mainBusiness: string // ngành nghề chính
    legalRepName: string // tên người đại diện
  }
  financialHighlights: Array<{
    label: string
    value: string | number
    available: boolean
  }>
  financialRatios: Array<{
    label:string
    value:string
    status: "good" | "warning" | "poor"
  }>
  collateralEvaluation: {
    totalValue: string
    realEstateValue: string // loại tài sản
    equipmentValue: string
    ltvRatio: string
    adequacy: string
  }
  riskAssessment: string
  riskFactors: Array<any>
  strengths: string[]
  weaknesses: string[]
  recommendations: string[]
  conclusion: string
}

// Props của Template
interface LoanAssessmentTemplateProps {
  data: any; // Dùng any để linh hoạt
  editingField: string | null
  onEdit: (fieldId: string) => void
  onStopEdit: () => void
  onUpdateField: (path: string, value: string) => void
}

// --- COMPONENT CON ĐỂ HIỂN THỊ TRƯỜNG DỮ LIỆU (SỬA LẠI ĐỂ NHẬN onCHANGE) ---
const InfoField = ({ label, value, fieldId, multiline = false, onChange, ...props }: any) => {
  const displayValue = value || "---"
  const placeholderText = `Nhập ${label.toLowerCase()}`

  return (
    <div className={`p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-all-smooth ${multiline ? 'md:col-span-2' : ''}`}>
      <span className="text-sm font-medium text-gray-600 block mb-1">{label}</span>
      <EditableField
        value={displayValue}
        fieldId={fieldId}
        onChange={onChange} // <--- SỬA Ở ĐÂY: Truyền hàm onChange xuống
        displayClassName={`text-sm font-semibold cursor-pointer hover:bg-white hover:border-gray-200 px-2 py-1 rounded transition-all-smooth w-full ${!value ? 'text-gray-400 italic' : ''}`}
        placeholder={placeholderText}
        multiline={multiline}
        {...props}
      />
    </div>
  )
}

// Component Section không đổi
const ReportSection = ({ icon, title, children }: any) => {
    // ... code giữ nguyên ...
    return (
        <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-3">
                {icon}
                {title}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">{children}</div>
        </section>
    )
}

export function LoanAssessmentTemplate({
  data,
  editingField,
  onEdit,
  onStopEdit,
  onUpdateField,
}: LoanAssessmentTemplateProps) {
  if (!data) {
    return <div className="p-8 text-center">Đang tải...</div>
  }

  // Loại bỏ commonEditableProps, chúng ta sẽ truyền trực tiếp
  
  return (
    <div className="p-8 max-w-4xl mx-auto animate-fade-in-up">
      {/* --- HEADER --- */}
      <div className="text-center mb-8 pb-6 border-b border-red-100">
        <EditableField
          value={data.title}
          onChange={(value) => onUpdateField("title", value)}
          fieldId="title"
          className="text-2xl font-bold text-center border-none focus-visible:ring-0"
          displayClassName="text-2xl font-bold text-gray-900 mb-2 hover:bg-red-50 hover:border-red-200"
          placeholder="Tiêu đề báo cáo"
          editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit}
        />
        <div className="flex justify-center flex-wrap gap-x-8 gap-y-2 text-sm text-gray-600 mb-4">
          <span>
            Công ty: <strong className="text-red-600">{data.company || "Chưa xác định"}</strong>
          </span>
          <span>
            Số tiền vay: <strong className="text-red-600">{data.loanAmount || "Chưa xác định"}</strong>
          </span>
        </div>
        <Badge variant="outline" className="text-red-600 border-red-200 bg-red-50 transition-all-smooth">
          {data.reportType}
        </Badge>
      </div>

      {/* --- TÓM TẮT --- */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">1. Tóm tắt Thẩm định</h2>
        <EditableField
          value={data.executiveSummary}
          onChange={(value) => onUpdateField("executiveSummary", value)}
          fieldId="executiveSummary"
          className="min-h-[120px] text-sm leading-relaxed"
          displayClassName="text-sm leading-relaxed text-gray-700 bg-red-50 p-4 rounded-lg hover:bg-red-100 hover:border-red-200 transition-all-smooth w-full"
          placeholder="Tóm tắt sẽ được tạo ở đây..."
          multiline
          editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit}
        />
      </section>

      {/* --- CÁC PHẦN DỮ LIỆU --- */}
      
      <ReportSection icon={<Briefcase className="h-5 w-5 text-red-500" />} title="Thông tin Doanh nghiệp">
          <InfoField label="Tên đầy đủ" value={data.borrowerProfile?.companyName} fieldId="borrowerProfile.companyName" onChange={(v: string) => onUpdateField("borrowerProfile.companyName", v)} editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit} multiline />
          <InfoField label="Mã số doanh nghiệp" value={data.borrowerProfile?.businessType} fieldId="borrowerProfile.businessType" onChange={(v: string) => onUpdateField("borrowerProfile.businessType", v)} editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit} />
          <InfoField label="Ngành nghề KD chính" value={data.borrowerProfile?.mainBusiness} fieldId="borrowerProfile.mainBusiness" onChange={(v: string) => onUpdateField("borrowerProfile.mainBusiness", v)} editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit} />
          <InfoField label="Địa chỉ trụ sở" value={data.borrowerProfile?.legalRep} fieldId="borrowerProfile.legalRep" onChange={(v: string) => onUpdateField("borrowerProfile.legalRep", v)} editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit} multiline />
      </ReportSection>

      <ReportSection icon={<UserCheck className="h-5 w-5 text-red-500" />} title="Người đại diện Pháp luật">
          <InfoField label="Họ và tên" value={data.borrowerProfile?.legalRepName} fieldId="borrowerProfile.legalRepName" onChange={(v: string) => onUpdateField("borrowerProfile.legalRepName", v)} editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit} />
          <InfoField label="Chức vụ" value={data.borrowerProfile?.legalRepPosition} fieldId="borrowerProfile.legalRepPosition" onChange={(v: string) => onUpdateField("borrowerProfile.legalRepPosition", v)} editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit} />
          <InfoField label="Số CCCD/CMND" value={data.borrowerProfile?.legalRepId} fieldId="borrowerProfile.legalRepId" onChange={(v: string) => onUpdateField("borrowerProfile.legalRepId", v)} editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit} />
      </ReportSection>

      <ReportSection icon={<DollarSign className="h-5 w-5 text-red-500" />} title="Thông tin Khoản vay Đề xuất">
          <InfoField label="Số tiền đề nghị" value={data.loanDetails?.amount} fieldId="loanDetails.amount" onChange={(v: string) => onUpdateField("loanDetails.amount", v)} editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit} />
          <InfoField label="Thời hạn" value={data.loanDetails?.term} fieldId="loanDetails.term" onChange={(v: string) => onUpdateField("loanDetails.term", v)} editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit} />
          <InfoField label="Lãi suất đề xuất" value={data.loanDetails?.requestedRate} fieldId="loanDetails.requestedRate" onChange={(v: string) => onUpdateField("loanDetails.requestedRate", v)} editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit} />
          <InfoField label="Phương thức trả nợ" value={data.loanDetails?.repaymentMethod} fieldId="loanDetails.repaymentMethod" onChange={(v: string) => onUpdateField("loanDetails.repaymentMethod", v)} editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit} />
          <InfoField label="Mục đích" value={data.loanDetails?.purpose} fieldId="loanDetails.purpose" onChange={(v: string) => onUpdateField("loanDetails.purpose", v)} editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit} multiline />
      </ReportSection>

      <ReportSection icon={<BarChart2 className="h-5 w-5 text-red-500" />} title="Thông tin Tài chính">
          {data.financialHighlights?.map((item: any, index: number) => (
             <InfoField key={index} label={item.label} value={item.value} fieldId={`financialHighlights[${index}].value`} onChange={(v: string) => onUpdateField(`financialHighlights[${index}].value`, v)} editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit} />
          ))}
      </ReportSection>

      <ReportSection icon={<Landmark className="h-5 w-5 text-red-500" />} title="Tài sản Bảo đảm">
          <InfoField label="Loại tài sản chính" value={data.collateralEvaluation?.realEstateValue} fieldId="collateralEvaluation.realEstateValue" onChange={(v: string) => onUpdateField("collateralEvaluation.realEstateValue", v)} editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit} multiline />
          <InfoField label="Giá trị thẩm định" value={data.collateralEvaluation?.totalValue} fieldId="collateralEvaluation.totalValue" onChange={(v: string) => onUpdateField("collateralEvaluation.totalValue", v)} editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit} />
          <InfoField label="Tỷ lệ cho vay/TSBĐ" value={data.collateralEvaluation?.ltvRatio} fieldId="collateralEvaluation.ltvRatio" onChange={(v: string) => onUpdateField("collateralEvaluation.ltvRatio", v)} editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit} />
      </ReportSection>

      <ReportSection icon={<ShieldCheck className="h-5 w-5 text-red-500" />} title="Thông tin Tín dụng (CIC)">
          {data.financialRatios?.map((item: any, index: number) => (
             <InfoField key={index} label={item.label} value={item.value} fieldId={`financialRatios[${index}].value`} onChange={(v: string) => onUpdateField(`financialRatios[${index}].value`, v)} editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit} />
          ))}
      </ReportSection>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">2. Khuyến nghị & Kết luận</h2>
        <EditableField
          value={data.conclusion}
          onChange={(value) => onUpdateField("conclusion", value)}
          fieldId="conclusion"
          className="min-h-[100px] text-sm leading-relaxed"
          displayClassName="text-sm leading-relaxed text-gray-700 bg-blue-50 p-4 rounded-lg hover:bg-blue-100 hover:border-blue-200 transition-all-smooth w-full"
          placeholder="Nhập kết luận và khuyến nghị tại đây..."
          multiline
          editingField={editingField} onEdit={onEdit} onStopEdit={onStopEdit}
        />
      </section>

      <div className="text-center text-sm text-gray-500 border-t border-red-100 pt-4 mt-8">
        <p>Báo cáo được tạo tự động bởi Loan Assessment AI • {new Date().toLocaleDateString("vi-VN")}</p>
      </div>
    </div>
  )
}