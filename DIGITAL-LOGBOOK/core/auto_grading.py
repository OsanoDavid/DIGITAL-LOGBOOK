"""Deterministic scoring for industrial-attachment reports and final results."""
import re

SECTION_RULES = (
    ('Organisation description (mission, vision and objectives)', ('organisation description', 'organization description', 'mission', 'vision', 'objectives')),
    ('Organisation chart / organogram', ('organogram', 'organizational chart', 'organisational chart', 'organization chart', 'organisation chart')),
    ('Mandate of the organisation', ('mandate',)),
    ('Relevant departments and operating procedures', ('operating procedures', 'operational procedures', 'departments')),
    ('Gaps or opportunities', ('identified gaps', 'opportunities', 'gaps')),
    ('Prototype design and implementation', ('prototype', 'design and implement', 'implementation', 'system design')),
    ('Conclusion', ('conclusion',)),
)


def grade_report(pdf_file):
    """Return an explainable 0–100 score for a text-based PDF report."""
    try:
        import fitz
    except ImportError as exc:
        raise ValueError('Automatic PDF grading is temporarily unavailable. Please contact the administrator to install PyMuPDF.') from exc
    pdf_file.seek(0)
    document = fitz.open(stream=pdf_file.read(), filetype='pdf')
    if document.page_count == 0:
        raise ValueError('The PDF has no pages.')

    text = '\n'.join(page.get_text() for page in document).lower()
    if len(re.sub(r'\s+', '', text)) < 300:
        raise ValueError('The PDF contains too little readable text. Upload a text-based PDF, not a scanned image.')

    fonts, sizes = [], []
    for page in document:
        for block in page.get_text('dict').get('blocks', []):
            for line in block.get('lines', []):
                for span in line.get('spans', []):
                    fonts.append(span.get('font', '').lower().replace(' ', ''))
                    sizes.append(round(span.get('size', 0), 1))

    pages = document.page_count
    page_score = 10 if pages >= 10 else 7 if pages >= 7 else 4 if pages >= 4 else 1
    times_score = 10 if any('times' in font for font in fonts) else 0
    size_score = 10 if sizes and sum(11.5 <= size <= 12.5 for size in sizes) / len(sizes) >= .6 else 0
    section_matches = [name for name, terms in SECTION_RULES if any(term in text for term in terms)]
    section_score = round(70 * len(section_matches) / len(SECTION_RULES), 1)
    score = round(page_score + times_score + size_score + section_score, 1)
    return score, {
        'pages': pages,
        'page_score': page_score,
        'font_score': times_score + size_score,
        'sections_found': section_matches,
        'sections_missing': [name for name, _ in SECTION_RULES if name not in section_matches],
        'score': score,
    }


def letter_grade(mark):
    if mark >= 70:
        return 'A'
    if mark >= 60:
        return 'B'
    if mark >= 50:
        return 'C'
    if mark >= 40:
        return 'D'
    return 'F'


def issue_final_grade(period):
    """Issue a grade only when every required component is available."""
    ready = (
        period.recommendation_letter
        and period.report_auto_score is not None
        and period.week_7_finalized and period.week_12_finalized
        and period.week_7_supervisor_marks is not None
        and period.week_12_supervisor_marks is not None
    )
    if not ready:
        return False

    try:
        w7 = float(period.week_7_supervisor_marks)
        w12 = float(period.week_12_supervisor_marks)
        report = float(period.report_auto_score)
    except (TypeError, ValueError):
        return False

    total_points = w7 + w12 + report
    final_mark = round((total_points / 200) * 100, 1)
    period.lecturer_marks = final_mark
    period.lecturer_grade = letter_grade(final_mark)
    period.lecturer_comment = (
        f'Week 7 = {w7:.1f}, '
        f'Week 12 = {w12:.1f}, '
        f'Report = {report:.1f}.'
    )
    period.lecturer_signed = True
    return True
