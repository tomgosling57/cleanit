import os

_SVG_ICONS = {}
SVG_DIR = 'icons/svg'

def load_svg_icons(app):
    """
    Loads SVG icons from the static/icons/svg directory into a dictionary
    and makes them available globally in Jinja2 templates.
    """
    svg_path = os.path.join(app.static_folder, SVG_DIR)
    if not os.path.exists(svg_path):
        app.logger.warning(f"SVG directory not found: {svg_path}")
        app.jinja_env.globals['svg_icons'] = {}
        return

    for filename in os.listdir(svg_path):
        if filename.endswith('.svg'):
            file_path = os.path.join(svg_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    _SVG_ICONS[filename.replace('.svg', '')] = f.read()
            except IOError as e:
                app.logger.error(f"Error loading SVG file {file_path}: {e}")
    app.jinja_env.globals['svg_icons'] = _SVG_ICONS