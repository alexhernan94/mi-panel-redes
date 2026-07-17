"""
Estilos responsive para dashboard mobile-first.
Se inyectan junto con ESTILO_EDITORIAL para que el panel sea usable en móvil.
"""

ESTILO_MOBILE = """
<style>
    /* === MOBILE-FIRST RESPONSIVE === */
    
    /* Reducir padding general en móvil */
    @media (max-width: 768px) {
        .stApp > header { display: none; }
        .block-container { padding: 1rem 0.8rem !important; max-width: 100% !important; }
        
        /* KPIs en 2 columnas en vez de 4 */
        [data-testid="column"] { min-width: 45% !important; }
        [data-testid="stMetric"] { padding: 0.8rem !important; }
        [data-testid="stMetricValue"] { font-size: 1.5rem !important; }
        [data-testid="stMetricLabel"] { font-size: 0.6rem !important; }
        
        /* Tabs más compactos */
        .stTabs [data-baseweb="tab"] { font-size: 0.65rem !important; padding-bottom: 0.4rem; }
        .stTabs [data-baseweb="tab-list"] { gap: 0.8rem !important; }
        
        /* Header más pequeño */
        h1 { font-size: 1.3rem !important; }
        h2 { font-size: 1.1rem !important; }
        h3 { font-size: 1rem !important; }
        h4 { font-size: 0.9rem !important; }
        
        /* Tablas scrollables */
        [data-testid="stDataFrame"] { overflow-x: auto !important; }
        
        /* Gráficos de altura reducida */
        .vega-embed { max-height: 180px !important; }
        
        /* Idea cards más compactos */
        .idea-card { padding: 0.8rem !important; font-size: 0.78rem !important; }
        
        /* Badges más pequeños */
        .badge-largo, .badge-corto, .badge-foto { font-size: 0.55rem !important; padding: 2px 6px !important; }
        .badge-keyword { font-size: 0.65rem !important; padding: 3px 8px !important; }
        
        /* Bloque Hoy - más compacto */
        div[style*="linear-gradient"] { padding: 1.2rem !important; }
        div[style*="linear-gradient"] h2 { font-size: 1.2rem !important; }
        div[style*="linear-gradient"] p { font-size: 0.8rem !important; }
        
        /* Semana visual - más estrecha */
        div[style*="text-align:center"] { padding: 4px 2px !important; font-size: 0.7rem !important; }
    }
    
    /* Tablets */
    @media (min-width: 769px) and (max-width: 1024px) {
        .block-container { padding: 1.5rem 1.5rem !important; }
        [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
    }
    
    /* Touch-friendly: botones más grandes */
    @media (hover: none) and (pointer: coarse) {
        button { min-height: 44px !important; }
        input { min-height: 44px !important; font-size: 16px !important; }
        .stRadio > div { gap: 0.5rem !important; }
        .stRadio label { padding: 0.5rem 0.8rem !important; }
    }
</style>
"""
