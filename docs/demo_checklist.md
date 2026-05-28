# Demo Checklist

Run these commands before a judging walkthrough:

```bash
python -m scripts.parse_dataset --pdf C:\Users\SATHVIKA\Downloads\Placement_RAG_Dataset_Enhanced.pdf
python -m scripts.build_index
python -m pytest
python -m scripts.evaluate
streamlit run app.py
```

Recommended live questions:

- `Is the Amazon CGPA cutoff 6.4 or 7.0? Explain.`
- `Which company hires the most Interns?`
- `Which Python-focused company hires the most Interns?`
- `Which company's package grew the most from 2021 to 2024?`
- `Compare Google and Amazon on all dimensions: eligibility, package, hiring, trend.`
- `What is Infosys's current stock price?`

Expected evaluation summary after hardening:

```text
30 official queries evaluated
23 grounded
3 conflict-aware
3 fallback
1 edge-case
```
