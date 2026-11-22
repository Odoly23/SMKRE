from celery import shared_task
from kazu.limpeza import hala_o


# knaar kada loron: kansela kazu loron 30 la verifika / la aprova; hamoos kanseladu-automátiku loron 30
@shared_task
def limpeza_automatiku():
	return hala_o()
