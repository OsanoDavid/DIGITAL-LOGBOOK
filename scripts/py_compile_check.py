import py_compile,traceback
files=['core/views.py','core/tests.py','sist_project/settings.py']
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f, 'OK')
    except Exception:
        print('ERROR compiling', f)
        traceback.print_exc()
