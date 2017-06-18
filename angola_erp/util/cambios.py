# Copyright (c) 2016, Helio de Jesus and contributors
# For license information, please see license.txt

# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import frappe
from frappe import utils 
import datetime
from datetime import timedelta
from frappe.utils import get_datetime_str, formatdate, nowdate, getdate, cint
from frappe.model.naming import make_autoname
import frappe.async
from frappe.utils import cstr
from frappe import _

from frappe.model.document import Document

from lxml import html
import requests


@frappe.whitelist()
def cambios(fonte):

	if not fonte:
		frappe.throw("A fonte tem que ser BNA ou BFA.")


	if fonte.upper() == 'BNA':
		try:
			page=requests.get('http://www.bna.ao/Servicos/cambios_table.aspx?idl=1')
		except Exception, e:
			if frappe.message_log: frappe.message_log.pop()
			return 0,0

		#print page
		if page.status_code == 200:
			tree = html.fromstring(page.content)

			i = 2
			for tr in tree.xpath("//tr"):
				#print tree.xpath('//tr['+ str(i) + ']') == []

				if tree.xpath('//tr['+ str(i) + ']') != []:
					print "meoda ", tr.xpath('//tr['+ str(i) +']/td[1]/text()')[0]
					#print tr.xpath(tr.xpath('//tr['+ str(i) +']/td[1]/text()')[0].strip()) == '  USD'
					if tr.xpath('//tr['+ str(i) +']/td[1]/text()')[0] == 'USD': 
						moeda= tr.xpath('//tr['+ str(i) +']/td[1]/text()')[0]     #moeda USD
						moedacompra= tr.xpath('//tr['+ str(i) +']/td[2]/text()')[0]	#Compra
						moedavenda= tr.xpath('//tr['+ str(i) +']/td[3]/text()')[0]    #Venda
					i += 1

			print moeda
			print moedacompra
			print moedavenda
			
			return moedacompra, moedavenda
	

	if fonte.upper() == 'BFA':
		try:
			page= requests.get('http://www.bfa.ao/Servicos/Cambios/Divisas.aspx?idl=1')
		except Exception, e:
			if frappe.message_log: frappe.message_log.pop()
			return 0,0

		if page.status_code == 200:

			tree = html.fromstring(page.content)
			i = 2 
			for tr in tree.xpath("//tr"):	

				if tr.xpath('//*[@id="usd"]/text()')[0].strip()=='USD': 
					moeda= tr.xpath('//*[@id="usd"]/text()')[0].strip()     #moeda USD
					moedacompra= tr.xpath('//tr[4]/td[1]/text()')[0].strip()	#Compra
					moedavenda= tr.xpath('//tr[4]/td[2]/text()')[0].strip()    #Venda

			print moeda
			print moedacompra
			print moedavenda

			return moedacompra, moedavenda




@frappe.whitelist()
def update_cambios(fonte):

	#Get the list of rates from BNA / BFA
	#Get list of Currency; if listed updates the rate
	
	# select name,from_currency,to_currency,max(date),exchange_rate from `tabCurrency Exchange` where from_currency='usd' and to_currency='kz';
		
	print "adfadsfasfdsadfadfadfadfadf"
	print "adfadsfasfdsadfadfadfadfadf"
	print "adfadsfasfdsadfadfadfadfadf"
	print "adfadsfasfdsadfadfadfadfadf"
	print "adfadsfasfdsadfadfadfadfadf"
	print "adfadsfasfdsadfadfadfadfadf"

	if not fonte:
		frappe.throw("A fonte tem que ser BNA ou BFA.")

	if fonte.upper() == 'BNA':
		try:
			page=requests.get('http://www.bna.ao/Servicos/cambios_table.aspx?idl=1')
		except Exception, e:
			if frappe.message_log: frappe.message_log.pop()
			return 0,0

	if fonte.upper() == 'BFA':
		try:
			page= requests.get('http://www.bfa.ao/Servicos/Cambios/Divisas.aspx?idl=1')
		except Exception, e:
			if frappe.message_log: frappe.message_log.pop()
			return 0,0

		#print page
	if page.status_code == 200:
		tree = html.fromstring(page.content)

		i = 2
		#BNA
		if fonte.upper() == 'BNA':
			for tr in tree.xpath("//tr"):
				#print tree.xpath('//tr['+ str(i) + ']') == []

				if tree.xpath('//tr['+ str(i) + ']') != []:
					print "meoda BNA ", tr.xpath('//tr['+ str(i) +']/td[1]/text()')[0]
					#print tr.xpath(tr.xpath('//tr['+ str(i) +']/td[1]/text()')[0].strip()) == '  USD'

					moeda= tr.xpath('//tr['+ str(i) +']/td[1]/text()')[0]     #moeda 
					moedacompra= tr.xpath('//tr['+ str(i) +']/td[2]/text()')[0]	#Compra
					moedavenda= tr.xpath('//tr['+ str(i) +']/td[3]/text()')[0]    #Venda

					cambios_ = frappe.db.sql(""" select name,from_currency,to_currency,max(date),exchange_rate from `tabCurrency Exchange` where to_currency='kz' and from_currency=%s ;""",(moeda),as_dict=True)

					print "moeda ", moeda
					print cambios_[0]['max(date)']
					print formatdate(get_datetime_str(frappe.utils.nowdate()),"YYY-MM-dd")
					print formatdate(cambios_[0]['max(date)'],"YYYY-MM-dd") == formatdate(get_datetime_str(frappe.utils.nowdate()),"YYY-MM-dd")
					if (cambios_[0].to_currency != None):
#						print "NAO Tem cambios "

#					if (len(cambios_) >0):
						if formatdate(cambios_[0]['max(date)'],"YYYY-MM-dd") == formatdate(get_datetime_str(frappe.utils.nowdate()),"YYY-MM-dd"):
						#if (cambios_[-0].date == frappe.utils.nowdate()):
							print "Ja foi atualizado hoje ...."
						else:
							print "Tem cambios ", cambios_
							#Just add or should check if value changed...!!!

							for reg in cambios_:
								print " cambio ", reg.exchange_rate
								if (reg.exchange_rate <> moedavenda):	
									print "Cambios diferentes...."
									#add new record
									cambios_novo = frappe.get_doc({
										"doctype": "Currency Exchange",
										"from_currency": str(moeda),
										"to_currency": "KZ",
										"exchange_rate": moedavenda,
										"date": frappe.utils.nowdate()
#										"name":'{0}-{1}-{2}'.format(formatdate(get_datetime_str(frappe.utils.nowdate()), "yyyy-MM-dd"),"USD", "KZ")


									})

									cambios_novo.insert()

					

					if tr.xpath('//tr['+ str(i) +']/td[1]/text()')[0] == 'USD': 
						moeda= tr.xpath('//tr['+ str(i) +']/td[1]/text()')[0]     #moeda USD
						moedacompra= tr.xpath('//tr['+ str(i) +']/td[2]/text()')[0]	#Compra
						moedavenda= tr.xpath('//tr['+ str(i) +']/td[3]/text()')[0]    #Venda
					i += 1

			print moeda
			print moedacompra
			print moedavenda
			
	#			return moedacompra, moedavenda
	

		if fonte.upper() == 'BFA':

			for tr in tree.xpath("//tr"):	

				if tr.xpath('//*[@id="usd"]/text()')[0].strip()=='USD': 
					moeda= tr.xpath('//*[@id="usd"]/text()')[0].strip()     #moeda USD
					moedacompra= tr.xpath('//tr[4]/td[1]/text()')[0].strip()	#Compra
					moedavenda= tr.xpath('//tr[4]/td[2]/text()')[0].strip()    #Venda

			print moeda
			print moedacompra
			print moedavenda

#			return moedacompra, moedavenda


