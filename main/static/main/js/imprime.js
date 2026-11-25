/* butaun "Imprime / Rai PDF" (CSP: la iha script inline) */
(function () {
	var b = document.getElementById('btn-imprime');
	if (b) b.addEventListener('click', function () { window.print(); });
})();
