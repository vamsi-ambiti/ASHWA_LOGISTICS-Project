import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create the configured initial Render admin without resetting existing credentials.'

    def handle(self, *args, **options):
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', '').strip().lower()
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', '')
        if not email or not password:
            self.stdout.write('Initial admin creation skipped; configure its environment variables to enable it.')
            return

        User = get_user_model()
        user = User.objects.filter(email__iexact=email).order_by('pk').first()
        if user:
            if user.is_active and user.is_staff and user.is_superuser:
                self.stdout.write('Initial admin already exists; credentials left unchanged.')
                return
            raise CommandError('The configured admin email is already assigned to a non-admin account.')

        username = email
        username_field = User._meta.get_field(User.USERNAME_FIELD)
        if len(username) > username_field.max_length:
            raise CommandError('The configured admin email is too long to use as a username.')
        if User.objects.filter(**{f'{User.USERNAME_FIELD}__iexact': username}).exists():
            raise CommandError('The configured admin username is already in use.')

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS('Initial admin account created.'))
