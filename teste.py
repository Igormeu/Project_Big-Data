from mapas_ce import carregar_shapefile, preparar_mapa_ce, mapa_mortalidade
from HubDados import DataHubCE
from modulo_analise import preparar_dados
import matplotlib.pyplot as plt

hub = DataHubCE()
dados = hub.carregar_tudo()

df_total = preparar_dados(
    dados["idhm"], dados["cnes"], dados["mortalidade"]
)

# 1. Carregar shapefile
mapa = carregar_shapefile("shapefiles/BR_Municipios_2024.shp")

# 2. Unir shapefile + dados do CE
mapa_ce = preparar_mapa_ce(mapa, df_total)

print(mapa_ce.shape)
print(mapa_ce.head())
print(mapa_ce.geometry.is_empty.sum())

# 3. Gerar mapa
fig = mapa_mortalidade(mapa_ce, coluna="mortes_idosos", salvar_em="mapa_mortalidade.png")
plt.show()
