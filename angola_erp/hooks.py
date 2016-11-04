# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "angola_erp"
app_title = "Angola ERPNext"
app_publisher = "Helio de Jesus"
app_description = "Angola ERPNEXT extensao"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "hcesar@gmail.com"
app_license = "MIT"
fixtures = ["Custom Field","Custom Script","IRT","INSS"]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/angola_erp/css/angola_erp.css"
# app_include_js = "/assets/angola_erp/js/angola_erp.js"

# include js, css files in header of web template
# web_include_css = "/assets/angola_erp/css/angola_erp.css"
# web_include_js = "/assets/angola_erp/js/angola_erp.js"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "angola_erp.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "angola_erp.install.before_install"
# after_install = "angola_erp.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "angola_erp.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}

	"Salary Component":{
		"validate": "angola_erp.angola_erpnext.validations.salary_component.validate",
	},
	"Employee": {
		"validate": "angola_erp.angola_erpnext.validations.employee.validate",

	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"angola_erp.tasks.all"
# 	],
# 	"daily": [
# 		"angola_erp.tasks.daily"
# 	],
# 	"hourly": [
# 		"angola_erp.tasks.hourly"
# 	],
# 	"weekly": [
# 		"angola_erp.tasks.weekly"
# 	]
# 	"monthly": [
# 		"angola_erp.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "angola_erp.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "angola_erp.event.get_events"
# }

