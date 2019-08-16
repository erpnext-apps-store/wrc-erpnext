# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in wrc_erpnext/__init__.py
from wrc_erpnext import __version__ as version

setup(
	name='wrc_erpnext',
	version=version,
	description='ERPNext customisation for WRC',
	author='Frappe',
	author_email='info@frappe.io',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
