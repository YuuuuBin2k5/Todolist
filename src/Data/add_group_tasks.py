# -*- coding: utf-8 -*-
import sqlite3
import os
from datetime import datetime, timedelta

def add_sample_group_tasks():
    """Thêm một số group tasks mẫu để test"""
    
    # Đường dẫn database
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, 'todolist_database.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lấy thông tin users và groups
        cursor.execute("SELECT user_id, user_name FROM users")
        users = cursor.fetchall()
        
        cursor.execute("SELECT group_id, group_name FROM groups")
        groups = cursor.fetchall()
        
        print("Users:", users)
        print("Groups:", groups)
        
        if not users or not groups:
            print("Cần có users và groups trước khi thêm group tasks")
            return
            
        # Thêm một số group tasks mẫu
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)
        
        sample_tasks = [
            (1, 1, "Thiết kế giao diện đăng nhập", "Tạo mockup và wireframe cho trang đăng nhập", 0, tomorrow.strftime('%Y-%m-%d %H:%M:%S')),
            (1, 2, "Implement API authentication", "Xây dựng API xác thực người dùng", 0, next_week.strftime('%Y-%m-%d %H:%M:%S')),
            (1, 3, "Database optimization", "Tối ưu hóa queries và indexing", 1, today.strftime('%Y-%m-%d %H:%M:%S')),
            (2, 1, "Huấn luyện model AI", "Thu thập dữ liệu và train model nhận diện", 0, tomorrow.strftime('%Y-%m-%d %H:%M:%S')),
            (2, 4, "Tối ưu thuật toán pathfinding", "Cải thiện A* algorithm cho AI", 0, next_week.strftime('%Y-%m-%d %H:%M:%S')),
            (3, 2, "Implement game logic", "Viết logic chính của game dò mìn", 1, today.strftime('%Y-%m-%d %H:%M:%S')),
            (3, 5, "UI/UX design cho game", "Thiết kế giao diện game thân thiện", 0, tomorrow.strftime('%Y-%m-%d %H:%M:%S')),
        ]
        
        for group_id, assignee_id, title, note, is_done, due_at in sample_tasks:
            cursor.execute("""
                INSERT OR IGNORE INTO group_tasks (group_id, assignee_id, title, note, is_done, due_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (group_id, assignee_id, title, note, is_done, due_at))
        
        conn.commit()
        print(f"Đã thêm {len(sample_tasks)} group tasks mẫu!")
        
        # Hiển thị kết quả
        cursor.execute("""
            SELECT gt.title, u.user_name as assignee, g.group_name, gt.is_done, gt.due_at
            FROM group_tasks gt
            JOIN users u ON gt.assignee_id = u.user_id
            JOIN groups g ON gt.group_id = g.group_id
            ORDER BY gt.due_at
        """)
        
        tasks = cursor.fetchall()
        print("\nGroup tasks đã có:")
        for title, assignee, group, is_done, due_at in tasks:
            status = "✓" if is_done else "○"
            print(f"{status} {title} - {assignee} ({group}) - {due_at}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Lỗi database: {e}")

if __name__ == "__main__":
    add_sample_group_tasks()