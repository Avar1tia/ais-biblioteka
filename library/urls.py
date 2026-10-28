from django.urls import path
from . import views

app_name = "library"
urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("authors/", views.authors, name="authors"),
    path("signup/", views.signup, name="signup"),
    path("book/<int:pk>/", views.book_detail, name="book_detail"),
    path("readers/", views.readers, name="readers"),
    path("readers/new/", views.reader_create, name="reader_create"),
    path("readers/<int:pk>/edit/", views.reader_edit, name="reader_edit"),
    path("loans/", views.loans, name="loans"),
    path("loans/new/", views.loan_create, name="loan_create"),
    path("loans/<int:pk>/return/", views.loan_return, name="loan_return"),
    path("reservations/", views.reservations, name="reservations"),
    path("reservations/new/", views.reservation_create, name="reservation_create"),
    path("reservations/<int:pk>/<str:action>/", views.reservation_action, name="reservation_action"),
    path("reports/overdue/", views.overdue_report, name="overdue_report"),
    path("cabinet/", views.cabinet, name="cabinet"),
]
