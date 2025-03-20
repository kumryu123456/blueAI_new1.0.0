#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BlueAI 클라이언트 - 자동화 실행 엔진
"""

import logging
import threading
import time
import uuid
from enum import Enum
from typing import Dict, Any, Optional, List, Callable

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

# 로깅 설정
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """작업 상태 열거형"""
    WAITING = "대기 중"
    RUNNING = "실행 중"
    COMPLETED = "완료"
    FAILED = "실패"
    CANCELED = "취소됨"
    PAUSED = "일시중지"


class Task:
    """자동화 작업 클래스"""
    
    def __init__(self, task_id: str, command: str, params: Optional[Dict[str, Any]] = None):
        self.task_id = task_id
        self.command = command
        self.params = params or {}
        
        self.status = TaskStatus.WAITING
        self.progress = 0
        self.result = None
        self.error = None
        
        self.start_time = None
        self.end_time = None
        
        # 작업 단계
        self.steps = []
        self.current_step = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """작업 상태를 딕셔너리로 변환"""
        return {
            "task_id": self.task_id,
            "command": self.command,
            "status": self.status.value,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "current_step": self.current_step,
            "total_steps": len(self.steps)
        }


class AutomationEngine(QObject):
    """자동화 작업 실행 엔진"""
    
    # 시그널 정의
    task_started = pyqtSignal(str)  # 작업 ID
    task_completed = pyqtSignal(str, dict)  # 작업 ID, 결과
    task_failed = pyqtSignal(str, str)  # 작업 ID, 오류 메시지
    task_canceled = pyqtSignal(str)  # 작업 ID
    status_changed = pyqtSignal(str, int, dict)  # 상태, 진행률, 상세 정보
    log_message = pyqtSignal(str, str)  # 메시지, 로그 레벨
    
    def __init__(self, server_client=None):
        super().__init__()
        
        # 서버 클라이언트 참조
        self.server_client = server_client
        
        # 현재 실행 중인 작업
        self.current_task = None
        
        # 작업 실행 스레드
        self.task_thread = None
        
        # 작업 중지 플래그
        self.stop_requested = False
        
        # 자동화 모듈 등록
        self.automation_modules = {}
        
        # 설정
        self.settings = {
            "headless_mode": False
        }
        
        # 자동화 모듈 디렉토리 (나중에 동적으로 로드)
        self.modules_dir = None
    
    def register_automation_module(self, name: str, module) -> None:
        """자동화 모듈 등록"""
        self.automation_modules[name] = module
        self.log_message.emit(f"자동화 모듈 등록됨: {name}", "INFO")
    
    def set_server_client(self, server_client) -> None:
        """서버 클라이언트 설정"""
        self.server_client = server_client
        
        # 서버 명령 수신 연결
        if server_client:
            server_client.command_received.connect(self._handle_command)
    
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """설정 업데이트"""
        self.settings.update(settings)
        self.log_message.emit("자동화 엔진 설정이 업데이트되었습니다.", "INFO")
    
    def create_task(self, command: str, params: Optional[Dict[str, Any]] = None) -> str:
        """새 작업 생성"""
        task_id = str(uuid.uuid4())
        task = Task(task_id, command, params)
        self.current_task = task
        
        # 작업 단계 설정 (실제로는 명령에 따라 동적으로 결정)
        self._prepare_task_steps(task)
        
        self.log_message.emit(f"작업 생성됨: {command} (ID: {task_id})", "INFO")
        return task_id
    
    def _prepare_task_steps(self, task: Task) -> None:
        """작업 단계 준비"""
        # 간단한 예시 - 실제로는 명령에 따라 동적으로 단계 구성
        command = task.command.lower()
        
        if "웹" in command or "사이트" in command or "브라우저" in command:
            # 웹 자동화 단계
            task.steps = [
                {"name": "브라우저 초기화", "action": "init_browser"},
                {"name": "페이지 열기", "action": "open_page", "url": task.params.get("url", "https://www.google.com")},
                {"name": "작업 실행", "action": "execute_action", "action_type": "navigate"}
            ]
            
            # 검색 관련 명령이면 검색 단계 추가
            if "검색" in command:
                task.steps.append({"name": "검색 실행", "action": "execute_action", "action_type": "search"})
            
            # 스크린샷 단계 추가
            task.steps.append({"name": "스크린샷 촬영", "action": "take_screenshot"})
            
            # 마무리 단계
            task.steps.append({"name": "브라우저 종료", "action": "close_browser"})
        
        else:
            # 기본 단계
            task.steps = [
                {"name": "초기화", "action": "init"},
                {"name": "명령 실행", "action": "execute", "command": command},
                {"name": "정리", "action": "cleanup"}
            ]
    
    def start_task(self, command: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """작업 시작"""
        if self.is_running():
            self.log_message.emit("이미 작업이 실행 중입니다.", "WARNING")
            return None
        
        # 새 작업 생성 (전달된 명령이 있는 경우)
        if command:
            self.create_task(command, params)
        
        # 현재 작업 없으면 오류
        if not self.current_task:
            self.log_message.emit("시작할 작업이 없습니다.", "ERROR")
            return None
        
        # 작업 상태 초기화
        self.stop_requested = False
        self.current_task.status = TaskStatus.RUNNING
        self.current_task.start_time = time.time()
        self.current_task.progress = 0
        
        # 상태 업데이트
        self._update_status()
        
        # 시작 시그널 발생
        self.task_started.emit(self.current_task.task_id)
        
        # 별도 스레드에서 작업 실행
        self.task_thread = threading.Thread(target=self._task_worker)
        self.task_thread.daemon = True
        self.task_thread.start()
        
        self.log_message.emit(f"작업 시작: {self.current_task.command}", "INFO")
        return self.current_task.task_id
    
    def _task_worker(self) -> None:
        """작업 실행 스레드"""
        try:
            task = self.current_task
            
            # 단계별 실행
            for i, step in enumerate(task.steps):
                if self.stop_requested:
                    task.status = TaskStatus.CANCELED
                    self.log_message.emit("작업이 사용자에 의해 취소되었습니다.", "INFO")
                    self.task_canceled.emit(task.task_id)
                    self._update_status()
                    return
                
                # 현재 단계 업데이트
                task.current_step = i
                progress = int((i / len(task.steps)) * 100)
                task.progress = progress
                
                # 상태 업데이트
                self._update_status()
                
                # 단계 실행 로그
                step_name = step.get("name", f"단계 {i+1}")
                self.log_message.emit(f"단계 실행: {step_name}", "INFO")
                
                # 해당 액션 실행
                action = step.get("action", "")
                result = self._execute_action(action, step)
                
                # 단계 완료
                self.log_message.emit(f"단계 완료: {step_name}", "INFO")
                
                # 일부러 딜레이 추가 (데모용)
                time.sleep(1)
            
            # 작업 완료
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            task.end_time = time.time()
            task.result = {"message": "작업이 성공적으로 완료되었습니다."}
            
            # 서버에 결과 전송
            if self.server_client and self.server_client.is_connected():
                self.server_client.send_result(task.task_id, task.result)
            
            # 상태 업데이트
            self._update_status()
            
            # 완료 시그널 발생
            self.task_completed.emit(task.task_id, task.result)
            self.log_message.emit(f"작업 완료: {task.command}", "INFO")
            
        except Exception as e:
            if task:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.end_time = time.time()
                
                # 실패 시그널 발생
                self.task_failed.emit(task.task_id, task.error)
            
            error_msg = f"작업 실행 중 오류: {str(e)}"
            self.log_message.emit(error_msg, "ERROR")
            logger.error(error_msg, exc_info=True)
            
            # 상태 업데이트
            self._update_status()
    
    def _execute_action(self, action: str, params: Dict[str, Any]) -> Any:
        """작업 액션 실행"""
        # 웹 자동화 관련 액션
        if action == "init_browser":
            module = self.automation_modules.get("web")
            if module:
                return module.init_browser(headless=self.settings.get("headless_mode", False))
            
        elif action == "open_page":
            module = self.automation_modules.get("web")
            if module:
                return module.open_page(params.get("url", "https://www.google.com"))
            
        elif action == "execute_action":
            module = self.automation_modules.get("web")
            if module:
                action_type = params.get("action_type", "")
                if action_type == "navigate":
                    return module.navigate()
                elif action_type == "search":
                    return module.search(self.current_task.command)
            
        elif action == "take_screenshot":
            module = self.automation_modules.get("web")
            if module:
                return module.take_screenshot()
            
        elif action == "close_browser":
            module = self.automation_modules.get("web")
            if module:
                return module.close_browser()
        
        # 기본 액션
        elif action == "init":
            return {"status": "success"}
            
        elif action == "execute":
            return {"status": "success", "command": params.get("command", "")}
            
        elif action == "cleanup":
            return {"status": "success"}
        
        # 액션 모듈을 찾을 수 없거나 지원하지 않는 액션
        self.log_message.emit(f"지원하지 않는 액션: {action}", "WARNING")
        return {"status": "error", "message": f"지원하지 않는 액션: {action}"}
    
    def stop_task(self) -> bool:
        """작업 중지"""
        if not self.is_running():
            self.log_message.emit("실행 중인 작업이 없습니다.", "WARNING")
            return False
        
        self.log_message.emit("작업 중지 요청...", "INFO")
        self.stop_requested = True
        
        # 작업 스레드가 종료될 때까지 최대 3초 대기
        if self.task_thread and self.task_thread.is_alive():
            self.task_thread.join(timeout=3.0)
        
        # 작업이 여전히 실행 중이면 강제 종료
        if self.task_thread and self.task_thread.is_alive():
            self.log_message.emit("작업 강제 종료", "WARNING")
            
            # 작업 상태 업데이트
            if self.current_task:
                self.current_task.status = TaskStatus.CANCELED
                self._update_status()
                self.task_canceled.emit(self.current_task.task_id)
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """현재 작업 상태 조회"""
        if not self.current_task:
            return {
                "status": "대기 중",
                "progress": 0,
                "details": {}
            }
        
        status_dict = self.current_task.to_dict()
        
        # 실행 중인 단계 정보 추가
        if 0 <= self.current_task.current_step < len(self.current_task.steps):
            current_step = self.current_task.steps[self.current_task.current_step]
            status_dict["current_step_name"] = current_step.get("name", f"단계 {self.current_task.current_step+1}")
        
        # 상세 정보
        details = {
            "task_id": self.current_task.task_id,
            "command": self.current_task.command,
            "current_step": f"{self.current_task.current_step + 1}/{len(self.current_task.steps)}" 
                          if self.current_task.steps else "N/A",
        }
        
        if self.current_task.error:
            details["error"] = self.current_task.error
        
        if self.current_task.result:
            details["result"] = str(self.current_task.result)
        
        return {
            "status": self.current_task.status.value,
            "progress": self.current_task.progress,
            "details": details
        }
    
    def is_running(self) -> bool:
        """작업 실행 중인지 확인"""
        return (self.current_task and 
                self.current_task.status == TaskStatus.RUNNING and
                self.task_thread and 
                self.task_thread.is_alive())
    
    def _update_status(self) -> None:
        """상태 업데이트 및 시그널 발생"""
        if not self.current_task:
            return
        
        status = self.get_status()
        self.status_changed.emit(
            status["status"],
            status["progress"],
            status["details"]
        )
    
    @pyqtSlot(dict)
    def _handle_command(self, command_data: Dict[str, Any]) -> None:
        """서버로부터 수신한 명령 처리"""
        command = command_data.get("command", "")
        params = command_data.get("params", {})
        
        self.log_message.emit(f"서버 명령 처리: {command}", "INFO")
        
        # 작업 시작
        task_id = self.start_task(command, params)
        
        if task_id:
            # 시작 확인 메시지 전송
            if self.server_client and self.server_client.is_connected():
                self.server_client.send_result(task_id, {"status": "started"})