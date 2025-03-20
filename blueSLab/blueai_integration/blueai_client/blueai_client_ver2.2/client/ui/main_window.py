#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BlueAI 클라이언트 - 메인 윈도우 UI
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QTextBrowser, QStatusBar, 
                           QTabWidget, QProgressBar, QMessageBox, QInputDialog,
                           QSystemTrayIcon, QMenu, QAction, QCheckBox,
                           QLineEdit, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QTextCursor, QColor

# 로깅 설정
logger = logging.getLogger(__name__)

class LogViewer(QTextBrowser):
    """로그 메시지를 표시하는 위젯"""
    
    # 로그 메시지를 위한 시그널
    log_signal = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        
        # 로그 레벨별 색상
        self.log_colors = {
            "DEBUG": QColor(100, 100, 100),  # 회색
            "INFO": QColor(0, 0, 0),         # 검정
            "WARNING": QColor(255, 165, 0),  # 주황
            "ERROR": QColor(255, 0, 0),      # 빨강
            "CRITICAL": QColor(128, 0, 0)    # 어두운 빨강
        }
        
        # 최대 로그 라인 수
        self.max_lines = 1000
        
        # 시그널 연결
        self.log_signal.connect(self._append_log_safe)
    
    def append_log(self, message, level="INFO"):
        """로그 메시지 추가 (스레드 안전)"""
        # 시그널을 통해 메인 스레드에서 처리
        self.log_signal.emit(message, level)
    
    @pyqtSlot(str, str)
    def _append_log_safe(self, message, level):
        """메인 UI 스레드에서 실행되는 실제 로그 추가 메서드"""
        # 현재 시간
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 메시지 형식
        formatted_message = f"[{timestamp}] {level}: {message}"
        
        # 색상 설정
        color = self.log_colors.get(level, QColor(0, 0, 0))
        
        # HTML 태그로 색상 설정
        html = f'<span style="color:{color.name()};">{formatted_message}</span><br>'
        
        # 메시지 추가
        self.append(html)
        
        # 최대 라인 수 제한
        if self.document().lineCount() > self.max_lines:
            cursor = QTextCursor(self.document())
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 
                              self.document().lineCount() - self.max_lines)
            cursor.removeSelectedText()


class TaskStatusWidget(QWidget):
    """작업 상태 표시 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 상태 헤더
        header_layout = QHBoxLayout()
        self.status_label = QLabel("작업 상태: 대기 중")
        self.status_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.status_label)
        
        header_layout.addStretch()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedWidth(200)
        header_layout.addWidget(self.progress_bar)
        
        layout.addLayout(header_layout)
        
        # 상세 정보 영역
        self.details_browser = QTextBrowser()
        layout.addWidget(self.details_browser)
        
        # 제어 버튼 영역
        controls_layout = QHBoxLayout()
        
        self.start_button = QPushButton("시작")
        controls_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("중지")
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.stop_button)
        
        self.refresh_button = QPushButton("새로고침")
        controls_layout.addWidget(self.refresh_button)
        
        layout.addLayout(controls_layout)
    
    def update_status(self, status: str, progress: int = 0, details: Optional[Dict[str, Any]] = None):
        """작업 상태 업데이트"""
        self.status_label.setText(f"작업 상태: {status}")
        self.progress_bar.setValue(progress)
        
        # 상태에 따른 색상
        if status == "완료":
            self.status_label.setStyleSheet("font-weight: bold; color: green;")
        elif status == "실패":
            self.status_label.setStyleSheet("font-weight: bold; color: red;")
        elif status == "실행 중":
            self.status_label.setStyleSheet("font-weight: bold; color: blue;")
        else:
            self.status_label.setStyleSheet("font-weight: bold;")
        
        # 상세 정보 업데이트
        if details:
            self.details_browser.clear()
            try:
                for key, value in details.items():
                    self.details_browser.append(f"<b>{key}:</b> {value}")
            except Exception as e:
                self.details_browser.append(f"상세 정보 표시 오류: {str(e)}")
    
    def set_controls_state(self, running: bool):
        """제어 버튼 상태 업데이트"""
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)


class MainWindow(QMainWindow):
    """BlueAI 클라이언트 메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        
        # 서버 클라이언트 및 자동화 엔진은 나중에 외부에서 설정
        self.server_client = None
        self.automation_engine = None
        
        # UI 컴포넌트 초기화
        self.setup_ui()
        
        # 상태 업데이트 타이머
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_status)
        
        # 시스템 트레이 설정
        self.setup_tray()
        
        logger.info("메인 윈도우 초기화 완료")
    
    def setup_ui(self):
        """UI 초기화"""
        self.setWindowTitle("BlueAI 클라이언트")
        self.setMinimumSize(800, 600)
        
        # 아이콘 설정 (실제 경로로 수정 필요)
        icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 중앙 위젯 및 레이아웃
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # 서버 연결 영역
        connection_layout = QHBoxLayout()
        
        self.connection_label = QLabel("서버 상태: 연결 안됨")
        self.connection_label.setStyleSheet("color: red;")
        connection_layout.addWidget(self.connection_label)
        
        connection_layout.addStretch()
        
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("서버 주소 (예: ws://localhost:8080)")
        connection_layout.addWidget(self.server_input)
        
        self.connect_button = QPushButton("연결")
        self.connect_button.clicked.connect(self.toggle_connection)
        connection_layout.addWidget(self.connect_button)
        
        main_layout.addLayout(connection_layout)
        
        # 명령어 입력 영역
        command_layout = QHBoxLayout()
        
        command_label = QLabel("명령어:")
        command_layout.addWidget(command_label)
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("자동화 명령어 입력")
        self.command_input.returnPressed.connect(self.execute_command)
        command_layout.addWidget(self.command_input, 1)
        
        self.execute_button = QPushButton("실행")
        self.execute_button.clicked.connect(self.execute_command)
        command_layout.addWidget(self.execute_button)
        
        main_layout.addLayout(command_layout)
        
        # 메인 탭 영역
        self.tab_widget = QTabWidget()
        
        # 작업 탭
        self.task_tab = QWidget()
        task_layout = QVBoxLayout(self.task_tab)
        
        # 작업 상태 위젯
        self.task_status = TaskStatusWidget()
        task_layout.addWidget(self.task_status)
        
        # 버튼 연결
        self.task_status.start_button.clicked.connect(self.start_task)
        self.task_status.stop_button.clicked.connect(self.stop_task)
        self.task_status.refresh_button.clicked.connect(self.refresh_status)
        
        self.tab_widget.addTab(self.task_tab, "작업")
        
        # 로그 탭
        self.log_tab = QWidget()
        log_layout = QVBoxLayout(self.log_tab)
        
        self.log_viewer = LogViewer()
        log_layout.addWidget(self.log_viewer)
        
        self.tab_widget.addTab(self.log_tab, "로그")
        
        # 설정 탭
        self.settings_tab = QWidget()
        settings_layout = QVBoxLayout(self.settings_tab)
        
        settings_form = QFormLayout()
        
        # 헤드리스 모드 설정
        self.headless_checkbox = QCheckBox("헤드리스 모드")
        self.headless_checkbox.setChecked(False)
        settings_form.addRow("브라우저 설정:", self.headless_checkbox)
        
        # 자동 재연결 설정
        self.auto_reconnect_checkbox = QCheckBox("연결 끊김 시 자동 재연결")
        self.auto_reconnect_checkbox.setChecked(True)
        settings_form.addRow("서버 연결:", self.auto_reconnect_checkbox)
        
        settings_layout.addLayout(settings_form)
        
        # 저장 버튼
        settings_buttons = QHBoxLayout()
        settings_buttons.addStretch()
        
        self.save_settings_button = QPushButton("설정 저장")
        self.save_settings_button.clicked.connect(self.save_settings)
        settings_buttons.addWidget(self.save_settings_button)
        
        settings_layout.addLayout(settings_buttons)
        settings_layout.addStretch()
        
        self.tab_widget.addTab(self.settings_tab, "설정")
        
        main_layout.addWidget(self.tab_widget)
        
        self.setCentralWidget(central_widget)
        
        # 상태바
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("준비")
        
        # 메뉴바 설정
        self.setup_menubar()
    
    def setup_menubar(self):
        """메뉴바 설정"""
        menubar = self.menuBar()
        
        # 파일 메뉴
        file_menu = menubar.addMenu("파일")
        
        exit_action = QAction("종료", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 실행 메뉴
        run_menu = menubar.addMenu("실행")
        
        run_action = QAction("작업 실행", self)
        run_action.triggered.connect(self.start_task)
        run_menu.addAction(run_action)
        
        stop_action = QAction("작업 중지", self)
        stop_action.triggered.connect(self.stop_task)
        run_menu.addAction(stop_action)
        
        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말")
        
        about_action = QAction("정보", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_tray(self):
        """시스템 트레이 설정"""
        icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icon.png")
        if os.path.exists(icon_path):
            tray_icon = QIcon(icon_path)
        else:
            # 기본 아이콘
            tray_icon = self.style().standardIcon(self.style().SP_ComputerIcon)
        
        # 시스템 트레이 아이콘 설정
        self.tray_icon = QSystemTrayIcon(tray_icon, self)
        
        # 트레이 메뉴 설정
        tray_menu = QMenu()
        
        show_action = QAction("보이기", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("숨기기", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction("종료", self)
        exit_action.triggered.connect(self.close)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # 트레이 아이콘 표시
        self.tray_icon.show()
    
    def tray_icon_activated(self, reason):
        """트레이 아이콘 클릭 이벤트 처리"""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
    
    def set_server_client(self, server_client):
        """서버 클라이언트 설정"""
        self.server_client = server_client
        if server_client:
            self.server_client.connection_changed.connect(self.update_connection_status)
            self.server_client.log_message.connect(self.log_viewer.append_log)
            self.update_connection_status(self.server_client.is_connected())
    
    def set_automation_engine(self, automation_engine):
        """자동화 엔진 설정"""
        self.automation_engine = automation_engine
        if automation_engine:
            self.automation_engine.status_changed.connect(self.update_task_status)
            self.automation_engine.log_message.connect(self.log_viewer.append_log)
    
    @pyqtSlot(bool)
    def update_connection_status(self, connected):
        """서버 연결 상태 업데이트"""
        if connected:
            self.connection_label.setText("서버 상태: 연결됨")
            self.connection_label.setStyleSheet("color: green;")
            self.connect_button.setText("연결 해제")
            self.statusBar.showMessage("서버에 연결됨")
        else:
            self.connection_label.setText("서버 상태: 연결 안됨")
            self.connection_label.setStyleSheet("color: red;")
            self.connect_button.setText("연결")
            self.statusBar.showMessage("서버에 연결되지 않음")
    
    def toggle_connection(self):
        """서버 연결/연결 해제 토글"""
        if not self.server_client:
            self.log_viewer.append_log("서버 클라이언트가 초기화되지 않았습니다.", "ERROR")
            return
        
        if self.server_client.is_connected():
            # 연결 해제
            self.server_client.disconnect()
        else:
            # 연결
            server_url = self.server_input.text().strip()
            if not server_url:
                self.log_viewer.append_log("서버 주소를 입력하세요.", "WARNING")
                return
            
            self.server_client.connect(server_url)
    
    def execute_command(self):
        """명령어 실행"""
        command = self.command_input.text().strip()
        if not command:
            self.statusBar.showMessage("명령어를 입력하세요")
            return
        
        if not self.server_client or not self.server_client.is_connected():
            self.log_viewer.append_log("서버에 연결되어 있지 않습니다.", "WARNING")
            return
        
        if not self.automation_engine:
            self.log_viewer.append_log("자동화 엔진이 초기화되지 않았습니다.", "ERROR")
            return
        
        self.log_viewer.append_log(f"명령어 실행: {command}")
        self.statusBar.showMessage(f"명령어 실행 중: {command}")
        
        # 탭 전환
        self.tab_widget.setCurrentWidget(self.task_tab)
        
        # 명령 전송
        self.server_client.send_command(command)
    
    def start_task(self):
        """작업 시작"""
        if not self.automation_engine:
            self.log_viewer.append_log("자동화 엔진이 초기화되지 않았습니다.", "ERROR")
            return
        
        self.automation_engine.start_task()
        self.task_status.set_controls_state(True)
    
    def stop_task(self):
        """작업 중지"""
        if not self.automation_engine:
            self.log_viewer.append_log("자동화 엔진이 초기화되지 않았습니다.", "ERROR")
            return
        
        self.automation_engine.stop_task()
        self.task_status.set_controls_state(False)
    
    def update_status(self):
        """상태 주기적 업데이트"""
        if self.automation_engine:
            status = self.automation_engine.get_status()
            if status:
                self.update_task_status(status.get("status", ""), 
                                      status.get("progress", 0), 
                                      status.get("details", {}))
    
    @pyqtSlot(str, int, dict)
    def update_task_status(self, status, progress, details):
        """작업 상태 업데이트"""
        self.task_status.update_status(status, progress, details)
        
        # 작업 상태에 따라 제어 버튼 업데이트
        self.task_status.set_controls_state(status == "실행 중")
    
    def refresh_status(self):
        """상태 새로고침"""
        self.update_status()
    
    def save_settings(self):
        """설정 저장"""
        settings = {
            "headless_mode": self.headless_checkbox.isChecked(),
            "auto_reconnect": self.auto_reconnect_checkbox.isChecked()
        }
        
        # 실제 설정 저장 로직은 나중에 구현
        self.log_viewer.append_log("설정이 저장되었습니다.")
        self.statusBar.showMessage("설정 저장됨")
        
        # 설정 적용
        if self.automation_engine:
            self.automation_engine.update_settings(settings)
        
        if self.server_client:
            self.server_client.set_auto_reconnect(settings.get("auto_reconnect", True))
    
    def show_about(self):
        """정보 대화상자 표시"""
        QMessageBox.information(
            self, 
            "정보", 
            "BlueAI 클라이언트\n\n버전: 0.1.0\n\n서버 연결 및 자동화 클라이언트"
        )
    
    def closeEvent(self, event):
        """창 닫기 이벤트 처리"""
        # 작업 중인지 확인
        if self.automation_engine and self.automation_engine.is_running():
            reply = QMessageBox.question(
                self, '종료 확인',
                "작업이 실행 중입니다. 종료하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
            
            # 작업 중지
            self.automation_engine.stop_task()
        
        # 서버 연결 해제
        if self.server_client and self.server_client.is_connected():
            self.server_client.disconnect()
        
        # 트레이 아이콘 제거
        if self.tray_icon:
            self.tray_icon.hide()
        
        logger.info("애플리케이션 종료됨")
        event.accept()