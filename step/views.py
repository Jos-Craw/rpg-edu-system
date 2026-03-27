from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count 
from .models import Group, Student, Lesson, Attendance, Performance
import datetime
from django.db.models import Avg, Count, Sum
from django.utils import timezone
import json


def home(request):
    # Достаем реальные данные
    groups = Group.objects.all() # или .filter(teacher=request.user)
    all_lessons = Lesson.objects.all().order_by('-date')
    
    # # Считаем активность (тепловая карта)
    # last_month = timezone.now() - timezone.timedelta(days=30)
    # daily_activity = Performance.objects.filter(lesson__date__gte=last_month) \
    #     .values('lesson__date') \
    #     .annotate(total_xp=Sum('classwork_score') + Sum('homework_score')) \
    #     .order_by('lesson__date')

    # heatmap_data = [{'x': str(item['lesson__date']), 'y': item['total_xp']} for item in daily_activity]

    return render(request, 'home.html', {
        'groups': groups,             # Проверь это имя!
        'all_lessons': all_lessons,   # И это!
        # 'heatmap_data': json.dumps(heatmap_data),
    })



def group_detail(request, id):
    # Используем id, который пришел из urls.py
    group = get_object_or_404(Group, id=id)
    students = group.student_set.all()
    lessons = group.lesson_set.all().order_by('date')
    
    line_series = []
    for student in students:
        total_xp = 0
        points = []
        for lesson in lessons:
            perf = Performance.objects.filter(student=student, lesson=lesson).first()
            if perf.classwork_score:
                total_xp += perf.classwork_score * 2

            if perf.homework_score:
                total_xp += perf.homework_score * 3
            points.append({'x': lesson.date.strftime('%d.%m'), 'y': total_xp})
        line_series.append({'name': student.name, 'data': points})

    rank_stats = group.student_set.values('rank').annotate(count=Count('id'))
    donut_labels = [item['rank'] for item in rank_stats]
    donut_values = [item['count'] for item in rank_stats]

    return render(request, 'group.html', {
        'group': group,
        'students': students,
        'lessons': lessons,
        'line_chart_data': json.dumps(line_series),
        'donut_labels': json.dumps(donut_labels),
        'donut_values': json.dumps(donut_values),
    })

def log_lesson(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    students = group.student_set.all()
    
    if request.method == "POST":
        # 1. Создаем урок (добавляем request.FILES)
        lesson = Lesson.objects.create(
            group=group,
            date=request.POST.get('date') or datetime.date.today(),
            topic=request.POST.get('topic', 'Без темы'),
            # Имена должны совпадать с name="hw_desc" в HTML
            homework_description=request.POST.get('hw_desc', ''),
            # FILES берем из отдельного словаря
            topic_file=request.FILES.get('topic_file'),
            homework_file=request.FILES.get('homework_file')
        )
        
        attendances_to_create = []
        performances_to_create = []
        
        for student in students:
            # Чекбокс возвращает 'on', если нажат
            is_present = request.POST.get(f'present_{student.id}') == 'on'
            
            # Обязательно приводим к int, чтобы не упало при сложении XP
            hw_val = int(request.POST.get(f'hw_{student.id}', 0))
            cw_val = int(request.POST.get(f'cw_{student.id}', 0))
            
            attendances_to_create.append(
                Attendance(student=student, lesson=lesson, status=is_present)
            )
            performances_to_create.append(
                Performance(
                    student=student, 
                    lesson=lesson, 
                    homework_score=hw_val, 
                    classwork_score=cw_val
                )
            )
            

        # Массовое сохранение в БД
        Attendance.objects.bulk_create(attendances_to_create)
        Performance.objects.bulk_create(performances_to_create)
        for student in students:
            student.recalculate_stats()
            
        return redirect('group_detail', id=group.id)

    return render(request, 'log_lesson.html', {
        'group': group, 
        'students': students, 
        'today': datetime.date.today()
    })



from django.shortcuts import render, get_object_or_404
from django.db.models import Avg
from .models import Student, Performance, Lesson


def student_profile(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    total_xp = student.xp
    level = student.level

    # --- ГРАНИЦЫ УРОВНЯ ---
    def get_level_thresholds(level):
        if level == 0:
            return 0, 10
        elif level == 1:
            return 10, 30
        elif level == 2:
            return 30, 60
        elif level == 3:
            return 60, 100
        elif level == 4:
            return 100, 150
        else:
            start = level * 30
            end = (level + 1) * 30
            return start, end

    start_xp, end_xp = get_level_thresholds(level)

    # XP внутри уровня
    current_level_xp = total_xp - start_xp
    needed_xp = end_xp - start_xp

    # защита от багов
    if current_level_xp < 0:
        current_level_xp = 0

    progress_percent = int((current_level_xp / needed_xp) * 100) if needed_xp > 0 else 0

    # --- СТАТИСТИКА ---
    perf_query = Performance.objects.filter(student=student)

    avg_class = perf_query.aggregate(Avg('classwork_score'))['classwork_score__avg'] or 0
    avg_hw = perf_query.aggregate(Avg('homework_score'))['homework_score__avg'] or 0

    total_lessons = Lesson.objects.filter(group=student.group).count()
    attended_count = perf_query.count()
    attendance = (attended_count / total_lessons * 100) if total_lessons > 0 else 0

    stats_data = [
        round(avg_class * 10),
        round(avg_hw * 10),
        round(attendance),
        progress_percent,
        min(total_xp, 100)
    ]

    performances = perf_query.order_by('-lesson__date')[:10]

    return render(request, 'student_profile.html', {
        'student': student,

        # XP
        'current_xp': total_xp,

        # границы уровня
        'level_start': start_xp,
        'level_end': end_xp,

        # прогресс
        'progress_percent': progress_percent,

        # остальное
        'performances': performances,
        'stats_data': stats_data,
    })






def all_lessons_view(request):
    # Получаем все занятия из базы данных
    lessons = Lesson.objects.all().order_by("-date")
    return render(request, 'all_lessons.html', {'all_lessons': lessons})

def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    performances = Performance.objects.filter(lesson=lesson).select_related('student')
    
    # Находим посещаемость и приклеиваем её прямо к объектам оценок
    for perf in performances:
        att = Attendance.objects.filter(lesson=lesson, student=perf.student).first()
        perf.is_present = att.status if att else False

    return render(request, 'lesson_detail.html', {
        'lesson': lesson,
        'performances': performances,
    })


