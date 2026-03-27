from django.contrib import admin
from .models import Group, Student, Lesson, Attendance, Performance
from .utils import get_xp_for_next_level, get_level_thresholds
from django.utils.html import format_html

class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0

class PerformanceInline(admin.TabularInline):
    model = Performance
    extra = 0

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('group', 'date', 'topic_summary')
    fields = ('group', 'date', 'topic', 'topic_file', 'homework_description', 'homework_file')
    inlines = [AttendanceInline, PerformanceInline]

    def topic_summary(self, obj):
        return obj.topic[:30]
    topic_summary.short_description = 'Тема'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "level", "xp", "rank", "xp_progress")

    def xp_progress(self, obj):
        start, end = get_level_thresholds(obj.level)

        current = obj.xp - start
        needed = end - start

        # защита
        if current < 0:
            current = 0
        if current > needed:
            current = needed

        percent = int((current / needed) * 100) if needed > 0 else 0

        return f"{current} / {needed} XP ({percent}%)"

    xp_progress.short_description = "Прогресс"

admin.site.register(Group)
admin.site.register(Attendance)
admin.site.register(Performance)