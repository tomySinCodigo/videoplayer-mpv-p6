import sys, os
os.environ["PATH"] = os.path.dirname(__file__) + os.pathsep + os.environ["PATH"]
import mpv
from PySide6.QtWidgets import (QApplication, QWidget)
from PySide6.QtCore import Qt, QTimer, Signal
from skin_player import Ui_SkinPlayer


class PlayerMpv(QWidget, Ui_SkinPlayer):
    # Señales para comunicación thread-safe
    position_changed = Signal(float)
    duration_changed = Signal(float)
    volume_changed = Signal(int)
    
    def __init__(self, *args, **kw):
        super(PlayerMpv, self).__init__(*args, **kw)
        self.setupUi(self)
        self.__configPlayerMpv()

    def __configPlayerMpv(self):
        # Configuración optimizada de MPV
        self.player = mpv.MPV(
            wid=0, 
            vo='gpu',  # Usar GPU para renderizado
            hwdec='auto',  # Decodificación por hardware automática
            keep_open=True,
            idle=True,
            log_handler=self._log_handler,
            loglevel='warn',  # Reducir logging para mejor rendimiento
            # Optimizaciones adicionales
            cache=True,
            demuxer_max_bytes='50MiB',  # Buffer más pequeño
            demuxer_readahead_secs=10,  # Menor readahead
            video_sync='display-resample',  # Mejor sincronización
            interpolation=True,  # Interpolación de frames para mejor calidad
            tscale='oversample',  # Mejor escalado temporal
            framedrop='vo',  # Permitir drop de frames
        )

        self._duration = 0
        self._position = 0
        self._inmove = False
        self._is_playing = False
        self.player.wid = int(self.fm_video.winId())
        
        # Usar señales Qt para thread safety
        self.position_changed.connect(self._on_position_changed)
        self.duration_changed.connect(self._on_duration_changed)
        self.volume_changed.connect(self._on_volume_changed)
        
        # Observers optimizados
        @self.player.property_observer('time-pos')
        def timeObserver(name, value):
            if value is not None and not self._inmove:
                self.position_changed.emit(value)

        @self.player.property_observer('duration')
        def durationObserver(name, value):
            if value is not None:
                self.duration_changed.emit(value)

        @self.player.property_observer('volume')
        def volumeObserver(name, value):
            if value is not None:
                self.volume_changed.emit(int(value))

        @self.player.property_observer('pause')
        def pauseObserver(name, value):
            self._is_playing = not value if value is not None else False

        # Conexiones de UI
        self._connect_ui()
        
        # Timer optimizado - solo cuando sea necesario
        self.timer = QTimer()
        self.timer.timeout.connect(self._updateUi)
        self.timer.setSingleShot(False)

    def _log_handler(self, loglevel, component, message):
        """Handler de logs optimizado - solo errores importantes"""
        if loglevel in ['error', 'fatal']:
            print(f'[{loglevel}] {component}: {message}')

    def _connect_ui(self):
        """Separar conexiones UI para mejor organización"""
        self.bt_play.clicked.connect(self.playPause)
        self.bt_stop.clicked.connect(self.stop)
        self.sld_vol.valueChanged.connect(self._on_volume_slider_changed)
        self.sld_tiempo.sliderPressed.connect(self._moveStart)
        self.sld_tiempo.sliderReleased.connect(self._moveEnd)
        self.sld_tiempo.valueChanged.connect(self._moveSlide)
        self.bt_toggle.clicked.connect(self.togglePag)
        self.bt_forward.clicked.connect(self.goForward)
        self.bt_rewind.clicked.connect(self.goRewind)
        self.bt_next.clicked.connect(self.nextFrame)
        self.bt_prev.clicked.connect(self.previousFrame)
        self.bt_cap.clicked.connect(self.capture)

    # Slots thread-safe usando señales Qt
    def _on_position_changed(self, value):
        self._position = value
        self.update_time_display()

    def _on_duration_changed(self, value):
        self._duration = value
        self.sld_tiempo.setMaximum(int(value))
        self.update_duration_display()

    def _on_volume_changed(self, value):
        # Evitar bucles infinitos
        if self.sld_vol.value() != value:
            self.sld_vol.blockSignals(True)
            self.sld_vol.setValue(value)
            self.sld_vol.blockSignals(False)
        self.lb_vol.setText(str(value))

    def _on_volume_slider_changed(self, value):
        """Manejar cambios del slider de volumen"""
        try:
            self.player.volume = value
            self.lb_vol.setText(str(value))
        except Exception as e:
            print(f"Error setting volume: {e}")

    def update_time_display(self):
        if not self._inmove:
            self.lb_time.setText(self.format_time(self._position))
            # print(self.format_time(self._position))
            # print('poss::: ', self._position, type(self._position))
            self.lb_time_t.setText(self.sec_hmsz(sec=self._position))
            if self._duration:
                res = self._duration - self._position
                self.lb_time_rem.setText(self.sec_hmsz(sec=res))

    def update_duration_display(self):
        # Solo actualizar si es diferente
        duration_text = self.format_time(self._duration)
        if self.lb_time.text() != duration_text:
            self.lb_time.setText(duration_text)

    def format_time(self, seconds):
        """Formateo de tiempo optimizado"""
        if seconds is None or seconds < 0:
            return '00:00'
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f'{hours:02d}:{minutes:02d}:{secs:02d}'
        return f'{minutes:02d}:{secs:02d}'
    
    def setVideo(self, url: str):
        """Cargar video de forma más robusta"""
        try:
            if os.path.exists(url):
                self.player.loadfile(url)
                self._start_ui_timer()
            else:
                print(f"Error: File not found - {url}")
        except Exception as e:
            print(f"Error loading video: {e}")

    def _start_ui_timer(self):
        """Iniciar timer solo cuando sea necesario"""
        if not self.timer.isActive():
            self.timer.start(250)  # Reducir frecuencia a 4 FPS para UI
    
    def _stop_ui_timer(self):
        """Detener timer cuando no sea necesario"""
        if self.timer.isActive():
            self.timer.stop()

    def play(self):
        try:
            self.player.pause = False
            self._start_ui_timer()
        except Exception as e:
            print(f"Error playing: {e}")

    def pause(self):
        try:
            self.player.pause = True
        except Exception as e:
            print(f"Error pausing: {e}")

    def stop(self):
        try:
            self.player.stop()
            self._stop_ui_timer()
            self._position = 0
            self._duration = 0
            self.sld_tiempo.setValue(0)
            self.lb_time.setText('00:00')
        except Exception as e:
            print(f"Error stopping: {e}")

    def closeEvent(self, event):
        """Cleanup mejorado"""
        try:
            self._stop_ui_timer()
            if hasattr(self, 'player'):
                self.player.terminate()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            event.accept()

    def playPause(self):
        """Toggle play/pause optimizado"""
        try:
            if self._is_playing:
                self.pause()
            else:
                self.play()
        except Exception as e:
            print(f"Error in playPause: {e}")
        
    def _moveStart(self):
        self._inmove = True

    def _moveEnd(self):
        self._inmove = False
        pos = self.sld_tiempo.value()
        try:
            self.player.seek(pos, reference='absolute')
        except Exception as e:
            print(f"Error seeking: {e}")

    def _moveSlide(self, value):
        if self._inmove:
            self.lb_time.setText(self.format_time(value))

    def _updateUi(self):
        """Actualización UI optimizada"""
        try:
            if not self._inmove and self._duration > 0 and self._is_playing:
                pos = int(self._position)
                if self.sld_tiempo.value() != pos:
                    self.sld_tiempo.blockSignals(True)
                    self.sld_tiempo.setValue(pos)
                    self.sld_tiempo.blockSignals(False)
            
            # Detener timer si no está reproduciendo
            if not self._is_playing and self.timer.isActive():
                self._stop_ui_timer()
                
        except Exception as e:
            print(f"Error updating UI: {e}")

    def _mseg_hmsz(self, milliseconds: float | str) -> tuple:
        '''retorna tupla[int] = h, m, s, z'''
        h, r = divmod(float(milliseconds), 3.6e6)
        m, r = divmod(r, 6e4)
        s, z = divmod(r, 1e3)
        return int(h), int(m), int(s), int(z)
        
    def ms_hms(self, msec: int) -> str:
        timestamp = '00:00:00'
        if msec:
            h, m, s, z = self._mseg_hmsz(msec)
            timestamp = f'{h:02d}:{m:02d}:{s:02d}'
        return timestamp

    def ms_hmsz(self, msec: int) -> str:
        timestamp = '00:00:00.000'
        if msec:
            h, m, s, z = self._mseg_hmsz(msec)
            timestamp = f'{h:02d}:{m:02d}:{s:02d}.{z:03d}'
        return timestamp
    
    def sec_hmsz(self, sec:float) -> str:
        if sec:
            msec = sec * 1000
            return self.ms_hmsz(msec=msec)
        else:
            return '00:00:00.000'
    
    def togglePag(self):
        indice = 1 if self.sw.currentIndex()==0 else 0
        self.sw.setCurrentIndex(indice)

    def goForward(self):
        self.player.seek(5, reference='relative')

    def goRewind(self):
        self.player.seek(-5, reference='relative')

    def nextFrame(self):
        self.player.frame_step()

    def previousFrame(self):
        self.player.frame_back_step()

    def capture(self):
        time:str = self.getTimestamp()
        if time:
            self.player.screenshot_to_file(f'{time}.jpg')

    def getTimestamp(self) -> str:
        current_time:float = self.player.time_pos
        ts = None
        if current_time:
            ts = str(self.sec_hmsz(sec=current_time)).replace(':', '.')
        return ts


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Windows11")
    wg = PlayerMpv()

    v1 = "D:/temp-test/video.mp4"
    if os.path.exists(v1):
        wg.setVideo(v1)
        wg.show()
    else:
        print("Video file not found!")
        
    sys.exit(app.exec())