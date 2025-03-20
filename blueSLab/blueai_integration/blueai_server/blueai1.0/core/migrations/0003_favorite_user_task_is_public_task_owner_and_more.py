# Generated by Django 5.1.7 on 2025-03-18 01:24

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_remove_task_is_favorite_alter_task_conversation_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='favorite',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='favorite_tasks', to=settings.AUTH_USER_MODEL, verbose_name='사용자'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='task',
            name='is_public',
            field=models.BooleanField(default=False, verbose_name='공개 여부'),
        ),
        migrations.AddField(
            model_name='task',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='owned_tasks', to=settings.AUTH_USER_MODEL, verbose_name='소유자'),
        ),
        migrations.AddField(
            model_name='task',
            name='shared_with',
            field=models.ManyToManyField(blank=True, related_name='shared_tasks', to=settings.AUTH_USER_MODEL, verbose_name='공유 대상'),
        ),
        migrations.AlterUniqueTogether(
            name='favorite',
            unique_together={('task', 'user')},
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, verbose_name='프로젝트 이름')),
                ('description', models.TextField(blank=True, verbose_name='설명')),
                ('is_public', models.BooleanField(default=False, verbose_name='공개 여부')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='수정일')),
                ('max_tasks', models.IntegerField(default=1000, verbose_name='최대 작업 수')),
                ('storage_limit_mb', models.IntegerField(default=1000, verbose_name='저장 공간 제한 (MB)')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owned_projects', to=settings.AUTH_USER_MODEL, verbose_name='소유자')),
            ],
            options={
                'verbose_name': '프로젝트',
                'verbose_name_plural': '프로젝트 목록',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='ProjectMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('host', '소유자'), ('admin', '관리자'), ('editor', '편집자'), ('viewer', '뷰어'), ('guest', '게스트')], default='guest', max_length=20, verbose_name='역할')),
                ('invited_at', models.DateTimeField(auto_now_add=True, verbose_name='초대일')),
                ('joined_at', models.DateTimeField(blank=True, null=True, verbose_name='참여일')),
                ('invited_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_invitations', to=settings.AUTH_USER_MODEL, verbose_name='초대자')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='core.project', verbose_name='프로젝트')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_memberships', to=settings.AUTH_USER_MODEL, verbose_name='사용자')),
            ],
            options={
                'verbose_name': '프로젝트 멤버',
                'verbose_name_plural': '프로젝트 멤버 목록',
                'unique_together': {('project', 'user')},
            },
        ),
        migrations.CreateModel(
            name='ProjectTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='core.project')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='core.task')),
            ],
            options={
                'verbose_name': '프로젝트 작업',
                'verbose_name_plural': '프로젝트 작업 목록',
                'unique_together': {('project', 'task')},
            },
        ),
    ]
