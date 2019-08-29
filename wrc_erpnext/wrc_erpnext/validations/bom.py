# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from stdnum import ean
from erpnext.stock.doctype.item.item import InvalidBarcode


def validate(doc, method):
	validate_barcode(doc)


def validate_barcode(doc):
	if doc.barcode:
		duplicate = frappe.db.get_value(
			"BOM", filters={"barcode": doc.barcode, "docstatus": 1}, fieldname=["name"])
		if duplicate:
			frappe.throw(_("Barcode {0} is already used in Item {1}").format(
				doc.barcode, duplicate, frappe.DuplicateEntryError))

		if doc.barcode_type and doc.barcode_type.upper() in ('EAN', 'UPC-A', 'EAN-13', 'EAN-8'):
			if not ean.is_valid(doc.barcode):
				frappe.throw(_("Barcode {0} is not a valid {1} code").format(
					doc.barcode, doc.barcode_type), InvalidBarcode)
