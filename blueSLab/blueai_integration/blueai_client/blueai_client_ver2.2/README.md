# BlueAI 클라이언트

BlueAI 서버와 통신하여 웹 자동화 작업을 수행하는 클라이언트 애플리케이션입니다.

## 주요 기능

- BlueAI 서버와의 실시간 통신 (WebSocket)
- Playwright를 이용한 웹 자동화
- 간단한 PyQt 기반 사용자 인터페이스
- 작업 상태 모니터링 및 로깅
- 시스템 트레이 통합

## 시스템 요구사항

- Python 3.8 이상
- PyQt5
- Playwright
- Websocket-client
- Requests

## 설치 방법

### 소스코드로 설치

```bash
# 저장소 클론
git clone https://github.com/blueai/blueai-client.git
cd blueai-client

# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -e .

# Playwright 브라우저 설치
python -m playwright install
```

### pip로 설치 (향후 지원 예정)

```bash
pip install blueai-client

# Playwright 브라우저 설치
python -m playwright install
```

## 사용 방법

### 기본 실행

```bash
blueai-client
```

### 명령줄 옵션

```bash
# 서버 URL 지정
blueai-client --server ws://myserver.com:8080

# 헤드리스 모드로 실행
blueai-client --headless

# 디버그 모드 활성화
blueai-client --debug
```

## 폴더 구조

```
blueai-client/
├── client/
│   ├── __init__.py
│   ├── main.py                      # 애플리케이션 진입점
│   ├── core/
│   │   ├── __init__.py
│   │   ├── server_client.py         # 서버 통신 담당
│   │   └── automation_engine.py     # 자동화 실행 엔진
│   ├── automations/
│   │   ├── __init__.py
│   │   ├── web_automation.py        # Playwright 기반 웹 자동화
│   │   └── desktop_automation.py    # (향후 구현) PyAutoGUI 기반 데스크톱 자동화
│   ├── ui/
│   │   ├── __init__.py
│   │   └── main_window.py           # 메인 UI 클래스
│   └── resources/
│       └── icon.png                 # 애플리케이션 아이콘
└── setup.py                         # 설치 및 배포 스크립트
```

## 개발 계획

- [x] 기본 UI 구현
- [x] 서버 연결 모듈 구현
- [x] 웹 자동화 모듈 구현
- [ ] 데스크톱 자동화 모듈 추가
- [ ] OCR 및 이미지 인식 기능 추가
- [ ] 스크립트 녹화 및 재생 기능
- [ ] 플러그인 시스템 구현

## 라이센스

MIT License

## 연락처

- 이메일: info@blueai.example.com
- 이슈 트래커: https://github.com/blueai/blueai-client/issues