# Pixel Autumn Leaves

[English](#english) | [Español](#español)

---

## English

Omarchy shell service plugin that renders an animated autumn pixel-art wallpaper with gently falling leaves on the `Bottom` Wayland layer (behind windows, above the static wallpaper).

- **Zero-overhead theme awareness**: Automatically activates only when the **Pixel Autumn** theme is set in Omarchy. With any other theme, no windows are created and the render loop is completely stopped.
- **Accurate canopy spawning**: Leaves detach from real procedural canopy clusters and settle on the grass with a natural pixel-art settling and fading animation.
- **Low CPU footprint**: Runs at 20 FPS (ideal for pixel art) with lightweight QML primitives.

### Installation

```bash
omarchy plugin add https://github.com/oliveralerubio/omarchy-pixel-autumn-leaves.git --enable --yes
```

To regenerate the procedural pixel-art scene or tweak tree parameters:

```bash
python3 gen_scene.py .   # requires Pillow (python-pillow)
```

### Requirements

- [Omarchy](https://github.com/basecamp/omarchy) Linux desktop environment.
- [Pixel Autumn](https://github.com/oliveralerubio/omarchy-pixel-autumn) theme.

### License

MIT License.

---

## Español

Plugin de servicio para el shell de Omarchy que pinta un fondo animado pixel art otoñal con hojas que caen suavemente sobre la capa Wayland `Bottom` (detrás de las ventanas, sobre el fondo estático).

- **Detección inteligente de tema**: Se activa únicamente cuando el tema activo en Omarchy es **Pixel Autumn**. Con cualquier otro tema, no crea ventanas y el bucle de render se detiene por completo (cero consumo).
- **Nacimiento orgánico en copas**: Las hojas nacen dentro de las copas de los árboles procedimentales y se posan sobre el pasto con una animación pixel art escalonada.
- **Bajo consumo de CPU**: Animado a 20 FPS con primitivas QML optimizadas.

### Instalación

```bash
omarchy plugin add https://github.com/oliveralerubio/omarchy-pixel-autumn-leaves.git --enable --yes
```

Para regenerar la escena procedimental o ajustar parámetros de los árboles:

```bash
python3 gen_scene.py .   # requires Pillow (python-pillow)
```

### Requisitos

- Entorno de escritorio [Omarchy](https://github.com/basecamp/omarchy).
- Tema [Pixel Autumn](https://github.com/oliveralerubio/omarchy-pixel-autumn).

### Licencia

MIT License.
