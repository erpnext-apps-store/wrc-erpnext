# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe import _
from collections import OrderedDict
from wrc_erpnext.wrc_erpnext.payments_integration import execute,\
	generate_file_and_attach_to_doctype, generate_file_name
from frappe.utils import getdate, flt, cstr

@frappe.whitelist()
def generate_report(name):
	frappe.flags.witholding_tax_amt = 0
	data, file_name = create_eft_file(name)
	return generate_file_and_attach_to_doctype(file_name, data, 'Payment Order', name)

def create_eft_file(name):
	''' generates a file for eft transactions based on kundu pei system for processing payment order '''

	payment_order = frappe.get_doc("Payment Order", name)
	file_name = generate_file_name(name, payment_order.doctype, getdate())

	if not payment_order.company_bank_account:
		frappe.throw(_('Company Bank Account has to be mentioned'))

	# client bank account
	bank_account = frappe.get_doc("Bank Account", payment_order.company_bank_account)

	trace_record = get_trace_record(bank_account)

	# total amount getting debitted
	total_amount = sum(entry.get("amount") for entry in payment_order.get("references"))

	# fetch header row information (record type 0)
	header = get_header_row(payment_order, bank_account)

	# fetch detail row information (record type 1)
	detail = []
	bank_account.client_name = cstr(bank_account.client_name)[:16]
	for ref_doc in payment_order.get("references"):
		detail.append(get_detail_row(ref_doc, trace_record, bank_account, payment_order.company)) 

	detail.append(get_debitor_information(ref_doc, trace_record, bank_account, total_amount))
	detail_records = "\r\n".join(detail)

	# fetch trailer row information (record type 7)
	trailer = get_trailer_row(payment_order, bank_account, total_amount)

	return "\r\n".join([header, detail_records, trailer]), file_name

def get_header_row(payment_order, bank_account):

	date = getdate().strftime('%Y%m%d') 

	sequence_no = 1

	header_row = OrderedDict(
		record_type=['0', '', 1],
		blank_1=['', '',17],
		sequence_no=[sequence_no, '', 2, 'right', '0'],
		Bank=[bank_account, 'bank', 3],
		blank_2=['', '', 7],
		user_name=[bank_account, 'client_name', 26, 'left', ' '],
		user_id=[bank_account, 'client_code', 6, 'right', '0'],
		entry_description=['Purchase Invoice', '', 12, 'left', ' '],
		processing_date=[date, '', 8],
		blank_3=['', '', 50]
	)
	return execute(header_row)

def get_trailer_row(payment_order, bank_account, total_amount):
	no_of_records = len(payment_order.get("references"))

	trailer_row = OrderedDict(
		record_type=['7', '', 1],
		bsb_no=[bank_account, 'bsb_number', 7],
		blank_1=['', '', 12],
		net_amount=['0', '', 10, 'right', '0'],
		total_credit=[total_amount, '', 10, 'right', '0'],
		total_debit=[total_amount, '', 10, 'right', '0'],
		blank_2=['', '', 24],
		user_records=[no_of_records, '', 6],
		blank_3=['', '', 52]
	)
	return execute(trailer_row)

def get_detail_row(ref_doc, trace_detail, bank_account, company):

	vendor_bank_account = frappe.get_cached_doc('Bank Account', ref_doc.bank_account)

	account_detail = get_account_detail(vendor_bank_account)
	reference_doc = frappe.get_cached_doc(ref_doc.reference_doctype, ref_doc.reference_name)
	# reference_doc.name = reference_doc.name[-18:].partition('-')
	withholding_tax = get_withholding_tax(ref_doc, company)
	frappe.flags.witholding_tax_amt += flt(withholding_tax) 

	detail_row = OrderedDict(
		record_type=['1', '', 1],
		bsb_no=[vendor_bank_account,'bsb_number', 7],
		vendor_account=[account_detail, '', 15],
		indicator=[' ', '', 1],
		transaction_code=['53', '', 2],
		amount=[reference_doc, 'grand_total', 10, 'right', '0'],
		payment_to=[ref_doc, 'supplier', 32, 'left', ' '],
		lodgment_reference=[reference_doc, 'name', 18, 'left', ' '],
		trace_record=[trace_detail, '', 22],
		remitter_name=[bank_account, 'client_name', 16, 'left', ' '],
		withholding_tax=[withholding_tax, '', 8, 'right', '0']
	)

	return execute(detail_row)

def get_debitor_information(ref_doc, trace_detail, bank_account, total_amount):
	''' Returns debitor row corresponding to all the column '''
	account_detail = get_account_detail(bank_account)
	return execute(OrderedDict(
		record_type=['1', '', 1],
		bsb_no=[bank_account,'bsb_number', 7],
		vendor_account=[account_detail, '', 15],
		indicator=[' ', '', 1],
		transaction_code=['13', '', 2],
		amount=[total_amount, '', 10, 'right', '0'],
		payment_to=[bank_account, 'client_name', 32, 'left', ' '],
		lodgment_reference=[ref_doc, 'reference_doctype', 18, 'left', ' '],
		trace_record=[trace_detail, '', 22],
		remitter_name=[bank_account, 'client_name', 16, 'left', ' '],
		withholding_tax=[frappe.flags.witholding_tax_amt, '', 8, 'right', '0']
	))

def get_account_detail(ref_doc):
	''' Return account detail based on account type + bank account no'''
	return execute(OrderedDict(
		account_type = [ref_doc, 'account_type', 3, 'right', '0'],
		account_number = [ref_doc, 'bank_account_no', 12, 'right', '0']
	))

def get_trace_record(bank_account):
	''' Return trace record based on bsb number + account type + bank account no '''
	return execute(OrderedDict(
		bsb_no = [bank_account, 'bsb_number', 7, 'right', '0'],
		account_type = [bank_account, 'account_type', 3, 'right', '0'],
		account_number = [bank_account, 'bank_account_no', 12, 'right', '0']
	))

def get_withholding_tax(ref_doc, company):
	''' Returns withholding tax amount '''
	tax_witholding_accounts = get_tax_witholding_account(ref_doc.supplier, company)
	if not tax_witholding_accounts:
		return 0
	return frappe.get_value('Purchase Taxes and Charges', filters={
		'parenttype': 'Purchase Invoice',
		'add_deduct_tax': 'Deduct',
		'parent': ref_doc.reference_name,
		'account_head': ('in', tax_witholding_accounts)
		}, fieldname='base_tax_amount_after_discount_amount')

def get_tax_witholding_account(supplier, company):
	''' Returns a list of withholding tax accounts linked with given supplier for the provided company '''
	tax_category = frappe.get_cached_value('Supplier', name=supplier, fieldname='tax_withholding_category')
	accounts = frappe.db.get_values('Tax Withholding Account', filters={
		'parent': tax_category,
		'parentfield': 'accounts',
		'company': company
	},fieldname = 'account')
	return [a[0] for a in accounts]