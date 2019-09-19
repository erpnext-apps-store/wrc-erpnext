frappe.ui.form.on('Bank Account', {
    bsb_number: function(frm) {
        if (frm.doc.bsb_number) {
            frappe.call({
                method: "wrc_erpnext.wrc_erpnext.validations.bank_account.validate_bsb_number",
                args: {
                    bsb_number: frm.doc.bsb_number
                },
                callback: function(r) {
                    {
                        if(r && r.message) return;
                    }
                }
            });
        }
    }
});