# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe import _
from collections import OrderedDict
from wrc_erpnext.wrc_erpnext.payments_integration import execute, generate_file_and_attach_to_doctype
from frappe.utils import getdate

@frappe.whitelist()
def generate_report(name):
	data, file_name = create_eft_file(name)
	return generate_file_and_attach_to_doctype(file_name, data, 'Payment Order', name)

def create_eft_file(name):
	''' generates a file for eft transactions based on kundu pei system for processing payment order '''

	payment_order = frappe.get_doc("Payment Order", name)

	if not payment_order.company_bank_account:
		frappe.throw(_('Company Bank Account has to be mentioned'))
	# client bank account
	bank_account = frappe.get_doc("Bank Account", payment_order.company_bank_account)

	trace_record = OrderedDict(
		account_type = [bank_account, 'bsb_no', 7, 'right', '0'],
		account_number = [bank_account, 'bank_account_no', 12, 'right', '0']
	)
	trace_record = execute(trace_record)

	total_amount = sum(entry.get("amount") for entry in payment_order.get("references"))
	file_name = 'sample_name.txt'

	header = get_header_row(payment_order, bank_account)
	detail = []
	for ref_doc in payment_order.get("references"):
		detail.append(get_detail_row(ref_doc, trace_record, bank_account)) 

	detail.append(get_debitor_information(ref_doc, trace_record, bank_account, total_amount))

	trailer = get_trailer_row(payment_order, bank_account, total_amount)
	detail_records = "\n".join(detail)

	return "\n".join([header, detail_records, trailer]), file_name

def get_header_row(payment_order, bank_account):

	date = getdate().strftime('%Y%m%d') 

	sequence_no = '01'

	header_row = OrderedDict(
		record_type=['0', '', 1],
		blank_1=['', '',17],
		sequence_no=[sequence_no, '', 2, 'right', '0'],
		Bank=[bank_account, 'bank', 3],
		blank_2=['', '', 7],
		user_name=[bank_account, 'client_name', 26, 'left', ' '],
		user_id=[bank_account, 'client_code', 6, 'right', '0'],
		entry_description=['PAYMENT ENTRY', '', 12, 'left', ' '],
		processing_date=[date, '', 8],
		blank_3=['', '', 50]
	)
	return execute(header_row)

def get_trailer_row(payment_order, bank_account, total_amount):
	no_of_records = len(payment_order.get("references"))

	trailer_row = OrderedDict(
		record_type=['7', '', 1],
		bsb_number=[bank_account, 'bsb_no', 7],
		blank_1=['', '', 12],
		net_amount=['0', '', 10, 'right', '0'],
		total_credit=[total_amount, '', 10, 'right', '0'],
		total_debit=[total_amount, '', 10, 'right', '0'],
		blank_2=['', '', 24],
		user_records=[no_of_records, '', 6],
		blank_3=['', '', 52]
	)
	return execute(trailer_row)

def get_detail_row(ref_doc, trace_detail, bank_account):

	vendor_bank_account = frappe.get_cached_doc('Bank Account', ref_doc.bank_account)

	account_detail = get_account_detail(vendor_bank_account)
	reference_doc = frappe.get_cached_doc(ref_doc.reference_doctype, ref_doc.reference_name)

	detail_row = OrderedDict(
		record_type=['1', '', 1],
		bsb_number=[vendor_bank_account,'bsb_no', 7],
		vendor_account=[account_detail, '', 15],
		indicator=[' ', '', 1],
		transaction_code=['53', '', 2],
		amount=[reference_doc, 'grand_total', 10, 'right', '0'],
		payment_to=[ref_doc, 'supplier', 32, 'left', ' '],
		lodgment_reference=[reference_doc, 'name', 18, 'left', ' '],
		trace_record=[trace_detail, '', 22],
		remitter_name=[bank_account, 'client_name', 16, 'left', ' '],
		withholding_tax=['', '', 8, 'right', '0']
	)

	return execute(detail_row)

def get_debitor_information(ref_doc, trace_detail, bank_account, total_amount):
	account_detail = get_account_detail(bank_account)
	withholding_tax = get_withholding_tax(ref_doc)
	return execute(OrderedDict(
		record_type=['1', '', 1],
		bsb_number=[bank_account,'bsb_no', 7],
		vendor_account=[account_detail, '', 15],
		indicator=[' ', '', 1],
		transaction_code=['13', '', 2],
		amount=[total_amount, '', 10, 'right', '0'],
		payment_to=[bank_account, 'client_name', 32, 'left', ' '],
		lodgment_reference=[ref_doc, 'reference_doctype', 18, 'left', ' '],
		trace_record=[trace_detail, '', 22],
		remitter_name=[bank_account, 'client_name', 16, 'left', ' '],
		withholding_tax=[withholding_tax, '', 8, 'right', '0']
	))

def get_account_detail(ref_doc):
	return execute(OrderedDict(
		account_type = [ref_doc, 'account_type', 3, 'right', '0'],
		account_number = [ref_doc, 'bank_account_no', 12, 'right', '0']
	))

def get_withholding_tax(ref_doc):
	tax_witholding_category = frappe.get_cached_value('Supplier', name=ref_doc.supplier, fieldname='tax_witholding_category')
	if not tax_witholding_category:
		return 0
	return frappe.get_value('Purchase Taxes and Charges', filters={
		'parenttype': 'Purchase Invoice',
		'add_deduct_tax': 'Deduct',
		'parent': ref_doc.reference_name
		}, fieldname='base_tax_amount_after_discount_amount')