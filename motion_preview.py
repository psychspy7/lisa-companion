"""Private local video review. A Vidu clip is 2D footage, separate from the skeletal room."""
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QPushButton
from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
def show_clip(path,parent=None):
 dialog=QDialog(parent);dialog.setWindowTitle("Lisa · Motion preview");dialog.resize(720,900);dialog.setStyleSheet("QDialog{background:#161116;color:#eee}QLabel{color:#ddd}QPushButton{padding:10px;color:#eee;background:#45303a;border:0}")
 layout=QVBoxLayout(dialog);video=QVideoWidget(dialog);layout.addWidget(video,1);label=QLabel("Local clip · muted preview");layout.addWidget(label)
 player=QMediaPlayer(dialog);output=QAudioOutput(dialog);output.setMuted(True);player.setAudioOutput(output);player.setVideoOutput(video);player.errorOccurred.connect(lambda *_:label.setText("This clip could not play. Try another MP4 or WebM."))
 close=QPushButton("Close preview");close.clicked.connect(dialog.accept);layout.addWidget(close);player.setSource(QUrl.fromLocalFile(str(path)));player.play()
 try:dialog.exec()
 finally:player.stop();player.setSource(QUrl())
