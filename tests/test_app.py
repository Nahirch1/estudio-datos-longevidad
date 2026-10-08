"""Prueba de humo de la app (necesita streamlit): python3 tests/test_app.py"""
import pathlib
from streamlit.testing.v1 import AppTest
at = AppTest.from_file(str(pathlib.Path(__file__).resolve().parent.parent / 'app' / 'app_streamlit.py'), default_timeout=120).run()
assert not at.exception, at.exception
print('app OK; métricas:', [m.value for m in at.metric])
