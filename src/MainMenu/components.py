# File: MainMenu/components.py

import locale
from datetime import datetime
from PyQt5.QtWidgets import (QDialog, QFrame, QHBoxLayout, QCheckBox, QLabel, QVBoxLayout,
                             QApplication, QMenu, QInputDialog, QStyle, QPushButton,
                             QScrollArea, QWidget, QLineEdit, QDateTimeEdit, QTextEdit, QDialogButtonBox, QMessageBox,
                             QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QComboBox)
from PyQt5.QtCore import Qt, QMimeData, QDate, QDateTime, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QDrag, QCursor, QFont, QColor, QFontMetrics
from config import COLOR_WHITE, COLOR_BORDER, TEXT_MUTED, COLOR_PRIMARY, COLOR_TEXT_PRIMARY

# Thiết lập ngôn ngữ Tiếng Việt để hiển thị đúng Thứ trong tuần
try:
    locale.setlocale(locale.LC_TIME, 'vi_VN.UTF-8')
except locale.Error:
    import logging
    logging.debug("Locale vi_VN not supported, skipping.")

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

        # styling for a clean card-like look
        self.setStyleSheet(f"""
            QFrame#TaskDetailItem {{ background: {COLOR_WHITE}; border: 1px solid {COLOR_BORDER}; border-radius: 10px; padding: 10px; }}
            QLabel#StatusSmall {{ font-size: 12px; color: {TEXT_MUTED}; }}
            QLabel#NoteLabelInDialog {{ color: {COLOR_TEXT_PRIMARY}; }}
        """)

        # Outer horizontal layout: content on left, checkbox column on right
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(8, 8, 8, 8)

        # Left content (title, info, note, actions)
        content_layout = QVBoxLayout()
        content_layout.setSpacing(6)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Arial", 11, QFont.Bold))
        title_lbl.setWordWrap(True)
        content_layout.addWidget(title_lbl)

        # top info row: assignee, due and small status label
        info_row = QHBoxLayout()
        status_label = QLabel("Đã hoàn thành" if is_done else "Chưa hoàn thành")
        status_label.setObjectName('StatusSmall')
        status_label.setStyleSheet(f'color: {TEXT_MUTED};')
        info_row.addWidget(status_label)
        if assignee:
            assignee_label = QLabel(f"👤 {assignee}")
            assignee_label.setStyleSheet(f'color: {COLOR_PRIMARY}; margin-left:8px;')
            info_row.addWidget(assignee_label)
        if due_at:
            due_label = QLabel(f"⏰ {due_at}")
            due_label.setStyleSheet(f'color: {TEXT_MUTED}; margin-left:8px;')
            info_row.addWidget(due_label)
        info_row.addStretch()
        content_layout.addLayout(info_row)

        if note_text:
            note_label = QLabel(f"<b>Ghi chú:</b> {note_text}")
            note_label.setWordWrap(True)
            note_label.setObjectName("NoteLabelInDialog")
            content_layout.addWidget(note_label)

        # actions row (delete only)
        actions_row = QHBoxLayout()
        actions_row.addStretch()
        delete_btn = QPushButton("Xóa")
        def do_delete():
            try:
                if self.calendar_ref and task_id is not None:
                    success = self.calendar_ref.delete_task(task_id, is_group=is_group)
                    if not success:
                        # if deletion failed, show a message and do not close
                        QMessageBox.warning(self, 'Lỗi', 'Không thể xóa nhiệm vụ (không có quyền hoặc lỗi).')
                    else:
                        # close parent dialog or remove widget as appropriate
                        try:
                            # if this widget is inside a dialog, close dialog
                            dlg = self.window()
                            if isinstance(dlg, QDialog):
                                dlg.accept()
                        except Exception:
                            pass
            except Exception:
                pass
        delete_btn.clicked.connect(do_delete)
        actions_row.addWidget(delete_btn)
        content_layout.addLayout(actions_row)

        outer_layout.addLayout(content_layout)

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


class ElidedLabel(QLabel):
    """QLabel that elides long text with '...' and updates on resize.

    Usage: l = ElidedLabel('A very long title'); l.setToolTip(full_text)
    """
    def __init__(self, text='', parent=None):
        super().__init__(parent)
        self._full_text = str(text or '')
        self.setText(self._full_text)

    def setText(self, text):
        # store full text and update display
        try:
            self._full_text = str(text or '')
        except Exception:
            self._full_text = ''
        super().setText(self._full_text)
        self._update_elided()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elided()

    def _update_elided(self):
        try:
            fm = QFontMetrics(self.font())
            # subtract padding allowance
            avail = max(8, self.width() - 24)
            elided = fm.elidedText(self._full_text, Qt.ElideRight, avail)
            super().setText(elided)
            # always show full text on tooltip
            if self._full_text:
                self.setToolTip(self._full_text)
        except Exception:
            pass

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


class TaskBadge(QFrame):
    """Compact task badge shown in calendar tile with an interactive checkbox on the right.

    Provides: title label, optional tooltip (note), and a checkbox that toggles completion
    with permission checks via calendar_ref.
    """
    def __init__(self, title, color='#66bb6a', note='', assignee_name=None, parent=None, task_id=None, is_group=False, calendar_ref=None):
        super().__init__(parent)
        self.setObjectName('TaskBadge')
        self.task_id = task_id
        self.is_group = is_group
        self.calendar_ref = calendar_ref
        self.note = note
        self.assignee_name = assignee_name
        self.title = title or ''

        self.setContentsMargins(0, 0, 0, 0)
        # make badges compact and cap width so long titles don't expand the calendar
        self.setFixedHeight(36)
        self.setMinimumHeight(36)
        # tighter max width to avoid extreme expansion from very long titles
        BADGE_MAX_W = 240
        self.setMaximumWidth(BADGE_MAX_W)
            

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 6, 2)
        layout.setSpacing(8)

        # optional left indicator: group icon or assignee initial
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setStyleSheet('border-radius:8px;')
        # default empty, will be set below when is_group / assignee present
        layout.addWidget(self.icon_label, 0, Qt.AlignVCenter)

        self.label = ElidedLabel(self.title)
        self.label.setStyleSheet('color: white; font-size: 13px; font-weight:600;')
        self.label.setWordWrap(False)
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        try:
            # ensure the label doesn't request excessive width
            self.label.setMaximumWidth(BADGE_MAX_W - 40)
        except Exception:
            pass
        # allow widget to shrink text with elide if too long in layout (handled by QLabel width)
        layout.addWidget(self.label, 1)

        # interactive check control on the right — use a small checkable QPushButton
        # We keep the attribute name `checkbox` for backward compatibility so other code can call
        # .setChecked/.isChecked and we connect to toggled events.
        from PyQt5.QtWidgets import QPushButton
        self.checkbox = QPushButton('')
        self.checkbox.setCheckable(True)
        # larger clickable area for touch and visibility
        self.checkbox.setFixedSize(24, 24)
        # show a visible check mark when checked; no text when unchecked
        self.checkbox.setStyleSheet(
            'QPushButton { background: rgba(255,255,255,0.12); border-radius: 6px; border: none; color: white; font-weight: bold; }'
            'QPushButton:checked { background: white; color: #2b2b2b; }'
        )
        layout.addWidget(self.checkbox, 0, Qt.AlignRight)

        # visual style
        base_style = f'background: {color}; border-radius: 12px; padding: 4px;'
        self.setStyleSheet(base_style)
        # if group task, show a subtle left marker and slightly different tint
        try:
            if self.is_group:
                # small white circle with group emoji (keeps compact)
                self.icon_label.setText('👥')
                self.icon_label.setStyleSheet('font-size:11px; color: white; background: rgba(0,0,0,0.12); border-radius:8px;')
            else:
                # hide icon area by setting transparent background
                self.icon_label.setText('')
                self.icon_label.setStyleSheet('background: transparent;')
        except Exception:
            pass
        # add drop shadow for depth
        try:
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(12)
            shadow.setOffset(0, 4)
            shadow.setColor(QColor(0, 0, 0, 80))
            self.setGraphicsEffect(shadow)
        except Exception:
            pass
        # add opacity effect and an animation to highlight changes
        try:
            opacity = QGraphicsOpacityEffect(self)
            opacity.setOpacity(1.0)
            self._opacity_effect = opacity
            self.setGraphicsEffect(opacity)
            self._anim = QPropertyAnimation(opacity, b"opacity")
            self._anim.setDuration(220)
            self._anim.setEasingCurve(QEasingCurve.InOutQuad)
        except Exception:
            self._anim = None
        # tooltip is handled by ElidedLabel for title; keep separate tooltip for note
        try:
            if note:
                self.setToolTip(note)
        except Exception:
            pass

        # connect toggled to our handler; handler will accept bool or int
        self.checkbox.toggled.connect(self._on_checkbox_changed)

        # interaction state for dragging
        self.drag_start_position = None

    def text(self):
        return self.title

    def mousePressEvent(self, event):
        try:
            # register drag start position on left click; do NOT open detail on single click
            if event.button() == Qt.LeftButton:
                self.drag_start_position = event.pos()
        except Exception:
            pass

    def mouseDoubleClickEvent(self, event):
        # double-clicking a TaskBadge opens a single-task detail dialog
        try:
            if event.button() == Qt.LeftButton and self.calendar_ref:
                try:
                    # build a small dialog containing TaskDetailItemWidget for this task
                    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
                    dlg = QDialog(self)
                    dlg.setWindowTitle('Chi tiết công việc')
                    dlg.setMinimumWidth(420)
                    data = {
                        'title': self.title,
                        'is_done': bool(self.checkbox.isChecked()),
                        'note': self.note,
                        'assignee_name': self.assignee_name,
                        'due_at': None,
                        'task_id': self.task_id,
                        'is_group': self.is_group
                    }
                    content = TaskDetailItemWidget(data, calendar_ref=self.calendar_ref)
                    layout = QVBoxLayout(dlg)
                    layout.addWidget(content)
                    buttons = QDialogButtonBox(QDialogButtonBox.Close)
                    buttons.rejected.connect(dlg.reject)
                    layout.addWidget(buttons)
                    dlg.exec_()
                    return
                except Exception:
                    pass
            super().mouseDoubleClickEvent(event)
        except Exception:
            try:
                super().mouseDoubleClickEvent(event)
            except Exception:
                pass

    def enterEvent(self, event):
        # subtle brighten on hover
        try:
            self.setStyleSheet(self.styleSheet() + 'border: 1px solid rgba(255,255,255,0.18); transform: scale(1.01);')
        except Exception:
            pass

    def leaveEvent(self, event):
        try:
            # revert to base by resetting to original background color (approx)
            # keep the background color part of stylesheet unchanged; simple reset
            self.setStyleSheet(self.styleSheet().replace('border: 1px solid rgba(255,255,255,0.18); transform: scale(1.01);', ''))
        except Exception:
            pass

    def mouseMoveEvent(self, event):
        # Dragging disabled: do nothing to prevent creating drag actions
        return

    def mouseReleaseEvent(self, event):
        """Clear drag start position on mouse release to avoid stale state."""
        try:
            self.drag_start_position = None
        except Exception:
            pass

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        delete_action = context_menu.addAction('Xóa công việc này')
        action = context_menu.exec_(self.mapToGlobal(event.pos()))
        if action == delete_action:
            try:
                if self.task_id and self.calendar_ref:
                    success = self.calendar_ref.delete_task(self.task_id, self.is_group)
                    if not success:
                        QMessageBox.warning(self, 'Lỗi', 'Không thể xóa nhiệm vụ (không có quyền hoặc lỗi).')
                    else:
                        self.deleteLater()
            except Exception:
                pass

    def _on_checkbox_changed(self, state):
        # state may be bool (QPushButton.toggled) or int (Qt.Checked from QCheckBox)
        if isinstance(state, bool):
            is_done = 1 if state else 0
        else:
            is_done = 1 if state == Qt.Checked else 0
        # Optimistic UI: update visuals immediately, then persist; revert on failure
        try:
            if not self.task_id or not self.calendar_ref:
                return

            # permission check first
            try:
                allowed, msg = self.calendar_ref.can_toggle_task(self.task_id, self.is_group)
            except Exception:
                allowed, msg = False, 'Lỗi kiểm tra quyền.'
            if not allowed:
                # revert immediately
                self.checkbox.blockSignals(True)
                # set checked state back
                self.checkbox.setChecked(not bool(is_done))
                # update visible tick for QPushButton
                try:
                    self.checkbox.setText('✓' if self.checkbox.isChecked() else '')
                except Exception:
                    pass
                self.checkbox.blockSignals(False)
                QMessageBox.warning(self, 'Không có quyền', msg)
                return

            # optimistic style
            # show tick mark on the QPushButton if used
            try:
                self.checkbox.setText('✓' if bool(is_done) else '')
            except Exception:
                pass
            if is_done:
                self.setStyleSheet('background: #bdbdbd; border-radius: 12px; padding: 4px; color: #fff;')
                self.label.setStyleSheet('color: #fff; text-decoration: line-through; font-size:11px;')
            else:
                self.setStyleSheet('background: #66bb6a; border-radius: 12px; padding: 4px;')
                self.label.setStyleSheet('color: #fff; font-size:11px;')

            # persist change via calendar API which now returns boolean success
            try:
                success = self.calendar_ref.update_task_status(self.task_id, is_done, self.is_group)
            except Exception:
                success = False

            if not success:
                # revert visuals and checkbox
                self.checkbox.blockSignals(True)
                self.checkbox.setChecked(not bool(is_done))
                try:
                    self.checkbox.setText('✓' if self.checkbox.isChecked() else '')
                except Exception:
                    pass
                self.checkbox.blockSignals(False)
                # revert styles
                if not is_done:
                    self.setStyleSheet('background: #bdbdbd; border-radius: 12px; padding: 4px;')
                    self.label.setStyleSheet('color:#fff; text-decoration: line-through; font-size:11px;')
                else:
                    self.setStyleSheet('background: #66bb6a; border-radius: 12px; padding: 4px;')
                    self.label.setStyleSheet('color:#fff; font-size:11px;')
                QMessageBox.warning(self, 'Lỗi', 'Không thể cập nhật trạng thái lên server.')
            else:
                # animate a subtle highlight to show success
                try:
                    if self._anim:
                        self._anim.stop()
                        self._anim.setStartValue(0.6)
                        self._anim.setEndValue(1.0)
                        self._anim.start()
                except Exception:
                    pass
                # refresh only this day to avoid full calendar redraw
                try:
                    if hasattr(self, 'day') and self.calendar_ref:
                        self.calendar_ref.refresh_day(self.day)
                except Exception:
                    pass
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
    def __init__(self, parent=None, default_date: datetime = None, members: list = None):
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
        self.title_input.setFixedHeight(40)
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.title_input)

        # Date & time
        date_label = QLabel("Ngày giờ hoàn thành")
        date_label.setStyleSheet("color: #2e7d32; font-weight:600;")
        self.date_edit = QDateTimeEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat('yyyy-MM-dd HH:mm:ss')
        self.date_edit.setFixedHeight(40)
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

        # Assignee selection: only show when members are provided.
        # members should already be ordered with leader first by the caller.
        if members:
            assignee_label = QLabel("Phân công")
            assignee_label.setStyleSheet("color: #2e7d32; font-weight:600;")
            self.assignee_combo = QComboBox()
            try:
                for mid, mname in members:
                    # add actual user_id as data
                    self.assignee_combo.addItem(mname, mid)
            except Exception:
                pass
            main_layout.addWidget(assignee_label)
            main_layout.addWidget(self.assignee_combo)
        else:
            self.assignee_combo = None

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

    def assignee(self):
        try:
            if not self.assignee_combo:
                return None
            return self.assignee_combo.currentData()
        except Exception:
            return None


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
        self.main_layout.setContentsMargins(2, 2, 2, 2)

        self.date_label = QLabel(date_text)
        self.date_label.setObjectName("DateLabel")
        self.date_label.setAlignment(Qt.AlignRight)
        self.date_label.setStyleSheet("background: transparent;")
        self.main_layout.addWidget(self.date_label)

        # Create a simple container for tasks (no scrolling) so we can display
        # a compact overflow indicator (+N) instead of letting the cell scroll.
        tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(tasks_container)
        self.tasks_layout.setAlignment(Qt.AlignTop)
        self.tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_layout.setSpacing(4)  # spacing between task widgets
        # make visible/height configurable on the instance (helps testing/user-specific cases)
        self.MAX_VISIBLE_BADGES = 3
        self.BADGE_HEIGHT = 36
        spacing = max(0, self.tasks_layout.spacing())
        visible_height = self.MAX_VISIBLE_BADGES * self.BADGE_HEIGHT + max(0, (self.MAX_VISIBLE_BADGES - 1)) * spacing + 6
        try:
            tasks_container.setFixedHeight(visible_height)
        except Exception:
            pass

        # keep a reference so add_task/others can access the container and adjust if needed
        self.tasks_container = tasks_container
        self.main_layout.addWidget(tasks_container)
            
    def _prompt_for_new_task(self):
        # KIỂM TRA QUYỀN TRƯỚC KHI LÀM BẤT CỨ ĐIỀU GÌ
        if self.calendar_ref and self.calendar_ref.current_view_mode == 'group':
            # Ensure we have the correct leader id; some flows may not have called
            # calendar_ref.set_group_context so current_group_leader_id can be None.
            try:
                leader_id = self.calendar_ref.current_group_leader_id
                if leader_id is None:
                    # try to resolve from the current group id
                    try:
                        grp = self.calendar_ref._get_current_group_id()
                        if grp:
                            leader_id = self.calendar_ref.db.get_group_leader(grp)
                            # cache it on calendar_ref for subsequent checks
                            try:
                                self.calendar_ref.current_group_leader_id = leader_id
                            except Exception:
                                pass
                    except Exception:
                        leader_id = None
                is_leader = (self.calendar_ref.user_id == leader_id)
            except Exception:
                is_leader = False

            # Nếu không phải là trưởng nhóm
            if not is_leader:
                QMessageBox.warning(self, "Không có quyền", "Chỉ trưởng nhóm mới có thể thêm công việc.")
                return # Dừng hàm tại đây, không cho thực hiện thêm

        # Sử dụng self.day để tạo ngày mặc định
        default_date = datetime(self.year, self.month, self.day)
        
        # SỬA LỖI 2: Truyền tham số bằng từ khóa (keyword arguments)
        # Prepare member list (for possible assignment) — keep safe in case DB call fails
        members = []
        try:
            if self.calendar_ref:
                members = self.calendar_ref._get_current_group_members() or []
        except Exception:
            members = []

        dialog = AddTaskDialog(parent=self, default_date=default_date, members=members)

        # Nếu người dùng nhấn "Thêm" và có nhập tiêu đề
        if dialog.exec_() == QDialog.Accepted and dialog.title():
            title = dialog.title()
            due_datetime_obj = dialog.due_datetime().toPyDateTime()
            note = dialog.note()
            try:
                assignee_id = dialog.assignee()
            except Exception:
                assignee_id = None

            if self.calendar_ref:
                # Dựa vào chế độ xem hiện tại để quyết định thêm việc cá nhân hay nhóm
                if self.calendar_ref.current_view_mode == 'group':
                    # pass assignee_id (may be None or empty) to add_group_task_to_db
                    self.calendar_ref.add_group_task_to_db(due_datetime_obj, title, assignee_id=assignee_id if assignee_id else None, note_text=note)
                else:
                    self.calendar_ref.add_task_to_db(due_datetime_obj, title, note_text=note)

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
            # detect TaskBadge by objectName to support both old QLabel badges and new QFrame-based badges
            is_badge = getattr(task_widget, 'objectName', lambda: '')() == 'TaskBadge'
            if is_badge:
                # set day and calendar_ref if missing
                if not hasattr(task_widget, 'day'):
                    task_widget.day = self.day
                if not getattr(task_widget, 'calendar_ref', None):
                    task_widget.calendar_ref = self.calendar_ref
                # ensure badge checkbox reflects current state (if attribute exists)
                try:
                    if hasattr(task_widget, 'checkbox'):
                        # leave checked state as-is if already set, otherwise default to unchecked
                        if not hasattr(task_widget.checkbox, 'isChecked'):
                            pass
                except Exception:
                    pass
                # count existing badges
                badges = [self.tasks_layout.itemAt(i).widget() for i in range(self.tasks_layout.count()) if self.tasks_layout.itemAt(i).widget() is not None]
                badge_widgets = [b for b in badges if getattr(b, 'objectName', lambda: '')() == 'TaskBadge']
                if len(badge_widgets) < 3:
                    self.tasks_layout.addWidget(task_widget)
                else:
                    # find existing overflow label or create one
                    overflow = None
                    for b in badges:
                        try:
                            if b.property('is_overflow'):
                                overflow = b
                                break
                        except Exception:
                            continue
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
        # Drag-and-drop disabled: do not accept any external drag events
        return

    def dropEvent(self, event):
        # Drag-and-drop disabled: ignore drops
        return

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        add_task_action = context_menu.addAction("Thêm công việc mới")
        action = context_menu.exec_(self.mapToGlobal(event.pos()))
        if action == add_task_action:
            self._prompt_for_new_task()

    