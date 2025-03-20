#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BlueAI 클라이언트 - 서버 통신 모듈
"""

import json
import logging
import time
import threading
from typing import Dict, Any, Optional, Callable

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import websocket

# 로깅 설정
logger = logging.getLogger(__name__)

class ServerClient(QObject):
    """서버와의 통신을 담당하는 클래스"""
    
    # 시그널 정의
    connection_changed = pyqtSignal(bool)  # 연결 상태 변경 시 (연결됨/끊김)
    command_received = pyqtSignal(dict)    # 서버로부터 명령 수신 시
    log_message = pyqtSignal(str, str)     # 로그 메시지 (메시지, 레벨)
    
    def __init__(self):
        super().__init__()
        
        # WebSocket 클라이언트
        self.ws = None
        
        # 연결 상태
        self.connected = False
        
        # 자동 재연결 설정
        self.auto_reconnect = True
        self.reconnect_delay = 5  # 초
        self.reconnect_max_attempts = 5
        self.reconnect_attempts = 0
        self.reconnect_thread = None
        
        # 인증 토큰
        self.auth_token = None
        
        # 서버 URL
        self.server_url = None
        
        # 명령 콜백
        self.command_callbacks = {}
    
    def connect(self, url: str, token: Optional[str] = None) -> bool:
        """서버에 연결"""
        if self.connected:
            self.log_message.emit("이미 서버에 연결되어 있습니다.", "WARNING")
            return True
        
        self.server_url = url
        self.auth_token = token
        
        try:
            # WebSocket 연결 시도
            self.log_message.emit(f"서버 연결 시도: {url}", "INFO")
            
            # WebSocket 설정
            self.ws = websocket.WebSocketApp(
                url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # 별도 스레드에서 WebSocket 실행
            self.ws_thread = threading.Thread(target=self.ws.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
            # 연결 타임아웃 대기 (최대 5초)
            for _ in range(50):  # 100ms * 50 = 5초
                if self.connected:
                    break
                time.sleep(0.1)
            
            return self.connected
            
        except Exception as e:
            error_msg = f"서버 연결 실패: {str(e)}"
            self.log_message.emit(error_msg, "ERROR")
            logger.error(error_msg)
            return False
    
    def disconnect(self) -> bool:
        """서버 연결 해제"""
        if not self.connected or not self.ws:
            return True
        
        try:
            self.log_message.emit("서버 연결 해제 중...", "INFO")
            self.ws.close()
            
            # 스레드 종료 대기
            if hasattr(self, 'ws_thread') and self.ws_thread.is_alive():
                self.ws_thread.join(timeout=2.0)
            
            # 재연결 스레드 종료
            if self.reconnect_thread and self.reconnect_thread.is_alive():
                self.reconnect_thread.join(timeout=1.0)
            
            self.connected = False
            self.connection_changed.emit(False)
            
            return True
            
        except Exception as e:
            error_msg = f"서버 연결 해제 실패: {str(e)}"
            self.log_message.emit(error_msg, "ERROR")
            logger.error(error_msg)
            return False
    
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self.connected
    
    def send_command(self, command: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """서버에 명령 전송"""
        if not self.connected or not self.ws:
            self.log_message.emit("서버에 연결되어 있지 않습니다.", "WARNING")
            return False
        
        try:
            # 명령 메시지 구성
            message = {
                "type": "command",
                "command": command
            }
            
            # 추가 데이터가 있으면 포함
            if data:
                message["data"] = data
            
            # 토큰이 있으면 포함
            if self.auth_token:
                message["token"] = self.auth_token
            
            # JSON으로 변환 후 전송
            self.ws.send(json.dumps(message))
            self.log_message.emit(f"명령 전송: {command}", "INFO")
            
            return True
            
        except Exception as e:
            error_msg = f"명령 전송 실패: {str(e)}"
            self.log_message.emit(error_msg, "ERROR")
            logger.error(error_msg)
            return False
    
    def send_result(self, task_id: str, result: Dict[str, Any]) -> bool:
        """작업 결과 전송"""
        if not self.connected or not self.ws:
            self.log_message.emit("서버에 연결되어 있지 않습니다.", "WARNING")
            return False
        
        try:
            # 결과 메시지 구성
            message = {
                "type": "result",
                "task_id": task_id,
                "result": result
            }
            
            # 토큰이 있으면 포함
            if self.auth_token:
                message["token"] = self.auth_token
            
            # JSON으로 변환 후 전송
            self.ws.send(json.dumps(message))
            self.log_message.emit(f"결과 전송 (작업 ID: {task_id})", "INFO")
            
            return True
            
        except Exception as e:
            error_msg = f"결과 전송 실패: {str(e)}"
            self.log_message.emit(error_msg, "ERROR")
            logger.error(error_msg)
            return False
    
    def register_command_callback(self, command: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """특정 명령에 대한 콜백 등록"""
        self.command_callbacks[command] = callback
    
    def set_auto_reconnect(self, enabled: bool, max_attempts: int = 5, delay: int = 5) -> None:
        """자동 재연결 설정"""
        self.auto_reconnect = enabled
        self.reconnect_max_attempts = max_attempts
        self.reconnect_delay = delay
    
    def _on_open(self, ws):
        """WebSocket 연결 성공 시 호출"""
        self.connected = True
        self.reconnect_attempts = 0
        
        self.log_message.emit("서버에 연결되었습니다.", "INFO")
        self.connection_changed.emit(True)
        
        # 인증 토큰이 있으면 인증 요청
        if self.auth_token:
            auth_message = {
                "type": "auth",
                "token": self.auth_token
            }
            ws.send(json.dumps(auth_message))
    
    def _on_message(self, ws, message):
        """서버로부터 메시지 수신 시 호출"""
        try:
            # JSON 파싱
            data = json.loads(message)
            
            # 메시지 타입에 따른 처리
            msg_type = data.get("type", "")
            
            if msg_type == "command":
                # 명령 메시지 처리
                command = data.get("command", "")
                self.log_message.emit(f"서버 명령 수신: {command}", "INFO")
                
                # 명령 시그널 발생
                self.command_received.emit(data)
                
                # 등록된 콜백이 있으면 실행
                if command in self.command_callbacks:
                    self.command_callbacks[command](data)
                
            elif msg_type == "auth":
                # 인증 응답 처리
                if data.get("success", False):
                    self.log_message.emit("서버 인증 성공", "INFO")
                else:
                    self.log_message.emit(f"서버 인증 실패: {data.get('message', '알 수 없는 오류')}", "ERROR")
                    # 인증 실패 시 연결 해제
                    self.disconnect()
            
            elif msg_type == "error":
                # 오류 메시지 처리
                self.log_message.emit(f"서버 오류: {data.get('message', '알 수 없는 오류')}", "ERROR")
            
            else:
                # 기타 메시지 처리
                self.log_message.emit(f"알 수 없는 메시지 타입: {msg_type}", "WARNING")
            
        except json.JSONDecodeError:
            self.log_message.emit("잘못된 JSON 형식의 메시지를 수신했습니다.", "ERROR")
        except Exception as e:
            self.log_message.emit(f"메시지 처리 중 오류 발생: {str(e)}", "ERROR")
    
    def _on_error(self, ws, error):
        """WebSocket 오류 발생 시 호출"""
        error_msg = f"WebSocket 오류: {str(error)}"
        self.log_message.emit(error_msg, "ERROR")
        logger.error(error_msg)
    
    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket 연결 종료 시 호출"""
        was_connected = self.connected
        self.connected = False
        
        if was_connected:
            self.log_message.emit("서버 연결이 종료되었습니다.", "INFO")
            self.connection_changed.emit(False)
        
        # 자동 재연결이 활성화되어 있고, 이전에 연결된 적이 있으면 재연결 시도
        if self.auto_reconnect and was_connected and self.server_url:
            self._try_reconnect()
    
    def _try_reconnect(self):
        """서버 재연결 시도"""
        if self.reconnect_attempts >= self.reconnect_max_attempts:
            self.log_message.emit(f"최대 재연결 시도 횟수({self.reconnect_max_attempts}회)를 초과했습니다.", "WARNING")
            return
        
        self.reconnect_attempts += 1
        
        self.log_message.emit(
            f"서버 재연결 시도 ({self.reconnect_attempts}/{self.reconnect_max_attempts})... "
            f"{self.reconnect_delay}초 후 시도합니다.", 
            "INFO"
        )
        
        # 별도 스레드에서 재연결 시도 (UI 블로킹 방지)
        self.reconnect_thread = threading.Thread(target=self._reconnect_worker)
        self.reconnect_thread.daemon = True
        self.reconnect_thread.start()
    
    def _reconnect_worker(self):
        """재연결 작업자 스레드"""
        time.sleep(self.reconnect_delay)
        
        if not self.connected:
            self.connect(self.server_url, self.auth_token)