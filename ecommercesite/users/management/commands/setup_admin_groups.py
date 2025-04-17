from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.admin_groups import create_admin_groups, assign_user_to_admin_group

class Command(BaseCommand):
    help = 'Sets up admin groups with different permission levels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--assign-superadmin',
            action='store',
            dest='superadmin_username',
            help='Assign a user to the SuperAdmins group',
        )

    def handle(self, *args, **options):
        # Create the admin groups
        groups = create_admin_groups()
        self.stdout.write(self.style.SUCCESS('Successfully created admin groups'))
        
        # List the created groups and their permissions count
        for group_name, group in groups.items():
            permission_count = group.permissions.count()
            self.stdout.write(f'Group: {group_name} - {permission_count} permissions')
        
        # Assign a user to SuperAdmins if specified
        if options['superadmin_username']:
            try:
                user = User.objects.get(username=options['superadmin_username'])
                success = assign_user_to_admin_group(user, 'SuperAdmins')
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully assigned {user.username} to SuperAdmins group'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Failed to assign {user.username} to SuperAdmins group'
                        )
                    )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f'User {options["superadmin_username"]} does not exist'
                    )
                )