import os
from pathlib import Path
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath, QPen, QColor
from PyQt5.QtCore import Qt, QRectF
import logging

def load_avatar_pixmap(user_id, size=44):
    """Trả về QPixmap dạng tròn cho `user_id` nếu tồn tại file avatar.

    Tìm trong `src/assets/avatars` các file có tên `user_{id}.[png|jpg|jpeg|bmp]`.
    Trả về QPixmap kích thước `size` x `size`, hoặc `None` nếu không tìm thấy file hoặc tải thất bại.
    """
    try:
        base = Path(__file__).resolve().parents[1]  # points to src/
        avatar_dir = base / 'assets' / 'avatars'
        # trỏ tới thư mục chứa ảnh đại diện
        if not avatar_dir.exists():
            return None
        found = None
        for ext in ('.png', '.jpg', '.jpeg', '.bmp'):
            p = avatar_dir / f'user_{user_id}{ext}'
            if p.exists():
                found = p
                break
        if not found:
            logging.debug('avatar_utils: no avatar file found for user_id=%s in %s', user_id, str(avatar_dir))
            return None
        src = QPixmap(str(found))
        if src.isNull():
            return None
        target = QPixmap(size, size)
        target.fill(Qt.transparent)
        painter = QPainter(target)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(0.0, 0.0, float(size), float(size))
        path = QPainterPath()
        path.addEllipse(rect)
        painter.setClipPath(path)
        src_scaled = src.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        sx = (src_scaled.width() - size) // 2
        sy = (src_scaled.height() - size) // 2
        painter.drawPixmap(-sx, -sy, src_scaled)
        pen = QPen(QColor(255, 255, 255, 200))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(rect.adjusted(1.0, 1.0, -1.0, -1.0))
        painter.end()
        return target
    except Exception:
        logging.exception('avatar_utils: failed to load avatar for user_id=%s', user_id)
        return None


def load_avatar_for_task(task_data: dict, db=None, size=44):
    """Cố gắng tải QPixmap avatar cho task được cung cấp dưới dạng dict.

    Thứ tự ưu tiên:
      1) sử dụng `task_data['assignee_id']` nếu có
      2) nếu không có và `db` được cung cấp, cố gắng ánh xạ `task_data['assignee_name']` -> user_id qua DB
    Trả về QPixmap hoặc `None`.
    Cũng ghi log các đường dẫn ứng viên để hỗ trợ gỡ lỗi.
    """
    try:
        assignee_id = None
        if task_data is None:
            return None
        assignee_id = task_data.get('assignee_id')
        if not assignee_id and db and task_data.get('assignee_name'):
            try:
                assignee_id = db.get_user_id_by_name(task_data.get('assignee_name'))
                logging.debug('avatar_utils: resolved assignee_name=%s -> id=%s', task_data.get('assignee_name'), assignee_id)
            except Exception:
                logging.exception('avatar_utils: DB lookup failed for name=%s', task_data.get('assignee_name'))
        if assignee_id:
            pix = load_avatar_pixmap(assignee_id, size=size)
            if pix:
                logging.debug('avatar_utils: loaded avatar for assignee_id=%s', assignee_id)
                return pix
        logging.debug('avatar_utils: no avatar available for task_data=%s', task_data)
        return None
    except Exception:
        logging.exception('avatar_utils: unexpected error in load_avatar_for_task')
        return None
