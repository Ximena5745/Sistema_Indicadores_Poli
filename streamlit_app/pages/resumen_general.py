from ._page_wrapper import load_disabled_page

module = load_disabled_page("1_Resumen_General.py")

def render():
    module.render()
