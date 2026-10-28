from django.contrib import admin
from .models import Author, Genre, Publisher, Book, BookCopy, Reader, Loan, Reservation, EventLog

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "genre", "year", "isbn")
    search_fields = ("title", "isbn", "authors__name")
    filter_horizontal = ("authors",)

@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    list_display = ("inventory_number", "book", "status")
    list_filter = ("status",)
    search_fields = ("inventory_number", "book__title")

@admin.register(Reader)
class ReaderAdmin(admin.ModelAdmin):
    list_display = ("full_name", "ticket_number", "email", "active")
    search_fields = ("full_name", "ticket_number", "email")
    list_filter = ("active",)

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("copy", "reader", "issued_at", "due_at", "returned_at")
    list_filter = ("issued_at", "returned_at")

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("book", "reader", "status", "created_at")
    list_filter = ("status",)

admin.site.register(Author)
admin.site.register(Genre)
admin.site.register(Publisher)
admin.site.register(EventLog)
admin.site.site_header = "АИС «Библиотека» — администрирование"
admin.site.site_title = "АИС Библиотека"
