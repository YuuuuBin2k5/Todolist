# -*- coding: utf-8 -*-
"""
    Trang chủ hiện đại và đẹp mắt cho ứng dụng To-do List
    - Hiển thị thống kê công việc
    - Danh sách công việc hôm nay và tuần này
    - Lịch mini
    - Công việc gần hết hạn
    - Tiến độ hoàn thành
"""

import sqlite3
import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QCheckBox, QScrollArea, QFrame,
                             QGridLayout, QProgressBar, QTextEdit, QCalendarWidget,
                             QGroupBox, QSizePolicy, QSpacerItem)
from PyQt5.QtCore import Qt, pyqtSignal, QDate, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QPainter, QBrush

def _get_database_path():
    """Lấy đường dẫn tuyệt đối đến file database trong thư mục Data"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.dirname(current_dir)
    return os.path.join(src_dir, 'Data', 'todolist_database.db')

class StatsCard(QFrame):
    """Widget hiển thị thống kê dạng card"""
    def __init__(self, title, value, color="#5c6bc0", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)
        self.setFixedSize(150, 100)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 12px;
                padding: 10px;
                margin: 5px;
            }}
            QLabel {{
                color: white;
                font-weight: bold;
                border: none;
                background: transparent;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Giá trị số
        value_label = QLabel(str(value))
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        # Tiêu đề
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 12px;")
        title_label.setWordWrap(True)
        
        layout.addWidget(value_label)
        layout.addWidget(title_label)

class TaskItemWidget(QFrame):
    """Widget hiển thị một task với giao diện đẹp"""
    task_updated = pyqtSignal()
    
    def __init__(self, task_id, title, is_done, due_date=None, note="", parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self.title = title
        self.is_done = is_done
        self.due_date = due_date
        self.note = note
        self.parent_widget = parent
        
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 5px;
                margin: 2px;
            }
            QFrame:hover {
                border: 1px solid #5c6bc0;
                background-color: #f8f9ff;
            }
            QCheckBox {
                spacing: 8px;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #5c6bc0;
            }
            QCheckBox::indicator:checked {
                background-color: #5c6bc0;
                border: 2px solid #5c6bc0;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 12px;
                color: #ef5350;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #ffebee;
                border-radius: 4px;
            }
        """)
        
        self.setupUI()
        
    def setupUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)
        
        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.is_done)
        self.checkbox.stateChanged.connect(self._handle_completion_change)
        
        # Nội dung task
        content_layout = QVBoxLayout()
        
        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setWordWrap(True)
        title_font = self.title_label.font()
        title_font.setPointSize(11)
        title_font.setBold(not self.is_done)
        self.title_label.setFont(title_font)
        
        if self.is_done:
            self.title_label.setStyleSheet("text-decoration: line-through; color: #888;")
        else:
            self.title_label.setStyleSheet("color: #333;")
            
        content_layout.addWidget(self.title_label)
        
        # Due date và note (nếu có)
        if self.due_date or self.note:
            details_layout = QHBoxLayout()
            details_layout.setSpacing(10)
            
            if self.due_date:
                due_label = QLabel(f"📅 {self.due_date}")
                due_label.setStyleSheet("color: #666; font-size: 10px;")
                details_layout.addWidget(due_label)
                
            if self.note:
                note_label = QLabel(f"📝 {self.note[:30]}...")
                note_label.setStyleSheet("color: #666; font-size: 10px;")
                details_layout.addWidget(note_label)
                
            details_layout.addStretch()
            content_layout.addLayout(details_layout)
        
        layout.addWidget(self.checkbox)
        layout.addLayout(content_layout, 1)
        
        # Nút xóa
        delete_btn = QPushButton("✕")
        delete_btn.setFixedSize(20, 20)
        delete_btn.clicked.connect(self._handle_delete)
        layout.addWidget(delete_btn)
        
    def _handle_completion_change(self, state):
        self.is_done = self.checkbox.isChecked()
        
        if self.is_done:
            self.title_label.setStyleSheet("text-decoration: line-through; color: #888;")
            title_font = self.title_label.font()
            title_font.setBold(False)
            self.title_label.setFont(title_font)
        else:
            self.title_label.setStyleSheet("color: #333;")
            title_font = self.title_label.font()
            title_font.setBold(True)
            self.title_label.setFont(title_font)
        
        self._update_task_in_db()
        
    def _update_task_in_db(self):
        try:
            conn = sqlite3.connect(_get_database_path())
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET is_done = ? WHERE task_id = ?", 
                           (self.is_done, self.task_id))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Lỗi khi cập nhật task: {e}")
        finally:
            self.task_updated.emit()
            
    def _handle_delete(self):
        try:
            conn = sqlite3.connect(_get_database_path())
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE task_id = ?", (self.task_id,))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Lỗi khi xóa task: {e}")
        finally:
            self.task_updated.emit()
            self.parent_widget.load_tasks()

class HomePageWidget(QWidget):
    """Trang chủ chính với giao diện đẹp và đầy đủ tính năng"""
    
    def __init__(self, user_id=None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setupUI()
        self.load_data()
        
        # Timer để cập nhật thời gian thực
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Cập nhật mỗi giây
        
    def setupUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header với chào mừng và thời gian
        self.create_header(main_layout)
        
        # Thống kê nhanh
        self.create_stats_section(main_layout)
        
        # Layout chính với 2 cột
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Cột trái: Tasks và Quick Add
        left_column = QVBoxLayout()
        self.create_quick_add_section(left_column)
        self.create_today_tasks_section(left_column)
        content_layout.addLayout(left_column, 2)
        
        # Cột phải: Calendar mini và Upcoming tasks
        right_column = QVBoxLayout()
        self.create_mini_calendar_section(right_column)
        self.create_upcoming_tasks_section(right_column)
        content_layout.addLayout(right_column, 1)
        
        main_layout.addLayout(content_layout)
        
    def create_header(self, parent_layout):
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 #667eea, stop:1 #764ba2);
                border-radius: 15px;
                padding: 20px;
            }
            QLabel {
                color: white;
                background: transparent;
                border: none;
            }
        """)
        
        header_layout = QVBoxLayout(header_frame)
        
        # Chào mừng
        self.welcome_label = QLabel("Chào mừng trở lại! 👋")
        welcome_font = QFont()
        welcome_font.setFamily("Segoe UI, Arial, sans-serif")  # Font hỗ trợ tiếng Việt tốt
        welcome_font.setPointSize(18)
        welcome_font.setBold(True)
        self.welcome_label.setFont(welcome_font)
        
        # Thời gian hiện tại
        self.time_label = QLabel()
        time_font = QFont()
        time_font.setFamily("Segoe UI, Arial, sans-serif")  # Font hỗ trợ tiếng Việt tốt
        time_font.setPointSize(12)
        self.time_label.setFont(time_font)
        self.update_time()
        
        header_layout.addWidget(self.welcome_label)
        header_layout.addWidget(self.time_label)
        
        parent_layout.addWidget(header_frame)
        
    def create_stats_section(self, parent_layout):
        stats_frame = QGroupBox("📊 Thống kê")
        stats_frame.setStyleSheet("""
            QGroupBox {
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-weight: bold;
                font-size: 14px;
                color: #333;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                margin-top: 10px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        stats_layout = QHBoxLayout(stats_frame)
        
        # Các thẻ thống kê sẽ được tạo động trong load_data()
        self.stats_layout = stats_layout
        
        parent_layout.addWidget(stats_frame)
        
    def create_quick_add_section(self, parent_layout):
        add_frame = QGroupBox("➕ Thêm công việc mới")
        add_frame.setStyleSheet("""
            QGroupBox {
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-weight: bold;
                font-size: 14px;
                color: #333;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                margin-top: 10px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        add_layout = QVBoxLayout(add_frame)
        
        # Input và nút thêm
        input_layout = QHBoxLayout()
        
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Nhập công việc mới...")
        self.task_input.setStyleSheet("""
            QLineEdit {
                font-family: 'Segoe UI', 'Arial', sans-serif;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #5c6bc0;
                background-color: #f8f9ff;
            }
        """)
        self.task_input.returnPressed.connect(self._add_task)
        
        add_btn = QPushButton("Thêm")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c6bc0;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4a5aa8;
            }
            QPushButton:pressed {
                background-color: #3f4f96;
            }
        """)
        add_btn.clicked.connect(self._add_task)
        
        input_layout.addWidget(self.task_input, 1)
        input_layout.addWidget(add_btn)
        
        add_layout.addLayout(input_layout)
        parent_layout.addWidget(add_frame)
        
    def create_today_tasks_section(self, parent_layout):
        tasks_frame = QGroupBox("📋 Công việc hôm nay")
        tasks_frame.setStyleSheet("""
            QGroupBox {
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-weight: bold;
                font-size: 14px;
                color: #333;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                margin-top: 10px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        tasks_layout = QVBoxLayout(tasks_frame)
        
        # Scroll area cho danh sách tasks
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f8f9fa;
                border-radius: 8px;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
        """)
        
        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(5, 5, 5, 5)
        self.tasks_layout.setAlignment(Qt.AlignTop)
        
        scroll_area.setWidget(self.tasks_container)
        tasks_layout.addWidget(scroll_area)
        
        parent_layout.addWidget(tasks_frame)
        
    def create_mini_calendar_section(self, parent_layout):
        calendar_frame = QGroupBox("🗓️ Lịch")
        calendar_frame.setStyleSheet("""
            QGroupBox {
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-weight: bold;
                font-size: 14px;
                color: #333;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                margin-top: 10px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        calendar_layout = QVBoxLayout(calendar_frame)
        
        self.mini_calendar = QCalendarWidget()
        self.mini_calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                border-radius: 8px;
            }
            QCalendarWidget QToolButton {
                background-color: #5c6bc0;
                color: white;
                border: none;
                padding: 5px;
            }
        """)
        
        calendar_layout.addWidget(self.mini_calendar)
        parent_layout.addWidget(calendar_frame)
        
    def create_upcoming_tasks_section(self, parent_layout):
        upcoming_frame = QGroupBox("⏰ Sắp đến hạn")
        upcoming_frame.setStyleSheet("""
            QGroupBox {
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-weight: bold;
                font-size: 14px;
                color: #333;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                margin-top: 10px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        upcoming_layout = QVBoxLayout(upcoming_frame)
        
        # Container cho upcoming tasks
        self.upcoming_container = QWidget()
        self.upcoming_layout = QVBoxLayout(self.upcoming_container)
        self.upcoming_layout.setAlignment(Qt.AlignTop)
        
        upcoming_scroll = QScrollArea()
        upcoming_scroll.setWidgetResizable(True)
        upcoming_scroll.setWidget(self.upcoming_container)
        upcoming_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f8f9fa;
                border-radius: 8px;
            }
        """)
        
        upcoming_layout.addWidget(upcoming_scroll)
        parent_layout.addWidget(upcoming_frame)
        
    def update_time(self):
        current_time = datetime.now()
        time_str = current_time.strftime("%H:%M:%S")
        
        # Tên ngày trong tuần bằng tiếng Việt (sử dụng weekday())
        day_names = [
            'Thứ Hai',    # 0 - Monday
            'Thứ Ba',     # 1 - Tuesday  
            'Thứ Tư',     # 2 - Wednesday
            'Thứ Nam',    # 3 - Thursday
            'Thứ Sáu',    # 4 - Friday
            'Thứ Bảy',    # 5 - Saturday
            'Chủ Nhật'    # 6 - Sunday
        ]
        
        day_name = day_names[current_time.weekday()]
        date_str = f"{day_name}, {current_time.strftime('%d/%m/%Y')}"
            
        self.time_label.setText(f"{date_str} • {time_str}")
        
    def load_data(self):
        """Tải và hiển thị tất cả dữ liệu"""
        self.load_stats()
        self.load_tasks()
        self.load_upcoming_tasks()
        
    def load_stats(self):
        """Tải thống kê và hiển thị"""
        try:
            conn = sqlite3.connect(_get_database_path())
            cursor = conn.cursor()
            
            # Tổng số tasks
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (self.user_id,))
            total_tasks = cursor.fetchone()[0]
            
            # Tasks hoàn thành
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND is_done = 1", (self.user_id,))
            completed_tasks = cursor.fetchone()[0]
            
            # Tasks hôm nay
            today = datetime.now().date().strftime("%Y-%m-%d")
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND DATE(created_at) = ?", (self.user_id, today))
            today_tasks = cursor.fetchone()[0]
            
            # Tasks chưa hoàn thành
            pending_tasks = total_tasks - completed_tasks
            
            conn.close()
            
            # Xóa các stats cũ
            for i in reversed(range(self.stats_layout.count())): 
                item = self.stats_layout.itemAt(i)
                if item and item.widget():
                    item.widget().setParent(None)
            
            # Thêm các thẻ thống kê mới
            stats_data = [
                ("Tổng công việc", total_tasks, "#5c6bc0"),
                ("Hoàn thành", completed_tasks, "#4caf50"),
                ("Đang thực hiện", pending_tasks, "#ff9800"),
                ("Hôm nay", today_tasks, "#9c27b0")
            ]
            
            for title, value, color in stats_data:
                card = StatsCard(title, value, color)
                self.stats_layout.addWidget(card)
                
            # Thêm spacer để căn trái
            self.stats_layout.addStretch()
            
        except sqlite3.Error as e:
            print(f"Lỗi khi tải thống kê: {e}")
            
    def load_tasks(self):
        """Tải công việc hôm nay"""
        # Xóa tasks cũ
        for i in reversed(range(self.tasks_layout.count())): 
            item = self.tasks_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
            
        try:
            conn = sqlite3.connect(_get_database_path())
            cursor = conn.cursor()
            
            # Lấy tasks (ưu tiên chưa hoàn thành trước)
            cursor.execute("""
                SELECT task_id, title, is_done, due_at, note 
                FROM tasks 
                WHERE user_id = ? 
                ORDER BY is_done ASC, created_at DESC 
                LIMIT 20
            """, (self.user_id,))
            
            tasks = cursor.fetchall()
            conn.close()
            
            if not tasks:
                no_tasks_label = QLabel("Không có công việc nào. Hãy thêm công việc mới! 😊")
                no_tasks_label.setAlignment(Qt.AlignCenter)
                no_tasks_label.setStyleSheet("""
                    font-family: 'Segoe UI', 'Arial', sans-serif;
                    color: #888;
                    font-size: 14px;
                    padding: 20px;
                    font-style: italic;
                """)
                self.tasks_layout.addWidget(no_tasks_label)
            else:
                for task_id, title, is_done, due_at, note in tasks:
                    # Format due_at nếu có
                    due_date_str = None
                    if due_at:
                        try:
                            due_date = datetime.fromisoformat(due_at.replace('Z', '+00:00'))
                            due_date_str = due_date.strftime("%d/%m")
                        except:
                            pass
                    
                    task_widget = TaskItemWidget(
                        task_id, title, bool(is_done), due_date_str, note or "", self
                    )
                    task_widget.task_updated.connect(self.load_data)
                    self.tasks_layout.addWidget(task_widget)
                    
        except sqlite3.Error as e:
            print(f"Lỗi khi tải tasks: {e}")
            
    def load_upcoming_tasks(self):
        """Tải các task sắp đến hạn"""
        # Xóa upcoming tasks cũ
        for i in reversed(range(self.upcoming_layout.count())): 
            item = self.upcoming_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
            
        try:
            conn = sqlite3.connect(_get_database_path())
            cursor = conn.cursor()
            
            # Lấy tasks có due_at trong 7 ngày tới
            next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            cursor.execute("""
                SELECT task_id, title, due_at 
                FROM tasks 
                WHERE user_id = ? AND is_done = 0 AND due_at IS NOT NULL 
                AND DATE(due_at) <= ? 
                ORDER BY due_at ASC 
                LIMIT 10
            """, (self.user_id, next_week))
            
            upcoming_tasks = cursor.fetchall()
            conn.close()
            
            if not upcoming_tasks:
                no_upcoming_label = QLabel("Không có công việc sắp đến hạn 🎉")
                no_upcoming_label.setAlignment(Qt.AlignCenter)
                no_upcoming_label.setStyleSheet("""
                    font-family: 'Segoe UI', 'Arial', sans-serif;
                    color: #888;
                    font-size: 12px;
                    padding: 15px;
                    font-style: italic;
                """)
                self.upcoming_layout.addWidget(no_upcoming_label)
            else:
                for task_id, title, due_at in upcoming_tasks:
                    upcoming_item = self._create_upcoming_item(title, due_at)
                    self.upcoming_layout.addWidget(upcoming_item)
                    
        except sqlite3.Error as e:
            print(f"Lỗi khi tải upcoming tasks: {e}")
            
    def _create_upcoming_item(self, title, due_at):
        """Tạo item cho upcoming task"""
        item_frame = QFrame()
        item_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
                margin: 2px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(item_frame)
        layout.setContentsMargins(8, 6, 8, 6)
        
        # Title
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #333;")
        
        # Due date
        try:
            due_date = datetime.fromisoformat(due_at.replace('Z', '+00:00'))
            due_str = due_date.strftime("%d/%m - %H:%M")
            
            # Tính số ngày còn lại
            days_left = (due_date.date() - datetime.now().date()).days
            if days_left == 0:
                due_str += " (Hôm nay)"
                color = "#f44336"
            elif days_left == 1:
                due_str += " (Ngày mai)"
                color = "#ff9800"
            else:
                due_str += f" ({days_left} ngày)"
                color = "#666"
                
        except:
            due_str = due_at
            color = "#666"
            
        due_label = QLabel(due_str)
        due_label.setStyleSheet(f"font-size: 10px; color: {color};")
        
        layout.addWidget(title_label)
        layout.addWidget(due_label)
        
        return item_frame
        
    def _add_task(self):
        """Thêm task mới"""
        title = self.task_input.text().strip()
        if not title:
            return
            
        try:
            conn = sqlite3.connect(_get_database_path())
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (user_id, title, is_done, created_at) 
                VALUES (?, ?, 0, CURRENT_TIMESTAMP)
            """, (self.user_id, title))
            conn.commit()
            conn.close()
            
            self.task_input.clear()
            self.load_data()  # Reload toàn bộ dữ liệu
            
        except sqlite3.Error as e:
            print(f"Lỗi khi thêm task: {e}")