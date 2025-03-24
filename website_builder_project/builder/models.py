from django.db import models
from django.contrib.auth.models import User

class Website(models.Model):
    # 기본 정보
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='websites')
    name = models.CharField(max_length=200, verbose_name="웹사이트 이름")
    purpose = models.TextField(verbose_name="웹사이트 목적")
    target_audience = models.CharField(max_length=200, verbose_name="대상 사용자", blank=True)
    
    # 디자인 관련 정보
    design_style = models.CharField(max_length=100, verbose_name="디자인 스타일", blank=True)
    
    # 페이지 및 기능 정보
    features = models.JSONField(default=list, verbose_name="핵심 기능")
    pages = models.JSONField(default=list, verbose_name="페이지 구성")
    
    # 코드 필드
    html_code = models.TextField(blank=True, verbose_name="HTML 코드")
    css_code = models.TextField(blank=True, verbose_name="CSS 코드")
    js_code = models.TextField(blank=True, verbose_name="JavaScript 코드")
    
    # 메타데이터
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    class Meta:
        verbose_name = "웹사이트"
        verbose_name_plural = "웹사이트 목록"
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.name
    
    def get_full_html(self):
        """전체 HTML 문서 생성"""
        return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.name}</title>
    <style>
        {self.css_code}
    </style>
</head>
<body>
    {self.html_code}
    
    <script>
        {self.js_code}
    </script>
</body>
</html>
        """


class Conversation(models.Model):
    """대화 내역을 저장하는 모델"""
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='conversations')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Conversation for {self.website.name} ({self.timestamp})"


class Message(models.Model):
    """대화 내 개별 메시지"""
    ROLE_CHOICES = [
        ('user', '사용자'),
        ('assistant', 'AI 어시스턴트'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}..."