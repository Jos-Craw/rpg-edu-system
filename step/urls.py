from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('group/<int:id>/', views.group_detail, name='group_detail'),
    path('group/<int:group_id>/log/', views.log_lesson, name='log_lesson'),
    path('student/<int:student_id>/', views.student_profile, name='student_profile'),
    path('lessons/', views.all_lessons_view, name='all_lessons'),
    path('lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),

]