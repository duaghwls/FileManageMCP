"""
server.py - 파일 정리 MCP 서버
FastMCP를 사용하여 파일 정리 도구들을 LLM에 노출합니다.

실행 방법:
    uv run python server.py
    또는
    python server.py
"""

from fastmcp import FastMCP
from typing import Optional

# 도구 함수들 임포트
from tools import (
    # 설정 도구
    set_dry_run,
    get_dry_run_status,
    configure_workspace,
    config,
    # 분석 도구
    list_directory,
    read_file_snippet,
    get_image_metadata,
    analyze_directory_structure,
    # 액션 도구
    move_file,
    rename_file,
    create_folder,
    batch_rename_with_date,
    # 고급 분석 및 정리 도구 (Enhanced)
    suggest_filename_from_content,
    get_image_for_analysis,
    analyze_file_relationships,
    rename_with_suggestion,
    group_files_into_folder,
    find_files_needing_rename,
)


# FastMCP 서버 인스턴스 생성
mcp = FastMCP(
    name="file-organization-agent",
    version="1.0.0",
)


# ============================================================================
# 설정 도구 등록
# ============================================================================


@mcp.tool()
def tool_set_dry_run(enabled: bool) -> str:
    """
    Dry Run 모드를 설정합니다.
    Dry Run이 활성화되면 파일 시스템을 실제로 변경하지 않고
    어떤 작업이 수행될지만 보여줍니다.

    Args:
        enabled: True면 Dry Run 활성화 (안전 모드), False면 실제 변경 수행

    Returns:
        설정 결과 메시지
    """
    return set_dry_run(enabled)


@mcp.tool()
def tool_get_status() -> str:
    """
    현재 설정 상태를 확인합니다.
    Dry Run 모드 상태와 작업 영역 설정을 보여줍니다.

    Returns:
        현재 설정 상태 정보
    """
    from utils import get_target_root

    root = get_target_root()
    root_info = (
        f"작업 영역: {root}"
        if root
        else "작업 영역: 설정되지 않음 (모든 경로 접근 가능 - 주의!)"
    )
    return (
        f"{get_dry_run_status()}\n{root_info}\n최대 디렉토리 깊이: {config.max_depth}"
    )


@mcp.tool()
def tool_configure_workspace(root_path: str) -> str:
    """
    작업 영역(샌드박스)을 설정합니다.
    설정 후에는 이 디렉토리 내에서만 파일 작업이 허용됩니다.
    시스템 보호를 위해 반드시 작업 전에 설정하세요.

    Args:
        root_path: 작업할 루트 디렉토리 경로 (예: "D:\\MyDocuments\\ToOrganize")

    Returns:
        설정 결과 메시지
    """
    return configure_workspace(root_path)


# ============================================================================
# 분석 도구 등록 (Read-Only)
# ============================================================================


@mcp.tool()
def tool_list_directory(path: str, show_hidden: bool = False) -> str:
    """
    디렉토리의 파일과 폴더 목록을 조회합니다.
    각 항목의 생성/수정 날짜와 YYMMDD 형식 파일명 제안도 함께 표시합니다.

    조직 규칙:
    - 폴더는 00~99 접두사 사용 (예: 01_Project)
    - 파일은 YYMMDD 날짜 접두사 사용 (예: 251202_Report.docx)

    Args:
        path: 탐색할 디렉토리 경로
        show_hidden: 숨김 파일/폴더 표시 여부 (기본: False)

    Returns:
        디렉토리 내용 목록 (날짜 정보 포함)
    """
    return list_directory(path, show_hidden)


@mcp.tool()
def tool_read_file_snippet(path: str, max_length: int = 5000) -> str:
    """
    파일의 시작 부분을 읽어 내용을 확인합니다.
    텍스트/코드 파일의 컨텍스트 파악에 유용합니다.
    Windows 환경의 cp949/euc-kr 인코딩도 자동으로 처리합니다.

    Args:
        path: 읽을 파일 경로
        max_length: 최대 읽을 글자 수 (기본: 5000)

    Returns:
        파일 내용 스니펫과 메타데이터
    """
    return read_file_snippet(path, max_length)


@mcp.tool()
def tool_get_image_metadata(path: str) -> str:
    """
    이미지 파일의 EXIF 메타데이터를 추출합니다.
    특히 촬영 날짜 정보를 가져와 YYMMDD 파일명을 제안합니다.

    Args:
        path: 이미지 파일 경로 (JPG, PNG 등)

    Returns:
        이미지 메타데이터 정보 및 파일명 제안
    """
    return get_image_metadata(path)


@mcp.tool()
def tool_analyze_directory_structure(path: str) -> str:
    """
    디렉토리 구조를 분석하고 정리가 필요한 부분을 찾습니다.

    분석 항목:
    - 파일/폴더 통계
    - 확장자별 분포
    - 명명 규칙 위반 (폴더 번호 체계)
    - 디렉토리 깊이 초과
    - 날짜 접두사 누락 파일

    Args:
        path: 분석할 디렉토리 경로

    Returns:
        구조 분석 결과 및 정리 제안
    """
    return analyze_directory_structure(path)


# ============================================================================
# 액션 도구 등록 (File Modification - Dry Run 지원)
# ============================================================================


@mcp.tool()
def tool_move_file(source: str, destination: str) -> str:
    """
    파일을 다른 위치로 이동합니다.

    안전 기능:
    - Dry Run 모드에서는 실제 이동 없이 시뮬레이션만 수행
    - 작업 영역 외부로의 이동 차단
    - 시스템 폴더 접근 차단

    Args:
        source: 이동할 파일의 현재 경로
        destination: 이동할 대상 경로 (디렉토리 또는 전체 경로)

    Returns:
        작업 결과 메시지 (Dry Run 시 시뮬레이션 결과)
    """
    return move_file(source, destination)


@mcp.tool()
def tool_rename_file(path: str, new_name: str) -> str:
    """
    파일 또는 폴더의 이름을 변경합니다.

    명명 규칙:
    - 폴더: 'NN_이름' 형식 권장 (예: 01_Project, 99_Archive)
    - 파일: 'YYMMDD_파일명' 형식 권장 (예: 251202_Report.docx)

    안전 기능:
    - Dry Run 모드에서는 실제 변경 없이 시뮬레이션만 수행
    - 명명 규칙 위반 시 경고 표시

    Args:
        path: 이름을 변경할 파일/폴더 경로
        new_name: 새 이름 (경로 제외, 이름만)

    Returns:
        작업 결과 메시지 (Dry Run 시 시뮬레이션 결과)
    """
    return rename_file(path, new_name)


@mcp.tool()
def tool_create_folder(path: str, name: Optional[str] = None) -> str:
    """
    새 폴더를 생성합니다.

    명명 규칙:
    - 'NN_이름' 형식 권장 (예: 01_Business, 02_Project)
    - 99_Archive는 보관용으로 예약

    제한 사항:
    - 최대 디렉토리 깊이: 5단계
    - Dry Run 모드에서는 실제 생성 없이 시뮬레이션만 수행

    Args:
        path: 폴더를 생성할 위치 또는 전체 폴더 경로
        name: 폴더 이름 (선택적, path에 포함된 경우 생략)

    Returns:
        작업 결과 메시지 (Dry Run 시 시뮬레이션 결과)
    """
    return create_folder(path, name)


@mcp.tool()
def tool_batch_rename_with_date(directory: str, use_modified: bool = True) -> str:
    """
    디렉토리 내 모든 파일에 YYMMDD 날짜 접두사를 일괄 추가합니다.
    이미 날짜 접두사가 있는 파일은 건너뜁니다.

    예시:
    - report.docx → 251202_report.docx (수정일 기준)
    - photo.jpg → 241115_photo.jpg (생성일 또는 수정일 기준)

    Args:
        directory: 대상 디렉토리 경로
        use_modified: True면 수정일, False면 생성일 사용 (기본: True)

    Returns:
        작업 결과 (Dry Run 시 시뮬레이션 결과)
    """
    return batch_rename_with_date(directory, use_modified)


# ============================================================================
# 고급 분석 및 정리 도구 등록 (Enhanced Analysis & Organization Tools)
# ============================================================================


@mcp.tool()
def tool_find_files_needing_rename(directory: str) -> str:
    """
    디렉토리 내에서 이름 변경이 필요한 파일들(의미를 알 수 없는 파일명)을 찾습니다.
    분석 가능한 텍스트/이미지 파일만 필터링하여 반환합니다.

    이 도구로 먼저 대상 파일을 파악한 후:
    - 텍스트 파일: tool_suggest_filename_from_content 사용
    - 이미지 파일: tool_get_image_for_analysis 사용

    Args:
        directory: 탐색할 디렉토리 경로

    Returns:
        이름 변경이 필요한 파일 목록 및 사용할 도구 안내
    """
    return find_files_needing_rename(directory)


@mcp.tool()
def tool_suggest_filename_from_content(path: str, max_content_length: int = 1000) -> str:
    """
    텍스트/문서 파일의 내용을 읽어 LLM이 적절한 이름을 제안할 수 있도록
    파일 정보와 내용을 반환합니다.

    지원 파일: .py, .txt, .md, .js, .json, .html, .css, .docx, .pdf 등

    사용 워크플로우:
    1. 이 도구로 파일 내용 확인
    2. 내용을 바탕으로 적절한 파일명 결정
    3. tool_rename_with_suggestion으로 이름 변경

    Args:
        path: 분석할 파일 경로
        max_content_length: 최대 읽을 글자 수 (기본: 1000)

    Returns:
        파일 정보 및 내용 스니펫
    """
    return suggest_filename_from_content(path, max_content_length)


@mcp.tool()
def tool_get_image_for_analysis(path: str, max_size: int = 512):
    """
    이미지 파일을 LLM Vision이 분석할 수 있도록 FastMCP Image 타입으로 반환합니다.
    Claude Vision이 실제 이미지로 인식하여 분석할 수 있습니다.

    지원 파일: .jpg, .jpeg, .png, .gif, .webp, .bmp

    사용 워크플로우:
    1. 이 도구로 이미지 데이터 획득 (Vision이 자동 인식)
    2. 이미지 내용을 분석하여 적절한 파일명 결정
    3. tool_rename_with_suggestion으로 이름 변경

    Args:
        path: 이미지 파일 경로
        max_size: 이미지 최대 크기 (기본: 512px, 큰 이미지는 리사이즈)

    Returns:
        FastMCP Image와 메타데이터 텍스트 (또는 에러 메시지)
    """
    return get_image_for_analysis(path, max_size)


@mcp.tool()
def tool_analyze_file_relationships(directory: str) -> str:
    """
    디렉토리 내 파일들의 관계를 분석하여 그룹핑 제안을 위한 정보를 반환합니다.

    분석 항목:
    - 확장자별 파일 그룹
    - 공통 접두사를 가진 파일들
    - 공통 키워드
    - 같은 날짜에 수정된 파일들
    - 의미를 알 수 없는 파일명 목록

    이 분석 결과를 바탕으로 tool_group_files_into_folder로 파일들을 정리할 수 있습니다.

    Args:
        directory: 분석할 디렉토리 경로

    Returns:
        파일 관계 분석 결과 및 그룹핑 제안
    """
    return analyze_file_relationships(directory)


@mcp.tool()
def tool_rename_with_suggestion(
    path: str, suggested_name: str, keep_extension: bool = True
) -> str:
    """
    LLM이 제안한 이름으로 파일명을 변경합니다.

    명명 규칙:
    - 파일명 형식: YYMMDD_설명적인이름.확장자
    - 언어 규칙: 파일 내용이 한글이면 한글로, 영어면 영어로 작성
    - 예: 241213_프로젝트계획서.docx

    안전 기능:
    - Dry Run 모드에서는 시뮬레이션만 수행
    - keep_extension=True면 원본 확장자 자동 유지

    Args:
        path: 이름을 변경할 파일 경로
        suggested_name: 제안된 새 이름
        keep_extension: True면 원본 확장자 유지 (기본: True)

    Returns:
        작업 결과 메시지 (Dry Run 시 시뮬레이션 결과)
    """
    return rename_with_suggestion(path, suggested_name, keep_extension)


@mcp.tool()
def tool_group_files_into_folder(
    directory: str, folder_name: str, file_names: list
) -> str:
    """
    새 폴더를 생성하고 지정된 파일들을 해당 폴더로 이동합니다.
    관련 파일들을 그룹으로 묶어 정리하는 데 사용합니다.

    명명 규칙:
    - 폴더명 형식: NN_폴더이름 (예: 01_ProjectFiles)
    - 99는 Archive 용도로 예약

    안전 기능:
    - Dry Run 모드에서는 시뮬레이션만 수행
    - 최대 디렉토리 깊이 체크

    Args:
        directory: 작업할 디렉토리 경로
        folder_name: 생성할 폴더 이름 (예: "01_ProjectFiles")
        file_names: 이동할 파일 이름 목록 (예: ["file1.txt", "file2.py"])

    Returns:
        작업 결과 메시지 (Dry Run 시 시뮬레이션 결과)
    """
    return group_files_into_folder(directory, folder_name, file_names)


# ============================================================================
# 프롬프트 리소스 등록
# ============================================================================


@mcp.resource("organization://rules")
def get_organization_rules() -> str:
    """파일 정리 규칙 문서를 반환합니다."""
    return """
# 파일 정리 규칙

## 2가지 절대 규칙

1. **5단계 규칙**: 디렉토리 깊이는 최대 5단계까지만 허용
2. **번호 체계**: 폴더는 00~99 접두사 사용 (예: `01_Project`). 99는 Archive 용도로 예약

## 폴더 구조 예시

### 개인 폴더
- 01_Gallery (갤러리/사진)
- 02_Study (학습 자료)  
- 03_Hobby (취미 관련)

### 업무 폴더
- 01_Business (사업/업무)
- 02_Project (프로젝트)
- 03_Freelance (프리랜스)

### 공통 폴더
- Template (템플릿 파일)
- Quick Share (빠른 공유용 임시 폴더)

## 파일 명명 규칙
   
1. **시간순 정렬 파일**: `YYMMDD_파일명` (예: `251202_회의록`)
   - 파일의 생성일 또는 수정일을 기준으로 함
   
2. **알파벳순 정렬 파일**: 참조 문서 등은 이름순 정렬

3. **버전 관리**: `_v1.0`, `_v2.0` 형식 사용
   - 'Final', '최종', '진짜최종' 금지!
   - 예: `251202_프로젝트계획서_v1.0.docx`

4. **언어 일치**: 한글 내용 파일은 한글 이름으로, 영어 내용 파일은 영어 이름으로 작성

## 지능형 정리 (AI 활용)

- **의미 불명 파일**: `asd.txt`, `temp1.py` 등 의미를 알 수 없는 파일은 `tool_suggest_filename_from_content`를 사용하여 내용을 분석하고 이름을 제안받을 수 있음.
- **이미지 파일**: `IMG_1234.JPG` 등은 `tool_get_image_for_analysis`를 사용하여 이미지 내용을 분석하고 이름을 제안받을 수 있음.

## 금지 사항

- 시스템 폴더 접근 금지 (Windows, Program Files 등)
- .git 폴더 수정 금지
- 5단계 이상 중첩 폴더 생성 금지
"""


@mcp.resource("organization://workflow")
def get_workflow_guide() -> str:
    """정리 작업 워크플로우 가이드를 반환합니다."""
    return """
# 파일 정리 워크플로우

## 1단계: 준비
1. `tool_configure_workspace`로 작업 영역 설정
2. `tool_get_status`로 Dry Run 활성화 확인
3. `tool_analyze_directory_structure`로 현황 파악

## 2단계: 지능형 분석 및 정리
1. **의미 불명 파일 찾기**:
   - `tool_find_files_needing_rename`으로 정리 대상 발굴
2. **내용 기반 분석**:
   - 텍스트/문서: `tool_suggest_filename_from_content`
   - 이미지: `tool_get_image_for_analysis`
3. **이름 변경 실행**:
   - `tool_rename_with_suggestion` 사용

## 3단계: 그룹핑 및 구조화
1. **관계 분석**:
   - `tool_analyze_file_relationships`로 연관 파일 파악
2. **그룹핑 실행**:
   - `tool_group_files_into_folder`로 주제별 폴더 이동
3. **일괄 날짜 처리**:
   - 필요 시 `tool_batch_rename_with_date` 실행

## 4단계: 실행 (Dry Run 해제)
1. **최종 확인**: 사용자에게 계획된 작업 승인 요청
2. **모드 전환**: `tool_set_dry_run(false)`
3. **작업 수행**: 계획된 도구 호출 실행

## 5단계: 검증
1. `tool_analyze_directory_structure`로 정리 결과 확인
2. 완료 후 `tool_set_dry_run(true)`로 안전 모드 복귀
"""


# ============================================================================
# 서버 시작
# ============================================================================

if __name__ == "__main__":
    import sys
    import io

    # Windows 인코딩 문제 해결 - stderr만 래핑 (stdout은 MCP 프로토콜용)
    if sys.platform == "win32":
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )

    # MCP는 stdout을 프로토콜 통신에 사용하므로 로그는 stderr로 출력
    print("[START] File Organization MCP Server", file=sys.stderr)
    print("        Name: file-organization-agent", file=sys.stderr)
    print("        Version: 1.0.0", file=sys.stderr)
    print("", file=sys.stderr)
    print("[TOOLS] Available:", file=sys.stderr)
    print(
        "   [Config] tool_set_dry_run, tool_get_status, tool_configure_workspace",
        file=sys.stderr,
    )
    print(
        "   [Read]   tool_list_directory, tool_read_file_snippet, tool_get_image_metadata",
        file=sys.stderr,
    )
    print("   [Read]   tool_analyze_directory_structure", file=sys.stderr)
    print(
        "   [Action] tool_move_file, tool_rename_file, tool_create_folder",
        file=sys.stderr,
    )
    print("   [Action] tool_batch_rename_with_date", file=sys.stderr)
    print("", file=sys.stderr)
    print("[NOTE] Dry Run mode is ENABLED by default.", file=sys.stderr)
    print(
        "       Call tool_set_dry_run(false) for actual file changes.", file=sys.stderr
    )
    print("", file=sys.stderr)

    # stdio 전송 방식으로 서버 실행
    mcp.run()
