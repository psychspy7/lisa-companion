"""Activation gate. Online redemption once; verified receipt works offline."""
from PySide6.QtCore import QUrl,QTimer
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QLineEdit,QPushButton,QHBoxLayout
from activation import Activation
from settings_ui import STYLE
class ActivationDialog(QDialog):
    def __init__(self,backend,license,ready=None):
        super().__init__();self.backend=backend;self.license=license;self.ready_callback=ready;self.announced=False;self.setWindowTitle("LISA · Kitty Corp")
        self.setMinimumSize(560,410);self.setStyleSheet(STYLE)
        column=QVBoxLayout(self);column.setSpacing(20);column.setContentsMargins(32,32,32,32)
        title=QLabel("L I S A");title.setStyleSheet("font-size:38px; color:#ecd3cd;");column.addWidget(title)
        note=QLabel("Your world, with Lisa.\n\nBuy Lisa from Kitty Corp, then enter your personal access code.\nInternet is needed for first activation. Afterward, this Windows account\nand device can use the local companion offline.")
        note.setWordWrap(True);column.addWidget(note)
        self.code=QLineEdit();self.code.setMaxLength(80);self.code.setPlaceholderText("LISA-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX")
        column.addWidget(self.code);self.code.returnPressed.connect(self.redeem)
        self.state=QLabel("No API keys or Google sign-in are required to activate.")
        self.state.setWordWrap(True);column.addWidget(self.state)
        row=QHBoxLayout();self.activate=QPushButton("Activate Lisa");self.activate.clicked.connect(self.redeem);row.addWidget(self.activate)
        buy=QPushButton("Buy Lisa · Kitty Corp");buy.clicked.connect(lambda:QDesktopServices.openUrl(QUrl(self.license.purchase_url)));row.addWidget(buy);column.addLayout(row)
        self.restore=QPushButton("Recover activation on this device");self.restore.clicked.connect(lambda:self.run(self.license.recover));column.addWidget(self.restore)
    def showEvent(self,event):
        super().showEvent(event)
        if not self.announced and self.ready_callback:
            self.announced=True;QTimer.singleShot(0,self.ready_callback)
    def redeem(self):self.run(lambda:self.license.activate(self.code.text()))
    def run(self,fn):
        self.activate.setEnabled(False);self.restore.setEnabled(False);self.code.setEnabled(False);self.state.setText("Connecting securely…")
        def done(value):
            self.activate.setEnabled(True);self.restore.setEnabled(True);self.code.setEnabled(True)
            if isinstance(value,Exception):self.state.setText(str(value));return
            if self.license.valid():self.code.clear();self.accept()
            else:self.state.setText("Activation was not completed. Check the code and connection, then retry.")
        self.backend.work(fn,done)
def require_activation(backend,ready=None):
    license=Activation(backend.store.directory)
    if license.valid():return True
    return ActivationDialog(backend,license,ready).exec()==QDialog.DialogCode.Accepted
