#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BlueAI 클라이언트 - Playwright 기반 웹 자동화 모듈
"""

import os
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from PyQt5.QtCore import QObject, pyqtSignal

# Playwright를 설치해야 함
# pip install playwright
# python -m playwright install
try:
    from playwright.sync_api import sync_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# 로깅 설정
logger = logging.getLogger(__name__)

class WebAutomation(QObject):
    """Playwright를 사용한 웹 자동화 클래스"""
    
    # 시그널 정의
    log_message = pyqtSignal(str, str)  # 메시지, 로그 레벨
    
    def __init__(self):
        super().__init__()
        
        # Playwright 인스턴스
        self.playwright = None
        self.browser = None
        self.page = None
        
        # 브라우저 타입 (chromium, firefox, webkit)
        self.browser_type = "chromium"
        
        # 헤드리스 모드 (화면 표시 여부)
        self.headless = False
        
        # 스크린샷 저장 경로
        self.screenshot_dir = os.path.join(os.path.expanduser("~"), "BlueAI", "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    def init_browser(self, browser_type: str = "chromium", headless: bool = False) -> Dict[str, Any]:
        """브라우저 초기화"""
        if not PLAYWRIGHT_AVAILABLE:
            error_msg = "Playwright가 설치되지 않았습니다. pip install playwright를 실행한 후 python -m playwright install을 실행하세요."
            self.log_message.emit(error_msg, "ERROR")
            return {"status": "error", "message": error_msg}
        
        self.browser_type = browser_type
        self.headless = headless
        
        try:
            # 기존 브라우저 종료
            self.close_browser()
            
            # Playwright 시작
            self.playwright = sync_playwright().start()
            
            # 브라우저 타입에 따라 브라우저 실행
            if browser_type == "firefox":
                self.browser = self.playwright.firefox.launch(headless=headless)
                browser_name = "Firefox"
            elif browser_type == "webkit":
                self.browser = self.playwright.webkit.launch(headless=headless)
                browser_name = "WebKit"
            else:  # 기본값: chromium
                self.browser = self.playwright.chromium.launch(headless=headless)
                browser_name = "Chromium"
            
            self.log_message.emit(f"{browser_name} 브라우저가 시작되었습니다. (헤드리스 모드: {headless})", "INFO")
            return {"status": "success", "browser": browser_name}
            
        except Exception as e:
            error_msg = f"브라우저 초기화 중 오류: {str(e)}"
            self.log_message.emit(error_msg, "ERROR")
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
    
    def open_page(self, url: str) -> Dict[str, Any]:
        """페이지 열기"""
        if not self.browser:
            error_msg = "브라우저가 초기화되지 않았습니다."
            self.log_message.emit(error_msg, "ERROR")
            return {"status": "error", "message": error_msg}
        
        try:
            # 새 페이지 생성
            self.page = self.browser.new_page()
            
            # 페이지 이동
            self.log_message.emit(f"페이지 이동: {url}", "INFO")
            self.page.goto(url)
            
            # 페이지 로드 대기
            self.page.wait_for_load_state("networkidle")
            
            # 페이지 제목 가져오기
            title = self.page.title()
            
            self.log_message.emit(f"페이지 로드 완료: {title}", "INFO")
            return {"status": "success", "title": title, "url": self.page.url}
            
        except Exception as e:
            error_msg = f"페이지 열기 중 오류: {str(e)}"
            self.log_message.emit(error_msg, "ERROR")
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
    
    def navigate(self, url: Optional[str] = None) -> Dict[str, Any]:
        """페이지 이동"""
        if not self.page:
            error_msg = "열린 페이지가 없습니다."
            self.log_message.emit(error_msg, "ERROR")
            return {"status": "error", "message": error_msg}
        
        try:
            if url:
                # 새 URL로 이동
                self.log_message.emit(f"페이지 이동: {url}", "INFO")
                self.page.goto(url)
                
                # 페이지 로드 대기
                self.page.wait_for_load_state("networkidle")
            
            # 현재 URL 및 제목 가져오기
            current_url = self.page.url
            title = self.page.title()
            
            self.log_message.emit(f"현재 페이지: {title} ({current_url})", "INFO")
            return {"status": "success", "title": title, "url": current_url}
            
        except Exception as e:
            error_msg = f"페이지 이동 중 오류: {str(e)}"
            self.log_message.emit(error_msg, "ERROR")
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
    
    def search(self, query: str) -> Dict[str, Any]:
        """검색 수행"""
        if not self.page:
            error_msg = "열린 페이지가 없습니다."
            self.log_message.emit(error_msg, "ERROR")
            return {"status": "error", "message": error_msg}
        
        try:
            # 현재 URL 확인
            current_url = self.page.url
            
            # 구글 검색
            if "google.com" in current_url:
                self.log_message.emit(f"구글 검색: {query}", "INFO")
                
                # 검색창에 쿼리 입력
                self.page.fill('input[name="q"]', query)
                
                # 검색 버튼 클릭 또는 Enter 키 입력
                self.page.press('input[name="q"]', "Enter")
                
                # 결과 로드 대기
                self.page.wait_for_load_state("networkidle")
                
            # 네이버 검색
            elif "naver.com" in current_url:
                self.log_message.emit(f"네이버 검색: {query}", "INFO")
                
                # 검색창에 쿼리 입력
                self.page.fill('input#query', query)
                
                # 검색 버튼 클릭
                self.page.click('button.ico_search_submit')
                
                # 결과 로드 대기
                self.page.wait_for_load_state("networkidle")
                
            # 다음 검색
            elif "daum.net" in current_url:
                self.log_message.emit(f"다음 검색: {query}", "INFO")
                
                # 검색창에 쿼리 입력
                self.page.fill('input#q', query)
                
                # 검색 버튼 클릭
                self.page.click('.ico_pctop.btn_search')
                
                # 결과 로드 대기
                self.page.wait_for_load_state("networkidle")
                
            # 기타 사이트 (일반적인 검색창 처리)
            else:
                self.log_message.emit(f"일반 검색: {query}", "INFO")
                
                # 일반적인 검색창 선택자 시도
                search_selectors = [
                    'input[type="search"]',
                    'input[name="q"]',
                    'input[name="query"]',
                    'input[name="search"]',
                    'input.search',
                    'input.searchbox'
                ]
                
                # 검색창 찾기
                search_input = None
                for selector in search_selectors:
                    if self.page.query_selector(selector):
                        search_input = selector
                        break
                
                if search_input:
                    # 검색창에 쿼리 입력
                    self.page.fill(search_input, query)
                    
                    # Enter 키 입력
                    self.page.press(search_input, "Enter")
                    
                    # 결과 로드 대기
                    self.page.wait_for_load_state("networkidle")
                else:
                    error_msg = "검색창을 찾을 수 없습니다."
                    self.log_message.emit(error_msg, "WARNING")
                    return {"status": "error", "message": error_msg}
            
            # 검색 결과 URL 및 제목 가져오기
            result_url = self.page.url
            title = self.page.title()
            
            self.log_message.emit(f"검색 완료: {title}", "INFO")
            return {"status": "success", "title": title, "url": result_url, "query": query}
            
        except Exception as e:
            error_msg = f"검색 중 오류: {str(e)}"
            self.log_message.emit(error_msg, "ERROR")
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
    
    def click(self, selector: str) -> Dict[str, Any]:
        """요소 클릭"""
        if not self.page:
            error_msg = "열린 페이지가 없습니다."
            self.log_message.emit(error_msg, "ERROR")
            return {"status": "error", "message": error_msg}
        
        try:
            # 요소 존재 확인
            if not self.page.query_selector(selector):
                error_msg = f"선택자와 일치하는 요소를 찾을 수 없습니다: {selector}"
                self.log_message.emit(error_msg, "WARNING")
                return {"status": "error", "message": error_msg}
            
            # 요소 클릭
            self.log_message.emit(f"요소 클릭: {selector}", "INFO")
            self.page.click(selector)
            
            # 페이지 변화 대기
            self.page.wait_for_load_state("networkidle")
            
            # 현재 URL 및 제목 가져오기
            current_url = self.page.url
            title = self.page.title()
            
            self.log_message.emit(f"클릭 후 페이지: {title} ({current_url})", "INFO")
            return {"status": "success", "title": title, "url": current_url}
            
        except Exception as e:
            error_msg = f"요소 클릭 중 오류: {str(e)}"
            self.log_message.emit(error_msg, "ERROR")
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
    
    def fill(self, selector: str, value: str) -> Dict[str, Any]:
        """입력 필드에 텍스트 입력"""
        if not self.page:
            error_msg = "열린 페이지가 없습니다."
            self.log_message.emit(error_msg, "ERROR")
            return {"status": "error", "message": error_msg}
        
        try:
            # 요소 존재 확인
            if not self.page.query_selector(selector):
                error_msg = f"선택자와 일치하는 입력 필드를 찾을 수 없습니다: {selector}"
                self.log_message.emit(error_msg, "WARNING")
                return {"status": "error", "message": error_msg}
            
            # 요소에 텍스트 입력
            self.log_message.emit(f"텍스트 입력: {value} (선택자: {selector})", "INFO")
            self.page.fill(selector, value)
            
            return {"status": "success", "selector": selector, "value": value}
            
        except Exception as e:
            error_msg = f"텍스트 입력 중 오류: {str(e)}"
            self.log_message.emit(error_msg, "ERROR")
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
    
    def take_screenshot(self, path: Optional[str] = None) -> Dict[str, Any]:
        """스크린샷 촬영"""
        if not self.page:
            error_msg = "열린 페이지가 없습니다."
            self.log_message.emit(error_msg, "ERROR")
            return {"status": "error", "message": error_msg}
        
        try:
            # 스크린샷 파일 경로 설정
            if not path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                path = os.path.join(self.screenshot_dir, filename)
            
            # 스크린샷 촬영
            self.log_message.emit(f"스크린샷 촬영: {path}", "INFO")
            self.page.screenshot(path=path)
            
            return {"status": "success", "path": path}
            
        except Exception as e:
            error_msg = f"스크린샷 촬영 중 오류: {str(e)}"
            self.log_message.emit(error_msg, "ERROR")
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
    
    def extract_text(self, selector: str) -> Dict[str, Any]:
        """요소의 텍스트 추출"""
        if not self.page:
            error_msg = "열린 페이지가 없습니다."
            self.log_message.emit(error_msg, "ERROR")
            return {"status": "error", "message": error_msg}
        
        try:
            # 요소 존재 확인
            element = self.page.query_selector(selector)
            if not element:
                error_msg = f"선택자와 일치하는 요소를 찾을 수 없습니다: {selector}"
                self.log_message.emit(error_msg, "WARNING")
                return {"status": "error", "message": error_msg}
            
            # 요소의 텍스트 추출
            text = element.inner_text()
            self.log_message.emit(f"텍스트 추출: {text[:50]}{'...' if len(text) > 50 else ''}", "INFO")
            
            return {"status": "success", "text": text, "selector": selector}
            
        except Exception as e:
            error_msg = f"텍스트 추출 중 오류: {str(e)}"
            self.log_message.emit(error_msg, "ERROR")
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
    
    def wait_for(self, selector: str, timeout: int = 30) -> Dict[str, Any]:
        """요소가 나타날 때까지 대기"""
        if not self.page:
            error_msg = "열린 페이지가 없습니다."
            self.log_message.emit(error_msg, "ERROR")
            return {"status": "error", "message": error_msg}
        
        try:
            # 요소 대기
            self.log_message.emit(f"요소 대기: {selector} (최대 {timeout}초)", "INFO")
            element = self.page.wait_for_selector(selector, timeout=timeout * 1000)
            
            if element:
                self.log_message.emit(f"요소 발견됨: {selector}", "INFO")
                return {"status": "success", "selector": selector}
            else:
                error_msg = f"요소를 찾을 수 없습니다: {selector}"
                self.log_message.emit(error_msg, "WARNING")
                return {"status": "error", "message": error_msg}
            
        except Exception as e:
            error_msg = f"요소 대기 중 오류: {str(e)}"
            self.log_message.emit(error_msg, "ERROR")
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
    
    def close_browser(self) -> Dict[str, Any]:
        """브라우저 종료"""
        try:
            if self.browser:
                self.log_message.emit("브라우저 종료 중...", "INFO")
                self.browser.close()
                self.browser = None
                self.page = None
            
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
            
            self.log_message.emit("브라우저가 종료되었습니다.", "INFO")
            return {"status": "success"}
            
        except Exception as e:
            error_msg = f"브라우저 종료 중 오류: {str(e)}"
            self.log_message.emit(error_msg, "ERROR")
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}