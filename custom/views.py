from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from custom.models import PostuAdministrativu, Suku, Aldeia


# Dropdown bertingkat: Munisípiu → Postu → Suku → Aldeia (AJAX, retorna <option>)
@login_required
def load_post(request):
	munisipiu_id = request.GET.get('munisipiu') or None
	post = PostuAdministrativu.active.filter(munisipiu_id=munisipiu_id).order_by('name')
	return render(request, 'custom/post_dropdown.html', {'post': post})


@login_required
def load_suku(request):
	postu_id = request.GET.get('postu') or None
	suku = Suku.active.filter(postu_id=postu_id).order_by('name')
	return render(request, 'custom/suku_dropdown.html', {'suku': suku})


@login_required
def load_aldeia(request):
	suku_id = request.GET.get('suku') or None
	aldeia = Aldeia.active.filter(suku_id=suku_id).order_by('name')
	return render(request, 'custom/aldeia_dropdown.html', {'aldeia': aldeia})
