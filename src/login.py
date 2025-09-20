import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint, QSize
from PyQt5.QtGui import QFont, QColor

class LoginRegisterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.container_width = 900
        self.container_height = 500
        self.form_width = self.container_width // 2
        
        self.setWindowTitle("Login Page | Caged Coder")
        self.setGeometry(100, 100, self.container_width, self.container_height)
        self.setFixedSize(self.container_width, self.container_height) # Giữ kích thước cố định

        # Main Container
        self.main_container = QWidget()
        self.main_container.setStyleSheet("""
            background-color: white;
            border-radius: 30px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.35);
        """)
        self.setCentralWidget(self.main_container)
        
        # Base layout for forms and toggle panel
        self.base_layout = QHBoxLayout(self.main_container)
        self.base_layout.setSpacing(0)
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Forms (Sign-in & Sign-up) ---
        self.stacked_forms = QStackedWidget()
        self.stacked_forms.setFixedSize(self.container_width, self.container_height) # Kích thước toàn bộ để chứa cả 2 form
        self.stacked_forms.setStyleSheet("background-color: transparent;")
        
        self.sign_in_form = self.create_form("Sign In", "or use your email password")
        self.sign_up_form = self.create_form("Create Account", "or use your email for registration")
        
        self.stacked_forms.addWidget(self.sign_in_form)
        self.stacked_forms.addWidget(self.sign_up_form)
        self.base_layout.addWidget(self.stacked_forms)
        
        # --- Toggle Panel ---
        self.toggle_panel = QWidget()
        self.toggle_panel.setFixedSize(self.form_width, self.container_height)
        self.toggle_panel.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5c6bc0, stop:1 #2da0a8);
            color: white;
            border-radius: 0 150px 100px 0;
            z-index: 1000;
        """)
        self.toggle_layout = QStackedWidget(self.toggle_panel)
        self.toggle_layout.setFixedSize(self.form_width, self.container_height)
        
        # Toggle Panel Left
        self.toggle_left = self.create_toggle_panel("Welcome Back!", "Enter your personal details to use all of site features", "Sign In")
        self.toggle_layout.addWidget(self.toggle_left)
        
        # Toggle Panel Right
        self.toggle_right = self.create_toggle_panel("Hello, Friend!", "Register with your personal details to use all of site features", "Sign Up")
        self.toggle_layout.addWidget(self.toggle_right)
        
        self.base_layout.addWidget(self.toggle_panel)
        self.base_layout.setAlignment(self.toggle_panel, Qt.AlignRight)
        
        # Set initial state
        self.stacked_forms.setCurrentWidget(self.sign_in_form)
        self.toggle_layout.setCurrentWidget(self.toggle_right)
        
        # --- Connect Buttons ---
        self.toggle_left.findChild(QPushButton).clicked.connect(self.show_sign_in)
        self.toggle_right.findChild(QPushButton).clicked.connect(self.show_sign_up)
        
        # --- Animations ---
        self.animation_form = QPropertyAnimation(self.stacked_forms, b"pos")
        self.animation_form.setDuration(600)
        
        self.animation_toggle = QPropertyAnimation(self.toggle_panel, b"pos")
        self.animation_toggle.setDuration(600)

    def create_form(self, title, subtitle):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        
        title_label = QLabel(f"<h1>{title}</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Social Icons
        social_layout = QHBoxLayout()
        for _ in range(4):
            icon_label = QLabel("Icon") # Placeholder for social icons
            icon_label.setFixedSize(40, 40)
            icon_label.setStyleSheet("border: 1px solid #ccc; border-radius: 20px; text-align: center;")
            social_layout.addWidget(icon_label)
        social_layout.setAlignment(Qt.AlignCenter)
        layout.addLayout(social_layout)
        
        subtitle_label = QLabel(f"<p>{subtitle}</p>")
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)
        
        layout.addWidget(QLineEdit(placeholderText="Name" if "Create" in title else "Email"))
        if "Create" in title:
            layout.addWidget(QLineEdit(placeholderText="Email"))
        layout.addWidget(QLineEdit(placeholderText="Password"))
        
        if "Sign In" in title:
            layout.addWidget(QLabel("<a href='#'>Forgot Your Password?</a>"))
        
        button = QPushButton(title)
        button.setFixedSize(120, 30)
        button.setStyleSheet("background-color: #2da0a8; color: white; border: none; font-weight: 600; text-transform: uppercase; border-radius: 8px;")
        layout.addWidget(button, alignment=Qt.AlignCenter)
        
        return widget

    def create_toggle_panel(self, title, subtitle, button_text):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        
        title_label = QLabel(f"<h1>{title}</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel(f"<p>{subtitle}</p>")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)
        
        button = QPushButton(button_text)
        button.setFixedSize(120, 30)
        button.setStyleSheet("background-color: transparent; border: 1px solid white; color: white; font-weight: 600; text-transform: uppercase; border-radius: 8px;")
        layout.addWidget(button, alignment=Qt.AlignCenter)
        
        return widget

    def show_sign_up(self):
        self.stacked_forms.setCurrentWidget(self.sign_up_form)
        self.toggle_layout.setCurrentWidget(self.toggle_left)
        
        self.animate_transition(is_sign_up=True)

    def show_sign_in(self):
        self.stacked_forms.setCurrentWidget(self.sign_in_form)
        self.toggle_layout.setCurrentWidget(self.toggle_right)
        
        self.animate_transition(is_sign_up=False)

    def animate_transition(self, is_sign_up):
        # Tính toán vị trí ban đầu và kết thúc
        start_pos_forms = self.stacked_forms.pos()
        end_pos_forms = QPoint(self.form_width if is_sign_up else 0, 0)
        
        start_pos_toggle = self.toggle_panel.pos()
        end_pos_toggle = QPoint(0 if is_sign_up else self.form_width, 0)
        
        # Animation cho Forms
        self.animation_form.setStartValue(start_pos_forms)
        self.animation_form.setEndValue(end_pos_forms)
        
        # Animation cho Toggle Panel
        self.animation_toggle.setStartValue(start_pos_toggle)
        self.animation_toggle.setEndValue(end_pos_toggle)
        
        self.animation_form.start()
        self.animation_toggle.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWidget {
            font-family: 'Montserrat', sans-serif;
        }
        QPushButton {
            cursor: pointer;
        }
    """)
    window = LoginRegisterApp()
    window.show()
    sys.exit(app.exec_())