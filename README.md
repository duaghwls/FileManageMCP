# 📂 File Organization MCP Server

Windows용 로컬 MCP 서버로, LLM이 파일 시스템을 정리할 수 있도록 도구를 제공합니다.

## ✨ 주요 기능

- **디렉토리 분석**: 파일/폴더 목록 조회, 날짜 정보 추출
- **파일 내용 확인**: 텍스트/코드 파일 스니펫 읽기 (cp949/euc-kr 인코딩 지원)
- **이미지 메타데이터**: EXIF 정보에서 촬영 날짜 추출
- **파일 작업**: 이동, 이름 변경, 폴더 생성
- **일괄 처리**: 날짜 접두사 일괄 추가
- **안전 기능**: Dry Run 모드, 샌드박스 제한, 시스템 폴더 보호

## 📋 파일 정리 규칙

### 2가지 절대 규칙
1. **5단계 규칙**: 디렉토리 깊이는 최대 5단계까지
2. **번호 체계**: 폴더는 `00~99` 접두사 사용 (예: `01_Project`), `99`는 Archive용

### 명명 규칙
- **폴더**: `NN_이름` 형식 (예: `01_Business`, `02_Project`)
- **파일**: `YYMMDD_파일명` 형식 (예: `251202_회의록.docx`)
- **버전**: `_v1.0` 형식 (Final, 최종 금지!)

## 🚀 설치 및 실행

### 요구 사항
- Windows 10/11
- Python 3.13+
- `uv` (권장) 또는 `pip`

### 방법 1: uv 사용 (권장)

```bash
# 프로젝트 디렉토리로 이동
cd C:\{your_path}\FileManageMCP

# uv로 의존성 설치 및 실행
uv run python server.py
```

### 방법 2: pip 사용

```bash
# 가상환경 생성 (선택사항)
python -m venv venv
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python server.py
```

## ⚙️ Cursor/Claude Desktop 설정

### Cursor 설정 (`settings.json`)

```json
{
  "mcpServers": {
    "file-organization-agent": {
      "command": "uv",
      "args": ["run", "--directory", "{your_path}\\FileManageMCP", "python", "server.py"]
    } 
  }
}

```

### Claude Desktop 설정 (`claude_desktop_config.json`)

Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "file-organization-agent": {
      "command": "uv",
      "args": ["run", "python", "server.py"],
      "cwd": "C:\\{your_path}\\FileManageMCP"
    }
  }
}
```

또는 Python 직접 실행:

```json
{
  "mcpServers": {
    "file-organization-agent": {
      "command": "python",
      "args": ["C:\\{your_path}\\FileManageMCP\\server.py"],
      "env": {
        "MCP_FILE_AGENT_ROOT": "D:\\MyDocuments"
      }
    }
  }
}
```

## 🛠️ 사용 가능한 도구

### 설정 도구
| 도구 | 설명 |
|------|------|
| `tool_set_dry_run` | Dry Run 모드 설정 (기본: 활성화) |
| `tool_get_status` | 현재 설정 상태 확인 |
| `tool_configure_workspace` | 작업 영역(샌드박스) 설정 |

### 분석 도구 (Read-Only)
| 도구 | 설명 |
|------|------|
| `tool_list_directory` | 디렉토리 내용 조회 (날짜 정보 포함) |
| `tool_read_file_snippet` | 파일 내용 미리보기 |
| `tool_get_image_metadata` | 이미지 EXIF 정보 추출 |
| `tool_analyze_directory_structure` | 디렉토리 구조 분석 및 문제점 파악 |

### 액션 도구 (Dry Run 지원)
| 도구 | 설명 |
|------|------|
| `tool_move_file` | 파일 이동 |
| `tool_rename_file` | 파일/폴더 이름 변경 |
| `tool_create_folder` | 새 폴더 생성 |
| `tool_batch_rename_with_date` | 날짜 접두사 일괄 추가 |

## 🔒 안전 기능

### Dry Run 모드 (기본 활성화)
- 모든 파일 수정 작업은 기본적으로 시뮬레이션만 수행
- 실제 변경 전 예상 결과 확인 가능
- `tool_set_dry_run(false)` 호출로 실제 모드 전환

### 샌드박스 제한
- `tool_configure_workspace`로 작업 영역 설정
- 설정된 영역 외부 접근 차단

### 시스템 폴더 보호
접근 차단되는 경로:
- `C:\Windows`
- `C:\Program Files`
- `C:\Program Files (x86)`
- `.git`, `node_modules` 등

## 📖 사용 예시

### 1. 기본 워크플로우

```
User: D:\Downloads 폴더를 정리해줘

AI: 
1. 먼저 작업 영역을 설정합니다.
   → tool_configure_workspace("D:\\Downloads")

2. 현재 상태를 확인합니다.
   → tool_get_status()  # Dry Run 활성화 확인

3. 디렉토리 구조를 분석합니다.
   → tool_analyze_directory_structure("D:\\Downloads")

4. 파일 목록을 확인합니다.
   → tool_list_directory("D:\\Downloads")

5. 정리 계획을 세우고 Dry Run으로 시뮬레이션합니다.
   → tool_create_folder("D:\\Downloads", "01_Documents")
   → tool_move_file("D:\\Downloads\\report.docx", "D:\\Downloads\\01_Documents")

6. 결과 확인 후 실제 실행합니다.
   → tool_set_dry_run(false)
   → (위 작업 재실행)
```

### 2. 날짜 접두사 일괄 추가

```
User: 모든 파일에 날짜 접두사를 붙여줘

AI:
1. 대상 확인
   → tool_list_directory("D:\\Downloads")

2. Dry Run 시뮬레이션
   → tool_batch_rename_with_date("D:\\Downloads", use_modified=true)

3. 확인 후 실제 실행
   → tool_set_dry_run(false)
   → tool_batch_rename_with_date("D:\\Downloads", use_modified=true)
```

## 📁 프로젝트 구조

```
03_FileManageMCP/
├── server.py          # MCP 서버 진입점 (FastMCP)
├── tools.py           # MCP 도구 함수 구현
├── utils.py           # 유틸리티 (경로 검증, 인코딩 처리)
├── requirements.txt   # Python 의존성
└── README.md          # 이 문서
```

## 🐛 문제 해결

### "권한 오류" 발생
- 관리자 권한이 필요한 폴더인지 확인
- 다른 프로그램에서 파일을 사용 중인지 확인

### 인코딩 오류
- 한글 파일명/내용은 자동으로 cp949/euc-kr 처리됨
- 바이너리 파일은 내용 읽기 불가 (메타데이터만 표시)

### MCP 연결 실패
- Python 경로가 올바른지 확인
- `uv` 또는 `pip`으로 의존성 설치 확인
- `mcp` 패키지 버전 확인: `pip show fastmcp`

## 📄 라이선스

MIT License

