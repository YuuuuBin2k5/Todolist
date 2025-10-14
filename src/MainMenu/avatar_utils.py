import os
from pathlib import Path
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath, QPen, QColor
from PyQt5.QtCore import Qt, QRectF
import logging

def load_avatar_pixmap(user_id, size=44):
    """Return a circular QPixmap for the given user_id if an avatar file exists.

    Looks under src/assets/avatars for files named user_{id}.[png|jpg|jpeg|bmp].
    Returns a QPixmap of `size` x `size`, or None if no file found or load fails.
    """
    try:
        base = Path(__file__).resolve().parents[1]  # points to src/
        avatar_dir = base / 'assets' / 'avatars'
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
    """Try to load an avatar QPixmap for the given task dictionary.

    Priority:
      1) use task_data['assignee_id'] if present
      2) if not present and db provided, try to map task_data['assignee_name'] -> user_id via DB
    Returns QPixmap or None.
    Also logs the candidate paths for debugging.
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
