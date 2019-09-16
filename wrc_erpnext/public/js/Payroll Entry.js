frappe.ui.form.on('Payroll Entry', {
	refresh: function(frm) {
		if (frm.doc.docstatus==1 && (frm.doc.salary_slips_submitted
			|| (frm.doc.__onload && frm.doc.__onload.submitted_ss))) {
			frm.add_custom_button(__('Generate File'), function() {
				frm.trigger("generate_text_and_download_file");
			});
		}
	},
	generate_text_and_download_file: (frm) => {
		return frappe.call({
			method: "wrc_erpnext.wrc_erpnext.payments_integration.generate_report",
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
	}
});