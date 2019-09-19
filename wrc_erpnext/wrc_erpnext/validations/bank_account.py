# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import re

def validate(doc, method):
	validate_bsb_number(doc.bsb_number)

@frappe.whitelist()
def validate_bsb_number(bsb_number):
	if bsb_number:
		pattern = re.compile('^\d{3}-\d{3}$')
		if not re.match(pattern, bsb_number):
			frappe.throw(_("Invalid BSB Number!"))