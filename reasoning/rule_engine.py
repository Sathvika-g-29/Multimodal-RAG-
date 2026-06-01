import re
from dataclasses import dataclass

from retriever.retriever import EvidenceChunk


@dataclass(frozen=True)
class RuleAnswer:
    text: str
    evidence: list[EvidenceChunk]


def answer_with_rules(query: str, corpus: list[EvidenceChunk]) -> RuleAnswer | None:
    normalized = query.casefold()

    if _needs_external_current_info(normalized):
        return RuleAnswer(
            text=(
                "This information is not available in the placement corpus. "
                "A live external lookup/tool call is required, so I should not answer it from RAG evidence."
            ),
            evidence=[],
        )

    if _is_out_of_scope(normalized):
        return RuleAnswer(
            text="I do not have enough information in the provided placement dataset to answer that.",
            evidence=[],
        )

    company = _find_company(normalized, corpus)
    companies = _find_companies(normalized, corpus)

    if "which is better" in normalized or "should i join" in normalized:
        return _answer_subjective_comparison(companies, corpus)

    if "compare" in normalized and len(companies) >= 2 and "all dimensions" in normalized:
        return _answer_full_company_comparison(companies[:2], corpus)

    if "compare" in normalized and len(companies) >= 2 and "eligibility" in normalized:
        return _answer_eligibility_comparison(companies[:2], corpus)

    if company and ("conflict" in normalized or "or" in normalized and "cgpa" in normalized):
        return _answer_conflict(company, corpus)

    if "conflicting" in normalized and "cgpa" in normalized:
        return _answer_conflicting_companies(corpus)

    if company and _is_direct_eligibility_query(normalized):
        return _answer_student_eligibility(normalized, company, corpus)

    if company and "cgpa" in normalized and ("cutoff" in normalized or "requirement" in normalized):
        return _answer_company_cgpa(company, corpus)

    if company and "backlog" in normalized:
        return _answer_company_backlogs(company, corpus)

    if company and "bond" in normalized:
        return _answer_company_bond(company, corpus)

    if company and (
        "technology" in normalized
        or "language" in normalized
        or "technical focus" in normalized
    ):
        return _answer_company_tech_focus(company, corpus)

    if company and "round" in normalized:
        return _answer_company_interview_rounds(company, corpus)

    if company and ("topics" in normalized or "prepare" in normalized):
        return _answer_company_preparation(company, corpus)

    if company and "package" in normalized:
        return _answer_company_package(company, corpus)

    if "backlog" in normalized and "at least 2" in normalized:
        return _answer_backlog_filter(corpus, minimum_backlogs=2)

    if "cgpa above 8" in normalized or "cgpa greater than 8" in normalized:
        return _answer_cgpa_above(corpus, threshold=8.0)

    if "bond-free" in normalized or "bond free" in normalized or "zero-bond" in normalized:
        return _answer_bond_free(normalized, corpus)

    if "python" in normalized and "intern" in normalized:
        return _answer_python_focused_max_interns(corpus)

    if "python" in normalized and ("focus" in normalized or "technical" in normalized or "use" in normalized):
        return _answer_python_focus(corpus)

    if "sde" in normalized and "versus" in normalized:
        return _answer_role_comparison(normalized, corpus, role="sde_roles", label="SDE")

    if "most interns" in normalized or "hires the most intern" in normalized:
        return _answer_max_role(corpus, role="intern_roles", label="Intern")

    if "most analysts" in normalized or "hires the most analyst" in normalized:
        return _answer_max_role(corpus, role="analyst_roles", label="Analyst")

    if "grew the most" in normalized or "largest" in normalized and "increase" in normalized:
        return _answer_largest_growth(corpus)

    if "cgpa 5.0" in normalized or "cgpa of 5.0" in normalized:
        return _answer_low_cgpa_edge_case(corpus, cgpa=5.0)

    if "package-to-cgpa" in normalized or "package to cgpa" in normalized:
        return _answer_best_package_to_cgpa_ratio(corpus)

    if "8.0+" in normalized and "zero backlog" in normalized and "rank" in normalized:
        return _answer_rank_by_package(corpus, cgpa=8.0, backlogs=0)

    if "highest package" in normalized or "maximum pay" in normalized:
        parsed = _parse_student_profile(normalized)
        if parsed:
            cgpa, backlogs = parsed
            return _answer_best_eligible_company(normalized, corpus, cgpa, backlogs)
        return _answer_highest_package(corpus)

    return None


def _eligibility_chunks(corpus: list[EvidenceChunk]) -> list[EvidenceChunk]:
    return [chunk for chunk in corpus if chunk.metadata.get("section") == "eligibility"]


def _find_company(query: str, corpus: list[EvidenceChunk]) -> str | None:
    companies = _find_companies(query, corpus)
    return companies[0] if companies else None


def _find_companies(query: str, corpus: list[EvidenceChunk]) -> list[str]:
    companies = {
        str(chunk.metadata["company"])
        for chunk in corpus
        if chunk.metadata.get("company")
    }
    return [
        company
        for company in sorted(companies, key=len, reverse=True)
        if company.casefold() in query
    ]


def _answer_company_cgpa(company: str, corpus: list[EvidenceChunk]) -> RuleAnswer | None:
    chunk = _company_section_chunk(company, "eligibility", corpus)
    if not chunk:
        return None

    cgpa = chunk.metadata["min_cgpa"]
    conflicts = _company_conflict_chunks(company, corpus)
    note = ""
    evidence = [chunk]
    if conflicts:
        portal = next((item for item in conflicts if item.metadata.get("source_authority") == "portal"), None)
        if portal:
            note = f" A portal record lists {portal.metadata['cgpa']}, so verify with the placement cell."
            evidence.extend(conflicts)
    return RuleAnswer(
        text=f"{company} officially requires a minimum CGPA of {cgpa}.{note}",
        evidence=evidence,
    )


def _answer_company_package(company: str, corpus: list[EvidenceChunk]) -> RuleAnswer | None:
    chunk = _company_section_chunk(company, "eligibility", corpus)
    if not chunk:
        return None

    return RuleAnswer(
        text=f"{company} offers {chunk.metadata['package_lpa']} LPA in the official eligibility table.",
        evidence=[chunk],
    )


def _answer_student_eligibility(
    query: str,
    company: str,
    corpus: list[EvidenceChunk],
) -> RuleAnswer:
    profile = None
    student_id = _parse_student_id(query)
    if student_id:
        from tools.student_profile_tool import fetch_student_profile

        profile = fetch_student_profile(student_id)
        if not profile:
            return RuleAnswer(
                text=(
                    f"I could not find student profile {student_id} in the student database. "
                    "Please verify the roll number or connect the MySQL student-profile tool."
                ),
                evidence=[],
            )
    else:
        parsed = _parse_student_profile(query)
        if parsed:
            cgpa, backlogs = parsed
        else:
            return RuleAnswer(
                text=(
                    "To check your eligibility, I need your student ID/roll number so I can fetch "
                    "your CGPA and backlog details from the student database."
                ),
                evidence=[],
            )

    chunk = _company_section_chunk(company, "eligibility", corpus)
    if not chunk:
        return RuleAnswer(
            text=f"I could not find eligibility criteria for {company} in the placement corpus.",
            evidence=[],
        )

    if profile:
        cgpa = profile.cgpa
        backlogs = profile.backlogs
        student_note = f"student {profile.student_id}"
    else:
        student_note = "the provided profile"

    required_cgpa = float(chunk.metadata["min_cgpa"])
    allowed_backlogs = int(chunk.metadata["max_backlogs"])
    cgpa_ok = cgpa >= required_cgpa
    backlog_ok = backlogs <= allowed_backlogs

    if cgpa_ok and backlog_ok:
        text = (
            f"Yes, {student_note} is eligible for {company}. CGPA {cgpa:g} meets the "
            f"required {required_cgpa:g}, and {backlogs} backlog(s) are within the allowed "
            f"limit of {allowed_backlogs}."
        )
    else:
        reasons = []
        if not cgpa_ok:
            reasons.append(f"CGPA {cgpa:g} is below the required {required_cgpa:g}")
        if not backlog_ok:
            reasons.append(f"{backlogs} backlog(s) exceed the allowed limit of {allowed_backlogs}")
        text = f"No, {student_note} is not eligible for {company}: {'; '.join(reasons)}."

    return RuleAnswer(text=text, evidence=[chunk])


def _is_direct_eligibility_query(query: str) -> bool:
    terms = ["am i eligible", "eligible for", "can i apply", "apply to", "apply for"]
    return any(term in query for term in terms)


def _parse_student_id(query: str) -> str | None:
    match = re.search(r"(?:roll(?: number)?|student(?: id)?|id)\s*(?:is|:)?\s*([a-z0-9]{6,})", query, re.I)
    return match.group(1).upper() if match else None


def _answer_company_backlogs(company: str, corpus: list[EvidenceChunk]) -> RuleAnswer | None:
    chunk = _company_section_chunk(company, "eligibility", corpus)
    if not chunk:
        return None
    backlogs = int(chunk.metadata["max_backlogs"])
    text = (
        f"{company} allows up to {backlogs} backlog(s)."
        if backlogs
        else f"{company} does not allow active backlogs."
    )
    return RuleAnswer(text=text, evidence=[chunk])


def _answer_company_bond(company: str, corpus: list[EvidenceChunk]) -> RuleAnswer | None:
    chunk = _company_section_chunk(company, "eligibility", corpus)
    if not chunk:
        return None
    years = int(chunk.metadata["bond_years"])
    text = f"{company} has a bond period of {years} year(s)."
    return RuleAnswer(text=text, evidence=[chunk])


def _answer_company_tech_focus(company: str, corpus: list[EvidenceChunk]) -> RuleAnswer | None:
    chunk = _company_section_chunk(company, "eligibility", corpus)
    if not chunk:
        return None
    return RuleAnswer(
        text=f"{company}'s technical focus is {chunk.metadata['tech_focus']}.",
        evidence=[chunk],
    )


def _answer_company_interview_rounds(company: str, corpus: list[EvidenceChunk]) -> RuleAnswer:
    chunks = _company_interview_chunks(company, corpus)
    round_chunks = [chunk for chunk in chunks if chunk.text.casefold().startswith("round")]
    if not round_chunks:
        return RuleAnswer(
            text=f"I found interview notes for {company}, but no explicit round breakdown.",
            evidence=chunks[:3],
        )
    summary = " ".join(chunk.text for chunk in round_chunks)
    return RuleAnswer(text=f"{company} interview rounds: {summary}", evidence=round_chunks)


def _answer_company_preparation(company: str, corpus: list[EvidenceChunk]) -> RuleAnswer:
    eligibility = _company_section_chunk(company, "eligibility", corpus)
    interview_chunks = _company_interview_chunks(company, corpus)
    tip_chunks = [chunk for chunk in interview_chunks if "tip:" in chunk.text.casefold()]
    evidence = ([eligibility] if eligibility else []) + tip_chunks[:2]
    topics = _eligibility_topics(eligibility) if eligibility else "the listed interview topics"
    focus = eligibility.metadata["tech_focus"] if eligibility else "the company focus area"
    tips = " ".join(chunk.text for chunk in tip_chunks[:2])
    text = f"For {company}, prepare {topics}. Technical focus: {focus}."
    if tips:
        text = f"{text} {tips}"
    return RuleAnswer(text=text, evidence=evidence)


def _eligibility_topics(chunk: EvidenceChunk | None) -> str:
    if not chunk:
        return "the listed interview topics"
    if chunk.metadata.get("key_topics"):
        return str(chunk.metadata["key_topics"])
    match = re.search(r"key topics (.*?), technical focus", chunk.text, flags=re.IGNORECASE)
    return match.group(1) if match else "the listed interview topics"


def _answer_conflict(company: str, corpus: list[EvidenceChunk]) -> RuleAnswer | None:
    conflicts = _company_conflict_chunks(company, corpus)
    if not conflicts:
        return None

    official = next((chunk for chunk in conflicts if chunk.metadata.get("source_authority") == "official"), None)
    portal = next((chunk for chunk in conflicts if chunk.metadata.get("source_authority") == "portal"), None)
    if not official or not portal:
        return None

    text = (
        f"There are conflicting records for {company}. The official record lists CGPA "
        f"{official.metadata['cgpa']} and package {official.metadata['package_lpa']} LPA, while the portal "
        f"record lists CGPA {portal.metadata['cgpa']} and package {portal.metadata['package_lpa']} LPA. "
        "Please verify with the official placement cell."
    )
    return RuleAnswer(text=text, evidence=conflicts)


def _answer_conflicting_companies(corpus: list[EvidenceChunk]) -> RuleAnswer:
    conflicts = [chunk for chunk in corpus if chunk.metadata.get("section") == "conflict"]
    companies = sorted({str(chunk.metadata["company"]) for chunk in conflicts})
    return RuleAnswer(
        text=f"Companies with conflicting CGPA data are: {', '.join(companies)}.",
        evidence=conflicts,
    )


def _company_conflict_chunks(company: str, corpus: list[EvidenceChunk]) -> list[EvidenceChunk]:
    return [
        chunk
        for chunk in corpus
        if chunk.metadata.get("section") == "conflict" and chunk.metadata.get("company") == company
    ]


def _company_section_chunk(company: str, section: str, corpus: list[EvidenceChunk]) -> EvidenceChunk | None:
    return next(
        (
            chunk
            for chunk in corpus
            if chunk.metadata.get("section") == section and chunk.metadata.get("company") == company
        ),
        None,
    )


def _company_interview_chunks(company: str, corpus: list[EvidenceChunk]) -> list[EvidenceChunk]:
    return [
        chunk
        for chunk in corpus
        if chunk.metadata.get("section") == "interview"
        and chunk.metadata.get("company") == company
    ]


def _answer_eligibility_comparison(companies: list[str], corpus: list[EvidenceChunk]) -> RuleAnswer:
    chunks = [
        chunk
        for company in companies
        for chunk in [_company_section_chunk(company, "eligibility", corpus)]
        if chunk
    ]
    details = "; ".join(
        (
            f"{chunk.metadata['company']}: CGPA {chunk.metadata['min_cgpa']}, "
            f"backlogs {chunk.metadata['max_backlogs']}, package {chunk.metadata['package_lpa']} LPA, "
            f"bond {chunk.metadata['bond_years']} years, focus {chunk.metadata['tech_focus']}"
        )
        for chunk in chunks
    )
    return RuleAnswer(text=f"Eligibility comparison: {details}.", evidence=chunks)


def _answer_full_company_comparison(companies: list[str], corpus: list[EvidenceChunk]) -> RuleAnswer:
    evidence: list[EvidenceChunk] = []
    parts: list[str] = []
    for company in companies:
        eligibility = _company_section_chunk(company, "eligibility", corpus)
        hiring = _company_section_chunk(company, "hiring_distribution", corpus)
        trend = _company_section_chunk(company, "trend", corpus)
        company_evidence = [chunk for chunk in [eligibility, hiring, trend] if chunk]
        evidence.extend(company_evidence)
        if eligibility and hiring and trend:
            parts.append(
                (
                    f"{company}: CGPA {eligibility.metadata['min_cgpa']}, "
                    f"backlogs {eligibility.metadata['max_backlogs']}, package {eligibility.metadata['package_lpa']} LPA, "
                    f"bond {eligibility.metadata['bond_years']} years, focus {eligibility.metadata['tech_focus']}, "
                    f"SDE {hiring.metadata['sde_roles']}, Analyst {hiring.metadata['analyst_roles']}, "
                    f"Intern {hiring.metadata['intern_roles']}, 2021-2024 growth {trend.metadata['increase_2021_2024']} LPA"
                )
            )
    return RuleAnswer(text="; ".join(parts) + ".", evidence=evidence)


def _answer_subjective_comparison(companies: list[str], corpus: list[EvidenceChunk]) -> RuleAnswer:
    if len(companies) < 2:
        return RuleAnswer(
            text=(
                "This depends on the student's goals. The dataset supports objective comparison by package, "
                "eligibility, hiring distribution, bond, and interview focus."
            ),
            evidence=[],
        )
    comparison = _answer_full_company_comparison(companies[:2], corpus)
    return RuleAnswer(
        text=(
            "There is no universally better company; it depends on your profile and priorities. "
            f"Objective comparison from the dataset: {comparison.text}"
        ),
        evidence=comparison.evidence,
    )


def _answer_backlog_filter(corpus: list[EvidenceChunk], minimum_backlogs: int) -> RuleAnswer:
    matches = [
        chunk
        for chunk in _eligibility_chunks(corpus)
        if int(chunk.metadata["max_backlogs"]) >= minimum_backlogs
    ]
    names = ", ".join(str(chunk.metadata["company"]) for chunk in matches)
    return RuleAnswer(
        text=f"Companies that allow at least {minimum_backlogs} backlogs are: {names}.",
        evidence=matches,
    )


def _answer_cgpa_above(corpus: list[EvidenceChunk], threshold: float) -> RuleAnswer:
    matches = [
        chunk
        for chunk in _eligibility_chunks(corpus)
        if float(chunk.metadata["min_cgpa"]) > threshold
    ]
    names = ", ".join(
        f"{chunk.metadata['company']} ({chunk.metadata['min_cgpa']})"
        for chunk in matches
    )
    return RuleAnswer(
        text=f"Companies requiring CGPA above {threshold:g} are: {names}.",
        evidence=matches,
    )


def _answer_bond_free(query: str, corpus: list[EvidenceChunk]) -> RuleAnswer:
    matches = [
        chunk
        for chunk in _eligibility_chunks(corpus)
        if int(chunk.metadata["bond_years"]) == 0
    ]
    if "40" in query:
        matches = [chunk for chunk in matches if float(chunk.metadata["package_lpa"]) > 40]

    names = ", ".join(
        f"{chunk.metadata['company']} ({chunk.metadata['package_lpa']} LPA)"
        for chunk in matches
    )
    return RuleAnswer(text=f"Matching bond-free companies: {names}.", evidence=matches)


def _answer_python_focus(corpus: list[EvidenceChunk]) -> RuleAnswer:
    matches = [
        chunk
        for chunk in _eligibility_chunks(corpus)
        if str(chunk.metadata.get("tech_focus", "")).casefold() == "python"
    ]
    names = ", ".join(
        f"{chunk.metadata['company']} ({chunk.metadata['package_lpa']} LPA)"
        for chunk in matches
    )
    return RuleAnswer(text=f"Python-focused companies are: {names}.", evidence=matches)


def _answer_python_focused_max_interns(corpus: list[EvidenceChunk]) -> RuleAnswer:
    python_companies = {
        str(chunk.metadata["company"])
        for chunk in _eligibility_chunks(corpus)
        if str(chunk.metadata.get("tech_focus", "")).casefold() == "python"
    }
    hiring_matches = [
        chunk
        for chunk in corpus
        if chunk.metadata.get("section") == "hiring_distribution"
        and chunk.metadata.get("company") in python_companies
    ]
    best = max(hiring_matches, key=lambda chunk: int(chunk.metadata["intern_roles"]))
    return RuleAnswer(
        text=(
            f"Among Python-focused companies, {best.metadata['company']} hires the most Interns with "
            f"{best.metadata['intern_roles']} roles."
        ),
        evidence=[best] + [
            chunk
            for chunk in _eligibility_chunks(corpus)
            if chunk.metadata.get("company") == best.metadata.get("company")
        ],
    )


def _answer_max_role(corpus: list[EvidenceChunk], role: str, label: str) -> RuleAnswer:
    hiring = [chunk for chunk in corpus if chunk.metadata.get("section") == "hiring_distribution"]
    best = max(hiring, key=lambda chunk: int(chunk.metadata[role]))
    return RuleAnswer(
        text=f"{best.metadata['company']} hires the most {label}s with {best.metadata[role]} roles.",
        evidence=[best],
    )


def _answer_role_comparison(
    query: str,
    corpus: list[EvidenceChunk],
    role: str,
    label: str,
) -> RuleAnswer | None:
    companies = [
        company
        for company in sorted(
            {
                str(chunk.metadata["company"])
                for chunk in corpus
                if chunk.metadata.get("company")
            },
            key=len,
            reverse=True,
        )
        if company.casefold() in query
    ]
    if len(companies) < 2:
        return None

    chunks = [
        chunk
        for chunk in corpus
        if chunk.metadata.get("section") == "hiring_distribution"
        and chunk.metadata.get("company") in companies[:2]
    ]
    details = ", ".join(f"{chunk.metadata['company']}: {chunk.metadata[role]}" for chunk in chunks)
    return RuleAnswer(text=f"{label} role comparison: {details}.", evidence=chunks)


def _answer_largest_growth(corpus: list[EvidenceChunk]) -> RuleAnswer:
    trends = [chunk for chunk in corpus if chunk.metadata.get("section") == "trend"]
    best = max(trends, key=lambda chunk: float(chunk.metadata["increase_2021_2024"]))
    return RuleAnswer(
        text=(
            f"{best.metadata['company']} grew the most from 2021 to 2024, increasing by "
            f"{best.metadata['increase_2021_2024']} LPA."
        ),
        evidence=[best],
    )


def _answer_low_cgpa_edge_case(corpus: list[EvidenceChunk], cgpa: float) -> RuleAnswer:
    matches = [
        chunk
        for chunk in _eligibility_chunks(corpus)
        if float(chunk.metadata["min_cgpa"]) <= cgpa
    ]
    if matches:
        names = ", ".join(str(chunk.metadata["company"]) for chunk in matches)
        text = f"With CGPA {cgpa:g}, matching companies are: {names}."
    else:
        text = f"No company in this dataset has a CGPA cutoff at or below {cgpa:g}."
    return RuleAnswer(text=text, evidence=matches)


def _answer_highest_package(corpus: list[EvidenceChunk]) -> RuleAnswer:
    best = max(_eligibility_chunks(corpus), key=lambda chunk: float(chunk.metadata["package_lpa"]))
    return RuleAnswer(
        text=f"{best.metadata['company']} has the highest official package at {best.metadata['package_lpa']} LPA.",
        evidence=[best],
    )


def _answer_best_package_to_cgpa_ratio(corpus: list[EvidenceChunk]) -> RuleAnswer:
    best = max(
        _eligibility_chunks(corpus),
        key=lambda chunk: float(chunk.metadata["package_lpa"]) / float(chunk.metadata["min_cgpa"]),
    )
    ratio = float(best.metadata["package_lpa"]) / float(best.metadata["min_cgpa"])
    return RuleAnswer(
        text=(
            f"{best.metadata['company']} has the best package-to-CGPA ratio at "
            f"{ratio:.2f} ({best.metadata['package_lpa']} LPA / CGPA {best.metadata['min_cgpa']})."
        ),
        evidence=[best],
    )


def _answer_rank_by_package(
    corpus: list[EvidenceChunk],
    cgpa: float,
    backlogs: int,
) -> RuleAnswer:
    matches = [
        chunk
        for chunk in _eligibility_chunks(corpus)
        if float(chunk.metadata["min_cgpa"]) <= cgpa
        and int(chunk.metadata["max_backlogs"]) >= backlogs
    ]
    ranked = sorted(matches, key=lambda chunk: float(chunk.metadata["package_lpa"]), reverse=True)
    ranking = ", ".join(
        f"{index}. {chunk.metadata['company']} ({chunk.metadata['package_lpa']} LPA)"
        for index, chunk in enumerate(ranked, start=1)
    )
    return RuleAnswer(
        text=f"For CGPA {cgpa:g}+ and zero backlog students, package ranking is: {ranking}.",
        evidence=ranked[:5],
    )


def _answer_best_eligible_company(
    query: str,
    corpus: list[EvidenceChunk],
    cgpa: float,
    backlogs: int,
) -> RuleAnswer:
    matches = [
        chunk
        for chunk in _eligibility_chunks(corpus)
        if float(chunk.metadata["min_cgpa"]) <= cgpa
        and int(chunk.metadata["max_backlogs"]) >= backlogs
    ]
    if "no bond" in query or "zero bond" in query:
        matches = [chunk for chunk in matches if int(chunk.metadata["bond_years"]) == 0]

    if not matches:
        return RuleAnswer(
            text="No company in this dataset matches the given CGPA, backlog, and bond constraints.",
            evidence=[],
        )

    best = max(matches, key=lambda chunk: float(chunk.metadata["package_lpa"]))
    return RuleAnswer(
        text=(
            f"For CGPA {cgpa:g} and {backlogs} backlog(s), the highest-paying eligible company is "
            f"{best.metadata['company']} at {best.metadata['package_lpa']} LPA."
        ),
        evidence=[best],
    )


def _parse_student_profile(query: str) -> tuple[float, int] | None:
    cgpa_match = re.search(r"cgpa(?: of)?\s*(\d+(?:\.\d+)?)", query)
    backlog_match = re.search(r"(\d+)\s*backlog", query)
    if not cgpa_match:
        return None
    return float(cgpa_match.group(1)), int(backlog_match.group(1)) if backlog_match else 0


def _is_out_of_scope(query: str) -> bool:
    out_of_scope_terms = [
        "campus visit date",
        "stock price",
        "work-from-home",
        "work from home",
        "highest in the world",
        "pays the most in the world",
    ]
    return any(term in query for term in out_of_scope_terms)


def _needs_external_current_info(query: str) -> bool:
    current_info_terms = [
        "who is the ceo",
        "current ceo",
        "latest ceo",
        "current stock price",
        "today",
        "live",
    ]
    return any(term in query for term in current_info_terms)
