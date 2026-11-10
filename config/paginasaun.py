"""Paginasaun komún: 10 kada pájina, foun liu iha leten (númeru 1 = foun liu)."""
from django.core.paginator import Paginator

POR_PAJINA = 10


def pajina(request, qs, por=POR_PAJINA):
	# Pájina sala (?page=abc / 999) → pájina válida (la iha erru 404 ka 500)
	return Paginator(qs, por).get_page(request.GET.get('page'))
