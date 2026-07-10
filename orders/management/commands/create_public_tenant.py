import os

from django.core.management.base import BaseCommand

from orders.models import Client, Domain


class Command(BaseCommand):
    help = "Idempotently creates the public tenant and its domain(s)."

    def handle(self, *args, **options):
        client, created = Client.objects.get_or_create(
            schema_name="public",
            defaults={"name": "Public Tenant"},
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created public tenant: {client}"))
        else:
            self.stdout.write("Public tenant already exists.")

        # Comma-separated list, e.g. PUBLIC_DOMAINS="app.railway.app,mydomain.com"
        domains = os.environ.get(
            "PUBLIC_DOMAINS",
            "gregarious-purpose-production-98d4.up.railway.app",
        ).split(",")

        for i, raw_domain in enumerate(domains):
            domain_name = raw_domain.strip()
            if not domain_name:
                continue
            domain, created = Domain.objects.get_or_create(
                domain=domain_name,
                defaults={"tenant": client, "is_primary": i == 0},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created domain: {domain_name}"))
            else:
                self.stdout.write(f"Domain {domain_name} already exists.")
