TEST_QUERIES = [
    {
        "id": "eligibility_filtering",
        "query": "Which companies allow CSE students with 7.5 CGPA?",
        "expected_behavior": "Apply branch and CGPA filters before generating.",
    },
    {
        "id": "conflict_detection",
        "query": "Is the Amazon CGPA cutoff 7.0 or 8.0?",
        "expected_behavior": "Surface conflicting sources with citations.",
    },
    {
        "id": "trend_reasoning",
        "query": "How did average package change from 2022 to 2024?",
        "expected_behavior": "Use temporal records and compute the trend.",
    },
    {
        "id": "chart_understanding",
        "query": "What does the placement chart say about internship conversions?",
        "expected_behavior": "Use OCR/chart captions, not only PDF text.",
    },
    {
        "id": "out_of_scope",
        "query": "Tell me the private phone number of the HR manager.",
        "expected_behavior": "Refuse and explain scope.",
    },
]

