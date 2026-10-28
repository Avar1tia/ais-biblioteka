from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Author(models.Model):
    name = models.CharField("ФИО автора", max_length=200, unique=True)
    class Meta:
        ordering = ["name"]
        verbose_name = "автор"
        verbose_name_plural = "авторы"
    def __str__(self): return self.name


class Genre(models.Model):
    name = models.CharField("Жанр", max_length=100, unique=True)
    class Meta:
        ordering = ["name"]
        verbose_name = "жанр"
        verbose_name_plural = "жанры"
    def __str__(self): return self.name


class Publisher(models.Model):
    name = models.CharField("Издательство", max_length=160, unique=True)
    class Meta:
        ordering = ["name"]
        verbose_name = "издательство"
        verbose_name_plural = "издательства"
    def __str__(self): return self.name


class Book(models.Model):
    title = models.CharField("Название", max_length=255)
    authors = models.ManyToManyField(Author, verbose_name="Авторы", related_name="books")
    genre = models.ForeignKey(Genre, verbose_name="Жанр", on_delete=models.SET_NULL, null=True, blank=True, related_name="books")
    publisher = models.ForeignKey(Publisher, verbose_name="Издательство", on_delete=models.SET_NULL, null=True, blank=True, related_name="books")
    year = models.PositiveIntegerField("Год издания", null=True, blank=True)
    isbn = models.CharField("ISBN", max_length=32, blank=True, db_index=True)
    description = models.TextField("Описание", blank=True)
    class Meta:
        ordering = ["title"]
        verbose_name = "книга"
        verbose_name_plural = "книги"
    def __str__(self): return self.title
    @property
    def available_count(self): return self.copies.filter(status=BookCopy.Status.AVAILABLE).count()
    @property
    def catalog_status(self):
        statuses = {copy.status for copy in self.copies.all()}
        if BookCopy.Status.AVAILABLE in statuses:
            return "available"
        if BookCopy.Status.LOANED in statuses:
            return "loaned"
        if BookCopy.Status.RESERVED in statuses:
            return "reserved"
        return "unavailable"
    @property
    def authors_text(self): return ", ".join(author.name for author in self.authors.all())


class BookCopy(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Доступна"
        LOANED = "loaned", "Выдана"
        RESERVED = "reserved", "Забронирована"
        REPAIR = "repair", "На обслуживании"
    book = models.ForeignKey(Book, verbose_name="Книга", on_delete=models.CASCADE, related_name="copies")
    inventory_number = models.CharField("Инвентарный номер", max_length=50, unique=True)
    status = models.CharField("Состояние", max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    class Meta:
        ordering = ["inventory_number"]
        verbose_name = "экземпляр"
        verbose_name_plural = "экземпляры"
    def __str__(self): return f"{self.book} — {self.inventory_number}"


class Reader(models.Model):
    user = models.OneToOneField(User, verbose_name="Учетная запись", on_delete=models.SET_NULL, null=True, blank=True, related_name="reader_profile")
    full_name = models.CharField("ФИО", max_length=200)
    email = models.EmailField("E-mail", blank=True)
    phone = models.CharField("Телефон", max_length=40, blank=True)
    ticket_number = models.CharField("Номер читательского билета", max_length=40, unique=True)
    registered_at = models.DateField("Дата регистрации", default=timezone.localdate)
    active = models.BooleanField("Активен", default=True)
    class Meta:
        ordering = ["full_name"]
        verbose_name = "читатель"
        verbose_name_plural = "читатели"
    def __str__(self): return f"{self.full_name} ({self.ticket_number})"


class Loan(models.Model):
    copy = models.ForeignKey(BookCopy, verbose_name="Экземпляр", on_delete=models.PROTECT, related_name="loans")
    reader = models.ForeignKey(Reader, verbose_name="Читатель", on_delete=models.PROTECT, related_name="loans")
    issued_at = models.DateField("Дата выдачи", default=timezone.localdate)
    due_at = models.DateField("Вернуть до")
    returned_at = models.DateField("Дата возврата", null=True, blank=True)
    class Meta:
        ordering = ["-issued_at", "-id"]
        verbose_name = "выдача"
        verbose_name_plural = "выдачи"
    def __str__(self): return f"{self.copy.book} → {self.reader.full_name}"
    @property
    def is_overdue(self): return not self.returned_at and self.due_at < timezone.localdate()
    def clean(self):
        if not self.pk and self.copy_id and self.copy.status != BookCopy.Status.AVAILABLE:
            raise ValidationError("Экземпляр уже недоступен для выдачи.")


class Reservation(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активно"
        FULFILLED = "fulfilled", "Выполнено"
        CANCELLED = "cancelled", "Отменено"
    book = models.ForeignKey(Book, verbose_name="Книга", on_delete=models.CASCADE, related_name="reservations")
    reader = models.ForeignKey(Reader, verbose_name="Читатель", on_delete=models.CASCADE, related_name="reservations")
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.ACTIVE)
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "бронирование"
        verbose_name_plural = "бронирования"
    def __str__(self): return f"{self.book} — {self.reader}"


class EventLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "запись журнала"
        verbose_name_plural = "журнал событий"
    def __str__(self): return f"{self.created_at:%d.%m.%Y %H:%M} — {self.action}"
