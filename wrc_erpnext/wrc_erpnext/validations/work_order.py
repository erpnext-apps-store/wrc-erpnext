# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate
from erpnext.manufacturing.doctype.work_order.work_order import check_if_scrap_warehouse_mandatory

@frappe.whitelist()
def get_bom_barcode_details(barcode, project=None):
	bom = frappe.db.get_value("BOM Barcode", {"barcode": barcode}, "parent")

	if not bom:
		frappe.msgprint(
			_("Invalid Barcode. There is no BOM attached to this barcode."))
		return "invalid"

	else:
		item = frappe.db.get_value("BOM", bom, "item")
		res = set_bom_details(item)

		if project:
			if not frappe.db.exists("BOM", {"name": bom, "project": project}):
				res = get_bom_barcode_details(barcode)
				frappe.msgprint(_("Default BOM not found for Item {0} and Project {1}").format(
					item, project), alert=1)

		bom_data = frappe.db.get_value('BOM', bom,
                                 ['project', 'allow_alternative_item', 'transfer_material_against', 'item_name'], as_dict=1)
		res['project'] = project or bom_data.pop("project")
		res.update(bom_data)
		res['item'] = item
		res['bom_no'] = bom
		res.update(check_if_scrap_warehouse_mandatory(res["bom_no"]))
		return res

@frappe.whitelist()
def get_item_details(item, project=None):
	res = set_bom_details(item)

	filters = {"item": item, "is_default": 1}

	if project:
		filters = {"item": item, "project": project}

	res["bom_no"] = frappe.db.get_value("BOM", filters=filters)

	if not res["bom_no"]:
		variant_of = frappe.db.get_value("Item", item, "variant_of")

		if variant_of:
			res["bom_no"] = frappe.db.get_value(
				"BOM", filters={"item": variant_of, "is_default": 1})

	if not res["bom_no"]:
		if project:
			res = wrc_erpnext.get_item_details(item)
			frappe.msgprint(_("Default BOM not found for Item {0} and Project {1}").format(
				item, project), alert=1)
		else:
			frappe.throw(_("Default BOM for {0} not found").format(item))

	bom_data = frappe.db.get_value('BOM', res['bom_no'],
								['project', 'allow_alternative_item', 'transfer_material_against', 'item_name'], as_dict=1)

	barcode = frappe.db.get_value(
		"BOM Barcode", {"parent": res['bom_no']}, "barcode")
	res['project'] = project or bom_data.pop("project")
	res['bom_barcode'] = barcode
	res.update(bom_data)
	res.update(check_if_scrap_warehouse_mandatory(res["bom_no"]))

	return res

def set_bom_details(item):
	res = frappe.db.sql("""
		select stock_uom, description
		from `tabItem`
		where disabled=0
			and (end_of_life is null or end_of_life='0000-00-00' or end_of_life > %s)
			and name=%s
	""", (nowdate(), item), as_dict=1)

	if not res:
		return {}
	res = res[0]
	return res