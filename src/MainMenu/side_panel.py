# FILE: src/MainMenu/side_panel.py

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPainter, QBrush, QColor, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal

class SidePanel(QFrame):
    personal_area_requested = pyqtSignal()
    group_area_requested = pyqtSignal()
    member_list_requested = pyqtSignal()
    add_member_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedWidth(300)
        self.setObjectName("SidePanel")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(15)

        self.avatar = QLabel()
        self.avatar.setFixedSize(120, 120)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.create_circular_avatar()
        self.layout.addWidget(self.avatar, 0, Qt.AlignCenter)
        self.layout.addSpacing(15)

        name_title_label = QLabel("TÊN")
        self.name_value_label = QLabel("Đang tải...")
        role_title_label = QLabel("VAI TRÒ")
        self.role_value_label = QLabel("Đang tải...")
        self.name_value_label.setObjectName("InfoValueLabel")
        self.role_value_label.setObjectName("InfoValueLabel")
        self.layout.addWidget(name_title_label)
        self.layout.addWidget(self.name_value_label)
        self.layout.addSpacing(10)
        self.layout.addWidget(role_title_label)
        self.layout.addWidget(self.role_value_label)
        self.layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.personal_btn = QPushButton("KHU VỰC CÁ NHÂN")
        self.group_btn = QPushButton("KHU VỰC NHÓM")
        self.personal_btn.clicked.connect(self.personal_area_requested.emit)
        self.group_btn.clicked.connect(self.group_area_requested.emit)
        self.layout.addWidget(self.personal_btn)
        self.layout.addWidget(self.group_btn)
        
        self.member_list_btn = QPushButton("Danh sách thành viên")
        self.add_member_btn = QPushButton("Thêm thành viên")
        self.member_list_btn.clicked.connect(self.member_list_requested.emit)
        self.add_member_btn.clicked.connect(self.add_member_requested.emit)
        self.layout.addWidget(self.member_list_btn)
        self.layout.addWidget(self.add_member_btn)
        self.member_list_btn.hide()
        self.add_member_btn.hide()
        
        self.layout.addStretch(1)

        self.exit_btn = QPushButton("EXIT")
        self.exit_btn.setObjectName("ExitButton")
        self.layout.addWidget(self.exit_btn)

    def set_user_info(self, user_name, user_role):
        self.name_value_label.setText(user_name)
        self.role_value_label.setText(user_role)

    def update_view(self, view_mode, is_leader=False):
        """Chỉ cần enable/disable các nút, CSS sẽ tự xử lý giao diện."""
        if view_mode == 'personal':
            self.personal_btn.setEnabled(False)
            self.group_btn.setEnabled(True)
            self.member_list_btn.hide()
            self.add_member_btn.hide()
        elif view_mode == 'group':
            self.personal_btn.setEnabled(True)
            self.group_btn.setEnabled(False)
            self.member_list_btn.show()
            self.add_member_btn.setVisible(is_leader)

    def create_circular_avatar(self):
        pixmap = QPixmap(self.avatar.size())
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor("#cccccc")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.avatar.width(), self.avatar.height())
        painter.end()
        self.avatar.setPixmap(pixmap)