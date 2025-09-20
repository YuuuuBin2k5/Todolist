import os
import sqlite3

# ==============================================================================
# PHẦN DÀNH CHO BẠN: ĐIỀN DỮ LIỆU CỦA BẠN VÀO CÁC DANH SÁCH DƯỚI ĐÂY
# ==============================================================================

# --- 1. Dữ liệu người dùng ---
# Định dạng: ('tên_đăng_nhập', 'mật_khẩu')
users_data = [
    ('truongvi', 'tvi123', 'vi@mail'),
    ('nhatanh', 'nanh123', 'anh@mail'),
    ('quochuy', 'qhuy123', 'huy@mail'),
    ('ngocmanh', 'nmanh123', 'manh@mail'),
    ('tantai', 'ttai123', 'tai@mail'),
]

# --- 2. Dữ liệu nhóm ---
# Định dạng: ('tên_nhóm', user_id_của_leader)
# LƯU Ý: user_id phải tồn tại trong bảng users ở trên.
groups_data = [
    ('Project Todo List', 1), # Gán an_nguyen (user_id=1) làm leader
    ('Project AI Rắn săn mồi', 3), # Gán binh_tran (user_id=2) làm leader
    ('Project AI Dò mìn', 2)
]

# --- 3. Dữ liệu thành viên nhóm ---
# Định dạng: (user_id, group_id)
# LƯU Ý: user_id và group_id phải tồn tại.
group_members_data = [
    (1, 1), # Thêm an_nguyen vào nhóm Dự án Alpha
    (2, 1), # Thêm binh_tran vào nhóm Dự án Alpha
    (3, 1), # Thêm an_nguyen vào nhóm Học Tập
    (4, 1), # Thêm binh_tran vào nhóm Học Tập
    (5, 1),

    (3, 2),
    (4, 2),

    (1, 3),
    (2, 3)
]

# --- 4. Dữ liệu công việc cá nhân ---
# Định dạng: (user_id, 'tiêu_đề', 'ghi_chú', is_done, 'ngày_hết_hạn')
# is_done: 0 = chưa xong, 1 = đã xong.
# ngày_hết_hạn: có thể để None hoặc dạng 'YYYY-MM-DD HH:MM:SS'.
tasks_data = [
    # (1, 'Hoàn thành báo cáo', 'Báo cáo tiến độ tuần này', 0, '2025-09-25 17:00:00'),
    # (2, 'Mua sắm', 'Sữa, bánh mì', 1, None),
]

# --- 5. Dữ liệu công việc nhóm ---
# Định dạng: (group_id, assignee_id, 'tiêu_đề', 'ghi_chú', is_done, 'ngày_hết_hạn')
# assignee_id: user_id của người được giao, có thể để None nếu chưa giao.
group_tasks_data = [
    (1, 1, 'Thiết kế Database', 'Sử dụng Sqlite3', 0, '2025-09-25 10:00:00'), 
    (1, 2, 'Thiết kế form đăng nhập', 'Sử dụng PyQT5', 0, '2025-09-26 15:00:00'),
    (1, 3, 'Thiết kế form chính', 'Sử dụng PyQt5', 0, '2025-09-27 18:00:00')
]


# ==============================================================================
# PHẦN HỆ THỐNG: BẠN KHÔNG CẦN CHỈNH SỬA CODE BÊN DƯỚI
# ==============================================================================

def insert_data(conn, cursor):
    """Hàm để chèn tất cả dữ liệu vào database."""
    print("Bắt đầu chèn dữ liệu...")
    try:
        if users_data:
            cursor.executemany("INSERT INTO users (user_name, user_password, email) VALUES (?, ?, ?)", users_data)
            print(f"-> Đã chèn {len(users_data)} người dùng.")

        if groups_data:
            cursor.executemany("INSERT INTO groups (group_name, leader_id) VALUES (?, ?)", groups_data)
            print(f"-> Đã chèn {len(groups_data)} nhóm.")

        if group_members_data:
            cursor.executemany("INSERT INTO group_members (user_id, group_id) VALUES (?, ?)", group_members_data)
            print(f"-> Đã chèn {len(group_members_data)} thành viên nhóm.")

        if tasks_data:
            cursor.executemany("INSERT INTO tasks (user_id, title, note, is_done, due_at) VALUES (?, ?, ?, ?, ?)", tasks_data)
            print(f"-> Đã chèn {len(tasks_data)} công việc cá nhân.")

        if group_tasks_data:
            cursor.executemany("INSERT INTO group_tasks (group_id, assignee_id, title, note, is_done, due_at) VALUES (?, ?, ?, ?, ?, ?)", group_tasks_data)
            print(f"-> Đã chèn {len(group_tasks_data)} công việc nhóm.")

        conn.commit()
        print("\n=> Chèn dữ liệu thành công!")

    except sqlite3.IntegrityError as e:
        print(f"\n[LỖI] Dữ liệu không hợp lệ hoặc đã tồn tại: {e}")
        conn.rollback()
    except sqlite3.Error as e:
        print(f"\n[LỖI] Đã xảy ra lỗi SQLite: {e}")
        conn.rollback()

if __name__ == "__main__":
    # Đường dẫn tới database nằm trong thư mục Data (cùng thư mục với script này)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, 'todolist_database.db')
    connection = None
    try:
        connection = sqlite3.connect(db_path)
        db_cursor = connection.cursor()
        insert_data(connection, db_cursor)
    except sqlite3.Error as e:
        print(f"Lỗi kết nối database: {e}")
    finally:
        if connection:
            connection.close()