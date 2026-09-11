from django.db import migrations


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


def recalculate_student_final_grades(apps, schema_editor):
    AttachmentPeriod = apps.get_model('core', 'AttachmentPeriod')
    for period in AttachmentPeriod.objects.all():
        ready = (
            period.recommendation_letter
            and period.report_auto_score is not None
            and period.week_7_finalized
            and period.week_12_finalized
            and period.week_7_supervisor_marks is not None
            and period.week_12_supervisor_marks is not None
        )
        if ready:
            try:
                w7 = float(period.week_7_supervisor_marks)
                w12 = float(period.week_12_supervisor_marks)
                report = float(period.report_auto_score)
            except (TypeError, ValueError):
                continue
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
            period.save(update_fields=['lecturer_marks', 'lecturer_grade', 'lecturer_comment', 'lecturer_signed'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_add_supervisor_signature'),
    ]

    operations = [
        migrations.RunPython(recalculate_student_final_grades, reverse_code=migrations.RunPython.noop),
    ]
