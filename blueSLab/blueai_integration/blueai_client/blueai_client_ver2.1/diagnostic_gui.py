#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BlueAI - 페이지 ID 진단 도구 통합 예제
메인 애플리케이션에 페이지 ID 문제 진단 및 해결 도구를 통합하는 예제
"""

import os
import sys
import logging
import argparse
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QTextEdit

# 경로 설정 (필요한 경우)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# BlueAI 모듈 임포트
from core.plugin_manager import PluginManager
from core.workflow_manager import WorkflowManager
from core.settings_manager import SettingsManager

# 진단 도구 임포트
from debug_diagnostic import PageIDMonitor, patch_playwright_plugin, repair_page_ids, setup_diagnostic_logging

class DiagnosticWindow(QMainWindow):
    """페이지 ID 진단 도구 창"""
    
    def __init__(self, plugin_manager, workflow_manager):
        super().__init__()
        self.plugin_manager = plugin_manager
        self.workflow_manager = workflow_manager
        self.playwright_plugin = plugin_manager.get_plugin("automation", "playwright")
        self.monitor = None
        
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle('BlueAI 페이지 ID 진단 도구')
        self.setGeometry(100, 100, 800, 600)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 레이아웃
        layout = QVBoxLayout(central_widget)
        
        # 상태 표시 라벨
        self.status_label = QLabel('페이지 ID 진단 도구 준비됨')
        layout.addWidget(self.status_label)
        
        # 버튼 생성
        self.start_monitor_btn = QPushButton('모니터링 시작')
        self.start_monitor_btn.clicked.connect(self.start_monitoring)
        layout.addWidget(self.start_monitor_btn)
        
        self.stop_monitor_btn = QPushButton('모니터링 중지 및 보고서 생성')
        self.stop_monitor_btn.clicked.connect(self.stop_monitoring)
        self.stop_monitor_btn.setEnabled(False)
        layout.addWidget(self.stop_monitor_btn)
        
        self.patch_plugin_btn = QPushButton('Playwright 플러그인 패치')
        self.patch_plugin_btn.clicked.connect(self.patch_plugin)
        layout.addWidget(self.patch_plugin_btn)
        
        self.repair_btn = QPushButton('페이지 ID 복구')
        self.repair_btn.clicked.connect(self.repair_page_ids)
        layout.addWidget(self.repair_btn)
        
        # 로그 표시 영역
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)
        
        # 로그 핸들러
        self.log_handler = LogHandler(self.log_display)
        logger = logging.getLogger()
        logger.addHandler(self.log_handler)
        
        self.show()
    
    def start_monitoring(self):
        """페이지 ID 모니터링 시작"""
        try:
            if not self.playwright_plugin:
                self.log("오류: Playwright 플러그인을 찾을 수 없습니다.")
                return
            
            # 모니터 생성 및 시작
            self.monitor = PageIDMonitor(self.playwright_plugin, self.workflow_manager)
            self.monitor.start_monitoring()
            
            self.log("페이지 ID 모니터링이 시작되었습니다.")
            self.status_label.setText("모니터링 중...")
            
            # 버튼 상태 변경
            self.start_monitor_btn.setEnabled(False)
            self.stop_monitor_btn.setEnabled(True)
            
        except Exception as e:
            self.log(f"모니터링 시작 중 오류: {str(e)}")
    
    def stop_monitoring(self):
        """모니터링 중지 및 보고서 생성"""
        try:
            if self.monitor:
                self.monitor.stop_monitoring()
                report_path = self.monitor.generate_report()
                
                self.log(f"모니터링이 중지되었습니다.")
                self.log(f"보고서가 생성되었습니다: {report_path}")
                self.status_label.setText("모니터링 중지됨")
                
                # 버튼 상태 변경
                self.start_monitor_btn.setEnabled(True)
                self.stop_monitor_btn.setEnabled(False)
            else:
                self.log("모니터가 실행 중이 아닙니다.")
        
        except Exception as e:
            self.log(f"모니터링 중지 중 오류: {str(e)}")
    
    def patch_plugin(self):
        """Playwright 플러그인 패치"""
        try:
            if not self.playwright_plugin:
                self.log("오류: Playwright 플러그인을 찾을 수 없습니다.")
                return
            
            patch_playwright_plugin(self.playwright_plugin)
            self.log("Playwright 플러그인이 패치되었습니다.")
            self.patch_plugin_btn.setEnabled(False)
            
        except Exception as e:
            self.log(f"플러그인 패치 중 오류: {str(e)}")
    
    def repair_page_ids(self):
        """페이지 ID 복구"""
        try:
            if not self.playwright_plugin:
                self.log("오류: Playwright 플러그인을 찾을 수 없습니다.")
                return
            
            success = repair_page_ids(self.playwright_plugin, self.workflow_manager)
            
            if success:
                self.log("페이지 ID가 복구되었습니다.")
            else:
                self.log("페이지 ID 복구 중 문제가 발생했습니다.")
            
        except Exception as e:
            self.log(f"페이지 ID 복구 중 오류: {str(e)}")
    
    def log(self, message):
        """로그 메시지 추가"""
        self.log_display.append(message)


class LogHandler(logging.Handler):
    """QTextEdit에 로그를 표시하는 핸들러"""
    
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    def emit(self, record):
        msg = self.format(record)
        self.text_widget.append(msg)


def main():
    """메인 함수"""
    # 명령줄 인수 파싱
    parser = argparse.ArgumentParser(description='BlueAI 페이지 ID 진단 도구')
    parser.add_argument('--plugins-dir', type=str, default='plugins',
                      help='플러그인 디렉토리')
    args = parser.parse_args()
    
    # 진단용 로깅 설정
    logger, _ = setup_diagnostic_logging()
    
    try:
        # QApplication 인스턴스 생성
        app = QApplication(sys.argv)
        app.setApplicationName("BlueAI 페이지 ID 진단 도구")
        
        # 필요한 매니저 초기화
        settings_manager = SettingsManager()
        plugin_manager = PluginManager(args.plugins_dir)
        
        # 플러그인 로드
        logger.info("플러그인 로드 중...")
        loaded_plugins = plugin_manager.load_all_plugins()
        logger.info(f"로드된 플러그인: {loaded_plugins}")
        
        # 플러그인 초기화
        logger.info("플러그인 초기화 중...")
        plugin_manager.initialize_all_plugins()
        
        # 워크플로우 관리자 초기화
        workflow_manager = WorkflowManager(
            checkpoint_dir=os.path.join(os.path.expanduser("~"), "BlueAI", "checkpoints"),
            plugin_manager=plugin_manager
        )
        
        # 진단 도구 창 생성
        window = DiagnosticWindow(plugin_manager, workflow_manager)
        
        # 애플리케이션 실행
        return app.exec_()
        
    except Exception as e:
        logger.error(f"진단 도구 실행 중 오류: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())