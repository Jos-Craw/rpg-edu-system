from django.contrib import admin
from .models import Group, Student, Lesson, Attendance, Performance

# Классы для "вложенного" редактирования
class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0 # Чтобы не плодились пустые строки

class PerformanceInline(admin.TabularInline):
    model = Performance
    extra = 0

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    # Добавь файлы в список отображения и в саму форму
    list_display = ('group', 'date', 'topic_summary')
    # Если у тебя прописан fields, добавь туда новые поля:
    fields = ('group', 'date', 'topic', 'topic_file', 'homework_description', 'homework_file')
    inlines = [AttendanceInline, PerformanceInline]

    def topic_summary(self, obj):
        return obj.topic[:30]
    topic_summary.short_description = 'Тема'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "level", "xp", "rank", "xp_progress")

    def xp_progress(self, obj):
        # границы уровня
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

        start, end = get_level_thresholds(obj.level)

        current = obj.xp - start
        needed = end - start

        if current < 0:
            current = 0

        return f"{current} / {needed} XP"

    xp_progress.short_description = "Прогресс"

# Регистрируем остальное
admin.site.register(Group)
# Lesson уже зарегистрирован через @admin.register
admin.site.register(Attendance)
admin.site.register(Performance)