"""
    Chứa các widget hỗ trợ cho Calendar bao gồm: 
    - Widget cho một công việc + logic (kéo thả)    ---> TaskWidget
    - Widget cho một ngày + logic (nhận TaskWidget) ---> DayWidget
"""

import locale
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (QDialog, QFrame, QHBoxLayout, QCheckBox, QLabel, QVBoxLayout, 
                             QApplication, QMenu, QInputDialog, QStyle, QPushButton, 
                             QScrollArea, QWidget)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag, QCursor, QFont

try:
    locale.setlocale(locale.LC_TIME, 'vi_VN.UTF-8')
except locale.Error:
    print("Locale vi_VN not supported, skipping.")

VIETNAMESE_DAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
VIETNAMESE_MONTHS = [
    "Tháng Một", "Tháng Hai", "Tháng Ba", "Tháng Tư", "Tháng Năm", "Tháng Sáu",
    "Tháng Bảy", "Tháng Tám", "Tháng Chín", "Tháng Mười", "Tháng Mười Một", "Tháng Mười Hai"
]

class TaskDetailItemWidget(QFrame):
    def __init__(self, task_text, is_done, note_text, parent=None):
        super().__init__(parent)
        self.setObjectName("TaskDetailItem")
        self.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(self)
        name_label = QLabel(task_text)
        name_label.setFont(QFont("Arial", 11, QFont.Bold))
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        status_text = "✅ Đã hoàn thành" if is_done else "❌ Chưa hoàn thành"
        status_label = QLabel(f"<b>Trạng thái:</b> {status_text}")
        layout.addWidget(status_label)
        if note_text:
            note_label = QLabel(f"<b>Ghi chú:</b> {note_text}")
            note_label.setWordWrap(True)
            note_label.setObjectName("NoteLabelInDialog")
            layout.addWidget(note_label)

class DayDetailDialog(QDialog):
    def __init__(self, full_date, tasks_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chi Tiết Công Việc Trong Ngày")
        self.setMinimumSize(450, 400)
        self.setObjectName("DayDetailDialog")
        main_layout = QVBoxLayout(self)
        day_name = VIETNAMESE_DAYS[full_date.weekday()]
        month_name = VIETNAMESE_MONTHS[full_date.month - 1]
        date_str = f"{day_name}, ngày {full_date.day} {month_name} năm {full_date.year}"
        date_label = QLabel(date_str)
        date_label.setObjectName("DateHeaderLabel")
        date_label.setAlignment(Qt.AlignCenter)
        header_font = QApplication.instance().font()
        header_font.setPointSize(16)
        header_font.setBold(True)
        date_label.setFont(header_font)
        main_layout.addWidget(date_label)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        tasks_layout = QVBoxLayout(scroll_content)
        tasks_layout.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        if tasks_list:
            for task in tasks_list:
                detail_item = TaskDetailItemWidget(
                    task.label.text(),
                    task.checkbox.isChecked(),
                    task.note
                )
                tasks_layout.addWidget(detail_item)
        else:
            tasks_layout.addWidget(QLabel("Không có công việc nào trong ngày này."))
        close_button = QPushButton("Đóng")
        close_button.clicked.connect(self.accept)
        main_layout.addWidget(close_button, 0, Qt.AlignRight)

class TaskWidget(QFrame):
    def __init__(self, text, is_done=False, note="", task_id=None, view_mode='personal', parent=None):
        super().__init__(parent)
        self.setObjectName("TaskWidget")
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        self.note = note
        self.task_id = task_id
        self.view_mode = view_mode
        self.table_name = 'tasks' if view_mode == 'personal' else 'group_tasks'

        self.layout = QHBoxLayout(self)
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(is_done)
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)

        self.label = QLabel(text)
        self.note_icon_label = QLabel()
        note_icon = self.style().standardIcon(QStyle.SP_FileIcon)
        self.note_icon_label.setPixmap(note_icon.pixmap(16, 16))
        
        self.layout.addWidget(self.checkbox)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.note_icon_label)

        self._update_note_icon()
    
    def _on_checkbox_changed(self, state):
        if self.task_id is None: return
        try:
            is_done = 1 if state == Qt.Checked else 0
            conn = sqlite3.connect("todolist_database.db")
            cursor = conn.cursor()
            query = f"UPDATE {self.table_name} SET is_done = ? WHERE task_id = ?"
            cursor.execute(query, (is_done, self.task_id))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Lỗi khi cập nhật trạng thái công việc: {e}")

    def _update_note_icon(self):
        self.note_icon_label.setVisible(bool(self.note))

    def mouseDoubleClickEvent(self, event):
        new_note, ok = QInputDialog.getMultiLineText(self, "Sửa Ghi Chú", "Nội dung ghi chú:", self.note)
        
        if ok and self.task_id is not None:
            self.note = new_note
            self._update_note_icon()
            try:
                conn = sqlite3.connect("todolist_database.db")
                cursor = conn.cursor()
                query = f"UPDATE {self.table_name} SET note = ? WHERE task_id = ?"
                cursor.execute(query, (self.note, self.task_id))
                conn.commit()
                conn.close()
            except sqlite3.Error as e:
                print(f"Lỗi khi cập nhật ghi chú: {e}")
   
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setProperty("task_widget_ref", self)
        drag.setMimeData(mime_data)
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        drag.exec_(Qt.CopyAction)
    
    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        delete_action = context_menu.addAction("Xóa công việc này")
        action = context_menu.exec_(self.mapToGlobal(event.pos()))
        
        if action == delete_action:
            if self.task_id is not None:
                try:
                    conn = sqlite3.connect("todolist_database.db")
                    cursor = conn.cursor()
                    query = f"DELETE FROM {self.table_name} WHERE task_id = ?"
                    cursor.execute(query, (self.task_id,))
                    conn.commit()
                    conn.close()
                except sqlite3.Error as e:
                    print(f"Lỗi khi xóa công việc: {e}")
            self.deleteLater()

class DayWidget(QFrame):
    def __init__(self, date_text, year, month, user_id, group_id, view_mode, parent=None):
        super().__init__(parent)
        self.setObjectName("DayWidget")
        self.setFrameShape(QFrame.StyledPanel)
        self.setAcceptDrops(True)

        self.day = int(date_text)
        self.year = year
        self.month = month
        self.user_id = user_id
        self.group_id = group_id
        self.view_mode = view_mode
        self.table_name = 'tasks' if view_mode == 'personal' else 'group_tasks'

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignTop)
        
        self.date_label = QLabel(date_text)
        self.date_label.setObjectName("DateLabel")
        self.date_label.setAlignment(Qt.AlignRight)
        self.main_layout.addWidget(self.date_label)

        self.tasks_layout = QVBoxLayout()
        self.tasks_layout.setAlignment(Qt.AlignLeft) 

        tasks_wrapper_layout = QHBoxLayout()
        tasks_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        tasks_wrapper_layout.addLayout(self.tasks_layout)
        tasks_wrapper_layout.addStretch()

        self.main_layout.addLayout(tasks_wrapper_layout)

    def mouseDoubleClickEvent(self, event):
        child_widget = self.childAt(event.pos())
        if child_widget is None or child_widget == self:
            tasks_list = []
            for i in range(self.tasks_layout.count()):
                wrapper_layout = self.tasks_layout.itemAt(i)
                if wrapper_layout and wrapper_layout.layout():
                    widget = wrapper_layout.layout().itemAt(0).widget()
                    if isinstance(widget, TaskWidget):
                        tasks_list.append(widget)
            
            full_date = datetime(self.year, self.month, self.day)
            dialog = DayDetailDialog(full_date, tasks_list, self)
            dialog.exec_()
        else:
            super().mouseDoubleClickEvent(event)

    def add_task(self, task_widget):
        wrapper_layout = QHBoxLayout()
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(task_widget)
        wrapper_layout.addStretch()
        self.tasks_layout.addLayout(wrapper_layout)

    def dragEnterEvent(self, event):
        if event.mimeData().property("task_widget_ref"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        source_widget = event.mimeData().property("task_widget_ref")

        if source_widget:
            task_text = source_widget.label.text()
            note_text = source_widget.note
            due_at_str = f"{self.year}-{self.month:02d}-{self.day:02d} 00:00:00"

            try:
                conn = sqlite3.connect("todolist_database.db")
                cursor = conn.cursor()
                if self.view_mode == 'personal':
                    query = "INSERT INTO tasks (user_id, title, note, is_done, due_at) VALUES (?, ?, ?, ?, ?)"
                    params = (self.user_id, task_text, note_text, 0, due_at_str)
                else:
                    if self.group_id is None: return
                    query = "INSERT INTO group_tasks (group_id, title, note, is_done, due_at) VALUES (?, ?, ?, ?, ?)"
                    params = (self.group_id, task_text, note_text, 0, due_at_str)
                
                cursor.execute(query, params)
                new_task_id = cursor.lastrowid
                conn.commit()
                conn.close()

                new_task = TaskWidget(task_text, note=note_text, task_id=new_task_id, view_mode=self.view_mode)
                self.add_task(new_task)
                event.setDropAction(Qt.CopyAction)
                event.accept()
            except sqlite3.Error as e:
                print(f"Lỗi khi thả công việc: {e}")
                event.ignore()

    def contextMenuEvent(self, event):
        if self.view_mode == 'group' and self.group_id is None:
            return
            
        context_menu = QMenu(self)
        add_task_action = context_menu.addAction("Thêm công việc mới")
        action = context_menu.exec_(self.mapToGlobal(event.pos()))
        if action == add_task_action:
            self._prompt_for_new_task()

    def _prompt_for_new_task(self):
        task_text, ok = QInputDialog.getText(self, "Công việc mới", "Nhập tên công việc:")
        if ok and task_text:
            due_at_str = f"{self.year}-{self.month:02d}-{self.day:02d} 00:00:00"
            try:
                conn = sqlite3.connect("todolist_database.db")
                cursor = conn.cursor()

                if self.view_mode == 'personal':
                    query = "INSERT INTO tasks (user_id, title, note, is_done, due_at) VALUES (?, ?, ?, ?, ?)"
                    params = (self.user_id, task_text, "", 0, due_at_str)
                else:
                    query = "INSERT INTO group_tasks (group_id, title, note, is_done, due_at) VALUES (?, ?, ?, ?, ?)"
                    params = (self.group_id, task_text, "", 0, due_at_str)
                
                cursor.execute(query, params)
                new_task_id = cursor.lastrowid
                conn.commit()
                conn.close()

                new_task = TaskWidget(task_text, note="", task_id=new_task_id, view_mode=self.view_mode)
                self.add_task(new_task)
            except sqlite3.Error as e:
                print(f"Lỗi khi thêm công việc mới: {e}")