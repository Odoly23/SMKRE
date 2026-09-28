"""Helper ba test: kria utilizador ho role lalais."""
from django.contrib.auth.models import User, Group
from django.core.management import call_command
from custom.models import Munisipiu
from users.models import Pesoal, PesoalUser

PASSWORD = 'Teste#Seguru-2026'


def setup_master():
	call_command('setup_smkre', verbosity=0, stdout=open('/dev/null', 'w'))


def make_user(role, email=None, munisipiu_code='LIQ', must_change=False, password=PASSWORD):
	email = email or f'{role}@teste.tl'
	user = User.objects.create_user(username=email, email=email, password=password)
	user.groups.add(Group.objects.get_or_create(name=role)[0])
	pesoal = Pesoal.objects.create(name=f'{role.title()} Teste', email=email, sexo='Feto',
		munisipiu=Munisipiu.objects.filter(code=munisipiu_code).first())
	PesoalUser.objects.create(pesoal=pesoal, user=user, must_change_password=must_change)
	return user
