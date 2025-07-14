import type { NextRequest } from "next/server"

export const maxDuration = 30

export async function POST(req: NextRequest) {
  try {
    const { messages } = await req.json()
    const lastMessage = messages[messages.length - 1]?.content || ""
    const input = lastMessage.toLowerCase()

    let response = ""

    if (
      input.includes("thẩm định") ||
      input.includes("khoản vay") ||
      input.includes("tín dụng") ||
      input.includes("loan")
    ) {
      response =
        "Tôi đã tạo báo cáo thẩm định khoản vay cho bạn dựa trên hồ sơ và dữ liệu có sẵn. Báo cáo hiện có độ tin cậy 95% với đầy đủ thông tin cần thiết."

      // Generate loan assessment document
      const documentData = {
        title: "Báo cáo Thẩm định Khoản vay",
        company: "Công ty TNHH Sản xuất ABC",
        loanAmount: "5 tỷ VND",
        period: "2024",
        reportType: "Thẩm định Khoản vay",
        dataAvailability: 95,
        riskScore: 75,
        executiveSummary:
          "Công ty TNHH Sản xuất ABC đề xuất khoản vay <strong>5 tỷ VND</strong> với mục đích mở rộng dây chuyền sản xuất và tăng vốn lưu động. Dựa trên phân tích tài chính và đánh giá rủi ro, công ty thể hiện <em>khả năng trả nợ tốt</em> với điểm rủi ro <strong>75/100</strong>.",
        loanDetails: {
          amount: "5 tỷ VND",
          purpose: "Mở rộng dây chuyền sản xuất và tăng vốn lưu động",
          term: "36 tháng",
          requestedRate: "8.5%/năm",
          repaymentMethod: "Trả gốc và lãi hàng tháng",
        },
        borrowerProfile: {
          companyName: "Công ty TNHH Sản xuất ABC",
          businessType: "Sản xuất thiết bị điện tử",
          establishedYear: 2018,
          employees: 150,
          legalRep: "Nguyễn Văn A",
        },
        financialHighlights: [
          { label: "Doanh thu 2023", value: "<strong>12 tỷ VND</strong>", available: true },
          { label: "Lợi nhuận 2023", value: "<strong>1.8 tỷ VND</strong>", available: true },
          { label: "Tổng tài sản", value: "<strong>8.5 tỷ VND</strong>", available: true },
          { label: "Vốn chủ sở hữu", value: "<strong>5.3 tỷ VND</strong>", available: true },
          { label: "Nợ hiện tại", value: "<strong>1.5 tỷ VND</strong>", available: true },
          { label: "Thu nhập hàng tháng", value: "<strong>250 triệu VND</strong>", available: true },
        ],
        financialRatios: [
          { label: "Tỷ lệ Nợ/Thu nhập", value: "34%", status: "good" },
          { label: "Hệ số thanh toán nợ", value: "2.94", status: "good" },
          { label: "Tỷ số thanh khoản", value: "1.8", status: "warning" },
          { label: "Tỷ số thanh khoản nhanh", value: "1.2", status: "warning" },
        ],
        collateralEvaluation: {
          totalValue: "6.5 tỷ VND",
          realEstateValue: "4 tỷ VND",
          equipmentValue: "2.5 tỷ VND",
          ltvRatio: "76.9%",
          adequacy: "Đủ đảm bảo",
        },
        riskAssessment:
          "Dựa trên phân tích toàn diện, khoản vay có mức độ rủi ro <strong>THẤP</strong>. Công ty TNHH Sản xuất ABC có <em>5 điểm mạnh</em> và <em>4 điểm cần cải thiện</em>. Khả năng trả nợ được đánh giá dựa trên <u>dòng tiền ổn định</u> và <u>tài sản đảm bảo có giá trị</u>.",
        riskFactors: [
          {
            factor: "Biến động thị trường điện tử",
            level: "Trung bình",
            impact: "Có thể ảnh hưởng đến doanh thu 10-15%",
          },
          {
            factor: "Cạnh tranh ngành",
            level: "Cao",
            impact: "Áp lực giảm giá và margin",
          },
        ],
        strengths: [
          "Tăng trưởng doanh thu ổn định 3 năm liên tiếp",
          "Tỷ suất lợi nhuận cao (15% trên doanh thu)",
          "Tài sản đảm bảo có giá trị cao",
          "Lịch sử tín dụng tốt",
        ],
        weaknesses: ["Phụ thuộc vào một số khách hàng lớn", "Ngành có tính cạnh tranh cao", "Vốn lưu động còn hạn chế"],
        recommendations: [
          "Phê duyệt khoản vay với <strong>lãi suất ưu đãi</strong>",
          "Thiết lập <em>hạn mức tín dụng dài hạn</em>",
          "Theo dõi định kỳ báo cáo tài chính <u>hàng quý</u>",
          "Duy trì mối quan hệ tín dụng tốt",
        ],
        conclusion:
          "Sau khi thẩm định kỹ lưỡng, <strong>khuyến nghị PHÊ DUYỆT</strong> khoản vay 5 tỷ VND cho Công ty TNHH Sản xuất ABC. Công ty có <em>tình hình tài chính tốt</em>, <em>khả năng trả nợ cao</em> và <u>tài sản đảm bảo đầy đủ</u>.",
      }

      response += ` DOCUMENT_GENERATED:${JSON.stringify(documentData)}`
    } else {
      response =
        "Chào bạn! Tôi là Loan Assessment Agent, chuyên hỗ trợ thẩm định khoản vay. Tôi có thể giúp bạn:\n\n• Thẩm định khả năng trả nợ\n• Đánh giá rủi ro tín dụng\n• Phân tích tài sản đảm bảo\n• Tạo báo cáo thẩm định chi tiết\n\nHãy cho tôi biết bạn cần thẩm định khoản vay nào?"
    }

    return new Response(
      JSON.stringify({
        id: `chatcmpl-${Date.now()}`,
        object: "chat.completion",
        created: Math.floor(Date.now() / 1000),
        model: "loan-assessment-agent",
        choices: [
          {
            index: 0,
            message: {
              role: "assistant",
              content: response,
            },
            finish_reason: "stop",
          },
        ],
      }),
      {
        headers: {
          "Content-Type": "application/json",
        },
      },
    )
  } catch (error) {
    console.error("Error in chat API:", error)
    return new Response(
      JSON.stringify({
        error: "Internal server error",
        message: "Unable to process request",
      }),
      {
        status: 500,
        headers: {
          "Content-Type": "application/json",
        },
      },
    )
  }
}
