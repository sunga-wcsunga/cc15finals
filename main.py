import sys
from database import get_connection
from PyQt6.QtWidgets import (
   QApplication, QMainWindow, QWidget, QFrame, QPushButton, QLabel,
   QStackedWidget, QTableView, QLineEdit, QDateTimeEdit, QDialog,
   QVBoxLayout, QHBoxLayout, QFormLayout, QTextEdit, QComboBox,
   QMessageBox, QHeaderView, QAbstractItemView, QDateEdit, QSpinBox,
   QDialogButtonBox, QSizePolicy
)
from PyQt6.QtCore import (
   Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel,
   QDateTime, QDate
)
from PyQt6.QtGui import QFont, QColor, QPalette


# ─────────────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────────────
def init_db():
   conn = get_connection()
   c = conn.cursor()
   c.execute("""
       CREATE TABLE IF NOT EXISTS patients (
           patient_id      INT AUTO_INCREMENT PRIMARY KEY,
           full_name       VARCHAR(100) NOT NULL,
           age             INTEGER,
           phone           VARCHAR(20),
           address         VARCHAR(255),
           medical_history TEXT,
           dental_history  TEXT,
           diagnosis       TEXT,
           last_visit      DATE,
           next_appt       DATE,
           status          VARCHAR(20) DEFAULT 'Active'
       )
   """)
   c.execute("""
       CREATE TABLE IF NOT EXISTS appointments (
           appt_id       INT AUTO_INCREMENT PRIMARY KEY,
           patient_name  VARCHAR(100),
           dentist_name  VARCHAR(100),
           appt_datetime DATETIME
       )
   """)

   c.execute("""
       CREATE TABLE IF NOT EXISTS users (
           username VARCHAR(100) PRIMARY KEY,
           email VARCHAR(100),
           password VARCHAR(100),
           role VARCHAR(50)
       )
   """)

   conn.commit()
   conn.close()

# ─────────────────────────────────────────────
#  REGISTER AND LOGIN
# ─────────────────────────────────────────────
def register_user(username, email, password, role):
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        """
        INSERT INTO users(username, email, password, role)
        VALUES (%s, %s, %s, %s)
        """,
        (username, email, password, role)
    )

    conn.commit()
    conn.close()

def login_user(username, password):
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        """
        SELECT * FROM users
        WHERE username=%s AND password=%s
        """,
        (username, password)
    )

    user = c.fetchone()
    conn.close()
    return user


# ─────────────────────────────────────────────
#  TABLE MODELS
# ─────────────────────────────────────────────
class PatientTableModel(QAbstractTableModel):
   HEADERS = ["ID", "Full Name", "Age", "Phone", "Last Visit", "Next Appt", "Status"]


   def __init__(self):
       super().__init__()
       self._data = []
       self.refresh()


   def refresh(self):
       conn = get_connection()
       c = conn.cursor()
       c.execute(
           "SELECT patient_id, full_name, age, phone, last_visit, next_appt, status "
           "FROM patients ORDER BY patient_id"
       )
       self._data = c.fetchall()
       conn.close()
       self.layoutChanged.emit()


   def rowCount(self, parent=QModelIndex()):
       return len(self._data)


   def columnCount(self, parent=QModelIndex()):
       return len(self.HEADERS)


   def data(self, index, role=Qt.ItemDataRole.DisplayRole):
       if not index.isValid():
           return None
       row = self._data[index.row()]
       col = index.column()
       if role == Qt.ItemDataRole.DisplayRole:
           val = row[col]
           return str(val) if val is not None else ""
       if role == Qt.ItemDataRole.TextAlignmentRole:
           return Qt.AlignmentFlag.AlignCenter
       if role == Qt.ItemDataRole.BackgroundRole:
           status = row[6]
           if status == "Active":
               return QColor("#d4f8e8")
           elif status == "Pending":
               return QColor("#fff3cd")
           elif status == "Inactive":
               return QColor("#fde8e8")
       return None


   def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
       if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
           return self.HEADERS[section]
       return None


   def get_patient_id(self, row):
       if 0 <= row < len(self._data):
           return self._data[row][0]
       return None




class AppointmentTableModel(QAbstractTableModel):
   HEADERS = ["ID", "Patient Name", "Dentist", "Date & Time"]


   def __init__(self):
       super().__init__()
       self._data = []
       self.refresh()


   def refresh(self):
       conn = get_connection()
       c = conn.cursor()
       c.execute(
           "SELECT appt_id, patient_name, dentist_name, appt_datetime "
           "FROM appointments ORDER BY appt_datetime"
       )
       self._data = c.fetchall()
       conn.close()
       self.layoutChanged.emit()


   def rowCount(self, parent=QModelIndex()):
       return len(self._data)


   def columnCount(self, parent=QModelIndex()):
       return len(self.HEADERS)


   def data(self, index, role=Qt.ItemDataRole.DisplayRole):
       if not index.isValid():
           return None
       row = self._data[index.row()]
       if role == Qt.ItemDataRole.DisplayRole:
           val = row[index.column()]
           return str(val) if val is not None else ""
       if role == Qt.ItemDataRole.TextAlignmentRole:
           return Qt.AlignmentFlag.AlignCenter
       return None


   def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
       if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
           return self.HEADERS[section]
       return None




# ─────────────────────────────────────────────
#  ADD / EDIT PATIENT DIALOG
# ─────────────────────────────────────────────
class PatientDialog(QDialog):
   def __init__(self, parent=None, patient_id=None):
       super().__init__(parent)
       self.patient_id = patient_id
       self.setWindowTitle("Edit Patient Record" if patient_id else "Add New Patient")
       self.setFixedWidth(540)
       self.setStyleSheet("""
           QDialog   { background-color: #ffd6e7; }
           QLabel    { color: #c42d74; font-family: 'Gill Sans MT'; font-size: 11px; font-weight: bold; }
           QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {
               background-color: white;
               border: 1px solid #ff73b4;
               border-radius: 6px;
               padding: 4px 8px;
               font-size: 11px;
           }
           QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
           QDateEdit:focus, QSpinBox:focus { border: 2px solid #c42d74; }
       """)
       self._build_ui()
       if patient_id:
           self._load_patient()


   def _build_ui(self):
       layout = QVBoxLayout(self)
       layout.setSpacing(10)
       layout.setContentsMargins(20, 20, 20, 20)


       title = QLabel("Add New Patient" if not self.patient_id else "Edit Patient Record")
       tf = QFont("Tw Cen MT Condensed Extra Bold", 18)
       tf.setItalic(True)
       title.setFont(tf)
       title.setStyleSheet("color: #ff73b4; margin-bottom: 6px;")
       layout.addWidget(title)


       layout.addWidget(self._section_label("Personal Information"))
       form1 = QFormLayout()
       form1.setSpacing(6)
       self.full_name_edit = QLineEdit()
       self.age_spin       = QSpinBox()
       self.age_spin.setRange(1, 120)
       self.phone_edit     = QLineEdit()
       self.address_edit   = QLineEdit()
       self.status_combo   = QComboBox()
       self.status_combo.addItems(["Active", "Pending", "Inactive"])
       form1.addRow("Full Name *", self.full_name_edit)
       form1.addRow("Age",         self.age_spin)
       form1.addRow("Phone",       self.phone_edit)
       form1.addRow("Address",     self.address_edit)
       form1.addRow("Status",      self.status_combo)
       layout.addLayout(form1)


       layout.addWidget(self._section_label("Visit Information"))
       form2 = QFormLayout()
       form2.setSpacing(6)
       date_style = "background-color: white; border: 1px solid #ff73b4; border-radius: 6px; padding: 4px 8px;"
       self.last_visit_edit = QDateEdit(QDate.currentDate())
       self.last_visit_edit.setCalendarPopup(True)
       self.last_visit_edit.setDisplayFormat("yyyy-MM-dd")
       self.last_visit_edit.setStyleSheet(date_style)
       self.next_appt_edit = QDateEdit(QDate.currentDate())
       self.next_appt_edit.setCalendarPopup(True)
       self.next_appt_edit.setDisplayFormat("yyyy-MM-dd")
       self.next_appt_edit.setStyleSheet(date_style)
       form2.addRow("Last Visit",       self.last_visit_edit)
       form2.addRow("Next Appointment", self.next_appt_edit)
       layout.addLayout(form2)


       layout.addWidget(self._section_label("Medical & Dental History"))
       form3 = QFormLayout()
       form3.setSpacing(6)
       self.med_history_edit    = QTextEdit(); self.med_history_edit.setFixedHeight(60)
       self.dental_history_edit = QTextEdit(); self.dental_history_edit.setFixedHeight(60)
       self.diagnosis_edit      = QTextEdit(); self.diagnosis_edit.setFixedHeight(60)
       form3.addRow("Medical History",   self.med_history_edit)
       form3.addRow("Dental History",    self.dental_history_edit)
       form3.addRow("Diagnosis / Notes", self.diagnosis_edit)
       layout.addLayout(form3)


       save_btn   = QPushButton("Save Patient")
       cancel_btn = QPushButton("Cancel")
       for btn in (save_btn, cancel_btn):
           btn.setFont(QFont("Segoe UI Black", 9, QFont.Weight.Bold))
       save_btn.setStyleSheet(
           "background-color: #c42d74; color: white; border-radius: 14px; padding: 8px 20px;"
       )
       cancel_btn.setStyleSheet(
           "background-color: #ff73b4; color: white; border-radius: 14px; padding: 8px 20px;"
       )
       save_btn.clicked.connect(self._save)
       cancel_btn.clicked.connect(self.reject)
       btn_row = QHBoxLayout()
       btn_row.addStretch()
       btn_row.addWidget(cancel_btn)
       btn_row.addWidget(save_btn)
       layout.addLayout(btn_row)


   def _section_label(self, text):
       lbl = QLabel(text)
       lbl.setStyleSheet(
           "color: #c42d74; font-family: 'Segoe UI Black'; font-size: 10px; font-weight: bold; "
           "border-bottom: 1px solid #ff73b4; padding-bottom: 2px; margin-top: 4px;"
       )
       return lbl


   def _load_patient(self):
       conn = get_connection()
       c = conn.cursor()
       c.execute(
           "SELECT full_name, age, phone, address, medical_history, dental_history, "
           "diagnosis, last_visit, next_appt, status FROM patients WHERE patient_id=%s",
           (self.patient_id,)
       )
       row = c.fetchone()
       conn.close()
       if not row:
           return
       (full_name, age, phone, address, med_hist,
        dental_hist, diagnosis, last_visit, next_appt, status) = row
       self.full_name_edit.setText(full_name or "")
       self.age_spin.setValue(age or 1)
       self.phone_edit.setText(phone or "")
       self.address_edit.setText(address or "")
       self.med_history_edit.setPlainText(med_hist or "")
       self.dental_history_edit.setPlainText(dental_hist or "")
       self.diagnosis_edit.setPlainText(diagnosis or "")
       if last_visit:
           self.last_visit_edit.setDate(
               QDate(
                   last_visit.year,
                   last_visit.month,
                   last_visit.day
               )
           )

       if next_appt:
           self.next_appt_edit.setDate(
               QDate(
                   next_appt.year,
                   next_appt.month,
                   next_appt.day
               )
           )
       idx = self.status_combo.findText(status or "Active")
       if idx >= 0:
           self.status_combo.setCurrentIndex(idx)

   def _save(self):

       full_name = self.full_name_edit.text().strip()

       if not full_name:
           QMessageBox.warning(
               self,
               "Missing Info",
               "Please enter the patient's full name."
           )
           return

       data = (
           full_name,
           self.age_spin.value(),
           self.phone_edit.text().strip(),
           self.address_edit.text().strip(),
           self.med_history_edit.toPlainText().strip(),
           self.dental_history_edit.toPlainText().strip(),
           self.diagnosis_edit.toPlainText().strip(),
           self.last_visit_edit.date().toString("yyyy-MM-dd"),
           self.next_appt_edit.date().toString("yyyy-MM-dd"),
           self.status_combo.currentText(),
       )

       try:

           conn = get_connection()
           c = conn.cursor()

           if self.patient_id:

               c.execute("""
                   UPDATE patients SET
                       full_name=%s,
                       age=%s,
                       phone=%s,
                       address=%s,
                       medical_history=%s,
                       dental_history=%s,
                       diagnosis=%s,
                       last_visit=%s,
                       next_appt=%s,
                       status=%s
                   WHERE patient_id=%s
               """, data + (self.patient_id,))

           else:

               c.execute("""
                   INSERT INTO patients
                       (
                           full_name,
                           age,
                           phone,
                           address,
                           medical_history,
                           dental_history,
                           diagnosis,
                           last_visit,
                           next_appt,
                           status
                       )
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               """, data)

           conn.commit()
           conn.close()

           QMessageBox.information(
               self,
               "Saved",
               "Database save successful."
           )

           super().accept()

       except Exception as e:

           QMessageBox.critical(
               self,
               "Database Error",
               str(e)
           )


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Login")
        self.setFixedSize(350, 220)
        self.setStyleSheet("background-color: #ffd6e7;")

        layout = QVBoxLayout(self)

        title = QLabel("Ngiponch Clinic Login")
        title.setFont(QFont("Tw Cen MT Condensed Extra Bold", 20))
        title.setStyleSheet("color:#c42d74;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username")

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        login_btn = QPushButton("Login")
        register_btn = QPushButton("Register")

        login_btn.setStyleSheet(
            "background-color:#c42d74;color:white;border-radius:12px;padding:8px;"
        )

        register_btn.setStyleSheet(
            "background-color:#ff73b4;color:white;border-radius:12px;padding:8px;"
        )

        login_btn.clicked.connect(self.login)
        register_btn.clicked.connect(self.open_register)

        layout.addWidget(title)
        layout.addWidget(self.username_edit)
        layout.addWidget(self.password_edit)
        layout.addWidget(login_btn)
        layout.addWidget(register_btn)

    def login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()

        user = login_user(username, password)

        if user:
            super().accept()
        else:
            QMessageBox.critical(
                self,
                "Login Failed",
                "Invalid username or password."
            )

    def open_register(self):
        dlg = RegisterDialog()
        dlg.exec()

class RegisterDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Register")
        self.setFixedSize(350, 300)
        self.setStyleSheet("background-color: #ffd6e7;")

        layout = QVBoxLayout(self)

        title = QLabel("Create Account")
        title.setFont(QFont("Tw Cen MT Condensed Extra Bold", 20))
        title.setStyleSheet("color:#c42d74;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username")

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Email")

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["Admin", "Staff"])

        register_btn = QPushButton("Register")

        register_btn.setStyleSheet(
            "background-color:#c42d74;color:white;border-radius:12px;padding:8px;"
        )

        register_btn.clicked.connect(self.register)

        layout.addWidget(title)
        layout.addWidget(self.username_edit)
        layout.addWidget(self.email_edit)
        layout.addWidget(self.password_edit)
        layout.addWidget(self.role_combo)
        layout.addWidget(register_btn)

    def register(self):
        username = self.username_edit.text().strip()
        email = self.email_edit.text().strip()
        password = self.password_edit.text().strip()
        role = self.role_combo.currentText()

        if not username or not password:
            QMessageBox.warning(
                self,
                "Missing Fields",
                "Please complete all fields."
            )
            return

        try:
            register_user(username, email, password, role)

            QMessageBox.information(
                self,
                "Success",
                "Account created successfully."
            )

            super().accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )

# ─────────────────────────────────────────────
#  MAIN WINDOW
# ─────────────────────────────────────────────
class MainWindow(QMainWindow):
   def __init__(self):
       super().__init__()
       self.setWindowTitle("Ngiponch Clinic")
       self.setFixedSize(997, 746)
       self.setStyleSheet("background-color: #ffd6e7;")


       central = QWidget()
       self.setCentralWidget(central)


       self._build_sidebar(central)
       self._build_stack(central)


       self.btn_home.clicked.connect(lambda: self.stack.setCurrentIndex(0))
       self.btn_apt.clicked.connect(lambda: (self.stack.setCurrentIndex(1), self.apt_model.refresh()))
       self.btn_pat.clicked.connect(lambda: (self.stack.setCurrentIndex(2), self._refresh_patients()))
       self.btn_logout.clicked.connect(self._logout)


   # ── SIDEBAR ──────────────────────────────
   def _build_sidebar(self, central):
       sidebar = QFrame(central)
       sidebar.setGeometry(0, 0, 261, 741)
       sidebar.setStyleSheet("background-color: #ff73b4;")
       sidebar.setFrameShape(QFrame.Shape.StyledPanel)
       sidebar.setFrameShadow(QFrame.Shadow.Raised)


       lbl_name = QLabel("Ngiponch", sidebar)
       lbl_name.setGeometry(30, 30, 231, 51)
       f1 = QFont("Tw Cen MT Condensed Extra Bold", 30)
       f1.setItalic(True)
       lbl_name.setFont(f1)
       lbl_name.setStyleSheet("color: white;")


       lbl_clinic = QLabel("Clinic", sidebar)
       lbl_clinic.setGeometry(110, 80, 101, 31)
       f2 = QFont("Tw Cen MT Condensed Extra Bold", 25)
       f2.setItalic(True)
       lbl_clinic.setFont(f2)
       lbl_clinic.setStyleSheet("color: white;")


       btn_style = "background-color: #c42d74; color: white; border-radius: 20px;"
       btn_font  = QFont("Segoe UI Black", 10, QFont.Weight.Bold)


       self.btn_home   = QPushButton("Home", sidebar)
       self.btn_apt    = QPushButton("Appointments", sidebar)
       self.btn_pat    = QPushButton("Patients", sidebar)
       self.btn_logout = QPushButton("Log Out", sidebar)


       for btn, (x, y) in zip(
           [self.btn_home, self.btn_apt, self.btn_pat, self.btn_logout],
           [(20, 140), (20, 200), (20, 260), (20, 620)]
       ):
           btn.setGeometry(x, y, 211, 51)
           btn.setFont(btn_font)
           btn.setStyleSheet(btn_style)


   # ── STACKED PAGES ────────────────────────
   def _build_stack(self, central):
       self.stack = QStackedWidget(central)
       self.stack.setGeometry(260, 0, 731, 721)
       self.stack.addWidget(self._build_home_page())
       self.stack.addWidget(self._build_apt_page())
       self.stack.addWidget(self._build_patients_page())
       self.stack.setCurrentIndex(0)


   # ── HOME PAGE ────────────────────────────
   def _build_home_page(self):
       page = QWidget()
       page.setStyleSheet("background-color: #ffd6e7;")


       frame = QFrame(page)
       frame.setGeometry(40, 60, 671, 531)
       frame.setStyleSheet("background-color: white; border-radius: 20px;")
       frame.setFrameShape(QFrame.Shape.StyledPanel)


       title_lbl = QLabel("Welcome to Ngiponch Clinic!", frame)
       title_lbl.setGeometry(20, 40, 551, 51)
       tf = QFont("Tw Cen MT Condensed Extra Bold", 30)
       tf.setItalic(True)
       title_lbl.setFont(tf)
       title_lbl.setStyleSheet("color: #ff73b4;")


       sub_lbl = QLabel("A CC15 database project submitted to Mr. Marlowee Oliva", frame)
       sub_lbl.setGeometry(30, 100, 451, 21)
       sf = QFont("Ubuntu Mono", 9)
       sf.setItalic(True)
       sub_lbl.setFont(sf)
       sub_lbl.setStyleSheet("color: #ff73b4;")


       self._stat_cards = []
       for label, color, x in [
           ("Total Patients", "#c42d74", 30),
           ("Active",         "#28a745", 230),
           ("Pending",        "#fd7e14", 430),
       ]:
           card = QFrame(frame)
           card.setGeometry(x, 160, 170, 90)
           card.setStyleSheet(f"background-color: {color}; border-radius: 14px;")
           card_lbl = QLabel(label, card)
           card_lbl.setGeometry(10, 8, 150, 20)
           card_lbl.setStyleSheet(
               "color: white; font-family: 'Segoe UI Black'; font-size: 10px; "
               "font-weight: bold; background: transparent;"
           )
           val_lbl = QLabel("0", card)
           val_lbl.setGeometry(10, 30, 150, 50)
           val_lbl.setFont(QFont("Segoe UI Black", 28, QFont.Weight.Bold))
           val_lbl.setStyleSheet("color: white; background: transparent;")
           self._stat_cards.append(val_lbl)


       self._update_stats()
       return page


   def _update_stats(self):
       conn = get_connection()
       c = conn.cursor()
       c.execute("SELECT COUNT(*) FROM patients")
       total = c.fetchone()[0]
       c.execute("SELECT COUNT(*) FROM patients WHERE status='Active'")
       active = c.fetchone()[0]
       c.execute("SELECT COUNT(*) FROM patients WHERE status='Pending'")
       pending = c.fetchone()[0]
       conn.close()
       for lbl, val in zip(self._stat_cards, [total, active, pending]):
           lbl.setText(str(val))


   # ── APPOINTMENTS PAGE ────────────────────
   def _build_apt_page(self):
       page = QWidget()
       page.setStyleSheet("background-color: #ffd6e7;")


       lbl_title = QLabel("Request An Appointment", page)
       lbl_title.setGeometry(50, 40, 411, 51)
       tf = QFont("Tw Cen MT Condensed Extra Bold", 25)
       tf.setItalic(True)
       lbl_title.setFont(tf)
       lbl_title.setStyleSheet("color: #ff73b4;")


       frame = QFrame(page)
       frame.setGeometry(40, 100, 461, 231)
       frame.setStyleSheet("background-color: rgb(255, 206, 218); border-radius: 20px;")
       frame.setFrameShape(QFrame.Shape.StyledPanel)


       lbl_p = QLabel("Patient's Name", frame)
       lbl_p.setGeometry(30, 30, 141, 37)
       lbl_p.setFont(QFont("Gill Sans MT", 11, QFont.Weight.Bold))
       lbl_p.setStyleSheet("color: #ff73b4;")


       self.apt_patient_edit = QLineEdit(frame)
       self.apt_patient_edit.setGeometry(30, 70, 211, 31)
       self.apt_patient_edit.setStyleSheet("background-color: white;")


       lbl_d = QLabel("Dentist Name", frame)
       lbl_d.setGeometry(30, 110, 141, 37)
       lbl_d.setFont(QFont("Gill Sans MT", 11, QFont.Weight.Bold))
       lbl_d.setStyleSheet("color: #ff73b4;")


       self.apt_dentist_edit = QLineEdit(frame)
       self.apt_dentist_edit.setGeometry(30, 150, 211, 31)
       self.apt_dentist_edit.setStyleSheet("background-color: white;")


       self.apt_datetime = QDateTimeEdit(QDateTime.currentDateTime(), frame)
       self.apt_datetime.setGeometry(270, 60, 161, 41)
       self.apt_datetime.setFont(QFont("Segoe UI Black", 9, QFont.Weight.Bold))
       self.apt_datetime.setStyleSheet("color: #c42d74; background-color: white;")
       self.apt_datetime.setCalendarPopup(True)
       self.apt_datetime.setDisplayFormat("yyyy-MM-dd HH:mm")


       btn_add_apt = QPushButton("Add Appointment", frame)
       btn_add_apt.setGeometry(270, 140, 151, 51)
       btn_add_apt.setFont(QFont("Segoe UI Black", 9, QFont.Weight.Bold))
       btn_add_apt.setStyleSheet("background-color: #c42d74; color: white; border-radius: 20px;")
       btn_add_apt.clicked.connect(self._add_appointment)


       lbl_table = QLabel("Appointments", page)
       lbl_table.setGeometry(40, 360, 411, 51)
       tf2 = QFont("Tw Cen MT Condensed Extra Bold", 25)
       tf2.setItalic(True)
       lbl_table.setFont(tf2)
       lbl_table.setStyleSheet("color: #ff73b4;")


       self.apt_model = AppointmentTableModel()
       self.apt_proxy = QSortFilterProxyModel()
       self.apt_proxy.setSourceModel(self.apt_model)


       self.apt_table = QTableView(page)
       self.apt_table.setGeometry(40, 420, 461, 261)
       self.apt_table.setStyleSheet("background-color: white;")
       self.apt_table.setModel(self.apt_proxy)
       self.apt_table.setSortingEnabled(True)
       self.apt_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
       self.apt_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
       self.apt_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
       self.apt_table.horizontalHeader().setStyleSheet(
           "QHeaderView::section { background-color: #c42d74; color: white; font-weight: bold; padding: 4px; }"
       )


       btn_del_apt = QPushButton("Delete Selected Appointment", page)
       btn_del_apt.setGeometry(40, 690, 250, 38)
       btn_del_apt.setFont(QFont("Segoe UI Black", 9, QFont.Weight.Bold))
       btn_del_apt.setStyleSheet("background-color: #c42d74; color: white; border-radius: 14px;")
       btn_del_apt.clicked.connect(self._delete_appointment)


       return page


   def _add_appointment(self):
       patient = self.apt_patient_edit.text().strip()
       dentist = self.apt_dentist_edit.text().strip()
       dt      = self.apt_datetime.dateTime().toString("yyyy-MM-dd HH:mm")
       if not patient or not dentist:
           QMessageBox.warning(self, "Missing Info", "Please fill in patient and dentist names.")
           return
       conn = get_connection()
       c = conn.cursor()

       c.execute(
           "INSERT INTO appointments (patient_name, dentist_name, appt_datetime) VALUES (%s,%s,%s)",
           (patient, dentist, dt)
       )
       conn.commit()
       conn.close()
       self.apt_patient_edit.clear()
       self.apt_dentist_edit.clear()
       self.apt_model.refresh()
       QMessageBox.information(self, "Success", "Appointment added successfully!")

   def _delete_appointment(self):

       idx = self.apt_table.currentIndex()

       if not idx.isValid():
           QMessageBox.warning(
               self,
               "No Selection",
               "Please select an appointment to delete."
           )
           return

       src_idx = self.apt_proxy.mapToSource(idx)

       if src_idx.row() < 0:
           return

       appt_id = self.apt_model._data[src_idx.row()][0]

       reply = QMessageBox.question(
           self,
           "Confirm Delete",
           "Are you sure you want to delete this appointment?",
           QMessageBox.StandardButton.Yes |
           QMessageBox.StandardButton.No
       )

       if reply != QMessageBox.StandardButton.Yes:
           return

       try:

           conn = get_connection()
           c = conn.cursor()

           c.execute(
               "DELETE FROM appointments WHERE appt_id=%s",
               (appt_id,)
           )

           conn.commit()
           conn.close()

           self.apt_table.clearSelection()

           self.apt_model.refresh()

           self.apt_table.setCurrentIndex(QModelIndex())

           QMessageBox.information(
               self,
               "Deleted",
               "Appointment deleted successfully."
           )

       except Exception as e:

           QMessageBox.critical(
               self,
               "Delete Error",
               str(e)
           )

   # ── PATIENTS PAGE ────────────────────────
   def _build_patients_page(self):
       page = QWidget()
       page.setStyleSheet("background-color: #ffd6e7;")


       lbl = QLabel("Patient Records", page)
       lbl.setGeometry(30, 20, 261, 41)
       f = QFont("Tw Cen MT Condensed Extra Bold", 25)
       f.setItalic(True)
       lbl.setFont(f)
       lbl.setStyleSheet("color: #c42d74;")


       search_lbl = QLabel("Search:", page)
       search_lbl.setGeometry(30, 65, 55, 28)
       search_lbl.setStyleSheet("color: #c42d74; font-weight: bold;")


       self.search_edit = QLineEdit(page)
       self.search_edit.setGeometry(90, 65, 300, 28)
       self.search_edit.setPlaceholderText("Search by name, phone, status...")
       self.search_edit.setStyleSheet(
           "background-color: white; border: 1px solid #ff73b4; border-radius: 8px; padding: 2px 8px;"
       )
       self.search_edit.textChanged.connect(
           lambda text: self.patient_proxy.setFilterFixedString(text)
       )


       self.patient_model = PatientTableModel()
       self.patient_proxy = QSortFilterProxyModel()
       self.patient_proxy.setSourceModel(self.patient_model)
       self.patient_proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
       self.patient_proxy.setFilterKeyColumn(-1)


       self.patient_table = QTableView(page)
       self.patient_table.setGeometry(30, 100, 681, 481)
       self.patient_table.setModel(self.patient_proxy)
       self.patient_table.setSortingEnabled(True)
       self.patient_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
       self.patient_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
       self.patient_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
       self.patient_table.setAlternatingRowColors(True)
       self.patient_table.horizontalHeader().setStyleSheet(
           "QHeaderView::section { background-color: #c42d74; color: white; "
           "font-family: 'Segoe UI Black'; font-size: 10px; font-weight: bold; padding: 5px; }"
       )
       self.patient_table.setStyleSheet("""
           QTableView {
               background-color: white;
               alternate-background-color: #fff0f6;
               border-radius: 10px;
               gridline-color: #ffd6e7;
           }
           QTableView::item:selected { background-color: #ff73b4; color: white; }
       """)


       btn_font = QFont("Segoe UI Black", 9, QFont.Weight.Bold)


       btn_add = QPushButton("＋ Add Patient", page)
       btn_add.setGeometry(30, 595, 150, 38)
       btn_add.setFont(btn_font)
       btn_add.setStyleSheet("background-color: #c42d74; color: white; border-radius: 14px;")
       btn_add.clicked.connect(self._add_patient)


       btn_edit = QPushButton("✎ Edit Selected", page)
       btn_edit.setGeometry(195, 595, 150, 38)
       btn_edit.setFont(btn_font)
       btn_edit.setStyleSheet("background-color: #ff73b4; color: white; border-radius: 14px;")
       btn_edit.clicked.connect(self._edit_patient)


       btn_del = QPushButton("✕ Delete Selected", page)
       btn_del.setGeometry(360, 595, 160, 38)
       btn_del.setFont(btn_font)
       btn_del.setStyleSheet("background-color: #a01050; color: white; border-radius: 14px;")
       btn_del.clicked.connect(self._delete_patient)


       btn_view = QPushButton("👁 View Full Record", page)
       btn_view.setGeometry(535, 595, 170, 38)
       btn_view.setFont(btn_font)
       btn_view.setStyleSheet("background-color: #c42d74; color: white; border-radius: 14px;")
       btn_view.clicked.connect(self._view_patient)


       return page


   def _refresh_patients(self):
       self.patient_model.refresh()
       self._update_stats()


   def _get_selected_patient_id(self):
       idx = self.patient_table.currentIndex()
       if not idx.isValid():
           return None
       src_idx = self.patient_proxy.mapToSource(idx)
       return self.patient_model.get_patient_id(src_idx.row())


   def _add_patient(self):
       dlg = PatientDialog(self)
       if dlg.exec() == QDialog.DialogCode.Accepted:
           self._refresh_patients()
           QMessageBox.information(self, "Success", "Patient record added successfully!")


   def _edit_patient(self):
       pid = self._get_selected_patient_id()
       if pid is None:
           QMessageBox.warning(self, "No Selection", "Please select a patient to edit.")
           return
       dlg = PatientDialog(self, patient_id=pid)
       if dlg.exec() == QDialog.DialogCode.Accepted:
           self._refresh_patients()
           QMessageBox.information(self, "Success", "Patient record updated successfully!")

   def _delete_patient(self):

       pid = self._get_selected_patient_id()

       if pid is None:
           QMessageBox.warning(
               self,
               "No Selection",
               "Please select a patient to delete."
           )
           return

       conn = get_connection()
       c = conn.cursor()

       c.execute(
           "SELECT full_name FROM patients WHERE patient_id=%s",
           (pid,)
       )

       row = c.fetchone()

       conn.close()

       name = row[0] if row else "this patient"

       reply = QMessageBox.question(
           self,
           "Confirm Delete",
           f"Are you sure you want to permanently delete the record for {name}?\n\nThis action cannot be undone.",
           QMessageBox.StandardButton.Yes |
           QMessageBox.StandardButton.No,
           QMessageBox.StandardButton.No
       )

       if reply != QMessageBox.StandardButton.Yes:
           return

       try:

           conn = get_connection()
           c = conn.cursor()

           c.execute(
               "DELETE FROM patients WHERE patient_id=%s",
               (pid,)
           )

           conn.commit()
           conn.close()

           self.patient_table.clearSelection()

           self.patient_model.refresh()

           self.patient_table.setCurrentIndex(QModelIndex())

           QApplication.processEvents()

           self._update_stats()

           QMessageBox.information(
               self,
               "Deleted",
               f"Record for {name} has been deleted."
           )

       except Exception as e:

           QMessageBox.critical(
               self,
               "Delete Error",
               str(e)
           )


   def _view_patient(self):
       pid = self._get_selected_patient_id()
       if pid is None:
           QMessageBox.warning(self, "No Selection", "Please select a patient to view.")
           return
       conn = get_connection()
       c = conn.cursor()
       c.execute(
           "SELECT patient_id, full_name, age, phone, address, medical_history, "
           "dental_history, diagnosis, last_visit, next_appt, status "
           "FROM patients WHERE patient_id=%s", (pid,)
       )
       row = c.fetchone()
       conn.close()
       if not row:
           return


       dlg = QDialog(self)
       dlg.setWindowTitle(f"Patient Record — {row[1]}")
       dlg.setFixedSize(480, 520)
       dlg.setStyleSheet("background-color: #ffd6e7;")
       layout = QVBoxLayout(dlg)
       layout.setContentsMargins(20, 20, 20, 20)
       layout.setSpacing(8)


       header = QLabel(f"Patient ID #{row[0]}  ·  {row[1]}")
       hf = QFont("Tw Cen MT Condensed Extra Bold", 18)
       hf.setItalic(True)
       header.setFont(hf)
       header.setStyleSheet("color: #c42d74;")
       layout.addWidget(header)


       fields = [
           ("Age",               str(row[2])),
           ("Phone",             str(row[3] or "—")),
           ("Address",           str(row[4] or "—")),
           ("Medical History",   str(row[5] or "—")),
           ("Dental History",    str(row[6] or "—")),
           ("Diagnosis / Notes", str(row[7] or "—")),
           ("Last Visit",        str(row[8] or "—")),
           ("Next Appointment",  str(row[9] or "—")),
           ("Status",            str(row[10] or "—")),
       ]
       for lbl_text, val_text in fields:
           row_frame = QFrame()
           row_frame.setStyleSheet("background-color: white; border-radius: 8px;")
           row_layout = QHBoxLayout(row_frame)
           row_layout.setContentsMargins(10, 4, 10, 4)
           lbl = QLabel(f"<b>{lbl_text}:</b>")
           lbl.setStyleSheet("color: #c42d74; min-width: 140px; background: transparent;")
           val = QLabel(val_text)
           val.setStyleSheet("color: #333; background: transparent;")
           val.setWordWrap(True)
           row_layout.addWidget(lbl)
           row_layout.addWidget(val, 1)
           layout.addWidget(row_frame)


       close_btn = QPushButton("Close")
       close_btn.setFont(QFont("Segoe UI Black", 9, QFont.Weight.Bold))
       close_btn.setStyleSheet(
           "background-color: #c42d74; color: white; border-radius: 14px; padding: 8px 24px;"
       )
       close_btn.clicked.connect(dlg.accept)
       btn_row = QHBoxLayout()
       btn_row.addStretch()
       btn_row.addWidget(close_btn)
       layout.addLayout(btn_row)
       dlg.exec()

   def _logout(self):

       reply = QMessageBox.question(
           self,
           "Log Out",
           "Are you sure you want to log out?",
           QMessageBox.StandardButton.Yes |
           QMessageBox.StandardButton.No,
           QMessageBox.StandardButton.No
       )

       if reply == QMessageBox.StandardButton.Yes:

           self.close()

           login = LoginDialog()

           if login.exec() == QDialog.DialogCode.Accepted:

               self.__init__()
               self.show()

           else:

               QApplication.quit()




# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    init_db()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#ffd6e7"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#c42d74"))
    palette.setColor(QPalette.ColorRole.Base, QColor("white"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#fff0f6"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#ff73b4"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))

    app.setPalette(palette)

    login = LoginDialog()

    if login.exec() == QDialog.DialogCode.Accepted:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
