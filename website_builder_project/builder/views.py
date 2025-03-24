# builder/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import zipfile
import os
import openai

from .models import Website, Conversation, Message

# OpenAI API 키 설정
from django.conf import settings
openai.api_key = settings.OPENAI_API_KEY

@login_required
def dashboard(request):
    """사용자의 웹사이트 목록을 보여주는 대시보드"""
    websites = Website.objects.filter(user=request.user)
    return render(request, 'builder/dashboard.html', {'websites': websites})

@login_required
def create_website(request):
    """새 웹사이트 생성"""
    if request.method == 'POST':
        name = request.POST.get('name')
        purpose = request.POST.get('purpose')
        target_audience = request.POST.get('target_audience', '')
        
        # 기본 웹사이트 객체 생성
        website = Website.objects.create(
            user=request.user,
            name=name,
            purpose=purpose,
            target_audience=target_audience,
            design_style='',
            features=[],
            pages=[],
            html_code='<div class="container"><h1>' + name + '</h1><p>웹사이트 제작 중...</p></div>',
            css_code='/* 기본 스타일 */',
            js_code='// 자바스크립트 코드'
        )
        
        # 초기 대화 생성
        conversation = Conversation.objects.create(website=website)
        
        return redirect('edit_website', website_id=website.id)
    
    return render(request, 'builder/create_website.html')

@login_required
def edit_website(request, website_id):
    """웹사이트 편집 페이지"""
    website = get_object_or_404(Website, id=website_id, user=request.user)
    
    # 기존 대화가 있는지 확인하고 없으면 생성
    conversation, created = Conversation.objects.get_or_create(website=website)
    
    return render(request, 'builder/editor.html', {
        'website': website,
        'conversation': conversation
    })

@login_required
def preview_website(request, website_id):
    """웹사이트 미리보기"""
    website = get_object_or_404(Website, id=website_id, user=request.user)
    html_content = website.get_full_html()
    
    return HttpResponse(html_content)

@login_required
def send_message(request, website_id):
    """사용자 메시지 전송 및 AI 응답 생성"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됨'}, status=405)
    
    website = get_object_or_404(Website, id=website_id, user=request.user)
    conversation, created = Conversation.objects.get_or_create(website=website)
    
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        if not user_message:
            return JsonResponse({'error': '메시지가 비어있음'}, status=400)
        
        # 사용자 메시지 저장
        Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_message
        )
        
        # 이전 대화 내용 가져오기
        messages_history = []
        for msg in conversation.messages.all().order_by('timestamp'):
            messages_history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # AI 시스템 메시지 추가
        system_message = {
            "role": "system",
            "content": f"""
            당신은 웹사이트 빌더 AI 어시스턴트입니다. 사용자의 요구사항에 맞는 웹사이트를 만드는 것을 도와주세요.
            
            웹사이트 정보:
            - 이름: {website.name}
            - 목적: {website.purpose}
            - 대상: {website.target_audience}
            
            당신은 HTML, CSS, JavaScript 코드를 생성할 수 있습니다. 사용자의 요청에 따라 웹사이트의 내용, 디자인, 기능을 업데이트하세요.
            
            응답 형식:
            1. 먼저 사용자 요청에 대한 답변을 작성하세요.
            2. 반드시 응답 끝에 다음 형식으로 코드를 포함하세요:
            
            ---HTML---
            (HTML 코드)
            ---CSS---
            (CSS 코드)
            ---JS---
            (JavaScript 코드)
            ---END---
            
            모든 응답에 항상 위 형식의 코드 블록을 포함해야 합니다. 코드가 없는 응답은 허용되지 않습니다.
            """
        }
        
        messages = [system_message] + messages_history
        
        # OpenAI API 호출
        response = openai.chat.completions.create(
            model="gpt-4",  # 또는 이용 가능한 다른 모델
            messages=messages,
            max_tokens=2000
        )
        
        ai_response = response.choices[0].message.content
        
        # 응답에서 코드 부분 분리
        html_code = None
        css_code = None
        js_code = None
        
        website_updated = False
        
        if "---HTML---" in ai_response and "---END---" in ai_response:
            # HTML 코드 추출
            html_start = ai_response.find("---HTML---") + len("---HTML---")
            css_start = ai_response.find("---CSS---")
            html_code = ai_response[html_start:css_start].strip()
            
            # CSS 코드 추출
            css_start = ai_response.find("---CSS---") + len("---CSS---")
            js_start = ai_response.find("---JS---")
            css_code = ai_response[css_start:js_start].strip()
            
            # JS 코드 추출
            js_start = ai_response.find("---JS---") + len("---JS---")
            end_marker = ai_response.find("---END---")
            js_code = ai_response[js_start:end_marker].strip()
            
            # 추출된 코드 부분 제거
            response_content = ai_response[:ai_response.find("---HTML---")].strip()
            
            # 웹사이트 코드 업데이트
            if html_code:
                website.html_code = html_code
            if css_code:
                website.css_code = css_code
            if js_code:
                website.js_code = js_code
            
            website.updated_at = timezone.now()
            website.save()
            website_updated = True
            
            # 응답 메시지는 코드 부분을 제외한 내용만 포함
            ai_response = response_content
        
        # AI 응답 메시지 저장
        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=ai_response
        )
        
        return JsonResponse({
            'response': ai_response,
            'website_updated': website_updated
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def save_website(request, website_id):
    """웹사이트 변경사항 저장"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됨'}, status=405)
    
    website = get_object_or_404(Website, id=website_id, user=request.user)
    
    try:
        # 저장 시간 업데이트
        website.updated_at = timezone.now()
        website.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@login_required
def clear_conversation(request, website_id):
    """대화 내역 초기화"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됨'}, status=405)
    
    website = get_object_or_404(Website, id=website_id, user=request.user)
    
    try:
        # 기존 대화 삭제
        conversations = Conversation.objects.filter(website=website)
        for conversation in conversations:
            # 메시지 먼저 삭제
            Message.objects.filter(conversation=conversation).delete()
            # 대화 삭제
            conversation.delete()
        
        # 새 대화 생성
        Conversation.objects.create(website=website)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_website_code(request, website_id):
    """웹사이트 코드 가져오기 (AJAX)"""
    website = get_object_or_404(Website, id=website_id, user=request.user)
    
    return JsonResponse({
        'html_code': website.html_code,
        'css_code': website.css_code,
        'js_code': website.js_code
    })

@login_required
def update_website_code(request, website_id):
    """웹사이트 코드 업데이트 (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됨'}, status=405)
    
    website = get_object_or_404(Website, id=website_id, user=request.user)
    
    try:
        data = json.loads(request.body)
        
        # 코드 업데이트
        if 'html_code' in data:
            website.html_code = data['html_code']
        if 'css_code' in data:
            website.css_code = data['css_code']
        if 'js_code' in data:
            website.js_code = data['js_code']
        
        website.updated_at = timezone.now()
        website.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def export_website(request, website_id):
    """웹사이트 코드 내보내기"""
    website = get_object_or_404(Website, id=website_id, user=request.user)
    
    # 모든 파일을 담을 ZIP 파일 생성
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{website.name.replace(" ", "_")}.zip"'
    
    with zipfile.ZipFile(response, 'w') as zip_file:
        # HTML 파일 추가
        zip_file.writestr('index.html', website.get_full_html())
        
        # CSS 파일 추가 (분리된 파일로)
        if website.css_code.strip():
            zip_file.writestr('style.css', website.css_code)
        
        # JavaScript 파일 추가 (분리된 파일로)
        if website.js_code.strip():
            zip_file.writestr('script.js', website.js_code)
        
        # README 파일 추가
        readme_content = f"""# {website.name}

## 개요
{website.purpose}

## 대상 사용자
{website.target_audience}

## 기능
- {', '.join(website.features) if website.features else '기본 기능'}

## 생성일
{website.created_at.strftime('%Y-%m-%d')}

## 수정일
{website.updated_at.strftime('%Y-%m-%d %H:%M:%S')}

이 웹사이트는 AI 웹사이트 빌더를 사용하여 생성되었습니다.
"""
        zip_file.writestr('README.md', readme_content)
    
    return response