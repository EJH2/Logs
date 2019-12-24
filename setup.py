import os

from setuptools import find_packages, setup

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='discord_logview',
    version='2.0.2',
    packages=find_packages(),
    include_package_data=True,
    license='MIT License',
    description='A simple app to beautify Discord log files.',
    url='https://logs.discord.website',
    author='EJH2',
    author_email='me@ej.gl',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        "natural",
        "celery",
        "celery-progress",
        "channels",
        "channels-redis",
        "demoji",
        "django",
        "django-allauth",
        "djangorestframework",
        "drf-yasg",
        "itsdangerous",
        "pendulum",
        "psycopg2",
        "python-decouple",
        "redis",
        "requests",
        "sentry-sdk",
        "shortuuid"
    ],
    extras_require={
        'win': ["gevent"],
        'test': ["responses"]
    }
)
