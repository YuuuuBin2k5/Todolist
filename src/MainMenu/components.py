# File: MainMenu/components.py

import locale
from datetime import datetime
from PyQt5.QtWidgets import (QDialog, QFrame, QHBoxLayout, QCheckBox, QLabel, QVBoxLayout,
                             QApplication, QMenu, QInputDialog, QStyle, QPushButton,
                             QScrollArea, QWidget, QLineEdit, QDateTimeEdit, QTextEdit, QDialogButtonBox, QMessageBox)
from PyQt5.QtCore import Qt, QMimeData, QDate, QDateTime
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
    def __init__(self, task_data: dict, calendar_ref=None, parent=None):
        """task_data keys: title, is_done, note, assignee_name, due_at, task_id, is_group"""
        super().__init__(parent)
        self.setObjectName("TaskDetailItem")
        self.setFrameShape(QFrame.StyledPanel)
        self.calendar_ref = calendar_ref

        # normalize
        title = task_data.get('title')
        is_done = task_data.get('is_done', False)
        note_text = task_data.get('note', '')
        assignee = task_data.get('assignee_name')
        due_at = task_data.get('due_at')
        task_id = task_data.get('task_id')
        is_group = task_data.get('is_group', False)

        layout = QVBoxLayout(self)

        name_label = QLabel(title)
        name_label.setFont(QFont("Arial", 11, QFont.Bold))
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        # top info row: status, assignee, due
        info_row = QHBoxLayout()
        status_text = "✅ Đã hoàn thành" if is_done else "❌ Chưa hoàn thành"
        status_label = QLabel(status_text)
        status_label.setObjectName('StatusSmall')
        info_row.addWidget(status_label)
        if assignee:
            assignee_label = QLabel(f"👤 {assignee}")
            assignee_label.setStyleSheet('color:#0056b3; margin-left:8px;')
            info_row.addWidget(assignee_label)
        if due_at:
            due_label = QLabel(f"⏰ {due_at}")
            due_label.setStyleSheet('color:#666; margin-left:8px;')
            info_row.addWidget(due_label)
        info_row.addStretch()
        layout.addLayout(info_row)

        if note_text:
            note_label = QLabel(f"<b>Ghi chú:</b> {note_text}")
            note_label.setWordWrap(True)
            note_label.setObjectName("NoteLabelInDialog")
            layout.addWidget(note_label)

        # actions for leader/owner
        actions_row = QHBoxLayout()
        actions_row.addStretch()
        # toggle button
        toggle_btn = QPushButton("Đổi trạng thái")
        delete_btn = QPushButton("Xóa")
        def do_toggle():
            try:
                if self.calendar_ref and task_id is not None:
                    # flip
                    new_state = 0 if is_done else 1
                    self.calendar_ref.update_task_status(task_id, new_state, is_group=is_group)
            except Exception:
                pass
        def do_delete():
            try:
                if self.calendar_ref and task_id is not None:
                    self.calendar_ref.delete_task(task_id, is_group=is_group)
            except Exception:
                pass
        toggle_btn.clicked.connect(do_toggle)
        delete_btn.clicked.connect(do_delete)
        actions_row.addWidget(toggle_btn)
        actions_row.addWidget(delete_btn)
        layout.addLayout(actions_row)

# ==============================================================================
# LỚP BỊ THIẾU SỐ 2: DayDetailDialog
# ==============================================================================
class DayDetailDialog(QDialog):
    def __init__(self, full_date, tasks_data: list, calendar_ref=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chi Tiết Công Việc Trong Ngày")
        self.setMinimumSize(520, 460)
        self.setObjectName("DayDetailDialog")
        self.calendar_ref = calendar_ref

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

        if tasks_data:
            for tdata in tasks_data:
                detail_item = TaskDetailItemWidget(tdata, calendar_ref=self.calendar_ref)
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
    def __init__(self, text, is_done=False, note="", assignee_name=None, parent=None, task_id=None, is_group=False, calendar_ref=None):
        super().__init__(parent)
        self.setObjectName("TaskWidget")
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        self.note = note
        # optional identifiers for persistence actions
        self.task_id = task_id
        self.is_group = is_group
        self.calendar_ref = calendar_ref

        self.main_v_layout = QVBoxLayout(self)
        self.main_v_layout.setContentsMargins(4, 4, 4, 4)
        self.main_v_layout.setSpacing(2)

        top_h_layout = QHBoxLayout()
        self.checkbox = QCheckBox()
        # Convert is_done to boolean (handles int 0/1, string "0"/"1", or actual boolean)
        if isinstance(is_done, str):
            self.checkbox.setChecked(is_done == "1" or is_done.lower() == "true")
        elif isinstance(is_done, int):
            self.checkbox.setChecked(bool(is_done))
        else:
            self.checkbox.setChecked(bool(is_done))
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        # connect checkbox state change to update DB via calendar_ref
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)

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


class TaskBadge(QLabel):
    """A compact, rounded badge used inside calendar day tiles to represent a task.

    This is a visual-only lightweight widget; interactions (edit/toggle) should be done
    in the DayDetailDialog or via context menus if desired.
    """
    def __init__(self, title, color='#66bb6a', note='', assignee_name=None, parent=None, task_id=None, is_group=False, calendar_ref=None):
        super().__init__(parent)
        self.setObjectName('TaskBadge')
        self.setText(title if title else '')
        self.setToolTip(note if note else title)
        self.setWordWrap(False)
        self.setContentsMargins(6, 4, 6, 4)
        self.task_id = task_id
        self.is_group = is_group
        self.calendar_ref = calendar_ref
        self.assignee_name = assignee_name
        # color may be a hex; use different default for group vs personal
        style = f"background: {color}; color: white; padding: 6px 10px; border-radius: 12px; font-size: 11px;"
        self.setStyleSheet(style)
        self.setMinimumHeight(26)
        self.setMaximumWidth(220)

    def mousePressEvent(self, event):
        # If a short click and the badge has a 'day' attribute, open day detail dialog
        try:
            if event.button() == Qt.LeftButton and hasattr(self, 'day') and self.calendar_ref:
                # open day detail via calendar_ref
                try:
                    self.calendar_ref.open_day_detail(self.day)
                    return
                except Exception:
                    pass
            # otherwise start possible drag
            if event.button() == Qt.LeftButton:
                self.drag_start_position = event.pos()
        except Exception:
            pass

    def _update_note_icon(self):
        # placeholder for compatibility with TaskWidget
        return

    def mouseDoubleClickEvent(self, event):
        # Allow editing note on double click if needed
        try:
            new_note, ok = QInputDialog.getMultiLineText(self, "Sửa Ghi Chú", "Nội dung ghi chú:", getattr(self, 'note', ''))
            if ok:
                self.note = new_note
        except Exception:
            pass

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
            # If this widget is backed by a DB task, request deletion via calendar_ref
            try:
                if self.task_id and self.calendar_ref:
                    self.calendar_ref.delete_task(self.task_id, self.is_group)
            except Exception:
                pass
            self.deleteLater()

    def _on_checkbox_changed(self, state):
        is_done = 1 if state == Qt.Checked else 0
        # optimistic UI is already updated by the checkbox
        try:
            if self.task_id and self.calendar_ref:
                # Permission check: ask calendar if current user can toggle this task
                try:
                    allowed, msg = self.calendar_ref.can_toggle_task(self.task_id, self.is_group)
                except Exception:
                    allowed, msg = False, "Lỗi kiểm tra quyền."
                if not allowed:
                    # revert checkbox to previous state
                    self.checkbox.blockSignals(True)
                    self.checkbox.setChecked(not bool(is_done))
                    self.checkbox.blockSignals(False)
                    # show message to user
                    QMessageBox.warning(self, "Không có quyền", msg)
                    return
                # call calendar wrapper to persist change
                self.calendar_ref.update_task_status(self.task_id, is_done, self.is_group)
        except Exception:
            pass

# ==============================================================================
# LỚP 4: GroupTaskWidget (Widget cho group tasks với thông tin assignee)
# ==============================================================================
class GroupTaskWidget(TaskWidget):
    def __init__(self, text, is_done=False, assignee_name="", note="", parent=None, task_id=None, is_group=True, calendar_ref=None):
        # TaskWidget signature: (text, is_done=False, note="", assignee_name=None, parent=None, task_id=None, is_group=False, calendar_ref=None)
        super().__init__(text, is_done, note, assignee_name, parent, task_id, is_group, calendar_ref)
        self.assignee_name = assignee_name

# ==============================================================================
# LỚP 5: DayWidget (Phiên bản đầy đủ và đã sửa lỗi)
# ==============================================================================
class AddTaskDialog(QDialog):
    def __init__(self, parent=None, default_date: datetime = None):
        super().__init__(parent)
        self.setWindowTitle("✨ Thêm công việc mới")
        self.setMinimumWidth(420)
        self.setObjectName("AddTaskDialog")

        # --- Styling (green theme) ---
        self.setStyleSheet("""
            #AddTaskDialog { background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #f4fff4, stop:1 #ecffef); border-radius: 12px; }
            QLabel#HeaderLabel { font-size:16px; font-weight:700; color:#1b5e20; }
            QLineEdit, QTextEdit, QDateTimeEdit { background: white; border: 1px solid #cfe9cf; border-radius: 8px; padding: 8px; }
            QLineEdit:focus, QTextEdit:focus, QDateTimeEdit:focus { border: 1px solid #66bb6a; }
            QPushButton#OkButton { background-color: #28a745; color: white; border-radius: 8px; padding: 8px 14px; }
            QPushButton#CancelButton { background-color: transparent; color: #2e7d32; border: 1px solid #cfe9cf; border-radius: 8px; padding: 6px 12px; }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        header = QLabel("🪴 Thêm công việc")
        header.setObjectName("HeaderLabel")
        main_layout.addWidget(header)

        # Title
        title_label = QLabel("Tiêu đề")
        title_label.setStyleSheet("color: #2e7d32; font-weight:600;")
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Nhập tiêu đề công việc...")
        self.title_input.setFixedHeight(34)
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.title_input)

        # Date & time
        date_label = QLabel("Ngày giờ hoàn thành")
        date_label.setStyleSheet("color: #2e7d32; font-weight:600;")
        self.date_edit = QDateTimeEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat('yyyy-MM-dd HH:mm:ss')
        self.date_edit.setFixedHeight(34)
        if default_date:
            dt = QDateTime(default_date.year, default_date.month, default_date.day,
                           default_date.hour if hasattr(default_date, 'hour') else 0,
                           default_date.minute if hasattr(default_date, 'minute') else 0,
                           default_date.second if hasattr(default_date, 'second') else 0)
            self.date_edit.setDateTime(dt)
        else:
            self.date_edit.setDateTime(QDateTime.currentDateTime())
        main_layout.addWidget(date_label)
        main_layout.addWidget(self.date_edit)

        # Note
        note_label = QLabel("Ghi chú (tùy chọn)")
        note_label.setStyleSheet("color: #2e7d32; font-weight:600;")
        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Một vài ghi chú ngắn...")
        self.note_edit.setFixedHeight(90)
        main_layout.addWidget(note_label)
        main_layout.addWidget(self.note_edit)

        # Buttons
        buttons_box = QDialogButtonBox()
        ok_btn = buttons_box.addButton("Thêm", QDialogButtonBox.AcceptRole)
        ok_btn.setObjectName("OkButton")
        cancel_btn = buttons_box.addButton("Hủy", QDialogButtonBox.RejectRole)
        cancel_btn.setObjectName("CancelButton")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        main_layout.addWidget(buttons_box)

    def title(self) -> str:
        return self.title_input.text().strip()

    def due_datetime(self) -> QDateTime:
        return self.date_edit.dateTime()

    def note(self) -> str:
        return self.note_edit.toPlainText().strip()


class DayWidget(QFrame):
    def __init__(self, date_text, year, month, parent=None, calendar_ref=None):
        super().__init__(parent)
        self.setObjectName("DayWidget")
        self.setFrameShape(QFrame.StyledPanel)
        self.setAcceptDrops(True)

        self.day = int(date_text)
        self.year = year
        self.month = month
        self.calendar_ref = calendar_ref

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignTop)

        self.date_label = QLabel(date_text)
        self.date_label.setObjectName("DateLabel")
        self.date_label.setAlignment(Qt.AlignRight)
        self.date_label.setStyleSheet("background: transparent;")
        self.main_layout.addWidget(self.date_label)

        self.tasks_layout = QVBoxLayout()
        self.main_layout.addLayout(self.tasks_layout)

    def _prompt_for_new_task(self):
        default_date = datetime(self.year, self.month, self.day)
        dialog = AddTaskDialog(self, default_date=default_date)
        if dialog.exec_() == QDialog.Accepted and dialog.title():
            title = dialog.title()
            due_qdt = dialog.due_datetime()
            due_dt = datetime(due_qdt.date().year(), due_qdt.date().month(), due_qdt.date().day(),
                              due_qdt.time().hour(), due_qdt.time().minute(), due_qdt.time().second())
            note = dialog.note()

            if self.calendar_ref:
                if getattr(self.calendar_ref, 'current_view_mode', 'personal') == 'group':
                    # no assignee selected from day cell; pass None
                    try:
                        self.calendar_ref.add_group_task_to_db(due_dt, title, None, note)
                    except Exception:
                        # fallback to personal task if group handling fails
                        self.calendar_ref.add_task_to_db(due_dt, title, note)
                else:
                    self.calendar_ref.add_task_to_db(due_dt, title, note)
            else:
                new_task = TaskWidget(title, note=note)
                self.add_task(new_task)

    def set_today_highlight(self, enabled=True):
        if enabled:
            self.setStyleSheet(
                "background-color: rgba(255, 0, 0, 60);"
                "border-radius: 6px;"
                "padding: 4px;"
            )
        else:
            self.setStyleSheet("")

    def mouseDoubleClickEvent(self, event):
        child_widget = self.childAt(event.pos())
        if child_widget is None or child_widget == self:
            tasks_data = []
            for i in range(self.tasks_layout.count()):
                widget = self.tasks_layout.itemAt(i).widget()
                # normalize TaskBadge or TaskWidget into dict for dialog
                if widget is None:
                    continue
                if hasattr(widget, 'task_id'):
                    tasks_data.append({
                        'title': widget.text() if hasattr(widget, 'text') else getattr(widget, 'label', lambda: '')(),
                        'is_done': getattr(widget, 'checkbox', None) and getattr(widget.checkbox, 'isChecked', lambda: False)(),
                        'note': getattr(widget, 'note', ''),
                        'assignee_name': getattr(widget, 'assignee_name', None) or None,
                        'due_at': None,
                        'task_id': getattr(widget, 'task_id', None),
                        'is_group': getattr(widget, 'is_group', False)
                    })

            full_date = datetime(self.year, self.month, self.day)
            dialog = DayDetailDialog(full_date, tasks_data, calendar_ref=self.calendar_ref, parent=self)
            dialog.exec_()
        else:
            super().mouseDoubleClickEvent(event)

    def add_task(self, task_widget):
        # If given a TaskBadge, attach day info and limit number displayed with an overflow indicator
        try:
            if isinstance(task_widget, QLabel) and getattr(task_widget, 'objectName', lambda: '')() == 'TaskBadge':
                # set day and calendar_ref if missing
                if not hasattr(task_widget, 'day'):
                    task_widget.day = self.day
                if not getattr(task_widget, 'calendar_ref', None):
                    task_widget.calendar_ref = self.calendar_ref
                # count existing badges
                badges = [self.tasks_layout.itemAt(i).widget() for i in range(self.tasks_layout.count()) if self.tasks_layout.itemAt(i).widget() is not None]
                badge_widgets = [b for b in badges if getattr(b, 'objectName', lambda: '')() == 'TaskBadge']
                if len(badge_widgets) < 3:
                    self.tasks_layout.addWidget(task_widget)
                else:
                    # find existing overflow label or create one
                    overflow = None
                    for b in badges:
                        if isinstance(b, QLabel) and b.property('is_overflow'):
                            overflow = b
                            break
                    if not overflow:
                        overflow = QLabel()
                        overflow.setProperty('is_overflow', True)
                        overflow.setStyleSheet('background:#ddd; color:#333; padding:4px 8px; border-radius:10px;')
                        self.tasks_layout.addWidget(overflow)
                    # update count
                    prev = int(overflow.text().lstrip('+')) if overflow.text() else 0
                    overflow.setText(f"+{prev+1}")
            else:
                # generic widget (TaskWidget or others)
                self.tasks_layout.addWidget(task_widget)
        except Exception:
            try:
                self.tasks_layout.addWidget(task_widget)
            except Exception:
                pass

    def clear_tasks(self):
        """Xóa tất cả widget công việc trong ô ngày trước khi thêm mới."""
        while self.tasks_layout.count():
            item = self.tasks_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def dragEnterEvent(self, event):
        if event.mimeData().property("task_widget_ref"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        source_widget = event.mimeData().property("task_widget_ref")
        if source_widget:
            task_text = source_widget.label.text()
            note_text = source_widget.note
            full_date = datetime(self.year, self.month, self.day)
            if self.calendar_ref:
                if getattr(self.calendar_ref, 'current_view_mode', 'personal') == 'group':
                    self.calendar_ref.add_group_task_to_db(full_date, task_text, None, note_text)
                else:
                    self.calendar_ref.add_task_to_db(full_date, task_text, note_text)
                event.setDropAction(Qt.CopyAction)
                event.accept()
            else:
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