from ._page_wrapper import load_disabled_page

module = load_disabled_page("2_Gestion_OM.py")

def render():
    module.render()
