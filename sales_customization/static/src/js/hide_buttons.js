odoo.define('sales_customization.hide_buttons', function (require) {
    "use strict";
    
    var FormController = require('web.FormController');

    FormController.include({
        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                // Hide buttons immediately when form loads
                self._hidePromoButtons();
                return Promise.resolve();
            });
        },
        
        _hidePromoButtons: function () {
            var buttons = this.$el.find(
                '[name="action_open_coupon_wizard"], ' +
                '[name="578"], ' +
                '[data-action="578"], ' +
                '.btn-promotion, ' +
                '.btn-coupon'
            );
            buttons.hide();
        },
        
        renderButtons: function ($node) {
            var res = this._super.apply(this, arguments);
            this._hidePromoButtons();
            return res;
        }
    });
});