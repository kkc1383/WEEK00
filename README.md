# 🛠️ KRAFTON Jungle Week00 Mini Project  

## 🙋 Contributors


 - 강경찬: [@kkc1383](https://github.com/kkc1383)  
 - 백준혁: [@Junryul](https://github.com/Junryul)  
 - 박준성: [@junsung-park97](https://github.com/junsung-park97)  

## 💤 Sleep Tracker Web App

Flask 기반의 수면 기록 웹 애플리케이션입니다.  
입학시험을 위해 학습한 웹 프로그래밍 기술 스택을 기반으로  
서버 사이드 렌더링(SSR)과 JWT 인증 방식을 적용하여  
보다 안정적이고 안전한 사용자 경험을 제공합니다.

---

## 🖼️ 주요 화면 구성

### 🔐 1. 로그인 페이지
![1](https://github.com/user-attachments/assets/07ad07ee-270f-4fd3-be2d-328e122f0e53)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
![5](https://github.com/user-attachments/assets/a6b45121-4c44-4388-9fc1-ab3ab871b2ec)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
![6](https://github.com/user-attachments/assets/7a5d1a5a-7941-42ba-ab16-9f5e8d8a88d9)


- 사용자는 아이디/비밀번호를 입력해 JWT 기반 인증을 수행합니다.
- 로그인 성공 시 access token과 refresh token을 발급받아 이후 인증에 사용됩니다.
- 회원가입, 비밀번호 찾기 등 계정 관리 기능이 포함되어 있습니다.

---

### 🕒 2. 수면 시작/종료 페이지
![2](https://github.com/user-attachments/assets/cc9b7539-79e9-4944-96e6-c90cf8055ae7)

- 현재 사용자의 수면 상태를 보여주며, 수면 시작/종료를 제어할 수 있습니다.
- 실시간 경과 시간이 중앙에 표시되고, 목표 기상 시간과 비교하여 달성 여부도 판단합니다.
- 하단에는 그룹 내 다른 사용자들의 수면 현황도 실시간으로 확인할 수 있습니다 (AJAX 기반 갱신).

---

### 📅 3. 월간 통계/캘린더 페이지
![4](https://github.com/user-attachments/assets/a5d4cbdb-fd09-459b-b5cc-2f21c82aa5cc)

- 각 날짜별로 수면 목표 달성 여부를 색깔로 시각화한 월간 달력입니다.
  - ✅ 초록색: 목표 달성
  - ❌ 빨간색: 목표 미달성
- 우측에는 나의 수면 통계 및 그룹 평균 통계를 함께 표시하여 비교할 수 있도록 구성했습니다.
- 평균 수면 시간, 목표 달성 횟수, 최고 수면자 등을 한눈에 확인할 수 있습니다.

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

## 📘 학습 포인트

이 프로젝트는 단순한 기능 구현을 넘어서 다음과 같은 **웹 개발 핵심 개념들을 실습하고 학습**하는 데 목적이 있습니다:

### ✅ Server-Side Rendering (SSR)

- **Jinja2 템플릿 엔진**을 사용해 서버에서 HTML을 렌더링합니다.
- 인증 상태(로그인 여부, 수면 중 여부 등)에 따라 **템플릿에서 동적으로 콘텐츠를 조건부 출력**합니다:
  ```html
  {% if is_sleeping %}
    <h2>수면 중입니다</h2>
  {% else %}
    <h2>지금부터 잘까요?</h2>
  {% endif %}
- SSR 방식은 초기 로딩 속도가 빠르고 SEO에 유리하며, 인증 상태에 따라 서버에서 UI를 직접 제어할 수 있는 장점이 있습니다.

### 🔐 JWT 기반 인증 (JSON Web Token)

클라이언트가 로그인하면 **Access Token**과 **Refresh Token**을 발급합니다.

- **Access Token**은 JSON 응답으로 전달되고,  
- **Refresh Token**은 `HttpOnly` 쿠키로 클라이언트에 전달됩니다.

이후 인증이 필요한 요청에는 **Access Token을 HTTP 헤더에 첨부**하여 사용합니다.

---

#### 🔄 자동 로그인 연장 구조

- Access Token이 만료되면 `/refresh` 경로에 요청을 보내  
  **Refresh Token을 통해 새로운 Access Token을 발급**받습니다.
- Refresh Token은 쿠키에 저장되어 있어  
  클라이언트는 **자동으로 갱신 요청**을 보낼 수 있습니다.

---

#### 🔓 로그아웃 처리

- 로그아웃 시:
  - 서버에서 Refresh Token을 **DB에서 삭제**하고,
  - 클라이언트 쿠키도 함께 삭제합니다.
- 만료되었거나 위조된 JWT는 서버에서 적절하게 **에러 처리**를 통해 보호됩니다.

---

#### 🔒 보안 학습 포인트

- JWT는 `HS256` 알고리즘과 **서버의 비밀 키 (`SECRET_KEY`)**로 서명됩니다.
- 토큰에는 만료 시간(`exp`)을 포함한 인증 정보가 들어 있어  
  **별도의 세션 저장 없이 인증 상태 유지**가 가능합니다.
- Refresh Token은 `HttpOnly`, `Path` 설정을 통해  
  **클라이언트 측에서 접근할 수 없도록 보호**됩니다.
---

## ⚙️ 설치 및 실행 방법

### 1. 저장소 클론

```bash
git clone https://github.com/kkc1383/WEEK00.git
cd sleep-tracker
```

### 2. 가상환경 생성 및 실행 (ubuntu 기준)

```bash
python -m venv venv
source venv/bin/activate
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
python app.py
```

---

## 📂 디렉토리 구조

```
WEEK00/
│
├── app/
│   ├── templates/       # HTML 템플릿 (Jinja2)
│   ├── static/          # JS, CSS, SourceImg
│   └── __init__.py
│
├── .env.example         # 환경변수 템플릿 파일 (민감정보 없음)
├── requirements.txt     # 필요한 패키지 목록
├── .gitignore           # Git 제외 목록
└── app.py               # 실행 진입점
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

```
