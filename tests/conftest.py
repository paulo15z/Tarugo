import os
import sys

import django


def pytest_configure(config) -> None:
    """
    Configura Django para permitir import de modules com models.

    Args:
        config: Objeto de configuração do pytest.
    """
    project_root = os.path.dirname(os.path.dirname(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    if not django.apps.apps.ready:
        django.setup()

