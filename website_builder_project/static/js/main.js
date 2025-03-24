// 페이지 로드 완료 시 실행
document.addEventListener("DOMContentLoaded", function () {
  // 자동 높이 조정 텍스트 영역
  const autoResizeTextareas = document.querySelectorAll(".auto-resize");
  autoResizeTextareas.forEach((textarea) => {
    textarea.addEventListener("input", function () {
      this.style.height = "auto";
      this.style.height = this.scrollHeight + "px";
    });

    // 초기 높이 설정
    textarea.dispatchEvent(new Event("input"));
  });

  // 토스트 메시지 초기화 (부트스트랩)
  const toastElList = [].slice.call(document.querySelectorAll(".toast"));
  toastElList.map(function (toastEl) {
    return new bootstrap.Toast(toastEl);
  });

  // 툴팁 초기화 (부트스트랩)
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});

// 확인 대화상자 함수
function confirmAction(message, callback) {
  if (confirm(message)) {
    callback();
  }
}

// AJAX 요청 헬퍼 함수
function ajaxRequest(url, method, data, successCallback, errorCallback) {
  const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

  fetch(url, {
    method: method,
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify(data),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      if (successCallback) successCallback(data);
    })
    .catch((error) => {
      console.error("Error:", error);
      if (errorCallback) errorCallback(error);
    });
}
