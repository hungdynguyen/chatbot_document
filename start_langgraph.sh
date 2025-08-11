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
PROJECT_ROOT="$(dirname "$(realpath "$0")")"
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

echo ""
echo "🔧 FORCE CPU MODE FOR COMPATIBILITY:"
export CUDA_VISIBLE_DEVICES=""
export TORCH_USE_CUDA_DSA=1
export CUDA_LAUNCH_BLOCKING=1
log_success "Đã force CPU mode để tránh lỗi CUDA incompatibility"


echo ""
echo "🧹 CLEANUP & SETUP FOLDERS:"
log_info "Đang xóa và tạo mới các folder output..."

# Tạo timestamp cho session này
CURRENT_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SESSION_ID="session_${CURRENT_TIMESTAMP}_$(openssl rand -hex 4)"

# Xóa các folder output cũ
cd "$PROJECT_ROOT"
if [ -d "backend/parsed_output" ]; then
    rm -rf backend/parsed_output
    log_success "Đã xóa parsed_output cũ"
fi

if [ -d "backend/context" ]; then
    rm -rf backend/context  
    log_success "Đã xóa context cũ"
fi

# Xóa toàn bộ evaluation_results (không backup)
if [ -d "backend/evaluation_results" ]; then
    rm -rf backend/evaluation_results
    log_success "Đã xóa toàn bộ evaluation results cũ"
fi
# Xóa và tạo lại thư mục upload
UPLOAD_DIR="$BACKEND_DIR/upload_files"
if [ -d "$UPLOAD_DIR" ]; then
    rm -rf "$UPLOAD_DIR"
    log_success "Đã xóa thư mục upload cũ."
fi
# Tạo lại folder structure
mkdir -p backend/parsed_output/{docx,pdf,xlsx,txt}
mkdir -p backend/context
mkdir -p backend/evaluation_results/auto_reports
mkdir -p "$UPLOAD_DIR"

# 1. Kiểm tra Docker
log_info "Kiểm tra Docker..."
check_docker

# 2. Tạo network Docker
create_network

# 3. Dừng các service cũ nếu có
log_info "Dừng các service cũ nếu có..."
kill_port 6333  # Qdrant
kill_port 8000  # FastAPI Backend
kill_port 3002  # Frontend Docker

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
    qdrant/qdrant:latest

if [ $? -eq 0 ]; then
    log_success "Qdrant đã khởi động thành công trên port 6333"
else
    log_error "Không thể khởi động Qdrant"
    exit 1
fi

# Đợi Qdrant khởi động hoàn toàn
log_info "Đợi Qdrant khởi động hoàn toàn..."
sleep 5


# 6. Khởi động Backend API (FastAPI) 
log_info "Khởi động Backend API (FastAPI - LangGraph)..."
(
    # Chạy trong một subshell để đảm bảo môi trường được kích hoạt đúng cách
    log_info "Kích hoạt môi trường 'venv' cho backend..."
    if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
        source "$PROJECT_ROOT/venv/bin/activate"
    else
        log_error "Không tìm thấy môi trường ảo 'venv' trong thư mục project root"
        exit 1
    fi
    
    # Chuyển vào thư mục backend
    cd "$BACKEND_DIR" || exit 1
    
    # Khởi động FastAPI
    export PYTHONPATH="$BACKEND_DIR:$PYTHONPATH"
    nohup python -m uvicorn api.main_lang:app --reload --host 0.0.0.0 --port 8000 --loop asyncio > "$PROJECT_ROOT/backend_langgraph.log" 2>&1 &

    # Quay lại thư mục gốc
    cd "$PROJECT_ROOT"
    # nohup uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
)

# Đợi Backend API khởi động với cơ chế kiểm tra lặp lại
log_info "Đợi Backend API khởi động... (tối đa 150 giây)"
ATTEMPTS=0
MAX_ATTEMPTS=60
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



log_success "Đã tạo lại folder structure mới"


echo "========================================================================="
echo "                          KHỞI ĐỘNG HOÀN TẤT                           "
echo "========================================================================="
echo ""
log_success "Tất cả service đã được khởi động thành công!"
echo ""
echo "📊 THÔNG TIN CÁC SERVICE:"
echo "  • Qdrant Vector DB:        http://localhost:6333"
echo "  • Backend API:             http://localhost:8000"
echo "  • Frontend App:            http://localhost:3002"
echo ""
echo "📝 LOG FILES:"
echo "  • Backend API:             $PROJECT_ROOT/backend_langgraph.log"
echo "  • Frontend Docker:         docker-compose logs"
echo ""
echo "🔧 LỆNH HỮU ÍCH:"
echo "  • Xem log backend:         tail -f $PROJECT_ROOT/backend_langgraph.log"
echo "  • Xem log frontend:        docker-compose -f $FRONTEND_DIR/docker-compose.yml logs -f"
echo "  • Dừng tất cả:             ./stop.sh"
echo ""
log_info "Hệ thống đã sẵn sàng sử dụng!"
