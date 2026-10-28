from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from library.models import Author, Genre, Publisher, Book, BookCopy, Reader, Loan, Reservation

class Command(BaseCommand):
    help = "Создает демонстрационные данные АИС Библиотека"

    def handle(self, *args, **opts):
        admin, _ = User.objects.get_or_create(username="admin", defaults={"is_staff": True, "is_superuser": True, "email": "admin@library.local"})
        admin.is_staff = True; admin.is_superuser = True; admin.set_password("admin123"); admin.save()
        librarian, _ = User.objects.get_or_create(username="librarian", defaults={"is_staff": True, "email": "librarian@library.local"})
        librarian.is_staff = True; librarian.set_password("library123"); librarian.save()
        reader_user, _ = User.objects.get_or_create(username="reader", defaults={"email": "reader@example.com"})
        reader_user.set_password("reader123"); reader_user.save()

        pub, _ = Publisher.objects.get_or_create(name="Учебное издательство")
        genres = {name: Genre.objects.get_or_create(name=name)[0] for name in ["Роман", "Антиутопия", "Фэнтези"]}
        data = [
            ("Преступление и наказание", "Ф. М. Достоевский", "Роман", 1866, "978-5-00000-001-1"),
            ("Мастер и Маргарита", "М. А. Булгаков", "Роман", 1967, "978-5-00000-002-8"),
            ("Война и мир", "Л. Н. Толстой", "Роман", 1869, "978-5-00000-003-5"),
            ("1984", "Дж. Оруэлл", "Антиутопия", 1949, "978-5-00000-004-2"),
            ("Гарри Поттер и философский камень", "Дж. К. Роулинг", "Фэнтези", 1997, "978-5-00000-005-9"),
        ]
        books = []
        for idx, (title, author_name, genre_name, year, isbn) in enumerate(data, 1):
            author, _ = Author.objects.get_or_create(name=author_name)
            book, _ = Book.objects.get_or_create(title=title, defaults={"genre": genres[genre_name], "publisher": pub, "year": year, "isbn": isbn, "description": "Демонстрационная запись библиотечного каталога."})
            book.authors.add(author); books.append(book)
            BookCopy.objects.get_or_create(book=book, inventory_number=f"LIB-{idx:04d}")

        reader, _ = Reader.objects.get_or_create(ticket_number="R-0001", defaults={"user": reader_user, "full_name": "Иванов Иван Иванович", "email": "reader@example.com", "phone": "+7 900 000-00-00"})
        if reader.user_id != reader_user.id:
            reader.user = reader_user; reader.save(update_fields=["user"])
        Reader.objects.get_or_create(ticket_number="R-0002", defaults={"full_name": "Петрова Анна Сергеевна", "email": "anna@example.com"})
        Reader.objects.get_or_create(ticket_number="R-0003", defaults={"full_name": "Сидоров Максим Олегович", "email": "max@example.com"})

        if not Loan.objects.exists():
            copy = books[2].copies.first()
            loan = Loan.objects.create(copy=copy, reader=reader, issued_at=timezone.localdate()-timedelta(days=20), due_at=timezone.localdate()-timedelta(days=6))
            copy.status = BookCopy.Status.LOANED; copy.save(update_fields=["status"])
            Reservation.objects.get_or_create(book=books[1], reader=reader)
        self.stdout.write(self.style.SUCCESS("Демо-данные готовы. admin/admin123, librarian/library123, reader/reader123"))
