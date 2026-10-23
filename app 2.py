from pathlib import Path
 
import pandas as pd

import plotly.express as px

import streamlit as st
 
 
# CONFIGURAÇÃO DA PÁGINA

st.set_page_config(

    page_title="Copas do Mundo",

    layout="wide"

)
 
st.title("Dashboard das Copas do Mundo")
 
st.write("""

Este dashboard analisa as Copas do Mundo presentes no arquivo

WorldCups.csv, de 1930 a 2014.
 
O objetivo é comparar títulos, gols, público e quantidade

de seleções participantes.

""")
 
with st.expander("Perguntas da análise"):

    st.markdown("""

    1. Quais seleções conquistaram mais títulos?

    2. Como o total de gols variou entre as edições?

    3. Qual edição apresentou a maior média de gols por partida?

    4. Qual edição apresentou o maior público médio por partida?

    5. Como a quantidade de seleções participantes mudou?

    """)
 
 
# LEITURA AUTOMÁTICA DO CSV

@st.cache_data

def carregar_dados():

    caminho = Path(__file__).resolve().parent / "WorldCups.csv"
 
    return pd.read_csv(

        caminho,

        dtype="string",

        encoding="utf-8-sig"

    )
 
 
try:

    original = carregar_dados()
 
except FileNotFoundError:

    st.error(

        "Coloque o arquivo WorldCups.csv na mesma pasta do app.py."

    )

    st.stop()
 
except (

    pd.errors.ParserError,

    pd.errors.EmptyDataError,

    UnicodeDecodeError

):

    st.error("Não foi possível ler o CSV. Confira o arquivo.")

    st.stop()
 
 
# VERIFICAÇÃO ANTES DO TRATAMENTO

st.subheader("1. Conhecendo a base")
 
col1, col2 = st.columns(2)
 
col1.metric("Registros originais", original.shape[0])

col2.metric("Colunas originais", original.shape[1])
 
with st.expander("Verificação antes do tratamento"):

    st.write("Primeiras linhas:")

    st.dataframe(

        original.head(),

        use_container_width=True

    )
 
    st.write("Valores ausentes:")

    st.dataframe(

        original.isna().sum().rename("Ausentes").to_frame()

    )
 
    st.write(

        "Linhas totalmente duplicadas:",

        int(original.duplicated().sum())

    )
 
    st.write("Tipos de leitura:")

    st.dataframe(

        original.dtypes.astype(str).rename("Tipo").to_frame()

    )
 
    st.caption(

        "As colunas foram lidas inicialmente como texto "

        "para preservar os valores antes das conversões."

    )
 
 
# CONFERÊNCIA DAS COLUNAS

df = original.copy()
 
df.columns = df.columns.str.strip()
 
colunas_necessarias = [

    "Year",

    "Country",

    "Winner",

    "Runners-Up",

    "Third",

    "Fourth",

    "GoalsScored",

    "QualifiedTeams",

    "MatchesPlayed",

    "Attendance"

]
 
if df.columns.duplicated().any():

    st.error("O CSV contém nomes de colunas repetidos.")

    st.stop()
 
faltantes = sorted(

    set(colunas_necessarias) - set(df.columns)

)
 
if faltantes:

    st.error(

        "Colunas ausentes no CSV: " + ", ".join(faltantes)

    )

    st.stop()
 
 
# TRATAMENTO DOS DADOS
 
# Remove espaços extras e identifica textos vazios.

for coluna in df.columns:

    df[coluna] = (

        df[coluna]

        .str.strip()

        .replace("", pd.NA)

    )
 
colunas_numericas = [

    "Year",

    "GoalsScored",

    "QualifiedTeams",

    "MatchesPlayed"

]
 
falhas_conversao = {}
 
# Converte números armazenados como texto.

for coluna in colunas_numericas:

    antes = df[coluna].copy()
 
    df[coluna] = pd.to_numeric(

        antes,

        errors="coerce"

    )
 
    falhas_conversao[coluna] = int(

        (antes.notna() & df[coluna].isna()).sum()

    )
 
# Neste CSV, os pontos do público separam milhares.

antes_publico = df["Attendance"].copy()
 
df["Attendance"] = pd.to_numeric(

    antes_publico.str.replace(".", "", regex=False),

    errors="coerce"

)
 
falhas_conversao["Attendance"] = int(

    (

        antes_publico.notna()
& df["Attendance"].isna()

    ).sum()

)
 
# Remove somente duplicatas exatas.

duplicatas_removidas = int(df.duplicated().sum())
 
df = df.drop_duplicates().copy()
 
# Preserva Winner e cria uma coluna para o ranking histórico.

df["CampeaoAnalise"] = df["Winner"].replace({

    "Germany FR": "Germany"

})
 
nomes_portugues = {

    "Brazil": "Brasil",

    "Germany": "Alemanha",

    "Italy": "Itália",

    "Argentina": "Argentina",

    "Uruguay": "Uruguai",

    "France": "França",

    "England": "Inglaterra",

    "Spain": "Espanha"

}
 
df["CampeaoAnalise"] = df["CampeaoAnalise"].replace(

    nomes_portugues

)
 
with st.expander("Tratamentos realizados"):

    st.markdown("""

    - Removemos espaços extras para evitar diferenças de digitação.

    - Convertemos os números para permitir cálculos.

    - Retiramos os pontos de milhar da coluna de público:

      `590.549` passou a ser `590549`.

    - Removemos linhas totalmente duplicadas.

    - Agrupamos Alemanha Ocidental e Alemanha na contagem

      histórica de títulos.

    - Preservamos valores ausentes, sem preenchê-los com zero

      nem excluir automaticamente linhas inteiras.

    """)
 
    st.write(

        "Duplicatas removidas:",

        duplicatas_removidas

    )
 
    st.write("Valores que não puderam ser convertidos:")

    st.dataframe(

        pd.Series(

            falhas_conversao,

            name="Falhas de conversão"

        ).to_frame()

    )
 
    st.write("Valores ausentes após o tratamento:")

    st.dataframe(

        df[colunas_necessarias]

        .isna()

        .sum()

        .rename("Ausentes")

        .to_frame()

    )
 
 
# VERIFICAÇÃO DE CONSISTÊNCIA

for coluna in colunas_numericas + ["Attendance"]:

    valores = df[coluna].dropna()
 
    if (

        (valores < 0)

        | ((valores % 1) != 0)

    ).any():

        st.error(

            f"A coluna {coluna} contém valores negativos "

            "ou fracionários. Confira o CSV."

        )

        st.stop()
 
if (df["MatchesPlayed"].dropna() == 0).any():

    st.error("Existe uma edição com zero partidas. Confira o CSV.")

    st.stop()
 
anos_validos = df["Year"].dropna()
 
if anos_validos.empty:

    st.error("Não existem anos válidos no arquivo.")

    st.stop()
 
if anos_validos.duplicated().any():

    st.error(

        "Existem registros diferentes para o mesmo ano. "

        "Confira o CSV antes de analisar."

    )

    st.stop()
 
df = df.sort_values("Year")
 
# Cria as médias de cada edição.

df["GolsPorPartida"] = (

    df["GoalsScored"] / df["MatchesPlayed"]

)
 
df["PublicoPorPartida"] = (

    df["Attendance"] / df["MatchesPlayed"]

)
 
 
# FILTRO POR EDIÇÃO

st.sidebar.header("Filtros")
 
anos = sorted(

    anos_validos.astype(int).unique().tolist()

)
 
anos_selecionados = st.sidebar.multiselect(

    "Selecione as edições",

    options=anos,

    default=anos

)
 
dados = df[

    df["Year"].isin(anos_selecionados)

].copy()
 
if dados.empty:

    st.warning(

        "Selecione pelo menos uma edição na barra lateral."

    )

    st.stop()
 
st.caption(

    "Os gráficos, indicadores e explicações acompanham "

    "as edições selecionadas."

)
 
 
# FORMATAÇÃO DOS NÚMEROS

def formatar(valor, casas=0):

    if pd.isna(valor):

        return "Sem dados"
 
    texto = f"{valor:,.{casas}f}"
 
    return (

        texto

        .replace(",", "X")

        .replace(".", ",")

        .replace("X", ".")

    )
 
 
# INDICADORES

st.subheader("2. Resumo das edições selecionadas")
 
# Usa pares completos para calcular médias corretamente.

pares_gols = dados.dropna(

    subset=["GoalsScored", "MatchesPlayed"]

)
 
pares_publico = dados.dropna(

    subset=["Attendance", "MatchesPlayed"]

)
 
media_gols = (

    pares_gols["GoalsScored"].sum()

    / pares_gols["MatchesPlayed"].sum()

    if not pares_gols.empty

    else float("nan")

)
 
media_publico = (

    pares_publico["Attendance"].sum()

    / pares_publico["MatchesPlayed"].sum()

    if not pares_publico.empty

    else float("nan")

)
 
col1, col2, col3, col4 = st.columns(4)
 
col1.metric(

    "Edições selecionadas",

    len(dados)

)
 
col2.metric(

    "Total de gols informados",

    formatar(

        dados["GoalsScored"].sum(min_count=1)

    )

)
 
col3.metric(

    "Gols por partida",

    formatar(media_gols, 2)

)
 
col4.metric(

    "Público por partida",

    formatar(media_publico)

)
 
st.caption(

    "As médias gerais dividem os totais pelas partidas "

    "das edições com dados completos. Público representa "

    "presenças nos jogos, não pessoas únicas."

)
 
 
# GRÁFICO 1 — TÍTULOS

st.subheader("3. Quais seleções conquistaram mais títulos?")
 
titulos = (

    dados["CampeaoAnalise"]

    .dropna()

    .value_counts()

    .rename_axis("Seleção")

    .reset_index(name="Títulos")

    .sort_values(

        ["Títulos", "Seleção"],

        ascending=[False, True]

    )

)
 
if not titulos.empty:

    fig_titulos = px.bar(

        titulos,

        x="Seleção",

        y="Títulos",

        text="Títulos",

        title="Títulos nas edições selecionadas"

    )
 
    fig_titulos.update_yaxes(dtick=1)
 
    st.plotly_chart(

        fig_titulos,

        use_container_width=True

    )
 
    maior = int(titulos["Títulos"].max())
 
    lideres = titulos.loc[

        titulos["Títulos"].eq(maior),

        "Seleção"

    ].tolist()
 
    st.write(

        f"A maior quantidade no recorte é de {maior} título(s), "

        f"alcançada por: {', '.join(lideres)}. "

        "Cada barra representa a quantidade de edições "

        "vencidas pela seleção."

    )
 
    st.caption(

        "Alemanha Ocidental e Alemanha foram agrupadas "

        "na contagem histórica."

    )
 
else:

    st.warning(

        "Não há campeões informados nas edições selecionadas."

    )
 
 
# FUNÇÃO PARA OS GRÁFICOS POR EDIÇÃO

def grafico_edicoes(

    coluna,

    titulo,

    eixo,

    explicacao,

    casas=0

):

    base = (

        dados

        .dropna(subset=["Year", coluna])

        .sort_values("Year")

    )
 
    if base.empty:

        st.warning("Não há dados válidos para este gráfico.")

        return
 
    fig = px.line(

        base,

        x="Year",

        y=coluna,

        markers=True,

        title=titulo,

        labels={

            "Year": "Ano",

            coluna: eixo,

            "Country": "País-sede"

        },

        hover_data=["Country"]

    )
 
    fig.update_xaxes(

        tickmode="array",

        tickvals=base["Year"].tolist()

    )
 
    st.plotly_chart(

        fig,

        use_container_width=True

    )
 
    maior = base[coluna].max()

    menor = base[coluna].min()
 
    anos_maior = ", ".join(

        base.loc[

            base[coluna].eq(maior),

            "Year"

        ].astype(int).astype(str).tolist()

    )
 
    anos_menor = ", ".join(

        base.loc[

            base[coluna].eq(menor),

            "Year"

        ].astype(int).astype(str).tolist()

    )
 
    st.write(

        f"No recorte selecionado, o maior valor foi "

        f"{formatar(maior, casas)}, em {anos_maior}. "

        f"O menor foi {formatar(menor, casas)}, "

        f"em {anos_menor}."

    )
 
    st.write(explicacao)
 
    if len(base) == 1:

        st.caption(

            "Selecione mais edições para comparar mudanças."

        )
 
    if len(base) < len(dados):

        st.caption(

            "Edições com valores ausentes nesta análise "

            "não aparecem neste gráfico."

        )
 
 
# GRÁFICO 2 — TOTAL DE GOLS

st.subheader("4. Como o total de gols variou?")
 
grafico_edicoes(

    coluna="GoalsScored",

    titulo="Total de gols por edição",

    eixo="Total de gols",

    explicacao=(

        "Cada ponto representa o total de gols de uma Copa. "

        "A linha conecta as edições selecionadas. "

        "Como a quantidade de partidas varia, um total maior "

        "não significa necessariamente mais gols por jogo."

    )

)
 
 
# GRÁFICO 3 — MÉDIA DE GOLS

st.subheader("5. Qual edição teve mais gols por partida?")
 
grafico_edicoes(

    coluna="GolsPorPartida",

    titulo="Média de gols por partida",

    eixo="Gols por partida",

    explicacao=(

        "Dividimos o total de gols pelo número de partidas "

        "de cada edição. Isso permite comparar torneios "

        "com quantidades diferentes de jogos. "

        "A média não mostra como os gols se distribuíram "

        "entre as partidas."

    ),

    casas=2

)
 
 
# GRÁFICO 4 — PÚBLICO MÉDIO

st.subheader("6. Qual edição teve maior público por partida?")
 
grafico_edicoes(

    coluna="PublicoPorPartida",

    titulo="Público médio por partida",

    eixo="Presenças por partida",

    explicacao=(

        "Dividimos o público acumulado pelo número de partidas. "

        "Uma pessoa pode ter assistido a vários jogos. "

        "Como o CSV não informa a capacidade dos estádios, "

        "não podemos calcular a taxa de ocupação."

    )

)
 
 
# GRÁFICO 5 — SELEÇÕES PARTICIPANTES

st.subheader("7. Como mudou a quantidade de seleções?")
 
grafico_edicoes(

    coluna="QualifiedTeams",

    titulo="Seleções participantes por edição",

    eixo="Quantidade de seleções",

    explicacao=(

        "O gráfico mostra a quantidade de seleções participantes "

        "em cada edição. Os dados permitem observar mudanças "

        "no tamanho do torneio, mas não explicam sozinhos "

        "as causas dessas mudanças."

    )

)
 
 
# TABELA E ESTATÍSTICAS

with st.expander("Consultar os dados e as estatísticas"):

    st.write("Dados das edições selecionadas:")
 
    st.dataframe(

        dados,

        use_container_width=True,

        hide_index=True

    )
 
    st.write("Estatísticas descritivas:")
 
    st.dataframe(

        dados[

            [

                "GoalsScored",

                "MatchesPlayed",

                "QualifiedTeams",

                "Attendance",

                "GolsPorPartida",

                "PublicoPorPartida"

            ]

        ].describe(),

        use_container_width=True

    )
 
    st.caption(

        "A tabela apresenta quantidade de valores disponíveis, "

        "média, desvio padrão, mínimo, quartis e máximo."

    )
 
    st.download_button(

        "Baixar dados das edições selecionadas",

        data=dados.to_csv(index=False).encode("utf-8-sig"),

        file_name="copas_selecionadas.csv",

        mime="text/csv"

    )
 
 
# VALIDAÇÃO

st.subheader("8. Validação dos resultados")
 
st.write(

    "Estas verificações utilizam a base completa, "

    "independentemente do filtro. Os resultados esperados "

    "correspondem ao CSV fornecido na atividade."

)
 
ranking_completo = df["CampeaoAnalise"].value_counts()
 
pico_gols = df["GoalsScored"].max()
 
anos_pico = set(

    df.loc[

        df["GoalsScored"].eq(pico_gols),

        "Year"

    ].dropna().astype(int).tolist()

)
 
publico_1930 = df.loc[

    df["Year"].eq(1930),

    "Attendance"

]
 
publico_correto = (

    len(publico_1930) == 1

    and pd.notna(publico_1930.iloc[0])

    and publico_1930.iloc[0] == 590549

)
 
verificacoes = [

    (

        "20 edições",

        len(df) == 20

    ),

    (

        "Período de 1930 a 2014",

        df["Year"].min() == 1930

        and df["Year"].max() == 2014

    ),

    (

        "Total de 2.379 gols",

        df["GoalsScored"].sum() == 2379

    ),

    (

        "Brasil com 5 títulos",

        ranking_completo.get("Brasil", 0) == 5

    ),

    (

        "Alemanha com 4 títulos",

        ranking_completo.get("Alemanha", 0) == 4

    ),

    (

        "Itália com 4 títulos",

        ranking_completo.get("Itália", 0) == 4

    ),

    (

        "Pico de 171 gols em 1998 e 2014",

        pico_gols == 171

        and anos_pico == {1998, 2014}

    ),

    (

        "Público de 1930 convertido para 590549",

        publico_correto

    )

]
 
tabela_validacao = pd.DataFrame(

    [

        {

            "Verificação": descricao,

            "Resultado": (

                "OK" if bool(resultado) else "Conferir"

            )

        }

        for descricao, resultado in verificacoes

    ]

)
 
st.dataframe(

    tabela_validacao,

    use_container_width=True,

    hide_index=True

)
 
st.caption(

    "Esses testes verificam a consistência com o arquivo "

    "da atividade. Não substituem a conferência dos dados "

    "com registros históricos oficiais."

)
 
 
# FONTES E LIMITAÇÕES

st.subheader("9. Fontes e limites da análise")
 
st.markdown("""

**Base utilizada:** arquivo WorldCups.csv fornecido na atividade.
 
**Referência oficial para consulta histórica:**  

[FIFA — Arquivo das Copas do Mundo](https://www.archives.fifa.com/fifa_world_cup)
 
O CSV não contém autoria ou endereço original de download.

A FIFA é indicada como referência histórica, sem afirmar

que publicou este arquivo específico.
 
A base termina em 2014. Portanto, os resultados não incluem

as Copas posteriores a esse ano.

""")
 
 
# USO DA IA

with st.expander("10. Como a IA ajudou no desenvolvimento?"):

    st.markdown("""

    **Problema encontrado:** adaptar os exemplos do tutorial

    aos dados das Copas e converter o público armazenado como texto.
 
    **Prompt utilizado:** solicitar um dashboard conforme o PDF,

    usando o CSV fornecido, com análises e explicações.
 
    **Sugestões aplicadas:** converter números, retirar pontos

    de milhar do público, agrupar a Alemanha no ranking histórico

    e analisar médias por partida além dos totais.
 
    **Como conferir:** utilizar a tabela de validação e comparar

    os resultados com os dados originais.
 
    **Registro do grupo:** após executar o aplicativo, descrevam

    quais sugestões aceitaram, o que modificaram e quais testes

    realizaram.

    """)
 
 
# GUIA PARA APRESENTAÇÃO

with st.expander("11. Como explicar a aplicação?"):

    st.markdown("""

    **O que investigamos?**  

    Títulos, gols, público e quantidade de seleções nas Copas

    de 1930 a 2014 presentes no CSV.
 
    **Quais ferramentas utilizamos?**  

    Pandas para leitura e tratamento, Plotly para gráficos

    e Streamlit para construir a aplicação.
 
    **Por que comparar médias?**  

    As edições têm quantidades diferentes de partidas.

    As médias ajudam a comparar gols e público por jogo.
 
    **Como os filtros funcionam?**  

    Selecionamos as edições na barra lateral.

    Os indicadores, gráficos e explicações são atualizados.
 
    **Quais são os limites?**  

    A base termina em 2014 e não permite provar as causas

    das diferenças observadas.
 
    **Como a IA ajudou?**  

    Na adaptação do código, no tratamento dos dados

    e na escolha das visualizações.

    """)
 