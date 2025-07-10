# 💤 Sleep Tracker Web App

Flask 기반의 수면 기록 웹 애플리케이션입니다.  
서버 사이드 렌더링(SSR) 방식과 JWT 기반 인증 시스템을 도입하여  
보다 안정적이고 보안성 높은 사용자 경험을 제공합니다.

---

## 🚀 주요 기능

- 회원가입 및 JWT 로그인/로그아웃
- 수면 시간 측정 (수면 시작/종료 버튼)
- 일일 수면 기록 저장 및 시각화
- 목표 기상 시간과 실제 기상 시간 비교
- 그룹 내 사용자들의 수면 통계 조회
- JWT Refresh 토큰을 활용한 자동 로그인 연장
- 이메일을 통한 비밀번호 찾기 기능 (Gmail SMTP)

---

## 🛠️ 기술 스택

- **Backend**: Flask, Flask-JWT-Extended, PyMongo
- **Frontend**: HTML, CSS, JavaScript, Jinja2 (SSR)
- **Database**: MongoDB
- **Authentication**: JWT (JSON Web Token)
- **Email Notification**: Gmail SMTP + Python smtplib

---

## 📦 SSR & JWT 구조 개요

### ✅ SSR (Server-Side Rendering)

- Flask + Jinja2 템플릿 기반 렌더링
- 인증 상태에 따라 동적 콘텐츠 조건부 렌더링
- 일부 상태 정보는 AJAX로 비동기 갱신

### 🔐 JWT 인증 방식

- 로그인 시 Access Token + Refresh Token 발급
- Access Token은 JSON 응답, Refresh Token은 HTTP-Only 쿠키로 전달
- `/refresh` 경로를 통한 자동 로그인 연장
- 로그아웃 시 토큰 삭제 및 블랙리스트 처리

---

## ⚙️ 설치 및 실행 방법

### 1. 저장소 클론

```bash
git clone https://github.com/your-username/sleep-tracker.git
cd sleep-tracker
```

### 2. 가상환경 생성 및 실행 (ubuntu 기준)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env.example` 파일을 복사해 `.env`로 만들고, 실제 값을 채워주세요:

```bash
cp .env.example .env
```

`.env` 예시:

```
# Flask Secret Key
SECRET_KEY=your_flask_secret_key

# MongoDB URI
MONGO_URI=mongodb://your_user:your_pass@your_host:27017/your_dbname?authSource=admin

# JWT 암호화 키
JWT_SECRET_KEY=your_jwt_secret_key

# Gmail 계정 정보 (앱 비밀번호 사용)
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

### 5. 앱 실행

```bash
flask run
```

---

## 📂 디렉토리 구조

```
sleep-tracker/
│
├── app/
│   ├── templates/       # HTML 템플릿 (Jinja2)
│   ├── static/          # JS, CSS
│   └── __init__.py
│
├── .env.example         # 환경변수 템플릿 파일 (민감정보 없음)
├── requirements.txt     # 필요한 패키지 목록
├── .gitignore           # Git 제외 목록
└── run.py               # 실행 진입점
```

---

## ✅ TODO

- [ ] 수면 데이터 주간/월간 통계 시각화 개선
- [ ] JWT Refresh Token 보안 강화 (blacklist 등)
- [ ] 이메일 전송 예외 처리 및 사용자 피드백 메시지 추가
- [ ] 모바일 반응형 UI 개선
- [ ] API 테스트 자동화 (pytest, Postman 등)

---

## 🛡️ 보안 안내

- `.env` 파일에는 절대 민감한 정보를 커밋하지 마세요.
- `.env.example` 파일만 Git에 포함하여 팀원과 공유하세요.
- 실제 배포 환경에서는 환경변수 설정을 CI/CD 파이프라인 또는 서버 설정으로 주입하세요.

---

## 📄 라이선스

MIT License

``'
