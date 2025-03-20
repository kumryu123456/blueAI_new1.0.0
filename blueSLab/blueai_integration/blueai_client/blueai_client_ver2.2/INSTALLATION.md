# BlueAI 클라이언트 설치 가이드

이 문서는 BlueAI 클라이언트 애플리케이션의 설치 및 실행 방법에 대해 상세히 설명합니다.

## 사전 요구사항

- Python 3.8 이상
- pip (파이썬 패키지 관리자)
- 인터넷 연결

## 설치 방법

### 1. 저장소 클론 또는 소스코드 다운로드

```bash
# Git을 사용하는 경우
git clone https://github.com/blueai/blueai-client.git
cd blueai-client

# 또는 압축 파일로 다운로드한 경우
# 압축 해제 후 해당 디렉토리로 이동
cd blueai-client
```

### 2. 가상환경 생성 (선택사항이지만 권장)

```bash
# Linux/macOS
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. 의존성 설치

```bash
# 개발 모드로 설치
pip install -e .

# 또는 일반 설치
pip install .
```

### 4. Playwright 설치

Playwright는 웹 자동화를 위한 필수 라이브러리입니다. 
브라우저를 제어하기 위해 필요한 브라우저 바이너리도 함께 설치해야 합니다.

```bash
# Playwright 브라우저 설치
python -m playwright install
```

이 명령은 Chromium, Firefox, WebKit 브라우저를 자동으로 다운로드하고 설치합니다.

## 프로젝트 구조 확인

설치 후에는 다음과 같은 디렉토리 구조가 생성됩니다:

```
~/BlueAI/
├── config/       # 설정 파일
├── logs/         # 로그 파일
└── screenshots/  # 스크린샷 저장 디렉토리
```

## 애플리케이션 실행

### 기본 실행

```bash
# 설치 후 실행
blueai-client

# 또는 소스 디렉토리에서 직접 실행
python -m client.main
```

### 명령줄 옵션 사용

```bash
# 서버 URL 지정
blueai-client --server ws://example.com:8080

# 헤드리스 모드로 실행 (브라우저 UI 없음)
blueai-client --headless

# 디버그 모드로 실행 (상세 로깅)
blueai-client --debug
```

## 문제 해결

### 의존성 관련 오류

의존성 관련 오류가 발생하면 다음 명령으로 필요한 패키지를 직접 설치할 수 있습니다:

```bash
pip install PyQt5 playwright websocket-client requests
```

### Playwright 오류

Playwright 관련 오류가 발생하면 다음 명령으로 Playwright를 재설치해 보세요:

```bash
pip uninstall playwright -y
pip install playwright
python -m playwright install
```

### 연결 오류

서버 연결 오류가 발생하면 다음을 확인하세요:

1. 서버 URL이 올바른지 확인
2. 서버가 실행 중인지 확인
3. 네트워크 연결 상태 확인
4. 방화벽 설정 확인

## 로그 확인

애플리케이션 로그는 다음 위치에 저장됩니다:

```
~/BlueAI/logs/blueai_client.log
```

로그 파일을 확인하여 문제 해결에 도움을 받을 수 있습니다.