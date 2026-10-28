# Лабораторная работа № 3 — Контейнеризация

**Проект:** АИС «Библиотека» (Django + PostgreSQL).  
**Стенды ЛР №2:** `library-test` (`192.168.56.11`), `library-stage` (`192.168.56.12`), `library-prod` (`192.168.56.13`).

В архиве — действующий исходный код учебного Django-проекта, `Dockerfile` и `compose.yaml`.
Операции установки Docker и запуска контейнеров надо выполнить на ваших ВМ: они не выполнены автоматически этим архивом.

## 1. Установка Docker Engine + Compose на КАЖДОЙ ВМ

Выполните в Ubuntu Server 22.04/24.04, сначала `test`, потом `stage` и `prod`:

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${UBUNTU_CODENAME:-$VERSION_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo docker --version
sudo docker compose version
sudo docker run --rm hello-world
```

Если загрузка из Docker Hub недоступна — проверьте DNS и выход через NAT; не утверждайте об успешной установке без вывода команд.

## 2. Часть 1 — образ и одиночный контейнер (на library-test)

Перенесите папку проекта на ВМ, например в `~/AIS_Biblioteka_Lab3`, и перейдите в неё:

```bash
cd ~/AIS_Biblioteka_Lab3
sudo docker pull python:3.12-slim-bookworm
sudo docker build -t ais-library:lab3 .
sudo docker images
sudo docker run --rm -d --name library-standalone -p 8000:8000 -e SEED_DEMO=1 ais-library:lab3
sudo docker ps
curl -I http://127.0.0.1:8000/
sudo docker logs library-standalone --tail 25
```

Приложение в режиме одиночного контейнера использует учебную SQLite-БД. Для второй части используется уже PostgreSQL.
Остановите одиночный контейнер, чтобы не занимать порт 8000:

```bash
sudo docker stop library-standalone
```

> `docker run --rm` удаляет контейнер после остановки: данные его SQLite-БД будут потеряны. Это допустимо только для первой части. Сохранность данных во второй части проверяется на томе PostgreSQL.

## 3. Часть 2 — Django и PostgreSQL в Docker Compose

```bash
cd ~/AIS_Biblioteka_Lab3
cp .env.example .env
nano .env                 # заменить примерные пароли и SECRET_KEY
sudo docker pull postgres:16-alpine
sudo docker compose config
sudo docker compose up -d --build
sudo docker compose ps
sudo docker compose logs --tail=40 web
```

Инициализируйте учебные записи и 5 книг ОДИН РАЗ (важно: `seed_demo` перезаписывает пароли демонстрационных пользователей):

```bash
sudo docker compose exec web python manage.py seed_demo
sudo docker compose exec web python manage.py check
curl -I http://127.0.0.1:8000/
```

Откройте `http://192.168.56.11:8000/` с другой ВМ в изолированной сети или внутри `library-test` используйте `curl`.
Чтобы открыть сайт **на Windows-хосте** при схеме VirtualBox NAT + Internal Network,
добавьте проброс NAT-порта **host 8080 → guest 8000** для `library-test`, затем откройте `http://127.0.0.1:8080/`.
Гостевая система должна принимать порт 8000 (проверьте `sudo ufw status`).

Демонстрационные пользователи после `seed_demo` (только для учебного стенда):
`admin / admin123`, `librarian / library123`, `reader / reader123`.
После защиты удалите демо-пароли либо смените их.

## 4. Проверка PostgreSQL и volume (главное для части 2)

Проверьте, что веб-приложение связано с PostgreSQL:

```bash
sudo docker compose exec web python manage.py shell -c "from django.db import connection; print(connection.vendor)"
# Ожидается: postgresql
sudo docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT id, title FROM library_book ORDER BY id;"'
```

**Создайте новую книгу через интерфейс:** войдите как `admin`, откройте `http://...:8000/admin/library/book/add/`,
укажите название **«ЛР3 — проверка постоянного хранения»** и сохраните. Для наличия можно через Django Admin добавить экземпляр.
Затем проверьте новую запись командой:

```bash
sudo docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT id, title FROM library_book ORDER BY id DESC LIMIT 10;"'
sudo docker compose down
sudo docker compose up -d
sudo docker compose ps
```

Снова проверьте запись тем же SQL-запросом:

```bash
sudo docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT id, title FROM library_book ORDER BY id DESC LIMIT 10;"'
```

Снова откройте каталог / Django Admin и убедитесь, что запись сохранилась.
**НЕ выполнять `docker compose down -v`** — ключ `-v` удаляет постоянный том и уничтожает лабораторные данные.

Для наблюдения за выводом (stdout/stderr) после фонового запуска:

```bash
sudo docker compose up -d --build
sudo docker compose logs -f web
# Ctrl+C выходит из просмотра логов, но не останавливает фоновые контейнеры
```

## 5. Скриншоты для отчёта

Сделайте реальные изображения (по мере выполнения):
- [ ] Docker и Compose на всех трёх ВМ (`docker --version`, `docker compose version`, `hostname`)
- [ ] `hello-world`, `docker pull python:3.12-slim-bookworm`
- [ ] `Dockerfile`, `docker build`, `docker ps` и браузер/`curl` после части 1
- [ ] `docker pull postgres:16-alpine` и `compose.yaml` (видны volume и 2 сервиса)
- [ ] `docker compose ps` (оба контейнера работают), проверка vendor `postgresql`
- [ ] книга «ЛР3 — проверка постоянного хранения» до перезапуска
- [ ] `docker compose down` / `docker compose up -d` и та же книга ПОСЛЕ перезапуска

## 6. Ответы на контрольные вопросы (кратко)

1. **Изоляция:** пространства имён Linux (PID, network, mount и т. д.) и cgroups; контейнеры используют ядро хостовой системы.
2. **Сеть как у хоста:** режим `--network host` (на Linux), контейнер разделяет пространство сети с хостом; параметр `-p` лишь публикует порт и не делает сеть идентичной.
3. **Команды:** `docker compose build` → `docker compose up -d` → `docker compose logs -f web`.

## Примечание об учебном режиме

`runserver`, `DEBUG=1` и демонстрационные пароли используются только для сдачи лабораторной.
Для реального внешнего развертывания требуются WSGI/ASGI сервер, HTTPS, `DEBUG=0`, безопасное управление секретами и отдельное обслуживание static-файлов.
