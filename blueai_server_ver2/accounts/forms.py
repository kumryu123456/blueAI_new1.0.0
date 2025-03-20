# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from .models import User, UserProfile

class CustomUserCreationForm(UserCreationForm):
    """사용자 회원가입 폼"""
    email = forms.EmailField(
        label=_('이메일'),
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '이메일 주소'})
    )
    first_name = forms.CharField(
        label=_('이름'),
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '이름'})
    )
    last_name = forms.CharField(
        label=_('성'),
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '성'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '사용자 아이디'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '비밀번호'
        })
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '비밀번호 확인'
        })
    
    def clean_email(self):
        """이메일 중복 검사"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('이미 사용 중인 이메일입니다.'))
        return email

class CustomAuthenticationForm(AuthenticationForm):
    """로그인 폼"""
    username = forms.CharField(
        label=_('사용자 아이디 또는 이메일'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '사용자 아이디 또는 이메일'})
    )
    password = forms.CharField(
        label=_('비밀번호'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '비밀번호'})
    )
    
    def clean_username(self):
        """이메일로 로그인 지원"""
        username = self.cleaned_data.get('username')
        if '@' in username:
            try:
                user = User.objects.get(email=username)
                return user.username
            except User.DoesNotExist:
                pass
        return username

class CustomUserChangeForm(UserChangeForm):
    """사용자 정보 수정 폼"""
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'display_name', 'profile_image', 'bio')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'display_name': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 비밀번호 필드 제거 (별도 페이지에서 처리)
        if 'password' in self.fields:
            del self.fields['password']

class ProfileUpdateForm(forms.ModelForm):
    """프로필 정보 수정 폼"""
    class Meta:
        model = User
        fields = ('display_name', 'first_name', 'last_name', 'email', 'profile_image', 'bio')
        widgets = {
            'display_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    # 추가 필드 (UserProfile 모델용)
    phone = forms.CharField(
        label=_('전화번호'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    organization = forms.CharField(
        label=_('조직'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    position = forms.CharField(
        label=_('직책'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    theme_preference = forms.ChoiceField(
        label=_('테마 설정'),
        choices=[('light', '라이트'), ('dark', '다크'), ('system', '시스템 설정')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    language_preference = forms.ChoiceField(
        label=_('언어 설정'),
        choices=[('ko', '한국어'), ('en', '영어'), ('ja', '일본어'),
                ('zh', '중국어'), ('fr', '프랑스어'), ('pt', '포르투갈어')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class PasswordResetForm(forms.Form):
    """비밀번호 재설정 요청 폼"""
    email_or_phone = forms.CharField(
        label='이메일 주소 또는 휴대폰 번호', 
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '이메일 또는 휴대폰 번호를 입력하세요'})
    )
    new_password1 = forms.CharField(
        label='새 비밀번호', 
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    new_password2 = forms.CharField(
        label='새 비밀번호 확인', 
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    
    def clean_email_or_phone(self):
        email_or_phone = self.cleaned_data.get('email_or_phone')
        if not email_or_phone:
            raise forms.ValidationError('이메일 주소 또는 휴대폰 번호를 입력하세요.')
        return email_or_phone
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', '비밀번호가 일치하지 않습니다.')
            
        return cleaned_data

class PasswordChangeForm(forms.Form):
    """비밀번호 변경 폼"""
    old_password = forms.CharField(
        label=_('현재 비밀번호'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '현재 비밀번호'})
    )
    new_password1 = forms.CharField(
        label=_('새 비밀번호'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '새 비밀번호'}),
        validators=[validate_password]
    )
    new_password2 = forms.CharField(
        label=_('새 비밀번호 확인'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '새 비밀번호 확인'})
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_old_password(self):
        """현재 비밀번호 검증"""
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError(_('현재 비밀번호가 올바르지 않습니다.'))
        return old_password
    
    def clean_new_password2(self):
        """새 비밀번호 일치 검증"""
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError(_('두 비밀번호가 일치하지 않습니다.'))
        return password2
    
    def save(self, commit=True):
        """비밀번호 저장"""
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user
    
def password_reset_request_view(request):
    """비밀번호 재설정 요청 뷰 - 이메일 또는 휴대폰 번호 지원"""
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email_or_phone = form.cleaned_data['email_or_phone']
            
            # Check if input is email or phone number
            is_email = '@' in email_or_phone  # Simple email check
            
            if is_email:
                # Find users by email
                users = User.objects.filter(email=email_or_phone)
            else:
                # Find users by phone number (assuming phone is stored in UserProfile)
                profiles = UserProfile.objects.filter(phone=email_or_phone)
                users = User.objects.filter(id__in=profiles.values_list('user_id', flat=True))
            
            if not users.exists():
                messages.error(request, '해당 정보로 등록된 사용자가 없습니다.')
                return render(request, 'accounts/password_reset_request.html', {'form': form})
            
            # Use the first user found (can be refined based on additional criteria if needed)
            user = users.first()
            
            # Generate reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            current_site = get_current_site(request)
            
            if is_email:
                # Send email reset
                mail_subject = '[BlueAI] 비밀번호 재설정 요청'
                message = render_to_string('accounts/password_reset_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': uid,
                    'token': token,
                    'protocol': 'https' if request.is_secure() else 'http',
                })
                
                email_message = EmailMultiAlternatives(mail_subject, message, settings.DEFAULT_FROM_EMAIL, [email_or_phone])
                email_message.content_subtype = 'html'
                email_message.send()
                
                messages.success(request, '비밀번호 재설정 링크가 이메일로 발송되었습니다.')
            else:
                # For SMS implementation, you would need an SMS service provider
                # This is a placeholder for SMS functionality
                # You would typically use a service like Twilio, AWS SNS, etc.
                
                # Store the token in session for phone verification
                request.session['reset_token'] = {
                    'uid': uid,
                    'token': token,
                    'phone': email_or_phone,
                    'expiry': (timezone.now() + timezone.timedelta(minutes=30)).isoformat()
                }
                
                # Redirect to phone verification page
                return redirect('accounts:password_reset_phone_verify')
            
            return redirect('accounts:login')
    else:
        form = PasswordResetForm()
    
    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset_phone_verify(request):
    """휴대폰 번호로 비밀번호 재설정 인증 뷰"""
    if 'reset_token' not in request.session:
        messages.error(request, '유효하지 않은 세션입니다. 다시 시도해주세요.')
        return redirect('accounts:password_reset_request')
    
    reset_token = request.session['reset_token']
    
    # Check if token has expired
    expiry = datetime.fromisoformat(reset_token['expiry'])
    if timezone.now() > expiry:
        del request.session['reset_token']
        messages.error(request, '인증 시간이 만료되었습니다. 다시 시도해주세요.')
        return redirect('accounts:password_reset_request')
    
    if request.method == 'POST':
        verification_code = request.POST.get('verification_code')
        
        # In a real implementation, you would verify the code sent via SMS
        # For this example, we'll use a simple code '123456' for demonstration purposes
        if verification_code == '123456':  # This is just a placeholder
            uid = reset_token['uid']
            token = reset_token['token']
            
            # Clean up the session
            del request.session['reset_token']
            
            # Redirect to password reset confirm view with the token
            return redirect('accounts:password_reset_confirm', uidb64=uid, token=token)
        else:
            messages.error(request, '인증 코드가 일치하지 않습니다. 다시 시도해주세요.')
    
    return render(request, 'accounts/password_reset_phone_verify.html', {
        'phone': reset_token['phone']
    })