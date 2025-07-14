#!/bin/bash

# =============================================================================
# Script khởi động toàn bộ hệ thống Loan Assessment
# =============================================================================

# Màu sắc cho output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Thư mục gốc của project
PROJECT_ROOT="/root/chatbot"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Hàm để in log với màu sắc
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Hàm kiểm tra port có đang được sử dụng không
# Sử dụng /dev/tcp của bash để kiểm tra kết nối, đáng tin cậy hơn lsof với Docker.
check_port() {
    local port=$1
    # Sử dụng netcat (nc) để kiểm tra cổng. Tùy chọn -z yêu cầu nc
    # quét các cổng đang lắng nghe mà không gửi bất kỳ dữ liệu nào.
    # Đây là phương pháp đáng tin cậy nhất.
    if command -v nc >/dev/null 2>&1; then
        nc -z 127.0.0.1 $port
        return $?
    else
        # Nếu không có nc, quay lại sử dụng /dev/tcp của bash
        (echo > /dev/tcp/127.0.0.1/$port) >/dev/null 2>&1
        return $?
    fi
}

# Hàm dừng process đang chạy trên port
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        log_warning "Dừng process đang chạy trên port $port (PID: $pid)"
        kill -9 $pid 2>/dev/null
        sleep 2
    fi
}

# Hàm kiểm tra Docker có đang chạy không
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker không được khởi động. Vui lòng khởi động Docker trước."
        exit 1
    fi
    log_success "Docker đã sẵn sàng"
}

# Hàm tạo network backend nếu chưa có
create_network() {
    if ! docker network inspect backend >/dev/null 2>&1; then
        log_info "Tạo Docker network 'backend'..."
        docker network create backend
        log_success "Đã tạo network 'backend'"
    else
        log_info "Network 'backend' đã tồn tại"
    fi
}

# =============================================================================
# MAIN SCRIPT
# =============================================================================

clear
echo "========================================================================="
echo "                    KHỞI ĐỘNG HỆ THỐNG LOAN ASSESSMENT                 "
echo "========================================================================="
echo ""

# Chuyển về thư mục project
cd "$PROJECT_ROOT" || {
    log_error "Không thể chuyển đến thư mục project: $PROJECT_ROOT"
    exit 1
}

# 1. Kiểm tra Docker
log_info "Kiểm tra Docker..."
check_docker

# 2. Tạo network Docker
create_network

# 3. Dừng các service cũ nếu có
log_info "Dừng các service cũ nếu có..."
kill_port 6333  # Qdrant
kill_port 8080  # Text Embeddings Router
kill_port 9200  # Prometheus port for embeddings router
kill_port 8000  # FastAPI Backend
kill_port 3002  # Frontend Docker
kill_port 7860  # Langflow (nếu có)

# Dừng containers cũ
docker-compose -f frontend/docker-compose.yml down 2>/dev/null
docker stop qdrant-container 2>/dev/null
docker rm qdrant-container 2>/dev/null

log_success "Đã dọn dẹp các service cũ"

# 4. Khởi động Qdrant
log_info "Khởi động Qdrant Vector Database..."
docker run -d \
    --name qdrant-container \
    --network backend \
    -p 6333:6333 \
    -p 6334:6334 \
    -v "$(pwd)/qdrant_storage:/qdrant/storage:z" \
    qdrant/qdrant

if [ $? -eq 0 ]; then
    log_success "Qdrant đã khởi động thành công trên port 6333"
else
    log_error "Không thể khởi động Qdrant"
    exit 1
fi

# Đợi Qdrant khởi động hoàn toàn
log_info "Đợi Qdrant khởi động hoàn toàn..."
sleep 5

# 5. Khởi động Text Embeddings Router
log_info "Khởi động Text Embeddings Router..."
if [ -f "$HOME/.cargo/bin/text-embeddings-router" ]; then
    nohup ~/.cargo/bin/text-embeddings-router \
        --model-id sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 \
        --port 8080 \
        --prometheus-port 9200 \
        > text-embeddings.log 2>&1 &
    
    # Đợi router khởi động, có thể mất thời gian tải model
    log_info "Đợi Text Embeddings Router khởi động... (tối đa 90 giây)"
    ATTEMPTS=0
    MAX_ATTEMPTS=24 # 18 lần * 5 giây = 90 giây
    while ! check_port 8080 && [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
        ATTEMPTS=$((ATTEMPTS + 1))
        sleep 5
        echo -n "."
    done
    echo ""

    if check_port 8080; then
        log_success "Text Embeddings Router đã khởi động thành công trên port 8080"
    else
        log_error "Không thể khởi động Text Embeddings Router. Kiểm tra log tại text-embeddings.log"
        exit 1
    fi
else
    log_warning "Text Embeddings Router không tìm thấy tại ~/.cargo/bin/text-embeddings-router"
    log_info "Bỏ qua Text Embeddings Router..."
fi

# 6. Khởi động Backend API (FastAPI) trong môi trường Conda
log_info "Khởi động Backend API (FastAPI)..."
(
    # Chạy trong một subshell để đảm bảo môi trường được kích hoạt đúng cách
    log_info "Kích hoạt môi trường Conda 'chatbot_env' cho backend..."
    # Sử dụng '.' thay cho 'source' để tương thích tốt hơn
    . /root/miniconda3/etc/profile.d/conda.sh
    conda activate chatbot_env
    
    # Chuyển vào thư mục backend
    cd "$BACKEND_DIR" || exit 1
    
    # Khởi động FastAPI
    nohup uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
)

# Đợi Backend API khởi động với cơ chế kiểm tra lặp lại
log_info "Đợi Backend API khởi động... (tối đa 60 giây)"
ATTEMPTS=0
MAX_ATTEMPTS=12 # 12 lần * 5 giây = 60 giây
while ! check_port 8000 && [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    ATTEMPTS=$((ATTEMPTS + 1))
    sleep 5
    echo -n "."
done
echo ""

if check_port 8000; then
    log_success "Backend API đã khởi động thành công trên port 8000"
else
    log_error "Không thể khởi động Backend API. Kiểm tra log tại backend.log"
    exit 1
fi

# 7. Khởi động Langflow
log_info "Khởi động Langflow..."
(
    # Chạy trong một subshell để đảm bảo môi trường được kích hoạt đúng cách
    log_info "Kích hoạt môi trường Conda 'chatbot_env' cho Langflow..."
    . /root/miniconda3/etc/profile.d/conda.sh
    conda activate chatbot_env
    
    # Chuyển về thư mục project để file log được tạo đúng chỗ
    cd "$PROJECT_ROOT" || exit 1
    
    # Khởi động Langflow bằng uv run
    nohup uv run langflow run --host 0.0.0.0 --port 7860 > langflow.log 2>&1 &
)

# Đợi Langflow khởi động với cơ chế kiểm tra lặp lại
log_info "Đợi Langflow khởi động... (tối đa 60 giây)"
ATTEMPTS=0
MAX_ATTEMPTS=12 # 12 lần * 5 giây = 60 giây
while ! check_port 7860 && [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    ATTEMPTS=$((ATTEMPTS + 1))
    sleep 5
    echo -n "."
done
echo ""

if check_port 7860; then
    log_success "Langflow đã khởi động thành công trên port 7860"
else
    log_error "Không thể khởi động Langflow. Kiểm tra log tại langflow.log"
    # Không thoát script, chỉ cảnh báo vì Langflow có thể không phải lúc nào cũng cần thiết
fi


# 8. Khởi động Frontend (Next.js với Docker)
log_info "Khởi động Frontend (Next.js với Docker)..."
cd "$FRONTEND_DIR" || {
    log_error "Không thể chuyển đến thư mục frontend: $FRONTEND_DIR"
    exit 1
}

# Build và khởi động frontend container
docker compose up -d 

# Thay vì đợi cố định, chúng ta sẽ lặp và kiểm tra trong tối đa 2 phút
log_info "Đợi Frontend khởi động... (tối đa 120 giây)"
ATTEMPTS=0
MAX_ATTEMPTS=24 # 24 lần * 5 giây = 120 giây
while ! check_port 3002 && [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    ATTEMPTS=$((ATTEMPTS + 1))
    sleep 5
    echo -n "."
done
echo "" # Xuống dòng sau khi các dấu chấm kết thúc

if check_port 3002; then
    log_success "Frontend đã khởi động thành công trên port 3002"
else
    log_error "Không thể khởi động Frontend"
    exit 1
fi

# 9. Hiển thị thông tin tổng kết
echo "========================================================================="
echo "                          KHỞI ĐỘNG HOÀN TẤT                           "
echo "========================================================================="
echo ""
log_success "Tất cả service đã được khởi động thành công!"
echo ""
echo "📊 THÔNG TIN CÁC SERVICE:"
echo "  • Qdrant Vector DB:        http://localhost:6333"
echo "  • Text Embeddings Router:  http://localhost:8080  (nếu có)"
echo "  • Backend API:             http://localhost:8000"
echo "  • Frontend App:            http://localhost:3002"
echo "  • Langflow:                http://localhost:7860"
echo ""
echo "📝 LOG FILES:"
echo "  • Text Embeddings:         $PROJECT_ROOT/text-embeddings.log"
echo "  • Backend API:             $PROJECT_ROOT/backend.log"
echo "  • Langflow:                $PROJECT_ROOT/langflow.log"
echo "  • Frontend Docker:         docker-compose logs"
echo ""
echo "🔧 LỆNH HỮU ÍCH:"
echo "  • Xem log backend:         tail -f $PROJECT_ROOT/backend.log"
echo "  • Xem log langflow:        tail -f $PROJECT_ROOT/langflow.log"
echo "  • Xem log frontend:        docker-compose -f $FRONTEND_DIR/docker-compose.yml logs -f"
echo "  • Dừng tất cả:             ./stop.sh"
echo ""
log_info "Hệ thống đã sẵn sàng sử dụng!"
