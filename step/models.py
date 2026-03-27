from django.db import models
import os
from django.core.validators import MinValueValidator, MaxValueValidator

class Group(models.Model):
    name = models.CharField("Название группы", max_length=100)
    schedule_time = models.CharField("Время занятий", max_length=100)
    classroom = models.CharField("Аудитория", max_length=50)

    def __str__(self): return self.name

class Student(models.Model):
    RANK_CHOICES = [
        ('Странник', 'Странник'),
        ('Ученик', 'Ученик'),
        ('Искатель', 'Искатель'),
        ('Опытный', 'Опытный'),
        ('Мастер', 'Мастер'),
        ('Магистр', 'Магистр'),
        ('Легенда', 'Легенда'),
    ]

    name = models.CharField("ФИО", max_length=100)
    group = models.ForeignKey('Group', on_delete=models.CASCADE)

    level = models.IntegerField(
        "Уровень",
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(30)]
    )

    xp = models.IntegerField("Очки опыта (XP)", default=0)

    rank = models.CharField(
        "Ранг",
        max_length=50,
        choices=RANK_CHOICES,
        blank=True
    )

    def recalculate_stats(self):
        performances = self.performance_set.all()

        total_xp = 0

        for p in performances:
            if p.classwork_score:
                total_xp += p.classwork_score * 2

            if p.homework_score:
                total_xp += p.homework_score * 3

        self.xp = total_xp
        xp = total_xp
        level = 0

        while True:
            if level == 0:
                need = 10
            elif level == 1:
                need = 20
            elif level == 2:
                need = 30
            elif level == 3:
                need = 40
            else:
                need = 30

            if xp < need:
                break

            xp -= need
            level += 1

        self.level = level

        self._update_rank_by_level()

        self.save()

    def _update_rank_by_level(self):
        if self.level < 3:
            self.rank = "Странник"
        elif self.level < 6:
            self.rank = "Ученик"
        elif self.level < 10:
            self.rank = "Искатель"
        elif self.level < 15:
            self.rank = "Опытный"
        elif self.level < 21:
            self.rank = "Мастер"
        elif self.level < 30:
            self.rank = "Магистр"
        else:
            self.rank = "Легенда"

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