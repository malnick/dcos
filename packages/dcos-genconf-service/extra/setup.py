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
        'dcos_genconf'
    ],
    'entry_points': {
        'console_scripts': [
            'dcos-genconf=dcos_genconf.service:main'
        ]
    },
    'install_requires': ['gen']
}

setup(**config)
