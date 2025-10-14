from Managers.database_manager import Database
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
                             QPushButton, QInputDialog, QMessageBox, QLabel, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal

class GroupSelectionDialog(QDialog):
    """Cửa sổ để chọn, tạo và xem các nhóm."""
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.selected_group = None # Sẽ lưu (group_id, group_name)
        
        self.setWindowTitle("Chọn Nhóm")
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        self.group_list_widget = QListWidget()
        self.group_list_widget.itemDoubleClicked.connect(self.accept_selection)
        layout.addWidget(self.group_list_widget)
        
        button_layout = QHBoxLayout()
        create_btn = QPushButton("Tạo nhóm mới")
        create_btn.clicked.connect(self.create_new_group)
        select_btn = QPushButton("Chọn nhóm")
        select_btn.clicked.connect(self.accept_selection)
        
        button_layout.addWidget(create_btn)
        button_layout.addStretch()
        button_layout.addWidget(select_btn)
        layout.addLayout(button_layout)
        
        self.load_groups()

    def load_groups(self):
        """Tải danh sách các nhóm mà người dùng là thành viên."""
        self.group_list_widget.clear()
        try:
            db = Database()
            groups = db.get_groups_for_user(self.user_id)
            
            for group_id, group_name in groups:
                item = QListWidgetItem(group_name)
                item.setData(Qt.UserRole, group_id) # Lưu group_id vào item
                self.group_list_widget.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể tải danh sách nhóm: {e}")

    def create_new_group(self):
        """Mở hộp thoại để tạo nhóm mới."""
        group_name, ok = QInputDialog.getText(self, "Tạo Nhóm Mới", "Nhập tên nhóm:")
        if ok and group_name:
            try:
                db = Database()
                gid = db.create_group(group_name, self.user_id)
                if gid:
                    # đảm bảo leader ở trong group_members
                    db.add_group_member(gid, self.user_id)
                    QMessageBox.information(self, "Thành công", f"Đã tạo nhóm '{group_name}' thành công.")
                    self.load_groups()
                else:
                    QMessageBox.warning(self, "Lỗi", "Không thể tạo nhóm (có thể tên trùng).")
            except Exception as e:
                 QMessageBox.critical(self, "Lỗi CSDL", f"Không thể tạo nhóm: {e}")

    def accept_selection(self):
        """Lưu lại nhóm được chọn và đóng dialog."""
        current_item = self.group_list_widget.currentItem()
        if current_item:
            group_id = current_item.data(Qt.UserRole)
            group_name = current_item.text()
            self.selected_group = (group_id, group_name)
            self.accept() # Đóng dialog với kết quả OK
        else:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn một nhóm từ danh sách.")

class MemberListDialog(QDialog):
    """Cửa sổ hiển thị danh sách thành viên trong nhóm."""
    def __init__(self, group_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Danh sách thành viên")
        self.setMinimumSize(350, 400)

        layout = QVBoxLayout(self)
        self.member_list = QListWidget()
        layout.addWidget(self.member_list)

        try:
            db = Database()
            members = db.get_group_members(group_id)
            for row in members:
                # Hỗ trợ các hàng là (user_id, user_name) hoặc (user_id, user_name, email)
                try:
                    uid = row[0]
                    name = row[1] if len(row) > 1 else str(uid)
                    email = row[2] if len(row) > 2 else None
                except Exception:
                    # fallback: bỏ qua hàng malformed
                    continue
                if not email:
                    # thử lấy email từ user record nếu thiếu
                    try:
                        user = db.get_user_by_id(uid)
                        email = user[2] if user and len(user) > 2 else 'unknown'
                    except Exception:
                        email = 'unknown'
                self.member_list.addItem(f"{name} ({email})")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể tải danh sách thành viên: {e}")

class AddMemberDialog(QDialog):
    """Cửa sổ để thêm thành viên mới vào nhóm."""
    member_added = pyqtSignal()

    def __init__(self, group_id, parent=None):
        super().__init__(parent)
        self.group_id = group_id
        self.setWindowTitle("Thêm thành viên")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Email của người dùng cần thêm:"))
        self.email_input = QLineEdit()
        layout.addWidget(self.email_input)
        
        add_btn = QPushButton("Thêm")
        add_btn.clicked.connect(self.add_member)
        layout.addWidget(add_btn)

    def add_member(self):
        email = self.email_input.text().strip()
        if not email:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập email.")
            return 

        try:
            db = Database()
            user_result = db.get_user_by_email(email)
            if not user_result:
                QMessageBox.warning(self, "Không tìm thấy", f"Không tìm thấy người dùng với email '{email}'.")
                return
            user_id_to_add = user_result[0]
            try:
                db.add_group_member(self.group_id, user_id_to_add)
                QMessageBox.information(self, "Thành công", "Đã thêm thành viên mới vào nhóm.")
                self.member_added.emit()
                self.accept()
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không thể thêm thành viên: {e}")
            except Exception as e:
                # Lỗi toàn vẹn hoặc lỗi DB khác
                QMessageBox.warning(self, "Lỗi", f"Không thể thêm thành viên: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể truy xuất dữ liệu: {e}")