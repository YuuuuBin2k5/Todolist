# -*- coding: utf-8 -*-
import os
from datetime import datetime, timedelta
import time

from Managers.database_manager import Database

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QScrollArea, QFrame,
                             QGridLayout, QGroupBox, QComboBox, QMessageBox,
                             QDateTimeEdit, QGraphicsDropShadowEffect, QMenu, QAction, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QDateTime
from PyQt5.QtGui import QIcon, QColor

from config import (
    ICON_DIR, COLOR_BACKGROUND, COLOR_PRIMARY, 
    COLOR_SUCCESS, COLOR_DANGER, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_BORDER, COLOR_HOVER, 
    PRIORITY_COLORS, COLOR_WHITE
)

def _parse_iso_datetime_module(s: str):
    """Module-level ISO datetime parser usable by widgets in this file."""
    if not s:
        return None
    if isinstance(s, datetime):
        return s
    s = str(s)
    try:
        if s.endswith('Z'):
            return datetime.fromisoformat(s.replace('Z', '+00:00'))
        return datetime.fromisoformat(s)
    except Exception:
        pass
    try:
        s2 = s.replace('T', ' ').rstrip('Z')
        try:
            return datetime.strptime(s2, '%Y-%m-%d %H:%M:%S')
        except Exception:
            return datetime.strptime(s2, '%Y-%m-%d')
    except Exception:
        return None

class TaskItemWidget(QFrame):
    task_toggled = pyqtSignal(str)
    task_deleted = pyqtSignal(str)
    task_started = pyqtSignal(str)

    def __init__(self, task_data, meta_data, parent=None):
        super().__init__(parent)
        self.task_id = task_data['id']
        self.task_data = task_data
        self.meta_data = meta_data
        self.setupUI()
        self.apply_shadow()

    def setupUI(self):
        self.setObjectName("TaskItemWidget")
        is_done = self.task_data['is_done']
        
        self.setStyleSheet(f"""
            #TaskItemWidget {{
                background-color: {COLOR_WHITE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px; padding: 12px; margin: 4px 8px;
            }}
            #TaskItemWidget[done="true"] {{ background-color: #F8F9FA; }}
            QLabel {{ background-color: transparent; border: none; }}
        """)
        self.setProperty("done", is_done)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        
        content_layout = QVBoxLayout()
        title_label = QLabel(self.task_data['title'])
        title_font_style = f"font-size: 15px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};"
        if is_done:
            title_font_style = f"font-size: 15px; text-decoration: line-through; color: {COLOR_TEXT_SECONDARY};"
        title_label.setStyleSheet(title_font_style)
        content_layout.addWidget(title_label)

        # Hiện ghi chú nếu có
        note_text = self.task_data.get('note', '')
        if note_text:
            note_label = QLabel(note_text)
            note_label.setStyleSheet(f"font-size:12px; color: {COLOR_TEXT_SECONDARY}; padding-top:4px;")
            content_layout.addWidget(note_label)
        
        details_text = []
 
        priority = self.task_data.get('priority', 4)
        if priority < 4:
            priority_color = PRIORITY_COLORS.get(priority, COLOR_TEXT_SECONDARY)
            details_text.append(f"<b style='color:{priority_color};'>P{priority}</b>")

        assignee_name = self.task_data.get('assignee_name')
        if assignee_name:
            details_text.append(f"👤 {assignee_name}")

        if self.task_data['due_at']:
            try:
                due_date = _parse_iso_datetime_module(self.task_data['due_at'])
                if due_date:
                    details_text.append(f"📅 {due_date.strftime('%d/%m %H:%M')}")
                else:
                    details_text.append(f"📅 {self.task_data['due_at']}")
            except Exception:
                details_text.append(f"📅 {self.task_data['due_at']}")

        if self.task_data['estimated_minutes']:
             details_text.append(f"⏱️ {self.task_data['estimated_minutes']}m")
        if self.meta_data and 'actual' in self.meta_data:
             details_text.append(f"✅ {self.meta_data['actual']}m")

        if details_text:
            details_label = QLabel("  •  ".join(details_text))
            details_label.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_SECONDARY}; padding-top: 4px;")
            content_layout.addWidget(details_label)

        action_layout = QHBoxLayout()
        action_layout.setSpacing(5)
        action_layout.setAlignment(Qt.AlignRight)

        if not is_done:
            start_btn = self._create_icon_button(os.path.join(ICON_DIR, 'play.svg'), "Start Task", COLOR_PRIMARY)
            start_btn.clicked.connect(lambda: self.task_started.emit(self.task_id))
            action_layout.addWidget(start_btn)
            
            complete_btn = self._create_icon_button(os.path.join(ICON_DIR, 'check-circle.svg'), "Mark as Complete", COLOR_SUCCESS)
            complete_btn.clicked.connect(lambda: self.task_toggled.emit(self.task_id))
            action_layout.addWidget(complete_btn)
        else:
            undo_btn = self._create_icon_button(os.path.join(ICON_DIR, 'rotate-ccw.svg'), "Mark as Pending", COLOR_TEXT_SECONDARY)
            undo_btn.clicked.connect(lambda: self.task_toggled.emit(self.task_id))
            action_layout.addWidget(undo_btn)
            
        delete_btn = self._create_icon_button(os.path.join(ICON_DIR, 'x-circle.svg'), "Delete Task", COLOR_DANGER)
        delete_btn.clicked.connect(lambda: self.task_deleted.emit(self.task_id))
        action_layout.addWidget(delete_btn)

        main_layout.addLayout(content_layout)
        main_layout.addStretch()
        main_layout.addLayout(action_layout)

    def _create_icon_button(self, icon_path, tooltip, color):
        button = QPushButton()
        if os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
        button.setFixedSize(28, 28)
        button.setToolTip(tooltip)
        button.setStyleSheet(f"""
            QPushButton {{ border-radius: 14px; background-color: transparent; padding: 4px; }}
            QPushButton:hover {{ background-color: {color}; }}
        """)
        return button
        
    def apply_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 25))
        self.setGraphicsEffect(shadow)


class DoNowView(QWidget):
    def __init__(self, user_id=None, db=None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.db = Database()
        self.tasks, self.meta, self.history = [], {}, {}
        self.search_text, self.filter_status, self.page, self.page_size = "", "all", 1, 10
        
        # [THÊM] State để lưu priority được chọn trong form
        self.current_priority = 4
        # Ensure view context defaults exist so callers can safely query
        self.view_mode = 'personal'
        self.group_id = None
        self.is_leader = False
        
        self.setupUI()
        self.load_data_from_db()
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self._check_deadlines)
        self.notification_timer.start(60 * 1000)

    def setupUI(self):
        self.setStyleSheet(f"""
            QWidget#DoNowView {{ background-color: {COLOR_BACKGROUND}; }}
            QGroupBox {{ font-size: 14px; font-weight: bold; color: {COLOR_TEXT_PRIMARY}; border: 1px solid {COLOR_BORDER}; border-radius: 8px; margin-top: 10px; padding: 15px; }}
            QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; left: 15px; padding: 0 5px; background-color: {COLOR_BACKGROUND}; }}
            QLineEdit, QDateTimeEdit, QComboBox {{ border: 1px solid {COLOR_BORDER}; border-radius: 6px; padding: 10px; background-color: {COLOR_WHITE}; font-size: 13px; color: {COLOR_TEXT_PRIMARY}; }}
            QLineEdit:focus, QDateTimeEdit:focus, QComboBox:focus {{ border: 1px solid {COLOR_PRIMARY}; }}
            QPushButton#MainCTA {{ background-color: {COLOR_PRIMARY}; color: {COLOR_WHITE}; font-weight: bold; font-size: 13px; border: none; border-radius: 6px; padding: 10px; }}
            QPushButton#MainCTA:hover {{ background-color: {COLOR_HOVER}; }}
            QPushButton#PaginationButton {{ background-color: {COLOR_WHITE}; color: {COLOR_TEXT_PRIMARY}; border: 1px solid {COLOR_BORDER}; border-radius: 6px; padding: 8px 16px; }}
            QPushButton#PaginationButton:disabled {{ background-color: #F8F9FA; color: {COLOR_TEXT_SECONDARY}; }}
            QPushButton#PaginationButton:hover {{ border-color: {COLOR_PRIMARY}; }}
            QScrollArea {{ border: none; background-color: transparent; }}
            #TasksContainer {{ background-color: transparent; }}
        """)
        self.setObjectName("DoNowView")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(20)

        self.header_label = QLabel("My Tasks")
        self.header_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        self.header_label.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(self.header_label)
        main_layout.addWidget(self._create_form_group())
        main_layout.addWidget(self._create_filter_bar())
        main_layout.addWidget(self._create_task_list_group(), 1)
        main_layout.addLayout(self._create_pagination_controls())

    def _create_form_group(self):
        group = QGroupBox("✨ Add New Task")
        layout = QGridLayout(group)
        self.title_input = QLineEdit(placeholderText="e.g., Finish project report")
        self.due_date_input = QDateTimeEdit(calendarPopup=True)
        self.due_date_input.setDateTime(QDateTime.currentDateTime())
        self.estimated_input = QLineEdit(placeholderText="Time in minutes")
        # [THÊM] Ghi chú cho task
        self.note_input = QLineEdit(placeholderText="Optional note")

        # [THÊM] Nút chọn Priority
        self.priority_button = QPushButton()
        self.priority_button.setToolTip("Set Priority")
        self._set_priority(4) # Set icon mặc định
        self.priority_button.clicked.connect(self._show_priority_menu)

        self.member_selector = QComboBox()
        self.member_selector.setPlaceholderText("Assign to member")
        self.member_selector.hide()

        add_btn = QPushButton("Add Task")
        add_btn.setObjectName("MainCTA")
        # expose to instance so set_view_context can enable/disable or hide/show
        self.add_btn = add_btn

        layout.addWidget(self.title_input, 0, 0, 1, 3)
        layout.addWidget(self.add_btn, 0, 3)
        layout.addWidget(self.due_date_input, 1, 0)
        layout.addWidget(self.estimated_input, 1, 1)
        layout.addWidget(self.priority_button, 1, 2)
        layout.addWidget(self.member_selector, 1, 3)
        layout.addWidget(self.note_input, 2, 0, 1, 4)
        
        add_btn.clicked.connect(self._handle_add_task)
        self.title_input.returnPressed.connect(self._handle_add_task)
        # expose group container for title changes
        self.group = group
        return group

    def set_view_context(self, mode, group_id=None, is_leader=False):
        self.view_mode = mode
        self.group_id = group_id
        self.is_leader = is_leader
        
        if mode == 'personal':
            self.header_label.setText("My Tasks")
            self.group.setTitle("✨ Add New Task")
            self._set_form_enabled(True)
            self.member_selector.hide()
            self.add_btn.show()
        elif mode == 'group':
            self.header_label.setText("Group Tasks")
            if is_leader:
                self.group.setTitle("✨ Add Group Task")
                self._set_form_enabled(True)
                self._populate_member_selector()
                self.member_selector.show()
                self.add_btn.show()
            else:
                self.group.setTitle("Add Group Task (Leader Only)")
                self._set_form_enabled(False)
                self.member_selector.hide()
                self.add_btn.hide()

        self.load_data_from_db()

    def _set_form_enabled(self, enabled: bool):
        self.title_input.setEnabled(enabled)
        self.due_date_input.setEnabled(enabled)
        self.estimated_input.setEnabled(enabled)
        self.note_input.setEnabled(enabled)
        self.priority_button.setEnabled(enabled)
        self.add_btn.setEnabled(enabled)

    def _populate_member_selector(self):
        self.member_selector.clear()
        if not self.group_id: return
        try:
            members = self.db.get_group_members(self.group_id)
            self.member_selector.addItem("Unassigned", None)
            for member_id, member_name in members:
                self.member_selector.addItem(member_name, member_id)
        except Exception as e:
            import logging
            logging.exception("Lỗi khi tải danh sách thành viên")


    def _show_priority_menu(self):
        menu = QMenu(self)
        icons = {
            1: 'flag-red.svg', 2: 'flag-green.svg', 
            3: 'flag-blue.svg', 4: 'flag-grey.svg'
        }
        for p_val in range(1, 5):
            icon_path = os.path.join(ICON_DIR, icons[p_val])
            action = QAction(QIcon(icon_path), f"Priority {p_val}", self) if os.path.exists(icon_path) else QAction(f"Priority {p_val}", self)
            action.triggered.connect(lambda chk, prio=p_val: self._set_priority(prio))
            menu.addAction(action)
        menu.exec_(self.priority_button.mapToGlobal(self.priority_button.rect().bottomLeft()))

    # [THÊM] Hàm cập nhật state và icon cho nút priority
    def _set_priority(self, priority):
        self.current_priority = priority
        icon_map = {1: 'flag-red.svg', 2: 'flag-green.svg', 3: 'flag-blue.svg', 4: 'flag-grey.svg'}
        icon_path = os.path.join(ICON_DIR, icon_map.get(priority, 'flag-grey.svg'))
        if os.path.exists(icon_path):
            self.priority_button.setIcon(QIcon(icon_path))

    def _create_filter_bar(self):
        container = QFrame()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0,0,0,0)
        self.search_input = QLineEdit(placeholderText="Search tasks...")
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["All Status", "Pending", "Done"])
        layout.addWidget(self.search_input, 1)
        layout.addWidget(self.status_filter_combo)
        self.search_input.textChanged.connect(self._handle_search_change)
        self.status_filter_combo.currentIndexChanged.connect(self._handle_filter_change)
        return container

    def _create_task_list_group(self):
        group = QGroupBox("📌 Task List")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(0, 5, 0, 5)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.tasks_container = QWidget()
        self.tasks_container.setObjectName("TasksContainer")
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setAlignment(Qt.AlignTop)
        self.tasks_layout.setSpacing(5)
        scroll_area.setWidget(self.tasks_container)
        layout.addWidget(scroll_area)
        return group

    def _create_pagination_controls(self):
        layout = QHBoxLayout()
        self.prev_btn = QPushButton("Previous")
        self.next_btn = QPushButton("Next")
        self.prev_btn.setObjectName("PaginationButton")
        self.next_btn.setObjectName("PaginationButton")
        self.page_label = QLabel(f"Page {self.page}")
        self.page_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-weight: bold;")
        self.page_label.setAlignment(Qt.AlignCenter)
        layout.addStretch()
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.page_label)
        layout.addWidget(self.next_btn)
        layout.addStretch()
        self.prev_btn.clicked.connect(lambda: self._handle_page_change(-1))
        self.next_btn.clicked.connect(lambda: self._handle_page_change(1))
        return layout

    def load_data_from_db(self):
        self.tasks = []
        try:
            if self.view_mode == 'personal':
                rows = self.db.get_tasks_for_user(self.user_id)
                for r in rows:
                    self.tasks.append({
                        "id": str(r[0]), "title": r[1], "is_done": bool(r[2]),
                        "due_at": r[3], "estimated_minutes": r[4], 
                        "priority": r[5] if len(r) > 5 else 4,
                        "note": r[6] if len(r) > 6 else ""
                    })
            elif self.view_mode == 'group' and self.group_id:
                rows = self.db.get_group_tasks(self.group_id)
                for r in rows:
                    assignee_id = r[2]
                    assignee_name = self.db.get_user_name(assignee_id) if assignee_id else "Unassigned"
                    self.tasks.append({
                        "id": str(r[0]), "title": r[3], "note": r[4],
                        "is_done": bool(r[5]), "due_at": r[6],
                        "assignee_name": assignee_name,
                        "priority": 4,
                        "estimated_minutes": None,
                    })
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải nhiệm vụ: {e}")
        self.render_tasks()

    # Compatibility wrapper: older callers call `load_data()`
    def load_data(self):
        """Backward-compatible alias used by MainWindow: load and render tasks."""
        self.load_data_from_db()

    def _parse_iso_datetime(self, s: str):
        if not s:
            return None
        if isinstance(s, datetime):
            return s
        s = str(s)
        try:
            if s.endswith('Z'):
                return datetime.fromisoformat(s.replace('Z', '+00:00'))
            return datetime.fromisoformat(s)
        except Exception:
            pass
        try:
            s2 = s.replace('T', ' ').rstrip('Z')
            try:
                return datetime.strptime(s2, '%Y-%m-%d %H:%M:%S')
            except Exception:
                return datetime.strptime(s2, '%Y-%m-%d')
        except Exception:
            return None

    def get_visible_tasks(self):
        def sort_key(task):
            # Sắp xếp theo is_done (chưa xong trước), sau đó là priority (1 là cao nhất), sau đó là điểm urgency
            return (task['is_done'], task.get('priority', 4), -calculate_urgency_score(task))

        now = time.time() * 1000
        def calculate_urgency_score(task):
            deadline_ms = float('-inf') # Dùng -inf để task không có deadline bị đẩy xuống dưới
            if task['due_at']:
                try:
                    dt_obj = _parse_iso_datetime_module(task['due_at'])
                    if dt_obj is None:
                        raise ValueError('unparsed')
                    deadline_ms = dt_obj.timestamp() * 1000
                except (ValueError, TypeError): pass
            urgency_hours = max(1, (deadline_ms - now) / (3600000))
            history_score = self.history.get(task['id'], 0) * 10
            return (1 / urgency_hours) * 100 + history_score
        
        sorted_tasks = sorted(self.tasks, key=sort_key)
        
        def filter_func(task):
            match_status = (self.filter_status == "all" or (self.filter_status == "pending" and not task['is_done']) or (self.filter_status == "done" and task['is_done']))
            match_search = self.search_text.lower() in task['title'].lower()
            return match_status and match_search
        
        filtered_tasks = list(filter(filter_func, sorted_tasks))
        start = (self.page - 1) * self.page_size
        return filtered_tasks, filtered_tasks[start:start + self.page_size]

    def render_tasks(self):
        while self.tasks_layout.count():
            child = self.tasks_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        all_filtered, visible_tasks = self.get_visible_tasks()

        if not visible_tasks:
            no_tasks_label = QLabel("🎉 Bạn không có nhiệm vụ nào.")
            no_tasks_label.setAlignment(Qt.AlignCenter)
            no_tasks_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 14px; padding: 40px;")
            self.tasks_layout.addWidget(no_tasks_label)
        else:
            for task in visible_tasks:
                task_widget = TaskItemWidget(task, self.meta.get(task['id']))
                task_widget.task_toggled.connect(self._handle_toggle_task)
                task_widget.task_deleted.connect(self._handle_delete_task)
                task_widget.task_started.connect(self._handle_start_task)
                self.tasks_layout.addWidget(task_widget)
        self.tasks_layout.addStretch()
        self.page_label.setText(f"Page {self.page}")
        self.prev_btn.setEnabled(self.page > 1)
        self.next_btn.setEnabled(len(all_filtered) > self.page * self.page_size)

    def _handle_add_task(self):
        title = self.title_input.text().strip()
        if not title: return
        
        qdt = self.due_date_input.dateTime()
        py_dt = datetime(qdt.date().year(), qdt.date().month(), qdt.date().day(), qdt.time().hour(), qdt.time().minute(), qdt.time().second())
        due_at = py_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        estimated = self.estimated_input.text().strip()
        est_mins = int(estimated) if estimated.isdigit() else None
        note = self.note_input.text().strip()
        
        try:
            if self.view_mode == 'personal':
                self.db.add_task_with_meta(
                    self.user_id, title, note=note, is_done=0, due_at=due_at, 
                    estimated_minutes=est_mins, priority=self.current_priority
                )
            elif self.view_mode == 'group' and self.is_leader:
                assignee_id = self.member_selector.currentData()
                # Use keyword args to avoid parameter ordering bugs (creator_id must be second param)
                self.db.add_group_task(
                    self.group_id,
                    creator_id=self.user_id,
                    title=title,
                    note=note,
                    is_done=0,
                    due_at=due_at,
                    assignee_id=assignee_id
                )
            else:
                return
            
            self.title_input.clear(); self.estimated_input.clear()
            self.note_input.clear()
            self._set_priority(4)
            self.load_data_from_db()
            # If calendar is open in the main window, refresh it so newly-added tasks appear
            try:
                win = self.window()
                cw = getattr(win, 'calendar_widget', None)
                if cw and getattr(cw, 'current_view_mode', '') == 'group':
                    try:
                        cw.set_group_context(self.group_id)
                        cw.populate_calendar()
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể thêm nhiệm vụ: {e}")
    
    def _handle_toggle_task(self, task_id):
        task = next((t for t in self.tasks if t['id'] == task_id), None)
        if not task: return
        
        new_status = not task['is_done']
        try:
            if self.view_mode == 'personal':
                self.db.update_task_status(int(task_id), int(new_status))
            elif self.view_mode == 'group':
                self.db.update_group_task_status(int(task_id), int(new_status))
                # also refresh calendar if visible
                try:
                    win = self.window()
                    cw = getattr(win, 'calendar_widget', None)
                    if cw and getattr(cw, 'current_view_mode', '') == 'group':
                        try:
                            cw.refresh_day(datetime.strptime(task.get('due_at') or '', '%Y-%m-%d %H:%M:%S').day if task.get('due_at') else None)
                        except Exception:
                            try:
                                cw.populate_calendar()
                            except Exception:
                                pass
                except Exception:
                    pass

            task['is_done'] = new_status
            self.render_tasks()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật trạng thái: {e}")


    def _handle_delete_task(self, task_id):
        try:
            if self.view_mode == 'personal':
                # only owner can delete personal task
                try:
                    data = self.db.get_task_by_id(int(task_id))
                    if data and data[1] != self.user_id:
                        QMessageBox.warning(self, 'Không có quyền', 'Bạn chỉ có thể xóa nhiệm vụ của chính mình.')
                        return
                except Exception:
                    pass
                self.db.delete_task(int(task_id))
            elif self.view_mode == 'group':
                # only group leader can delete group tasks
                try:
                    leader_id = self.db.get_group_leader(self.group_id)
                    if leader_id is None or leader_id != self.user_id:
                        QMessageBox.warning(self, 'Không có quyền', 'Chỉ trưởng nhóm mới có thể xóa công việc nhóm.')
                        return
                except Exception:
                    QMessageBox.warning(self, 'Lỗi', 'Không thể kiểm tra quyền xóa.')
                    return
                self.db.delete_group_task(int(task_id))
            
            self.tasks = [t for t in self.tasks if t['id'] != task_id]
            if task_id in self.meta: del self.meta[task_id]
            if task_id in self.history: del self.history[task_id]
            self.render_tasks()
            # notify calendar to refresh
            try:
                win = self.window()
                cw = getattr(win, 'calendar_widget', None)
                if cw and getattr(cw, 'current_view_mode', '') == 'group':
                    try:
                        cw.populate_calendar()
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xóa nhiệm vụ: {e}")

    def _handle_start_task(self, task_id):
        self.meta.setdefault(task_id, {})['start'] = time.time()
        QMessageBox.information(self, "Task Started", "Timer for task has started.")

    def _handle_search_change(self, text):
        self.search_text = text; self.page = 1; self.render_tasks()

    def _handle_filter_change(self, index):
        self.filter_status = {0: "all", 1: "pending", 2: "done"}.get(index)
        self.page = 1; self.render_tasks()
        
    def _handle_page_change(self, delta):
        self.page = max(1, self.page + delta); self.render_tasks()
        
    def _check_deadlines(self):
        now_utc = datetime.utcnow()
        for task in self.tasks:
            if not task['is_done'] and task['due_at']:
                try:
                    due_date = self._parse_iso_datetime(task['due_at'])
                    if due_date is None:
                        continue
                    time_left = due_date - now_utc
                    if timedelta(minutes=0) < time_left <= timedelta(minutes=15):
                        QMessageBox.warning(self, "Deadline Reminder", f"Task sắp đến hạn: {task['title']}\nCòn khoảng {time_left.seconds // 60} phút.")
                except Exception:
                    continue

