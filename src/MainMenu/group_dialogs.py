import sqlite3
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
                             QPushButton, QInputDialog, QMessageBox, QLabel, QLineEdit)
from PyQt5.QtCore import Qt

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
            conn = sqlite3.connect("todolist_database.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT g.group_id, g.group_name 
                FROM groups g
                JOIN group_members gm ON g.group_id = gm.group_id
                WHERE gm.user_id = ?
            """, (self.user_id,))
            groups = cursor.fetchall()
            conn.close()
            
            for group_id, group_name in groups:
                item = QListWidgetItem(group_name)
                item.setData(Qt.UserRole, group_id) # Lưu group_id vào item
                self.group_list_widget.addItem(item)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể tải danh sách nhóm: {e}")

    def create_new_group(self):
        """Mở hộp thoại để tạo nhóm mới."""
        group_name, ok = QInputDialog.getText(self, "Tạo Nhóm Mới", "Nhập tên nhóm:")
        if ok and group_name:
            try:
                conn = sqlite3.connect("todolist_database.db")
                cursor = conn.cursor()
                # Thêm nhóm mới với user hiện tại là leader
                cursor.execute("INSERT INTO groups (group_name, leader_id) VALUES (?, ?)", (group_name, self.user_id))
                group_id = cursor.lastrowid # Lấy id của nhóm vừa tạo
                
                # Tự động thêm leader vào bảng group_members
                cursor.execute("INSERT INTO group_members (user_id, group_id) VALUES (?, ?)",
                               (self.user_id, group_id, "Leader"))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Thành công", f"Đã tạo nhóm '{group_name}' thành công.")
                self.load_groups() # Tải lại danh sách
            except sqlite3.IntegrityError:
                 QMessageBox.warning(self, "Lỗi", "Tên nhóm này đã tồn tại.")
            except sqlite3.Error as e:
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
            conn = sqlite3.connect("todolist_database.db")
            cursor = conn.cursor()
            # Lấy tên, email của các thành viên
            cursor.execute("""
                SELECT u.user_name, u.email
                FROM users u
                JOIN group_members gm ON u.user_id = gm.user_id
                WHERE gm.group_id = ?
            """, (group_id,))
            members = cursor.fetchall()
            conn.close()
            for name, email in members:
                self.member_list.addItem(f"{name} ({email})")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể tải danh sách thành viên: {e}")

class AddMemberDialog(QDialog):
    """Cửa sổ để thêm thành viên mới vào nhóm."""
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
            conn = sqlite3.connect("todolist_database.db")
            cursor = conn.cursor()
            
            # Tìm user_id từ email
            cursor.execute("SELECT user_id, user_name FROM users WHERE email = ?", (email,))
            user_result = cursor.fetchone()
            
            if not user_result:
                QMessageBox.warning(self, "Không tìm thấy", f"Không tìm thấy người dùng với email '{email}'.")
                conn.close()
                return

            user_id_to_add = user_result[0]
            
            # Thêm user vào bảng group_members với vai trò Member
            cursor.execute("INSERT INTO group_members (user_id, group_id) VALUES (?, ?)",
                           (user_id_to_add, self.group_id))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Thành công", "Đã thêm thành viên mới vào nhóm.")
            self.accept() # Đóng dialog
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Lỗi", "Người dùng này đã ở trong nhóm.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể thêm thành viên: {e}")