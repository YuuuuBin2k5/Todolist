#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để thêm một số group tasks mẫu để test hiển thị assignee
"""
import sqlite3
import os
from datetime import datetime, timedelta

# Đường dẫn đến database
db_path = os.path.join(os.path.dirname(__file__), 'src', 'Data', 'todolist_database.db')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Thêm một số group tasks mẫu
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)
    
    sample_tasks = [
        # group_id=1 (Project Todo List), assignee_id=1 (truongvi)
        (1, "Thiết kế UI chính", 0, 1, tomorrow.strftime("%Y-%m-%d %H:%M:%S"), "Tạo wireframe và mockup cho giao diện chính"),
        (1, "Implement database schema", 1, 2, today.strftime("%Y-%m-%d %H:%M:%S"), "Tạo các bảng và relationship"),
        (1, "Code login system", 0, 1, next_week.strftime("%Y-%m-%d %H:%M:%S"), "Xây dựng hệ thống đăng nhập/đăng ký"),
        
        # group_id=2 (Project AI Rắn săn mồi), assignee_id=3 (quochuy - leader)
        (2, "Research AI algorithms", 0, 3, tomorrow.strftime("%Y-%m-%d %H:%M:%S"), "Nghiên cứu các thuật toán AI cho game"),
        (2, "Build game engine", 0, 4, next_week.strftime("%Y-%m-%d %H:%M:%S"), "Tạo engine cơ bản cho game"),
        
        # group_id=3 (Project AI Dò mìn), assignee_id=2 (nhatanh - leader)
        (3, "Design minesweeper logic", 1, 2, today.strftime("%Y-%m-%d %H:%M:%S"), "Thiết kế logic game dò mìn"),
        (3, "AI solver algorithm", 0, 5, next_week.strftime("%Y-%m-%d %H:%M:%S"), "Tạo thuật toán AI giải dò mìn"),
    ]
    
    for task in sample_tasks:
        cursor.execute("""
            INSERT INTO group_tasks (group_id, title, is_done, assignee_id, due_at, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, task)
    
    conn.commit()
    print(f"✅ Đã thêm {len(sample_tasks)} group tasks mẫu thành công!")
    
    # Hiển thị kết quả
    cursor.execute("""
        SELECT gt.title, u.user_name, g.group_name, gt.due_at, gt.is_done
        FROM group_tasks gt
        JOIN users u ON gt.assignee_id = u.user_id
        JOIN groups g ON gt.group_id = g.group_id
        ORDER BY gt.group_id, gt.due_at
    """)
    
    print("\n📋 Danh sách group tasks đã được thêm:")
    for title, assignee, group, due_at, is_done in cursor.fetchall():
        status = "✅" if is_done else "⏳"
        print(f"{status} [{group}] {title} - Assignee: {assignee} - Due: {due_at[:10]}")

except sqlite3.Error as e:
    print(f"❌ Lỗi database: {e}")
finally:
    if conn:
        conn.close()