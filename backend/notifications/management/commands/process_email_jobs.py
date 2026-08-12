import time

from django.core.management.base import BaseCommand

from notifications.jobs import process_due_email_jobs


class Command(BaseCommand):
    help = "Process durable background email jobs."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--batch-size", type=int, default=25)
        parser.add_argument("--poll-seconds", type=float, default=2.0)
        parser.add_argument("--schedule-seconds", type=float, default=300.0)

    def handle(self, *args, **options):
        batch_size = max(1, min(options["batch_size"], 200))
        poll_seconds = max(0.25, min(options["poll_seconds"], 30.0))
        schedule_seconds = max(30.0, options["schedule_seconds"])
        next_schedule_check = 0.0
        while True:
            monotonic_now = time.monotonic()
            if monotonic_now >= next_schedule_check:
                from bookings.reminders import reconcile_booking_reminders

                reconcile_booking_reminders()
                next_schedule_check = monotonic_now + schedule_seconds
            processed = process_due_email_jobs(limit=batch_size)
            if options["once"]:
                self.stdout.write(
                    self.style.SUCCESS(f"Processed {processed} email job(s).")
                )
                return
            if processed == 0:
                time.sleep(poll_seconds)
