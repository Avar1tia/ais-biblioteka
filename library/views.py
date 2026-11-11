from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import LoanForm, ReaderForm, ReservationForm, SignUpForm
from .models import Author, Book, BookCopy, EventLog, Genre, Loan, Reader, Reservation


def staff_required(view):
    return user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url="/accounts/login/")(view)


def log_event(request, action, obj=None, details=""):
    EventLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        object_type=obj.__class__.__name__ if obj else "",
        object_id=str(getattr(obj, "pk", "")) if obj else "",
        details=details,
    )


def catalog(request):
    q = request.GET.get("q", "").strip()
    genre_id = request.GET.get("genre", "").strip()
    books = Book.objects.prefetch_related("authors", "copies").select_related("genre", "publisher")
    if q:
        books = books.filter(Q(title__icontains=q) | Q(authors__name__icontains=q) | Q(isbn__icontains=q)).distinct()
    if genre_id:
        books = books.filter(genre_id=genre_id)
    return render(request, "library/catalog.html", {"books": books, "genres": Genre.objects.all(), "q": q, "selected_genre": genre_id})



def authors(request):
    return render(request, "library/authors.html", {"authors": Author.objects.prefetch_related("books").all()})


def signup(request):
    if request.user.is_authenticated:
        return redirect("library:catalog")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data.get("email", ""),
                password=form.cleaned_data["password1"],
            )
            Reader.objects.create(
                user=user,
                full_name=form.cleaned_data["full_name"],
                email=form.cleaned_data.get("email", ""),
                ticket_number=f"R-{user.pk:04d}",
            )
        login(request, user)
        messages.success(request, "Регистрация завершена. Добро пожаловать!")
        return redirect("library:catalog")
    return render(request, "library/signup.html", {"form": form})

def book_detail(request, pk):
    book = get_object_or_404(Book.objects.prefetch_related("authors", "copies"), pk=pk)
    return render(request, "library/book_detail.html", {"book": book})


@staff_required
def readers(request):
    q = request.GET.get("q", "").strip()
    qs = Reader.objects.all()
    if q:
        qs = qs.filter(Q(full_name__icontains=q) | Q(ticket_number__icontains=q) | Q(email__icontains=q))
    return render(request, "library/readers.html", {"readers": qs, "q": q})


@staff_required
def reader_create(request):
    form = ReaderForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(); log_event(request, "Создан читатель", obj); messages.success(request, "Читатель добавлен."); return redirect("library:readers")
    return render(request, "library/form.html", {"form": form, "title": "Новый читатель"})


@staff_required
def reader_edit(request, pk):
    obj = get_object_or_404(Reader, pk=pk)
    form = ReaderForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        obj = form.save(); log_event(request, "Изменен читатель", obj); messages.success(request, "Данные читателя сохранены."); return redirect("library:readers")
    return render(request, "library/form.html", {"form": form, "title": "Редактирование читателя"})


@staff_required
def loans(request):
    qs = Loan.objects.select_related("copy__book", "reader")
    status = request.GET.get("status", "active")
    if status == "active": qs = qs.filter(returned_at__isnull=True)
    elif status == "returned": qs = qs.filter(returned_at__isnull=False)
    return render(request, "library/loans.html", {"loans": qs, "status": status})


@staff_required
def loan_create(request):
    form = LoanForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            copy = BookCopy.objects.select_for_update().get(pk=form.cleaned_data["copy"].pk)
            if copy.status != BookCopy.Status.AVAILABLE:
                messages.error(request, "Экземпляр уже недоступен.")
                return redirect("library:loan_create")
            loan = form.save(commit=False)
            loan.copy = copy
            loan.full_clean()
            loan.save()
            copy.status = BookCopy.Status.LOANED
            copy.save(update_fields=["status"])
            log_event(request, "Оформлена выдача", loan)
        messages.success(request, "Выдача оформлена.")
        return redirect("library:loans")
    return render(request, "library/form.html", {"form": form, "title": "Оформить выдачу"})


@staff_required
@transaction.atomic
def loan_return(request, pk):
    loan = get_object_or_404(Loan.objects.select_for_update().select_related("copy"), pk=pk)
    if request.method == "POST" and not loan.returned_at:
        loan.returned_at = timezone.localdate(); loan.save(update_fields=["returned_at"])
        loan.copy.status = BookCopy.Status.AVAILABLE; loan.copy.save(update_fields=["status"])
        log_event(request, "Оформлен возврат", loan)
        messages.success(request, "Возврат оформлен.")
    return redirect("library:loans")


@staff_required
def reservations(request):
    return render(request, "library/reservations.html", {"reservations": Reservation.objects.select_related("book", "reader")})


@staff_required
def reservation_create(request):
    form = ReservationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(); log_event(request, "Создано бронирование", obj); messages.success(request, "Бронирование создано."); return redirect("library:reservations")
    return render(request, "library/form.html", {"form": form, "title": "Новое бронирование"})


@staff_required
def reservation_action(request, pk, action):
    obj = get_object_or_404(Reservation, pk=pk)
    if request.method == "POST" and action in {"fulfill", "cancel"}:
        obj.status = Reservation.Status.FULFILLED if action == "fulfill" else Reservation.Status.CANCELLED
        obj.save(update_fields=["status"]); log_event(request, "Изменен статус бронирования", obj, obj.status)
        messages.success(request, "Статус бронирования обновлен.")
    return redirect("library:reservations")


@staff_required
def overdue_report(request):
    overdue = Loan.objects.filter(returned_at__isnull=True, due_at__lt=timezone.localdate()).select_related("copy__book", "reader")
    return render(request, "library/overdue.html", {"loans": overdue})


@login_required
def cabinet(request):
    reader = getattr(request.user, "reader_profile", None)
    if not reader:
        messages.info(request, "К этой учетной записи не привязан профиль читателя.")
        return redirect("library:catalog")
    loans = reader.loans.select_related("copy__book")
    reservations = reader.reservations.select_related("book")
    return render(request, "library/cabinet.html", {"reader": reader, "loans": loans, "reservations": reservations})
