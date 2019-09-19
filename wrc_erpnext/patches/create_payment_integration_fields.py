# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	make_custom_fields()

def make_custom_fields(update=True):
	employee_fields = [
		dict(fieldname='account_type', label='Account Type', fieldtype='Link',
			options='Account Type', insert_after='bank_ac_no'),
		dict(fieldname='bsb_number', label='BSB Number', fieldtype='Data',
			 insert_after='account_type')
	]

	bank_account_fields = [
		dict(fieldname='bsb_number', label='BSB Number', fieldtype='Data',
			 insert_after='iban'),
		dict(fieldname='eft_section', label='EFT Details', fieldtype='Section Break',
			 insert_after='swift_number'),
		dict(fieldname='client_name', label='Client Name', fieldtype='Data',
			 insert_after='eft_section'),
		dict(fieldname='col_break1', fieldtype='Column Break',
			 insert_after='client_name'),
		dict(fieldname='client_code', label='Client Code', fieldtype='Data',
			 insert_after='col_break1')
	]

	custom_fields = {
		"Employee": employee_fields,
		"Bank Account": bank_account_fields
	}
	create_custom_fields(custom_fields, update=update)