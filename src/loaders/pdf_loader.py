"""PDF Loader — 加载银行理财公告/说明书/报告 PDF

双引擎策略：
- PyMuPDF (fitz)：默认引擎，速度快，中文支持好
- pdfplumber：兜底引擎，表格解析更强（暂未启用，需要 pip install pdfplumber）

文件名规范（理财文件目录约定）：
    <机构>_<日期>_<报告类型>_<产品名>_<事项>.pdf
    例：工银理财_2026-08-20_临时性信息披露_关于工银理财·鑫悦...业绩比较基准调整的公告.pdf

输出 Document，metadata 含 institution / report_type / effective_date / product_name / page_count。
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path

from loguru import logger

from ..schemas import Document


# 文件名模板正则
# 例：工银理财_2026-08-20_临时性信息披露_关于工银理财·鑫悦最短持有30天固收增强开放式理财产品2号实施业绩比较基准调整的公告.pdf
FILENAME_PATTERN = re.compile(
    r"^(?P<institution>[^_]+)_(?P<date>\d{4}-\d{2}-\d{2})_(?P<report_type>[^_]+)_(?P<rest>.+)\.pdf$"
)

# 仅机构名前缀格式（用于补全 institution）
INSTITUTION_PREFIX_PATTERN = re.compile(
    r"^(?P<institution>[^_]{2,20})(?:理财|银行)"
)

# 产品编号（理财登记系统编码，形如 24GS5969 / 26GS0740 / 26HH6088）
PRODUCT_CODE_PATTERN = re.compile(r"\b\d{2}[A-Z]{2}\d{4,6}\b")

# 报告类型枚举（标准化）
REPORT_TYPE_MAPPING = {
    "产品说明书": "产品说明书",
    "发行公告": "发行公告",
    "产品说明书&发行公告": "产品说明书",
    "临时性信息披露": "临时报告",
    "临时报告": "临时报告",
    "定期报告": "定期报告",
    "半年度报告": "定期报告",
    "年度报告": "定期报告",
    "净值公告": "净值公告",
    "分类统计": "分类统计",
}


def _extract_filename_meta(filename: str) -> dict:
    """从文件名解析元数据（机构/日期/报告类型）。

    支持两种命名风格：
    1. 完整风格：工银理财_2026-08-20_临时性信息披露_xxx.pdf
    2. 变体风格：招银理财_关于xxx公告_其他产品公告_506051DZ.pdf（无日期/类型）
    """
    filename_safe = Path(filename).name
    m = FILENAME_PATTERN.match(filename_safe)
    if m:
        institution = m.group("institution").strip()
        date_str = m.group("date")
        report_type_raw = m.group("report_type").strip()
        rest = m.group("rest").strip()
        report_type = REPORT_TYPE_MAPPING.get(report_type_raw, report_type_raw)
    else:
        # 变体风格：从"招银理财_xxx" 提取 institution，其余交给目录补全
        rest = filename_safe.replace(".pdf", "")
        prefix_match = INSTITUTION_PREFIX_PATTERN.match(rest)
        institution = prefix_match.group("institution").strip() if prefix_match else "未知"
        date_str = ""
        report_type = "未知"

    # 产品名 = 文件名剩余部分，去掉前后缀
    product_name = rest
    product_name = re.sub(r"^关于", "", product_name)
    product_name = re.sub(r"的公告$", "", product_name)
    product_name = re.sub(r"的说明书$", "", product_name)
    product_name = re.sub(r"实施.*$", "", product_name)
    product_name = product_name.strip()

    # 产品编号
    code_match = PRODUCT_CODE_PATTERN.search(rest)
    product_code = code_match.group(0) if code_match else ""

    return {
        "institution": institution,
        "effective_date": date_str,
        "report_type": report_type,
        "product_name": product_name,
        "product_code": product_code,
    }


def _extract_text_pymupdf(pdf_path: Path, max_pages: int = 80) -> tuple[str, int]:
    """PyMuPDF 提取文本（按页拼接，保留页边界）"""
    import fitz  # PyMuPDF

    doc = fitz.open(str(pdf_path))
    try:
        n_pages = min(len(doc), max_pages)
        text_parts = []
        for i in range(n_pages):
            page = doc[i]
            text = page.get_text("text")
            if text.strip():
                # 保留页边界标识，便于按页引用
                text_parts.append(f"\n[Page {i + 1}]\n{text}")

        full_text = "\n".join(text_parts)
        return full_text, len(doc)  # 返回总页数，不截断的
    finally:
        doc.close()


def _detect_title(content: str, fallback: str) -> str:
    """从文本中提取标题（取第一行非空且较短的内容）"""
    for line in content.split("\n")[:30]:
        line = line.strip()
        if not line:
            continue
        # 标题特征：长度适中、不含数字编号、可能含"公告/说明书/披露"
        if 5 <= len(line) <= 60 and re.search(r"公告|说明书|披露|报告|说明", line):
            return line
        # 如果第一行就是短句，也算标题
        if 5 <= len(line) <= 60:
            return line
    return fallback


def load_pdf_file(
    pdf_path: Path | str,
    min_text_chars: int = 100,
    max_pages: int = 80,
) -> Document | None:
    """加载单个 PDF 文件。

    Args:
        pdf_path: PDF 文件路径
        min_text_chars: 低于此字符数视为扫描件，返回 None
        max_pages: 单 PDF 最大页数（避免巨型报告 OOM）

    Returns:
        Document 或 None（如果文本为空 / 文件损坏）
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        logger.warning(f"PDF 不存在: {pdf_path}")
        return None

    filename = pdf_path.name
    file_meta = _extract_filename_meta(filename)

    # 从目录补全 institution / report_type（应对变体命名的招银文件）
    dir_meta = _extract_dir_meta(pdf_path)
    # 目录结构是规范化的，优先用目录的 institution（覆盖文件名解析的简化前缀）
    if dir_meta.get("institution"):
        file_meta["institution"] = dir_meta["institution"]
    if dir_meta.get("report_type"):
        file_meta["report_type"] = dir_meta["report_type"]

    try:
        text, total_pages = _extract_text_pymupdf(pdf_path, max_pages=max_pages)
    except Exception as e:
        logger.error(f"PyMuPDF 解析失败 {pdf_path}: {e}")
        return None

    if len(text) < min_text_chars:
        logger.warning(f"PDF 文本过短 ({len(text)} 字符)，疑似扫描件: {filename}")
        return None

    if total_pages > max_pages:
        logger.warning(f"PDF 页数超限 ({total_pages} > {max_pages})，仅提取前 {max_pages} 页")

    title = _detect_title(text, fallback=file_meta.get("product_name") or pdf_path.stem)

    # doc_id 基于文件路径（同一文件反复加载幂等）
    doc_id = hashlib.sha1(str(pdf_path.resolve()).encode("utf-8")).hexdigest()[:12]

    # 合并元数据：文件名解析 + 文件系统 + 内容
    metadata = {
        # 文件名解析
        "institution": file_meta.get("institution", ""),
        "effective_date": file_meta.get("effective_date", ""),
        "report_type": file_meta.get("report_type", ""),
        "product_name": file_meta.get("product_name", ""),
        "product_code": file_meta.get("product_code", ""),
        # 文件系统
        "title": title,
        "filename": filename,
        "file_path": str(pdf_path.resolve()),
        "file_extension": ".pdf",
        "page_count": total_pages,
        # 业务
        "source": "pdf_local",
        "doc_id": doc_id,
        "category": _extract_category(pdf_path),
    }

    return Document(
        content=text,
        metadata=metadata,
        source=str(pdf_path.resolve()),
    )


def _extract_category(pdf_path: Path) -> str:
    """从路径提取一级分类（产品说明书/定期报告/临时报告/分类统计）"""
    parts = pdf_path.parts
    for p in reversed(parts):
        if p in {"产品说明书&发行公告", "定期报告", "临时报告"}:
            return {
                "产品说明书&发行公告": "产品说明书",
                "定期报告": "定期报告",
                "临时报告": "临时报告",
            }.get(p, p)
    return "其他"


def _extract_dir_meta(pdf_path: Path) -> dict:
    """从目录结构补全元数据。

    路径示例：
      data/理财文件/临时报告/B01招银理财/新设份额/xxx.pdf
      data/理财文件/产品说明书&发行公告/招银理财/xxx.pdf
    """
    parts = pdf_path.parts
    result = {"institution": "", "report_type": "", "effective_date": ""}

    # 找分类（一级目录）
    for p in parts:
        if p in {"产品说明书&发行公告", "定期报告", "临时报告"}:
            result["report_type"] = {
                "产品说明书&发行公告": "产品说明书",
                "定期报告": "定期报告",
                "临时报告": "临时报告",
            }.get(p, p)
            break

    # 找机构（分类后的第一级目录）
    try:
        cat_idx = next(i for i, p in enumerate(parts) if p in {"产品说明书&发行公告", "定期报告", "临时报告"})
        if cat_idx + 1 < len(parts):
            result["institution"] = parts[cat_idx + 1]
    except StopIteration:
        pass

    # 找事项（如"新设份额"、"费率调整"）
    try:
        cat_idx = next(i for i, p in enumerate(parts) if p in {"产品说明书&发行公告", "定期报告", "临时报告"})
        for j in range(cat_idx + 2, len(parts) - 1):
            sub = parts[j]
            if sub not in {"业绩比较基准调整", "新设份额", "费率调整及费率优惠", "特殊案例"} and "公告" not in sub:
                continue
            # 这是事项子目录
            result["report_type"] = sub  # 用更精确的事项名覆盖
            break
    except StopIteration:
        pass

    return result


def load_pdf_dir(
    dir_path: Path | str,
    recursive: bool = True,
    limit: int | None = None,
    min_text_chars: int = 100,
    max_pages: int = 80,
) -> list[Document]:
    """递归加载目录下所有 .pdf 文件。

    Args:
        dir_path: PDF 根目录
        recursive: 是否递归
        limit: 最多加载几个文件（POC 阶段限定）
        min_text_chars: 跳过扫描件的阈值
        max_pages: 单 PDF 最大页数

    Returns:
        Document 列表
    """
    dir_path = Path(dir_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"目录不存在: {dir_path}")

    pattern = "**/*.pdf" if recursive else "*.pdf"
    files = sorted(dir_path.glob(pattern))

    if not files:
        logger.warning(f"未发现 PDF 文件: {dir_path}")
        return []

    if limit:
        files = files[:limit]

    logger.info(f"开始加载 {len(files)} 个 PDF...")
    docs = []
    skipped = 0
    for i, f in enumerate(files, 1):
        doc = load_pdf_file(f, min_text_chars=min_text_chars, max_pages=max_pages)
        if doc is None:
            skipped += 1
            continue
        docs.append(doc)
        if i % 20 == 0:
            logger.info(f"  加载进度: {i}/{len(files)}")

    logger.info(f"PDF 加载完成: {len(docs)} 成功 / {skipped} 跳过")
    return docs


def load_pdf_files(
    pdf_paths: list[Path | str],
    min_text_chars: int = 100,
    max_pages: int = 80,
) -> list[Document]:
    """批量加载指定的 PDF 文件列表（POC 用，从筛选结果加载）"""
    docs = []
    skipped = 0
    for p in pdf_paths:
        doc = load_pdf_file(p, min_text_chars=min_text_chars, max_pages=max_pages)
        if doc is None:
            skipped += 1
            continue
        docs.append(doc)
    logger.info(f"PDF 批量加载: {len(docs)} 成功 / {skipped} 跳过")
    return docs