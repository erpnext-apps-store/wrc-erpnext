// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Work Order", {
	production_item: function (frm) {
		if (frm.doc.production_item) {
			frappe.call({
				method: "wrc_erpnext.wrc_erpnext.validations.work_order.get_item_details",
				args: {
					item: frm.doc.production_item,
					project: frm.doc.project
				},
				freeze: true,
				callback: function (r) {
					frm.set_value('sales_order', "");
					frm.trigger('set_sales_order');
					erpnext.in_production_item_onchange = true;
					let fields = ["description", "stock_uom", "project", "bom_no", "allow_alternative_item",
						"transfer_material_against", "item_name"];

					$.each(fields, function (i, field) {
						frm.set_value(field, r.message[field]);
						frm.doc.bom_barcode = r.message["bom_barcode"];
					});
					if (r.message["set_scrap_wh_mandatory"]) {
						frm.toggle_reqd("scrap_warehouse", true);
					}
					erpnext.in_production_item_onchange = false;
				}
			});
		}
	},

	bom_barcode: function (frm) {
		frappe.call({
			method: "wrc_erpnext.wrc_erpnext.validations.work_order.get_bom_barcode_details",
			args: {
				barcode: frm.doc.bom_barcode,
				project: frm.doc.project
			},

			callback: function (r) {
				if (r.message !== "invalid") {
					frm.doc.production_item = r.message["item"];
					frm.set_value("item_name", r.message["item_name"]);
					frm.set_value("bom_no", r.message["bom_no"]);

					frm.set_value('sales_order', "");
					frm.trigger('set_sales_order');

					erpnext.in_production_item_onchange = true;
					let fields = ["description", "stock_uom", "project", "allow_alternative_item",
						"transfer_material_against", "item_name"];

					$.each(fields, function (i, field) {
						frm.set_value(field, r.message[field]);
					});

					if (r.message["set_scrap_wh_mandatory"]) {
						frm.toggle_reqd("scrap_warehouse", true);
					}
					frm.refresh();
				}
				else {
					frm.set_value("production_item", "");
					frm.set_value("bom_no", "");
					frm.set_value("quantity", "");
					frm.refresh();
				}
			}
		});
	},
});