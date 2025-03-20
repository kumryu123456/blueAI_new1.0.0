#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BlueAI 클라이언트 - 설치 스크립트
"""

from setuptools import setup, find_packages
import os

# README 파일 읽기
def read_readme():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()

# 버전 정보
VERSION = "0.1.0"

# 설치에 필요한 패키지
REQUIRED_PACKAGES = [
    "PyQt5>=5.15.0",
    "playwright>=1.20.0",
    "websocket-client>=1.2.0",
    "requests>=2.25.0"
]

# 개발용 추가 패키지
EXTRA_PACKAGES = {
    "dev": [
        "pytest>=6.0.0",
        "black>=21.5b2",
        "isort>=5.9.1",
        "pylint>=2.8.3",
        "pyinstaller>=4.3"
    ]
}

# 리소스 파일
DATA_FILES = [
    ("resources", ["client/resources/icon.png"])
]

setup(
    name="blueai-client",
    version=VERSION,
    description="BlueAI 서버와 통신하는 자동화 클라이언트",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="BlueAI Team",
    author_email="info@blueai.example.com",
    url="https://github.com/blueai/blueai-client",
    packages=find_packages(),
    install_requires=REQUIRED_PACKAGES,
    extras_require=EXTRA_PACKAGES,
    data_files=DATA_FILES,
    entry_points={
        "console_scripts": [
            "blueai-client=client.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)