#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BlueAI 클라이언트 - 애플리케이션 진입점
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any

from PyQt5.QtWidgets import QApplication

# 로깅 설정
def setup_logging():
    """로깅 설정"""
    log_dir = os.path.join(os.path.expanduser("~"), "BlueAI", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "blueai_client.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def parse_arguments():
    """명령줄 인수 파싱"""
    parser = argparse.ArgumentParser(description="BlueAI 클라이언트")
    
    parser.add_argument("--server", help="서버 URL (예: ws://localhost:8080)")
    parser.add_argument("--headless", action="store_true", help="헤드리스 모드로 브라우저 실행")
    parser.add_argument("--debug", action="store_true", help="디버그 모드 활성화")
    
    return parser.parse_args()

def load_settings() -> Dict[str, Any]:
    """설정 로드"""
    # 기본 설정
    settings = {
        "server_url": "ws://localhost:8080",
        "headless_mode": False,
        "auto_reconnect": True,
        "reconnect_delay": 5,
        "reconnect_max_attempts": 5
    }
    
    # 설정 파일이 있으면 로드
    settings_dir = os.path.join(os.path.expanduser("~"), "BlueAI", "config")
    settings_file = os.path.join(settings_dir, "settings.json")
    
    if os.path.exists(settings_file):
        try:
            import json
            with open(settings_file, "r", encoding="utf-8") as f:
                file_settings = json.load(f)
                settings.update(file_settings)
                
            logging.info(f"설정 로드됨: {settings_file}")
        except Exception as e:
            logging.error(f"설정 로드 중 오류: {str(e)}")
    
    return settings

def save_settings(settings: Dict[str, Any]) -> bool:
    """설정 저장"""
    settings_dir = os.path.join(os.path.expanduser("~"), "BlueAI", "config")
    os.makedirs(settings_dir, exist_ok=True)
    
    settings_file = os.path.join(settings_dir, "settings.json")
    
    try:
        import json
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
            
        logging.info(f"설정 저장됨: {settings_file}")
        return True
    except Exception as e:
        logging.error(f"설정 저장 중 오류: {str(e)}")
        return False

def main():
    """메인 함수"""
    # 명령줄 인수 파싱
    args = parse_arguments()
    
    # 로깅 설정
    setup_logging()
    
    # 디버그 모드 설정
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 설정 로드
    settings = load_settings()
    
    # 명령줄 인수로 설정 덮어쓰기
    if args.server:
        settings["server_url"] = args.server
    
    if args.headless:
        settings["headless_mode"] = True
    
    # 모듈 임포트
    from ui.main_window import MainWindow
    from core.server_client import ServerClient
    from core.automation_engine import AutomationEngine
    from automations.web_automation import WebAutomation
    
    # QApplication 인스턴스 생성
    app = QApplication(sys.argv)
    app.setApplicationName("BlueAI 클라이언트")
    
    # 메인 윈도우 생성
    main_window = MainWindow()
    
    # 서버 클라이언트 생성
    server_client = ServerClient()
    
    # 자동화 모듈 생성
    web_automation = WebAutomation()
    
    # 자동화 엔진 생성
    automation_engine = AutomationEngine()
    
    # 모듈 등록
    automation_engine.register_automation_module("web", web_automation)
    
    # 모듈 간 연결
    automation_engine.set_server_client(server_client)
    main_window.set_server_client(server_client)
    main_window.set_automation_engine(automation_engine)
    
    # 서버 URL 설정
    if settings.get("server_url"):
        main_window.server_input.setText(settings["server_url"])
    
    # 헤드리스 모드 설정
    main_window.headless_checkbox.setChecked(settings.get("headless_mode", False))
    
    # 자동 재연결 설정
    main_window.auto_reconnect_checkbox.setChecked(settings.get("auto_reconnect", True))
    server_client.set_auto_reconnect(
        settings.get("auto_reconnect", True),
        settings.get("reconnect_max_attempts", 5),
        settings.get("reconnect_delay", 5)
    )
    
    # 자동화 엔진 설정 업데이트
    automation_engine.update_settings({
        "headless_mode": settings.get("headless_mode", False)
    })
    
    # 메인 윈도우 표시
    main_window.show()
    
    # 이벤트 루프 시작
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()