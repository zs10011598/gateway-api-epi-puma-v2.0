from django.contrib.auth.models import User

admin_user = User()
admin_user.username = 'chagas_admin'
admin_user.set_password('Qwerty123')
admin_user.email = 'pedro.romero@bluestart.mx'
admin_user.first_name = 'Pedro'
admin_user.last_name = 'RM'
admin_user.is_superuser = True
admin_user.is_staff = True
admin_user.save()