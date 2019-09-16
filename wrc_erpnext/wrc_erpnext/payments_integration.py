# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cint,cstr, getdate
from frappe import _
import re
import datetime
from frappe.utils.data import get_link_to_form

def generate_file_and_attach_to_doctype(file_name, data, ref_doctype, ref_name):
	f = frappe.get_doc({
		'doctype': 'File',
		'file_name': file_name,
		'content': data,
		"attached_to_doctype": ref_doctype,
		"attached_to_name": ref_name,
		'is_private': True
	})
	f.save()
	return {
		'file_url': f.file_url,
		'file_name': file_name
	}

def execute(record_dict):
	row = ''
	for k, v in record_dict.items():
		val = validate_information(v[0], v[1], v[2])
		try :
			# format values based on length, justification and padding_type
			val =  format_value(val, v[2], v[3], v[4])
		except IndexError as e:
			# Handle blanks
			val = format_value(val, v[2])
		row += val
	return row

def validate_information(obj, attr, max_size):
	''' Checks if the information is not set in the system and is within the size '''

	if getattr(obj, attr, None):
		val = getattr(obj, attr)
		if type(val) == 'int':
			return validate_amount(val, max_size)
		else:
			return validate_field_size(val, frappe.unscrub(attr), max_size)

	elif not attr:
		return cstr(obj)

	else:
		if obj.doctype:
			link = obj.doctype +' '+ get_link_to_form(obj.doctype, obj.name)
		else:
			link = str(obj.name)
		frappe.throw(_("{0} in {1} is mandatory for generating file, set the field and try again").format(frappe.unscrub(attr), link))

def validate_field_size(val, label, max_size):
	''' check the size of the val '''
	if len(cstr(val)) > max_size:
		frappe.throw(_("{0} field is limited to size {1}".format(label, max_size)))
	return cstr(val)

def validate_amount(val, max_int_size):
	''' Validate amount to be within the allowed limits  '''
	int_size = len(str(val).split('.')[0])

	if int_size > max_int_size:
		frappe.throw(_("Amount for a single transaction exceeds maximum allowed amount, create a separate payment order by splitting the transactions"))

	return sanitize_data(cstr(val))

def format_value(val, length, justification='right', padding_type=' '):
	''' format value based on the length, justification and padding type '''
	if justification == 'right':
		return val.rjust(length, padding_type)
	else:
		return val.ljust(length, padding_type)

# def generate_file_name(name, company_account, date):
# 	''' generate file name with format (account_code)_mmdd_(payment_order_no) '''
# 	bank, acc_no = frappe.db.get_value("Bank Account", {"name": company_account}, ['bank', 'bank_account_no'])
# 	return bank[:1]+str(acc_no)[-4:]+'_'+date.strftime("%m%d")+sanitize_data(name, '')[4:]+'.txt'

def sanitize_data(val, replace_str=''):
	''' Remove all the non-alphanumeric characters from string '''
	pattern = re.compile('[\W_]+')
	return pattern.sub(replace_str, val)

# def format_date(val):
# 	''' Convert a datetime object to DD/MM/YYYY format '''
# 	return val.strftime("%d/%m/%Y")