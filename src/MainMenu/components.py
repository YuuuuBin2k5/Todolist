# File: MainMenu/components.py

import locale
from datetime import datetime
from PyQt5.QtWidgets import (QDialog, QFrame, QHBoxLayout, QCheckBox, QLabel, QVBoxLayout,
                             QApplication, QMenu, QInputDialog, QStyle, QPushButton,
                             QScrollArea, QWidget)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag, QCursor, QFont

# Thiết lập ngôn ngữ Tiếng Việt để hiển thị đúng Thứ trong tuần
try:
    locale.setlocale(locale.LC_TIME, 'vi_VN.UTF-8')
except locale.Error:
    print("Locale vi_VN not supported, skipping.")

VIETNAMESE_DAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
VIETNAMESE_MONTHS = [
    "Tháng Một", "Tháng Hai", "Tháng Ba", "Tháng Tư", "Tháng Năm", "Tháng Sáu",
    "Tháng Bảy", "Tháng Tám", "Tháng Chín", "Tháng Mười", "Tháng Mười Một", "Tháng Mười Hai"
]

# ==============================================================================
# LỚP BỊ THIẾU SỐ 1: TaskDetailItemWidget
# ==============================================================================
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

# ==============================================================================
# LỚP BỊ THIẾU SỐ 2: DayDetailDialog
# ==============================================================================
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

# ==============================================================================
# LỚP 3: TaskWidget (Phiên bản đầy đủ và đã sửa lỗi)
# ==============================================================================
class TaskWidget(QFrame):
    def __init__(self, text, is_done=False, note="", assignee_name=None, parent=None):
        super().__init__(parent)
        self.setObjectName("TaskWidget")
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        self.note = note

        self.main_v_layout = QVBoxLayout(self)
        self.main_v_layout.setContentsMargins(4, 4, 4, 4)
        self.main_v_layout.setSpacing(2)

        top_h_layout = QHBoxLayout()
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(is_done)
        self.label = QLabel(text)
        self.label.setWordWrap(True)

        self.note_icon_label = QLabel()
        note_icon = self.style().standardIcon(QStyle.SP_FileIcon)
        self.note_icon_label.setPixmap(note_icon.pixmap(16, 16))
        
        top_h_layout.addWidget(self.checkbox)
        top_h_layout.addWidget(self.label, 1)
        top_h_layout.addStretch()
        top_h_layout.addWidget(self.note_icon_label)
        
        self.main_v_layout.addLayout(top_h_layout)

        if assignee_name:
            self.assignee_label = QLabel(f"👤 {assignee_name}")
            assignee_font = self.assignee_label.font()
            assignee_font.setPointSize(9)
            assignee_font.setItalic(True)
            self.assignee_label.setFont(assignee_font)
            self.assignee_label.setStyleSheet("color: #0056b3; margin-left: 18px;")
            self.main_v_layout.addWidget(self.assignee_label)
        
        self._update_note_icon()

    def _update_note_icon(self):
        self.note_icon_label.setVisible(bool(self.note and self.note.strip()))

    def mouseDoubleClickEvent(self, event):
        new_note, ok = QInputDialog.getMultiLineText(self, "Sửa Ghi Chú", "Nội dung ghi chú:", self.note)
        if ok:
            self.note = new_note
            self._update_note_icon()
   
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
            self.deleteLater()

# ==============================================================================
# LỚP 4: DayWidget (Phiên bản đầy đủ và đã sửa lỗi)
# ==============================================================================
class DayWidget(QFrame):
    def __init__(self, date_text, year, month, parent=None):
        super().__init__(parent)
        self.setObjectName("DayWidget")
        self.setFrameShape(QFrame.StyledPanel)
        self.setAcceptDrops(True)

        self.day = int(date_text)
        self.year = year
        self.month = month

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignTop)

        self.date_label = QLabel(date_text)
        self.date_label.setObjectName("DateLabel")
        self.date_label.setAlignment(Qt.AlignRight)
        self.main_layout.addWidget(self.date_label)

        self.tasks_layout = QVBoxLayout()
        self.main_layout.addLayout(self.tasks_layout)

    def mouseDoubleClickEvent(self, event):
        child_widget = self.childAt(event.pos())
        if child_widget is None or child_widget == self:
            tasks_list = []
            for i in range(self.tasks_layout.count()):
                widget = self.tasks_layout.itemAt(i).widget()
                if isinstance(widget, TaskWidget):
                    tasks_list.append(widget)
            
            full_date = datetime(self.year, self.month, self.day)
            
            dialog = DayDetailDialog(full_date, tasks_list, self)
            dialog.exec_()
        else:
            super().mouseDoubleClickEvent(event)

    def add_task(self, task_widget):
        self.tasks_layout.addWidget(task_widget)

    def dragEnterEvent(self, event):
        if event.mimeData().property("task_widget_ref"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        source_widget = event.mimeData().property("task_widget_ref")
        if source_widget:
            task_text = source_widget.label.text()
            note_text = source_widget.note
            
            new_task = TaskWidget(task_text, note=note_text)
            self.add_task(new_task)
            event.setDropAction(Qt.CopyAction)
            event.accept()

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        add_task_action = context_menu.addAction("Thêm công việc mới")
        action = context_menu.exec_(self.mapToGlobal(event.pos()))
        if action == add_task_action:
            self._prompt_for_new_task()

    def _prompt_for_new_task(self):
        task_text, ok = QInputDialog.getText(self, "Công việc mới", "Nhập tên công việc:")
        if ok and task_text:
            new_task = TaskWidget(task_text, note="")
            self.add_task(new_task)