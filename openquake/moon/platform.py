from openquake.moon import Moon

pla = None


def platform_initialization():
    global pla

    if pla is None:
        pla = Moon()
        pla.primary_set()


def platform_get():
    if pla is None:
        platform_initialization()

    return pla
