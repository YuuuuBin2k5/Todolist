import os
import sqlite3

# ==============================================================================
# PHẦN DÀNH CHO BẠN: DỮ LIỆU MẪU ĐÃ ĐƯỢC LÀM PHONG PHÚ
# ==============================================================================

# --- 1. Dữ liệu người dùng ---
users_data = [
    ('truongvi', '123', 'vi@mail.com'),         # user_id = 1
    ('nhatanh', '123', 'anh@mail.com'),        # user_id = 2
    ('quochuy', '123', 'huy@mail.com'),        # user_id = 3
    ('ngocmanh', '123', 'manh@mail.com'),      # user_id = 4
    ('tantai', '123', 'tai@mail.com'),         # user_id = 5
    ('minhthu', '123', 'thu@mail.com'),        # user_id = 6
    ('hoangan', '123', 'hoangan@mail.com'),    # user_id = 7
    ('thuyvy', '123', 'vy@mail.com'),          # user_id = 8
]

# --- 2. Dữ liệu nhóm ---
groups_data = [
    ('Project Todo List', 1),            # group_id = 1
    ('Project AI Rắn săn mồi', 3),       # group_id = 2
    ('Project AI Dò mìn', 2),            # group_id = 3
    ('Project OOP', 6),                  # group_id = 4
    ('Bài tập nhóm Web', 7)              # group_id = 5
]

# --- 3. Dữ liệu thành viên nhóm ---
group_members_data = [
    (1, 1), (2, 1), (3, 1), (4, 1), (5, 1),
    (3, 2), (4, 2), (7, 2),
    (1, 3), (2, 3), (8, 3),
    (6, 4), (8, 4),
    (1, 5), (7, 5),
]

# --- 4. Dữ liệu công việc cá nhân ---
# ĐỊNH DẠNG: (user_id, title, note, is_done, priority, estimate_minutes, due_at)
# priority: 1=Thấp, 2=Trung bình, 3=Cao
tasks_data = [
    # Công việc của truongvi (user_id = 1)
    (1, 'Nộp báo cáo tuần', 'Báo cáo tổng kết công việc cho Ban Lãnh Đạo', 0, 3, 60, '2025-10-10 17:00:00'),
    (1, 'Kiểm tra email', 'Phản hồi các email quan trọng', 1, 2, 30, '2025-10-06 09:00:00'),
    (1, 'Chuẩn bị slide họp', 'Slide cho cuộc họp tổng kết dự án Todo List', 0, 3, 120, '2025-10-08 10:00:00'),
    (1, 'Gọi cho đối tác A', 'Thảo luận về hợp đồng mới', 1, 3, 45, '2025-10-06 14:00:00'),
    (1, 'Đọc tài liệu API', 'Nghiên cứu API thanh toán mới', 0, 2, 90, '2025-10-12 23:00:00'),

    # Công việc của nhatanh (user_id = 2)
    (2, 'Mua đồ dùng văn phòng', 'Giấy A4, bút, kẹp giấy', 1, 1, 60, None),
    (2, 'Cập nhật tài liệu hướng dẫn', 'Thêm phần hướng dẫn cho tính năng mới của AI Dò mìn', 0, 2, 75, '2025-10-11 11:00:00'),
    (2, 'Đặt lịch hẹn khám sức khỏe', '', 0, 1, 15, '2025-10-20 09:00:00'),
    (2, 'Sắp xếp lại Google Drive', 'Dọn dẹp các file không cần thiết', 0, 1, None, '2025-10-30 18:00:00'),

    # Công việc của quochuy (user_id = 3)
    (3, 'Nghiên cứu thuật toán A*', 'Tìm tài liệu và đọc về A* cho dự án AI', 0, 3, 180, '2025-10-15 23:59:59'),
    (3, 'Review code của ngocmanh', 'Kiểm tra pull request trên Github', 1, 2, 60, '2025-10-07 16:00:00'),
    (3, 'Đăng ký khóa học online', 'Khóa học "Advanced Python"', 1, 1, 30, '2025-10-01 10:00:00'),
    (3, 'Backup mã nguồn', 'Nén và lưu trữ source code dự án AI Rắn Săn Mồi', 0, 2, 20, None),

    # Công việc của ngocmanh (user_id = 4)
    (4, 'Sắp xếp lại file dự án', 'Dọn dẹp thư mục source code', 1, 1, 45, '2025-10-05 12:00:00'),
    (4, 'Fix bug #1024', 'Lỗi hiển thị sai trên màn hình chính', 0, 3, 90, '2025-10-06 17:00:00'),
    (4, 'Viết báo cáo lỗi', 'Mô tả chi tiết các lỗi tìm thấy trong quá trình test', 0, 2, 60, '2025-10-09 10:00:00'),

    # Công việc của tantai (user_id = 5)
    (5, 'Kiểm thử chức năng đăng nhập', 'Test các trường hợp thành công, thất bại', 0, 3, 120, '2025-10-11 15:00:00'),
    (5, 'Tìm hiểu về Unit Test', 'Đọc tài liệu về thư viện unittest của Python', 0, 2, 90, None),

    # Công việc của minhthu (user_id = 6)
    (6, 'Lên kế hoạch Social Media', 'Kế hoạch bài đăng cho tháng 11', 0, 3, 150, '2025-10-20 18:00:00'),
    (6, 'Phân tích hiệu quả chiến dịch', 'Báo cáo về chiến dịch quảng cáo Q3', 1, 2, 120, '2025-09-30 15:00:00'),

    # Công việc của hoangan (user_id = 7)
    (7, 'Triển khai CSDL lên server', 'Deploy database cho dự án Web', 0, 3, 180, '2025-10-19 17:00:00'),
    (7, 'Viết tài liệu API', 'Tài liệu cho các endpoint của dự án Web', 0, 2, 120, '2025-10-25 17:00:00'),

    # Công việc của thuyvy (user_id = 8)
    (8, 'Thiết kế banner quảng cáo', 'Banner cho sự kiện ra mắt sản phẩm mới', 0, 2, 90, '2025-10-15 11:00:00'),
    (8, 'Tìm ý tưởng cho logo mới', 'Nghiên cứu các xu hướng thiết kế hiện tại', 0, 1, None, '2025-10-22 12:00:00'),
]

# --- 5. Dữ liệu công việc nhóm ---
group_tasks_data = [
    # --- Công việc cho Project Todo List (group_id = 1) ---
    (1, 1, 'Thiết kế Database', 'Sử dụng SQLite3, vẽ sơ đồ ERD', 1, '2025-09-25 10:00:00'),
    (1, 2, 'Thiết kế form Đăng nhập', 'Sử dụng PyQt5, bao gồm validation', 1, '2025-09-28 15:00:00'),
    (1, 3, 'Thiết kế form Chính', 'Hiển thị danh sách công việc, các nút chức năng', 1, '2025-10-04 18:00:00'),
    (1, 4, 'Code logic backend API', 'Viết các hàm thêm/sửa/xóa task', 0, '2025-10-12 18:00:00'),
    (1, 5, 'Code giao diện form Chính', 'Kết nối UI với logic backend', 0, '2025-10-14 18:00:00'),
    (1, 2, 'Tích hợp chức năng tìm kiếm', 'Cho phép người dùng tìm kiếm công việc theo tiêu đề', 0, '2025-10-16 15:00:00'),
    (1, 1, 'Viết Unit Test cho backend', 'Đảm bảo các hàm CRUD hoạt động đúng', 0, '2025-10-18 17:00:00'),
    (1, 5, 'Test tổng thể ứng dụng', 'Kiểm tra tất cả các chức năng trước khi release', 0, '2025-10-22 17:00:00'),      # [SỬA] Giao cho user 5
    (1, 1, 'Chuẩn bị tài liệu Deploy', 'Viết hướng dẫn cài đặt và sử dụng', 0, '2025-10-24 17:00:00'),     # [SỬA] Giao cho user 1 (leader)
    (1, 3, 'Sửa lỗi giao diện', 'Fix các lỗi UI tồn đọng sau khi test', 0, '2025-10-25 18:00:00'),              # [MỚI] Thêm công việc
    (1, 2, 'Viết tài liệu hướng dẫn', 'Soạn tài liệu hướng dẫn sử dụng cho người dùng cuối', 0, '2025-10-27 18:00:00'), # [MỚI] Thêm công việc
    (1, 4, 'Tối ưu hóa truy vấn CSDL', 'Review và cải thiện tốc độ các query SQL', 0, '2025-10-28 12:00:00'), # [MỚI] Thêm công việc

    # --- Công việc cho Project AI Rắn săn mồi (group_id = 2) ---
    (2, 3, 'Xây dựng môi trường game', 'Sử dụng Pygame để vẽ rắn, mồi, bảng điểm', 1, '2025-10-01 12:00:00'),
    (2, 4, 'Tích hợp model AI', 'Viết code để model điều khiển con rắn', 0, '2025-10-15 12:00:00'),
    (2, 7, 'Huấn luyện và tối ưu model', 'Chạy training loop và tinh chỉnh tham số', 0, '2025-10-25 12:00:00'),
    (2, 3, 'Thêm chức năng lưu điểm cao', 'Lưu điểm số vào file hoặc database', 0, '2025-10-28 18:00:00'),
    (2, 4, 'Cải thiện giao diện người dùng', 'Thêm hiệu ứng và làm cho game đẹp hơn', 0, '2025-11-05 18:00:00'),
    (2, 7, 'Tạo file thực thi (.exe)', 'Sử dụng PyInstaller để đóng gói game', 0, '2025-11-10 18:00:00'),            # [SỬA] Giao cho user 7

    # --- Công việc cho Project AI Dò mìn (group_id = 3) ---
    (3, 2, 'Phân tích yêu cầu', 'Xác định các mức độ khó và kích thước bảng', 1, '2025-10-03 17:00:00'),
    (3, 8, 'Thiết kế giao diện game', 'Vẽ các ô, số, cờ và mìn', 0, '2025-10-10 17:00:00'),
    (3, 1, 'Xây dựng logic game', 'Tạo ma trận mìn, xử lý sự kiện click chuột', 0, '2025-10-17 17:00:00'),
    (3, 2, 'Fix bug mở ô', 'Sửa lỗi khi mở ô đầu tiên bị trúng mìn', 0, '2025-10-20 17:00:00'),
    (3, 1, 'Phát triển AI giải game', 'Nghiên cứu các thuật toán giải quyết Dò mìn', 0, '2025-10-30 17:00:00'),    # [SỬA] Giao cho user 1

    # --- Công việc cho Project OOP (group_id = 4) ---
    (4, 6, 'Xác định các lớp đối tượng', 'Phân tích yêu cầu, xác định class Student, Teacher, Course', 1, '2025-10-05 11:00:00'),
    (4, 8, 'Vẽ biểu đồ lớp (Class Diagram)', 'Sử dụng công cụ draw.io hoặc lucidchart', 1, '2025-10-09 15:00:00'),
    (4, 6, 'Implement class Student', 'Bao gồm các thuộc tính và phương thức cơ bản', 0, '2025-10-14 23:59:59'),
    (4, 8, 'Implement class Teacher', 'Bao gồm các thuộc tính và phương thức cơ bản', 0, '2025-10-14 23:59:59'),
    (4, 6, 'Viết mối quan hệ giữa các lớp', 'Implement các mối quan hệ kế thừa, composition', 0, '2025-10-18 18:00:00'),
    (4, 8, 'Viết báo cáo tổng kết', 'Tổng hợp lại quá trình thiết kế và implement', 0, '2025-10-20 10:00:00'), # [SỬA] Giao cho user 8

    # --- Công việc cho Bài tập nhóm Web (group_id = 5) ---
    (5, 7, 'Thiết kế layout trang chủ', 'Phác thảo layout trên Figma', 1, '2025-10-02 18:00:00'),
    (5, 1, 'Code HTML cho trang chủ', 'Xây dựng cấu trúc trang web với HTML5', 1, '2025-10-07 17:00:00'),
    (5, 7, 'Code CSS cho trang chủ', 'Style cho các thành phần đã có', 0, '2025-10-11 17:00:00'),
    (5, 1, 'Làm responsive cho di động', 'Sử dụng media queries để tối ưu hiển thị', 0, '2025-10-16 12:00:00'),
    (5, 7, 'Thêm chức năng gửi form liên hệ', 'Viết backend xử lý form bằng Flask hoặc Django', 0, '2025-10-22 12:00:00'),
    (5, 1, 'Deploy website', 'Đưa website lên Vercel hoặc Netlify', 0, '2025-10-28 12:00:00'),                 # [SỬA] Giao cho user 1
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
            # SỬA LẠI CÂU LỆNH INSERT ĐỂ BAO GỒM 2 CỘT MỚI
            cursor.executemany(
                "INSERT INTO tasks (user_id, title, note, is_done, priority, estimate_minutes, due_at) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                tasks_data
            )
            print(f"-> Đã chèn {len(tasks_data)} công việc cá nhân.")

        if group_tasks_data:
            cursor.executemany("INSERT INTO group_tasks (group_id, assignee_id, title, note, is_done, due_at) VALUES (?, ?, ?, ?, ?, ?)", group_tasks_data)
            print(f"-> Đã chèn {len(group_tasks_data)} công việc nhóm.")

        conn.commit()
        print("\n=> Chèn dữ liệu thành công!")

    except sqlite3.IntegrityError as e:
        print(f"\n[LỖI] Dữ liệu không hợp lệ hoặc đã tồn tại: {e}")
        print("=> GỢI Ý: Có thể bạn cần xóa file 'todolist_database.db' cũ trước khi chạy lại script này.")
        conn.rollback()
    except sqlite3.Error as e:
        print(f"\n[LỖI] Đã xảy ra lỗi SQLite: {e}")
        conn.rollback()

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, '..', 'Data', 'todolist_database.db') # Điều chỉnh đường dẫn
    connection = None
    try:
        connection = sqlite3.connect(db_path)
        db_cursor = connection.cursor()
        
        # Xóa dữ liệu cũ để tránh lỗi UNIQUE constraint
        print("Đang xóa dữ liệu cũ...")
        tables = ['users', 'groups', 'group_members', 'tasks', 'group_tasks']
        for table in tables:
            db_cursor.execute(f"DELETE FROM {table};")
            # Reset auto-increment key
            db_cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}';")
        connection.commit()
        print("Đã xóa dữ liệu cũ thành công.")
        
        insert_data(connection, db_cursor)
        
    except sqlite3.Error as e:
        print(f"Lỗi kết nối hoặc thao tác database: {e}")
    finally:
        if connection:
            connection.close()