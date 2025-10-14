import os
import sqlite3
from typing import List, Optional, Tuple, Dict

class Database:
    """Trợ giúp SQLite cho app: users, tasks, groups, group_members, group_tasks.
    Dùng _execute_query để tập trung thao tác và xử lý lỗi SQL.
    """
    def __init__(self):
        # Đường dẫn mặc định đến file DB
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.db_path = os.path.join(base_dir, "Data", "todolist_database.db")


    def _execute_query(self, query, params=(), commit=False, fetch=None):
        """Thực thi truy vấn SQL.

        Args:
            query (str): câu lệnh SQL với placeholders.
            params (tuple): tham số truyền vào query.
            commit (bool): nếu True thì commit transaction.
            fetch (None|'one'|'all'): cách trả về kết quả.

        Returns:
            kết quả fetch theo tham số fetch hoặc None.

        Lưu ý: In lỗi SQL ra stdout khi có exception.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute(query, params)
            if commit:
                conn.commit()
            if fetch == "one":
                return cur.fetchone()
            if fetch == "all":
                return cur.fetchall()
        except sqlite3.Error as e:
            import logging
            logging.exception("[DB ERROR] %s | %s %s", e, query, params)
        finally:
            conn.close()

    def _execute_insert(self, query, params=()):
        """Thực thi INSERT và trả về lastrowid hoặc None nếu lỗi.

        Dùng để giữ nhất quán khi cần id của hàng vừa thêm.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()
            last = cur.lastrowid
            cur.close()
            conn.close()
            return last
        except sqlite3.Error as e:
            import logging
            logging.exception("[DB ERROR] %s | %s %s", e, query, params)
            try:
                cur.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
            return None

    def get_login_user(self, email: str, password: str) -> Optional[Tuple]:
        """Tìm user theo email và mật khẩu.

        Trả về (user_id, user_name) nếu tồn tại, ngược lại None.
        """
        query = "SELECT user_id, user_name FROM users WHERE email = ? AND user_password = ?"
        return self._execute_query(query, (email, password), fetch="one")

    # ----------------- Người dùng -----------------------------
    def create_user(self, user_name: str, password: str, email: str) -> Optional[int]:
        """Tạo user mới và trả về user_id (lastrowid) hoặc None nếu lỗi.

        Mục đích: gọi khi đăng ký (signup). Caller có thể cần user_id
        để thêm vào bảng liên quan (ví dụ group_members) hoặc tạo session.
        """
        query = "INSERT INTO users (user_name, user_password, email) VALUES (?, ?, ?)"
        return self._execute_insert(query, (user_name, password, email))

    def get_user_by_id(self, user_id: int) -> Optional[Tuple]:
        """Lấy thông tin user theo user_id.

        Trả về (user_id, user_name, email) hoặc None.
        """
        query = "SELECT user_id, user_name, email FROM users WHERE user_id = ?"
        return self._execute_query(query, (user_id,), fetch="one")

    def get_user_by_email(self, email: str) -> Optional[Tuple]:
        """Tìm user theo email.

        Trả về (user_id, user_name) hoặc None.
        """
        query = "SELECT user_id, user_name FROM users WHERE email = ?"
        return self._execute_query(query, (email,), fetch="one")
    
    def update_user_password_by_email(self, new_password: str, email: str) -> None:
        """Cập nhật mật khẩu theo email.

        Không trả về, ném exception khi lỗi DB.
        """
        query = "UPDATE users SET user_password = ? WHERE email = ?"
        self._execute_query(query, (new_password, email), commit=True)

    # ----------------- Công việc (cá nhân) ---------------------
    def add_task(self, user_id: int, title: str, note: str = "", is_done: int = 0, due_at: Optional[str] = None, estimated_minutes: Optional[int] = None, priority: int = 2) -> None:
        """Wrapper tương thích cho add_task_with_meta.

        Giữ tương thích với code cũ.
        """
        return self.add_task_with_meta(user_id, title, note, is_done, due_at, estimated_minutes, priority)

    def add_task_with_meta(self, user_id: int, title: str, note: str = "", is_done: int = 0, due_at: Optional[str] = None, estimated_minutes: Optional[int] = None, priority: int = 2) -> None:
        """Thêm task với metadata (note, due_at, estimate, priority).

        Không trả về; ném lỗi khi DB thất bại.
        """
        if due_at is None:
            query = "INSERT INTO tasks (user_id, title, note, is_done, priority, estimate_minutes, created_at) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)"
            params = (user_id, title, note, is_done, priority, estimated_minutes)
        else:
            query = "INSERT INTO tasks (user_id, title, note, is_done, priority, estimate_minutes, due_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)"
            params = (user_id, title, note, is_done, priority, estimated_minutes, due_at)
        self._execute_query(query, params, commit=True)

    def get_tasks_for_user_month(self, user_id: int, month_str: str) -> List[Tuple]:
        """Lấy tasks của user trong tháng (format 'YYYY-MM').

        Trả về danh sách tuple hoặc [] nếu không có.
        """
        query = "SELECT task_id, title, is_done, note, due_at FROM tasks WHERE user_id = ? AND strftime('%Y-%m', due_at) = ?"
        res = self._execute_query(query, (user_id, month_str), fetch="all")
        return res or []

    def get_tasks_for_user(self, user_id: int) -> List[Tuple]:
        """Lấy tất cả tasks của user.

        Trả về danh sách row: (task_id, title, is_done, due_at, estimate_minutes, priority, note)
        """
        query = "SELECT task_id, title, is_done, due_at, estimate_minutes, priority, note FROM tasks WHERE user_id = ?"
        res = self._execute_query(query, (user_id,), fetch="all")
        return res or []

    def update_task_status(self, task_id: int, is_done: int) -> None:
        """Cập nhật cờ is_done của task.

        Args: task_id (int), is_done (0/1).
        """
        query = "UPDATE tasks SET is_done = ? WHERE task_id = ?"
        self._execute_query(query, (is_done, task_id), commit=True)

    def delete_task(self, task_id: int) -> None:
        """Xóa task theo id.

        Không trả về; ném lỗi khi DB thất bại.
        """
        query = "DELETE FROM tasks WHERE task_id = ?"
        self._execute_query(query, (task_id,), commit=True)

    # ----------------- Nhóm & thành viên -----------------------
    def create_group(self, group_name: str, leader_id: int) -> Optional[int]:
        """Tạo nhóm mới và trả về group_id (lastrowid) hoặc None nếu lỗi.

        Ghi chú: lastrowid là theo connection, nên phải lấy trực tiếp từ connection
        sử dụng cho thao tác insert này.
        """
        query = "INSERT INTO groups (group_name, leader_id) VALUES (?, ?)"
        return self._execute_insert(query, (group_name, leader_id))

    def add_group_member(self, group_id: int, user_id: int) -> None:
        """Thêm user vào group (không lỗi khi đã tồn tại).

        Dùng INSERT OR IGNORE để tránh duplicate.
        """
        query = "INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)"
        self._execute_query(query, (group_id, user_id), commit=True)

    def get_groups_for_user(self, user_id: int) -> List[Tuple]:
        """Lấy danh sách (group_id, group_name) mà user tham gia."""
        query = "SELECT g.group_id, g.group_name FROM groups g JOIN group_members gm ON g.group_id = gm.group_id WHERE gm.user_id = ?"
        return self._execute_query(query, (user_id,), fetch="all") or []

    def get_group_leader(self, group_id: int) -> Optional[int]:
        """Trả về leader_id của nhóm, hoặc None nếu không tìm thấy."""
        query = "SELECT leader_id FROM groups WHERE group_id = ?"
        res = self._execute_query(query, (group_id,), fetch="one")
        return res[0] if res else None

    def get_group_members(self, group_id: int) -> List[Tuple]:
        """Lấy danh sách thành viên nhóm: (user_id, user_name)."""
        query = "SELECT u.user_id, u.user_name FROM users u JOIN group_members gm ON u.user_id = gm.user_id WHERE gm.group_id = ?"
        return self._execute_query(query, (group_id,), fetch="all") or []

    # ----------------- Công việc nhóm --------------------------
    def add_group_task(self, group_id: int, creator_id: int, title: str, note: str = "", is_done: int = 0, due_at: Optional[str] = None, assignee_id: Optional[int] = None, estimated_minutes: Optional[int] = None, priority: int = 4) -> None:
        """Thêm công việc nhóm; assignee_id có thể None.

        Không trả về; commit khi thành công.
        """
        # Defensive: some DB instances may not have a creator_id (or leader_id) column
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(group_tasks)")
            cols = [r[1] for r in cur.fetchall()]
            cur.close()
            conn.close()
        except Exception:
            cols = []

        # prefer column named 'creator_id', fall back to 'leader_id' if present
        has_creator = 'creator_id' in cols or 'leader_id' in cols
        creator_col = 'creator_id' if 'creator_id' in cols else ('leader_id' if 'leader_id' in cols else None)

        has_estimate = 'estimated_minutes' in cols or 'estimate_minutes' in cols
        estimate_col = 'estimated_minutes' if 'estimated_minutes' in cols else ('estimate_minutes' if 'estimate_minutes' in cols else None)

        has_priority = 'priority' in cols

        if due_at is None:
            if has_creator and creator_col and has_estimate and estimate_col and has_priority:
                query = f"INSERT INTO group_tasks (group_id, assignee_id, title, note, is_done, {creator_col}, {estimate_col}, priority, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)"
                params = (group_id, assignee_id, title, note, is_done, creator_id, estimated_minutes, priority)
            elif has_creator and creator_col:
                query = f"INSERT INTO group_tasks (group_id, assignee_id, title, note, is_done, {creator_col}, created_at) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)"
                params = (group_id, assignee_id, title, note, is_done, creator_id)
            else:
                query = "INSERT INTO group_tasks (group_id, assignee_id, title, note, is_done, created_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)"
                params = (group_id, assignee_id, title, note, is_done)
        else:
            if has_creator and creator_col and has_estimate and estimate_col and has_priority:
                query = f"INSERT INTO group_tasks (group_id, assignee_id, title, note, is_done, due_at, {creator_col}, {estimate_col}, priority, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)"
                params = (group_id, assignee_id, title, note, is_done, due_at, creator_id, estimated_minutes, priority)
            elif has_creator and creator_col:
                query = f"INSERT INTO group_tasks (group_id, assignee_id, title, note, is_done, due_at, {creator_col}, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)"
                params = (group_id, assignee_id, title, note, is_done, due_at, creator_id)
            else:
                query = "INSERT INTO group_tasks (group_id, assignee_id, title, note, is_done, due_at, created_at) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)"
                params = (group_id, assignee_id, title, note, is_done, due_at)

        self._execute_query(query, params, commit=True)

    def get_group_tasks(self, group_id: int) -> List[Tuple]:
        """Lấy tất cả các task của một nhóm."""
        query = """
            SELECT task_id, group_id, assignee_id, title, note, is_done, due_at
            FROM group_tasks
            WHERE group_id = ?
            ORDER BY is_done ASC, due_at DESC
        """
        return self._execute_query(query, (group_id,), fetch="all") or []

    def get_group_tasks_for_month(self, group_id: int, month_str: str) -> List[Tuple]:
        """Lấy tasks của nhóm trong tháng (format 'YYYY-MM')."""
        query = "SELECT task_id, group_id, assignee_id, title, note, is_done, due_at FROM group_tasks WHERE group_id = ? AND strftime('%Y-%m', due_at) = ?"
        return self._execute_query(query, (group_id, month_str), fetch="all") or []

    def delete_group_task(self, task_id: int) -> None:
        """Xóa công việc nhóm theo id."""
        query = "DELETE FROM group_tasks WHERE task_id = ?"
        self._execute_query(query, (task_id,), commit=True)

    def update_group_task_status(self, task_id: int, is_done: int) -> None:
        """Cập nhật trạng thái is_done cho công việc nhóm."""
        query = "UPDATE group_tasks SET is_done = ? WHERE task_id = ?"
        self._execute_query(query, (is_done, task_id), commit=True)

    def get_task_by_id(self, task_id: int) -> Optional[Tuple]:
        """Lấy task cá nhân theo id. Trả về row hoặc None."""
        # include estimate_minutes and priority for UI consumption (backwards compatible)
        query = "SELECT task_id, user_id, title, note, is_done, due_at, estimate_minutes, priority FROM tasks WHERE task_id = ?"
        return self._execute_query(query, (task_id,), fetch="one")

    def get_group_task_by_id(self, task_id: int) -> Optional[Tuple]:
        """Lấy công việc nhóm theo id. Trả về row hoặc None."""
        query = "SELECT task_id, group_id, assignee_id, title, note, is_done, created_at, due_at FROM group_tasks WHERE task_id = ?"
        return self._execute_query(query, (task_id,), fetch="one")

    def get_group_tasks_for_user_month(self, user_id: int, month_str: str) -> List[Tuple]:
        """Lấy công việc nhóm được giao cho user trong tháng.
        Trả về danh sách hoặc [].
        """
        query = "SELECT task_id, group_id, assignee_id, title, note, is_done, due_at FROM group_tasks WHERE assignee_id = ? AND strftime('%Y-%m', due_at) = ?"
        return self._execute_query(query, (user_id, month_str), fetch="all") or []

    # ----------------- Tiện ích --------------------------------
    def get_user_name(self, user_id: int) -> Optional[str]:
        """Trả về user_name theo user_id hoặc None."""
        res = self.get_user_by_id(user_id)
        return res[1] if res else None

    def get_user_id_by_name(self, user_name: str) -> Optional[int]:
        """Tìm user_id theo user_name (kết quả đầu tiên). Trả về None nếu không tìm thấy."""
        try:
            query = "SELECT user_id FROM users WHERE user_name = ? LIMIT 1"
            res = self._execute_query(query, (user_name,), fetch="one")
            if res:
                return res[0]
        except sqlite3.Error:
            pass
        return None


    # Thống kê hoàn thành công việc cá nhân
    def _get_personal_completion_stats(self, user_id: int) -> Dict[str, int]:
        """Lấy số liệu 3 trạng thái: hoàn thành, quá hạn, và sắp tới."""
        stats = {'completed': 0, 'overdue': 0, 'upcoming': 0}
        
        # Sử dụng một câu truy vấn duy nhất với CASE để tăng hiệu suất
        query = """
            SELECT
                SUM(CASE WHEN is_done = 1 THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN is_done = 0 AND due_at < date('now', 'localtime') THEN 1 ELSE 0 END) as overdue,
                SUM(CASE WHEN is_done = 0 AND due_at >= date('now', 'localtime') THEN 1 ELSE 0 END) as upcoming
            FROM tasks
            WHERE user_id = ?
        """
        
        result = self._execute_query(query, (user_id,), fetch="one")
        
        if result:
            stats['completed'] = result[0] if result[0] is not None else 0
            stats['overdue'] = result[1] if result[1] is not None else 0
            stats['upcoming'] = result[2] if result[2] is not None else 0
            
        return stats

    # Thay thế hàm _get_stats_per_group cũ bằng hàm này
    def _get_stats_per_group(self, user_id: int) -> List[Dict[str, any]]:
        """
        Lấy số liệu 3 trạng thái cho TỪNG NHÓM mà người dùng tham gia.
        Trả về danh sách các dictionary.
        """
        stats_list = []
        
        # Cập nhật câu truy vấn để tính toán cả 3 trạng thái
        query = """
            SELECT
                g.group_name,
                SUM(CASE WHEN gt.is_done = 1 THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN gt.is_done = 0 AND gt.due_at < date('now', 'localtime') THEN 1 ELSE 0 END) as overdue,
                SUM(CASE WHEN gt.is_done = 0 AND gt.due_at >= date('now', 'localtime') THEN 1 ELSE 0 END) as upcoming
            FROM group_tasks gt
            JOIN groups g ON gt.group_id = g.group_id
            WHERE gt.group_id IN (SELECT group_id FROM group_members WHERE user_id = ?)
            GROUP BY g.group_name
        """
        
        results = self._execute_query(query, (user_id,), fetch="all")
        for row in results:
            if not row:
                continue
            stats_list.append({
                'group_name': row[0],
                'completed': int(row[1]) if row[1] is not None else 0,
                'overdue': int(row[2]) if row[2] is not None else 0,
                'upcoming': int(row[3]) if row[3] is not None else 0
            })
            
        return stats_list

