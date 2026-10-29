#!/usr/bin/env python3
# Generate harmless localhost-only test events for both sites.
import os
import sys

ROOT = os.path.abspath(os.path.dirname(__file__))

# Run from legitimate dir context
cwd = os.getcwd()
try:
    os.chdir(os.path.join(ROOT, 'sites', 'legitimate'))
    sys.path = [os.getcwd(), ROOT] + [p for p in sys.path if p != os.getcwd()]
    for k in list(sys.modules.keys()):
        if k.startswith(('app', 'services', 'config')):
            del sys.modules[k]
    from app import app as legit_app
    legit_client = legit_app.test_client()
    print('Legitimate: normal request to /')
    legit_client.get('/')
    print('Legitimate: navigate to /products')
    legit_client.get('/products')
    print('Legitimate: another page')
    legit_client.get('/about')
finally:
    os.chdir(cwd)

# Run from suspicious dir context
try:
    os.chdir(os.path.join(ROOT, 'sites', 'suspicious'))
    sys.path = [os.getcwd(), ROOT] + [p for p in sys.path if p != os.getcwd()]
    for k in list(sys.modules.keys()):
        if k.startswith(('app', 'services', 'config')):
            del sys.modules[k]
    from app import create_app
    susp_app = create_app()
    susp_client = susp_app.test_client()
    print('Suspicious: request to /')
    susp_client.get('/')
    print('Suspicious: lab-test redirect (302)')
    susp_client.get('/lab-test/redirect')
    print('Suspicious: repeated requests')
    for i in range(5):
        susp_client.get('/lab-test/repeat')
    print('Suspicious: unexpected resource local mock')
    susp_client.get('/lab-test/resources/unapproved.js')
finally:
    os.chdir(cwd)

print('\nDone. Check logs/web_logs.csv')
