# File: MainMenu/components.py

import locale
import os
from datetime import datetime
from PyQt5.QtWidgets import (QDialog, QFrame, QHBoxLayout, QCheckBox, QLabel, QVBoxLayout,
                            QMenu, QStyle, QPushButton,
                             QScrollArea, QWidget, QLineEdit, QDateTimeEdit, QTextEdit, QDialogButtonBox, QMessageBox,
                             QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QComboBox, QAction, QCalendarWidget, QTimeEdit)
from PyQt5.QtCore import Qt, QDateTime, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QCursor, QFont, QColor, QFontMetrics, QIcon
from MainMenu.avatar_utils import load_avatar_pixmap, load_avatar_for_task
from config import TEXT_MUTED,  COLOR_TEXT_PRIMARY, ACCENT_GROUP, ACCENT_PERSONAL, FONT_UI, PRIORITY_COLORS, ICON_DIR, COLOR_SUCCESS, COLOR_PRIMARY_BLUE

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
        """Modern IT-style task detail card.

        Displays title, status, assignee, due date, note and a delete action.
        """
        super().__init__(parent)
        self.setObjectName("TaskDetailItem")
        self.setFrameShape(QFrame.StyledPanel)
        self.calendar_ref = calendar_ref

        # normalize
        title = task_data.get('title') or ''
        is_done = bool(task_data.get('is_done', False))
        note_text = task_data.get('note') or ''
        assignee = task_data.get('assignee_name') or ''
        due_at = task_data.get('due_at') or ''
        task_id = task_data.get('task_id')
        is_group = bool(task_data.get('is_group', False))

        # try to fetch latest estimate/priority from DB when possible (only for personal tasks)
        priority_val = task_data.get('priority')
        estimate_minutes = task_data.get('estimate_minutes') or task_data.get('estimated_minutes') or task_data.get('estimate')
        try:
            # Only query personal tasks from tasks table. Group tasks have different storage and should not be queried here.
            if not is_group and (priority_val is None or estimate_minutes is None) and self.calendar_ref and hasattr(self.calendar_ref, 'db') and task_id:
                row = self.calendar_ref.db.get_task_by_id(task_id)
                # row now expected as (task_id, user_id, title, note, is_done, due_at, estimate_minutes, priority)
                if row:
                    # defensive mapping by length
                    try:
                        estimate_minutes = estimate_minutes or row[6]
                        priority_val = priority_val if priority_val is not None else row[7]
                    except Exception:
                        if len(row) >= 8:
                            estimate_minutes = estimate_minutes or row[6]
                            priority_val = priority_val if priority_val is not None else row[7]
        except Exception:
            pass

        accent = ACCENT_GROUP if is_group else ACCENT_PERSONAL

        # modern glassy card with subtle border
        self.setStyleSheet(f"""
            QFrame#TaskDetailItem {{ background: rgba(255,255,255,0.96); border: 1px solid rgba(20,30,40,0.04); border-radius: 12px; }}
            QLabel#TitleLabel {{ color: {COLOR_TEXT_PRIMARY}; font-weight:700; font-size:13px; }}
            QLabel#MetaLabel {{ color: {TEXT_MUTED}; font-size:11px; }}
            QLabel#NoteLabelInDialog {{ color: {TEXT_MUTED}; font-style: italic; }}
            QPushButton#DeleteIcon {{ background: transparent; border: 1px solid rgba(200,50,50,0.12); border-radius:18px; }}
            QPushButton#DeleteIcon:hover {{ background: rgba(231,76,60,0.12); }}
        """)

        # Outer layout: avatar | content | action
        outer = QHBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(12)

        # Avatar / accent block — use shared helper to load circular avatar pixmap
        avatar = QLabel()
        avatar.setFixedSize(44, 44)
        avatar.setAlignment(Qt.AlignCenter)
        avatar_text = (assignee[:1] or '').upper()
        avatar.setText(avatar_text)
        avatar.setStyleSheet(f'background: {accent}; color: white; border-radius: 10px; font-weight:700;')
        try:
            pix = None
            if is_group:
                # group: prefer assignee (via task_data or DB lookup)
                if self.calendar_ref and hasattr(self.calendar_ref, 'db'):
                    pix = load_avatar_for_task(task_data, db=self.calendar_ref.db, size=44)
                if not pix:
                    assignee_id = task_data.get('assignee_id')
                    if assignee_id:
                        pix = load_avatar_pixmap(assignee_id, size=44)
            else:
                # personal: try to load owner avatar if we have a task_id and DB
                try:
                    if task_id and self.calendar_ref and hasattr(self.calendar_ref, 'db'):
                        row = self.calendar_ref.db.get_task_by_id(task_id)
                        # row format from DB: (task_id, user_id, title, note, is_done, due_at)
                        if row and len(row) >= 2:
                            owner_id = row[1]
                            if owner_id:
                                pix = load_avatar_pixmap(owner_id, size=44)
                except Exception:
                    pass

            if pix:
                avatar.setPixmap(pix)
                avatar.setText('')
                avatar.setStyleSheet('background: transparent;')
        except Exception:
            pass
        outer.addWidget(avatar, 0, Qt.AlignVCenter)

        # Content column
        col = QVBoxLayout()
        col.setSpacing(6)

        title_lbl = QLabel(title)
        title_lbl.setObjectName('TitleLabel')
        title_lbl.setWordWrap(True)
        title_lbl.setFont(QFont(FONT_UI, 12, QFont.Bold))
        col.addWidget(title_lbl)

        # metadata row: status pill, due, assignee
        meta_row = QHBoxLayout()
        # status pill
        status_lbl = QLabel('Hoàn' if is_done else 'Chưa')
        status_lbl.setObjectName('MetaLabel')
        status_lbl.setAlignment(Qt.AlignCenter)
        # Use a soft gray-white background for the pill; text color indicates state/area
        gray_bg = '#f5f5f5'
        if is_done:
            # completed: use success color for the text
            status_lbl.setStyleSheet(f'background:{gray_bg}; color:{COLOR_SUCCESS}; padding:4px 8px; border-radius:10px; font-size:11px;')
        else:
            # incomplete: personal -> success (green), group -> primary blue
            text_col = COLOR_PRIMARY_BLUE if is_group else COLOR_SUCCESS
            status_lbl.setStyleSheet(f'background:{gray_bg}; color:{text_col}; padding:4px 8px; border-radius:10px; font-size:11px;')
        meta_row.addWidget(status_lbl)

        # priority pill (if available) - show only for personal tasks
        if not is_group:
            try:
                p = int(priority_val) if priority_val is not None else None
            except Exception:
                p = None
            if p is not None:
                color = PRIORITY_COLORS.get(p, '#808080')
                pr_lbl = QLabel(f'! P{p}')
                pr_lbl.setObjectName('MetaLabel')
                pr_lbl.setAlignment(Qt.AlignCenter)
                pr_lbl.setStyleSheet(f'background:{color}; color:#fff; padding:4px 8px; border-radius:10px; font-size:11px; margin-left:8px;')
                meta_row.addWidget(pr_lbl)

            # estimated time (minutes)
            if estimate_minutes is not None:
                try:
                    em = int(estimate_minutes)
                    # display in human friendly form
                    if em <= 0:
                        est_text = '0m'
                    elif em < 60:
                        est_text = f'{em}m'
                    else:
                        hrs = em // 60
                        mins = em % 60
                        est_text = f'{hrs}h{mins:02d}m' if mins else f'{hrs}h'
                    est_lbl = QLabel(f'⏱ {est_text}')
                    est_lbl.setObjectName('MetaLabel')
                    est_lbl.setStyleSheet(f'color: {TEXT_MUTED}; margin-left:8px;')
                    meta_row.addWidget(est_lbl)
                except Exception:
                    pass

        # due date
        if due_at:
            due_lbl = QLabel(f'⏰ {due_at}')
            due_lbl.setObjectName('MetaLabel')
            due_lbl.setStyleSheet(f'color: {TEXT_MUTED}; margin-left:8px;')
            meta_row.addWidget(due_lbl)

        # assignee
        if assignee:
            who_lbl = QLabel(f'👤 {assignee}')
            who_lbl.setObjectName('MetaLabel')
            who_lbl.setStyleSheet(f'color: {TEXT_MUTED}; margin-left:8px;')
            meta_row.addWidget(who_lbl)

        meta_row.addStretch()
        col.addLayout(meta_row)

        # note (muted)
        if note_text:
            note_lbl = QLabel(note_text)
            note_lbl.setObjectName('NoteLabelInDialog')
            note_lbl.setWordWrap(True)
            note_lbl.setStyleSheet(f'color: {TEXT_MUTED};')
            col.addWidget(note_lbl)

        outer.addLayout(col)

        # actions column (delete icon)
        action_col = QVBoxLayout()
        action_col.setAlignment(Qt.AlignTop)
        delete_btn = QPushButton()
        delete_btn.setObjectName('DeleteIcon')
        try:
            icon = self.style().standardIcon(QStyle.SP_TrashIcon)
            delete_btn.setIcon(icon)
        except Exception:
            delete_btn.setText('X')
        delete_btn.setFixedSize(36, 36)
        delete_btn.setCursor(QCursor(Qt.PointingHandCursor))
        action_col.addWidget(delete_btn)
        outer.addLayout(action_col)

        # delete handler with confirmation
        def do_delete():
            try:
                if not (self.calendar_ref and task_id is not None):
                    return
                ans = QMessageBox.question(self, 'Xác nhận', 'Bạn có chắc muốn xóa công việc này?', QMessageBox.Yes | QMessageBox.No)
                if ans != QMessageBox.Yes:
                    return
                try:
                    self.calendar_ref.delete_task(task_id, is_group=is_group)
                except Exception:
                    pass
                try:
                    self.deleteLater()
                except Exception:
                    pass
            except Exception:
                pass

        delete_btn.clicked.connect(do_delete)

    def enterEvent(self, event):
        try:
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(14)
            shadow.setOffset(0, 6)
            shadow.setColor(QColor(0, 0, 0, 60))
            self.setGraphicsEffect(shadow)
        except Exception:
            pass
        try:
            super().enterEvent(event)
        except Exception:
            pass

    def leaveEvent(self, event):
        try:
            self.setGraphicsEffect(None)
        except Exception:
            pass
        try:
            super().leaveEvent(event)
        except Exception:
            pass

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


        # build dialog layout with a modern header
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        day_name = VIETNAMESE_DAYS[full_date.weekday()]
        month_name = VIETNAMESE_MONTHS[full_date.month - 1]
        date_str = f"{day_name}, ngày {full_date.day} {month_name} năm {full_date.year}"

        header = QHBoxLayout()
        title = QLabel(date_str)
        title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight:700; font-size:15px;")
        header.addWidget(title)
        # task count badge
        try:
            cnt = len(tasks_data) if tasks_data else 0
        except Exception:
            cnt = 0
        count_badge = QLabel(f"{cnt} nhiệm vụ")
        count_badge.setStyleSheet('background:#eef3ff; color:#234; padding:6px 10px; border-radius:12px; font-size:12px;')
        header.addWidget(count_badge)
        header.addStretch()
        # close icon
        close_btn = QPushButton()
        try:
            close_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        except Exception:
            close_btn.setText('Đóng')
        close_btn.setFixedSize(34, 34)
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.clicked.connect(self.accept)
        header.addWidget(close_btn)
        main_layout.addLayout(header)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        tasks_layout = QVBoxLayout(scroll_content)
        tasks_layout.setAlignment(Qt.AlignTop)
        tasks_layout.setSpacing(12)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        if tasks_data:
            for tdata in tasks_data:
                detail_item = TaskDetailItemWidget(tdata, calendar_ref=self.calendar_ref)
                # add a subtle drop shadow to each card for depth
                try:
                    shadow = QGraphicsDropShadowEffect(detail_item)
                    shadow.setBlurRadius(8)
                    shadow.setOffset(0, 4)
                    shadow.setColor(QColor(0, 0, 0, 60))
                    detail_item.setGraphicsEffect(shadow)
                except Exception:
                    pass
                tasks_layout.addWidget(detail_item)
        else:
            empty_lbl = QLabel("Không có công việc nào trong ngày này.")
            empty_lbl.setStyleSheet(f"color: {TEXT_MUTED}; padding: 12px;")
            tasks_layout.addWidget(empty_lbl)


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
    def __init__(self, title, color='#66bb6a', note='', assignee_name=None, parent=None, task_id=None, is_group=False, calendar_ref=None, due_at=None):
        super().__init__(parent)
        self.setObjectName('TaskBadge')
        self.task_id = task_id
        self.is_group = is_group
        self.calendar_ref = calendar_ref
        self.note = note
        self.assignee_name = assignee_name
        self.title = title or ''
        self.due_at = due_at

        self.setContentsMargins(0, 0, 0, 0)
        # make badges compact and cap width so long titles don't expand the calendar
        self.setFixedHeight(34)
        self.setMinimumHeight(34)
        # chỉnh sửa chiều rộng tối đa để phù hợp với thiết kế
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
                        'assignee_id': getattr(self, 'assignee_id', None),
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

            # Check if task is in the past and prevent toggling
            try:
                if hasattr(self, 'due_at') and self.due_at:
                    from datetime import datetime
                    due_date = datetime.strptime(self.due_at, '%Y-%m-%d %H:%M:%S')
                    if due_date < datetime.now():
                        QMessageBox.warning(self, "Không thể thay đổi", "Không thể thay đổi trạng thái công việc đã quá hạn.")
                        # revert immediately
                        self.checkbox.blockSignals(True)
                        self.checkbox.setChecked(not bool(is_done))
                        try:
                            self.checkbox.setText('✓' if self.checkbox.isChecked() else '')
                        except Exception:
                            pass
                        self.checkbox.blockSignals(False)
                        return
            except Exception:
                pass

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
# LỚP 5: DayWidget 
# ==============================================================================
class AddTaskDialog(QDialog):
    def __init__(self, parent=None, default_date: datetime = None, members: list = None, mode: str = 'personal'):
        super().__init__(parent)
        self.setWindowTitle("✨ Thêm công việc mới")
        self.setMinimumWidth(420)
        self.setObjectName("AddTaskDialog")

        self.mode = mode or 'personal'
        if self.mode == 'group':
            self.setStyleSheet("""
                #AddTaskDialog { background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #e8f2ff, stop:1 #eaf6ff); border-radius: 12px; }
                QLabel#HeaderLabel { font-size:16px; font-weight:700; color:#0d47a1; }
                QLineEdit, QTextEdit, QDateTimeEdit { background: white; border: 1px solid #d0e6ff; border-radius: 8px; padding: 8px; }
                QLineEdit:focus, QTextEdit:focus, QDateTimeEdit:focus { border: 1px solid #42a5f5; }
                QPushButton#OkButton { background-color: #1976d2; color: white; border-radius: 8px; padding: 8px 14px; }
                QPushButton#CancelButton { background-color: transparent; color: #0d47a1; border: 1px solid #d0e6ff; border-radius: 8px; padding: 6px 12px; }
            """)
        else:
            # green themed dialog for personal tasks (default)
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
        # Header shows distinct emoji and text for modes to avoid confusion
        header_text = "🪴 Thêm công việc" if self.mode == 'personal' else "👥 Thêm công việc nhóm"
        header = QLabel(header_text)
        header.setObjectName("HeaderLabel")
        main_layout.addWidget(header)

        # Title
        title_label = QLabel("Tiêu đề")
        # label color adapts to mode
        title_color = '#2e7d32' if self.mode == 'personal' else '#0d47a1'
        title_label.setStyleSheet(f"color: {title_color}; font-weight:600;")
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Nhập tiêu đề công việc...")
        self.title_input.setFixedHeight(40)
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.title_input)

        # Date & time
        date_label = QLabel("Ngày giờ hoàn thành")
        date_label.setStyleSheet(f"color: {title_color}; font-weight:600;")
        # Date & time widgets: keep date picker and add explicit time selector to the right
        self.date_edit = QDateTimeEdit()
        self.date_edit.setCalendarPopup(True)
        # date_edit will handle date; time is handled by time_edit next to it
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        self.date_edit.setFixedHeight(40)

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat('HH:mm:ss')
        self.time_edit.setFixedHeight(40)
        self.time_edit.setFixedWidth(120)

        # initialize values from default_date if provided
        if default_date:
            dt = QDateTime(default_date.year, default_date.month, default_date.day,
                           default_date.hour if hasattr(default_date, 'hour') else 0,
                           default_date.minute if hasattr(default_date, 'minute') else 0,
                           default_date.second if hasattr(default_date, 'second') else 0)
            self.date_edit.setDateTime(dt)
            self.time_edit.setTime(dt.time())
        else:
            now = QDateTime.currentDateTime()
            self.date_edit.setDateTime(now)
            self.time_edit.setTime(now.time())

        # place them in a single row so the calendar popup is on the left and time on the right
        date_time_row = QHBoxLayout()
        date_time_row.setSpacing(8)
        date_time_row.addWidget(self.date_edit)
        date_time_row.addWidget(self.time_edit)
        main_layout.addWidget(date_label)
        main_layout.addLayout(date_time_row)

        # Improve calendar popup styling so it's readable on dark themes
        try:
            cal = QCalendarWidget()
            cal.setFirstDayOfWeek(Qt.Monday)
            cal.setGridVisible(True)
            # Basic style: white background, dark text, highlighted selection
            cal.setStyleSheet('''
                QCalendarWidget { background: #ffffff; color: #222222; }
                QCalendarWidget QToolButton { background: #f0f0f0; border: none; }
                QCalendarWidget QAbstractItemView:enabled { background: white; selection-background-color: #1976d2; selection-color: white; }
                QCalendarWidget QAbstractItemView { color: #222222; }
                QCalendarWidget QWidget#qt_calendar_navigationbar { background: #f0f0f0; }
            ''')
            self.date_edit.setCalendarWidget(cal)
        except Exception:
            pass

        # Note
        note_label = QLabel("Ghi chú (tùy chọn)")
        note_label.setStyleSheet(f"color: {title_color}; font-weight:600;")
        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Một vài ghi chú ngắn...")
        self.note_edit.setFixedHeight(90)
        main_layout.addWidget(note_label)
        main_layout.addWidget(self.note_edit)

        # Estimated time in minutes and Priority
        # These are only shown for personal tasks. Group tasks should not expose estimate/priority.
        if self.mode != 'group':
            estimated_label = QLabel("Thời gian ước lượng (phút)")
            estimated_label.setStyleSheet(f"color: {title_color}; font-weight:600;")
            self.estimated_input = QLineEdit()
            self.estimated_input.setPlaceholderText("Nhập số phút ước lượng...")
            self.estimated_input.setFixedHeight(40)
            main_layout.addWidget(estimated_label)
            main_layout.addWidget(self.estimated_input)

            # Priority
            priority_label = QLabel("Độ ưu tiên")
            priority_label.setStyleSheet(f"color: {title_color}; font-weight:600;")
            self.priority_button = QPushButton()
            self.priority_button.setToolTip("Chọn độ ưu tiên")
            self.priority_button.setFixedHeight(40)
            self.current_priority = 4  # Default priority
            self._set_priority(4)  # Set default icon
            self.priority_button.clicked.connect(self._show_priority_menu)
            main_layout.addWidget(priority_label)
            main_layout.addWidget(self.priority_button)
        else:
            # ensure attributes exist so other callers can safely read them
            self.estimated_input = None
            self.priority_button = None
            self.current_priority = 4

        # Assignee selection: only show when members are provided.
        # members should already be ordered with leader first by the caller.
        if members:
            assignee_label = QLabel("Phân công")
            assignee_label.setStyleSheet(f"color: {title_color}; font-weight:600;")
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
        try:
            # combine date from date_edit and time from time_edit into one QDateTime
            d = self.date_edit.date()
            t = self.time_edit.time()
            combined = QDateTime(d, t)
            return combined
        except Exception:
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

    def estimated_minutes(self) -> int:
        try:
            if not self.estimated_input:
                return None
            estimated = self.estimated_input.text().strip()
            return int(estimated) if estimated.isdigit() else None
        except Exception:
            return None

    def priority(self) -> int:
        try:
            return int(self.current_priority)
        except Exception:
            return 4

    def _show_priority_menu(self):
        menu = QMenu(self)
        # Use existing icon files in assets/icons; map priorities to available flags
        icon_map = {1: 'flag-red.svg', 2: 'flag-green.svg', 3: 'flag-blue.svg', 4: 'flag-grey.svg'}
        for p_val in [1, 2, 3, 4]:
            icon_path = os.path.join(ICON_DIR, icon_map.get(p_val, 'flag-grey.svg'))
            action = QAction(QIcon(icon_path), f"Ưu tiên {p_val}", self) if os.path.exists(icon_path) else QAction(f"Ưu tiên {p_val}", self)
            action.triggered.connect(lambda chk, prio=p_val: self._set_priority(prio))
            menu.addAction(action)
        menu.exec_(self.priority_button.mapToGlobal(self.priority_button.rect().bottomLeft()))

    def _set_priority(self, priority):
        self.current_priority = priority
        # Keep mapping consistent with _show_priority_menu
        icon_map = {1: 'flag-red.svg', 2: 'flag-green.svg', 3: 'flag-blue.svg', 4: 'flag-grey.svg'}
        icon_path = os.path.join(ICON_DIR, icon_map.get(priority, 'flag-grey.svg'))
        if os.path.exists(icon_path):
            self.priority_button.setIcon(QIcon(icon_path))
        self.priority_button.setText(f"P{priority}")


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
        self.is_today = False

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignTop)
        self.main_layout.setContentsMargins(2, 2, 2, 2)

        self.date_label = QLabel(date_text)
        self.date_label.setObjectName("DateLabel")
        self.date_label.setAlignment(Qt.AlignRight)
        self.date_label.setStyleSheet("background: transparent;")
        self.date_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.main_layout.addWidget(self.date_label)

        # Create a simple container for tasks (no scrolling) so we can display
        # a compact overflow indicator (+N) instead of letting the cell scroll.
        tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(tasks_container)
        self.tasks_layout.setAlignment(Qt.AlignTop)
        self.tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_layout.setSpacing(4)  # spacing between task widgets
        # chiều cao tối đa để hiển thị 3 badges với khoảng cách
        self.MAX_VISIBLE_BADGES = 2
        self.BADGE_HEIGHT = 30
        spacing = max(0, self.tasks_layout.spacing())
        visible_height = self.MAX_VISIBLE_BADGES * self.BADGE_HEIGHT + max(0, (self.MAX_VISIBLE_BADGES - 1)) * spacing + 6
        try:
            tasks_container.setFixedHeight(visible_height)
        except Exception:
            pass

        # keep a reference so add_task/others can access the container and adjust if needed
        self.tasks_container = tasks_container
        self.main_layout.addWidget(tasks_container)
        # overflow footer (separate from the tasks layout) so +N is never clipped
        try:
            self._total_tasks = 0
            self.overflow_footer = QPushButton()
            self.overflow_footer.setObjectName('OverflowFooter')
            self.overflow_footer.setProperty('is_overflow_footer', True)
            self.overflow_footer.setVisible(False)
            self.overflow_footer.setFixedHeight(self.BADGE_HEIGHT)
            self.overflow_footer.setCursor(QCursor(Qt.PointingHandCursor))
            self.overflow_footer.setFlat(True)
            self.overflow_footer.setStyleSheet('background: #f5f5f5; color: #444; border-radius:8px; padding:6px;')
            try:
                self.overflow_footer.clicked.connect(self.open_all_tasks_dialog)
            except Exception:
                pass
            self.main_layout.addWidget(self.overflow_footer)
        except Exception:
            # if QPushButton is unavailable for some reason, skip footer
            self.overflow_footer = None
        # keep full list of tasks (both visible and hidden) so dialog can list all
        self._all_task_widgets = []
            
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
        
        # Prepare member list (for possible assignment) — only for group mode
        members = []
        try:
            if self.calendar_ref and self.calendar_ref.current_view_mode == 'group':
                members = self.calendar_ref._get_current_group_members() or []
        except Exception:
            members = []

        # Pass mode so dialog can style itself separately for personal vs group
        mode = 'group' if (self.calendar_ref and self.calendar_ref.current_view_mode == 'group') else 'personal'
        dialog = AddTaskDialog(parent=self, default_date=default_date, members=members if mode == 'group' else None, mode=mode)

        # Nếu người dùng nhấn "Thêm" và có nhập tiêu đề
        if dialog.exec_() == QDialog.Accepted and dialog.title():
            title = dialog.title()
            due_datetime_obj = dialog.due_datetime().toPyDateTime()
            note = dialog.note()
            try:
                assignee_id = dialog.assignee()
            except Exception:
                assignee_id = None
            estimated_minutes = dialog.estimated_minutes()
            priority = dialog.priority()

            if self.calendar_ref:
                # Dựa vào chế độ xem hiện tại để quyết định thêm việc cá nhân hay nhóm
                if self.calendar_ref.current_view_mode == 'group':
                    # pass assignee_id (may be None or empty) to add_group_task_to_db
                    self.calendar_ref.add_group_task_to_db(due_datetime_obj, title, assignee_id=assignee_id if assignee_id else None, note_text=note)
                else:
                    self.calendar_ref.add_task_to_db(due_datetime_obj, title, note_text=note, estimated_minutes=estimated_minutes, priority=priority)

    def set_today_highlight(self, enabled=True):
        self.is_today = enabled
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
            self.open_all_tasks_dialog()
        else:
            super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        # single click on empty area or date label should also open day detail
        try:
            if event.button() == Qt.LeftButton:
                child_widget = self.childAt(event.pos())
                if child_widget is None or child_widget == self or child_widget == self.date_label:
                    self.open_all_tasks_dialog()
                    return
        except Exception:
            pass
        try:
            super().mousePressEvent(event)
        except Exception:
            pass

    def open_all_tasks_dialog(self):
        # build tasks_data for that day by scanning current tasks_layout
        tasks_data = []
        # use the full list so hidden tasks (overflow) are included
        for widget in getattr(self, '_all_task_widgets', []):
            try:
                if widget is None:
                    continue
                if hasattr(widget, 'task_id'):
                    tasks_data.append({
                        'title': widget.text() if hasattr(widget, 'text') else getattr(widget, 'label', lambda: '')(),
                        'is_done': getattr(widget, 'checkbox', None) and getattr(widget.checkbox, 'isChecked', lambda: False)(),
                        'note': getattr(widget, 'note', ''),
                        'assignee_name': getattr(widget, 'assignee_name', None) or None,
                        'assignee_id': getattr(widget, 'assignee_id', None),
                        'due_at': None,
                        'task_id': getattr(widget, 'task_id', None),
                        'is_group': getattr(widget, 'is_group', False)
                    })
            except Exception:
                continue
        full_date = datetime(self.year, self.month, self.day)
        dialog = DayDetailDialog(full_date, tasks_data, calendar_ref=self.calendar_ref, parent=self)
        # Lưu trạng thái ban đầu
        was_today = self.is_today
        # Tắt highlight ngày hôm nay khi mở dialog
        if self.is_today:
            self.set_today_highlight(False)
        dialog.exec_()
        # Bật lại highlight sau khi đóng dialog nếu ban đầu là today
        if was_today:
            self.set_today_highlight(True)

    def add_task(self, task_widget):
        # If given a TaskBadge, attach day info and limit number displayed with an overflow indicator
        try:
            # detect TaskBadge by objectName to support both old QLabel badges and new QFrame-based badges
            is_badge = getattr(task_widget, 'objectName', lambda: '')() == 'TaskBadge'
            if is_badge:
                # record in full list so open_all_tasks_dialog can include it
                try:
                    self._all_task_widgets.append(task_widget)
                except Exception:
                    self._all_task_widgets = [task_widget]
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
                # increment total tasks and decide whether to add visibly or update footer
                try:
                    self._total_tasks += 1
                except Exception:
                    self._total_tasks = 1
                # count visible badges currently in layout
                badges = [self.tasks_layout.itemAt(i).widget() for i in range(self.tasks_layout.count()) if self.tasks_layout.itemAt(i).widget() is not None]
                badge_widgets = [b for b in badges if getattr(b, 'objectName', lambda: '')() == 'TaskBadge']
                if len(badge_widgets) < self.MAX_VISIBLE_BADGES:
                    self.tasks_layout.addWidget(task_widget)
                else:
                    # show/update footer instead of putting overflow inside tasks_layout
                    try:
                        hidden = max(1, self._total_tasks - self.MAX_VISIBLE_BADGES)
                        if self.overflow_footer:
                            self.overflow_footer.setText(f"+{hidden}")
                            self.overflow_footer.setVisible(True)
                    except Exception:
                        pass
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
        # reset footer
        try:
            self._total_tasks = 0
            if getattr(self, 'overflow_footer', None):
                self.overflow_footer.setVisible(False)
                try:
                    self.overflow_footer.setText('')
                except Exception:
                    pass
        except Exception:
            pass

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

    