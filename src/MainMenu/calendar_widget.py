# Trong file MainMenu/calendar_widget.py

import calendar
from datetime import datetime, timedelta
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout, QApplication, QMessageBox
from PyQt5.QtGui import QFontDatabase, QFont
from PyQt5.QtCore import Qt
from MainMenu.components import DayWidget, TaskWidget, GroupTaskWidget, TaskBadge
from Managers.database_manager import Database
from config import (
    CALENDAR_BG_GRADIENT_START, CALENDAR_BG_GRADIENT_END, CALENDAR_MONTH_PILL_START, 
    CALENDAR_MONTH_PILL_END, FONT_PATH
)

calendar.setfirstweekday(calendar.SUNDAY)

VIETNAMESE_MONTHS = [
    "Tháng Một", "Tháng Hai", "Tháng Ba", "Tháng Tư", "Tháng Năm", "Tháng Sáu",
    "Tháng Bảy", "Tháng Tám", "Tháng Chín", "Tháng Mười", "Tháng Mười Một", "Tháng Mười Hai"
]

class CalendarWidget(QWidget):
    def __init__(self, user_id, db=None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.db = Database()
            
        self.current_date = datetime.now()
        
        # [MỚI] Thêm trạng thái để biết đang xem lịch cá nhân hay nhóm
        self.current_view_mode = 'personal' 
        self.user_names_cache = {} # Cache để lưu tên user, tránh query nhiều lần
        self.current_group_id = None
        self.current_group_leader_id = None

        self.initUI()
        self.populate_calendar()

    # [MỚI] Hàm để chuyển đổi chế độ xem
    def switch_view_mode(self, mode):
        print(f"CalendarWidget chuyển sang chế độ: {mode}")
        self.current_view_mode = mode
        self.populate_calendar() # Tải lại lịch với chế độ mới

    def set_group_context(self, group_id: int):
        """Set current group id and leader id for permission checks."""
        self.current_group_id = group_id
        try:
            self.current_group_leader_id = self.db.get_group_leader(group_id)
        except Exception:
            self.current_group_leader_id = None

    def initUI(self):
        # Modernized header with centered month label inside a pill and prev/next icons
        # Try to load a bundled font for a nicer look
        try:
            # Prefer centralized FONT_PATH if available
            font_path = FONT_PATH
            if os.path.exists(font_path):
                QFontDatabase.addApplicationFont(font_path)
                app_font = QFont("BeVietnamPro-Regular")
                app_font.setPointSize(10)
                self.setFont(app_font)
        except Exception:
            pass

        self.main_layout = QVBoxLayout(self)
        # overall background gradient (ocean theme)
        self.setStyleSheet(f'''
            QWidget {{ background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 {CALENDAR_BG_GRADIENT_START}, stop:1 {CALENDAR_BG_GRADIENT_END}); }}
        ''')
        header_layout = QHBoxLayout()
        self.prev_month_btn = QPushButton("◀")
        self.prev_month_btn.setFixedSize(36, 36)
        self.prev_month_btn.clicked.connect(self.prev_month)
        self.next_month_btn = QPushButton("▶")
        self.next_month_btn.setFixedSize(36, 36)
        self.next_month_btn.clicked.connect(self.next_month)

        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignCenter)
        font = self.month_label.font()
        font.setPointSize(20)
        font.setBold(True)
        self.month_label.setFont(font)
        # month label - ocean pill
        self.month_label.setStyleSheet(f"padding: 10px 24px; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {CALENDAR_MONTH_PILL_START}, stop:1 {CALENDAR_MONTH_PILL_END}); border-radius:18px; color: white;")

        header_layout.addStretch()
        header_layout.addWidget(self.prev_month_btn)
        header_layout.addSpacing(8)
        header_layout.addWidget(self.month_label)
        header_layout.addSpacing(8)
        header_layout.addWidget(self.next_month_btn)
        header_layout.addStretch()
        self.main_layout.addLayout(header_layout)

        # calendar grid
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(14)
        self.main_layout.addLayout(self.grid_layout)

    def _get_current_group_id(self):
        """Return the current group id if set; otherwise try to find a group for the user.

        This is used by DayWidget when adding group tasks from a day cell.
        """
        if self.current_group_id:
            return self.current_group_id
        try:
            groups = self.db.get_groups_for_user(self.user_id)
            if groups:
                return groups[0][0]
        except Exception:
            pass
        return None

    def _parse_iso_datetime(self, s: str):
        """Try to parse many ISO-like datetime strings into a datetime object.

        Accepts formats like:
          - 2025-10-06 05:24:08
          - 2025-10-06T05:24:08Z
          - 2025-10-06
        Returns datetime or None on failure.
        """
        if not s:
            return None
        if isinstance(s, datetime):
            return s
        s = str(s)
        # try fromisoformat with Z -> +00:00 replacement
        try:
            if s.endswith('Z'):
                return datetime.fromisoformat(s.replace('Z', '+00:00'))
            return datetime.fromisoformat(s)
        except Exception:
            pass
        # replace T with space and strip Z
        try:
            s2 = s.replace('T', ' ').rstrip('Z')
            try:
                return datetime.strptime(s2, '%Y-%m-%d %H:%M:%S')
            except Exception:
                return datetime.strptime(s2, '%Y-%m-%d')
        except Exception:
            return None

    # setup_week_headers and clear_calendar are implemented later in this file
    # to keep a single canonical implementation (see below).
                
    def populate_calendar(self, tasks_by_day=None):
        """
            Vẽ lại toàn bộ lịch cho tháng hiện tại (lưu trong self.current_date).
            Args:
                tasks_by_day (dict): Dictionary với key là ngày (int) và value là list các task tuple
        """
        self.clear_calendar() # Xóa lịch cũ
        self.setup_week_headers() # Vẽ lại tiêu đề tuần (vì cũng bị xóa ở trên)
        
        month_name = VIETNAMESE_MONTHS[self.current_date.month - 1]
        self.month_label.setText(f"{month_name} {self.current_date.year}")
        calendar.setfirstweekday(calendar.SUNDAY)
        month_calendar = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        

        # Duyệt qua từng tuần và từng ngày để tạo DayWidget
        today = datetime.now()


        for week_num, week_data in enumerate(month_calendar):
            for day_num, day_data in enumerate(week_data):
                if day_data != 0:
                    day_widget = DayWidget(str(day_data), self.current_date.year, self.current_date.month, calendar_ref=self)
                    self.grid_layout.addWidget(day_widget, week_num + 1, day_num)

                    if(self.current_date.year == today.year and
                       self.current_date.month == today.month and
                       day_data == today.day):
                        day_widget.set_today_highlight(True)

                    # Thêm widget ngày vào lưới tại đúng vị trí hàng (tuần) và cột (thứ)
                    # (đã thêm ở trên)
        
        # Nếu caller truyền sẵn tasks_by_day thì dùng nó (tránh fetch 2 lần).
        # Ngược lại widget sẽ tự fetch từ DB theo current_view_mode.
        for i in range(1, self.grid_layout.rowCount()): # Bắt đầu từ hàng 1 để bỏ qua header
            self.grid_layout.setRowStretch(i, 1)
        for i in range(self.grid_layout.columnCount()):
            self.grid_layout.setColumnStretch(i, 1)
        if tasks_by_day:
            tasks = tasks_by_day
        else:
            if self.current_view_mode == 'personal':
                tasks = self._fetch_personal_tasks_for_month()
            else:
                tasks = self._fetch_group_tasks_for_month()

        if tasks:
            self._display_tasks(tasks)
        

    def add_tasks_from_data(self, tasks_by_day):
        """
            Thêm tasks từ dữ liệu thực tế vào lịch.
            Args:
                tasks_by_day (dict): Dictionary với key là ngày (int) và value là list các task tuple
        """
        # Duyệt qua các ô trong lưới để tìm DayWidget tương ứng và thêm task
        # Keep a per-day set of seen tasks to avoid duplicates
        seen = {}
        for row in range(1, self.grid_layout.rowCount()):
            for col in range(self.grid_layout.columnCount()):
                item = self.grid_layout.itemAtPosition(row, col)
                if item and isinstance(item.widget(), DayWidget):
                    day_widget = item.widget()
                    day = int(day_widget.date_label.text()) # Lấy số ngày từ label
                    if day in tasks_by_day:
                        # ensure previous tasks (if any) are cleared before adding
                        try:
                            day_widget.clear_tasks()
                        except Exception:
                            pass
                        if day not in seen:
                            seen[day] = set()
                        for task_data in tasks_by_day[day]:
                            # normalize various forms (dict or tuple) into fields
                            t = None
                            if isinstance(task_data, dict):
                                t = {
                                    'task_id': task_data.get('task_id'),
                                    'title': task_data.get('title'),
                                    'is_done': task_data.get('is_done', False),
                                    'note': task_data.get('note', ''),
                                    'due_at': task_data.get('due_at'),
                                    'assignee_name': task_data.get('assignee_name') or ''
                                }
                            else:
                                # support tuple shapes like (task_id, title, is_done, note, due_at)
                                try:
                                    if len(task_data) >= 5:
                                        t = {
                                            'task_id': task_data[0],
                                            'title': task_data[1],
                                            'is_done': bool(task_data[2]),
                                            'note': task_data[3],
                                            'due_at': task_data[4],
                                            'assignee_name': ''
                                        }
                                    else:
                                        # fallback to (title, is_done, note)
                                        title, is_done_val, note_text = task_data
                                        t = {'task_id': None, 'title': title, 'is_done': bool(is_done_val), 'note': note_text, 'due_at': None, 'assignee_name': ''}
                                except Exception:
                                    continue

                            title = t['title']
                            is_done = t['is_done']
                            note_text = t.get('note', '')
                            due_at = t.get('due_at')
                            assignee_name = t.get('assignee_name', '')
                            key = ('id', t['task_id']) if t.get('task_id') else (title, due_at, assignee_name)
                            if key in seen[day]:
                                continue
                            seen[day].add(key)
                            # create a visual badge for the calendar tile
                            if assignee_name:
                                badge = TaskBadge(title, color='#5c6bc0', note=note_text, assignee_name=assignee_name, parent=None, task_id=t.get('task_id'), is_group=True, calendar_ref=self)
                                try:
                                    # set checked state without emitting toggled signal to avoid recursion
                                    badge.checkbox.blockSignals(True)
                                    badge.checkbox.setChecked(bool(is_done))
                                    badge.checkbox.setText('✓' if bool(is_done) else '')
                                    badge.checkbox.blockSignals(False)
                                except Exception:
                                    pass
                                if is_done:
                                    badge.setStyleSheet("background: #bdbdbd; border-radius: 12px; padding: 4px;")
                                    badge.label.setStyleSheet('color:#fff; text-decoration: line-through; font-size:11px;')
                                day_widget.add_task(badge)
                            else:
                                badge = TaskBadge(title, color='#66bb6a', note=note_text, parent=None, task_id=t.get('task_id'), is_group=False, calendar_ref=self)
                                try:
                                    badge.checkbox.setChecked(bool(is_done))
                                except Exception:
                                    pass
                                if is_done:
                                    badge.setStyleSheet("background: #bdbdbd; border-radius: 12px; padding: 4px;")
                                    badge.label.setStyleSheet('color:#fff; text-decoration: line-through; font-size:11px;')
                                day_widget.add_task(badge)

    def _fetch_personal_tasks_for_month(self):
        # Đổi tên hàm cũ _fetch_tasks_for_month thành _fetch_personal_tasks_for_month
        # Logic bên trong giữ nguyên
        tasks_by_day = {}
        month_str = self.current_date.strftime('%Y-%m')
        try:
            all_tasks = self.db.get_tasks_for_user_month(self.user_id, month_str)
            # all_tasks: list of tuples (task_id, title, is_done, note, due_at)
            for task in all_tasks:
                task_id, title, is_done_int, note, due_at_str = task
                if due_at_str:
                    dt = self._parse_iso_datetime(due_at_str)
                    if not dt:
                        continue
                    day = dt.day
                    if day not in tasks_by_day:
                        tasks_by_day[day] = []
                    tasks_by_day[day].append({
                        'task_id': task_id,
                        'title': title,
                        'is_done': bool(is_done_int),
                        'note': note,
                        'due_at': due_at_str,
                        'assignee_id': None,
                        'assignee_name': None,
                    })
            # Additionally include any group tasks assigned to this user in the same month
            try:
                group_tasks = self.db.get_group_tasks_for_user_month(self.user_id, month_str)
                for gt in group_tasks:
                    # gt: (task_id, group_id, assignee_id, title, note, is_done, due_at)
                    g_task_id, g_group_id, g_assignee_id, g_title, g_note, g_is_done, g_due_at = gt
                    if g_due_at:
                        g_dt = self._parse_iso_datetime(g_due_at)
                        if not g_dt:
                            continue
                        g_day = g_dt.day
                        if g_day not in tasks_by_day:
                            tasks_by_day[g_day] = []
                        tasks_by_day[g_day].append({
                            'task_id': g_task_id,
                            'title': g_title,
                            'is_done': bool(g_is_done),
                            'note': g_note,
                            'due_at': g_due_at,
                            'assignee_id': g_assignee_id,
                            'assignee_name': self.db.get_user_name(g_assignee_id) if g_assignee_id else 'Chưa phân công',
                        })
            except Exception:
                pass
        except Exception as e:
            print(f"Lỗi khi lấy task cá nhân: {e}")
        return tasks_by_day

    # [MỚI] Hàm để lấy task của nhóm
    def _fetch_group_tasks_for_month(self):
        tasks_by_day = {}
        month_str = self.current_date.strftime('%Y-%m')
        try:
            # Prefer explicit current_group_id if set; otherwise find first group for user
            group_id = self.current_group_id
            if not group_id:
                groups = self.db.get_groups_for_user(self.user_id)
                if not groups:
                    return {}
                group_id = groups[0][0]

            all_tasks = self.db.get_group_tasks_for_month(group_id, month_str)
            # all_tasks: list of tuples (task_id, group_id, assignee_id, title, note, is_done, due_at)
            for task_data in all_tasks:
                task_id, g_group_id, assignee_id, title, note, is_done_int, due_at_str = task_data
                if due_at_str:
                    dt = self._parse_iso_datetime(due_at_str)
                    if not dt:
                        continue
                    day = dt.day
                    try:
                        assignee_name = self.db.get_user_name(assignee_id) if assignee_id else ''
                    except Exception:
                        assignee_name = ''
                    if day not in tasks_by_day:
                        tasks_by_day[day] = []
                    tasks_by_day[day].append({
                        'task_id': task_id,
                        'title': title,
                        'is_done': bool(is_done_int),
                        'note': note,
                        'due_at': due_at_str,
                        'assignee_id': assignee_id,
                        'assignee_name': assignee_name,
                    })
        except Exception as e:
            print(f"Lỗi khi lấy task nhóm: {e}")
        return tasks_by_day
    
    def _get_user_name(self, user_id):
        if not user_id:
            return "Chưa giao"
        if user_id in self.user_names_cache:
            return self.user_names_cache[user_id]
        name = self.db.get_user_name(user_id)
        if name:
            self.user_names_cache[user_id] = name
            return name
        return "Không rõ"

    # [THAY ĐỔI] Sửa lại để xử lý cấu trúc dữ liệu mới (có thêm assignee_name)
    def _display_tasks(self, tasks):
        # Dedupe per day to prevent duplicate renderings
        seen = {}
        for row in range(1, self.grid_layout.rowCount()):
            for col in range(self.grid_layout.columnCount()):
                item = self.grid_layout.itemAtPosition(row, col)
                if item and isinstance(item.widget(), DayWidget):
                    day_widget = item.widget()
                    try:
                        day_text = day_widget.date_label.text().strip()
                        if not day_text:
                            continue
                        day_from_widget = int(day_text)
                        if day_from_widget in tasks:
                            # clear existing tasks before populating
                            try:
                                day_widget.clear_tasks()
                            except Exception:
                                pass
                            if day_from_widget not in seen:
                                seen[day_from_widget] = set()
                            for task_data in tasks[day_from_widget]:
                                # normalize
                                t = None
                                if isinstance(task_data, dict):
                                    t = {
                                        'task_id': task_data.get('task_id'),
                                        'title': task_data.get('title'),
                                        'is_done': task_data.get('is_done', False),
                                        'note': task_data.get('note', ''),
                                        'due_at': task_data.get('due_at'),
                                        'assignee_name': task_data.get('assignee_name') or ''
                                    }
                                else:
                                    try:
                                        if len(task_data) >= 5:
                                            t = {
                                                'task_id': task_data[0],
                                                'title': task_data[1],
                                                'is_done': bool(task_data[2]),
                                                'note': task_data[3],
                                                'due_at': task_data[4],
                                                'assignee_name': ''
                                            }
                                        else:
                                            title, is_done_val, note_text = task_data
                                            t = {'task_id': None, 'title': title, 'is_done': bool(is_done_val), 'note': note_text, 'due_at': None, 'assignee_name': ''}
                                    except Exception:
                                        continue

                                title = t['title']
                                is_done = t['is_done']
                                note = t.get('note', '')
                                due_at = t.get('due_at')
                                assignee_name = t.get('assignee_name', '')
                                key = ('id', t['task_id']) if t.get('task_id') else (title, due_at, assignee_name)

                                if key in seen[day_from_widget]:
                                    continue
                                seen[day_from_widget].add(key)

                                # Use visual TaskBadge inside calendar tiles; keep TaskWidget for detail dialogs
                                color = '#66bb6a' if not assignee_name else '#5c6bc0'
                                badge = TaskBadge(title, color=color, note=note, assignee_name=assignee_name, task_id=t.get('task_id'), is_group=bool(assignee_name), calendar_ref=self)
                                # ensure badge checkbox matches DB state and apply done style (block signals while doing so)
                                try:
                                    badge.checkbox.blockSignals(True)
                                    badge.checkbox.setChecked(bool(is_done))
                                    badge.checkbox.setText('✓' if bool(is_done) else '')
                                    badge.checkbox.blockSignals(False)
                                except Exception:
                                    pass
                                if is_done:
                                    badge.setStyleSheet("background: #bdbdbd; border-radius: 12px; padding: 4px;")
                                    badge.label.setStyleSheet('color:#fff; text-decoration: line-through; font-size:11px;')
                                day_widget.add_task(badge)
                    except Exception as e:
                        print(f"Lỗi khi hiển thị task: {e}")
                        
    # ... (các hàm còn lại như clear_calendar, setup_week_headers, prev_month, next_month giữ nguyên) ...
    def clear_calendar(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def setup_week_headers(self):
        days = ["Chủ Nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"]
        for i, day in enumerate(days):
            label = QLabel(day)
            label.setObjectName("WeekDayLabel")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet('color: #02457a; font-weight:700; background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #bfe9ff, stop:1 #e6f7ff); padding:8px; border-radius:6px;')
            self.grid_layout.addWidget(label, 0, i)

    def prev_month(self):
        self.current_date = self.current_date.replace(day=1) - timedelta(days=1)
        self.populate_calendar()

    def next_month(self):
        days_in_month = calendar.monthrange(self.current_date.year, self.current_date.month)[1]
        self.current_date = self.current_date.replace(day=days_in_month) + timedelta(days=1)
        self.populate_calendar()

    def add_task_to_db(self, date_obj, task_desc, note_text=""):
        """
        Nhận tín hiệu từ DayWidget để thêm công việc cá nhân vào database.
        """
        try:
            # Chuyển đổi đối tượng datetime thành chuỗi 'YYYY-MM-DD HH:MM:SS'
            try:
                due_date_str = date_obj.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                # fallback for date-only
                due_date_str = date_obj.strftime('%Y-%m-%d')
            # Use the richer API which supports estimate/priority; keep defaults
            # add_task is a compatibility wrapper but call add_task_with_meta to be explicit
            try:
                self.db.add_task_with_meta(self.user_id, task_desc, note_text, 0, due_date_str, estimated_minutes=None, priority=2)
            except Exception:
                # fallback to wrapper
                self.db.add_task(self.user_id, task_desc, note_text, 0, due_date_str)
            
            # Sau khi thêm thành công, vẽ lại lịch để hiển thị công việc mới
            self.populate_calendar()
            print(f"Đã thêm công việc cá nhân thành công: '{task_desc}' vào ngày {due_date_str}")

        except Exception as e:
            print(f"Lỗi khi thêm công việc cá nhân vào database: {e}")

    def open_day_detail(self, day: int):
        """Open DayDetailDialog for the given day (uses self.current_date year/month)."""
        try:
            from MainMenu.components import DayDetailDialog
            # build tasks_data for that day by scanning current grid
            tasks_data = []
            for row in range(1, self.grid_layout.rowCount()):
                for col in range(self.grid_layout.columnCount()):
                    item = self.grid_layout.itemAtPosition(row, col)
                    if item and isinstance(item.widget(), DayWidget):
                        day_widget = item.widget()
                        if int(day_widget.date_label.text()) == day:
                            # extract child widgets
                            for i in range(day_widget.tasks_layout.count()):
                                w = day_widget.tasks_layout.itemAt(i).widget()
                                if not w:
                                    continue
                                # try to normalize
                                if hasattr(w, 'task_id'):
                                    title = w.text() if hasattr(w, 'text') else getattr(w, 'label', lambda: '')()
                                    is_done = getattr(w, 'checkbox', None) and getattr(w.checkbox, 'isChecked', lambda: False)()
                                    note = getattr(w, 'note', '')
                                    assignee = getattr(w, 'assignee_name', None)
                                    tasks_data.append({'title': title, 'is_done': is_done, 'note': note, 'assignee_name': assignee, 'task_id': getattr(w, 'task_id', None), 'is_group': getattr(w, 'is_group', False)})
                            break
            # open dialog
            full_date = datetime(self.current_date.year, self.current_date.month, day)
            dialog = DayDetailDialog(full_date, tasks_data, calendar_ref=self)
            dialog.exec_()
        except Exception as e:
            print(f"Lỗi khi mở chi tiết ngày: {e}")

    def add_group_task_to_db(self, date_obj, task_desc, assignee_id=None, note_text=""):
        """
        Nhận tín hiệu từ DayWidget để thêm công việc nhóm vào database.
        """
        try:
            try:
                due_date_str = date_obj.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                due_date_str = date_obj.strftime('%Y-%m-%d')
            group_id = self._get_current_group_id()
            if group_id:
                # db.add_group_task(group_id, creator_id, title, note="", is_done=0, due_at=None, assignee_id=None)
                self.db.add_group_task(group_id, self.user_id, task_desc, note_text, 0, due_date_str, assignee_id)
                self.populate_calendar()
                print(f"Đã giao công việc nhóm thành công: '{task_desc}' cho user_id {assignee_id}")
            else:
                print(f"Lỗi: Người dùng {self.user_id} không thuộc nhóm nào.")

        except Exception as e:
            print(f"Lỗi khi thêm công việc nhóm vào database: {e}")

    def delete_task(self, task_id: int, is_group: bool = False):
        """Delete a task (personal or group) by id and refresh calendar."""
        try:
            if is_group:
                self.db.delete_group_task(task_id)
            else:
                self.db.delete_task(task_id)
            # refresh
            self.populate_calendar()
            print(f"Đã xóa task id={task_id} group={is_group}")
        except Exception as e:
            print(f"Lỗi khi xóa task: {e}")

    def update_task_status(self, task_id: int, is_done: int, is_group: bool = False):
        """Update the is_done status for a personal or group task.

        This is called by TaskWidget when the user toggles the checkbox.
        We persist the change. Caller may refresh specific day via refresh_day(day) to avoid full redraw.
        """
        try:
            if not task_id:
                return
            if is_group:
                # group tasks table
                self.db.update_group_task_status(task_id, is_done)
            else:
                self.db.update_task_status(task_id, is_done)
            # Do not call populate_calendar here to avoid full redraw; caller should call refresh_day(day)
            print(f"Cập nhật trạng thái task id={task_id} group={is_group} -> is_done={is_done}")
            return True
        except Exception as e:
            print(f"Lỗi khi cập nhật trạng thái task: {e}")
            return False

    def refresh_day(self, day: int):
        """Refresh widgets for a single day (day = 1..31) without re-rendering whole calendar.

        This fetches tasks for the current month and updates only the targeted DayWidget.
        """
        try:
            # collect tasks for the month then pick the single day
            if self.current_view_mode == 'personal':
                tasks = self._fetch_personal_tasks_for_month()
            else:
                tasks = self._fetch_group_tasks_for_month()

            tasks_for_day = {}
            if isinstance(tasks, dict) and day in tasks:
                tasks_for_day[day] = tasks[day]
            else:
                tasks_for_day[day] = []

            # delegate to _display_tasks which handles clearing/adding for days present in dict
            self._display_tasks(tasks_for_day)
        except Exception as e:
            print(f"Lỗi khi refresh day {day}: {e}")

    def can_toggle_task(self, task_id: int, is_group: bool = False) -> tuple:
        """Check whether the current user is allowed to toggle the given task.

        Returns (allowed: bool, message: str).
        For group tasks: group leader can toggle any task; other members can only toggle tasks assigned to themselves.
        For personal tasks: only task owner can toggle.
        """
        try:
            if is_group:
                data = self.db.get_group_task_by_id(task_id)
                if not data:
                    return False, "Không tìm thấy công việc nhóm."
                # data tuple from DB: (task_id, group_id, assignee_id, title, note, is_done, created_at, due_at)
                _, group_id, assignee_id, title, note, is_done, created_at, due_at = data
                # If current group leader is the current user -> allow
                if self.current_group_leader_id and self.user_id == self.current_group_leader_id:
                    return True, ""
                # else only assignee can toggle
                if assignee_id and assignee_id == self.user_id:
                    return True, ""
                return False, "Bạn không có quyền thay đổi trạng thái công việc này."
            else:
                data = self.db.get_task_by_id(task_id)
                if not data:
                    return False, "Không tìm thấy công việc."
                # data: (task_id, user_id, title, note, is_done, due_at)
                _, owner_id, title, note, is_done, due_at = data
                if owner_id == self.user_id:
                    return True, ""
                return False, "Bạn chỉ có thể thay đổi công việc của chính mình."
        except Exception as e:
            print(f"Lỗi khi kiểm tra quyền toggle task: {e}")
            return False, "Lỗi kiểm tra quyền." 