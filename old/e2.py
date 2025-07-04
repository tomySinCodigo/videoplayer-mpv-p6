import sys
import os
import platform
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QSlider, QLabel, 
                               QFileDialog, QFrame, QMessageBox)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, pyqtSignal
from PySide6.QtGui import QIcon, QPixmap
import subprocess
import locale

class MPVPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.mpv_process = None
        self.video_file = None
        self.duration = 0
        self.current_position = 0
        self.is_playing = False
        self.volume = 50
        
        # Timer para actualizar la posición
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)
        self.timer.start(1000)  # Actualizar cada segundo
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Reproductor MPV - PySide6")
        self.setGeometry(100, 100, 800, 600)
        
        # Layout principal
        main_layout = QVBoxLayout()
        
        # Área de video (frame negro)
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setMinimumHeight(400)
        main_layout.addWidget(self.video_frame)
        
        # Controles
        controls_layout = self.create_controls()
        main_layout.addLayout(controls_layout)
        
        self.setLayout(main_layout)
        
    def create_controls(self):
        # Layout principal de controles
        main_controls = QVBoxLayout()
        
        # Botón para abrir archivo
        open_button = QPushButton("Abrir Video")
        open_button.clicked.connect(self.open_file)
        main_controls.addWidget(open_button)
        
        # Slider de tiempo
        time_layout = QHBoxLayout()
        self.time_label = QLabel("00:00 / 00:00")
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(100)
        self.time_slider.valueChanged.connect(self.seek_video)
        time_layout.addWidget(self.time_label)
        time_layout.addWidget(self.time_slider)
        main_controls.addLayout(time_layout)
        
        # Controles de reproducción
        playback_layout = QHBoxLayout()
        
        # Botones principales
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_play_pause)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_video)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_video)
        
        playback_layout.addWidget(self.play_button)
        playback_layout.addWidget(self.pause_button)
        playback_layout.addWidget(self.stop_button)
        
        # Controles de frame
        self.prev_frame_button = QPushButton("← Frame")
        self.prev_frame_button.clicked.connect(self.previous_frame)
        
        self.next_frame_button = QPushButton("Frame →")
        self.next_frame_button.clicked.connect(self.next_frame)
        
        playback_layout.addWidget(self.prev_frame_button)
        playback_layout.addWidget(self.next_frame_button)
        
        # Controles de navegación
        self.rewind_button = QPushButton("⏪ -10s")
        self.rewind_button.clicked.connect(self.rewind)
        
        self.forward_button = QPushButton("⏩ +10s")
        self.forward_button.clicked.connect(self.forward)
        
        playback_layout.addWidget(self.rewind_button)
        playback_layout.addWidget(self.forward_button)
        
        # Botón de captura
        self.screenshot_button = QPushButton("📷 Captura")
        self.screenshot_button.clicked.connect(self.take_screenshot)
        playback_layout.addWidget(self.screenshot_button)
        
        main_controls.addLayout(playback_layout)
        
        # Control de volumen
        volume_layout = QHBoxLayout()
        volume_label = QLabel("Volumen:")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.volume_value_label = QLabel("50%")
        
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_value_label)
        main_controls.addLayout(volume_layout)
        
        return main_controls
        
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Seleccionar archivo de video",
            "",
            "Videos (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm);;Todos los archivos (*)"
        )
        
        if file_path:
            self.video_file = file_path
            self.load_video()
            
    def load_video(self):
        if not self.video_file:
            return
            
        # Cerrar proceso anterior si existe
        if self.mpv_process:
            self.mpv_process.terminate()
            
        # Obtener el ID de la ventana del frame de video
        wid = str(int(self.video_frame.winId()))
        
        # Comando MPV según el sistema operativo
        if platform.system() == "Windows":
            mpv_cmd = [
                "mpv",
                "--wid=" + wid,
                "--no-border",
                "--no-osd-bar",
                "--no-input-default-bindings",
                "--input-vo-keyboard=no",
                "--pause",
                self.video_file
            ]
        else:  # Linux
            mpv_cmd = [
                "mpv",
                "--wid=" + wid,
                "--no-border",
                "--no-osd-bar",
                "--no-input-default-bindings",
                "--input-vo-keyboard=no",
                "--pause",
                self.video_file
            ]
        
        try:
            self.mpv_process = subprocess.Popen(
                mpv_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.is_playing = False
            self.get_duration()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo cargar el video: {str(e)}")
            
    def send_command(self, command):
        if self.mpv_process and self.mpv_process.stdin:
            try:
                self.mpv_process.stdin.write(command + "\n")
                self.mpv_process.stdin.flush()
            except:
                pass
                
    def toggle_play_pause(self):
        if self.is_playing:
            self.pause_video()
        else:
            self.play_video()
            
    def play_video(self):
        self.send_command("set pause no")
        self.is_playing = True
        
    def pause_video(self):
        self.send_command("set pause yes")
        self.is_playing = False
        
    def stop_video(self):
        self.send_command("stop")
        self.is_playing = False
        self.current_position = 0
        self.time_slider.setValue(0)
        self.update_time_label()
        
    def seek_video(self, position):
        if self.duration > 0:
            time_position = (position / 100) * self.duration
            self.send_command(f"seek {time_position} absolute")
            
    def previous_frame(self):
        self.send_command("frame-back-step")
        
    def next_frame(self):
        self.send_command("frame-step")
        
    def rewind(self):
        self.send_command("seek -10")
        
    def forward(self):
        self.send_command("seek 10")
        
    def change_volume(self, value):
        self.volume = value
        self.send_command(f"set volume {value}")
        self.volume_value_label.setText(f"{value}%")
        
    def take_screenshot(self):
        if self.video_file:
            # Obtener el directorio del video
            video_dir = os.path.dirname(self.video_file)
            video_name = os.path.splitext(os.path.basename(self.video_file))[0]
            
            # Crear nombre de archivo para la captura
            screenshot_path = os.path.join(video_dir, f"{video_name}_screenshot.png")
            
            # Comando para captura
            self.send_command(f"screenshot-to-file {screenshot_path}")
            
            QMessageBox.information(self, "Captura", f"Captura guardada en:\n{screenshot_path}")
            
    def get_duration(self):
        # Obtener duración del video usando mpv
        try:
            cmd = ["mpv", "--no-video", "--no-audio", "--frames=1", "--msg-level=all=error", 
                   "--print-text=${duration}", self.video_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.stdout:
                self.duration = float(result.stdout.strip())
        except:
            self.duration = 0
            
    def update_position(self):
        if self.mpv_process and self.is_playing:
            # Aquí podrías implementar la obtención de la posición actual
            # Por simplicidad, incrementamos manualmente
            if self.current_position < self.duration:
                self.current_position += 1
                if self.duration > 0:
                    progress = (self.current_position / self.duration) * 100
                    self.time_slider.setValue(int(progress))
                    self.update_time_label()
                    
    def update_time_label(self):
        current_time = self.format_time(self.current_position)
        total_time = self.format_time(self.duration)
        self.time_label.setText(f"{current_time} / {total_time}")
        
    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
        
    def closeEvent(self, event):
        if self.mpv_process:
            self.mpv_process.terminate()
        event.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reproductor MPV")
        self.setGeometry(100, 100, 900, 700)
        
        # Widget central
        self.player = MPVPlayer()
        self.setCentralWidget(self.player)


def main():
    app = QApplication(sys.argv)
    
    # Verificar si MPV está instalado
    try:
        subprocess.run(["mpv", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        QMessageBox.critical(None, "Error", 
                           "MPV no está instalado o no está en el PATH del sistema.\n\n"
                           "Instalación:\n"
                           "Windows: Descargar desde https://mpv.io/\n"
                           "Linux: sudo apt install mpv (Ubuntu/Debian) o sudo pacman -S mpv (Arch)")
        sys.exit(1)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()