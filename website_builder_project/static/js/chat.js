// static/js/chat.js 파일을 생성하세요

/**
 * 웹사이트 빌더 채팅 인터페이스
 */
class ChatInterface {
  constructor(options) {
    // 필수 요소
    this.chatContainer = document.getElementById(
      options.chatContainerId || "chatMessages"
    );
    this.chatForm = document.getElementById(options.chatFormId || "chatForm");
    this.messageInput = document.getElementById(
      options.messageInputId || "messageInput"
    );
    this.previewFrame = document.getElementById(
      options.previewFrameId || "previewFrame"
    );
    this.websiteId = options.websiteId;

    // 추가 옵션
    this.sendMessageUrl = options.sendMessageUrl;
    this.refreshPreviewBtn = document.getElementById(
      options.refreshPreviewBtnId || "refreshPreview"
    );
    this.saveWebsiteBtn = document.getElementById(
      options.saveWebsiteBtnId || "saveWebsite"
    );
    this.saveWebsiteUrl = options.saveWebsiteUrl;

    // 상태 관리
    this.isProcessing = false;
    this.messageQueue = [];

    // 이벤트 리스너 등록
    this.initEventListeners();

    // 초기화 시 스크롤을 맨 아래로
    this.scrollToBottom();
  }

  /**
   * 이벤트 리스너 초기화
   */
  initEventListeners() {
    // 폼 제출 이벤트
    this.chatForm.addEventListener("submit", (e) => {
      e.preventDefault();
      this.sendMessage();
    });

    // 엔터 키 제출 (Shift+Enter는 줄바꿈)
    this.messageInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.chatForm.dispatchEvent(new Event("submit"));
      }
    });

    // 미리보기 새로고침 버튼
    if (this.refreshPreviewBtn) {
      this.refreshPreviewBtn.addEventListener("click", () =>
        this.refreshPreview()
      );
    }

    // 저장 버튼
    if (this.saveWebsiteBtn) {
      this.saveWebsiteBtn.addEventListener("click", () => this.saveWebsite());
    }

    // 자동 높이 조정
    this.messageInput.addEventListener("input", () => {
      this.messageInput.style.height = "auto";
      this.messageInput.style.height = this.messageInput.scrollHeight + "px";
    });
  }

  /**
   * 메시지 전송
   */
  sendMessage() {
    const message = this.messageInput.value.trim();
    if (!message || this.isProcessing) return;

    // 사용자 메시지 UI에 추가
    this.addMessageToUI("user", message);

    // 입력창 비우기
    this.messageInput.value = "";
    this.messageInput.style.height = "auto";

    // 로딩 표시기 추가
    this.addLoadingIndicator();

    // 처리 중 상태로 변경
    this.isProcessing = true;

    // CSRF 토큰 가져오기
    const csrfToken = document.querySelector(
      "[name=csrfmiddlewaretoken]"
    ).value;

    // AJAX 요청으로 메시지 전송
    fetch(this.sendMessageUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify({
        message: message,
      }),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("서버 응답 오류: " + response.status);
        }
        return response.json();
      })
      .then((data) => {
        // 로딩 표시기 제거
        this.removeLoadingIndicator();

        // AI 응답 UI에 추가
        this.addMessageToUI("assistant", data.response);

        // 웹사이트 코드 업데이트됐다면 미리보기 새로고침
        if (data.website_updated) {
          this.refreshPreview();
        }

        // 처리 완료 상태로 변경
        this.isProcessing = false;

        // 대기 중인 메시지가 있으면 처리
        if (this.messageQueue.length > 0) {
          const nextMessage = this.messageQueue.shift();
          this.messageInput.value = nextMessage;
          this.sendMessage();
        }
      })
      .catch((error) => {
        console.error("Error:", error);

        // 로딩 표시기 제거
        this.removeLoadingIndicator();

        // 에러 메시지 표시
        this.addMessageToUI(
          "assistant",
          "죄송합니다, 메시지 처리 중 오류가 발생했습니다: " + error.message
        );

        // 처리 완료 상태로 변경
        this.isProcessing = false;
      });
  }

  /**
   * UI에 메시지 추가
   */
  addMessageToUI(role, content) {
    const messageDiv = document.createElement("div");
    messageDiv.className = "message " + role;

    // 마크다운 처리 (선택적)
    if (typeof marked !== "undefined") {
    // marked 버전에 따라 호출 방식이 다름
    if (typeof marked.parse === "function") {
        messageDiv.innerHTML = marked.parse(content);
    } else if (typeof marked === "function") {
        messageDiv.innerHTML = marked(content);
    } else {
        messageDiv.textContent = content;
    }
    } else {
    // 줄바꿈을 <br>로 변환
    messageDiv.textContent = content;
    }

    this.chatContainer.appendChild(messageDiv);
    this.scrollToBottom();
  }

  /**
   * 로딩 표시기 추가
   */
  addLoadingIndicator() {
    const loadingDiv = document.createElement("div");
    loadingDiv.className = "message assistant loading-message";
    loadingDiv.innerHTML =
      '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    loadingDiv.id = "loadingIndicator";
    this.chatContainer.appendChild(loadingDiv);
    this.scrollToBottom();
  }

  /**
   * 로딩 표시기 제거
   */
  removeLoadingIndicator() {
    const loadingIndicator = document.getElementById("loadingIndicator");
    if (loadingIndicator) {
      loadingIndicator.remove();
    }
  }

  /**
   * 채팅창을 맨 아래로 스크롤
   */
  scrollToBottom() {
    this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
  }

  /**
   * 미리보기 새로고침
   */
  refreshPreview() {
    if (this.previewFrame) {
      this.previewFrame.src = this.previewFrame.src;
    }
  }

  /**
   * 웹사이트 저장
   */
  saveWebsite() {
    if (!this.saveWebsiteUrl) return;

    const csrfToken = document.querySelector(
      "[name=csrfmiddlewaretoken]"
    ).value;

    // 저장 버튼 비활성화 및 로딩 상태 표시
    if (this.saveWebsiteBtn) {
      this.saveWebsiteBtn.disabled = true;
      this.saveWebsiteBtn.innerHTML =
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 저장 중...';
    }

    fetch(this.saveWebsiteUrl, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          this.showToast(
            "성공",
            "웹사이트가 성공적으로 저장되었습니다.",
            "success"
          );
        } else {
          this.showToast(
            "오류",
            "저장 중 문제가 발생했습니다: " + (data.error || "알 수 없는 오류"),
            "danger"
          );
        }

        // 저장 버튼 상태 복원
        if (this.saveWebsiteBtn) {
          this.saveWebsiteBtn.disabled = false;
          this.saveWebsiteBtn.innerHTML = '<i class="bi bi-save"></i> 저장하기';
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        this.showToast(
          "오류",
          "저장 중 문제가 발생했습니다: " + error.message,
          "danger"
        );

        // 저장 버튼 상태 복원
        if (this.saveWebsiteBtn) {
          this.saveWebsiteBtn.disabled = false;
          this.saveWebsiteBtn.innerHTML = '<i class="bi bi-save"></i> 저장하기';
        }
      });
  }

  /**
   * 토스트 메시지 표시
   */
  showToast(title, message, type = "info") {
    // 이미 토스트 컨테이너가 있는지 확인
    let toastContainer = document.querySelector(".toast-container");

    // 없으면 생성
    if (!toastContainer) {
      toastContainer = document.createElement("div");
      toastContainer.className =
        "toast-container position-fixed bottom-0 end-0 p-3";
      document.body.appendChild(toastContainer);
    }

    // 고유 ID 생성
    const toastId = "toast-" + Date.now();

    // 토스트 HTML
    const toastHtml = `
            <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header bg-${type} text-white">
                    <strong class="me-auto">${title}</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

    // 토스트 추가
    toastContainer.insertAdjacentHTML("beforeend", toastHtml);

    // 부트스트랩 토스트 초기화 및 표시
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
      autohide: true,
      delay: 5000,
    });
    toast.show();

    // 자동 제거 (애니메이션 완료 후)
    toastElement.addEventListener("hidden.bs.toast", () => {
      toastElement.remove();
    });
  }
}

// 페이지 로드 시 초기화
document.addEventListener("DOMContentLoaded", function () {
  // 웹사이트 ID가 정의되어 있는지 확인
  const websiteIdElement = document.getElementById("websiteId");
  if (!websiteIdElement) return;

  const websiteId = websiteIdElement.value;

  // 채팅 인터페이스 초기화
  const chat = new ChatInterface({
    websiteId: websiteId,
    sendMessageUrl: `/website/${websiteId}/send-message/`,
    saveWebsiteUrl: `/website/${websiteId}/save/`,
  });
});
