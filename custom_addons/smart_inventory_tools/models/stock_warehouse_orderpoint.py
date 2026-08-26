from odoo import api, fields, models
from odoo.tools import float_compare, float_is_zero


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    smart_monitor = fields.Boolean(
        string="Smart Monitor",
        default=True,
        help="Include this replenishment rule in the Smart Reordering checks.",
    )
    alert_severity_override = fields.Selection(
        selection=[
            ("warning", "Warning"),
            ("critical", "Critical"),
        ],
        string="Alert Severity Override",
        help="Force the alert severity when stock is below the minimum. "
             "Leave empty to compute severity automatically.",
    )
    stock_health = fields.Selection(
        selection=[
            ("ok", "OK"),
            ("warning", "Warning"),
            ("critical", "Critical"),
        ],
        string="Stock Health",
        compute="_compute_smart_reorder_metrics",
    )
    shortage_qty = fields.Float(
        string="Shortage Quantity",
        compute="_compute_smart_reorder_metrics",
        digits="Product Unit of Measure",
    )
    suggested_qty = fields.Float(
        string="Suggested Quantity",
        compute="_compute_smart_reorder_metrics",
        digits="Product Unit of Measure",
    )

    @api.depends(
        "qty_on_hand",
        "product_min_qty",
        "product_max_qty",
        "product_uom",
        "alert_severity_override",
        "smart_monitor",
    )
    def _compute_smart_reorder_metrics(self):
        for orderpoint in self:
            rounding = orderpoint.product_uom.rounding if orderpoint.product_uom else 0.01
            qty_on_hand = orderpoint.qty_on_hand or 0.0
            qty_min = orderpoint.product_min_qty or 0.0
            qty_max = orderpoint.product_max_qty or 0.0

            below_min = float_compare(qty_on_hand, qty_min, precision_rounding=rounding) < 0
            shortage = max(qty_min - qty_on_hand, 0.0) if below_min else 0.0
            suggested = 0.0
            if below_min:
                suggested = max(qty_max - qty_on_hand, 0.0)
                if float_is_zero(suggested, precision_rounding=rounding):
                    suggested = shortage

            health = "ok"
            if below_min:
                half_min = qty_min * 0.5
                if (
                    float_compare(qty_on_hand, 0.0, precision_rounding=rounding) <= 0
                    or float_compare(qty_on_hand, half_min, precision_rounding=rounding) < 0
                ):
                    health = "critical"
                else:
                    health = "warning"
                if orderpoint.alert_severity_override:
                    health = orderpoint.alert_severity_override

            orderpoint.shortage_qty = shortage
            orderpoint.suggested_qty = suggested
            orderpoint.stock_health = health
