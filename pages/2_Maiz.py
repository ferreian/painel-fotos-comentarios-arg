"""
pages/2_Maiz.py — Fotos y Comentarios · Maíz (Argentina)

Wrapper fino: toda la lógica está en pagina_fotos.render().
"Milho" se mantiene como argumento porque es el nombre de la tabla en Supabase;
el rótulo visible ("Maíz") lo resuelve ROTULO_CULTURA en pagina_fotos.py.
"""
from pagina_fotos import render

render("Milho", icone="🌽", imagem="Design_stats-rafiki.png")
