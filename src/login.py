import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint, QSize
from PyQt5.QtGui import QFont, QColor, QPalette, QPixmap

# Import các hằng số từ file config.py.
from config import *

class LoginRegisterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Login/Register")
        
        self.setGeometry(100, 100, CONTAINER_WIDTH, CONTAINER_HEIGHT)
        self.setFixedSize(CONTAINER_WIDTH, CONTAINER_HEIGHT)

        self.main_container = QWidget()
        self.main_container.setStyleSheet(f"""
            background-color: {COLOR_WHITE};
            border-radius: 30px;
            box-shadow: 0 5px 15px {COLOR_SHADOW};
        """)
        self.setCentralWidget(self.main_container)
        
        self.base_layout = QHBoxLayout(self.main_container)
        self.base_layout.setSpacing(0)
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stacked_forms = QStackedWidget()
        
        self.stacked_forms.setFixedSize(FORM_WIDTH, CONTAINER_HEIGHT)
        self.stacked_forms.setStyleSheet("background-color: transparent;")
        
        self.sign_in_form = self.create_form("Sign In", "or use your email password")
        self.sign_up_form = self.create_form("Create Account", "or use your email for registration")
        
        self.stacked_forms.addWidget(self.sign_in_form)
        self.stacked_forms.addWidget(self.sign_up_form)
        
        self.base_layout.addWidget(self.stacked_forms)
        
        self.toggle_panel = QWidget()
        self.toggle_panel.setFixedSize(TOGGLE_PANEL_WIDTH, CONTAINER_HEIGHT)
        
        # Đặt border-radius ban đầu cho panel khi nó ở bên phải (trạng thái Sign In).
        # Đã cập nhật để bo tròn cả 4 góc.
        self.toggle_panel.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_PRIMARY_BLUE}, stop:1 {COLOR_SECONDARY_BLUE});
            color: white;
            border-top-left-radius: 150px;
            border-bottom-left-radius: 100px;
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
            z-index: 1000;
        """)
        
        self.toggle_layout = QStackedWidget(self.toggle_panel)
        self.toggle_layout.setFixedSize(TOGGLE_PANEL_WIDTH, CONTAINER_HEIGHT)
        self.toggle_layout.setStyleSheet("background-color: transparent;")
        
        self.toggle_left = self.create_toggle_panel("Welcome Back!", "Enter your personal details to use all of site features", "Sign In")
        self.toggle_layout.addWidget(self.toggle_left)
        
        self.toggle_right = self.create_toggle_panel("Hello, Friend!", "Register with your personal details to use all of site features", "Sign Up")
        self.toggle_layout.addWidget(self.toggle_right)
        
        self.base_layout.addWidget(self.toggle_panel)
        self.base_layout.setAlignment(self.toggle_panel, Qt.AlignRight)
        
        self.stacked_forms.setCurrentWidget(self.sign_in_form)
        self.toggle_layout.setCurrentWidget(self.toggle_right)
        
        self.toggle_left.findChild(QPushButton).clicked.connect(self.show_sign_in)
        self.toggle_right.findChild(QPushButton).clicked.connect(self.show_sign_up)
        
        self.animation_form = QPropertyAnimation(self.stacked_forms, b"pos")
        self.animation_form.setDuration(ANIMATION_DURATION_MS)
        
        self.animation_toggle = QPropertyAnimation(self.toggle_panel, b"pos")
        self.animation_toggle.setDuration(ANIMATION_DURATION_MS)

    def create_form(self, title, subtitle):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        # Thiết lập khoảng cách giữa các widget trong form
        layout.setSpacing(10)
        layout.setContentsMargins(30, 0, 30, 0)
        layout.setAlignment(Qt.AlignCenter)
        
        title_label = QLabel(f"<h1>{title}</h1>")
        # Điều chỉnh kích thước và độ đậm của tiêu đề
        title_label.setStyleSheet("font-size: 24px; font-weight: 700; color: #333;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        social_layout = QHBoxLayout()
        # Căn giữa các icon mạng xã hội
        social_layout.setAlignment(Qt.AlignCenter)
        social_layout.setSpacing(10)
        # Thêm các icon mạng xã hội 
        social_icons = ["./assets/images/google_icon.png", "./assets/images/facebook_icon.png", "./assets/images/instagram_icon.png", "./assets/images/github_icon.png"]
        for icon_path in social_icons:
            icon_label = QLabel()
            icon_pixmap = QPixmap(icon_path)
            icon_pixmap_scaled = icon_pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap_scaled)
            icon_label.setFixedSize(40, 40)
            icon_label.setAlignment(Qt.AlignCenter)

            icon_label.setStyleSheet("""
                border: 1px solid {COLOR_GRAY};
                border-radius: 20px;
            """)
            social_layout.addWidget(icon_label)
            
        layout.addLayout(social_layout)
        
        subtitle_label = QLabel(f"<p>{subtitle}</p>")
        # Điều chỉnh kích thước chữ của phụ đề
        subtitle_label.setStyleSheet("font-size: 14px; color: #555;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Căn chỉnh kích thước và style cho các ô nhập liệu
        email_input = QLineEdit(placeholderText="Email")
        email_input.setStyleSheet("padding: 10px; height: 40px; border: none; background-color: #f3f3f3; border-radius: 8px;")
        layout.addWidget(email_input)
        
        if "Create" in title:
            name_input = QLineEdit(placeholderText="Name")
            name_input.setStyleSheet("padding: 10px; height: 40px; border: none; background-color: #f3f3f3; border-radius: 8px;")
            layout.addWidget(name_input)
            
            password_input = QLineEdit(placeholderText="Password")
            password_input.setStyleSheet("padding: 10px; height: 40px; border: none; background-color: #f3f3f3; border-radius: 8px;")
            layout.addWidget(password_input)
        else:
            password_input = QLineEdit(placeholderText="Password")
            password_input.setStyleSheet("padding: 10px; height: 40px; border: none; background-color: #f3f3f3; border-radius: 8px;")
            layout.addWidget(password_input)
        
        if "Sign In" in title:
            forgot_password_label = QLabel("<a href='#'>Forgot Your Password?</a>")
            forgot_password_label.setStyleSheet("font-size: 12px; margin-top: 10px; margin-bottom: 20px;")
            layout.addWidget(forgot_password_label, alignment=Qt.AlignCenter)
        
        button = QPushButton(title)
        button.setFixedSize(120, 30)
        button.setStyleSheet(f"""
            background-color: {COLOR_SECONDARY_BLUE};
            color: {COLOR_WHITE};
            border: none;
            font-weight: 600;
            text-transform: uppercase;
            border-radius: 8px;
        """)
        layout.addWidget(button, alignment=Qt.AlignCenter)
        
        return widget

    def create_toggle_panel(self, title, subtitle, button_text):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        title_label = QLabel(f"<h1>{title}</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title_label)
        
        subtitle_label = QLabel(f"<p>{subtitle}</p>")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet("font-size: 14px; padding: 0 20px;")
        layout.addWidget(subtitle_label)
        
        button = QPushButton(button_text)
        button.setFixedSize(120, 30)
        button.setStyleSheet(f"background-color: transparent; border: 1px solid {COLOR_WHITE}; color: {COLOR_WHITE}; font-weight: 600; text-transform: uppercase; border-radius: 8px;")
        layout.addWidget(button, alignment=Qt.AlignCenter)
        
        return widget

    def show_sign_up(self):
        self.stacked_forms.setCurrentWidget(self.sign_up_form)
        self.toggle_layout.setCurrentWidget(self.toggle_left)
        
        # Đã cập nhật để bo tròn cả 4 góc khi panel di chuyển sang trái
        self.toggle_panel.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_PRIMARY_BLUE_PURPLE}, stop:1 {COLOR_SECONDARY_BLUE_PURPLE});
            color: white;
            border-top-right-radius: 150px;
            border-bottom-right-radius: 100px;
            border-top-left-radius: 10px;
            border-bottom-left-radius: 10px;
            z-index: 1000;
        """)
        self.animate_transition(is_sign_up=True)

    def show_sign_in(self):
        self.stacked_forms.setCurrentWidget(self.sign_in_form)
        self.toggle_layout.setCurrentWidget(self.toggle_right)
        
        # Đã cập nhật để bo tròn cả 4 góc khi panel quay về bên phải
        self.toggle_panel.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_PRIMARY_BLUE}, stop:1 {COLOR_SECONDARY_BLUE});
            color: white;
            border-top-left-radius: 150px;
            border-bottom-left-radius: 100px;
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
            z-index: 1000;
        """)
        self.animate_transition(is_sign_up=False)

    def animate_transition(self, is_sign_up):
        start_pos_forms = self.stacked_forms.pos()
        end_pos_forms = QPoint(FORM_WIDTH if is_sign_up else 0, 0)
        
        start_pos_toggle = self.toggle_panel.pos()
        end_pos_toggle = QPoint(0 if is_sign_up else FORM_WIDTH, 0)
        
        self.animation_form.setStartValue(start_pos_forms)
        self.animation_form.setEndValue(end_pos_forms)
        
        self.animation_toggle.setStartValue(start_pos_toggle)
        self.animation_toggle.setEndValue(end_pos_toggle)
        
        self.animation_form.start()
        self.animation_toggle.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWidget {
            font-family: 'Times New Roman', serif;
        }
        QPushButton {
            cursor: pointer;
        }
    """)
    window = LoginRegisterApp()
    window.show()
    sys.exit(app.exec_())
