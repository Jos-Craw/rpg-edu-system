from django.db import models
import os
from django.core.validators import MinValueValidator, MaxValueValidator
from .utils import get_xp_for_next_level, get_level_thresholds

class Group(models.Model):
    name = models.CharField("Название группы", max_length=100)
    schedule_time = models.CharField("Время занятий", max_length=100)
    classroom = models.CharField("Аудитория", max_length=50)

    def __str__(self): return self.name

def get_xp_for_next_level(level):
    if level < 3:
        return 10
    elif level < 7:
        return 15
    elif level < 10:
        return 20
    elif level < 15:
        return 25
    elif level < 18:
        return 30
    else:
        return 40


class Student(models.Model):
    name = models.CharField("ФИО", max_length=100)
    group = models.ForeignKey('Group', on_delete=models.CASCADE)
    xp = models.IntegerField("Очки опыта (XP)", default=0)

    @property
    def rank(self):
        if self.level < 3:
            return "Странник"
        elif self.level < 6:
            return "Ученик"
        elif self.level < 10:
            return "Искатель"
        elif self.level < 15:
            return "Опытный"
        elif self.level < 21:
            return "Мастер"
        elif self.level < 30:
            return "Магистр"
        else:
            return "Легенда"

    @property
    def level(self):
        xp_left = self.xp
        level = 0

        while True:
            need = get_xp_for_next_level(level)

            if xp_left < need:
                break

            xp_left -= need
            level += 1

        return level

    def recalculate_stats(self):
        performances = self.performance_set.all()

        total_xp = 0

        for p in performances:
            if p.classwork_score:
                total_xp += p.classwork_score * 2

            if p.homework_score:
                total_xp += p.homework_score * 3

        self.xp = total_xp

        # --- НОВАЯ ЛОГИКА УРОВНЕЙ ---
        xp_left = total_xp
        level = 0

        while True:
            need = get_xp_for_next_level(level)

            if xp_left < need:
                break

            xp_left -= need
            level += 1

    def recalculate_stats(self):
        performances = self.performance_set.all()

        total_xp = 0

        for p in performances:
            if p.classwork_score:
                total_xp += p.classwork_score * 2

            if p.homework_score:
                total_xp += p.homework_score * 3

        self.xp = total_xp
        self.save()


    def get_rank_icon(self):
        icons = {
            "Странник": "🪨",
            "Ученик": "🗡️",
            "Искатель": "🏹",
            "Опытный": "⚔️",
            "Мастер": "🛡️",
            "Магистр": "🔮",
            "Легенда": "👑",
        }
        return icons.get(self.rank, "❔")

    def __str__(self):
        return self.name


class Lesson(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    date = models.DateField("Дата занятия")
    topic = models.TextField("Тема урока")
    homework_description = models.TextField("Домашнее задание", blank=True)
    # Поля для файлов напрямую в уроке
    topic_file = models.FileField("Файл темы", upload_to='lessons/topics/', null=True, blank=True)
    homework_file = models.FileField("Файл ДЗ", upload_to='lessons/hw/', null=True, blank=True)
    parent_topic = models.ForeignKey(
        'self', # Ссылка на саму себя
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='child_topics' # Как найти "детей" этой темы
    )

    def __str__(self): 
        return f"{self.group} - {self.date} - {self.topic[:20]}"

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    status = models.BooleanField("Присутствовал", default=True)


    def __str__(self):
        icon = "✅" if self.status else "❌"
        return f"{icon} {self.student.name} — {self.lesson}"

class Performance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    homework_score = models.IntegerField("Балл за ДЗ (0-10)", default=0)
    classwork_score = models.IntegerField("Балл в классе (0-10)", default=0)

    def __str__(self):
        return f"{self.student.name} | ДЗ: {self.homework_score}, Класс: {self.classwork_score}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.student:
            self.student.recalculate_stats()