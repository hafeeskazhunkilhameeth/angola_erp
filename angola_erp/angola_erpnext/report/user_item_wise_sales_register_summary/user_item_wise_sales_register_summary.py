# Copyright (c) 2013, Helio de Jesus and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, erpnext
from frappe import _
from frappe.utils import flt
from frappe.model.meta import get_field_precision
from frappe.utils.xlsxutils import handle_html
from erpnext.accounts.report.sales_register.sales_register import get_mode_of_payments

def execute(filters=None):
	return _execute(filters)

def _execute(filters=None, additional_table_columns=None, additional_query_columns=None):
	if not filters: filters = {}
	columns = get_columns(additional_table_columns)

	company_currency = erpnext.get_company_currency(filters.company)

	item_list = get_items(filters, additional_query_columns)
#	if item_list:
#		itemised_tax, tax_columns = get_tax_accounts(item_list, columns, company_currency)
#	columns.append({
#		"fieldname": "currency",
#		"label": _("Currency"),
#		"fieldtype": "Data",
#		"width": 80
#	})
	mode_of_payments = get_mode_of_payments(set([d.parent for d in item_list]))
	so_dn_map = get_delivery_notes_against_sales_order(item_list)

	data = []
	for d in item_list:
#		delivery_note = None
#		if d.delivery_note:
#			delivery_note = d.delivery_note
#		elif d.so_detail:
#			delivery_note = ", ".join(so_dn_map.get(d.so_detail, []))

#		if not delivery_note and d.update_stock:
#			delivery_note = d.parent

		row = [d.posting_date, d.cost_center, d.item_code, d.item_name, d.item_group]

		if additional_query_columns:
			for col in additional_query_columns:
				row.append(d.get(col))

		row += [
			d.stock_qty, d.base_net_amount
		]

#		row += [(d.base_net_rate * d.qty)/d.stock_qty, d.base_net_amount] \
#			if d.stock_uom != d.uom else [d.base_net_rate, d.base_net_amount]

#		total_tax = 0
#		for tax in tax_columns:
#			item_tax = itemised_tax.get(d.name, {}).get(tax, {})
#			row += [item_tax.get("tax_rate", 0), item_tax.get("tax_amount", 0)]
#			total_tax += flt(item_tax.get("tax_amount"))

#		row += [d.base_net_amount + total_tax, company_currency]

		data.append(row)

	return columns, data

def get_columns(additional_table_columns):
	columns = [
		_("Posting Date") + "::100", _("Cost Center") + "::120",
		_("Item Code") + ":Link/Item:120", _("Item Name") + "::120",
		_("Item Group") + ":Link/Item Group:120",
		_("Stock Qty") + ":Float:100",
		_("Amount") + ":Currency/currency:120" ]

	if additional_table_columns:
		columns += additional_table_columns

#	columns += [		
#		_("Amount") + ":Currency/currency:120"
#	]

	return columns

def get_conditions(filters):
	conditions = ""

	for opts in (("company", " and company=%(company)s"),
		("customer", " and `tabSales Invoice`.customer = %(customer)s"),
		("item_code", " and `tabSales Invoice Item`.item_code = %(item_code)s"),
		("from_date", " and `tabSales Invoice`.posting_date>=%(from_date)s"),
		("to_date", " and `tabSales Invoice`.posting_date<=%(to_date)s"),
		("owner", " and `tabSales Invoice`.owner = %(owner)s")):
			if filters.get(opts[0]):
				conditions += opts[1]

	if filters.get("mode_of_payment"):
		conditions += """ and exists(select name from `tabSales Invoice Payment`
			where parent=`tabSales Invoice`.name
				and ifnull(`tabSales Invoice Payment`.mode_of_payment, '') = %(mode_of_payment)s)"""

	return conditions

def get_items(filters, additional_query_columns):
	conditions = get_conditions(filters)
	match_conditions = frappe.build_match_conditions("Sales Invoice")
	
	if match_conditions:
		match_conditions = " and {0} ".format(match_conditions)
	
	if additional_query_columns:
		additional_query_columns = ', ' + ', '.join(additional_query_columns)

	return frappe.db.sql("""
		select
			`tabSales Invoice`.posting_date, `tabSales Invoice Item`.cost_center,
			`tabSales Invoice Item`.name, `tabSales Invoice Item`.parent,
			`tabSales Invoice`.posting_date, `tabSales Invoice Item`.item_code, `tabSales Invoice Item`.item_name,
			`tabSales Invoice Item`.item_group, sum(`tabSales Invoice Item`.stock_qty) as stock_qty, 
			`tabSales Invoice Item`.stock_uom, sum(`tabSales Invoice Item`.base_net_amount) as base_net_amount, 
			`tabSales Invoice Item`.base_net_rate, `tabSales Invoice Item`.uom
		from `tabSales Invoice`, `tabSales Invoice Item`
		where `tabSales Invoice`.name = `tabSales Invoice Item`.parent
			and `tabSales Invoice`.docstatus = 1 %s %s
		group by `tabSales Invoice Item`.cost_center, `tabSales Invoice Item`.item_code
		order by `tabSales Invoice`.posting_date desc, `tabSales Invoice Item`.cost_center desc,`tabSales Invoice Item`.item_code desc
		""".format(additional_query_columns or '') % (conditions, match_conditions), filters, as_dict=1)

def get_delivery_notes_against_sales_order(item_list):
	so_dn_map = frappe._dict()
	so_item_rows = list(set([d.so_detail for d in item_list]))

	if so_item_rows:
		delivery_notes = frappe.db.sql("""
			select parent, so_detail
			from `tabDelivery Note Item`
			where docstatus=1 and so_detail in (%s)
			group by so_detail, parent
		""" % (', '.join(['%s']*len(so_item_rows))), tuple(so_item_rows), as_dict=1)

		for dn in delivery_notes:
			so_dn_map.setdefault(dn.so_detail, []).append(dn.parent)

	return so_dn_map

