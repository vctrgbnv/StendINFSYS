from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from telemetry.models import Session
from telemetry.services import import_csv_to_session


class Command(BaseCommand):
    help = "Импорт CSV показаний в указанную сессию"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Путь до CSV файла")
        parser.add_argument("--session", type=int, required=True, help="ID сессии")

    def handle(self, *args, **options):
        session_id = options["session"]
        csv_path = Path(options["csv_path"]).expanduser()
        if not csv_path.exists():
            raise CommandError(f"Файл {csv_path} не найден")
        try:
            session = Session.objects.get(pk=session_id)
        except Session.DoesNotExist as exc:
            raise CommandError(f"Сессия {session_id} не найдена") from exc

        with csv_path.open("r", encoding="utf-8") as f:
            csv_import = import_csv_to_session(session, f, file_name=csv_path.name)

        if csv_import.status == csv_import.STATUS_SUCCESS:
            self.stdout.write(self.style.SUCCESS(
                f"Импорт завершен: {csv_import.rows_processed} строк, ошибок {csv_import.rows_failed}"
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"Импорт не удался: {csv_import.error_message or 'неизвестная ошибка'}"
            ))
