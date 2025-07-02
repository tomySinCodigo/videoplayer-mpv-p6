import sys, os
os.environ["PATH"] = os.path.dirname(__file__) + os.pathsep + os.environ["PATH"]
import mpv
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QSlider, QLabel, 
                               QFileDialog, QFrame)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction


class MPVPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MPV Player")
        self.setGeometry(100, 100, 800, 600)
        
        # Crear instancia de MPV
        self.player = mpv.MPV(
            wid=0,  # Se asignará después
            vo='gpu',  # Video output
            keep_open=True,
            idle=True,
            log_handler=print,  # Para debug
            loglevel='info'
        )
        
        # Variables de estado
        self.duration = 0
        self.position = 0
        self.is_seeking = False
        
        self.setup_ui()
        self.setup_player()
        self.setup_timer()
        
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Frame para el video
        self.video_frame = QFrame()
        self.video_frame.setFrameStyle(QFrame.StyledPanel)
        self.video_frame.setMinimumHeight(400)
        self.video_frame.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_frame)
        
        # Controles de reproducción
        controls_layout = QHBoxLayout()
        
        # Botones principales
        self.play_btn = QPushButton("▶")
        self.pause_btn = QPushButton("⏸")
        self.stop_btn = QPushButton("⏹")
        self.prev_frame_btn = QPushButton("⏮")
        self.next_frame_btn = QPushButton("⏭")
        
        # Conectar botones
        self.play_btn.clicked.connect(self.play)
        self.pause_btn.clicked.connect(self.pause)
        self.stop_btn.clicked.connect(self.stop)
        self.prev_frame_btn.clicked.connect(self.previous_frame)
        self.next_frame_btn.clicked.connect(self.next_frame)
        
        controls_layout.addWidget(self.prev_frame_btn)
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.pause_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addWidget(self.next_frame_btn)
        
        layout.addLayout(controls_layout)
        
        # Slider de tiempo
        time_layout = QHBoxLayout()
        self.time_label = QLabel("00:00")
        self.time_slider = QSlider(Qt.Horizontal)
        self.duration_label = QLabel("00:00")
        
        self.time_slider.sliderPressed.connect(self.on_seek_start)
        self.time_slider.sliderReleased.connect(self.on_seek_end)
        self.time_slider.valueChanged.connect(self.on_seek)
        
        time_layout.addWidget(self.time_label)
        time_layout.addWidget(self.time_slider)
        time_layout.addWidget(self.duration_label)
        
        layout.addLayout(time_layout)
        
        # Controles de volumen
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("🔊"))
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        
        self.volume_label = QLabel("50%")
        
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        volume_layout.addStretch()
        
        layout.addLayout(volume_layout)
        
        # Botones de navegación
        nav_layout = QHBoxLayout()
        self.backward_btn = QPushButton("⏪ -10s")
        self.forward_btn = QPushButton("⏩ +10s")
        self.open_btn = QPushButton("Abrir Archivo")
        
        self.backward_btn.clicked.connect(self.seek_backward)
        self.forward_btn.clicked.connect(self.seek_forward)
        self.open_btn.clicked.connect(self.open_file)
        
        nav_layout.addWidget(self.backward_btn)
        nav_layout.addWidget(self.forward_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.open_btn)
        
        layout.addLayout(nav_layout)
        
    def setup_player(self):
        """Configurar el reproductor MPV"""
        # Asignar el widget como salida de video
        self.player.wid = int(self.video_frame.winId())
        
        # Eventos de MPV
        @self.player.property_observer('time-pos')
        def time_observer(_name, value):
            if value is not None and not self.is_seeking:
                self.position = value
                self.update_time_display()
        
        @self.player.property_observer('duration')
        def duration_observer(_name, value):
            if value is not None:
                self.duration = value
                self.time_slider.setMaximum(int(value))
                self.update_duration_display()
        
        @self.player.property_observer('volume')
        def volume_observer(_name, value):
            if value is not None:
                self.volume_slider.setValue(int(value))
                self.volume_label.setText(f"{int(value)}%")
    
    def setup_timer(self):
        """Configurar timer para actualizar la interfaz"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(100)  # Actualizar cada 100ms
    
    def open_file(self):
        """Abrir archivo de video"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Video", "", 
            "Videos (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm);;Todos los archivos (*)"
        )
        if file_path:
            self.player.loadfile(file_path)
    
    def play(self):
        """Reproducir"""
        self.player.pause = False
    
    def pause(self):
        """Pausar"""
        self.player.pause = True
    
    def stop(self):
        """Detener"""
        self.player.stop()
    
    def set_volume(self, value):
        """Establecer volumen"""
        self.player.volume = value
        self.volume_label.setText(f"{value}%")
    
    def seek_forward(self):
        """Adelantar 10 segundos"""
        self.player.seek(10, reference='relative')
    
    def seek_backward(self):
        """Retrasar 10 segundos"""
        self.player.seek(-10, reference='relative')
    
    def next_frame(self):
        """Siguiente frame"""
        self.player.frame_step()
    
    def previous_frame(self):
        """Frame anterior"""
        self.player.frame_back_step()
    
    def on_seek_start(self):
        """Iniciar búsqueda"""
        self.is_seeking = True
    
    def on_seek_end(self):
        """Finalizar búsqueda"""
        self.is_seeking = False
        position = self.time_slider.value()
        self.player.seek(position, reference='absolute')
    
    def on_seek(self, value):
        """Durante la búsqueda"""
        if self.is_seeking:
            self.time_label.setText(self.format_time(value))
    
    def update_ui(self):
        """Actualizar interfaz de usuario"""
        if not self.is_seeking and self.duration > 0:
            progress = int(self.position)
            self.time_slider.setValue(progress)
    
    def update_time_display(self):
        """Actualizar display de tiempo"""
        if not self.is_seeking:
            self.time_label.setText(self.format_time(self.position))
    
    def update_duration_display(self):
        """Actualizar display de duración"""
        self.duration_label.setText(self.format_time(self.duration))
    
    def format_time(self, seconds):
        """Formatear tiempo en MM:SS"""
        if seconds is None:
            return "00:00"
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def closeEvent(self, event):
        """Limpiar al cerrar"""
        self.player.terminate()
        event.accept()


def main():
    app = QApplication(sys.argv)
    player = MPVPlayer()
    player.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()