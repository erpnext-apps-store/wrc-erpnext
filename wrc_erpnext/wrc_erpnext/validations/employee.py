# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from wrc_erpnext.wrc_erpnext.validations.bank_account import validate_bsb_number

def validate(doc, method):
	validate_bsb_number(doc.bsb_number)