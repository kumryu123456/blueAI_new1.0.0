#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BlueAI 통합 자동화 시스템 - 워크플로우 관리자
자동화 워크플로우 관리 및 실행을 위한 관리자 (페이지 ID 동기화 문제 해결)
"""

import logging
import os
import json
import time
import uuid
from enum import Enum
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from threading import Thread, Event, Lock

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """워크플로우 상태 열거형"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class WorkflowStep:
    """워크플로우 단계 클래스"""
    
    def __init__(self, step_id, name, action, dependencies=None):
        self.step_id = step_id
        self.name = name
        self.action = action
        self.dependencies = dependencies or []
        self.status = WorkflowStatus.PENDING
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.retry_count = 0
        self.max_retries = 3
        
        # 페이지 ID 추적 추가
        self.page_id = None
    
    def to_dict(self):
        """단계 정보를 딕셔너리로 변환"""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "action": self.action,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "retry_count": self.retry_count,
            "page_id": self.page_id  # 페이지 ID 포함
        }


class Workflow:
    """워크플로우 클래스"""
    
    def __init__(self, workflow_id=None, name=None, description=None):
        self.workflow_id = workflow_id or str(uuid.uuid4())
        self.name = name or f"워크플로우 {self.workflow_id}"
        self.description = description or ""
        self.steps = {}
        self.step_order = []
        self.status = WorkflowStatus.PENDING
        self.current_step_id = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.creation_time = datetime.now().isoformat()
    
    def add_step(self, step):
        """워크플로우에 단계 추가"""
        self.steps[step.step_id] = step
        if step.step_id not in self.step_order:
            self.step_order.append(step.step_id)
    
    def set_step_order(self, step_order):
        """워크플로우 단계 순서 설정"""
        # 모든 단계가 존재하는지 확인
        for step_id in step_order:
            if step_id not in self.steps:
                raise ValueError(f"단계 ID가 존재하지 않음: {step_id}")
        
        # 단계 순서 설정
        self.step_order = step_order
    
    def to_dict(self):
        """워크플로우 정보를 딕셔너리로 변환"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "steps": {step_id: step.to_dict() for step_id, step in self.steps.items()},
            "step_order": self.step_order,
            "status": self.status.value,
            "current_step_id": self.current_step_id,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "creation_time": self.creation_time
        }


class WorkflowManager:
    """워크플로우 관리자 클래스"""
    
    def __init__(self, checkpoint_dir=None, plugin_manager=None):
        self.workflows = {}
        self.running_workflows = {}
        self.checkpoint_dir = checkpoint_dir or "checkpoints"
        self.plugin_manager = plugin_manager
        self.workflow_threads = {}
        self.stop_events = {}
        self.mutex = Lock()
        
        # 체크포인트 디렉토리 생성
        os.makedirs(self.checkpoint_dir, exist_ok=True)
    
    def create_workflow(self, name=None, description=None):
        """새 워크플로우 생성"""
        workflow = Workflow(name=name, description=description)
        self.workflows[workflow.workflow_id] = workflow
        return workflow
    
    def add_workflow_step(self, workflow_id, step):
        """워크플로우에 단계 추가"""
        if workflow_id not in self.workflows:
            raise ValueError(f"워크플로우 ID가 존재하지 않음: {workflow_id}")
        
        self.workflows[workflow_id].add_step(step)
    
    def set_workflow_step_order(self, workflow_id, step_order):
        """워크플로우 단계 순서 설정"""
        if workflow_id not in self.workflows:
            raise ValueError(f"워크플로우 ID가 존재하지 않음: {workflow_id}")
        
        self.workflows[workflow_id].set_step_order(step_order)
    
    def get_workflow(self, workflow_id):
        """워크플로우 가져오기"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self):
        """모든 워크플로우 목록 반환"""
        return list(self.workflows.values())
    
    def save_workflow_to_file(self, workflow_id, filepath=None):
        """워크플로우를 파일로 저장"""
        if workflow_id not in self.workflows:
            raise ValueError(f"워크플로우 ID가 존재하지 않음: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        
        if not filepath:
            filepath = os.path.join(self.checkpoint_dir, f"{workflow_id}.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(workflow.to_dict(), f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def load_workflow_from_file(self, filepath):
        """파일에서 워크플로우 로드"""
        with open(filepath, 'r', encoding='utf-8') as f:
            workflow_dict = json.load(f)
        
        workflow = Workflow(
            workflow_id=workflow_dict.get("workflow_id"),
            name=workflow_dict.get("name"),
            description=workflow_dict.get("description")
        )
        
        # 상태 설정
        workflow.status = WorkflowStatus(workflow_dict.get("status", "pending"))
        workflow.current_step_id = workflow_dict.get("current_step_id")
        workflow.error = workflow_dict.get("error")
        workflow.start_time = workflow_dict.get("start_time")
        workflow.end_time = workflow_dict.get("end_time")
        workflow.creation_time = workflow_dict.get("creation_time", datetime.now().isoformat())
        
        # 단계 로드
        for step_id, step_dict in workflow_dict.get("steps", {}).items():
            step = WorkflowStep(
                step_id=step_id,
                name=step_dict.get("name"),
                action=step_dict.get("action"),
                dependencies=step_dict.get("dependencies", [])
            )
            
            # 단계 상태 설정
            step.status = WorkflowStatus(step_dict.get("status", "pending"))
            step.result = step_dict.get("result")
            step.error = step_dict.get("error")
            step.start_time = step_dict.get("start_time")
            step.end_time = step_dict.get("end_time")
            step.retry_count = step_dict.get("retry_count", 0)
            step.page_id = step_dict.get("page_id")  # 페이지 ID 로드
            
            workflow.add_step(step)
        
        # 단계 순서 설정
        workflow.step_order = workflow_dict.get("step_order", [])
        
        # 워크플로우 추가
        self.workflows[workflow.workflow_id] = workflow
        
        return workflow.workflow_id
    
    def _save_checkpoint(self, workflow):
        """워크플로우 체크포인트 저장"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(self.checkpoint_dir, f"{workflow.workflow_id}_{timestamp}.json")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(workflow.to_dict(), f, ensure_ascii=False, indent=2)
            
            logger.info(f"체크포인트 저장됨: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"체크포인트 저장 중 오류: {str(e)}")
            return None
    
    def start_workflow(self, workflow_id):
        """워크플로우 실행 시작"""
        if workflow_id not in self.workflows:
            raise ValueError(f"워크플로우 ID가 존재하지 않음: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        
        # 이미 실행 중인 경우
        if workflow_id in self.running_workflows:
            logger.warning(f"워크플로우가 이미 실행 중: {workflow.name}")
            return False
        
        # 워크플로우 상태 초기화
        workflow.status = WorkflowStatus.RUNNING
        workflow.start_time = datetime.now().isoformat()
        workflow.end_time = None
        workflow.error = None
        
        # 스레드 준비
        stop_event = Event()
        self.stop_events[workflow_id] = stop_event
        
        # 실행 스레드 시작
        thread = Thread(target=self._run_workflow, args=(workflow_id, stop_event))
        thread.daemon = True
        thread.start()
        
        self.workflow_threads[workflow_id] = thread
        self.running_workflows[workflow_id] = workflow
        
        logger.info(f"워크플로우 시작됨: {workflow.name}")
        return True
    
    def stop_workflow(self, workflow_id):
        """워크플로우 실행 중지"""
        if workflow_id not in self.running_workflows:
            logger.warning(f"실행 중인 워크플로우가 아님: {workflow_id}")
            return False
        
        # 중지 이벤트 설정
        if workflow_id in self.stop_events:
            self.stop_events[workflow_id].set()
        
        # 스레드 종료 대기
        if workflow_id in self.workflow_threads:
            self.workflow_threads[workflow_id].join(5)  # 5초 대기
        
        # 워크플로우 상태 변경
        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.CANCELED
        workflow.end_time = datetime.now().isoformat()
        
        # 리소스 정리
        with self.mutex:
            if workflow_id in self.running_workflows:
                del self.running_workflows[workflow_id]
            if workflow_id in self.workflow_threads:
                del self.workflow_threads[workflow_id]
            if workflow_id in self.stop_events:
                del self.stop_events[workflow_id]
        
        logger.info(f"워크플로우 취소됨: {workflow.name}")
        
        # 마지막 체크포인트 저장
        self._save_checkpoint(workflow)
        
        return True
    
    def stop_all_workflows(self):
        """모든 워크플로우 중지"""
        workflow_ids = list(self.running_workflows.keys())
        
        for workflow_id in workflow_ids:
            self.stop_workflow(workflow_id)
        
        logger.info("모든 워크플로우가 중지됨")
    
    def is_workflow_running(self, workflow_id):
        """워크플로우 실행 중 여부 확인"""
        return workflow_id in self.running_workflows
    
    def _run_workflow(self, workflow_id, stop_event):
        """워크플로우 실행 (스레드에서 실행)"""
        workflow = self.workflows[workflow_id]
        
        try:
            # 체크포인트 저장
            self._save_checkpoint(workflow)
            
            # 실행할 단계 결정
            if not workflow.step_order:
                # 단계 순서가 지정되지 않은 경우 종속성에 따라 순서 결정
                workflow.step_order = self._determine_step_order(workflow)
            
            # 단계 실행 (순서대로)
            for step_id in workflow.step_order:
                # 중지 요청 확인
                if stop_event.is_set():
                    logger.info(f"워크플로우 중지됨: {workflow.name}")
                    workflow.status = WorkflowStatus.CANCELED
                    workflow.end_time = datetime.now().isoformat()
                    return
                
                # 단계 실행 가능 여부 확인
                if not self._can_execute_step(workflow, step_id):
                    logger.warning(f"단계를 실행할 수 없음 (종속성 문제): {step_id}")
                    continue
                
                # 단계 실행
                success = self.execute_workflow_step(workflow, step_id)
                
                # 실행 실패 시 워크플로우 중단
                if not success:
                    logger.error(f"단계 실행 실패: {step_id}")
                    workflow.status = WorkflowStatus.FAILED
                    workflow.error = f"단계 실행 실패: {step_id}"
                    workflow.end_time = datetime.now().isoformat()
                    return
            
            # 페이지 ID 동기화 체크
            self._sync_page_ids(workflow)
            
            # 모든 단계 완료
            workflow.status = WorkflowStatus.COMPLETED
            workflow.end_time = datetime.now().isoformat()
            logger.info(f"워크플로우 완료됨: {workflow.name}")
            
        except Exception as e:
            logger.error(f"워크플로우 실행 중 오류: {str(e)}")
            workflow.status = WorkflowStatus.FAILED
            workflow.error = str(e)
            workflow.end_time = datetime.now().isoformat()
            
        finally:
            # 실행 중인 워크플로우 목록에서 제거
            with self.mutex:
                if workflow_id in self.running_workflows:
                    del self.running_workflows[workflow_id]
                if workflow_id in self.workflow_threads:
                    del self.workflow_threads[workflow_id]
                if workflow_id in self.stop_events:
                    del self.stop_events[workflow_id]
            
            # 마지막 체크포인트 저장
            self._save_checkpoint(workflow)
    
    def _determine_step_order(self, workflow):
        """워크플로우 단계 실행 순서 결정 (종속성 기반)"""
        step_order = []
        visited = set()
        temp_visited = set()
        
        def visit(step_id):
            """DFS 순회"""
            if step_id in temp_visited:
                raise ValueError(f"워크플로우에 순환 종속성 발견: {step_id}")
            
            if step_id in visited:
                return
            
            temp_visited.add(step_id)
            
            # 종속성 방문
            for dep_id in workflow.steps[step_id].dependencies:
                if dep_id not in workflow.steps:
                    raise ValueError(f"종속성이 존재하지 않음: {dep_id}")
                visit(dep_id)
            
            temp_visited.remove(step_id)
            visited.add(step_id)
            step_order.append(step_id)
        
        # 모든 단계 방문
        for step_id in workflow.steps.keys():
            if step_id not in visited:
                visit(step_id)
        
        return step_order
    
    def _can_execute_step(self, workflow, step_id):
        """단계 실행 가능 여부 확인"""
        step = workflow.steps[step_id]
        
        # 이미 완료된 단계는 실행하지 않음
        if step.status == WorkflowStatus.COMPLETED:
            return False
        
        # 종속성 확인
        for dep_id in step.dependencies:
            if dep_id not in workflow.steps:
                logger.error(f"종속성이 존재하지 않음: {dep_id}")
                return False
            
            dep_step = workflow.steps[dep_id]
            if dep_step.status != WorkflowStatus.COMPLETED:
                logger.warning(f"종속성이 아직 완료되지 않음: {dep_id}")
                return False
        
        return True
    
    def _get_previous_steps(self, workflow, step_id):
        """현재 단계의 이전 단계 목록 반환"""
        step_index = workflow.step_order.index(step_id)
        if step_index > 0:
            return workflow.step_order[:step_index]
        return []
    
    def execute_workflow_step(self, workflow, step_id):
        """워크플로우 단계 실행"""
        step = workflow.steps[step_id]
        
        # 현재 단계 업데이트
        workflow.current_step_id = step_id
        
        # 단계 실행 시작
        step.status = WorkflowStatus.RUNNING
        step.start_time = datetime.now().isoformat()
        
        # 체크포인트 저장
        self._save_checkpoint(workflow)
        
        # 액션 정보 추출
        action = step.action
        plugin_type = action.get("plugin_type")
        plugin_name = action.get("plugin_name")
        action_name = action.get("action")
        params = action.get("params", {})
        
        logger.info(f"단계 시작: {step.name}")
        
        # 페이지 ID 추적 및 전달
        # 이전 단계에서 페이지 ID가 생성된 경우 이를 현재 단계에 전달
        if plugin_type == "automation" and plugin_name == "playwright":
            # 브라우저 자동화 단계에서 페이지 ID 처리
            
            # 이전 단계에서 페이지 ID 확인
            prev_steps = self._get_previous_steps(workflow, step_id)
            for prev_step_id in prev_steps:
                prev_step = workflow.steps[prev_step_id]
                
                # 이전 단계가 페이지 생성(new_page) 단계였다면
                if (prev_step.action.get("plugin_type") == "automation" and 
                    prev_step.action.get("plugin_name") == "playwright" and 
                    prev_step.action.get("action") == "new_page" and 
                    prev_step.result):
                    
                    # 페이지 ID를 현재 단계에 전달
                    params["page_id"] = prev_step.result
                    logger.info(f"이전 단계({prev_step_id})에서 페이지 ID({prev_step.result})를 현재 단계({step_id})로 전달")
                    step.page_id = prev_step.result
                    break
                
                # 이전 단계가 다른 playwright 액션이고 페이지 ID가 있는 경우
                elif (prev_step.action.get("plugin_type") == "automation" and 
                      prev_step.action.get("plugin_name") == "playwright" and
                      hasattr(prev_step, 'page_id') and prev_step.page_id):
                    
                    # 동일한 페이지 계속 사용
                    params["page_id"] = prev_step.page_id
                    logger.info(f"이전 단계({prev_step_id})의 페이지 ID({prev_step.page_id})를 현재 단계({step_id})로 전달")
                    step.page_id = prev_step.page_id
                    break
        
        # 플러그인 실행
        try:
            plugin = self.plugin_manager.get_plugin(plugin_type, plugin_name)
            if not plugin:
                raise ValueError(f"플러그인을 찾을 수 없음: {plugin_type}.{plugin_name}")
            
            # 플러그인 액션 실행
            result = plugin.execute(action_name, params)
            
            # 결과 저장
            step.result = result
            
            # 특별한 경우: new_page 액션의 경우 페이지 ID를 단계에 저장
            if plugin_type == "automation" and plugin_name == "playwright":
                if action_name == "new_page" and isinstance(result, str) and result.startswith("page_"):
                    step.page_id = result
                    logger.info(f"new_page 액션에서 페이지 ID({result})를 단계({step_id})에 저장")
                
                # goto나 다른 액션에서 페이지 ID가 반환될 경우에도 처리
                elif isinstance(result, dict) and "page_id" in result:
                    step.page_id = result["page_id"]
                    logger.info(f"{action_name} 액션에서 페이지 ID({result['page_id']})를 단계({step_id})에 저장")
            
            # 단계 완료 표시
            step.status = WorkflowStatus.COMPLETED
            step.end_time = datetime.now().isoformat()
            
            logger.info(f"단계 완료: {step.name}")
            if isinstance(result, (str, int, float, bool)):
                logger.info(f"결과: {type(result).__name__} 객체")
            elif result is None:
                logger.info("결과: None")
            else:
                logger.info(f"결과: {type(result).__name__} 객체")
            
            # 체크포인트 저장
            self._save_checkpoint(workflow)
            
            return True
        
        except Exception as e:
            import traceback
            error_details = f"{str(e)}\n{traceback.format_exc()}"
            
            # 오류 정보 저장
            step.error = error_details
            step.end_time = datetime.now().isoformat()
            
            # 재시도 로직
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                step.status = WorkflowStatus.PENDING
                
                logger.info(f"단계 재시도 중: {step.name} (시도 {step.retry_count}/{step.max_retries})")
                
                # 지연 후 재시도 (지수 백오프)
                retry_delay = 2 ** step.retry_count  # 2, 4, 8초...
                time.sleep(retry_delay)
                
                # 체크포인트 저장
                self._save_checkpoint(workflow)
                
                # 재귀적으로 동일 단계 실행
                return self.execute_workflow_step(workflow, step_id)
            else:
                # 최대 재시도 횟수 초과
                step.status = WorkflowStatus.FAILED
                
                logger.error(f"단계 실패: {step.name}")
                logger.error(f"오류: {str(e)}")
                
                # 체크포인트 저장
                self._save_checkpoint(workflow)
                
                return False
    
    def _sync_page_ids(self, workflow):
        """워크플로우 내의 페이지 ID들을 동기화"""
        playwright_plugin = self.plugin_manager.get_plugin("automation", "playwright")
        if not playwright_plugin:
            return
        
        # 현재 플러그인에 저장된 페이지 ID 목록
        plugin_page_ids = list(playwright_plugin.pages.keys())
        logger.info(f"플러그인에 저장된 페이지 ID 목록: {plugin_page_ids}")
        
        # 워크플로우 단계에서 사용된 페이지 ID 목록
        workflow_page_ids = []
        for step_id, step in workflow.steps.items():
            if hasattr(step, 'page_id') and step.page_id:
                workflow_page_ids.append(step.page_id)
        
        logger.info(f"워크플로우에서 사용된 페이지 ID 목록: {workflow_page_ids}")
        
        # 불일치 확인 및 해결
        missing_page_ids = [page_id for page_id in workflow_page_ids if page_id not in plugin_page_ids]
        if missing_page_ids:
            logger.warning(f"플러그인에 없는 페이지 ID 발견: {missing_page_ids}")
            
            # 첫 번째 missing ID를 현재 ID로 설정 (복구 시도)
            if missing_page_ids and hasattr(playwright_plugin, 'current_page_id'):
                playwright_plugin.current_page_id = missing_page_ids[0]
                logger.info(f"현재 페이지 ID를 {missing_page_ids[0]}로 설정 시도")

    def get_workflow_status(self, workflow_id):
        """워크플로우 상태 정보 가져오기"""
        if workflow_id not in self.workflows:
            return None
        
        workflow = self.workflows[workflow_id]
        
        # 상태 정보 구성
        status_info = {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "current_step_id": workflow.current_step_id,
            "start_time": workflow.start_time,
            "end_time": workflow.end_time,
            "steps": {}
        }
        
        # 단계 상태 추가
        for step_id, step in workflow.steps.items():
            status_info["steps"][step_id] = {
                "name": step.name,
                "status": step.status.value,
                "retry_count": step.retry_count,
                "page_id": step.page_id  # 페이지 ID 상태 추가
            }
        
        return status_info
    
    def resume_workflow(self, workflow_id, from_step_id=None):
        """중단된 워크플로우 재개"""
        if workflow_id not in self.workflows:
            raise ValueError(f"워크플로우 ID가 존재하지 않음: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        
        # 이미 실행 중인 경우
        if workflow_id in self.running_workflows:
            logger.warning(f"워크플로우가 이미 실행 중: {workflow.name}")
            return False
        
        # 특정 단계부터 재개 설정
        if from_step_id:
            if from_step_id not in workflow.steps:
                raise ValueError(f"단계 ID가 존재하지 않음: {from_step_id}")
            
            # 재개 시작 단계의 인덱스 찾기
            start_index = workflow.step_order.index(from_step_id)
            
            # 이전 단계 모두 완료 상태로 설정
            for i in range(start_index):
                prev_step_id = workflow.step_order[i]
                prev_step = workflow.steps[prev_step_id]
                prev_step.status = WorkflowStatus.COMPLETED
            
            # 재개 단계부터 나머지 단계 PENDING 상태로 설정
            for i in range(start_index, len(workflow.step_order)):
                step_id = workflow.step_order[i]
                step = workflow.steps[step_id]
                step.status = WorkflowStatus.PENDING
                step.error = None
                step.result = None
                step.start_time = None
                step.end_time = None
                step.retry_count = 0
        
        # 워크플로우 상태 업데이트
        workflow.status = WorkflowStatus.RUNNING
        workflow.start_time = datetime.now().isoformat()
        workflow.end_time = None
        workflow.error = None
        
        # 스레드 준비
        stop_event = Event()
        self.stop_events[workflow_id] = stop_event
        
        # 실행 스레드 시작
        thread = Thread(target=self._run_workflow, args=(workflow_id, stop_event))
        thread.daemon = True
        thread.start()
        
        self.workflow_threads[workflow_id] = thread
        self.running_workflows[workflow_id] = workflow
        
        logger.info(f"워크플로우 재개됨: {workflow.name}")
        return True