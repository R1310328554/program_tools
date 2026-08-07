from .registry import tools_by_category


def toolbox_nav(request):
    return {
        'nav_categories': tools_by_category(),
    }
