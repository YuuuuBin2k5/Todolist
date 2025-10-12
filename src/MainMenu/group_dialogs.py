# --- Nhập các thư viện và module cần thiết ---
from Managers.database_manager import Database  # Lớp quản lý cơ sở dữ liệu

# Nhập các lớp widget và công cụ từ PyQt5
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
                             QPushButton, QInputDialog, QMessageBox, QLabel, QLineEdit)
from PyQt5.QtCore import Qt  # Dùng cho các hằng số của Qt như Qt.UserRole

# ==============================================================================
# LỚP 1: GroupSelectionDialog - Cửa sổ chọn hoặc tạo nhóm
# ==============================================================================
class GroupSelectionDialog(QDialog):
    """
    Cửa sổ cho phép người dùng xem danh sách các nhóm họ tham gia,
    chọn một nhóm, hoặc tạo một nhóm mới.
    """
    def __init__(self, current_user_id, parent=None):
        """
        Khởi tạo cửa sổ.
        
        Args:
            current_user_id (int): ID của người dùng đang đăng nhập.
            parent (QWidget): Widget cha.
        """
        super().__init__(parent)
        self.current_user_id = current_user_id  # Lưu ID người dùng
        self.selected_group = None  # Sẽ lưu (group_id, group_name) khi người dùng chọn

        self.setWindowTitle("Quản lý Nhóm")  # Đặt tiêu đề cho cửa sổ
        self.setMinimumSize(400, 300)  # Đặt kích thước tối thiểu

        # Layout chính, sắp xếp các thành phần theo chiều dọc
        main_layout = QVBoxLayout(self)
        
        # Danh sách hiển thị các nhóm
        self.group_list_widget = QListWidget()
        # Gắn sự kiện double-click vào một mục trong danh sách để chọn nhóm đó
        self.group_list_widget.itemDoubleClicked.connect(self.accept_selection)
        main_layout.addWidget(self.group_list_widget)
        
        # Layout cho các nút bấm, sắp xếp theo chiều ngang
        button_layout = QHBoxLayout()
        create_group_button = QPushButton("Tạo nhóm mới")
        create_group_button.clicked.connect(self.create_new_group)  # Gắn sự kiện click
        
        select_group_button = QPushButton("Chọn nhóm")
        select_group_button.clicked.connect(self.accept_selection)  # Gắn sự kiện click

        button_layout.addWidget(create_group_button)  # Thêm nút tạo nhóm
        button_layout.addStretch()  # Thêm khoảng trống co giãn để đẩy nút "Chọn" sang phải
        button_layout.addWidget(select_group_button)  # Thêm nút chọn nhóm
        
        main_layout.addLayout(button_layout)  # Thêm layout nút bấm vào layout chính
        
        self.load_user_groups()  # Tải danh sách nhóm ngay khi cửa sổ được tạo

    def load_user_groups(self):
        """
        Tải danh sách các nhóm mà người dùng là thành viên từ CSDL và hiển thị lên QListWidget.
        """
        self.group_list_widget.clear()  # Xóa danh sách cũ trước khi tải lại
        try:
            db_manager = Database()  # Tạo đối tượng quản lý CSDL
            # Lấy danh sách nhóm của người dùng
            groups = db_manager.get_groups_for_user(self.current_user_id)
            
            # Lặp qua từng nhóm và thêm vào danh sách hiển thị
            for group_id, group_name in groups:
                list_item = QListWidgetItem(group_name)  # Tạo một mục mới với tên nhóm
                # Lưu trữ group_id ẩn trong item, để có thể lấy lại sau này
                list_item.setData(Qt.UserRole, group_id) 
                self.group_list_widget.addItem(list_item)
        except Exception as error:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể tải danh sách nhóm: {error}")

    def create_new_group(self):
        """
        Mở một hộp thoại nhỏ để người dùng nhập tên và tạo nhóm mới.
        """
        # Hiển thị dialog của Qt để người dùng nhập văn bản
        group_name, is_ok_pressed = QInputDialog.getText(self, "Tạo Nhóm Mới", "Nhập tên nhóm:")
        
        # Nếu người dùng nhấn "OK" và đã nhập tên nhóm
        if is_ok_pressed and group_name:
            try:
                db_manager = Database()
                # Gọi hàm tạo nhóm trong CSDL, người tạo sẽ là trưởng nhóm (leader)
                new_group_id = db_manager.create_group(group_name, self.current_user_id)
                
                if new_group_id:
                    # Quan trọng: Sau khi tạo nhóm, phải thêm chính trưởng nhóm vào danh sách thành viên
                    db_manager.add_group_member(new_group_id, self.current_user_id)
                    QMessageBox.information(self, "Thành công", f"Đã tạo nhóm '{group_name}' thành công.")
                    self.load_user_groups()  # Tải lại danh sách nhóm để hiển thị nhóm mới
                else:
                    QMessageBox.warning(self, "Lỗi", "Không thể tạo nhóm (có thể tên đã tồn tại).")
            except Exception as error:
                QMessageBox.critical(self, "Lỗi CSDL", f"Không thể tạo nhóm: {error}")

    def accept_selection(self):
        """
        Xác nhận việc chọn một nhóm, lưu thông tin và đóng cửa sổ.
        """
        current_item = self.group_list_widget.currentItem()  # Lấy mục đang được chọn
        if current_item:
            # Lấy group_id đã được lưu ẩn trong item
            group_id = current_item.data(Qt.UserRole)
            group_name = current_item.text()
            # Lưu lại thông tin nhóm đã chọn
            self.selected_group = (group_id, group_name)
            self.accept()  # Đóng cửa sổ và trả về kết quả thành công (Accepted)
        else:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn một nhóm từ danh sách.")

# ==============================================================================
# LỚP 2: MemberListDialog - Cửa sổ hiển thị danh sách thành viên
# ==============================================================================
class MemberListDialog(QDialog):
    """
    Một cửa sổ đơn giản chỉ để hiển thị danh sách các thành viên trong một nhóm.
    """
    def __init__(self, group_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Danh sách thành viên")
        self.setMinimumSize(350, 400)

        main_layout = QVBoxLayout(self)
        self.member_list_widget = QListWidget()  # Danh sách để hiển thị
        main_layout.addWidget(self.member_list_widget)

        try:
            db_manager = Database()
            # Lấy danh sách thành viên từ CSDL
            members = db_manager.get_group_members(group_id)
            # Lặp qua và thêm thông tin mỗi thành viên vào danh sách
            for user_id, user_name, user_email in members:
                self.member_list_widget.addItem(f"{user_name} ({user_email})")
        except Exception as error:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể tải danh sách thành viên: {error}")

# ==============================================================================
# LỚP 3: AddMemberDialog - Cửa sổ thêm thành viên mới
# ==============================================================================
class AddMemberDialog(QDialog):
    """
    Cửa sổ cho phép trưởng nhóm thêm một thành viên mới vào nhóm bằng email.
    """
    def __init__(self, target_group_id, parent=None):
        super().__init__(parent)
        self.target_group_id = target_group_id  # Lưu ID của nhóm cần thêm thành viên
        self.setWindowTitle("Thêm thành viên")

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(QLabel("Email của người dùng cần thêm:"))
        
        self.email_input = QLineEdit()  # Ô nhập liệu cho email
        main_layout.addWidget(self.email_input)
        
        add_button = QPushButton("Thêm")
        add_button.clicked.connect(self.add_member_to_group)
        main_layout.addWidget(add_button)

    def add_member_to_group(self):
        """
        Xử lý logic khi nút "Thêm" được nhấn.
        """
        email_to_add = self.email_input.text().strip()  # Lấy email từ ô nhập liệu
        
        # Kiểm tra xem người dùng có nhập email không
        if not email_to_add:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập email.")
            return 

        try:
            db_manager = Database()
            # Bước 1: Tìm user_id dựa trên email
            user_to_add = db_manager.get_user_by_email(email_to_add)
            
            if not user_to_add:
                QMessageBox.warning(self, "Không tìm thấy", f"Không tìm thấy người dùng với email '{email_to_add}'.")
                return
            
            user_id_to_add = user_to_add[0]  # Lấy user_id từ kết quả trả về
            
            # Bước 2: Thêm user_id vào bảng group_members
            db_manager.add_group_member(self.target_group_id, user_id_to_add)
            QMessageBox.information(self, "Thành công", "Đã thêm thành viên mới vào nhóm.")
            self.accept()  # Đóng cửa sổ nếu thêm thành công
        
        except Exception as error:
            # Bắt các lỗi chung khác từ CSDL (ví dụ: người dùng đã ở trong nhóm)
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể thêm thành viên: {error}")