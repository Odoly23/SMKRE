from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from custom.models import PostuAdministrativu, Suku, Aldeia


# Dropdown bertingkat: Munisípiu → Postu → Suku → Aldeia (AJAX, retorna <option>)
@login_required
def load_postu(request):
	munisipiu_id = request.GET.get('munisipiu')
	objects = PostuAdministrativu.active.filter(munisipiu_id=munisipiu_id) if munisipiu_id else PostuAdministrativu.objects.none()
	return render(request, 'custom/dropdown.html', {'objects': objects})


@login_required
def load_suku(request):
	postu_id = request.GET.get('postu')
	objects = Suku.active.filter(postu_id=postu_id) if postu_id else Suku.objects.none()
	return render(request, 'custom/dropdown.html', {'objects': objects})


@login_required
def load_aldeia(request):
	suku_id = request.GET.get('suku')
	objects = Aldeia.active.filter(suku_id=suku_id) if suku_id else Aldeia.objects.none()
	return render(request, 'custom/dropdown.html', {'objects': objects})
