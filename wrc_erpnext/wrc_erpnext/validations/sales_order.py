# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import json
import frappe.utils
from frappe.utils import flt
from frappe import _

def validate(doc,method):
	get_work_order_items(doc)
	
def get_work_order_items(doc, for_raw_material_request=0):
	'''Returns items with BOM that already do not have a linked work order'''
	items = []
	for table in [doc.items, doc.packed_items]:
		for i in table:
			bom = get_default_bom_item(i.item_code)
			stock_qty = i.qty if i.doctype == 'Packed Item' else i.stock_qty
			if not for_raw_material_request:
				total_work_order_qty = flt(frappe.db.sql('''select sum(qty) from `tabWork Order`
					where production_item=%s and sales_order=%s and sales_order_item = %s and docstatus<2''',
															(i.item_code, doc.name, i.name))[0][0])
				pending_qty = stock_qty - total_work_order_qty
			else:
				pending_qty = stock_qty

			if pending_qty:
				if bom:
					barcode = frappe.db.get_value(
						"BOM Barcode", {'parent': bom}, "barcode")
					items.append(dict(
						name=i.name,
						item_code=i.item_code,
						description=i.description,
						bom=bom,
						bom_barcode=barcode,
						warehouse=i.warehouse,
						pending_qty=pending_qty,
						required_qty=pending_qty if for_raw_material_request else 0,
						sales_order_item=i.name
					))
				else:
					items.append(dict(
						name=i.name,
						item_code=i.item_code,
						description=i.description,
						bom='',
						warehouse=i.warehouse,
						pending_qty=pending_qty,
						required_qty=pending_qty if for_raw_material_request else 0,
						sales_order_item=i.name
					))
	return items

@frappe.whitelist()
def make_work_orders(items, sales_order, company, project=None):
	'''Make Work Orders against the given Sales Order for the given `items`'''
	items = json.loads(items).get('items')
	out = []

	for i in items:
		if not i.get("bom"):
			frappe.throw(
				_("Please select BOM against item {0}").format(i.get("item_code")))
		if not i.get("pending_qty"):
			frappe.throw(
				_("Please select Qty against item {0}").format(i.get("item_code")))

		work_order = frappe.get_doc(dict(
			doctype='Work Order',
			production_item=i['item_code'],
			bom_barcode=i.get('bom_barcode'),
			bom_no=i.get('bom'),
			qty=i['pending_qty'],
			company=company,
			sales_order=sales_order,
			sales_order_item=i['sales_order_item'],
			project=project,
			fg_warehouse=i['warehouse'],
			description=i['description']
		)).insert()
		work_order.set_work_order_operations()
		work_order.save()
		out.append(work_order)

	return [p.name for p in out]