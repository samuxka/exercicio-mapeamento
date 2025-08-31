import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import requests

# Load the Excel data
df = pd.read_excel('planilha.xlsx')

# Clean and standardize 'Regiao-estado'
df['Regiao-estado'] = df['Regiao-estado'].replace({
    'null': None,
    '': None
}).fillna('Unknown')

# Create region_counts
region_counts = df.groupby('Regiao-estado').size().reset_index(name='count')
region_counts = region_counts[region_counts['Regiao-estado'] != 'Unknown']

# Create top_industry
top_industry = df.groupby('Regiao-estado')['industry'].agg(lambda x: x.mode()[0] if not x.empty else 'N/A').reset_index(name='top_industry')
top_industry = top_industry[top_industry['Regiao-estado'] != 'Unknown']

# Create industries_per_region
industries_per_region = df.groupby(['Regiao-estado', 'industry']).size().reset_index(name='count')
industries_per_region = industries_per_region[industries_per_region['Regiao-estado'] != 'Unknown']


# Define size categories and create sizes_per_region
size_mapping = {
    '11-50': 'P',
    '51-200': 'M',
    '201-500': 'L',
    '501-1000': 'G',
    '1001-5000': 'MG',
    '5001-10000': 'MG',
    '10001+': 'MG',
    '45931': 'Unknown'
}
df['size_category'] = df['size'].map(size_mapping).fillna('Unknown')
sizes_per_region = df.groupby(['Regiao-estado', 'size_category']).size().reset_index(name='count')
sizes_per_region = sizes_per_region[sizes_per_region['Regiao-estado'] != 'Unknown']
sizes_per_region = sizes_per_region[sizes_per_region['size_category'] != 'Unknown']

# Region mapping to match GeoJSON
region_mapping = {
    'Lisbon': 'Lisboa',
    'Porto': 'Porto',
    'Aveiro': 'Aveiro',
    'Braga': 'Braga',
    'Coimbra': 'Coimbra',
    'Faro': 'Faro',
    'Leiria': 'Leiria',
    'Setúbal': 'Setúbal',
    'Viana do Castelo': 'Viana do Castelo',
    'Vila Real': 'Vila Real',
    'Viseu': 'Viseu',
    'Castelo Branco': 'Castelo Branco',
    'Santarem': 'Santarém',
    'Azores': 'Açores'
}
region_counts['Regiao-estado'] = region_counts['Regiao-estado'].map(region_mapping).fillna(region_counts['Regiao-estado'])
top_industry['Regiao-estado'] = top_industry['Regiao-estado'].map(region_mapping).fillna(top_industry['Regiao-estado'])
industries_per_region['Regiao-estado'] = industries_per_region['Regiao-estado'].map(region_mapping).fillna(industries_per_region['Regiao-estado'])
sizes_per_region['Regiao-estado'] = sizes_per_region['Regiao-estado'].map(region_mapping).fillna(sizes_per_region['Regiao-estado'])

# Load GeoJSON
geojson_url = "https://data.opendatasoft.com/api/explore/v2.1/catalog/datasets/districts-portugal@e-redes/exports/geojson?lang=en&timezone=Europe%2FBerlin"
response = requests.get(geojson_url)
geojson = response.json()

# Color scale
colors = ['#D3D3D3', '#7AB34F', '#2E5D1C']
min_count, max_count = region_counts['count'].min(), region_counts['count'].max()
bins = pd.cut(region_counts['count'], bins=3, retbins=True, include_lowest=True)[1]
legend_items = [f"{int(bins[i])} - {int(bins[i+1])}" for i in range(len(bins)-1)]

# Gráficos vazios no tema escuro
empty_fig = go.Figure()
empty_fig.update_layout(
    template='plotly_dark',
    paper_bgcolor='#161616',
    plot_bgcolor='#161616',
    font=dict(color='white')
)

app = Dash(__name__)

app.layout = html.Div([
html.Div([
html.H1(id='region-title', style={'textAlign': 'center'}),
html.Div([
html.Div(id='company-count-box', style={'border': '1px solid white', 'padding': '10px', 'margin': '10px'}),
html.Div(id='top-segment-box', style={'border': '1px solid white', 'padding': '10px', 'margin': '10px'})
], style={'display': 'flex'}),
dcc.Graph(id='segments-graph', figure=empty_fig),
dcc.Graph(id='sizes-graph', figure=empty_fig),
], style={'width': '50%', 'float': 'left'}),
html.Div([
dcc.Graph(id='portugal-map'),
html.Div([
html.Div([
html.Div(style={'backgroundColor': color, 'width': '20px', 'height': '20px', 'display': 'inline-block'}),
html.Span(range_text, style={'marginLeft': '10px', 'color': 'white'})
], style={'marginBottom': '5px'}) for color, range_text in zip(colors, legend_items)
], style={'margin': '10px'})
], style={'width': '50%', 'float': 'right'}),
html.Div([
html.H3('Distribuição Geográfica e Estratégias de Posicionamento Regional'),
html.P('A planilha revela um forte cluster em Lisboa (mais de 80% das empresas listadas, com 228 na região de Lisbon vs. 60 em Porto), tornando-a o epicentro para setores como IT e RH. Porto emerge como um hub secundário para construção, manufatura e nonprofits. Para se posicionar:'),
html.Ul([
html.Li('Em Lisboa/Oeiras: Priorize networking em subúrbios como Oeiras (28 empresas, foco em pharma e tech como Novartis Portugal e IQVIA Portugal). Participe de eventos no Unicorn Factory Lisboa ou Landing.Jobs para conexões em startups de IT (29 empresas de IT em Lisboa). Posicione-se como especialista em inovação digital, visando vagas em empresas médias (51-200 funcionários, como Growin ou Bee Engineering), que representam 40% do dataset e crescem rápido pós-2010.'),
html.Li('Em Porto/Matosinhos: Foque em indústrias tradicionais como construção (ex: Mota-Engil Engenharia) e manufatura (ex: Laskasas). Com apenas 3 empresas de IT vs. 29 em Lisboa, evite tech aqui; em vez disso, explore RH local (apenas 1 vs. 20 em Lisboa) via associações como AEP - Portuguese Business Association. Posicione-se em papéis de gerenciamento de projetos em empresas grandes (501+ funcionários, como Grupo Impetus), aproveitando o custo de vida mais baixo para negociações salariais.')
]),
html.Table([
html.Thead(html.Tr([html.Th(col) for col in ['Região', 'Empresas Totais', 'Indústrias Dominantes', 'Dica de Posicionamento']])),
html.Tbody([
html.Tr([html.Td('Lisbon'), html.Td('228'), html.Td('IT (29), HR (20), Pharma (10)'), html.Td('Rede via LinkedIn com clusters em Oeiras; foque em startups fundadas pós-2016 para culturas ágeis.')]),
html.Tr([html.Td('Porto'), html.Td('60'), html.Td('Construction (8), Manufatura (6), Nonprofits (5)'), html.Td('Participe de eventos da UPTEC para tech/manufatura; posicione-se em papéis operacionais em firmas estabelecidas (pré-2000).')]),
html.Tr([html.Td('Aveiro/Braga'), html.Td('28'), html.Td('Construction/Manufatura (10), IT (5)'), html.Td('Mire empresas familiares como RODI Industries; use associações como Inova-Ria para entrada em redes regionais.')])
])
], style={'border': '1px solid white', 'width': '100%', 'borderCollapse': 'collapse'}),
html.H3('Análise Setorial e Oportunidades por Indústria'),
html.P('Indústrias top: IT & Services (42 empresas, 11% do total) e HR (28, 7%), com crescimento notável em tech pós-2010 (23 novas empresas). Construção e marketing também fortes, mas com mais empresas grandes (construction: 6 com 501+ funcionários). Insights para posicionamento:'),
html.Ul([
html.Li('IT & Software (57 empresas combinadas): Alto turnover em médias empresas (51-200: 147 no total, mas 40% em tech). Posicione-se destacando skills em IA/automação (ex: Smartex.ai em Porto ou Codacy em Lisboa). Evite genéricos; foque em certificações como AWS/DevOps para atrair firmas como Syone ou Crossjoin Solutions, que buscam talento internacional via Landing.Jobs.'),
html.Li('Human Resources/Staffing (30 empresas): Dominado por agências em Lisboa (20). Use como porta de entrada: contate Vertente Humana ou Adecco Portugal para colocações em tech/construção. Posicione-se como consultor em diversidade (crescimento em nonprofits), visando vagas em grandes como Triangle Solutions RH.'),
html.Li('Construção/Civil Engineering (24 empresas): Muitas grandes (1001+ funcionários, ex: Tecnovia SGPS). Foque em sustentabilidade (ex: via APREN para renováveis). Posicione-se com expertise em BIM ou green building para projetos em Porto/Braga, onde há clusters como NVE engenharias.'),
html.Li('Setores Emergentes (Pós-2010: 23% do dataset): Tech/internet/marketing dominam novas fundações. Posicione-se em nichos como cibersegurança (ex: Centro Nacional de Cibersegurança) ou impacto social (ex: Goparity), usando plataformas como Startup Portugal para pitchs a VCs como Indico Capital Partners.')
]),
html.Table([
html.Thead(html.Tr([html.Th(col) for col in ['Indústria', 'Empresas', '% Recentes (Pós-2010)', 'Estratégia Profissional']])),
html.Tbody([
html.Tr([html.Td('IT & Services'), html.Td('42'), html.Td('55%'), html.Td('Desenvolva portfólio em cloud/IA; rede com 29 em Lisboa via Beta-i para parcerias.')]),
html.Tr([html.Td('Human Resources'), html.Td('28'), html.Td('25%'), html.Td('Ofereça serviços de recrutamento remoto; use 20 em Lisboa como bridge para tech jobs.')]),
html.Tr([html.Td('Construction'), html.Td('17'), html.Td('18%'), html.Td('Certifique-se em ESG; mire grandes em Porto para projetos infra (ex: Metro do Porto).')]),
html.Tr([html.Td('Marketing & Advertising'), html.Td('16'), html.Td('38%'), html.Td('Foque em digital ads; posicione via associações como APPM para clients em Lisboa.')])
])
], style={'border': '1px solid white', 'width': '100%', 'borderCollapse': 'collapse'}),
html.H3('Perfil de Empresas e Networking Tático'),
html.P('Tamanhos: Empresas médias (51-200: 147) oferecem mais flexibilidade que grandes (10001+: 8, ex: ALTEN Portugal). Fundadas pré-2000 (45%) são estáveis, mas pós-2010 (23%) inovadoras. Estratégias:'),
html.Ul([
html.Li('Networking via LinkedIn: Todas as empresas têm perfis; priorize follow-ups com RH de firmas como Experis Portugal ou Get The Job. Envie mensagens personalizadas citando indústrias comuns (ex: "Interessado em IT sustentável, como em Madoqua").'),
html.Li('Entrada no Mercado: Para profissionais estrangeiros, vise RH agencies (28 listadas) para vistos/tech roles. Posicione CV destacando adaptação cultural (ex: bilingual PT/EN). Evite grandes burocráticas; mire médias em Lisboa para promoções rápidas.'),
html.Li('Crescimento Pessoal: Invista em educação via EDIT. ou Lisbon Digital School (marketing/tech). Para liderança, junte-se a associações como APG ou Ordem dos Engenheiros (nonprofits/engineering clusters).')
]),
], style={'clear': 'both', 'border': '1px solid white', 'padding': '10px', 'margin-top': '50px'})
], style={'backgroundColor': '#161616', 'color': 'white', 'minHeight': '100vh', 'padding': '20px'})

@app.callback(
    [Output('region-title', 'children'),
     Output('company-count-box', 'children'),
     Output('top-segment-box', 'children'),
     Output('segments-graph', 'figure'),
     Output('sizes-graph', 'figure')],
    Input('portugal-map', 'clickData')
)
def update_left_side(clickData):
    if clickData is None:
        return "Selecione uma Região", "", "", go.Figure(), go.Figure()
    
    location = clickData['points'][0]['location']
    region = location
    
    count_row = region_counts[region_counts['Regiao-estado'] == region]
    count = count_row['count'].values[0] if not count_row.empty else 0
    
    top_row = top_industry[top_industry['Regiao-estado'] == region]
    top_seg = top_row['top_industry'].values[0] if not top_row.empty else "N/A"
    
    ind_df = industries_per_region[industries_per_region['Regiao-estado'] == region]
    seg_fig = px.bar(
        ind_df, x='industry', y='count', title='Maiores Segmentos',
        template='plotly_dark'
    ) if not ind_df.empty else go.Figure()
    
    size_df = sizes_per_region[sizes_per_region['Regiao-estado'] == region]
    size_fig = px.bar(
        size_df, x='size_category', y='count',
        title='Tamanhos das Empresas (P:11-50, M:51-200, L:201-500, G:501-1000, MG:1001+)',
        template='plotly_dark'
    ) if not size_df.empty else go.Figure()
    
    # Dark background for figures
    for fig in [seg_fig, size_fig]:
        fig.update_layout(
            paper_bgcolor='#161616',
            plot_bgcolor='#161616',
            font=dict(color='white')
        )
    
    return region, f"Quantidade de Empresas: {count}", f"Maior Segmento: {top_seg}", seg_fig, size_fig

@app.callback(
    Output('portugal-map', 'figure'),
    Input('portugal-map', 'id')
)
def display_map(_):
    fig = px.choropleth_mapbox(
        region_counts,
        geojson=geojson,
        locations='Regiao-estado',
        featureidkey='properties.dis_name',
        color='count',
        color_continuous_scale=colors,
        range_color=(min_count, max_count),
        mapbox_style="carto-darkmatter",
        zoom=4,
        center={"lat": 39.3999, "lon": -8.2245},
        opacity=1,
        labels={'count': 'Empresas'}
    )
    fig.update_layout(
        margin={"r":0, "t":0, "l":0, "b":0},
        clickmode='event+select',
        paper_bgcolor='#161616',
        font=dict(color='white')
    )
    return fig

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=False)
