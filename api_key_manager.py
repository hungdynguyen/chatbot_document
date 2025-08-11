import time

class ApiKeyManager:
    """Quản lý danh sách API key và tự động chuyển đổi khi cần."""
    
    def __init__(self, api_keys: list):
        if not api_keys or not isinstance(api_keys, list):
            raise ValueError("Cần cung cấp một danh sách API key không rỗng.")
        self.api_keys = api_keys
        self.current_index = 0
        self.initial_index = 0

    def get_current_key(self) -> str:
        """Lấy key hiện tại."""
        return self.api_keys[self.current_index]

    def switch_to_next_key(self):
        """
        Chuyển sang key tiếp theo trong danh sách.
        Trả về True nếu đã quay vòng lại từ đầu, False nếu chưa.
        """
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        new_key = self.get_current_key()
        masked_key = f"{new_key[:8]}...{new_key[-5:]}" 
        print(f"🔄 Đã chuyển sang API key index {self.current_index}: {masked_key}")
        # Nếu quay vòng về key ban đầu, có thể tất cả các key đều đã hết hạn
        return self.current_index == self.initial_index