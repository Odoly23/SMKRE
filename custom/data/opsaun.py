# Opsaun padronizadu tuir dokumentu Anexu A no Anexu E (Rede ba Rai)
# Formatu: (code, name) ka (code, name, presiza_esplika)

POZISAUN = [
	('KOORDENADOR', 'Koordenadór'),
	('INVESTIGADOR', 'Investigadór / Pontu Fokál'),
	('ANALISTA', 'Analista / Advocacy Coordinator'),
	('OFISIAL-LEGAL', 'Ofisiál Legál'),
	('ADMINISTRASAUN', 'Administrasaun'),
]

TIPU_KONFLITU = [
	# Tuir formuláriu baze dadus sentrál RbR (Airtable)
	('IND-KOMUNIDADE', 'Disputa entre indivíduu ho komunidade', False),
	('IND-IND', 'Disputa entre indivíduu ho indivíduu', False),
	('GOV-RAI-PRIVADU', 'Governu foti komunidade nia rai privadu', False),
	('GOV-RAI-ESTADU', 'Governu hasai komunidade husi rai estadu', False),
	('KOM-KOM', 'Disputa entre komunidade ho komunidade', False),
	('ENTIDADE-LEGAL', 'Disputa entre entidade legál (kompañia, partidu, igreja) no komunidade ka indivíduu', False),
	('GOV-RAI-ABANDONADU', 'Governu hasai komunidade husi rai abandonadu ka rai estatutu la klaru', False),
	('SELUK', 'Seluk (favor esplika)', True),
]
# Tipu tuan (versaun uluk SIBAR-RbR): la hatudu tan iha formuláriu, kazu tuan sei mantein
TIPU_KONFLITU_TUAN = ['DESLOKAMENTU', 'TRADISIONAL', 'AKIZISAUN', 'FRONTEIRA']
# Tipu ne'ebé hatudu kampu Projetu / Entidade ne'ebé foti rai (Governu ka entidade legál)
TIPU_ENTIDADE = ['GOV-RAI-PRIVADU', 'GOV-RAI-ESTADU', 'GOV-RAI-ABANDONADU', 'ENTIDADE-LEGAL']

TIPU_RAI = [
	('ESTADU', 'Rai Estadu'),
	('PRIVADU', 'Rai Privadu'),
	('TRADISIONAL', 'Rai Tradisionál'),
	('DISPUTA', 'Rai Disputa'),
]

TIPU_EVIKSAUN = [
	('FORSADU', 'Forsadu'),
	('VOLUNTARIU', 'Voluntáriu'),
	('ORDEN-TRIBUNAL', 'Orden Tribunál'),
]

TIPU_ATOR = [
	('GOVERNU', 'Autoridade Governu'),
	('POLISIA', 'Polísia'),
	('MILITAR', 'Militár / F-FDTL'),
	('EMPREZA', 'Empreza Privadu'),
	('KOMUNIDADE', 'Membru Komunidade'),
	('SELUK', 'Seluk'),
]

ESTRAGU_PATRIMONIU = [
	('UMA', 'Uma destruidu'),
	('RAI-AGRIKULTURA', 'Rai agrikultura afetadu'),
	('TOOS', "To'os destruidu"),
	('FATIN-SAGRADU', 'Fatin sagradu afetadu'),
	('SELUK', 'Estragu seluk'),
]

NESESIDADE_URJENTE = [
	('APOIU-LEGAL', 'Apoiu Legál'),
	('ABRIGU', 'Abrigu Emerjénsia'),
	('MEDIASAUN', 'Apoiu Mediasaun'),
	('ADVOKASIA', 'Asaun Advokasia'),
]
