# 고등학교 영어 모의고사 변형문제 생성기

PDF에서 영어 지문을 추출하고, 규칙 기반으로 4개 PART의 변형문제를 만든 뒤
학생용 및 교사용 DOCX를 생성하는 Flask 웹앱입니다.

## 주요 기능

- PDF 업로드 및 영어 지문 자동 추출
- 추출 지문 선택 및 직접 편집
- PART 1: 어법, 어휘
- PART 2: 문장 순서, 문장 삽입
- PART 3: 제목, 주제, 요약
- PART 4: 문장 배열, 무관한 문장, 영작, 어법 서술형, 해석
- 학생용 DOCX 생성
- 교사용 정답 및 해설 DOCX 생성
- 작업별 JSON 저장

## 프로젝트 구조

```text
.
├─ app/
│  ├─ services/
│  │  ├─ pdf_service.py
│  │  ├─ question_generator.py
│  │  └─ docx_service.py
│  ├─ static/
│  ├─ templates/
│  ├─ __init__.py
│  ├─ routes.py
│  └─ storage.py
├─ samples/
├─ tests/
├─ requirements.txt
└─ run.py
```

## 실행 방법

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

브라우저에서 `http://127.0.0.1:5000`을 엽니다.

가상환경이 준비된 뒤에는 다음 명령으로 바로 실행할 수 있습니다.

```powershell
.\start.ps1
```

## 참고

- 텍스트 레이어가 없는 스캔 PDF는 먼저 OCR 처리가 필요합니다.
- 현재 문제 생성은 외부 API가 필요 없는 규칙 기반 방식입니다.
- 생성 결과는 `instance/outputs/<작업 ID>/`에 저장됩니다.
- 실제 수업 전에는 추출 지문과 자동 생성 문항을 교사가 검토하는 것을 권장합니다.
