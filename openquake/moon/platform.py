from openquake.moon import Moon

_pla = None


def _platform_initialization():
    global _pla

    if _pla is None:
        _pla = Moon()
        _pla.primary_set()

    return _pla


def platform_get():
    return _platform_initialization()


def platform_del():
    global _pla

    if _pla is not None:
        _pla.fini()

    _pla = None
