# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from collections import OrderedDict
from wrc_erpnext.wrc_erpnext.payments_integration import execute, generate_file_and_attach_to_doctype
from frappe.utils import getdate


@frappe.whitelist()
def generate_report(name):
	data, file_name = create_eft_file(name)
	return generate_file_and_attach_to_doctype(file_name, data, 'Payroll Entry', name)

def create_eft_file(name):
	payroll_entry = frappe.get_doc("Payroll Entry", name)

	if not payroll_entry.bank_account:
		frappe.throw(_('Bank Account has to be mentioned'))
	# client bank account
	bank_account = frappe.get_doc("Bank Account", payroll_entry.bank_account)

	trace_record = OrderedDict(
		account_type = [bank_account, 'bsb_no', 7, 'right', '0'],
		account_number = [bank_account, 'bank_account_no', 12, 'right', '0']
	)
	trace_record = execute(trace_record)

	file_name = 'sample_name.txt'
	header = get_header_row(payroll_entry, bank_account)
	detail = []
	for ref_doc in payroll_entry.get("employees"):
		detail.append(get_detail_row(ref_doc, payroll_entry, trace_record, bank_account)) 

	detail.append(get_debitor_information())


	trailer = get_trailer_row(payroll_entry, bank_account)
	detail_records = "\n".join(detail)

	return "\n".join([header, detail_records, trailer]), file_name

def get_header_row(payroll_entry, bank_account):

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
		entry_description=['PAYROLL', '', 12, 'left', ' '],
		processing_date=[date, '', 8],
		blank_3=['', '', 50]
	)
	return execute(header_row)

def get_trailer_row(payroll_entry, bank_account):
	no_of_records = len(payroll_entry.employees)
	journal_entry = get_journal_entry(payroll_entry.name)

	if not journal_entry[0]:
		frappe.throw(_('Bank Entry is not created for the payroll entry'))

	trailer_row = OrderedDict(
		record_type=['7', '', 1],
		bsb_number=[bank_account, 'bsb_no', 7],
		blank_1=['', '', 12],
		net_amount=[journal_entry[0], 'total_debit', 10, 'right', '0'],
		total_credit=[journal_entry[0], 'total_credit', 10, 'right', '0'],
		total_debit=[journal_entry[0], 'total_debit', 10, 'right', '0'],
		blank_2=['', '', 24],
		user_records=[no_of_records, '', 6],
		blank_3=['', '', 52]
	)
	return execute(trailer_row)

def get_detail_row(ref_doc, payroll_entry, trace_detail, bank_account):
	''' generates a file for eft transactions based on Kundu Pei system for processing payroll entry '''

	employee = frappe.get_doc('Employee', ref_doc.employee)
	account_detail = get_account_detail(employee, 'bank_ac_no')
	salary_slip = get_salary_slip(employee.name, payroll_entry.start_date, payroll_entry.end_date)

	detail_row = OrderedDict(
		record_type=['1', '', 1],
		bsb_number=[employee,'bsb_no', 7],
		vendor_account=[account_detail, '', 15],
		indicator=[' ', '', 1],
		transaction_code=['53', '', 2],
		amount=[salary_slip, 'net_pay', 10, 'right', '0'],
		payment_to=[employee, 'employee_name', 32, 'left', ' '],
		lodgment_reference=[payroll_entry, 'name', 18, 'left', ' '],
		trace_record=[trace_detail, '', 22],
		remitter_name=[bank_account, 'client_name', 16, 'left', ' '],
		withholding_tax=['', '', 8, 'right', '0']
	)

	return execute(detail_row)

def get_debitor_information(ref_doc, payroll_entry, trace_detail, bank_account):
	''' Returns creditor information '''
	account_detail = get_account_detail(bank_account, 'bank_account_no')
	journal_entry = get_journal_entry(payroll_entry.name)

	return execute(OrderedDict(
		record_type=['1', '', 1],
		bsb_number=[bank_account,'bsb_no', 7],
		vendor_account=[account_detail, '', 15],
		indicator=[' ', '', 1],
		transaction_code=['13', '', 2],
		amount=[journal_entry, 'total_debit', 10, 'right', '0'],
		payment_to=[bank_account, 'client_name', 32, 'left', ' '],
		lodgment_reference=[payroll_entry, 'name', 18, 'left', ' '],
		trace_record=[trace_detail, '', 22],
		remitter_name=[bank_account, 'client_name', 16, 'left', ' '],
		withholding_tax=['', '', 8, 'right', '0']
	))

def get_journal_entry(name):
	''' Return total credit and debit for given Journal Entry '''
	return frappe.db.sql('''
		SELECT
			je.`total_debit`,
			je.`total_credit`,
			jea.`parent` as name,
			jea.`parenttype` as doctype
		FROM `tabJournal Entry` je, `tabJournal Entry Account` jea
		WHERE
			je.name = jea.parent
			AND jea.reference_type='Payroll Entry'
			AND jea.reference_name=%s
	''', (name), as_dict=1)

def get_salary_slip(employee, start_date, end_date):
	return frappe.db.get_value('Salary Slip', filters={
		'employee': employee,
		'start_date': start_date,
		'end_date': end_date
		}, fieldname=['net_pay', 'name'], as_dict=1)

def get_account_detail(ref_doc, ref_fieldname):
	''' Creates a 15 digit combination of account type and bank account no '''
	return execute(OrderedDict(
		account_type = [ref_doc, 'account_type', 3, 'right', '0'],
		account_number = [ref_doc, ref_fieldname, 12, 'right', '0']
	))