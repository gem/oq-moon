import warnings

def pytest_configure(config):
    warnings.filterwarnings("ignore", category=ImportWarning, module="nose")

