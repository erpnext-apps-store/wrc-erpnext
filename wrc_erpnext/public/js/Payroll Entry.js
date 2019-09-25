frappe.ui.form.on('Payroll Entry', {
	onload: function(frm) {
		if (frm.doc.docstatus!==1) return
		check_bank_entry(frm).then(check => {
			if (check) {
				frm.add_custom_button(__('Generate File'), function() {
					frm.trigger("generate_text_and_download_file");
				});
			}
		});
	},
	generate_text_and_download_file: (frm) => {
		return frappe.call({
			method: "wrc_erpnext.wrc_erpnext.payroll_payments.generate_report",
			args: {
				name: frm.doc.name
			},
			freeze: true,
			freeze_message: __('Generating File'),
			callback: function(r) {
				{
					frm.reload_doc();
					const a = document.createElement('a');
					let file_obj = r.message;
					a.href = file_obj.file_url;
					a.target = '_blank';
					a.download = file_obj.file_name;
					a.click();
				}
			}
		});
	},
});

let check_bank_entry = function(frm) {
	return frappe.xcall("wrc_erpnext.wrc_erpnext.payroll_payments.get_bank_entries", {
		name: frm.doc.name
	})
}