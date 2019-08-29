# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	make_custom_fields()


def make_custom_fields(update=True):
	bom_barcode_field = [
		dict(fieldname='bom_barcode', label='BOM Barcode', fieldtype='Data',
			 insert_after='image')
	]

	bom_barcode_section = [
		dict(fieldname='barcode_section', label='Barcode', fieldtype='Section Break',
			 insert_after='base_total_cost'),
		dict(fieldname='barcode', label='Barcode No.', fieldtype='Data',
			 insert_after='barcode_section'),
		dict(fieldname='col_break1', fieldtype='Column Break',
			 insert_after='barcode'),
		dict(fieldname='barcode_type', label='Barcode Type', fieldtype='Select',
			 insert_after='barcode', options=' \nEAN\nUPC-A')
	]

	custom_fields = {
		"Work Order": bom_barcode_field,
		"BOM": bom_barcode_section
	}
	create_custom_fields(custom_fields, update=update)
