from django.contrib import admin
from .models import Website, Conversation, Message

@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'purpose', 'design_style', 'created_at', 'updated_at')
    list_filter = ('design_style', 'created_at')
    search_fields = ('name', 'purpose', 'target_audience')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'name', 'purpose', 'target_audience')
        }),
        ('디자인 및 구성', {
            'fields': ('design_style', 'features', 'pages')
        }),
        ('코드', {
            'fields': ('html_code', 'css_code', 'js_code'),
            'classes': ('collapse',)
        }),
        ('메타데이터', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('timestamp',)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('website', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('website__name',)
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('get_website', 'role', 'content_preview', 'timestamp')
    list_filter = ('role', 'timestamp')
    search_fields = ('content', 'conversation__website__name')
    
    def get_website(self, obj):
        return obj.conversation.website.name
    get_website.short_description = '웹사이트'
    
    def content_preview(self, obj):
        return obj.content[:50] + ('...' if len(obj.content) > 50 else '')
    content_preview.short_description = '내용'