import sys, os
os.environ["PATH"] = os.path.dirname(__file__) + os.pathsep + os.environ["PATH"]
import mpv
from PySide6.QtWidgets import (QApplication, QWidget)
from PySide6.QtCore import Qt, QTimer
from skin_player import Ui_SkinPlayer
# from PySide6.QtGui 


class PlayerMpv(QWidget, Ui_SkinPlayer):
    def __init__(self, *args, **kw):
        super(PlayerMpv, self).__init__(*args, **kw)
        self.setupUi(self)
        self.__configPlayerMpv()

    def __configPlayerMpv(self):
        self.player = mpv.MPV(
            wid=0, vo='gpu', keep_open=True,
            idle=True, log_handler=print,
            loglevel='info'
        )

        self._duration = 0
        self._position = 0
        self._inmove = False
        self.player.wid = int(self.fm_video.winId())
        
        @self.player.property_observer('time-pos')
        def timeObserber(name, value):
            if value is not None and not self._inmove:
                self._position = value
                self.update_time_display()

        @self.player.property_observer('duration')
        def durationObserver(name:str, value:float):
            if value is not None:
                self._duration = value
                # print('dur: ', value, type(value))
                # print('nam: ', name, type(name))
                self.sld_tiempo.setMaximum(int(value))
                self.update_duration_display()

        @self.player.property_observer('volume')
        def volumeMove(name:str, value:float):
            if value is not None:
                self.sld_vol.setValue(int(value))
                self.lb_vol.setText(f'{int(value)}')

        self.bt_play.clicked.connect(self.playPause)
        self.bt_stop.clicked.connect(self.stop)
        self.sld_vol.valueChanged.connect(self.setVol)
        self.sld_tiempo.sliderPressed.connect(self._moveStart)
        self.sld_tiempo.sliderReleased.connect(self._moveEnd)
        self.sld_tiempo.valueChanged.connect(self._moveSlide)

        self.timer = QTimer()
        self.timer.timeout.connect(self._updateUi)
        # self.timer.start(100)

    def update_time_display(self):
        if not self._inmove:
            self.lb_time.setText(self.format_time(self._position))

    def update_duration_display(self):
        self.lb_time.setText(self.format_time(self._duration))

    def format_time(self, seconds):
        if seconds is None:
            return '00:00:00'
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f'{minutes:02d}:{seconds:02d}'
    
    def setVideo(self, url:str):
        self.player.loadfile(url)
        self.timer.start(100)
    
    def play(self):
        self.player.pause = False

    def pause(self):
        self.player.pause = True

    def stop(self):
        self.player.stop()

    def setVol(self, value):
        self.player.volume = value
        self.lb_vol.setText(str(int(value)))

    def closeEvent(self, event):
        self.player.terminate()
        event.accept()

    def _getProperty(self, prop:str) -> str|bool :
        return self.player._get_property(prop)
    
    def _setProperty(self, *args):
        self.player._set_property(*args)

    def playPause(self):
        std:bool = self._getProperty(prop='core-idle')
        self.player.pause = not std
        if std:
            self.timer.start(100)
        else:
            self.timer.stop()
            print('detener timer')
        
    def _moveStart(self):
        self._inmove = True

    def _moveEnd(self):
        self._inmove = False
        pos = self.sld_tiempo.value()
        print('pos: ', pos, type(pos))
        self.player.seek(pos, reference='absolute')

    def _moveSlide(self, value):
        if self._inmove:
            self.lb_time.setText(self.format_time(value))

    def _updateUi(self):
        # print(self._inmove, self._duration)
        if not self._inmove and self._duration>0:
            pos = int(self._position)
            self.sld_tiempo.setValue(pos)
            print('moviendose')


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setStyle("Windows11")
    wg = PlayerMpv()

    v1 = "D:/temp-test/video.mp4"
    wg.setVideo(v1)
    wg.show()
    sys.exit(app.exec())