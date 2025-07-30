#!/bin/bash

# =============================================================================
# Script dừng toàn bộ hệ thống Loan Assessment
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

# Hàm dừng process đang chạy trên port
kill_port() {
    local port=$1
    local service_name=$2
    local pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        log_info "Dừng $service_name trên port $port (PID: $pid)"
        kill -9 $pid 2>/dev/null
        sleep 1
        if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_success "$service_name đã được dừng"
        else
            log_warning "$service_name vẫn đang chạy"
        fi
    else
        log_info "$service_name không đang chạy trên port $port"
    fi
}

# =============================================================================
# MAIN SCRIPT
# =============================================================================

clear
echo "========================================================================="
echo "                     DỪNG HỆ THỐNG LOAN ASSESSMENT                     "
echo "========================================================================="
echo ""

# Chuyển về thư mục project
cd "$PROJECT_ROOT" || {
    log_error "Không thể chuyển đến thư mục project: $PROJECT_ROOT"
    exit 1
}

# 1. Dừng Frontend Docker
log_info "Dừng Frontend Docker containers..."
cd "$FRONTEND_DIR"
sudo docker-compose down
if [ $? -eq 0 ]; then
    log_success "Frontend containers đã được dừng"
else
    log_warning "Có lỗi khi dừng frontend containers"
fi

# 2. Dừng Backend API
kill_port 8000 "Backend API (FastAPI)"

# 3. Dừng Text Embeddings Router
kill_port 8080 "Text Embeddings Router"

# 4. Dừng Qdrant container
log_info "Dừng Qdrant container..."
docker stop qdrant-container 2>/dev/null
docker rm qdrant-container 2>/dev/null
if [ $? -eq 0 ]; then
    log_success "Qdrant container đã được dừng và xóa"
else
    log_info "Qdrant container không tồn tại hoặc đã được dừng"
fi

# 5. Dừng Langflow (nếu có)
kill_port 7860 "Langflow"

# 6. Dừng Prometheus (nếu có)
kill_port 9100 "Prometheus (Text Embeddings)"

# 7. Xóa các file log (tùy chọn)
read -p "Bạn có muốn xóa các file log không? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "$PROJECT_ROOT"
    rm -f text-embeddings.log backend.log
    log_success "Đã xóa các file log"
fi

# 8. Thông báo hoàn tất
echo ""
echo "========================================================================="
echo "                            DỪNG HOÀN TẤT                              "
echo "========================================================================="
echo ""
log_success "Tất cả service đã được dừng!"
echo ""
log_info "Để khởi động lại hệ thống, chạy: ./start.sh"
echo ""
