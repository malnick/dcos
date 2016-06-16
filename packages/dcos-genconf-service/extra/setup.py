from setuptools import setup

config = {
    'name': 'dcos-genconf',
    'version': '0.1.0',
    'description': 'Generates DC/OS site-configuration from config.yaml.',
    'author': 'Mesosphere, Inc.',
    'author_email': 'help@dcos.io',
    'maintainer': 'DC/OS Community',
    'maintainer_email': 'help@dcos.io',
    'url': 'https://dcos.io',
    'packages': [
        'genconf'
    ],
    'entry_points': {
        'console_scripts': [
            'dcos-genconf= genconf.service:run'
        ]
    },
    'install_requires': ['gen']
}

setup(**config)
