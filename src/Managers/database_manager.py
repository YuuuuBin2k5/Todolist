import sqlite3
from typing import List, Optional, Any, Tuple


class Database:
    """
    Database helper wrapping sqlite3 for common operations used across the app.

    Provides convenience methods for users, tasks, groups, group_members and group_tasks.
    All queries use the single internal _execute_query to centralize error handling.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path


    def _execute_query(self, query, params=(), commit=False, fetch=None):
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
            print(f"[DB ERROR] {e} | {query} {params}")
        finally:
            conn.close()

    # ----------------- Users ---------------------------------
    def create_user(self, user_name: str, password: str, email: str) -> bool:
        query = "INSERT INTO users (user_name, user_password, email) VALUES (?, ?, ?)"
        res = self._execute_query(query, (user_name, password, email), commit=True)
        return res is None  # returns None on success path

    def get_user_by_credentials(self, user_name: str, password: str) -> Optional[Tuple]:
        query = "SELECT user_id, user_name FROM users WHERE user_name = ? AND user_password = ?"
        return self._execute_query(query, (user_name, password), fetch="one")

    def get_user_by_id(self, user_id: int) -> Optional[Tuple]:
        query = "SELECT user_id, user_name, email FROM users WHERE user_id = ?"
        return self._execute_query(query, (user_id,), fetch="one")

    def get_user_by_email(self, email: str) -> Optional[Tuple]:
        query = "SELECT user_id, user_name FROM users WHERE email = ?"
        return self._execute_query(query, (email,), fetch="one")

    # ----------------- Tasks (personal) -----------------------
    def add_task(self, user_id: int, title: str, note: str = "", is_done: int = 0, due_at: Optional[str] = None, estimated_minutes: Optional[int] = None, priority: int = 2) -> None:
        """Backward-compatible wrapper that delegates to add_task_with_meta.

        Older code may call add_task(...). Keep support by forwarding to the
        richer add_task_with_meta method which implements the concrete SQL.
        """
        return self.add_task_with_meta(user_id, title, note, is_done, due_at, estimated_minutes, priority)

    def add_task_with_meta(self, user_id: int, title: str, note: str = "", is_done: int = 0, due_at: Optional[str] = None, estimated_minutes: Optional[int] = None, priority: int = 2) -> None:
        # Map to actual table columns: estimate_minutes, priority
        if due_at is None:
            query = "INSERT INTO tasks (user_id, title, note, is_done, priority, estimate_minutes, created_at) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)"
            params = (user_id, title, note, is_done, priority, estimated_minutes)
        else:
            query = "INSERT INTO tasks (user_id, title, note, is_done, priority, estimate_minutes, due_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)"
            params = (user_id, title, note, is_done, priority, estimated_minutes, due_at)
        # execute once
        self._execute_query(query, params, commit=True)

    def get_tasks_for_user_month(self, user_id: int, month_str: str) -> List[Tuple]:
        query = "SELECT task_id, title, is_done, note, due_at FROM tasks WHERE user_id = ? AND strftime('%Y-%m', due_at) = ?"
        res = self._execute_query(query, (user_id, month_str), fetch="all")
        return res or []

    def get_tasks_for_user(self, user_id: int) -> List[Tuple]:
        # Return task rows with fields expected by HomePage: (task_id, title, is_done, due_at, estimate_minutes, priority, note)
        query = "SELECT task_id, title, is_done, due_at, estimate_minutes, priority, note FROM tasks WHERE user_id = ?"
        res = self._execute_query(query, (user_id,), fetch="all")
        return res or []

    def update_task_status(self, task_id: int, is_done: int) -> None:
        query = "UPDATE tasks SET is_done = ? WHERE task_id = ?"
        self._execute_query(query, (is_done, task_id), commit=True)

    def delete_task(self, task_id: int) -> None:
        query = "DELETE FROM tasks WHERE task_id = ?"
        self._execute_query(query, (task_id,), commit=True)

    # ----------------- Groups & membership --------------------
    def create_group(self, group_name: str, leader_id: int) -> Optional[int]:
        # Use a dedicated connection to perform the insert and fetch lastrowid
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO groups (group_name, leader_id) VALUES (?, ?)", (group_name, leader_id))
            gid = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()
            return gid
        except Exception as e:
            print(f"[DB ERROR create_group] {e}")
            try:
                cursor.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
            return None

    def add_group_member(self, group_id: int, user_id: int) -> None:
        query = "INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)"
        self._execute_query(query, (group_id, user_id), commit=True)

    def get_groups_for_user(self, user_id: int) -> List[Tuple]:
        query = "SELECT g.group_id, g.group_name FROM groups g JOIN group_members gm ON g.group_id = gm.group_id WHERE gm.user_id = ?"
        return self._execute_query(query, (user_id,), fetch="all") or []

    def get_group_leader(self, group_id: int) -> Optional[int]:
        query = "SELECT leader_id FROM groups WHERE group_id = ?"
        res = self._execute_query(query, (group_id,), fetch="one")
        return res[0] if res else None

    def get_group_members(self, group_id: int) -> List[Tuple]:
        query = "SELECT u.user_id, u.user_name, u.email FROM users u JOIN group_members gm ON u.user_id = gm.user_id WHERE gm.group_id = ?"
        return self._execute_query(query, (group_id,), fetch="all") or []

    # ----------------- Group tasks ----------------------------
    def add_group_task(self, group_id: int, creator_id: int, title: str, note: str = "", is_done: int = 0, due_at: Optional[str] = None, assignee_id: Optional[int] = None) -> None:
        if due_at is None:
            query = "INSERT INTO group_tasks (group_id, assignee_id, title, note, is_done, creator_id, created_at) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)"
            params = (group_id, assignee_id, title, note, is_done, creator_id)
        else:
            query = "INSERT INTO group_tasks (group_id, assignee_id, title, note, is_done, due_at, creator_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)"
            params = (group_id, assignee_id, title, note, is_done, due_at, creator_id)
        self._execute_query(query, params, commit=True)

    def get_group_tasks_for_month(self, group_id: int, month_str: str) -> List[Tuple]:
        # include task_id so UI can reference and delete/update specific group tasks
        query = "SELECT task_id, group_id, assignee_id, title, note, is_done, due_at FROM group_tasks WHERE group_id = ? AND strftime('%Y-%m', due_at) = ?"
        return self._execute_query(query, (group_id, month_str), fetch="all") or []

    def delete_group_task(self, task_id: int) -> None:
        query = "DELETE FROM group_tasks WHERE task_id = ?"
        self._execute_query(query, (task_id,), commit=True)

    def update_group_task_status(self, task_id: int, is_done: int) -> None:
        query = "UPDATE group_tasks SET is_done = ? WHERE task_id = ?"
        self._execute_query(query, (is_done, task_id), commit=True)

    def get_task_by_id(self, task_id: int) -> Optional[Tuple]:
        # Return columns in natural schema order: task_id, user_id, title, note, is_done, due_at
        query = "SELECT task_id, user_id, title, note, is_done, due_at FROM tasks WHERE task_id = ?"
        return self._execute_query(query, (task_id,), fetch="one")

    def get_group_task_by_id(self, task_id: int) -> Optional[Tuple]:
        # Select columns according to actual table schema: task_id, group_id, assignee_id, title, note, is_done, created_at, due_at
        query = "SELECT task_id, group_id, assignee_id, title, note, is_done, created_at, due_at FROM group_tasks WHERE task_id = ?"
        return self._execute_query(query, (task_id,), fetch="one")

    def get_group_tasks_for_user_month(self, user_id: int, month_str: str) -> List[Tuple]:
        """Return group tasks assigned to a specific user in a given year-month."""
        query = "SELECT task_id, group_id, assignee_id, title, note, is_done, due_at FROM group_tasks WHERE assignee_id = ? AND strftime('%Y-%m', due_at) = ?"
        return self._execute_query(query, (user_id, month_str), fetch="all") or []

    # ----------------- Utility --------------------------------
    def get_user_name(self, user_id: int) -> Optional[str]:
        res = self.get_user_by_id(user_id)
        return res[1] if res else None


