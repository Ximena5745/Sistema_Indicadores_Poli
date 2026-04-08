from ._page_wrapper import load_disabled_page

module = load_disabled_page("5_Seguimiento_de_reportes.py")

def render():
    module.render()
