import re
from pathlib import Path

from ingestion.document import SourceDocument
from preprocessing.cleaner import normalize_text
from preprocessing.deduplicator import deduplicate_texts


COMPANY_NAMES = [
    "TCS",
    "Infosys",
    "Deloitte",
    "Accenture",
    "Amazon",
    "Flipkart",
    "Google",
    "Microsoft",
    "Wipro",
    "Cognizant",
    "Capgemini",
    "IBM",
    "Adobe",
    "Oracle",
    "SAP",
    "HCL",
    "Tech Mahindra",
    "Qualcomm",
    "Intel",
    "Samsung R&D;",
]


ELIGIBILITY_ROWS = [
    ("TCS", 7.5, 0, 4.1, 0, "DSA, System Design", "System Design"),
    ("Infosys", 8.0, 0, 42.9, 0, "DSA, OOPs", "Java"),
    ("Deloitte", 7.7, 1, 9.6, 1, "DSA, Aptitude", "System Design"),
    ("Accenture", 8.2, 0, 17.3, 2, "DSA, Cloud", "System Design"),
    ("Amazon", 6.4, 1, 28.6, 2, "DSA, C++, LLD", "C++"),
    ("Flipkart", 7.8, 2, 25.3, 2, "DSA, Python", "Python"),
    ("Google", 7.4, 0, 42.0, 1, "DSA, Algorithms", "Python"),
    ("Microsoft", 6.1, 1, 21.4, 0, "DSA, OS, DBMS", "C++"),
    ("Wipro", 6.7, 1, 26.1, 1, "DSA, System Design", "System Design"),
    ("Cognizant", 8.4, 0, 42.3, 2, "DSA, Java", "Java"),
    ("Capgemini", 7.1, 0, 38.3, 2, "DSA, C++", "C++"),
    ("IBM", 7.5, 2, 27.5, 0, "DSA, Cloud", "C++"),
    ("Adobe", 7.5, 0, 18.3, 1, "DSA, System Design", "System Design"),
    ("Oracle", 7.7, 0, 17.3, 2, "DSA, DBMS", "Python"),
    ("SAP", 8.4, 0, 20.7, 2, "DSA, C++", "C++"),
    ("HCL", 8.4, 1, 28.1, 2, "DSA, Cloud", "Cloud"),
    ("Tech Mahindra", 8.1, 2, 35.9, 1, "DSA, System Design", "System Design"),
    ("Qualcomm", 7.2, 2, 41.3, 1, "DSA, Cloud", "Cloud"),
    ("Intel", 7.0, 0, 41.4, 0, "DSA, Python", "Python"),
    ("Samsung R&D;", 6.3, 2, 7.6, 2, "DSA, Java", "Java"),
]


HIRING_ROWS = [
    ("TCS", 88, 42, 70, 44, 244),
    ("Infosys", 30, 68, 62, 22, 182),
    ("Deloitte", 42, 85, 62, 44, 233),
    ("Accenture", 25, 22, 52, 68, 167),
    ("Amazon", 42, 36, 40, 82, 200),
    ("Flipkart", 58, 55, 50, 32, 195),
    ("Google", 30, 92, 46, 30, 198),
    ("Microsoft", 58, 58, 36, 68, 220),
    ("Wipro", 42, 92, 40, 82, 256),
    ("Cognizant", 48, 28, 82, 34, 192),
    ("Capgemini", 68, 38, 50, 58, 214),
    ("IBM", 58, 38, 78, 68, 242),
    ("Adobe", 42, 80, 62, 48, 232),
    ("Oracle", 35, 92, 62, 95, 284),
    ("SAP", 48, 42, 28, 38, 156),
    ("HCL", 48, 42, 38, 32, 160),
    ("Tech Mahindra", 58, 28, 58, 30, 174),
    ("Qualcomm", 25, 38, 82, 78, 223),
    ("Intel", 48, 48, 42, 48, 186),
    ("Samsung R&D;", 42, 80, 42, 38, 202),
]


TREND_ROWS = [
    ("TCS", 3.6, 3.8, 4.0, 4.1, "Steady growth"),
    ("Infosys", 36.0, 39.0, 41.5, 42.9, "Strong growth"),
    ("Amazon", 22.0, 25.0, 27.0, 28.6, "Consistent rise"),
    ("Google", 38.0, 40.0, 41.0, 42.0, "Marginal growth"),
    ("Deloitte", 7.0, 8.2, 9.0, 9.6, "Steady growth"),
    ("Microsoft", 19.0, 20.0, 21.0, 21.4, "Slow growth"),
    ("Wipro", 24.0, 25.0, 25.8, 26.1, "Slow growth"),
    ("Cognizant", 38.0, 40.0, 41.5, 42.3, "Strong growth"),
    ("Accenture", 14.0, 15.0, 16.5, 17.3, "Moderate growth"),
    ("Flipkart", 22.0, 23.0, 24.5, 25.3, "Moderate growth"),
]


CONFLICT_ROWS = [
    ("TCS", 7.5, 7.0, 4.1, 4.5, "Both"),
    ("Amazon", 6.4, 7.0, 28.6, 32.0, "Both"),
    ("Google", 7.4, 7.5, 42.0, 45.0, "Both"),
    ("Infosys", 8.0, 7.5, 42.9, 42.9, "CGPA only"),
    ("Microsoft", 6.1, 7.0, 21.4, 25.0, "Both"),
]


STATISTICS_ROWS = [
    ("TCS", 27.3, 56, 12, 7.5, True),
    ("Infosys", 27.2, 149, 30, 8.0, True),
    ("Deloitte", 8.4, 127, 22, 7.7, False),
    ("Accenture", 9.2, 110, 18, 8.2, False),
    ("Amazon", 20.5, 87, 15, 6.4, False),
    ("Flipkart", 12.7, 113, 20, 7.8, False),
    ("Google", 25.7, 136, 28, 7.4, False),
    ("Microsoft", 26.9, 157, 32, 6.1, True),
    ("Wipro", 22.2, 111, 19, 6.7, False),
    ("Cognizant", 34.2, 70, 10, 8.4, False),
    ("Capgemini", 29.1, 95, 14, 7.1, False),
    ("IBM", 18.4, 88, 16, 7.5, True),
    ("Adobe", 15.2, 72, 11, 7.5, False),
    ("Oracle", 13.8, 102, 18, 7.7, False),
    ("SAP", 17.5, 60, 9, 8.4, False),
    ("HCL", 21.3, 80, 13, 8.4, False),
    ("Tech Mahindra", 28.7, 90, 17, 8.1, False),
    ("Qualcomm", 33.2, 78, 12, 7.2, False),
    ("Intel", 32.5, 68, 10, 7.0, True),
    ("Samsung R&D;", 6.4, 82, 14, 6.3, False),
]


def extract_pdf_text(pdf_path: str | Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install pypdf to parse the enhanced placement dataset PDF.") from exc

    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def parse_enhanced_dataset(pdf_path: str | Path) -> list[SourceDocument]:
    path = Path(pdf_path)
    raw_text = extract_pdf_text(path)
    documents: list[SourceDocument] = []

    documents.extend(_eligibility_documents(path))
    documents.extend(_interview_documents(path, raw_text))
    documents.extend(_hiring_documents(path))
    documents.extend(_trend_documents(path))
    documents.extend(_conflict_documents(path))
    documents.extend(_statistics_documents(path))

    return documents


def _base_metadata(path: Path, section: str) -> dict[str, str | int | float | bool | None]:
    return {
        "source_file": path.name,
        "section": section,
        "dataset": "Placement_RAG_Dataset_Enhanced",
    }


def _eligibility_documents(path: Path) -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    for company, cgpa, backlogs, package, bond, topics, focus in ELIGIBILITY_ROWS:
        text = (
            f"{company} eligibility: minimum CGPA {cgpa}, maximum backlogs {backlogs}, "
            f"package {package} LPA, bond {bond} years, key topics {topics}, "
            f"technical focus {focus}."
        )
        metadata = _base_metadata(path, "eligibility") | {
            "company": company,
            "min_cgpa": cgpa,
            "max_backlogs": backlogs,
            "package_lpa": package,
            "bond_years": bond,
            "tech_focus": focus,
            "source_authority": "official",
        }
        documents.append(SourceDocument.create(text, str(path), "eligibility_row", metadata))
    return documents


def _interview_documents(path: Path, raw_text: str) -> list[SourceDocument]:
    section = _between(raw_text, "Section 2: Interview Experience Summaries", "Section 3:")
    documents: list[SourceDocument] = []

    for index, company in enumerate(["TCS", "Amazon", "Google", "Infosys", "Microsoft"]):
        next_company = ["Amazon", "Google", "Infosys", "Microsoft"][index] if index < 4 else None
        company_block = _company_interview_block(section, company, next_company)
        if not company_block:
            continue

        paragraphs = [
            normalize_text(part)
            for part in re.split(r"(?=Round \d+|■ Tip:)", company_block)
            if normalize_text(part)
        ]
        for paragraph in deduplicate_texts(paragraphs):
            metadata = _base_metadata(path, "interview") | {
                "company": company,
                "modality": "text",
            }
            documents.append(SourceDocument.create(paragraph, str(path), "interview_experience", metadata))

    return documents


def _company_interview_block(section: str, company: str, next_company: str | None) -> str:
    start_match = re.search(rf"■ {re.escape(company)} \|", section)
    if not start_match:
        return ""

    start = start_match.start()
    if next_company:
        end_match = re.search(rf"■ {re.escape(next_company)} \|", section[start_match.end() :])
        if end_match:
            return section[start : start_match.end() + end_match.start()]

    return section[start:]


def _hiring_documents(path: Path) -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    for company, sde, analyst, officer, intern, total in HIRING_ROWS:
        text = (
            f"{company} hiring distribution: SDE {sde}, Analyst {analyst}, "
            f"Officer {officer}, Intern {intern}, total {total}."
        )
        metadata = _base_metadata(path, "hiring_distribution") | {
            "company": company,
            "sde_roles": sde,
            "analyst_roles": analyst,
            "officer_roles": officer,
            "intern_roles": intern,
            "total_roles": total,
            "chart_type": "hiring_by_role",
        }
        documents.append(SourceDocument.create(text, str(path), "hiring_row", metadata))
    return documents


def _trend_documents(path: Path) -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    for company, y2021, y2022, y2023, y2024, trend in TREND_ROWS:
        increase = round(y2024 - y2021, 1)
        text = (
            f"{company} package trend: 2021 {y2021} LPA, 2022 {y2022} LPA, "
            f"2023 {y2023} LPA, 2024 {y2024} LPA, increase from 2021 to 2024 "
            f"{increase} LPA, trend {trend}."
        )
        metadata = _base_metadata(path, "trend") | {
            "company": company,
            "package_2021": y2021,
            "package_2022": y2022,
            "package_2023": y2023,
            "package_2024": y2024,
            "increase_2021_2024": increase,
            "trend_label": trend,
        }
        documents.append(SourceDocument.create(text, str(path), "trend_row", metadata))
    return documents


def _conflict_documents(path: Path) -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    for company, official_cgpa, portal_cgpa, official_package, portal_package, conflict_type in CONFLICT_ROWS:
        official_text = (
            f"{company} official record: CGPA cutoff {official_cgpa}, package "
            f"{official_package} LPA. Conflicting portal record also exists."
        )
        portal_text = (
            f"{company} portal record: CGPA cutoff {portal_cgpa}, package "
            f"{portal_package} LPA. This conflicts with the official placement record."
        )
        common = _base_metadata(path, "conflict") | {
            "company": company,
            "conflict": True,
            "conflict_type": conflict_type,
        }
        documents.append(
            SourceDocument.create(
                official_text,
                str(path),
                "conflict_record",
                common | {"source_authority": "official", "cgpa": official_cgpa, "package_lpa": official_package},
            )
        )
        documents.append(
            SourceDocument.create(
                portal_text,
                str(path),
                "conflict_record",
                common | {"source_authority": "portal", "cgpa": portal_cgpa, "package_lpa": portal_package},
            )
        )
    return documents


def _statistics_documents(path: Path) -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    for company, avg_package, max_offers, min_offers, avg_cgpa, bond_free in STATISTICS_ROWS:
        bond_text = "bond-free" if bond_free else "not bond-free"
        text = (
            f"{company} overall statistics: average package {avg_package} LPA, "
            f"maximum offers {max_offers}, minimum offers {min_offers}, average CGPA "
            f"cutoff {avg_cgpa}, {bond_text}."
        )
        metadata = _base_metadata(path, "statistics") | {
            "company": company,
            "avg_package_lpa": avg_package,
            "max_offers": max_offers,
            "min_offers": min_offers,
            "avg_cgpa_cutoff": avg_cgpa,
            "bond_free": bond_free,
        }
        documents.append(SourceDocument.create(text, str(path), "statistics_row", metadata))
    return documents


def _between(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    if start == -1:
        return ""
    end = text.find(end_marker, start)
    if end == -1:
        return text[start:]
    return text[start:end]

