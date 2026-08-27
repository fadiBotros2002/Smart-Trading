from odoo import api, fields, models


class SmartStockAlert(models.Model):
    _name = "smart.stock.alert"
    _description = "Smart Stock Alert"
    _order = "detected_at desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True, 
        copy=False, 
        default="New"
        )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
        ondelete="cascade",
        index=True,
        domain="[('is_storable', '=', True)]",
    )
    orderpoint_id = fields.Many2one(
        "stock.warehouse.orderpoint",
        string="Reordering Rule",
        required=True,
        ondelete="cascade",
        index=True,
    )
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Warehouse",
        related="orderpoint_id.warehouse_id",
        store=True,
        readonly=True,
    )
    location_id = fields.Many2one(
        "stock.location",
        string="Location",
        related="orderpoint_id.location_id",
        store=True,
        readonly=True,
    )
    qty_on_hand = fields.Float(
        string="On Hand",
        digits="Product Unit of Measure",
        required=True,
    )
    qty_min = fields.Float(
        string="Minimum Quantity",
        digits="Product Unit of Measure",
        required=True,
    )
    qty_max = fields.Float(
        string="Maximum Quantity",
        digits="Product Unit of Measure",
        required=True,
    )
    shortage_qty = fields.Float(
        string="Shortage Quantity",
        digits="Product Unit of Measure",
        required=True,
    )
    suggested_qty = fields.Float(
        string="Suggested Quantity",
        digits="Product Unit of Measure",
        required=True,
    )
    severity = fields.Selection(
        selection=[
            ("warning", "Warning"),
            ("critical", "Critical"),
        ],
        string="Severity",
        required=True,
        default="warning",
        index=True,
    )
    state = fields.Selection(
        selection=[
            ("open", "Open"),
            ("acknowledged", "Acknowledged"),
            ("replenishment_created", "Replenishment Created"),
            ("resolved", "Resolved"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        required=True,
        default="open",
        index=True,
        copy=False,
    )
    vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        domain="[('supplier_rank', '>', 0)]",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible",
        default=lambda self: self.env.user,
    )
    detected_at = fields.Datetime(
        string="Detected On",
        required=True,
        default=fields.Datetime.now,
        index=True,
    )

    @api.onchange("orderpoint_id")
    def _onchange_orderpoint_id(self):
        if not self.orderpoint_id:
            return
        orderpoint = self.orderpoint_id
        self.product_id = orderpoint.product_id
        self.qty_on_hand = orderpoint.qty_on_hand
        self.qty_min = orderpoint.product_min_qty
        self.qty_max = orderpoint.product_max_qty
        self.shortage_qty = orderpoint.shortage_qty
        self.suggested_qty = orderpoint.suggested_qty
        if orderpoint.stock_health in ("warning", "critical"):
            self.severity = orderpoint.stock_health
        sellers = orderpoint.product_id.seller_ids.filtered(
            lambda seller: seller.partner_id
        )
        if sellers:
            self.vendor_id = sellers[0].partner_id
