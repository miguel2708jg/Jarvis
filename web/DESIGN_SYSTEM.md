# Orbit Web Mobile Design System

## Direccion visual
La web se renderiza como una app movil centrada, inspirada en la referencia de dashboard educativo: fondo crema/menta, tarjetas blancas compactas, jerarquia teal, acentos amarillos para acciones primarias y navegacion inferior negra.

## Tokens CSS
- `--mobile-max: 430px`: ancho maximo de la experiencia web movil.
- `--mobile-gutter: 16px`: margen lateral interno.
- `--background: #eff7ef`: fondo principal.
- `--background-muted: #e3f0e9`: fondo exterior y lavados superiores.
- `--surface: #ffffff`: tarjetas, paneles y modales.
- `--surface-muted: #f7fbf7`: inputs, botones secundarios y estados suaves.
- `--ink: #101612`: texto principal y elementos de alto contraste.
- `--text-muted: #69766e`: descripcion y metadatos.
- `--accent: #5aae98` y `--accent-strong: #2f7d6a`: jerarquia teal.
- `--warning: #f2be3e`: acciones primarias, envio y llamadas importantes.
- `--tabbar: #090c0a`: navegacion inferior flotante.

## Layout
- La raiz `main` limita la UI a `430px` y la centra en desktop.
- Todas las vistas usan una sola columna como base, incluso en pantallas grandes.
- `app-shell` deja espacio inferior para la tabbar fija y respeta `safe-area-inset-bottom`.
- Las listas horizontales, como conversaciones y personalidades, usan scroll lateral y snap suave.

## Componentes
- `Hero`: cabecera compacta con eyebrow, titulo, copy y metricas verticales.
- `Panel`: contenedor blanco para controles de modulo.
- `Card`: item repetible con contenido breve y acciones directas.
- `Chip`: filtro o estado en forma pill.
- `Primary action`: boton amarillo de ancho completo en superficies moviles.
- `Tabbar`: barra negra fija, iconos sin texto y estado activo blanco.

## Reglas de uso
- Mantener tipografia compacta: `h1` cerca de 26px y `h2` cerca de 18px.
- Usar blanco para superficies funcionales y evitar tarjetas dentro de tarjetas.
- Reservar amarillo para acciones claras, no para decoracion secundaria.
- Evitar layouts de escritorio en la web principal; si se necesita desktop, crear una vista separada.
