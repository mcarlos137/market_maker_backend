from setuptools import setup

setup(
    name='damexCommons',
    packages=['damexCommons','damexCommons.connectors', 'damexCommons.businesses', 'damexCommons.tools'],
    version='0.1.64',
    description='DAMEX Commons',
    author='Me',
    install_requires=['ccxt==4.4.3', 'websocket-client', 'psycopg2-binary', 'google-api-python-client', 'solana'],
    setup_requires=['pytest-runner', 'ccxt', 'websocket-client', 'psycopg2-binary', 'google-api-python-client', 'solana'],
    tests_require=['pytest==8.2.2'],
    test_suite='tests',
)