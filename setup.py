import os

from setuptools import find_packages, setup

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='discord_logview',
    version='2.0.1',
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
        'Framework :: Django :: 2.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        "natural==0.2.0",
        "celery==4.3.0",
        "celery-progress==0.0.8",
        "channels==2.3.0",
        "channels-redis==2.4.0",
        "demoji==0.1.5",
        "django==2.2.8",
        "django-allauth==0.40.0",
        "djangorestframework==3.10.2",
        "drf-yasg==1.16.1",
        "itsdangerous==1.1.0",
        "pendulum==2.0.5",
        "psycopg2==2.8.3",
        "python-decouple==3.1",
        "redis==3.3.8",
        "requests==2.22.0",
        "sentry-sdk==0.12.3",
        "shortuuid==0.5.0"
    ],
    extras_require={
        'win': ["gevent==1.4.0"],
        'test': ["responses==0.10.9"]
    }
)
