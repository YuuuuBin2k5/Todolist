import sqlite3
import os

# --- PHIÊN BẢN ĐÃ SỬA LỖI - LUÔN TẠO FILE ĐÚNG CHỖ ---

# Lấy đường dẫn tuyệt đối đến thư mục chứa file script này (thư mục Data)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Tạo đường dẫn đầy đủ đến file database, nằm cùng thư mục với script
db_path = os.path.join(current_dir, 'todolist_database.db')

print(f"Sẽ tạo database tại: {db_path}")

# Kết nối tới DB bằng đường dẫn đầy đủ và chính xác
conn = sqlite3.connect(db_path)

cursor = conn.cursor()
# 1. Bảng User
print("Đang tạo bảng users...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT UNIQUE NOT NULL,
    user_password TEXT NOT NULL,
    email TEXT NOT NULL
)
""")

# 2. Bảng Group (ĐÃ CẬP NHẬT VỚI LEADER_ID)
print("Đang tạo bảng groups...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS groups (
    group_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT UNIQUE NOT NULL,
    leader_id INTEGER NOT NULL, -- Thêm leader_id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (leader_id) REFERENCES users(user_id) -- Khóa ngoại cho leader_id
)
""")

# 3. Bảng Tasks (Công việc cá nhân)
print("Đang tạo bảng tasks...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    note TEXT,
    is_done INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
""")

# 4. Bảng group_members (Thành viên nhóm)
print("Đang tạo bảng group_members...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS group_members (
    user_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, group_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (group_id) REFERENCES groups(group_id)
)
""")

# 5. Bảng group_tasks (Công việc nhóm)
print("Đang tạo bảng group_tasks...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS group_tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    assignee_id INTEGER,
    title TEXT NOT NULL,
    note TEXT,
    is_done INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_at TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES groups(group_id),
    FOREIGN KEY (assignee_id) REFERENCES users(user_id)
)
""")

# Lưu các thay đổi và đóng kết nối
conn.commit()
conn.close()

print("\nCơ sở dữ liệu đã được tạo thành công với leader_id trong bảng groups!")