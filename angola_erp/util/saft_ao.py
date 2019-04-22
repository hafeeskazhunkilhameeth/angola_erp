# -*- coding: utf-8 -*-
# Copyright (c) 2016, Helio de Jesus and contributors
# For license information, please see license.txt

#Date Changed: 18/04/2019
#Version: 1.0.4

from __future__ import unicode_literals

#from __future__ import unicode_literals
import sys
reload (sys)
sys.setdefaultencoding('utf-8')


from frappe.model.document import Document
import frappe.model
import frappe
from frappe.utils import nowdate, cstr, flt, cint, now, getdate
from frappe import throw, _
from frappe.utils import formatdate, encode
from frappe.model.naming import make_autoname
from frappe.model.mapper import get_mapped_doc

from frappe.email.doctype.email_group.email_group import add_subscribers

from frappe.contacts.doctype.address.address import get_company_address # for make_facturas_venda
from frappe.model.utils import get_fetch_values

import os 

import csv 
import json

import xml.etree.ElementTree as ET
from xml.dom import minidom 
from datetime import datetime, date, timedelta

import angola
import re


@frappe.whitelist()
def get_xml(args):
	from werkzeug.wrappers import Response
	response = Response()
	response.mimetype = 'text/xml'
	response.charset = 'utf-8'
	response.data = '<xml></xml>'

	print 'AAAAA'

	print response	

	return response

@frappe.whitelist()
def update_acc_codes():
	#Update account_number with the number of name
	accs = frappe.db.sql(""" select name,account_number from `tabAccount` """,as_dict=True)
	for acc in accs:
		if acc.name[0:1].isnumeric() == True:
			#starts with Numbers
			conta = acc.name[0:acc.name.find("-")-1]
			#print acc.name[0:acc.name.find("-")-1]
			#acc.account_number = conta
			frappe.db.set_value('Account',acc.name,'account_number',conta)
			frappe.db.commit()
	

@frappe.whitelist()
def gerar_saft_ao(company = None, processar = "Mensal", datainicio = None, datafim = None, update_acc_codes = False):
	Versao = "1.0.10" 


	######## Inside MasterFiles
		###GeneralLedgerAccounts
			###Accounts
		###Customer
		###Supplier
		###Product
		###TaxTable
	######## END MasterFiles	

	######## Inside GeneralLedgerEntries
		###Journal

	######## END GeneralLedgerEntries

	######## Inside SourceDocuments
		###SalesInvoice
		###MovementOfGoods
		###WorkingDocuments
		###Payments


	######## END SourceDocuments

	'''
	Documentos Gerais devem ter Header, Customer, TaxTable, Payments

	Documentos Accounting/Contabilidade: GeneralLedgerAccounts, Supppier, GeneralLedgerEntries
	
	Documentos Invoices: Supplier, Products, SalesInvoice, WorkingDocuments, Payments 																																																																																																																																
	'''

	'''
	Para gerar:	openssl genrsa -out ChavePrivada.pem 1024
	Para gerar:	openssl rsa -in ChavePrivada.pem -out ChavePublica.pem -outform PEM –pubout



	'''
	
	#read from source ...
	print company == None
	print processar
	print datainicio
	print datafim
	print update_acc_codes

	if company == None or company =="None":
		empresa = frappe.get_doc('Company', '2MS - Comercio e Representacoes, Lda')	#Should get as arg or based on default...
		#('Company','Farmacia Xixa') #
		#('Company', '2MS - Comercio e Representacoes, Lda')	#Should get as arg or based on default...
		#('Company','Fazenda-Aurora') #
	else:
		empresa = frappe.get_doc('Company', company)	#Should get as arg or based on default...
		#nome do file sera a (Empresa + "_" + SAFT_AO + "_" + NIF + data today)
		nomeficheiro = re.sub(r",|-|\s+","",empresa.name) + "_SAFT_AO_" + empresa.tax_id + "_" + datetime.today().strftime("%Y%m%d%H%M%S")
		#re.sub(r",|-|\s+","",s)

		agtvalidationnumber = "111111111"	#AGT Validation Number
		print 'nome file ', nomeficheiro
		print 'agt validar ', agtvalidationnumber



	emp_enderecos = angola.get_all_enderecos("Company",empresa.name)
	print 'ENdereco Empresa'
	print emp_enderecos

	#Updates Accounting number on TabAccount
	if update_acc_codes == True:
		#updates 
		update_acc_codes()

	'''
	DEFAULT processar = Mensal
	Processar pode ser Mensal, Semanal ou Diario
	'''

	print 'mes inicial ', angola.get_first_day(datetime.today())
	print 'mes fim ', angola.get_last_day(datetime.today())


	if datainicio == None:
		primeirodiames = angola.get_first_day(datetime.today())
		ultimodiames = angola.get_last_day(datetime.today())

		primeirodiames = datetime.strptime('2019-01-01',"%Y-%m-%d")
		ultimodiames = datetime.strptime('2019-04-30',"%Y-%m-%d")

		AnoFiscal = frappe.db.sql(""" select year, year_start_date, year_end_date, disabled from `tabFiscal Year` where year = %s """,(datetime.today().year)
,as_dict=True)

	else:
		print 'User type'
		print type(datainicio)
		print str(datetime.strptime(datainicio,"%Y-%m-%d").year)	
		print datafim
		#datainicio = datetime.strptime(datainicio,"%Y-%m-%d").year
		primeirodiames = angola.get_first_day(datetime.strptime(datainicio,"%Y-%m-%d")) #datetime.datetime.strptime(datainicio,("%Y-%m-%d"))
		ultimodiames = angola.get_last_day(datetime.strptime(datafim,"%Y-%m-%d")) #datetime.datetime.strptime(datafim,("%Y-%m-%d"))

		print 'Processar ', processar
		#case Semanal changes datafim
		#case Diario changes datafim to datainicio
		if processar.upper() == 'SEMANAL':
			primeirodiames, ultimodiames = angola.get_firstlast_week_day(datetime.strptime(datainicio,"%Y-%m-%d"))
			print angola.get_firstlast_week_day(datetime.strptime(datainicio,"%Y-%m-%d"))
			print primeirodiames.strftime("%Y-%m-%d")
			print ultimodiames.strftime("%Y-%m-%d")

		if processar.upper() == 'DIARIO':
			ultimodiames = primeirodiames
			print primeirodiames.strftime("%Y-%m-%d")
			print ultimodiames.strftime("%Y-%m-%d")



		AnoFiscal = frappe.db.sql(""" select year, year_start_date, year_end_date, disabled from `tabFiscal Year` where year = %s """,(str(datetime.strptime(datainicio,"%Y-%m-%d").year)),as_dict=True)

	print 'AnoFiscal'
	print AnoFiscal 
	print datetime.today().year


	#### Create Header

	data = ET.Element('AuditFile')
	print 'creating Header'
	head = ET.SubElement(data,'Header')

	auditfileversion = ET.SubElement(head,'AuditFileVersion')
	auditfileversion.text = str(Versao)

	companyid = ET.SubElement(head,'CompanyID')	
	companyid.text = empresa.name

	taxregistrationnumber = ET.SubElement(head,'TaxRegistrationNumber')
	taxregistrationnumber.text = empresa.tax_id

	taxaccountingbasis = ET.SubElement(head,'TaxAccountingBasis')
	taxaccountingbasis.text = "I"	#I contab. integrada c/Factur, C - Contab, F - Fact, Q - bens, services, Fact.

	companyname = ET.SubElement(head,'CompanyName')
	companyname.text = str(empresa.name)

	businessname = ET.SubElement(head,'BusinessName')
	businessname.text = empresa.name

	#START CompanyAddress
	companyaddress = ET.SubElement(head,'CompanyAddress')
	buildingnumber = ET.SubElement(companyaddress,'BuildingNumber')

	streetname = ET.SubElement(companyaddress,'StreetName')
	streetname.text = emp_enderecos.address_line1

	addressdetail = ET.SubElement(companyaddress,'AddressDetail')
	addressdetail.text = emp_enderecos.address_line1

	city = ET.SubElement(companyaddress,'City')
	city.text = emp_enderecos.city
	
	postalcode = ET.SubElement(companyaddress,'PostalCode')
	postalcode.text = emp_enderecos.pincode

	province = ET.SubElement(companyaddress,'Province')
	province.text = emp_enderecos.city

	country = ET.SubElement(companyaddress,'Country')
	country.text = "AO"	#default

	#END CompanyAddress
	fiscalyear = ET.SubElement(head,'FiscalYear')
	fiscalyear.text = AnoFiscal[0].year

	print 'Ano Inicio'
	print AnoFiscal[0].year_start_date

	startdate = ET.SubElement(head,'SartDate')	#iniciomes
	startdate.text = primeirodiames.strftime("%Y-%m-%d") #AnoFiscal[0].year_start_date.strftime("%Y-%m-%d")

	enddate = ET.SubElement(head,'EndDate')		#fimmes
	enddate.text = ultimodiames.strftime("%Y-%m-%d") #AnoFiscal[0].year_end_date.strftime("%Y-%m-%d")

	currencycode = ET.SubElement(head,'CurrencyCode')
	currencycode.text = "AOA"	#default

	datecreated = ET.SubElement(head,'DateCreated')
	datecreated.text = frappe.utils.nowdate()	#XML created

	taxentity = ET.SubElement(head,'TaxEntity')
	taxentity.text = "Global"	#default

	productcompanytaxid = ET.SubElement(head,'ProductCompanyTaxID')
	productcompanytaxid.text = "5417537802"	#TeorLogico

	
	softwarevalidationnumber = ET.SubElement(head,'SoftwareValidationNumber')
	softwarevalidationnumber.text = agtvalidationnumber	#AGT number

	productid = ET.SubElement(head,'ProductID')
	productid.text = "AngolaERP / TeorLogico"	#TeorLogico

	productversion = ET.SubElement(head,'ProductVersion')
	productversion.text = str(angola.get_versao_erp())


	headercomment = ET.SubElement(head,'HeaderComment')
	headercomment.text = "Ficheiro Financeiro."	

	telephone = ET.SubElement(head,'Telephone')
	telephone.text = emp_enderecos.phone

	fax = ET.SubElement(head,'Fax')
	productid.text = emp_enderecos.fax

	email = ET.SubElement(head,'Email')
	productid.text = emp_enderecos.email_id

	website = ET.SubElement(head,'Website')
	productid.text = empresa.website


	# END OF HEADER

	####MASTER Files
	masterfiles = ET.SubElement(data,'MasterFiles')


	##### Create GeneralLedgerAccounts
	#GeneralLedgerAccounts
	#masterfiles = ET.Element('MasterFiles')

	generalledgeraccounts = ET.SubElement(masterfiles,'GeneralLedgerAccounts')
	planocontas = frappe.db.sql(""" select * from `tabAccount` where docstatus = 0 and company = %s order by name, lft """,(empresa.name), as_dict=True)


	for planoconta in planocontas:
		account = ET.SubElement(generalledgeraccounts,'Account')
		accountid = ET.SubElement(account,'AccountID')
		accountid.text = str(planoconta.name)			#Due to 30 chars limit we have to add 
		#accountid.text = str(planoconta.account_number)	#Make sure update_acc_codes was run before...

		accountdescription = ET.SubElement(account,'AccountDescription')		
		accountdescription.text = str(planoconta.account_name)

		openingdeditbalance = ET.SubElement(account,'OpeningDebitBalance')
		openingcrebitbalance = ET.SubElement(account,'OpeningCreditBalance')
		closingdebitbalance = ET.SubElement(account,'ClosingDebitBalance')
		closingcreditbalance = ET.SubElement(account,'ClosingCreditBalance')

		aberturadebitoanoprev = 0 
		aberturacreditoanoprev = 0

		#GL Entry from previous year
		glentry = frappe.db.sql(""" select sum(debit), sum(credit), sum(debit-credit) from `tabGL Entry` where company = %s and fiscal_year = %s and account = %s """,(empresa.name,int(AnoFiscal[0].year)-1,planoconta.name), as_dict=True)


		if glentry:	#for Previous YEAR
			if flt(glentry[0]['sum(debit)']) != 0:
				aberturadebitoanoprev = glentry[0]['sum(debit)']
				openingdeditbalance.text = str(glentry[0]['sum(debit)']) 
			if flt(glentry[0]['sum(credit)']) != 0:
				aberturacreditoanoprev = glentry[0]['sum(credit)']
				openingcrebitbalance.text = str(glentry[0]['sum(credit)']) 	
		

		glentry = frappe.db.sql(""" select sum(debit), sum(credit), sum(debit-credit) from `tabGL Entry` where company = %s and fiscal_year = %s and account = %s """,(empresa.name,int(AnoFiscal[0].year),planoconta.name), as_dict=True)

		if glentry:	#Current YEAR
			print flt(glentry[0]['sum(debit)'])
			print flt(aberturadebitoanoprev)

			print 'adasdfasfsafasfda'
			print flt(glentry[0]['sum(debit-credit)'])

			print 'close db'
			print flt(glentry[0]['sum(debit)']) + flt(aberturadebitoanoprev)
			print (flt(glentry[0]['sum(debit)']) + flt(aberturadebitoanoprev)) - flt(glentry[0]['sum(credit)']) 			


			print 'ZERO ', flt(glentry[0]['sum(debit)']) == 0

			fechodebitoano = 0
			fechocreditoano = 0

			if flt(glentry[0]['sum(debit)']) != 0:

				fechodebitoano = (flt(glentry[0]['sum(debit)']) + flt(aberturadebitoanoprev)) - flt(glentry[0]['sum(credit)'])
				closingdebitbalance.text = str(fechodebitoano)
			if flt(glentry[0]['sum(credit)']) != 0:
				if fechodebitoano == 0:
					fechocreditoano = (flt(glentry[0]['sum(credit)']) + flt(aberturacreditoanoprev)) - flt(glentry[0]['sum(debit)'])
					closingcreditbalance.text = str(fechocreditoano)

#			if "2630" in planoconta.name: break

		groupingcategory = ET.SubElement(account,'GroupingCategory')
		if planoconta.is_group:	#fica GR
			groupingcategory.text = "GR"	#Ainda por verificar com os Contabilistas
		elif not planoconta.is_group:
			groupingcategory.text = "GA"	#Ainda por verificar com os Contabilistas

		groupingcode = ET.SubElement(account,'GroupingCode')
		if planoconta.parent_account:
			groupingcode.text = str(planoconta.parent_account)

	#Customers
	customers = ET.SubElement(masterfiles,'Customers')

	#masterfiles = ET.Element('MasterFiles')

	#create Customer
	clientes = frappe.db.sql(""" select * from `tabCustomer` where docstatus = 0 """,as_dict=True)

	adicionacliente = True

	#Faz loop
	for cliente in clientes:
		contascliente = frappe.db.sql(""" select * from `tabParty Account` where parenttype = 'Customer' and parentfield = 'accounts' and parent = %s and company = %s """,(cliente.name, empresa.name), as_dict=True)
		print 'account cliente'
		print cliente.name
		print contascliente

		if not contascliente:
			#test to see if exists ... but on diff company

			contascliente = frappe.db.sql(""" select * from `tabParty Account` where parenttype = 'Customer' and parentfield = 'accounts' and parent = %s """,(cliente.name), as_dict=True)
			print 'outra empresa'
			print contascliente
			if contascliente:
				#Outra empresa..
				adicionacliente = False
			else:
				adicionacliente = True
		
		
		if adicionacliente == True:
			print 'Add cliente'
			print 'Add cliente'
			print 'Add cliente'
			#Customers
			#customers = ET.SubElement(masterfiles,'Customers')
			customer = ET.SubElement(customers,'Customer')
			customerid = ET.SubElement(customer,'CustomerID')
			customerid.text = cliente.name

			accountid = ET.SubElement(customer,'AccountID')



			if not contascliente:
					contascliente = frappe.db.sql(""" select * from `tabAccount` where name like '31121000%%' and company = %s """,(empresa.name), as_dict=True)
					print contascliente
					accountid.text = contascliente[0].account_name
					#accountid.text = contascliente[0].account_number
#				else:
#					accountid.text = "Desconhecido"				
			else:

				accountid.text = contascliente[0].account
				#In case we need to get account_number instead
				#contascliente = frappe.db.sql(""" select * from `tabAccount` where name = %s and company = %s """,(contascliente[0].account,empresa.name), as_dict=True)
				#accountid.text = contascliente[0].account_number


			customertaxid = ET.SubElement(customer,'CustomerTaxID')
			if (cliente.tax_id != None and (cliente.tax != "N/A" or cliente.tax != "N-A")) :
				customertaxid.text = cliente.tax_id
			else:
				customertaxid.text = "999999990"

			companyname = ET.SubElement(customer,'CompanyName')
			if cliente.customer_name == 'Diversos' or cliente.customer_name == 'General':
				companyname.text = "Consumidor final"
			else:	
				companyname.text = cliente.customer_name

			contact = ET.SubElement(customer,'Contact')
			if cliente.customer_primary_contact:
				contact.text = cliente.customer_primary_contact

			#START BILLING address
			#address = ET.SubElement(customer,'Address')

			billingaddress = ET.SubElement(customer,'BillingAddress')
			cliente_endereco = angola.get_all_enderecos_a("Customer",cliente.name)
			#if cliente_endereco:
			#	print cliente_endereco.address_line1
			#	billingaddress.text = cliente_endereco.address_line1

			buildingnumber = ET.SubElement(billingaddress,'BuildingNumber')
			#if cliente_endereco:
			#	buildingnumber.text = cliente_endereco.address_line1

			streetname = ET.SubElement(billingaddress,'StreetName')
			if cliente_endereco:
				streetname.text = cliente_endereco.address_line1

			addressdetail = ET.SubElement(billingaddress,'AddressDetail')
			if cliente.customer_name == 'Diversos' or cliente.customer_name == 'General':
				addressdetail.text = "Consumidor final"
			elif cliente_endereco:				
				addressdetail.text = cliente_endereco.address_line1

			else:
				addressdetail.text = "Desconhecido"	#default

			city = ET.SubElement(billingaddress,'City')
			if cliente.customer_name == 'Diversos' or cliente.customer_name == 'General':
				city.text = "Desconhecido"	#default
			elif cliente_endereco:				
				city.text = cliente_endereco.city

			else:
				city.text = "Desconhecido"	#default


			if cliente_endereco:
				city.text = cliente_endereco.city

			postalcode = ET.SubElement(billingaddress,'PostalCode')
			if cliente.customer_name == 'Diversos' or cliente.customer_name == 'General':
				postalcode.text = "Desconhecido"	#default
			elif cliente_endereco:				
				postalcode.text = cliente_endereco.pincode

			else:
				postalcode.text = "Desconhecido"	#default


			province = ET.SubElement(billingaddress,'Province')
			if cliente_endereco:
				province.text = cliente_endereco.city


			country = ET.SubElement(billingaddress,'Country')
			if cliente.customer_name == 'Diversos' or cliente.customer_name == 'General':
				country.text = "Desconhecido"	#default
			elif cliente_endereco:				
				if cliente_endereco.country == 'Angola':
					country.text = "AO"
				else:
					country.text = cliente_endereco.country


			else:
				country.text = "Desconhecido"	#default


			#END BILLING address

			#START SHIPTO address
			shiptoaddress = ET.SubElement(customer,'ShipToAddress')

			buildingnumber = ET.SubElement(shiptoaddress,'BuildingNumber')

			streetname = ET.SubElement(shiptoaddress,'StreetName')
			if cliente_endereco:
				streetname.text = cliente_endereco.address_line1

			addressdetail = ET.SubElement(shiptoaddress,'AddressDetail')
			if cliente.customer_name == 'Diversos' or cliente.customer_name == 'General':
				addressdetail.text = "Consumidor final"
			elif cliente_endereco:				
				addressdetail.text = cliente_endereco.address_line1

			else:
				addressdetail.text = "Desconhecido"	#default

			city = ET.SubElement(shiptoaddress,'City')
			if cliente.customer_name == 'Diversos' or cliente.customer_name == 'General':
				city.text = "Desconhecido"	#default
			elif cliente_endereco:				
				city.text = cliente_endereco.city

			else:
				city.text = "Desconhecido"	#default

			postalcode = ET.SubElement(shiptoaddress,'PostalCode')
			if cliente.customer_name == 'Diversos' or cliente.customer_name == 'General':
				postalcode.text = "Desconhecido"	#default
			elif cliente_endereco:				
				postalcode.text = cliente_endereco.pincode

			else:
				postalcode.text = "Desconhecido"	#default

			province = ET.SubElement(shiptoaddress,'Province')
			if cliente_endereco:
				province.text = cliente_endereco.city

			country = ET.SubElement(shiptoaddress,'Country')
			if cliente.customer_name == 'Diversos' or cliente.customer_name == 'General':
				country.text = "Desconhecido"	#default
			elif cliente_endereco:				
				if cliente_endereco.country == 'Angola':
					country.text = "AO"
				else:
					country.text = cliente_endereco.country


			else:
				country.text = "Desconhecido"	#default



			#END SHIPTO address

			telephone = ET.SubElement(customer,'Telephone')
			if cliente_endereco:
				telephone.text = cliente_endereco.phone

			fax = ET.SubElement(customer,'Fax')
			if cliente_endereco:
				fax.text = cliente_endereco.fax

			email = ET.SubElement(customer,'Email')
			if cliente_endereco:
				email.text = cliente_endereco.email_id

			website = ET.SubElement(customer,'Website')
			website.text = cliente.website


			selfbillingindicator = ET.SubElement(customer,'SelfBillingIndicator')
			selfbillingindicator.text = 0	#default

		#END OF Customers

	#create Suppliers


	#Suppliers
	suppliers = ET.SubElement(masterfiles,'Suppliers')
	fornecedores = frappe.db.sql(""" select * from `tabSupplier` where docstatus = 0 """,as_dict=True)

	adicionafornecedor = True

	for fornecedor in fornecedores:
		contasfornecedor = frappe.db.sql(""" select * from `tabParty Account` where parenttype = 'Supplier' and parentfield = 'accounts' and parent = %s and company = %s """,(fornecedor.name, empresa.name), as_dict=True)
		print 'account fornecedor'
		print fornecedor.name
		print contasfornecedor

		if not contasfornecedor:
			#test to see if exists ... but on diff company

			contasfornecedor = frappe.db.sql(""" select * from `tabParty Account` where parenttype = 'Supplier' and parentfield = 'accounts' and parent = %s """,(fornecedor.name), as_dict=True)
			print 'outra empresa'
			print contasfornecedor
			if contasfornecedor:
				#Outra empresa..
				adicionafornecedor = False
			else:
				adicionafornecedor = True
		
		
		if adicionafornecedor == True:
			print 'Add Fornecedor'
			print 'Add Fornecedor'
			print 'Add Fornecedor'



			supplier = ET.SubElement(suppliers,'Supplier')
			supplierid = ET.SubElement(supplier,'SupplierID')
			supplierid.text = fornecedor.name

		
			accountid = ET.SubElement(supplier,'AccountID')

			if not contasfornecedor:
					contasfornecedor = frappe.db.sql(""" select * from `tabAccount` where name like '31121000%%' and company = %s """,(empresa.name), as_dict=True)
					print contasfornecedor
					accountid.text = contasfornecedor[0].account_name
					#accountid.text = contasfornecedor[0].account_number
#				else:
#					accountid.text = "Desconhecido"				
			else:

				accountid.text = contasfornecedor[0].account
				#In case we need to get account_number instead
				#contasfornecedor = frappe.db.sql(""" select * from `tabAccount` where name = %s and company = %s """,(contascliente[0].account,empresa.name), as_dict=True)
				#accountid.text = contasfornecedor[0].account_number



			suppliertaxid = ET.SubElement(supplier,'SupplierTaxID')
			suppliertaxid.text = fornecedor.tax_id
			if (fornecedor.tax_id != None and (fornecedor.tax != "N/A" or fornecedor.tax != "N-A")) :	
				suppliertaxid.text = fornecedor.tax_id
			else:
				suppliertaxid.text = "999999990"


			companyname = ET.SubElement(supplier,'CompanyName')
			companyname.text = fornecedor.supplier_name

			contact = ET.SubElement(supplier,'Contact')
			#contact.text = fornecedor.contact

			#START BILLING address
			#address = ET.SubElement(supplier,'Address')
			billingaddress = ET.SubElement(supplier,'BillingAddress')

			fornecedor_endereco = angola.get_all_enderecos_a("Supplier",fornecedor.name)
			#if fornecedor_endereco:
			#	print fornecedor_endereco.address_line1
			#	billingaddress.text = fornecedor_endereco.address_line1

			buildingnumber = ET.SubElement(billingaddress,'BuildingNumber')

			streetname = ET.SubElement(billingaddress,'StreetName')
			if fornecedor_endereco:
				streetname.text = fornecedor_endereco.address_line1


			addressdetail = ET.SubElement(billingaddress,'AddressDetail')
			if fornecedor_endereco:
				addressdetail.text = fornecedor_endereco.address_line1

			city = ET.SubElement(billingaddress,'City')
			if fornecedor_endereco:
				city.text = fornecedor_endereco.city


			postalcode = ET.SubElement(billingaddress,'PostalCode')
			if fornecedor_endereco:
				postalcode.text = fornecedor_endereco.pincode

			province = ET.SubElement(billingaddress,'Province')
			if fornecedor_endereco:
				province.text = fornecedor_endereco.city

			country = ET.SubElement(billingaddress,'Country')
			if fornecedor_endereco:
				if fornecedor_endereco.country == 'Angola':
					country.text = "AO"
				else:
					country.text = fornecedor_endereco.country


			#END BILLING ADDRESS

			#START SHIPTO address
			shipfromaddress = ET.SubElement(supplier,'ShipFromAddress')
			buildingnumber = ET.SubElement(shipfromaddress,'BuildingNumber')
			streetname = ET.SubElement(shipfromaddress,'StreetName')
			if fornecedor_endereco:
				streetname.text = fornecedor_endereco.address_line1

			addressdetail = ET.SubElement(shipfromaddress,'AddressDetail')
			if fornecedor_endereco:
				addressdetail.text = fornecedor_endereco.address_line1

			city = ET.SubElement(shipfromaddress,'City')
			if fornecedor_endereco:
				city.text = fornecedor_endereco.city

			postalcode = ET.SubElement(shipfromaddress,'PostalCode')
			if fornecedor_endereco:
				postalcode.text = fornecedor_endereco.pincode

			province = ET.SubElement(shipfromaddress,'Province')
			if fornecedor_endereco:
				province.text = fornecedor_endereco.city

			country = ET.SubElement(shipfromaddress,'Country')
			if fornecedor_endereco:
				if fornecedor_endereco.country == 'Angola':
					country.text = "AO"
				else:
					country.text = fornecedor_endereco.country


			#END SHIPTO ADDRESS

			telephone = ET.SubElement(supplier,'Telephone')
			if fornecedor_endereco:
				telephone.text = fornecedor_endereco.phone

			fax = ET.SubElement(supplier,'Fax')
			if fornecedor_endereco:
				fax.text = fornecedor_endereco.fax

			email = ET.SubElement(supplier,'Email')
			if fornecedor_endereco:
				email.text = fornecedor_endereco.email_id

			website = ET.SubElement(supplier,'Website')
			website.text = fornecedor.website

			selfbillingindicator = ET.SubElement(supplier,'SelfBillingIndicator')
			selfbillingindicator.text = 0 #default

	#END OF Suppliers



	#create Products / Services
	#Products


	products = ET.SubElement(masterfiles,'Products')

	produtos = frappe.db.sql(""" select * from `tabItem` where docstatus = 0 """,as_dict=True)

	for produto in produtos:
	
		product = ET.SubElement(products,'Product')
		producttype = ET.SubElement(product,'ProductType')
		if produto.is_stock_item:
			producttype.text = "P" #Produto
		else:
			producttype.text = "S" #Servico

		
		productcode = ET.SubElement(product,'ProductCode')
		productcode.text = produto.item_code

		productgroup = ET.SubElement(product,'ProductGroup')
		productgroup.text = produto.item_group

		productdescription = ET.SubElement(product,'ProductDescription')
		productdescription.text = produto.item_name

		productnumbercode = ET.SubElement(product,'ProductNumberCode')
		productnumbercode.text = produto.barcode

		customsdetails = ET.SubElement(product,'CustomsDetails')
		unnumber = ET.SubElement(product,'UNNumber')

	#END OF Products


	#create Retencoes...
	#TaxTable

	
	taxtable = ET.SubElement(masterfiles,'TaxTable')
	retencoes = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 """,as_dict=True)

	for retencao in retencoes:

		taxtableentry = ET.SubElement(taxtable,'TaxTableEntry')
		taxtype = ET.SubElement(taxtableentry,'TaxType')
		if "IPC" in retencao.name:
			taxtype.text = "NS"
		elif "SELO" in retencao.name:
			taxtype.text = "IS"
		elif "IVA" in retencao.name:
			taxtype.text = "IVA"
		else:
			taxtype.text = "NS"

		taxcountryregion = ET.SubElement(taxtableentry,'TaxCountryRegion')


		taxcode = ET.SubElement(taxtableentry,'TaxCode')
		if "IPC" in retencao.name:
			taxcode.text = "NS"
		elif "SELO" in retencao.name:
			taxcode.text = "ISE"
		elif "IVA" in retencao.name:
			taxcode.text = "ISE"
		else:
			taxcode.text = "NS"

		description = ET.SubElement(taxtableentry,'Description')
		description.text = retencao.descricao

		taxexpirationdate = ET.SubElement(taxtableentry,'TaxExpirationDate')
		if retencao.data_limite:
			taxexpirationdate.text = str(retencao.data_limite.strftime("%Y-%m-%d"))

		taxpercentage = ET.SubElement(taxtableentry,'TaxPercentage')
		taxamount = ET.SubElement(taxtableentry,'TaxAmount')
		if retencao.percentagem:
			taxpercentage.text = str(retencao.percentagem)
			taxamount.text = "0"	#default POR VERIFICAR
		else:
			taxamount.text = "0"	#default 



	#END OF TaxTable



	#GeneralLEdgerEntries
	generalledgerentries = ET.SubElement(data,'GeneralLedgerEntries')
	#generalledgerentries = ET.Element('GeneralLedgerEntries')

	#primeirodiames = '2019-02-18'
	#ultimodiames = '2019-02-18'


	jvs = frappe.db.sql(""" select count(name), sum(total_debit), sum(total_credit) from `tabJournal Entry` where company = %s and docstatus = 1 and posting_date >= %s and posting_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)

	numberofentries = ET.SubElement(generalledgerentries,'NumberOfEntries')
	totaldebit = ET.SubElement(generalledgerentries,'TotalDebit')
	totalcredit = ET.SubElement(generalledgerentries,'TotalCredit')

	if int(jvs[0]['count(name)']) !=0:
		numberofentries.text = str(jvs[0]['count(name)'])
		totaldebit.text = str(jvs[0]['sum(total_debit)'])
		totalcredit.text = str(jvs[0]['sum(total_credit)'])



		print 'Journal Entry'
		print 'Journal Entry'
		print jvs


		#JV
		jvs = frappe.db.sql(""" select * from `tabJournal Entry` where company = %s and docstatus = 1 and posting_date >= %s and posting_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)

		for jv in jvs:
			print jv.name
			print jv.cheque_date	
			journal = ET.SubElement(generalledgerentries,'Journal')
			journalid = ET.SubElement(journal,'JournalID')
			journalid.text = str(jv.name)
		
			description = ET.SubElement(journal,'Description')
			if jv.user_remark != None:
				description.text = str(jv.user_remark)
			elif jv.cheque_no != None:
				description.text = str(jv.cheque_no)
			elif jv.remark != None:
				description.text = str(jv.remark)


			#transaction

			transaction = ET.SubElement(journal,'Transaction')
			transactionid = ET.SubElement(transaction,'TransactionID')
			transactionid.text = str(jv.posting_date.strftime("%Y-%m-%d")) + "  " + str(jv.name)

			period = ET.SubElement(transaction,'Period')
			period.text = str(jv.modified.year)		#check date YEAR

			transactiondate = ET.SubElement(transaction,'TransactionDate')
			if jv.cheque_date:
				transactiondate.text = str(jv.cheque_date)
			else:
				transactiondate.text = str(jv.posting_date.strftime("%Y-%m-%d"))

			sourceid = ET.SubElement(transaction,'SourceID')
			sourceid.text = str(jv.owner)	

			description = ET.SubElement(transaction,'Description')
			if jv.user_remark != None:
				description.text = str(jv.remark)	

			docarchivalnumber = ET.SubElement(transaction,'DocArchivalNumber')
			#Sera o GL ou pode ser o jv.name !!!!

			transactiontype = ET.SubElement(transaction,'TransactionType')
			#jv.voucher_type
			transactiontype.text = "N"	# default para APP

			glpostingdate = ET.SubElement(transaction,'GLPostingDate')
			#glpostingdate.text = str(jv.posting_date.strftime("%Y-%m-%d")) + "T" + str(jv.posting_date.strftime("%H:%M:%S"))	#Posting date to JV
			glpostingdate.text = str(jv.posting_date.strftime("%Y-%m-%d"))

			customerid = ET.SubElement(transaction,'CustomerID')
			supplierid = ET.SubElement(transaction,'SupplierID')

			#lines
			lines = ET.SubElement(transaction,'Lines')
			jvaccounts = frappe.db.sql(""" select * from `tabJournal Entry Account` where parent = %s order by idx """,(jv.name), as_dict=True)

			for jvaccount in jvaccounts:
				#In case we need to get account_number instead
				#conta = frappe.db.sql(""" select * from `tabAccount` where name = %s and company = %s """,(jvaccount.account,empresa.name), as_dict=True)
				#accountid.text = conta[0].account_number

				#DEBIT
				if jvaccount.debit != 0:
					debitline = ET.SubElement(lines,'DebitLine')
					recordid = ET.SubElement(debitline,'RecordID')
					recordid.text = str(jvaccount.idx)

					accountid = ET.SubElement(debitline,'AccountID')
					accountid.text = str(jvaccount.account)
					#accountid.text = conta[0].account_number

					#Is this SI/DN or the JV ID
					sourcedocumentid = ET.SubElement(debitline,'SourceDocumentID')
					sourcedocumentid.text = str(jvaccount.account)

					systementrydate = ET.SubElement(debitline,'SystemEntryDate')
					systementrydate.text = str(jvaccount.creation.strftime("%Y-%m-%dT%H:%M:%S"))	#Creation


					description = ET.SubElement(debitline,'Description')
					description.text = str(jvaccount.account)	

					debitamount = ET.SubElement(debitline,'DebitAmount')
					debitamount.text = str(jvaccount.debit)	

					#para cliente ou supplier
					if jvaccount.party_type == "Customer":
						customerid.text = str(jvaccount.party)	

					elif jvaccount.party_type == "Supplier":
						supplierid.text = str(jvaccount.party)	

				elif jvaccount.credit != 0:
					#CREDIT
					creditline = ET.SubElement(lines,'CreditLine')
					recordid = ET.SubElement(creditline,'RecordID')
					recordid.text = str(jvaccount.idx)

					accountid = ET.SubElement(creditline,'AccountID')
					accountid.text = str(jvaccount.account)
					#accountid.text = conta[0].account_number

					sourcedocumentid = ET.SubElement(creditline,'SourceDocumentID')
					sourcedocumentid.text = str(jvaccount.account)

					systementrydate = ET.SubElement(creditline,'SystemEntryDate')
					systementrydate.text = str(jvaccount.creation.strftime("%Y-%m-%dT%H:%M:%S"))	#Creation

					description = ET.SubElement(creditline,'Description')
					description.text = str(jvaccount.account)	

					creditamount = ET.SubElement(creditline,'CreditAmount')
					creditamount.text = str(jvaccount.credit)	

					#para cliente ou supplier
					if jvaccount.party_type == "Customer":
						customerid.text = str(jvaccount.party)	

					elif jvaccount.party_type == "Supplier":
						supplierid.text = str(jvaccount.party)	


	#END OF GeneralLEdgerEntries




	####SourceDocuments
	sourcedocuments = ET.SubElement(data,'SourceDocuments')

	#create Sales Invoices


	#SalesInvoices
	salesinvoices = ET.SubElement(sourcedocuments,'SalesInvoices')

	'''
	A data de criação do documento de venda [campo 4.1.4.7 - data do documento de venda (InvoiceDate) do SAF-T (AO)];
	ii. A data e hora da criação do documento de venda [campo 4.1.4.12 - data de gravação do documento (SystemEntryDate) do SAF-T (AO)];
	iii. O número do documento de venda [campo 4.1.4.1 - identificação única do documento de venda (InvoiceNo) do SAF-T (AO)];
	iv. O valor do documento de venda [campo 4.1.4.20.3 - total do documento com impostos (GrossTotal) do SAF-T (AO)];
	v. A assinatura gerada no documento anterior, do mesmo tipo e série de documento [campo 4.1.4.4 - chave do documento (Hash) do SAF-T (AO)].

	Para assinar [Registo1.txt = 2010-05-18;2010-05-18T11:22:19;FAC 001/14;3.12;]
	openssl dgst -sha1 -sign ChavePrivada.pem -out Registo1.sha1 Registo1.txt
	'''
	#Debitos ou pagamentos
	facturas = frappe.db.sql(""" select count(name), sum(rounded_total) from `tabSales Invoice` where company = %s and (status = 'Paid' or status = 'Cancelled' ) and posting_date >= %s and posting_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)


	print facturas
	print int(facturas[0]['count(name)'])


	numberofentries = ET.SubElement(salesinvoices,'NumberOfEntries')
	totaldebit = ET.SubElement(salesinvoices,'TotalDebit')
	##### POR FAZER
	totalcredit = ET.SubElement(salesinvoices,'TotalCredit')

	####### POR FAZER

	if int(facturas[0]['count(name)']) !=0:
		numberofentries.text = str(int(facturas[0]['count(name)']))
		totaldebit.text = str(int(facturas[0]['sum(rounded_total)']))

	#Creditos ou devolucoes
	facturas = frappe.db.sql(""" select count(name), sum(rounded_total) from `tabSales Invoice` where company = %s and (status = 'Return' or status = 'Credit note issued') and posting_date >= %s and posting_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)
	if int(facturas[0]['count(name)']) !=0:
		totalcredit.text = str(int(facturas[0]['sum(rounded_total)']))



	#invoice
	facturas = frappe.db.sql(""" select * from `tabSales Invoice` where company = %s and (status = 'Paid' or status = 'Cancelled' or status = 'Return') and posting_date >= %s and posting_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)

	#Hash
	chaveanterior =""
	fileregisto = "registo"
	fileregistocontador = 1	

	for factura in facturas:
		print factura.name
		print factura.creation
		print factura.modified

		invoice = ET.SubElement(salesinvoices,'Invoice')

		invoiceno = ET.SubElement(invoice,'InvoiceNo')
		invoiceno.text = str(factura.name)

		#documentstatus
		documentstatus = ET.SubElement(invoice,'DocumentStatus')
		invoicestatus = ET.SubElement(documentstatus,'InvoiceStatus')
		if factura.status =="Paid" and factura.docstatus == 1:
			invoicestatus.text = "F"	#Facturado
		elif factura.status =="Cancelled" and factura.docstatus == 2:
			invoicestatus.text = "A"	#Anulado

		else:
			invoicestatus.text = "N"	#Normal


		invoicestatusdate = ET.SubElement(documentstatus,'InvoiceStatusDate')
		#Will be needed to add T between date and time!!!!!!!
		invoicestatusdate.text = factura.modified.strftime("%Y-%m-%dT%H:%M:%S")	#ultima change

		reason = ET.SubElement(documentstatus,'Reason')
		#Pode ser os Comments when deleted the Documents ....
		if factura.remarks != 'No Remarks' and factura.remarks != 'Sem Observações':
			reason.text = factura.remarks
		elif factura._comments != None:
			reason.text = factura._comments

		sourceid = ET.SubElement(documentstatus,'SourceID')
		sourceid.text = factura.modified_by	#User

		sourcebilling = ET.SubElement(documentstatus,'SourceBilling')
		sourcebilling.text = "P"	#Default

		salesinvoicehash = ET.SubElement(invoice,'Hash')
		#salesinvoicehash.text = 0	#por rever...

		salesinvoicehashcontrol = ET.SubElement(invoice,'HashControl')
		salesinvoicehashcontrol.text = "Nao validado pela AGT"	#default for now

		period = ET.SubElement(invoice,'Period')
		period.text = str(factura.modified.month)	#last modified month

		invoicedate = ET.SubElement(invoice,'InvoiceDate')
		invoicedate.text = factura.posting_date.strftime("%Y-%m-%d")	#posting date

		invoicetype = ET.SubElement(invoice,'InvoiceType')
		print 'NC ', factura.return_against
		if factura.is_pos == 1 and factura.status == 'Credit Note Issued':
			invoicetype.text = "NC"	#POS NC usually mistaken...
		if factura.is_pos == 1 :
			invoicetype.text = "FR"	#POS deve ser FR ou TV

		elif factura.return_against != None:
			invoicetype.text = "NC"	#Retorno / Credit Note

		else:
			invoicetype.text = "FT"	#default sales invoice

		#specialRegimes
		specialregimes = ET.SubElement(invoice,'SpecialRegimes')
		selfbillingindicator = ET.SubElement(specialregimes,'SelfBillingIndicator')
		selfbillingindicator.text = 0	#default 

		cashvatschemeindicator = ET.SubElement(specialregimes,'CashVATSchemeIndicator')
		cashvatschemeindicator.text = 0	#default 

		thirdpartiesbillingindicator = ET.SubElement(specialregimes,'ThirdPartiesBillingIndicator')
		thirdpartiesbillingindicator.text = 0	#default 

		sourceid = ET.SubElement(invoice,'SourceID')
		sourceid.text = factura.owner	#created by

		eaccode = ET.SubElement(invoice,'EACCode')

		systementrydate = ET.SubElement(invoice,'SystemEntryDate')
		systementrydate.text = factura.creation.strftime("%Y-%m-%dT%H:%M:%S")	#creation date

		transactions = ET.SubElement(invoice,'Transactions')

		entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='sales invoice' and company = %s and voucher_no = %s """,(empresa.name,factura.name), as_dict=True)
		if entradasgl:
			for entradagl in entradasgl:
				print 'transactions ids'
				print entradagl
				transactionid = ET.SubElement(transactions,'TransactionID')
				transactionid.text = entradagl.name	#entrada GL;single invoice can generate more than 2GL

		customerid = ET.SubElement(invoice,'CustomerID')
		customerid.text = factura.customer	#cliente


		#shipto
		shipto = ET.SubElement(invoice,'ShipTo')
		deliveryid = ET.SubElement(shipto,'DeliveryID')
		deliverydate = ET.SubElement(shipto,'DeliveryDate')
		warehouseid = ET.SubElement(shipto,'WarehouseID')
		locationid = ET.SubElement(shipto,'LocationID')
		#address
		address = ET.SubElement(shipto,'Address')	
		buildingnumber = ET.SubElement(address,'BuildingNumber')
		streetname = ET.SubElement(address,'StreetName')
		addressdetail = ET.SubElement(address,'AddressDetail')
		city = ET.SubElement(address,'City')
		postalcode = ET.SubElement(address,'PostalCode')
		province = ET.SubElement(address,'Province')
		country = ET.SubElement(address,'Country')
		#shipfrom
		shipfrom = ET.SubElement(invoice,'ShipFrom')
		deliveryid = ET.SubElement(shipfrom,'DeliveryID')
		deliverydate = ET.SubElement(shipfrom,'DeliveryDate')
		warehouseid = ET.SubElement(shipfrom,'WarehouseID')
		locationid = ET.SubElement(shipfrom,'LocationID')
		#address
		address = ET.SubElement(shipfrom,'Address')
		buildingnumber = ET.SubElement(address,'BuildingNumber')
		streetname = ET.SubElement(address,'StreetName')
		addressdetail = ET.SubElement(address,'AddressDetail')
		city = ET.SubElement(address,'City')
		postalcode = ET.SubElement(address,'PostalCode')
		province = ET.SubElement(address,'Province')
		country = ET.SubElement(address,'Country')

		movementendtime = ET.SubElement(invoice,'MovementEndTime')
		movementstarttime = ET.SubElement(invoice,'MovementStartTime')

		#line
		line = ET.SubElement(invoice,'Line')
		facturaitems = frappe.db.sql(""" select * from `tabSales Invoice Item` where parent = %s order by idx """,(factura.name), as_dict=True)
		
		for facturaitem in facturaitems:

			linenumber = ET.SubElement(line,'LineNumber')
			linenumber.text = str(facturaitem.idx)

			#SALES ORDER
			#orderreferences
			orderreferences = ET.SubElement(line,'OrderReferences')
			originatingon = ET.SubElement(orderreferences,'OriginatingON')
			orderdate = ET.SubElement(orderreferences,'OrderDate')
			if facturaitem.sales_order:
				originatingon.text = facturaitem.sales_order
				ordemvenda = frappe.db.sql(""" select * from `tabSales Order` where name = %s """,(facturaitem.sales_order), as_dict=True)
				orderdate.text = ordemvenda[0].transaction_date.strftime("%Y-%m-%d")



			productcode = ET.SubElement(line,'ProductCode')
			productcode.text = facturaitem.item_code

			productdescription = ET.SubElement(line,'ProductDescription')
			productdescription.text = facturaitem.item_name

			quantity = ET.SubElement(line,'Quantity')
			quantity.text = str(facturaitem.qty)


			unifofmeasure = ET.SubElement(line,'UnifOfMeasure')
			unifofmeasure.text = facturaitem.uom

			unitprice = ET.SubElement(line,'UnitPrice')
			unitprice.text = str(facturaitem.rate)

			taxbase = ET.SubElement(line,'TaxBase')
			taxbase.text = str(facturaitem.net_rate)

			taxpointdate = ET.SubElement(line,'TaxPointDate')
			dn = frappe.db.sql(""" select * from `tabDelivery Note` where name = %s """,(facturaitem.delivery_note), as_dict=True)
			print 'DNnnnn'
			print dn
			if dn:
				taxpointdate.text = dn[0].posting_date.strftime("%Y-%m-%d")	#DN

			#Against .. in case of change or DN ?????
			#references
			references = ET.SubElement(line,'References')
			reference = ET.SubElement(references,'Reference')
			if factura.return_against != None:
				reference.text = factura.return_against

			reason = ET.SubElement(references,'Reason')

			description = ET.SubElement(line,'Description')
			description.text = facturaitem.item_description

			#productserialnumber
			productserialnumber = ET.SubElement(line,'ProductSerialNumber')
			serialnumber = ET.SubElement(productserialnumber,'SerialNumber')
			serialnumber.text = facturaitem.serial_no

			###If invoice was cancelled or deleted should not add...!!!!!
			if factura.status !="Cancelled" and factura.docstatus != 2:
				debitamount = ET.SubElement(line,'DebitAmount')
				debitamount.text = str(facturaitem.amount)

				creditamount = ET.SubElement(line,'CreditAmount')
				#POR VER SE TEM....

			#tax
			taxes = ET.SubElement(line,'Taxes')
			
			### TAX por PRODUTO OU SERVICO

			#procura no recibo pelo IS
			#recibos = frappe.db.sql(""" select * from `tabPayment Entry` where parent = %s """,(factura.name), as_dict=True)
			recibosreferencias = frappe.db.sql(""" select * from `tabPayment Entry Reference` where reference_doctype = 'sales invoice' and docstatus = 1 and reference_name = %s """,(factura.name), as_dict=True)
			print 'recibos refenrecias'
			print factura.name
			print recibosreferencias
			if factura.name == 'FT19/0061':
				print 'TEM IPC'
				print facturaitem.imposto_de_consumo
				
			
			#if facturaitem.imposto_de_consumo or factura.is_pos == 1 :	#Caso tem IPC or IVA or IS_POS
			if factura.is_pos == 0 :	#NOT IS_POS
				#if factura.name == 'SINV-19/06853':
				#	print 'ipc ou is pos'
				#	return
		
				if recibosreferencias:
					recibos = frappe.db.sql(""" select * from `tabPayment Entry` where name = %s """,(recibosreferencias[0].parent), as_dict=True)
					print 'recibos'
					print recibosreferencias[0].parent
					print recibos

					#entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='payment entry' and company = %s and voucher_no = %s """,(empresa.name,recibosreferencias[0].parent), as_dict=True)
					for reciboreferencia in recibosreferencias:
						entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='payment entry' and company = %s and voucher_no = %s """,(empresa.name,reciboreferencia.parent), as_dict=True)

						print 'entradasgl+++++'

						#print entradasgl
						#return


						if entradasgl:
							for entradagl in entradasgl:

								print entradagl.account
								print entradagl.credit_in_account_currency
								if "34210000" in entradagl.account:
									tax = ET.SubElement(taxes,'Tax')
									taxtype = ET.SubElement(tax,'TaxType')

									taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
									taxcountryregion.text = "AO"

									#imposto de producao e consumo IPC
									taxtype.text = "NS"
									taxcode = ET.SubElement(tax,'TaxCode')
									taxcode.text = "NS"

									retn = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 and name  = 'ipc' """,as_dict=True)
									print retn


									taxpercentage = ET.SubElement(tax,'TaxPercentage')
									taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

									taxamount = ET.SubElement(tax,'TaxAmount')
									taxamount.text = str(entradagl.credit) 		


								elif "34710000" in entradagl.account:
									tax = ET.SubElement(taxes,'Tax')
									taxtype = ET.SubElement(tax,'TaxType')

									taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
									taxcountryregion.text = "AO"

									#imposto de selo
									taxtype.text = "IS"
									taxcode = ET.SubElement(tax,'TaxCode')
									taxcode.text = "NS"

									retn = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 and name  like '%%selo' """,as_dict=True)
									print retn


									taxpercentage = ET.SubElement(tax,'TaxPercentage')
									taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

									taxamount = ET.SubElement(tax,'TaxAmount')
									taxamount.text = str(entradagl.credit) 		


								elif "34140000" in entradagl.account:
									tax = ET.SubElement(taxes,'Tax')
									taxtype = ET.SubElement(tax,'TaxType')

									taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
									taxcountryregion.text = "AO"

									#retencao na fonte
									taxtype.text = "NS"
									taxcode = ET.SubElement(tax,'TaxCode')
									taxcode.text = "NS"

									retn = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 and name  like '%%fonte' """,as_dict=True)
									print retn


									taxpercentage = ET.SubElement(tax,'TaxPercentage')
									taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

									taxamount = ET.SubElement(tax,'TaxAmount')
									taxamount.text = str(entradagl.debit) 		



								elif "IVA" in entradagl.account:
									tax = ET.SubElement(taxes,'Tax')
									taxtype = ET.SubElement(tax,'TaxType')

									taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
									taxcountryregion.text = "AO"

									#IVA	ainda por rever
									taxtype.text = "IVA"
									taxcode = ET.SubElement(tax,'TaxCode')
									taxcode.text = "NOR"

								#else:
								#	taxtype.text = "NS"
								#	taxcode = ET.SubElement(tax,'TaxCode')
								#	taxcode.text = "NS"


									taxpercentage = ET.SubElement(tax,'TaxPercentage')
									taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

									taxamount = ET.SubElement(tax,'TaxAmount')
									taxamount.text = str(entradagl.credit) 		
			
							#return			
			else:
					#caso POS or even bcs previous found nothing... 
			
				entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='sales invoice' and company = %s and voucher_no = %s """,(empresa.name,factura.name), as_dict=True)
				#if factura.name == 'FT19/0061':
				#	print 'entradasgl'
				print entradasgl
				#	return

				if entradasgl:

					for entradagl in entradasgl:

						print entradagl.account
						print entradagl.credit_in_account_currency
						if factura.name == 'FT19/0061':
							return

						if "34210000" in entradagl.account:
							tax = ET.SubElement(taxes,'Tax')
							taxtype = ET.SubElement(tax,'TaxType')

							taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
							taxcountryregion.text = "AO"

							#imposto de producao e consumo IPC
							taxtype.text = "NS"
							taxcode = ET.SubElement(tax,'TaxCode')
							taxcode.text = "NS"

							retn = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 and name  = 'ipc' """,as_dict=True)
							print retn


							taxpercentage = ET.SubElement(tax,'TaxPercentage')
							taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

							taxamount = ET.SubElement(tax,'TaxAmount')
							taxamount.text = str(entradagl.credit) 		


						elif "34710000" in entradagl.account:
							tax = ET.SubElement(taxes,'Tax')
							taxtype = ET.SubElement(tax,'TaxType')

							taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
							taxcountryregion.text = "AO"

							#imposto de selo
							taxtype.text = "IS"
							taxcode = ET.SubElement(tax,'TaxCode')
							taxcode.text = "NS"

							retn = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 and name  like '%%selo' """,as_dict=True)
							print retn


							taxpercentage = ET.SubElement(tax,'TaxPercentage')
							taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

							taxamount = ET.SubElement(tax,'TaxAmount')
							taxamount.text = str(entradagl.credit) 		


						elif "34140000" in entradagl.account:
							tax = ET.SubElement(taxes,'Tax')
							taxtype = ET.SubElement(tax,'TaxType')

							taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
							taxcountryregion.text = "AO"

							#retencao na fonte
							taxtype.text = "NS"
							taxcode = ET.SubElement(tax,'TaxCode')
							taxcode.text = "NS"

							retn = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 and name  like '%%fonte' """,as_dict=True)
							print retn


							taxpercentage = ET.SubElement(tax,'TaxPercentage')
							taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

							taxamount = ET.SubElement(tax,'TaxAmount')
							taxamount.text = str(entradagl.debit) 		



						elif "IVA" in entradagl.account:
							tax = ET.SubElement(taxes,'Tax')
							taxtype = ET.SubElement(tax,'TaxType')

							taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
							taxcountryregion.text = "AO"

							#IVA	ainda por rever
							taxtype.text = "IVA"
							taxcode = ET.SubElement(tax,'TaxCode')
							taxcode.text = "NOR"

						#else:
						#	taxtype.text = "NS"
						#	taxcode = ET.SubElement(tax,'TaxCode')
						#	taxcode.text = "NS"


							taxpercentage = ET.SubElement(tax,'TaxPercentage')
							taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

							taxamount = ET.SubElement(tax,'TaxAmount')
							taxamount.text = str(entradagl.credit) 		


			taxexemptionreason = ET.SubElement(line,'TaxExemptionReason')
			taxexemptioncode = ET.SubElement(line,'TaxExemptionCode')
			settlementamount = ET.SubElement(line,'SettlementAmount')

			#customsinformation
			customsinformation = ET.SubElement(line,'CustomsInformation')
			arcno = ET.SubElement(customsinformation,'ARCNo')
			iecamount = ET.SubElement(customsinformation,'IECAmount')



		#documenttotals
		documenttotals = ET.SubElement(invoice,'DocumentTotals')

		taxpayable = ET.SubElement(documenttotals,'TaxPayable')
		print 'factura Referencia'
		if factura.docstatus != 2:
			salestaxescharges = frappe.db.sql(""" select * from `tabSales Taxes and Charges` where parent = %s """,(factura.name),as_dict=True)
			print salestaxescharges

			if salestaxescharges: 
				print salestaxescharges[0].tax_amount
				taxpayable.text = str(salestaxescharges[0].tax_amount) 		#por ir buscar 
			else:
				taxpayable.text = "0.00" 		#por ir buscar 
		#if retencao.credit_in_account_currency:
		#	taxpayable.text = str(retencao.credit_in_account_currency) 		#por ir buscar 

		nettotal = ET.SubElement(documenttotals,'NetTotal')
		nettotal.text = str(factura.net_total)		#Sem Impostos Total Factura

		grosstotal = ET.SubElement(documenttotals,'GrossTotal')
		if factura.rounded_total:
			grosstotal.text = str(factura.rounded_total)		#Total Factura + impostos.... por ir buscar
		else:
			grosstotal.text = "0.00"

		####ONLY IF NOT AOA .... POR VERIFICAR
		#currency
		currency = ET.SubElement(documenttotals,'Currency')
		currencycode = ET.SubElement(currency,'CurrencyCode')

		currencyamount = ET.SubElement(currency,'CurrencyAmount')
		#currencyamount.text = str(factura.rounded_total)		#Total Factura + impostos.... por ir buscar

		exchangerate = ET.SubElement(currency,'ExchangeRate')

		#settlement
		settlement = ET.SubElement(documenttotals,'Settlement')
		settlementdiscount = ET.SubElement(settlement,'SettlementDiscount')
		settlementamount = ET.SubElement(settlement,'SettlementAmount')
		settlementdate = ET.SubElement(settlement,'SettlementDate')
		paymentterms = ET.SubElement(settlement,'PaymentTerms')

		#payment
		payment = ET.SubElement(documenttotals,'Payment')


		if recibosreferencias:
			recibos = frappe.db.sql(""" select * from `tabPayment Entry` where name = %s """,(recibosreferencias[0].parent), as_dict=True)
			print 'recibos'
			print recibosreferencias[0].parent
			print recibos

			for recibo in recibos:
				paymentmechanism = ET.SubElement(payment,'PaymentMechanism')				

				if "Transferência Bancária" in recibo.mode_of_payment:
					paymentmechanism.text = "TB"
				elif "Cash" in recibo.mode_of_payment:					
					paymentmechanism.text = "NU"

				elif "TPA" in recibo.mode_of_payment:					
					paymentmechanism.text = "CD"

				paymentamount = ET.SubElement(payment,'PaymentAmount')
				paymentamount.text = str(recibo.paid_amount)

				paymentdate = ET.SubElement(payment,'PaymentDate')
				paymentdate.text = recibo.posting_date.strftime("%Y-%m-%d")

		#witholdingtax
		#withholdingtax = ET.SubElement(invoice,'WithholdingTax')

		if recibosreferencias:
			recibos = frappe.db.sql(""" select * from `tabPayment Entry` where name = %s """,(recibosreferencias[0].parent), as_dict=True)
			print 'recibos'
			print recibosreferencias[0].parent
			#print recibos

		#entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='payment entry' and company = %s and voucher_no = %s """,(empresa.name,recibosreferencias[0].parent), as_dict=True)
			for reciboreferencia in recibosreferencias:
				print reciboreferencia
				entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='payment entry' and company = %s and voucher_no = %s """,(empresa.name,reciboreferencia.parent), as_dict=True)
				#witholdingtax
				#withholdingtax = ET.SubElement(invoice,'WithholdingTax')

				print 'entradasgl'
				print entradasgl


				variasentradas = False
				if entradasgl:
					for entradagl in entradasgl:
						print 'conta ', entradagl.account
						if "34710000" in entradagl.account:
							#imposto selo
							if variasentradas == True:
								withholdingtax = ET.SubElement(invoice,'WithholdingTax')

							withholdingtaxtype = ET.SubElement(withholdingtax,'WithholdingTaxType')
							withholdingtaxtype.text = "IS"

							withholdingtaxdescription = ET.SubElement(withholdingtax,'WithholdingTaxDescription')
							withholdingtaxdescription.text = entradagl.account

							withholdingtaxamount = ET.SubElement(withholdingtax,'WithholdingTaxAmount')
							withholdingtaxamount.text = str(entradagl.credit)

						elif "34120000" in entradagl.account:
							#imposto industrial
							if variasentradas == True:
								withholdingtax = ET.SubElement(invoice,'WithholdingTax')

							withholdingtaxtype = ET.SubElement(withholdingtax,'WithholdingTaxType')
							withholdingtaxtype.text = "II"

							withholdingtaxdescription = ET.SubElement(withholdingtax,'WithholdingTaxDescription')
							withholdingtaxdescription.text = entradagl.account

							withholdingtaxamount = ET.SubElement(withholdingtax,'WithholdingTaxAmount')
							withholdingtaxamount.text = str(entradagl.credit_in_account_currency)

						elif "34310000" in entradagl.account:
							#IRT
							if variasentradas == True:
								withholdingtax = ET.SubElement(invoice,'WithholdingTax')

							withholdingtaxtype = ET.SubElement(withholdingtax,'WithholdingTaxType')
							withholdingtaxtype.text = "IRT"

							withholdingtaxdescription = ET.SubElement(withholdingtax,'WithholdingTaxDescription')
							withholdingtaxdescription.text = entradagl.account

							withholdingtaxamount = ET.SubElement(withholdingtax,'WithholdingTaxAmount')
							withholdingtaxamount.text = str(entradagl.credit_in_account_currency)

						variasentradas = True	#para garar varias entradas
		#HASH key to generate	
		#Invoicedate + Sytementrydate + InvoiceNo + Grosstotal
		if chaveanterior == "":
			#1st record
			print 'primeiro registo'
			hashinfo = str(factura.posting_date.strftime("%Y-%m-%d")) + ";" + str(factura.creation.strftime("%Y-%m-%dT%H:%M:%S")) + ";" + str(factura.name) + ";" + str(factura.rounded_total) + ";"
		else:
			print 'segundo registo'
			print chaveanterior
			hashinfo = str(factura.posting_date.strftime("%Y-%m-%d")) + ";" + str(factura.creation.strftime("%Y-%m-%dT%H:%M:%S")) + ";" + str(factura.name) + ";" + str(factura.rounded_total) + ";" + str(chaveanterior)


		print 'HASH do SALESINVOICE ', hashinfo
		hashfile = open("/tmp/" + str(fileregisto) + str(fileregistocontador) + ".txt","w")
		hashfile.write(hashinfo)

		ficheirosha1  = "/tmp/" + str(fileregisto) + str(fileregistocontador) + ".sha1"
		ficheirotxt  = "/tmp/" + str(fileregisto) + str(fileregistocontador) + ".txt"

#		myCMD = "openssl dgst -sha1 -sign /tmp/angolaer.cert/angolaerp-selfsigned-priv.pem -out /tmp/" +  ficheirosha1 + " /tmp/" + ficheirotxt + " > /tmp/resultado.txt"

#		myCMD1 = " dgst -sha1 -sign /tmp/angolaerp.cert2/angolaerp-selfsigned-priv.pem -out /tmp/" +  ficheirosha1 + " /tmp/" + ficheirotxt
		myCMD2 =  " /tmp/angolaerp.cert/privkey.pem -out /tmp/" +  ficheirosha1 + " /tmp/" + ficheirotxt

#		print myCMD
		from subprocess import *

#		decrypted = call(myCMD,shell=True)
#		print decrypted
#		p = Popen(["/tmp/angolaerp.cert2/bb.sh"], stdout=PIPE, stderr=PIPE)
		p = Popen(["/tmp/angolaerp.cert2/bb1.sh","/tmp/angolaerp.cert2/angolaerp-selfsigned-priv.pem",ficheirosha1,ficheirotxt], stdout=PIPE, stderr=PIPE)
		output, errors = p.communicate()
		p.wait()
		print 'Openssl Signing and Verifying...'
		print output
		print errors

#		os.system("/tmp/angolaer.cert/bb1.sh " + myCMD1)	#execute

		#encoding base 64
		#ficheirosha1  = str(fileregisto) + str(fileregistocontador) + ".sha1"
		ficheirob64  = "/tmp/" + str(fileregisto) + str(fileregistocontador) + ".b64"

		myCMD1 = 'openssl enc -base64 -in ' +  ficheirosha1 + ' -out ' + ficheirob64 + ' -A' #+ ' > /tmp/resultado.txt'

		print myCMD1
		print 'Openssl Encoding...'
		print ficheirosha1
		print ficheirob64
		os.system(myCMD1)	#Encondingi
#		p = Popen([myCMD1], stdout=PIPE, stderr=PIPE)
#		output, errors = p.communicate()
#		p.wait()

#		print output
#		print errors

	
		hashfile.close()	#close previous ...
		#hashfile.close()	#close previous ...

		hashcriado = open(ficheirob64,'r')	#open the file created to HASH
		print 'Hash criado'
		#print hashcriado.read()
		chaveanterior = str(hashcriado.read())	#para usar no next record...

		salesinvoicehash.text = str(chaveanterior)	#Hash created
		

		fileregistocontador += 1	#contador para registo1, registo2 ....


#		if fileregistocontador == 4:
#			return	
		
		'''
		In case we need to generate Hash for all records on the APP ... this will be done when SAFT export required
		A table Angolaerp_hash must be created with 
			Documenttype, DocumentNumber, Hash, Hashcontrol or Hashversion

		'''



	#END OF SAlesInvoice



	#create Purchase Invoices


	#BuyingInvoices
	purchaseinvoices = ET.SubElement(sourcedocuments,'PurchaseInvoices')
	#still need to filter per user request by MONTH or dates filter...
	#Default CURRENT MONTH

	#Debitos ou pagamentos
	facturas = frappe.db.sql(""" select count(name), sum(rounded_total) from `tabPurchase Invoice` where company = %s and (status = 'Paid' or status = 'Cancelled' ) and posting_date >= %s and posting_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)


	print facturas
	print int(facturas[0]['count(name)'])


	numberofentries = ET.SubElement(purchaseinvoices,'NumberOfEntries')
	totaldebit = ET.SubElement(purchaseinvoices,'TotalDebit')
	##### POR FAZER
	totalcredit = ET.SubElement(purchaseinvoices,'TotalCredit')

	####### POR FAZER

	if int(facturas[0]['count(name)']) !=0:
		numberofentries.text = str(int(facturas[0]['count(name)']))
		totaldebit.text = str(int(facturas[0]['sum(rounded_total)']))

	#Creditos ou devolucoes
	facturas = frappe.db.sql(""" select count(name), sum(rounded_total) from `tabPurchase Invoice` where company = %s and (status = 'Return') and posting_date >= %s and posting_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)
	if int(facturas[0]['count(name)']) !=0:
		totalcredit.text = str(int(facturas[0]['sum(rounded_total)']))



	#invoice
	facturas = frappe.db.sql(""" select * from `tabPurchase Invoice` where company = %s and (status = 'Paid' or status = 'Cancelled' or status = 'Return') and posting_date >= %s and posting_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)

	for factura in facturas:
		print factura.name
		print factura.creation
		print factura.modified

		invoice = ET.SubElement(purchaseinvoices,'Invoice')

		invoiceno = ET.SubElement(invoice,'InvoiceNo')
		invoiceno.text = str(factura.name)

		#documentstatus
		documentstatus = ET.SubElement(invoice,'DocumentStatus')
		invoicestatus = ET.SubElement(documentstatus,'InvoiceStatus')
		if factura.status =="Paid" and factura.docstatus == 1:
			invoicestatus.text = "F"	#Facturado
		elif factura.status =="Cancelled" and factura.docstatus == 2:
			invoicestatus.text = "A"	#Anulado

		else:
			invoicestatus.text = "N"	#Normal


		invoicestatusdate = ET.SubElement(documentstatus,'InvoiceStatusDate')
		#Will be needed to add T between date and time!!!!!!!
		invoicestatusdate.text = factura.modified.strftime("%Y-%m-%dT%H:%M:%S")	#ultima change

		reason = ET.SubElement(documentstatus,'Reason')
		#Pode ser os Comments when deleted the Documents ....
		if factura.remarks != 'No Remarks' and factura.remarks != 'Sem Observações':
			reason.text = factura.remarks
		elif factura._comments != None:
			reason.text = factura._comments

		sourceid = ET.SubElement(documentstatus,'SourceID')
		sourceid.text = factura.modified_by	#User

		sourcebilling = ET.SubElement(documentstatus,'SourceBilling')
		sourcebilling.text = "P"	#Default

		salesinvoicehash = ET.SubElement(invoice,'Hash')
		salesinvoicehash.text = 0	#por rever...

		salesinvoicehashcontrol = ET.SubElement(invoice,'HashControl')
		salesinvoicehashcontrol.text = "Nao validado pela AGT"	#default for now

		period = ET.SubElement(invoice,'Period')
		period.text = str(factura.modified.month)	#last modified month

		invoicedate = ET.SubElement(invoice,'InvoiceDate')
		invoicedate.text = factura.posting_date.strftime("%Y-%m-%d")	#posting date

		invoicetype = ET.SubElement(invoice,'InvoiceType')
		print 'NC ', factura.return_against
		if factura.is_pos == 1:
			invoicetype.text = "FR"	#POS deve ser FR ou TV
		elif factura.return_against != None:
			invoicetype.text = "NC"	#Retorno / Credit Note

		else:
			invoicetype.text = "FT"	#default sales invoice

		'''
		#specialRegimes
		specialregimes = ET.SubElement(invoice,'SpecialRegimes')
		selfbillingindicator = ET.SubElement(specialregimes,'SelfBillingIndicator')
		selfbillingindicator.text = 0	#default 

		cashvatschemeindicator = ET.SubElement(specialregimes,'CashVATSchemeIndicator')
		cashvatschemeindicator.text = 0	#default 

		thirdpartiesbillingindicator = ET.SubElement(specialregimes,'ThirdPartiesBillingIndicator')
		thirdpartiesbillingindicator.text = 0	#default 
		'''
		sourceid = ET.SubElement(invoice,'SourceID')
		sourceid.text = factura.owner	#created by

		supplierid = ET.SubElement(invoice,'SupplierID')
		supplierid.text = factura.supplier	#Fornecedor

		'''
		eaccode = ET.SubElement(invoice,'EACCode')

		systementrydate = ET.SubElement(invoice,'SystemEntryDate')
		systementrydate.text = factura.creation.strftime("%Y-%m-%dT%H:%M:%S")	#creation date

		transactions = ET.SubElement(invoice,'Transactions')

		entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='purchase invoice' and company = %s and voucher_no = %s """,(empresa.name,factura.name), as_dict=True)
		if entradasgl:
			for entradagl in entradasgl:
				print 'transactions ids'
				print entradagl
				transactionid = ET.SubElement(transactions,'TransactionID')
				transactionid.text = entradagl.name	#entrada GL;single invoice can generate more than 2GL



		#shipto
		shipto = ET.SubElement(invoice,'ShipTo')
		deliveryid = ET.SubElement(shipto,'DeliveryID')
		deliverydate = ET.SubElement(shipto,'DeliveryDate')
		warehouseid = ET.SubElement(shipto,'WarehouseID')
		locationid = ET.SubElement(shipto,'LocationID')
		#address
		address = ET.SubElement(shipto,'Address')	
		buildingnumber = ET.SubElement(address,'BuildingNumber')
		streetname = ET.SubElement(address,'StreetName')
		addressdetail = ET.SubElement(address,'AddressDetail')
		city = ET.SubElement(address,'City')
		postalcode = ET.SubElement(address,'PostalCode')
		province = ET.SubElement(address,'Province')
		country = ET.SubElement(address,'Country')
		#shipfrom
		shipfrom = ET.SubElement(invoice,'ShipFrom')
		deliveryid = ET.SubElement(shipfrom,'DeliveryID')
		deliverydate = ET.SubElement(shipfrom,'DeliveryDate')
		warehouseid = ET.SubElement(shipfrom,'WarehouseID')
		locationid = ET.SubElement(shipfrom,'LocationID')
		#address
		address = ET.SubElement(shipfrom,'Address')
		buildingnumber = ET.SubElement(address,'BuildingNumber')
		streetname = ET.SubElement(address,'StreetName')
		addressdetail = ET.SubElement(address,'AddressDetail')
		city = ET.SubElement(address,'City')
		postalcode = ET.SubElement(address,'PostalCode')
		province = ET.SubElement(address,'Province')
		country = ET.SubElement(address,'Country')

		movementendtime = ET.SubElement(invoice,'MovementEndTime')
		movementstarttime = ET.SubElement(invoice,'MovementStartTime')

		#line
		line = ET.SubElement(invoice,'Line')
		facturaitems = frappe.db.sql(""" select * from `tabPurchase Invoice Item` where parent = %s order by idx """,(factura.name), as_dict=True)
		
		for facturaitem in facturaitems:

			linenumber = ET.SubElement(line,'LineNumber')
			linenumber.text = str(facturaitem.idx)

			#SALES ORDER
			#orderreferences
			orderreferences = ET.SubElement(line,'OrderReferences')
			originatingon = ET.SubElement(orderreferences,'OriginatingON')
			orderdate = ET.SubElement(orderreferences,'OrderDate')
			if facturaitem.po_detail:
				ordemcompraitem = frappe.get_doc('Purchase Order Item', facturaitem.po_detail)
				originatingon.text = ordemcompraitem.parent
	
				ordemcompra = frappe.get_doc('Purchase Order Item', ordercompraitem.parent) #frappe.db.sql(""" select * from `tabPurchase Order` where name = %s """,(facturaitem.sales_order), as_dict=True)
				orderdate.text = ordemcompra.transaction_date.strftime("%Y-%m-%d")



			productcode = ET.SubElement(line,'ProductCode')
			productcode.text = facturaitem.item_code

			productdescription = ET.SubElement(line,'ProductDescription')
			productdescription.text = facturaitem.item_name

			quantity = ET.SubElement(line,'Quantity')
			quantity.text = str(facturaitem.qty)


			unifofmeasure = ET.SubElement(line,'UnifOfMeasure')
			unifofmeasure.text = facturaitem.uom

			unitprice = ET.SubElement(line,'UnitPrice')
			unitprice.text = str(facturaitem.rate)

			taxbase = ET.SubElement(line,'TaxBase')
			taxbase.text = str(facturaitem.net_rate)

			taxpointdate = ET.SubElement(line,'TaxPointDate')
			dn = frappe.db.sql(""" select * from `tabDelivery Note` where name = %s """,(facturaitem.delivery_note), as_dict=True)
			print 'DNnnnn'
			print dn
			if dn:
				taxpointdate.text = dn[0].posting_date.strftime("%Y-%m-%d")	#DN

			#Against .. in case of change or DN ?????
			#references
			references = ET.SubElement(line,'References')
			reference = ET.SubElement(references,'Reference')
			if factura.return_against != None:
				reference.text = factura.return_against

			reason = ET.SubElement(references,'Reason')

			description = ET.SubElement(line,'Description')
			description.text = facturaitem.item_description

			#productserialnumber
			productserialnumber = ET.SubElement(line,'ProductSerialNumber')
			serialnumber = ET.SubElement(productserialnumber,'SerialNumber')
			serialnumber.text = facturaitem.serial_no

			###If invoice was cancelled or deleted should not add...!!!!!
			if factura.status !="Cancelled" and factura.docstatus != 2:
				debitamount = ET.SubElement(line,'DebitAmount')
				debitamount.text = str(facturaitem.amount)

				creditamount = ET.SubElement(line,'CreditAmount')
				#POR VER SE TEM....

			#tax
			taxes = ET.SubElement(line,'Taxes')
			
			### TAX por PRODUTO OU SERVICO

			#procura no recibo pelo IS
			#recibos = frappe.db.sql(""" select * from `tabPayment Entry` where parent = %s """,(factura.name), as_dict=True)
			recibosreferencias = frappe.db.sql(""" select * from `tabPayment Entry Reference` where reference_doctype = 'sales invoice' and docstatus = 1 and reference_name = %s """,(factura.name), as_dict=True)
			print 'recibos refenrecias'
			print factura.name
			print recibosreferencias
			if factura.name == 'FT0029/18-1':
				print 'TEM IPC'
				print facturaitem.imposto_de_consumo
				

			if facturaitem.imposto_de_consumo:	#Caso tem IPC or IVA

				if recibosreferencias:
					recibos = frappe.db.sql(""" select * from `tabPayment Entry` where name = %s """,(recibosreferencias[0].parent), as_dict=True)
					print 'recibos'
					print recibosreferencias[0].parent
					print recibos

					entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='payment entry' and company = %s and voucher_no = %s """,(empresa.name,recibosreferencias[0].parent), as_dict=True)

					print 'entradasgl+++++'

					#print entradasgl
					#return


					if entradasgl:
						for entradagl in entradasgl:

							print entradagl.account
							print entradagl.credit_in_account_currency
							if "34210000" in entradagl.account:
								tax = ET.SubElement(taxes,'Tax')
								taxtype = ET.SubElement(tax,'TaxType')

								taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
								taxcountryregion.text = "AO"

								#imposto de producao e consumo IPC
								taxtype.text = "NS"
								taxcode = ET.SubElement(tax,'TaxCode')
								taxcode.text = "NS"

								retn = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 and name  = 'ipc' """,as_dict=True)
								print retn


								taxpercentage = ET.SubElement(tax,'TaxPercentage')
								taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

								taxamount = ET.SubElement(tax,'TaxAmount')
								taxamount.text = str(entradagl.credit) 		


							elif "34710000" in entradagl.account:
								tax = ET.SubElement(taxes,'Tax')
								taxtype = ET.SubElement(tax,'TaxType')

								taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
								taxcountryregion.text = "AO"

								#imposto de selo
								taxtype.text = "IS"
								taxcode = ET.SubElement(tax,'TaxCode')
								taxcode.text = "NS"

								retn = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 and name  like '%%selo' """,as_dict=True)
								print retn


								taxpercentage = ET.SubElement(tax,'TaxPercentage')
								taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

								taxamount = ET.SubElement(tax,'TaxAmount')
								taxamount.text = str(entradagl.credit) 		


							elif "34140000" in entradagl.account:
								tax = ET.SubElement(taxes,'Tax')
								taxtype = ET.SubElement(tax,'TaxType')

								taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
								taxcountryregion.text = "AO"

								#retencao na fonte
								taxtype.text = "NS"
								taxcode = ET.SubElement(tax,'TaxCode')
								taxcode.text = "NS"

								retn = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 and name  like '%%fonte' """,as_dict=True)
								print retn


								taxpercentage = ET.SubElement(tax,'TaxPercentage')
								taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

								taxamount = ET.SubElement(tax,'TaxAmount')
								taxamount.text = str(entradagl.debit) 		



							elif "IVA" in entradagl.account:
								tax = ET.SubElement(taxes,'Tax')
								taxtype = ET.SubElement(tax,'TaxType')

								taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
								taxcountryregion.text = "AO"

								#IVA	ainda por rever
								taxtype.text = "IVA"
								taxcode = ET.SubElement(tax,'TaxCode')
								taxcode.text = "NOR"

							#else:
							#	taxtype.text = "NS"
							#	taxcode = ET.SubElement(tax,'TaxCode')
							#	taxcode.text = "NS"


								taxpercentage = ET.SubElement(tax,'TaxPercentage')
								taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

								taxamount = ET.SubElement(tax,'TaxAmount')
								taxamount.text = str(entradagl.credit) 		
			
							#return			

			taxexemptionreason = ET.SubElement(line,'TaxExemptionReason')
			taxexemptioncode = ET.SubElement(line,'TaxExemptionCode')
			settlementamount = ET.SubElement(line,'SettlementAmount')

			#customsinformation
			customsinformation = ET.SubElement(line,'CustomsInformation')
			arcno = ET.SubElement(customsinformation,'ARCNo')
			iecamount = ET.SubElement(customsinformation,'IECAmount')


		'''
		#documenttotals
		documenttotals = ET.SubElement(invoice,'DocumentTotals')

		inputtax = ET.SubElement(documenttotals,'InputTax')	# IVA
		taxbase = ET.SubElement(documenttotals,'TaxBase')	# 

		grosstotal = ET.SubElement(documenttotals,'GrossTotal')
		if factura.rounded_total:
			grosstotal.text = str(factura.rounded_total)		#Total Factura + impostos.... por ir buscar
		else:
			grosstotal.text = "0.00"

		deductibletax = ET.SubElement(documenttotals,'DeductibleTax')
		deductiblepercentage = ET.SubElement(documenttotals,'DeductiblePercentage')
		currencycode = ET.SubElement(documenttotals,'CurrencyCode')
		currencyamount = ET.SubElement(documenttotals,'CurrencyAmount')

		operationtype = ET.SubElement(documenttotals,'OperationType')
		#How to know if is CMN-compras nacional PSN-prestacao nacional PSN-prestacao estrangeiro OBN-outros bens ICN-investimento


		'''
		print 'factura Referencia'
		if factura.docstatus != 2:
			salestaxescharges = frappe.db.sql(""" select * from `tabSales Taxes and Charges` where parent = %s """,(factura.name),as_dict=True)
			print salestaxescharges

			if salestaxescharges: 
				print salestaxescharges[0].tax_amount
				taxpayable.text = str(salestaxescharges[0].tax_amount) 		#por ir buscar 


		#if retencao.credit_in_account_currency:
		#	taxpayable.text = str(retencao.credit_in_account_currency) 		#por ir buscar 

		nettotal = ET.SubElement(documenttotals,'NetTotal')
		nettotal.text = str(factura.net_total)		#Sem Impostos Total Factura

		####ONLY IF NOT AOA .... POR VERIFICAR
		#currency
		currency = ET.SubElement(documenttotals,'Currency')
		currencycode = ET.SubElement(currency,'CurrencyCode')

		currencyamount = ET.SubElement(currency,'CurrencyAmount')
		#currencyamount.text = str(factura.rounded_total)		#Total Factura + impostos.... por ir buscar

		exchangerate = ET.SubElement(currency,'ExchangeRate')

		#settlement
		settlement = ET.SubElement(documenttotals,'Settlement')
		settlementdiscount = ET.SubElement(settlement,'SettlementDiscount')
		settlementamount = ET.SubElement(settlement,'SettlementAmount')
		settlementdate = ET.SubElement(settlement,'SettlementDate')
		paymentterms = ET.SubElement(settlement,'PaymentTerms')

		#payment
		payment = ET.SubElement(documenttotals,'Payment')


		if recibosreferencias:
			recibos = frappe.db.sql(""" select * from `tabPayment Entry` where name = %s """,(recibosreferencias[0].parent), as_dict=True)
			print 'recibos'
			print recibosreferencias[0].parent
			print recibos

			for recibo in recibos:
				paymentmechanism = ET.SubElement(payment,'PaymentMechanism')				

				if "Transferência Bancária" in recibo.mode_of_payment:
					paymentmechanism.text = "TB"
				elif "Cash" in recibo.mode_of_payment:					
					paymentmechanism.text = "NU"

				elif "TPA" in recibo.mode_of_payment:					
					paymentmechanism.text = "CD"

				paymentamount = ET.SubElement(payment,'PaymentAmount')
				paymentamount.text = str(recibo.paid_amount)

				paymentdate = ET.SubElement(payment,'PaymentDate')
				paymentdate.text = recibo.posting_date.strftime("%Y-%m-%d")

		#witholdingtax
		withholdingtax = ET.SubElement(invoice,'WithholdingTax')

		if recibosreferencias:
			recibos = frappe.db.sql(""" select * from `tabPayment Entry` where name = %s """,(recibosreferencias[0].parent), as_dict=True)
			print 'recibos'
			print recibosreferencias[0].parent
			print recibos

			entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='payment entry' and company = %s and voucher_no = %s """,(empresa.name,recibosreferencias[0].parent), as_dict=True)

			print 'entradasgl'
			print entradasgl



			if entradasgl:
				for entradagl in entradasgl:


					print 'conta ', entradagl.account
					if "34710000" in entradagl.account:
						#imposto selo
						withholdingtaxtype = ET.SubElement(withholdingtax,'WithholdingTaxType')
						withholdingtaxtype.text = "IS"

						withholdingtaxdescription = ET.SubElement(withholdingtax,'WithholdingTaxDescription')
						withholdingtaxdescription.text = entradagl.account

						withholdingtaxamount = ET.SubElement(withholdingtax,'WithholdingTaxAmount')
						withholdingtaxamount.text = str(entradagl.credit)

					elif "34120000" in entradagl.account:
						#imposto industrial
						withholdingtaxtype = ET.SubElement(withholdingtax,'WithholdingTaxType')
						withholdingtaxtype.text = "II"

						withholdingtaxdescription = ET.SubElement(withholdingtax,'WithholdingTaxDescription')
						withholdingtaxdescription.text = entradagl.account

						withholdingtaxamount = ET.SubElement(withholdingtax,'WithholdingTaxAmount')
						withholdingtaxamount.text = str(entradagl.credit_in_account_currency)

					elif "34310000" in entradagl.account:
						#IRT
						withholdingtaxtype = ET.SubElement(withholdingtax,'WithholdingTaxType')
						withholdingtaxtype.text = "IRT"

						withholdingtaxdescription = ET.SubElement(withholdingtax,'WithholdingTaxDescription')
						withholdingtaxdescription.text = entradagl.account

						withholdingtaxamount = ET.SubElement(withholdingtax,'WithholdingTaxAmount')
						withholdingtaxamount.text = str(entradagl.credit_in_account_currency)

		'''

	#END OF BuyingInvoices
	#create MovimentofGoods

	#MovementOfGoods
	movementofgoods = ET.SubElement(sourcedocuments,'MovementOfGoods')

	numberofmovementlines = ET.SubElement(movementofgoods,'NumberOfMovimentLines')
	totalquantityissued = ET.SubElement(movementofgoods,'TotalQuantityIssued')

	#get delivery notes / items and count during the period.

	#guiasremessa = frappe.db.sql(""" select * from `tabDelivery Note` where company = %s and posting_date >= %s and posting_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)

	#primeirodiames = '2019-03-01'
	#ultimodiames = '2019-03-01'

	guiasremessa = frappe.db.sql(""" select count(dn.name), sum(dni.qty) from `tabDelivery Note Item` dni join `tabDelivery Note` dn on dni.parent = dn.name where dn.company = %s and dn.docstatus <> 0 and dn.posting_date >= %s and dn.posting_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)


	print guiasremessa

	if int(guiasremessa[0]['count(dn.name)']) !=0:
		print 'num linhas ',guiasremessa[0]['count(dn.name)']

		numberofmovementlines.text = str(guiasremessa[0]['count(dn.name)'])

	#	guiasremessaitems = frappe.db.sql(""" select * from `tabDelivery Note Item` where parent = %s """,(guiasremessa.name), as_dict=True)



		print 'Qtys ',guiasremessa[0]['sum(dni.qty)']
		totalquantityissued.text = str(guiasremessa[0]['sum(dni.qty)'])

		

		guiasremessa = frappe.db.sql(""" select * from `tabDelivery Note` where company = %s and docstatus <> 0 and posting_date >= %s and posting_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)

		for guiaremessa in guiasremessa:
			stockmovement = ET.SubElement(movementofgoods,'StockMovement')
			documentnumber = ET.SubElement(stockmovement,'DocumentNumber')
			documentnumber.text = str(guiaremessa.name)

			#documentnumberunique = ET.SubElement(stockmovement,'DocumentNumberUnique')
			#documentnumberunique.text = 0	#default

			documentstatus = ET.SubElement(stockmovement,'DocumentStatus')
			movementstatus = ET.SubElement(documentstatus,'MovementStatus')
			if guiaremessa.status == 'Completed' and guiaremessa.docstatus == 1:
				#pago
				movementstatus.text = "F"
			elif guiaremessa.status == 'To bill' and (guiaremessa.docstatus == 1 or guiaremessa.docstatus == 2):
				#por pagar
				movementstatus.text = "N"
			elif guiaremessa.status == 'Cancelled' and guiaremessa.docstatus == 2:
				#cancelled
				movementstatus.text = "A"
			elif guiaremessa.status == 'Draft' and guiaremessa.docstatus == 0:
				#Draft
				movementstatus.text = "N"

			movementstatusdate = ET.SubElement(documentstatus,'MovementStatusDate')
			movementstatusdate.text = guiaremessa.modified.strftime("%Y-%m-%dT%H:%M:%S")

			reason = ET.SubElement(documentstatus,'Reason')
			sourceid = ET.SubElement(documentstatus,'SourceID')
			sourceid.text = guiaremessa.modified_by

			sourcebilling = ET.SubElement(documentstatus,'SourceBilling')
			sourcebilling.text = "P"	#default feito pela APP


			movementofgoodshash = ET.SubElement(stockmovement,'Hash')
			movementofgoodshash.text = 0	#default nossa app nao precisa.

			movementofgoodshashcontrol = ET.SubElement(stockmovement,'HashControl')
			movementofgoodshashcontrol.text = "Nao validado pela AGT"	#default for now


			period = ET.SubElement(stockmovement,'Period')
			period.text = str(guiaremessa.modified.month)	#last modified month

			movementdate = ET.SubElement(stockmovement,'MovementDate')
			movementdate.text = guiaremessa.modified.strftime("%Y-%m-%dT%H:%M:%S")

			movementtype = ET.SubElement(stockmovement,'MovementType')
			movementtype.text = "GR"	#default Delivery Note

			systementrydate = ET.SubElement(stockmovement,'SystemEntryDate')
			systementrydate.text = guiaremessa.creation.strftime("%Y-%m-%dT%H:%M:%S")

			#Get GL; TO CHECK as OURS GENS two or more GLs

			#transactionid = ET.SubElement(stockmovement,'TransactionID')

			transactions = ET.SubElement(stockmovement,'Transactions')

			entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='delivery note' and company = %s and voucher_no = %s """,(empresa.name,guiaremessa.name), as_dict=True)
			if entradasgl:
				for entradagl in entradasgl:
					print 'transactions ids'
					print entradagl
					transactionid = ET.SubElement(transactions,'TransactionID')
					transactionid.text = entradagl.name	#entrada GL;single invoice can generate more than 2GL




			customerid = ET.SubElement(stockmovement,'CustomerID')
			cliente_endereco = angola.get_all_enderecos_a("Customer",guiaremessa.customer)
			customerid.text = guiaremessa.customer

			supplierid = ET.SubElement(stockmovement,'SupplierID')
			#For now EMPTY

			sourceid = ET.SubElement(stockmovement,'SourceID')
			sourceid.text = guiaremessa.owner

			eaccode = ET.SubElement(stockmovement,'EACCode')

			movementcomments = ET.SubElement(stockmovement,'MovementComments')

			shipto = ET.SubElement(stockmovement,'ShipTo')
			deliveryid = ET.SubElement(shipto,'DeliveryID')
			deliverydate = ET.SubElement(shipto,'DeliveryDate')
			warehouseid = ET.SubElement(shipto,'WarehouseID')
			locationid = ET.SubElement(shipto,'LocationId')

			address = ET.SubElement(shipto,'Address')
			buildingnumber = ET.SubElement(address,'BuildingNumber')
			streetname = ET.SubElement(address,'StreetName')
			if cliente_endereco:
				streetname.text = cliente_endereco.address_line1

			addressdetail = ET.SubElement(address,'AddressDetail')
			if cliente_endereco:
				addressdetail.text = cliente_endereco.address_line1

			city = ET.SubElement(address,'City')
			if cliente_endereco:
				city.text = cliente_endereco.city

			postalcode = ET.SubElement(address,'PostalCode')
			if cliente_endereco:
				postalcode.text = cliente_endereco.pincode

			province = ET.SubElement(address,'Province')
			if cliente_endereco:
				province.text = cliente_endereco.city

			country = ET.SubElement(address,'Country')
			if cliente_endereco:
				if cliente_endereco.country == 'Angola':
					country.text = "AO"
				else:
					country.text = cliente_endereco.country



			shipfrom = ET.SubElement(stockmovement,'ShipFrom')
			deliveryid = ET.SubElement(shipfrom,'DeliveryID')
			deliverydate = ET.SubElement(shipfrom,'DeliveryDate')
			warehouseid = ET.SubElement(shipfrom,'WarehouseID')
			locationid = ET.SubElement(shipfrom,'LocationID')

			address = ET.SubElement(shipfrom,'Address')
			buildingnumber = ET.SubElement(address,'BuildingNumber')
			streetname = ET.SubElement(address,'StreetName')
			if cliente_endereco:
				streetname.text = cliente_endereco.address_line1

			addressdetail = ET.SubElement(address,'AddressDetail')
			if cliente_endereco:
				addressdetail.text = cliente_endereco.address_line1

			city = ET.SubElement(address,'City')
			if cliente_endereco:
				city.text = cliente_endereco.city

			postalcode = ET.SubElement(address,'PostalCode')
			if cliente_endereco:
				postalcode.text = cliente_endereco.pincode

			province = ET.SubElement(address,'Province')
			if cliente_endereco:
				province.text = cliente_endereco.city

			country = ET.SubElement(address,'Country')
			if cliente_endereco:
				if cliente_endereco.country == 'Angola':
					country.text = "AO"
				else:
					country.text = cliente_endereco.country



			movementendtime = ET.SubElement(stockmovement,'MovementEndTime')
			movementstarttime = ET.SubElement(stockmovement,'MovementStartTime')
			agtdoccodeid = ET.SubElement(stockmovement,'AGTDocCodeID')

			#Itens

			guiasremessaitems = frappe.db.sql(""" select * from `tabDelivery Note Item` where parent = %s order by idx """,(guiaremessa.name), as_dict=True)
			for guiaremessaitem in guiasremessaitems:
				line = ET.SubElement(stockmovement,'Line')

				linenumber = ET.SubElement(line,'LineNumber')
				linenumber.text = str(guiaremessaitem.idx)

				orderreferences = ET.SubElement(line,'OrderReferences')
				originatingon = ET.SubElement(orderreferences,'OriginatingON')
				orderdate = ET.SubElement(orderreferences,'OrderDate')

				productcode = ET.SubElement(line,'ProductCode')
				productcode.text = guiaremessaitem.item_code

				productdescription = ET.SubElement(line,'ProductDescription')
				productdescription.text = guiaremessaitem.item_name

				quantity = ET.SubElement(line,'Quantity')
				quantity.text = str(guiaremessaitem.qty)

				unitofmeasure = ET.SubElement(line,'UnifOfMeasure')
				unitofmeasure.text = guiaremessaitem.uom

				unitprice = ET.SubElement(line,'UnitPrice')
				unitprice.text = str(guiaremessaitem.rate) 

				description = ET.SubElement(line,'Description')
				description.text = guiaremessaitem.description

				productserialnumber = ET.SubElement(line,'ProductSerialNumber')
				serialnumber = ET.SubElement(productserialnumber,'SerialNumber')
				serialnumber.text = guiaremessaitem.serial_no

				#Sera que is o valor Valuation TAX or amount!!!
				debitamount = ET.SubElement(line,'DebitAmount')
				debitamount.text = 0

				creditamount = ET.SubElement(line,'CreditAmount')
				creditamount.text = 0

				tax = ET.SubElement(line,'Tax')
				taxtype = ET.SubElement(tax,'TaxType')
				taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
				taxcode = ET.SubElement(tax,'TaxCode')
				taxpercentage = ET.SubElement(tax,'TaxPercentage')

				taxexemptionreason = ET.SubElement(line,'TaxExemptionReason')
				taxexemptioncode = ET.SubElement(line,'TaxExemptionCode')
				settlementamount = ET.SubElement(line,'SettlementAmount')

				#customsinformation
				customsinformation = ET.SubElement(line,'CustomsInformation')
				arcno = ET.SubElement(customsinformation,'ARCNo')
				iecamount = ET.SubElement(customsinformation,'IECAmount')

			#documenttotals
			documenttotals = ET.SubElement(stockmovement,'DocumentTotals')
			taxpayable = ET.SubElement(documenttotals,'TaxPayable')
			nettotal = ET.SubElement(documenttotals,'NetTotal')
			grosstotal = ET.SubElement(documenttotals,'GrossTotal')
			#currency if NOT AOA
			currency = ET.SubElement(documenttotals,'Currency')
			currencycode = ET.SubElement(currency,'CurrencyCode')
			currencyamount = ET.SubElement(currency,'CurrencyAmount')
			exchangerate = ET.SubElement(currency,'ExchangeRate')


	#END OF MovementOfGoods



	#create WorkingDocuments...

	#WorkingDocuments
	'''
		Campo Workdate, SystemEntryDate, DocumentNumber, GrossTotal, Last Hash from previous Doc.
	'''


	workingdocuments = ET.SubElement(sourcedocuments,'WorkingDocuments')

	numberofentries = ET.SubElement(workingdocuments,'NumberOfEntries')

	totaldebit = ET.SubElement(workingdocuments,'TotalDebit')


	#Debitos ou pagamentos
	facturas = frappe.db.sql(""" select count(name), sum(rounded_total) from `tabQuotation` where company = %s and (status != 'Draft' and status != 'Cancelled') and transaction_date >= %s and transaction_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)


	print facturas
	print int(facturas[0]['count(name)'])


	##### POR FAZER
	totalcredit = ET.SubElement(workingdocuments,'TotalCredit')

	####### POR FAZER

	if int(facturas[0]['count(name)']) !=0:
		numberofentries.text = str(int(facturas[0]['count(name)']))
		totaldebit.text = str(int(facturas[0]['sum(rounded_total)']))

	#Creditos ou devolucoes
	facturas = frappe.db.sql(""" select count(name), sum(rounded_total) from `tabQuotation` where company = %s and (status != 'Draft' and status != 'Cancelled') and transaction_date >= %s and transaction_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)
	if int(facturas[0]['count(name)']) !=0:
		totalcredit.text = str(int(facturas[0]['sum(rounded_total)']))



	#invoice
	facturas = frappe.db.sql(""" select * from `tabQuotation` where company = %s and (status != 'Draft' and status != 'Cancelled') and transaction_date >= %s and transaction_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)

	for factura in facturas:
		print factura.name
		print factura.creation
		print factura.modified

		invoice = ET.SubElement(workingdocuments,'WorkDocument')

		invoiceno = ET.SubElement(invoice,'DocumentNumber')
		invoiceno.text = str(factura.name)

		#documentstatus
		documentstatus = ET.SubElement(invoice,'DocumentStatus')
		invoicestatus = ET.SubElement(documentstatus,'WorkStatus')
		if factura.status =="Paid" and factura.docstatus == 1:
			invoicestatus.text = "F"	#Facturado
		elif factura.status =="Cancelled" and factura.docstatus == 2:
			invoicestatus.text = "A"	#Anulado

		else:
			invoicestatus.text = "N"	#Normal


		invoicestatusdate = ET.SubElement(documentstatus,'WorkStatusDate')
		#Will be needed to add T between date and time!!!!!!!
		invoicestatusdate.text = factura.modified.strftime("%Y-%m-%dT%H:%M:%S")	#ultima change

		reason = ET.SubElement(documentstatus,'Reason')
		#Pode ser os Comments when deleted the Documents ....
		if factura.remarks != 'No Remarks' and factura.remarks != 'Sem Observações':
			reason.text = factura.remarks
		elif factura._comments != None:
			reason.text = factura._comments

		sourceid = ET.SubElement(documentstatus,'SourceID')
		sourceid.text = factura.modified_by	#User

		sourcebilling = ET.SubElement(documentstatus,'SourceBilling')
		sourcebilling.text = "P"	#Default

		salesinvoicehash = ET.SubElement(invoice,'Hash')
		salesinvoicehash.text = 0	#por rever...

		salesinvoicehashcontrol = ET.SubElement(invoice,'HashControl')
		salesinvoicehashcontrol.text = "Nao validado pela AGT"	#default for now

		period = ET.SubElement(invoice,'Period')
		period.text = str(factura.modified.month)	#last modified month

		invoicedate = ET.SubElement(invoice,'WorkDate')
		invoicedate.text = factura.transaction_date.strftime("%Y-%m-%d")	#posting date

		invoicetype = ET.SubElement(invoice,'WorkType')
		print 'NC ', factura.return_against
		#if factura.is_pos == 1:
		#	invoicetype.text = "FR"	#POS deve ser FR ou TV
		#elif factura.return_against != None:
		#	invoicetype.text = "NC"	#Retorno / Credit Note

		#else:
		invoicetype.text = "PF"	#default Proforma

		'''
		#specialRegimes
		specialregimes = ET.SubElement(invoice,'SpecialRegimes')
		selfbillingindicator = ET.SubElement(specialregimes,'SelfBillingIndicator')
		selfbillingindicator.text = 0	#default 

		cashvatschemeindicator = ET.SubElement(specialregimes,'CashVATSchemeIndicator')
		cashvatschemeindicator.text = 0	#default 

		thirdpartiesbillingindicator = ET.SubElement(specialregimes,'ThirdPartiesBillingIndicator')
		thirdpartiesbillingindicator.text = 0	#default 
		'''

		sourceid = ET.SubElement(invoice,'SourceID')
		sourceid.text = factura.owner	#created by

		eaccode = ET.SubElement(invoice,'EACCode')

		systementrydate = ET.SubElement(invoice,'SystemEntryDate')
		systementrydate.text = factura.creation.strftime("%Y-%m-%dT%H:%M:%S")	#creation date

		transactions = ET.SubElement(invoice,'Transactions')
		'''
		entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='sales invoice' and company = %s and voucher_no = %s """,(empresa.name,factura.name), as_dict=True)
		if entradasgl:
			for entradagl in entradasgl:
				print 'transactions ids'
				print entradagl
				transactionid = ET.SubElement(transactions,'TransactionID')
				transactionid.text = entradagl.name	#entrada GL;single invoice can generate more than 2GL
		'''
		customerid = ET.SubElement(invoice,'CustomerID')
		customerid.text = factura.customer	#cliente

		'''
		#shipto
		shipto = ET.SubElement(invoice,'ShipTo')
		deliveryid = ET.SubElement(shipto,'DeliveryID')
		deliverydate = ET.SubElement(shipto,'DeliveryDate')
		warehouseid = ET.SubElement(shipto,'WarehouseID')
		locationid = ET.SubElement(shipto,'LocationID')
		#address
		address = ET.SubElement(shipto,'Address')	
		buildingnumber = ET.SubElement(address,'BuildingNumber')
		streetname = ET.SubElement(address,'StreetName')
		addressdetail = ET.SubElement(address,'AddressDetail')
		city = ET.SubElement(address,'City')
		postalcode = ET.SubElement(address,'PostalCode')
		province = ET.SubElement(address,'Province')
		country = ET.SubElement(address,'Country')
		#shipfrom
		shipfrom = ET.SubElement(invoice,'ShipFrom')
		deliveryid = ET.SubElement(shipfrom,'DeliveryID')
		deliverydate = ET.SubElement(shipfrom,'DeliveryDate')
		warehouseid = ET.SubElement(shipfrom,'WarehouseID')
		locationid = ET.SubElement(shipfrom,'LocationID')
		#address
		address = ET.SubElement(shipfrom,'Address')
		buildingnumber = ET.SubElement(address,'BuildingNumber')
		streetname = ET.SubElement(address,'StreetName')
		addressdetail = ET.SubElement(address,'AddressDetail')
		city = ET.SubElement(address,'City')
		postalcode = ET.SubElement(address,'PostalCode')
		province = ET.SubElement(address,'Province')
		country = ET.SubElement(address,'Country')

		movementendtime = ET.SubElement(invoice,'MovementEndTime')
		movementstarttime = ET.SubElement(invoice,'MovementStartTime')
		'''

		#line
		line = ET.SubElement(invoice,'Line')
		facturaitems = frappe.db.sql(""" select * from `tabQuotation Item` where parent = %s order by idx """,(factura.name), as_dict=True)
		
		for facturaitem in facturaitems:

			linenumber = ET.SubElement(line,'LineNumber')
			linenumber.text = str(facturaitem.idx)

			#Quotation has no SO 
			#orderreferences
			orderreferences = ET.SubElement(line,'OrderReferences')
			originatingon = ET.SubElement(orderreferences,'OriginatingON')
			orderdate = ET.SubElement(orderreferences,'OrderDate')
			#if facturaitem.sales_order:
			#	originatingon.text = facturaitem.sales_order
			#	ordemvenda = frappe.db.sql(""" select * from `tabSales Order` where name = %s """,(facturaitem.sales_order), as_dict=True)
			#	orderdate.text = ordemvenda[0].transaction_date.strftime("%Y-%m-%d")



			productcode = ET.SubElement(line,'ProductCode')
			productcode.text = facturaitem.item_code

			productdescription = ET.SubElement(line,'ProductDescription')
			productdescription.text = facturaitem.item_name

			quantity = ET.SubElement(line,'Quantity')
			quantity.text = str(facturaitem.qty)


			unifofmeasure = ET.SubElement(line,'UnifOfMeasure')
			unifofmeasure.text = facturaitem.uom

			unitprice = ET.SubElement(line,'UnitPrice')
			unitprice.text = str(facturaitem.rate)

			taxbase = ET.SubElement(line,'TaxBase')
			taxbase.text = str(facturaitem.net_rate)

			taxpointdate = ET.SubElement(line,'TaxPointDate')
			dn = frappe.db.sql(""" select * from `tabDelivery Note` where name = %s """,(facturaitem.delivery_note), as_dict=True)
			print 'DNnnnn'
			print dn
			if dn:
				taxpointdate.text = dn[0].transaction_date.strftime("%Y-%m-%d")	#DN

			#Against .. in case of change or DN ?????
			#references
			references = ET.SubElement(line,'References')
			reference = ET.SubElement(references,'Reference')
			if factura.return_against != None:
				reference.text = factura.return_against

			reason = ET.SubElement(references,'Reason')

			description = ET.SubElement(line,'Description')
			description.text = facturaitem.item_description

			#productserialnumber
			productserialnumber = ET.SubElement(line,'ProductSerialNumber')
			serialnumber = ET.SubElement(productserialnumber,'SerialNumber')
			serialnumber.text = facturaitem.serial_no

			###If invoice was cancelled or deleted should not add...!!!!!
			if factura.status !="Cancelled" and factura.docstatus != 2:
				debitamount = ET.SubElement(line,'DebitAmount')
				debitamount.text = str(facturaitem.amount)

				creditamount = ET.SubElement(line,'CreditAmount')
				#POR VER SE TEM....

			#tax
			taxes = ET.SubElement(line,'Taxes')
			
			### TAX por PRODUTO OU SERVICO

			#procura no recibo pelo IS
			#recibos = frappe.db.sql(""" select * from `tabPayment Entry` where parent = %s """,(factura.name), as_dict=True)
			recibosreferencias = frappe.db.sql(""" select * from `tabPayment Entry Reference` where reference_doctype = 'sales invoice' and docstatus = 1 and reference_name = %s """,(factura.name), as_dict=True)
			print 'recibos refenrecias'
			print factura.name
			print recibosreferencias
			if factura.name == 'FT0029/18-1':
				print 'TEM IPC'
				print facturaitem.imposto_de_consumo
				

			if facturaitem.imposto_de_consumo:	#Caso tem IPC or IVA

				if recibosreferencias:
					recibos = frappe.db.sql(""" select * from `tabPayment Entry` where name = %s """,(recibosreferencias[0].parent), as_dict=True)
					print 'recibos'
					print recibosreferencias[0].parent
					print recibos

					entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='payment entry' and company = %s and voucher_no = %s """,(empresa.name,recibosreferencias[0].parent), as_dict=True)

					print 'entradasgl+++++'

					#print entradasgl
					#return


					if entradasgl:
						for entradagl in entradasgl:

							print entradagl.account
							print entradagl.credit_in_account_currency
							if "34210000" in entradagl.account:
								tax = ET.SubElement(taxes,'Tax')
								taxtype = ET.SubElement(tax,'TaxType')

								taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
								taxcountryregion.text = "AO"

								#imposto de producao e consumo IPC
								taxtype.text = "NS"
								taxcode = ET.SubElement(tax,'TaxCode')
								taxcode.text = "NS"

								retn = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 and name  = 'ipc' """,as_dict=True)
								print retn


								taxpercentage = ET.SubElement(tax,'TaxPercentage')
								taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

								taxamount = ET.SubElement(tax,'TaxAmount')
								taxamount.text = str(entradagl.credit) 		


							elif "34710000" in entradagl.account:
								tax = ET.SubElement(taxes,'Tax')
								taxtype = ET.SubElement(tax,'TaxType')

								taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
								taxcountryregion.text = "AO"

								#imposto de selo
								taxtype.text = "IS"
								taxcode = ET.SubElement(tax,'TaxCode')
								taxcode.text = "NS"

								retn = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 and name  like '%%selo' """,as_dict=True)
								print retn


								taxpercentage = ET.SubElement(tax,'TaxPercentage')
								taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

								taxamount = ET.SubElement(tax,'TaxAmount')
								taxamount.text = str(entradagl.credit) 		


							elif "34140000" in entradagl.account:
								tax = ET.SubElement(taxes,'Tax')
								taxtype = ET.SubElement(tax,'TaxType')

								taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
								taxcountryregion.text = "AO"

								#retencao na fonte
								taxtype.text = "NS"
								taxcode = ET.SubElement(tax,'TaxCode')
								taxcode.text = "NS"

								retn = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 and name  like '%%fonte' """,as_dict=True)
								print retn


								taxpercentage = ET.SubElement(tax,'TaxPercentage')
								taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

								taxamount = ET.SubElement(tax,'TaxAmount')
								taxamount.text = str(entradagl.debit) 		



							elif "IVA" in entradagl.account:
								tax = ET.SubElement(taxes,'Tax')
								taxtype = ET.SubElement(tax,'TaxType')

								taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
								taxcountryregion.text = "AO"

								#IVA	ainda por rever
								taxtype.text = "IVA"
								taxcode = ET.SubElement(tax,'TaxCode')
								taxcode.text = "NOR"

							#else:
							#	taxtype.text = "NS"
							#	taxcode = ET.SubElement(tax,'TaxCode')
							#	taxcode.text = "NS"


								taxpercentage = ET.SubElement(tax,'TaxPercentage')
								taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

								taxamount = ET.SubElement(tax,'TaxAmount')
								taxamount.text = str(entradagl.credit) 		
			
							#return			

			taxexemptionreason = ET.SubElement(line,'TaxExemptionReason')
			taxexemptioncode = ET.SubElement(line,'TaxExemptionCode')
			settlementamount = ET.SubElement(line,'SettlementAmount')

			#customsinformation
			customsinformation = ET.SubElement(line,'CustomsInformation')
			arcno = ET.SubElement(customsinformation,'ARCNo')
			iecamount = ET.SubElement(customsinformation,'IECAmount')



		#documenttotals
		documenttotals = ET.SubElement(invoice,'DocumentTotals')

		taxpayable = ET.SubElement(documenttotals,'TaxPayable')
		print 'factura Referencia'
		if factura.docstatus != 2:
			salestaxescharges = frappe.db.sql(""" select * from `tabSales Taxes and Charges` where parent = %s """,(factura.name),as_dict=True)
			print salestaxescharges

			if salestaxescharges: 
				print salestaxescharges[0].tax_amount
				taxpayable.text = str(salestaxescharges[0].tax_amount) 		#por ir buscar 
			else:
				taxpayable.text = "0.00" 		#por ir buscar 



		#if retencao.credit_in_account_currency:
		#	taxpayable.text = str(retencao.credit_in_account_currency) 		#por ir buscar 

		nettotal = ET.SubElement(documenttotals,'NetTotal')
		nettotal.text = str(factura.net_total)		#Sem Impostos Total Factura

		grosstotal = ET.SubElement(documenttotals,'GrossTotal')
		grosstotal.text = str(factura.rounded_total)		#Total Factura + impostos.... por ir buscar

		####ONLY IF NOT AOA .... POR VERIFICAR
		#currency
		currency = ET.SubElement(documenttotals,'Currency')
		currencycode = ET.SubElement(currency,'CurrencyCode')

		currencyamount = ET.SubElement(currency,'CurrencyAmount')
		#currencyamount.text = str(factura.rounded_total)		#Total Factura + impostos.... por ir buscar

		exchangerate = ET.SubElement(currency,'ExchangeRate')


	#### Purchase ORDER
	#### Still need to update as Quotation already added numbers .... This should be the last to be ADDED for both Quotation and Purchase Order

	#numberofentries = ET.SubElement(workingdocuments,'NumberOfEntries')

	#totaldebit = ET.SubElement(workingdocuments,'TotalDebit')


	#Debitos ou pagamentos
	#facturas = frappe.db.sql(""" select count(name), sum(rounded_total) from `tabQuotation` where company = %s and (status = 'Paid' or status = 'Cancelled' ) and transaction_date >= %s and transaction_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)


	#print facturas
	#print int(facturas[0]['count(name)'])


	##### POR FAZER
	#totalcredit = ET.SubElement(workingdocuments,'TotalCredit')

	####### POR FAZER

	#if int(facturas[0]['count(name)']) !=0:
	#	numberofentries.text = str(int(facturas[0]['count(name)']))
	#	totaldebit.text = str(int(facturas[0]['sum(rounded_total)']))

	#Creditos ou devolucoes
	#facturas = frappe.db.sql(""" select count(name), sum(rounded_total) from `tabQuotation` where company = %s and (status = 'Return') and transaction_date >= %s and transaction_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)
	#if int(facturas[0]['count(name)']) !=0:
	#	totalcredit.text = str(int(facturas[0]['sum(rounded_total)']))



	#invoice
	facturas = frappe.db.sql(""" select * from `tabPurchase Order` where company = %s and status != 'Draft' and transaction_date >= %s and transaction_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)

	print 'purchase orders'

	for factura in facturas:
		print factura.name
		print factura.creation
		print factura.modified

		invoice = ET.SubElement(workingdocuments,'WorkDocument')

		invoiceno = ET.SubElement(invoice,'DocumentNumber')
		invoiceno.text = str(factura.name)

		#documentstatus
		documentstatus = ET.SubElement(invoice,'DocumentStatus')
		invoicestatus = ET.SubElement(documentstatus,'WorkStatus')
		if factura.status =="Cancelled" and factura.docstatus == 2:
			invoicestatus.text = "A"	#Anulado

		else:
			invoicestatus.text = "N"	#Normal


		invoicestatusdate = ET.SubElement(documentstatus,'WorkStatusDate')
		#Will be needed to add T between date and time!!!!!!!
		invoicestatusdate.text = factura.modified.strftime("%Y-%m-%dT%H:%M:%S")	#ultima change

		reason = ET.SubElement(documentstatus,'Reason')
		#Pode ser os Comments when deleted the Documents ....
		if factura.remarks != 'No Remarks' and factura.remarks != 'Sem Observações':
			reason.text = factura.remarks
		elif factura._comments != None:
			reason.text = factura._comments

		sourceid = ET.SubElement(documentstatus,'SourceID')
		sourceid.text = factura.modified_by	#User

		sourcebilling = ET.SubElement(documentstatus,'SourceBilling')
		sourcebilling.text = "P"	#Default

		salesinvoicehash = ET.SubElement(invoice,'Hash')
		salesinvoicehash.text = 0	#por rever...

		salesinvoicehashcontrol = ET.SubElement(invoice,'HashControl')
		salesinvoicehashcontrol.text = "Nao validado pela AGT"	#default for now

		period = ET.SubElement(invoice,'Period')
		period.text = str(factura.modified.month)	#last modified month

		invoicedate = ET.SubElement(invoice,'WorkDate')
		invoicedate.text = factura.transaction_date.strftime("%Y-%m-%d")	#posting date

		invoicetype = ET.SubElement(invoice,'WorkType')
		print 'NC ', factura.return_against
		#if factura.is_pos == 1:
		#	invoicetype.text = "FR"	#POS deve ser FR ou TV
		#elif factura.return_against != None:
		#	invoicetype.text = "NC"	#Retorno / Credit Note

		#else:
		invoicetype.text = "PF"	#default Proforma

		'''
		#specialRegimes
		specialregimes = ET.SubElement(invoice,'SpecialRegimes')
		selfbillingindicator = ET.SubElement(specialregimes,'SelfBillingIndicator')
		selfbillingindicator.text = 0	#default 

		cashvatschemeindicator = ET.SubElement(specialregimes,'CashVATSchemeIndicator')
		cashvatschemeindicator.text = 0	#default 

		thirdpartiesbillingindicator = ET.SubElement(specialregimes,'ThirdPartiesBillingIndicator')
		thirdpartiesbillingindicator.text = 0	#default 
		'''

		sourceid = ET.SubElement(invoice,'SourceID')
		sourceid.text = factura.owner	#created by

		eaccode = ET.SubElement(invoice,'EACCode')

		systementrydate = ET.SubElement(invoice,'SystemEntryDate')
		systementrydate.text = factura.creation.strftime("%Y-%m-%dT%H:%M:%S")	#creation date

		transactions = ET.SubElement(invoice,'Transactions')
		'''
		entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='sales invoice' and company = %s and voucher_no = %s """,(empresa.name,factura.name), as_dict=True)
		if entradasgl:
			for entradagl in entradasgl:
				print 'transactions ids'
				print entradagl
				transactionid = ET.SubElement(transactions,'TransactionID')
				transactionid.text = entradagl.name	#entrada GL;single invoice can generate more than 2GL
		'''
		customerid = ET.SubElement(invoice,'CustomerID')
		customerid.text = factura.supplier	#cliente

		'''
		#shipto
		shipto = ET.SubElement(invoice,'ShipTo')
		deliveryid = ET.SubElement(shipto,'DeliveryID')
		deliverydate = ET.SubElement(shipto,'DeliveryDate')
		warehouseid = ET.SubElement(shipto,'WarehouseID')
		locationid = ET.SubElement(shipto,'LocationID')
		#address
		address = ET.SubElement(shipto,'Address')	
		buildingnumber = ET.SubElement(address,'BuildingNumber')
		streetname = ET.SubElement(address,'StreetName')
		addressdetail = ET.SubElement(address,'AddressDetail')
		city = ET.SubElement(address,'City')
		postalcode = ET.SubElement(address,'PostalCode')
		province = ET.SubElement(address,'Province')
		country = ET.SubElement(address,'Country')
		#shipfrom
		shipfrom = ET.SubElement(invoice,'ShipFrom')
		deliveryid = ET.SubElement(shipfrom,'DeliveryID')
		deliverydate = ET.SubElement(shipfrom,'DeliveryDate')
		warehouseid = ET.SubElement(shipfrom,'WarehouseID')
		locationid = ET.SubElement(shipfrom,'LocationID')
		#address
		address = ET.SubElement(shipfrom,'Address')
		buildingnumber = ET.SubElement(address,'BuildingNumber')
		streetname = ET.SubElement(address,'StreetName')
		addressdetail = ET.SubElement(address,'AddressDetail')
		city = ET.SubElement(address,'City')
		postalcode = ET.SubElement(address,'PostalCode')
		province = ET.SubElement(address,'Province')
		country = ET.SubElement(address,'Country')

		movementendtime = ET.SubElement(invoice,'MovementEndTime')
		movementstarttime = ET.SubElement(invoice,'MovementStartTime')
		'''

		#line
		line = ET.SubElement(invoice,'Line')
		facturaitems = frappe.db.sql(""" select * from `tabPurchase Order Item` where parent = %s order by idx """,(factura.name), as_dict=True)
		
		for facturaitem in facturaitems:

			linenumber = ET.SubElement(line,'LineNumber')
			linenumber.text = str(facturaitem.idx)

			#Quotation has no SO 
			#orderreferences
			orderreferences = ET.SubElement(line,'OrderReferences')
			originatingon = ET.SubElement(orderreferences,'OriginatingON')
			orderdate = ET.SubElement(orderreferences,'OrderDate')
			#if facturaitem.sales_order:
			#	originatingon.text = facturaitem.sales_order
			#	ordemvenda = frappe.db.sql(""" select * from `tabSales Order` where name = %s """,(facturaitem.sales_order), as_dict=True)
			#	orderdate.text = ordemvenda[0].transaction_date.strftime("%Y-%m-%d")



			productcode = ET.SubElement(line,'ProductCode')
			productcode.text = facturaitem.item_code

			productdescription = ET.SubElement(line,'ProductDescription')
			productdescription.text = facturaitem.item_name

			quantity = ET.SubElement(line,'Quantity')
			quantity.text = str(facturaitem.qty)


			unifofmeasure = ET.SubElement(line,'UnifOfMeasure')
			unifofmeasure.text = facturaitem.uom

			unitprice = ET.SubElement(line,'UnitPrice')
			unitprice.text = str(facturaitem.rate)

			taxbase = ET.SubElement(line,'TaxBase')
			taxbase.text = str(facturaitem.net_rate)

			taxpointdate = ET.SubElement(line,'TaxPointDate')
			dn = frappe.db.sql(""" select * from `tabDelivery Note` where name = %s """,(facturaitem.delivery_note), as_dict=True)
			print 'DNnnnn'
			print dn
			if dn:
				taxpointdate.text = dn[0].transaction_date.strftime("%Y-%m-%d")	#DN

			#Against .. in case of change or DN ?????
			#references
			references = ET.SubElement(line,'References')
			reference = ET.SubElement(references,'Reference')
			if factura.return_against != None:
				reference.text = factura.return_against

			reason = ET.SubElement(references,'Reason')

			description = ET.SubElement(line,'Description')
			description.text = facturaitem.item_description

			#productserialnumber
			productserialnumber = ET.SubElement(line,'ProductSerialNumber')
			serialnumber = ET.SubElement(productserialnumber,'SerialNumber')
			serialnumber.text = facturaitem.serial_no

			###If invoice was cancelled or deleted should not add...!!!!!
			if factura.status !="Cancelled" and factura.docstatus != 2:
				debitamount = ET.SubElement(line,'DebitAmount')
				debitamount.text = str(facturaitem.amount)

				creditamount = ET.SubElement(line,'CreditAmount')
				#POR VER SE TEM....

			#tax
			taxes = ET.SubElement(line,'Taxes')
			
			### TAX por PRODUTO OU SERVICO

			#procura no recibo pelo IS
			#recibos = frappe.db.sql(""" select * from `tabPayment Entry` where parent = %s """,(factura.name), as_dict=True)
			recibosreferencias = frappe.db.sql(""" select * from `tabPayment Entry Reference` where reference_doctype = 'sales invoice' and docstatus = 1 and reference_name = %s """,(factura.name), as_dict=True)
			print 'recibos refenrecias'
			print factura.name
			print recibosreferencias
			if factura.name == 'FT0029/18-1':
				print 'TEM IPC'
				print facturaitem.imposto_de_consumo
				

			if facturaitem.imposto_de_consumo:	#Caso tem IPC or IVA

				if recibosreferencias:
					recibos = frappe.db.sql(""" select * from `tabPayment Entry` where name = %s """,(recibosreferencias[0].parent), as_dict=True)
					print 'recibos'
					print recibosreferencias[0].parent
					print recibos

					entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='payment entry' and company = %s and voucher_no = %s """,(empresa.name,recibosreferencias[0].parent), as_dict=True)

					print 'entradasgl+++++'

					#print entradasgl
					#return


					if entradasgl:
						for entradagl in entradasgl:

							print entradagl.account
							print entradagl.credit_in_account_currency
							if "34210000" in entradagl.account:
								tax = ET.SubElement(taxes,'Tax')
								taxtype = ET.SubElement(tax,'TaxType')

								taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
								taxcountryregion.text = "AO"

								#imposto de producao e consumo IPC
								taxtype.text = "NS"
								taxcode = ET.SubElement(tax,'TaxCode')
								taxcode.text = "NS"

								retn = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 and name  = 'ipc' """,as_dict=True)
								print retn


								taxpercentage = ET.SubElement(tax,'TaxPercentage')
								taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

								taxamount = ET.SubElement(tax,'TaxAmount')
								taxamount.text = str(entradagl.credit) 		


							elif "34710000" in entradagl.account:
								tax = ET.SubElement(taxes,'Tax')
								taxtype = ET.SubElement(tax,'TaxType')

								taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
								taxcountryregion.text = "AO"

								#imposto de selo
								taxtype.text = "IS"
								taxcode = ET.SubElement(tax,'TaxCode')
								taxcode.text = "NS"

								retn = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 and name  like '%%selo' """,as_dict=True)
								print retn


								taxpercentage = ET.SubElement(tax,'TaxPercentage')
								taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

								taxamount = ET.SubElement(tax,'TaxAmount')
								taxamount.text = str(entradagl.credit) 		


							elif "34140000" in entradagl.account:
								tax = ET.SubElement(taxes,'Tax')
								taxtype = ET.SubElement(tax,'TaxType')

								taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
								taxcountryregion.text = "AO"

								#retencao na fonte
								taxtype.text = "NS"
								taxcode = ET.SubElement(tax,'TaxCode')
								taxcode.text = "NS"

								retn = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 and name  like '%%fonte' """,as_dict=True)
								print retn


								taxpercentage = ET.SubElement(tax,'TaxPercentage')
								taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

								taxamount = ET.SubElement(tax,'TaxAmount')
								taxamount.text = str(entradagl.debit) 		



							elif "IVA" in entradagl.account:
								tax = ET.SubElement(taxes,'Tax')
								taxtype = ET.SubElement(tax,'TaxType')

								taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
								taxcountryregion.text = "AO"

								#IVA	ainda por rever
								taxtype.text = "IVA"
								taxcode = ET.SubElement(tax,'TaxCode')
								taxcode.text = "NOR"

							#else:
							#	taxtype.text = "NS"
							#	taxcode = ET.SubElement(tax,'TaxCode')
							#	taxcode.text = "NS"


								taxpercentage = ET.SubElement(tax,'TaxPercentage')
								taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

								taxamount = ET.SubElement(tax,'TaxAmount')
								taxamount.text = str(entradagl.credit) 		
			
							#return			

			taxexemptionreason = ET.SubElement(line,'TaxExemptionReason')
			taxexemptioncode = ET.SubElement(line,'TaxExemptionCode')
			settlementamount = ET.SubElement(line,'SettlementAmount')

			#customsinformation
			customsinformation = ET.SubElement(line,'CustomsInformation')
			arcno = ET.SubElement(customsinformation,'ARCNo')
			iecamount = ET.SubElement(customsinformation,'IECAmount')



		#documenttotals
		documenttotals = ET.SubElement(invoice,'DocumentTotals')

		taxpayable = ET.SubElement(documenttotals,'TaxPayable')
		print 'factura Referencia'
		if factura.docstatus != 2:
			salestaxescharges = frappe.db.sql(""" select * from `tabSales Taxes and Charges` where parent = %s """,(factura.name),as_dict=True)
			print salestaxescharges

			if salestaxescharges: 
				print salestaxescharges[0].tax_amount
				taxpayable.text = str(salestaxescharges[0].tax_amount) 		#por ir buscar 
			else:
				taxpayable.text = "0.00" 		#por ir buscar 



		#if retencao.credit_in_account_currency:
		#	taxpayable.text = str(retencao.credit_in_account_currency) 		#por ir buscar 

		nettotal = ET.SubElement(documenttotals,'NetTotal')
		nettotal.text = str(factura.net_total)		#Sem Impostos Total Factura

		grosstotal = ET.SubElement(documenttotals,'GrossTotal')
		grosstotal.text = str(factura.rounded_total)		#Total Factura + impostos.... por ir buscar

		####ONLY IF NOT AOA .... POR VERIFICAR
		#currency
		currency = ET.SubElement(documenttotals,'Currency')
		currencycode = ET.SubElement(currency,'CurrencyCode')

		currencyamount = ET.SubElement(currency,'CurrencyAmount')
		#currencyamount.text = str(factura.rounded_total)		#Total Factura + impostos.... por ir buscar

		exchangerate = ET.SubElement(currency,'ExchangeRate')


	###END OF Purchase ORDER







	#END OF WORKINGDOCUMENTS




	#create Payments

	#Payments
	payments = ET.SubElement(sourcedocuments,'Payments')

	#primeirodiames = '2019-03-01'
	#ultimodiames = '2019-03-01'

	pagamentos = frappe.db.sql(""" select count(name), sum(paid_amount) from `tabPayment Entry` where company = %s and docstatus <> 0 and posting_date >= %s and posting_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)

	numberofentries = ET.SubElement(payments,'NumberOfEntries')
	totaldebit = ET.SubElement(payments,'TotalDebit')

	totalcredit = ET.SubElement(payments,'TotalCredit')

	if int(pagamentos[0]['count(name)']) !=0:


		numberofentries.text = str(pagamentos[0]['count(name)'])


		totaldebit.text = str(pagamentos[0]['sum(paid_amount)']) 



		pagamentos = frappe.db.sql(""" select * from `tabPayment Entry` where company = %s and docstatus <> 0 and posting_date >= %s and posting_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)

		#payment

		for recibo in pagamentos:
			payment = ET.SubElement(payments,'Payment')
			paymentrefno = ET.SubElement(payment,'PaymentRefNo')
			paymentrefno.text = recibo.name

			period = ET.SubElement(payment,'Period')
			period.text = str(recibo.modified.month)	#last modified month

			transactionid = ET.SubElement(payment,'TransactionID')
			#GLs created .... 

			transactiondate = ET.SubElement(payment,'TransactionDate')
			transactiondate.text = recibo.posting_date.strftime("%Y-%m-%d")

			paymenttype = ET.SubElement(payment,'PaymentType')
			paymenttype.text = "RC"	#default SAFT

			description = ET.SubElement(payment,'Description')
			description.text = recibo.remarks

			systemid = ET.SubElement(payment,'SystemID')
			systemid.text = recibo.name

			documentstatus = ET.SubElement(payment,'DocumentStatus')
			paymentstatus = ET.SubElement(documentstatus,'PaymentStatus')	
			if recibo.docstatus == 1:
				#pago
				paymentstatus.text = "N"
			elif recibo.docstatus == 2:
				#Canceled
				paymentstatus.text = "A"

			paymentstatusdate = ET.SubElement(documentstatus,'PaymentStatusDate')
			paymentstatusdate.text = recibo.modified.strftime("%Y-%m-%dT%H:%M:%S")

			reason = ET.SubElement(documentstatus,'Reason')

			sourceid = ET.SubElement(documentstatus,'SourceID')
			sourceid.text = recibo.owner

			sourcepayment = ET.SubElement(documentstatus,'SourcePayment')
			sourcepayment.text = "P"	#default nossa APP

			paymentmethod = ET.SubElement(payment,'PaymentMethod')
			paymentmechanism = ET.SubElement(paymentmethod,'PaymentMechanism')
			if "Transferência Bancária" in recibo.mode_of_payment:
				paymentmechanism.text = "TB"
			elif "Cash" in recibo.mode_of_payment:					
				paymentmechanism.text = "NU"

			elif "TPA" in recibo.mode_of_payment:					
				paymentmechanism.text = "CD"

			paymentamount = ET.SubElement(paymentmethod,'PaymentAmount')
			paymentamount.text = str(recibo.paid_amount) 

			paymentdate = ET.SubElement(paymentmethod,'PaymentDate')
			paymentdate.text = recibo.modified.strftime("%Y-%m-%d")

			sourceid = ET.SubElement(payment,'SourceID')
			sourceid.text = recibo.owner

			systementrydate = ET.SubElement(payment,'SystemEntryDate')
			systementrydate.text = recibo.posting_date.strftime("%Y-%m-%d")

			customerid = ET.SubElement(payment,'CustomerID')
			customerid.text = recibo.party


			#line
			recibosreferencias = frappe.db.sql(""" select * from `tabPayment Entry Reference` where parenttype = 'payment entry' and parent = %s order by idx """,(recibo.name), as_dict=True)

			print 'recibosreferencias'
			print recibosreferencias

			for reciboreferencia in recibosreferencias:
				line = ET.SubElement(payment,'Line')
				linenumber = ET.SubElement(line,'LineNumber')
				linenumber.text = str(reciboreferencia.idx)

				sourcedocumentid = ET.SubElement(line,'SourceDocumentID')
				originatingon = ET.SubElement(sourcedocumentid,'OriginatingON')
				originatingon.text = reciboreferencia.reference_name

				invoicedate = ET.SubElement(sourcedocumentid,'InvoiceDate')
				invoicedate.text = reciboreferencia.creation.strftime("%Y-%m-%dT%H:%M:%S")	#still need to know if should be postingdate from SL

				description = ET.SubElement(sourcedocumentid,'Description')

				settlementamount = ET.SubElement(line,'SettlementAmount')	#Desconto geral VALOR
				#procura no Sales Invoice 
				factura = frappe.db.sql(""" select * from `tabSales Invoice` where name = %s """,(reciboreferencia.reference_name), as_dict=True)
				if factura:
					if factura[0].discount_amount:
						settlementamount.text = str(factura[0].discount_amount) 
	
				debitamount = ET.SubElement(line,'DebitAmount')
				debitamount.text = str(reciboreferencia.allocated_amount) 

				creditamount = ET.SubElement(line,'CreditAmount')

				#tax
				#tax = ET.SubElement(line,'Tax')

				entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='payment entry' and company = %s and voucher_no = %s """,(empresa.name,recibo.name), as_dict=True)


				for entradagl in entradasgl:

					if "34210000" in entradagl.account:
						tax = ET.SubElement(line,'Tax')

						taxtype = ET.SubElement(tax,'TaxType')

						taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
						taxcountryregion.text = "AO"

						#imposto de producao e consumo IPC
						taxtype.text = "NS"
						taxcode = ET.SubElement(tax,'TaxCode')
						taxcode.text = "NS"

						retn = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 and name  = 'ipc' """,as_dict=True)
						print retn


						taxpercentage = ET.SubElement(tax,'TaxPercentage')
						taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

						taxamount = ET.SubElement(tax,'TaxAmount')
						taxamount.text = str(entradagl.credit) 		


					elif "34710000" in entradagl.account:
						tax = ET.SubElement(line,'Tax')
						taxtype = ET.SubElement(tax,'TaxType')

						taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
						taxcountryregion.text = "AO"

						#imposto de selo
						taxtype.text = "IS"
						taxcode = ET.SubElement(tax,'TaxCode')
						taxcode.text = "NS"

						retn = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 and name  like '%%selo' """,as_dict=True)
						print retn


						taxpercentage = ET.SubElement(tax,'TaxPercentage')
						taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

						taxamount = ET.SubElement(tax,'TaxAmount')
						taxamount.text = str(entradagl.credit) 		


					elif "34140000" in entradagl.account:
						tax = ET.SubElement(line,'Tax')
						taxtype = ET.SubElement(tax,'TaxType')

						taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
						taxcountryregion.text = "AO"

						#retencao na fonte
						taxtype.text = "NS"
						taxcode = ET.SubElement(tax,'TaxCode')
						taxcode.text = "NS"

						retn = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 and name  like '%%fonte' """,as_dict=True)
						print retn


						taxpercentage = ET.SubElement(tax,'TaxPercentage')
						taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

						taxamount = ET.SubElement(tax,'TaxAmount')
						taxamount.text = str(entradagl.debit) 		



					elif "IVA" in entradagl.account:
						tax = ET.SubElement(line,'Tax')
						taxtype = ET.SubElement(tax,'TaxType')

						taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
						taxcountryregion.text = "AO"

						#IVA	ainda por rever
						taxtype.text = "IVA"
						taxcode = ET.SubElement(tax,'TaxCode')
						taxcode.text = "NOR"

					#else:
					#	taxtype.text = "NS"
					#	taxcode = ET.SubElement(tax,'TaxCode')
					#	taxcode.text = "NS"


						taxpercentage = ET.SubElement(tax,'TaxPercentage')
						taxpercentage.text = str(retn[0].percentagem)		#por ir buscar

						taxamount = ET.SubElement(tax,'TaxAmount')
						taxamount.text = str(entradagl.credit) 		
			
				taxexemptionreason = ET.SubElement(line,'TaxExemptionReason')
				taxexemptioncode = ET.SubElement(line,'TaxExemptionCode')

			#documenttotals
			documenttotals = ET.SubElement(payment,'DocumentTotals')
	
			taxpayable = ET.SubElement(documenttotals,'TaxPayable')
			print 'Tax payable'
			pagamentotaxas = frappe.db.sql(""" select * from `tabPayment Entry Deduction` where parent = %s """,(recibo.name),as_dict=True)
			print pagamentotaxas

			if pagamentotaxas: 
				print pagamentotaxas[0].amount
				taxpayable.text = str(pagamentotaxas[0].amount) 		 
			else:
				taxpayable.text = "0.00" 		#por ir buscar 


			#Should it get from Each invoice the NETtotal and GrossTotal and do SUM
			nettotal = ET.SubElement(documenttotals,'NetTotal')
			grosstotal = ET.SubElement(documenttotals,'GrossTotal')
			#settlement
			settlement = ET.SubElement(documenttotals,'Settlement')
			settlementamount = ET.SubElement(settlement,'SettlementAmount')
			#currency
			currency = ET.SubElement(documenttotals,'Currency')
			currencycode = ET.SubElement(currency,'CurrencyCode')
			currencyamount = ET.SubElement(currency,'CurrencyAmount')
			exchangerate = ET.SubElement(currency,'ExchangeRate')

			#witholdingtax
			#withholdingtax = ET.SubElement(payment,'WithholdingTax')

			'''
			if pagamentotaxas: 

				entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='payment entry' and company = %s and voucher_no = %s """,(empresa.name,recibosreferencias[0].parent), as_dict=True)

				for entradagl in entradasgl:

					if "34710000" in entradagl.account:
						#imposto selo
						withholdingtaxtype = ET.SubElement(withholdingtax,'WithholdingTaxType')
						withholdingtaxtype.text = "IS"

						withholdingtaxdescription = ET.SubElement(withholdingtax,'WithholdingTaxDescription')
						withholdingtaxdescription.text = entradagl.account

						withholdingtaxamount = ET.SubElement(withholdingtax,'WithholdingTaxAmount')
						withholdingtaxamount.text = str(entradagl.credit)



					elif "34120000" in entradagl.account:
						#imposto industrial
						withholdingtaxtype = ET.SubElement(withholdingtax,'WithholdingTaxType')
						withholdingtaxtype.text = "II"

						withholdingtaxdescription = ET.SubElement(withholdingtax,'WithholdingTaxDescription')
						withholdingtaxdescription.text = entradagl.account

						withholdingtaxamount = ET.SubElement(withholdingtax,'WithholdingTaxAmount')
						withholdingtaxamount.text = str(entradagl.credit)

					elif "34310000" in entradagl.account:
						#IRT
						withholdingtaxtype = ET.SubElement(withholdingtax,'WithholdingTaxType')
						withholdingtaxtype.text = "IRT"

						withholdingtaxdescription = ET.SubElement(withholdingtax,'WithholdingTaxDescription')
						withholdingtaxdescription.text = entradagl.account

						withholdingtaxamount = ET.SubElement(withholdingtax,'WithholdingTaxAmount')
						withholdingtaxamount.text = str(entradagl.debit)

			'''

			if pagamentotaxas:
			#entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='payment entry' and company = %s and voucher_no = %s """,(empresa.name,recibosreferencias[0].parent), as_dict=True)
				for reciboreferencia in recibosreferencias:
					print reciboreferencia
					entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='payment entry' and company = %s and voucher_no = %s """,(empresa.name,reciboreferencia.parent), as_dict=True)
					#witholdingtax
					#withholdingtax = ET.SubElement(invoice,'WithholdingTax')

					print 'entradasgl'
					print entradasgl


					variasentradas = False
					if entradasgl:
						for entradagl in entradasgl:
							print 'conta ', entradagl.account
							if "34710000" in entradagl.account:
								#imposto selo
								if variasentradas == True:
									withholdingtax = ET.SubElement(payment,'WithholdingTax')

								withholdingtaxtype = ET.SubElement(withholdingtax,'WithholdingTaxType')
								withholdingtaxtype.text = "IS"

								withholdingtaxdescription = ET.SubElement(withholdingtax,'WithholdingTaxDescription')
								withholdingtaxdescription.text = entradagl.account

								withholdingtaxamount = ET.SubElement(withholdingtax,'WithholdingTaxAmount')
								withholdingtaxamount.text = str(entradagl.credit)

							elif "34120000" in entradagl.account:
								#imposto industrial
								if variasentradas == True:
									withholdingtax = ET.SubElement(payment,'WithholdingTax')

								withholdingtaxtype = ET.SubElement(withholdingtax,'WithholdingTaxType')
								withholdingtaxtype.text = "II"

								withholdingtaxdescription = ET.SubElement(withholdingtax,'WithholdingTaxDescription')
								withholdingtaxdescription.text = entradagl.account

								withholdingtaxamount = ET.SubElement(withholdingtax,'WithholdingTaxAmount')
								withholdingtaxamount.text = str(entradagl.credit_in_account_currency)

							elif "34310000" in entradagl.account:
								#IRT
								if variasentradas == True:
									withholdingtax = ET.SubElement(payment,'WithholdingTax')

								withholdingtaxtype = ET.SubElement(withholdingtax,'WithholdingTaxType')
								withholdingtaxtype.text = "IRT"

								withholdingtaxdescription = ET.SubElement(withholdingtax,'WithholdingTaxDescription')
								withholdingtaxdescription.text = entradagl.account

								withholdingtaxamount = ET.SubElement(withholdingtax,'WithholdingTaxAmount')
								withholdingtaxamount.text = str(entradagl.credit_in_account_currency)

							variasentradas = True	#para garar varias entradas




	#END OF Payments



	###END PROCESSING 
	print 'Creating the File....'
	#record the data...	
	mydata = ET.tostring(data, 'utf-8')
	reparsed = minidom.parseString(mydata)
	

	myfile = open("/tmp/" + nomeficheiro + ".xml","w")


	myfile.write(reparsed.toprettyxml(indent=" "))


	print 'file created'

	#END OF SAFT_AO




@frappe.whitelist()
def convert_csv_xml(ficheiro="csv_xml.csv", delimiter1 = None, site="http://127.0.0.1:8000"):

	#delimiter default , but added ;
	if delimiter1 == None:
		delimiter1 = str(u',').encode('utf-8') 
	if delimiter1 == ';':
		delimiter1 = str(u';').encode('utf-8') 	
	
	if not "tmp" in ficheiro:
		ficheiro = "/tmp/" + ficheiro	

	linhainicial = False
	colunas = []

	with open (ficheiro) as csvfile:
			readCSV = csv.reader(csvfile, delimiter = delimiter1)	

			for row in readCSV:
				if "DocType:" in row[0]:
					print row[1]	#Doctype name

				if "Column Name:" in row[0]:
					print len(row)	#Fields count
					for cols in row:	#Fields name print.
						print cols
						colunas.append(cols)
					#print row[1]	# 1st Fields...


				if linhainicial == True:	
					#Data starts here ....
#					print "Data starts here ...."
					for idx, cols in enumerate(row):
						#print idx
						#print cols
						print colunas[idx]
						print cols

				if "Start entering data below this line" in row[0]:
					print row
					linhainicial = True

			#testing ....
			convert_xml()



@frappe.whitelist()
def test_xs():
	from lxml import etree as ET
	from lxml.builder import ElementMaker

	NS_DC = "http://purl.org/dc/elements/1.1/"
	NS_OPF = "http://www.idpf.org/2007/opf"
	SCHEME = ET.QName(NS_OPF, 'scheme')
	FILE_AS = ET.QName(NS_OPF, "file-as")
	ROLE = ET.QName(NS_OPF, "role")
	opf = ElementMaker(namespace=NS_OPF, nsmap={"opf": NS_OPF, "dc": NS_DC})
	dc = ElementMaker(namespace=NS_DC)
#	validator = ET.RelaxNG(ET.parse("/tmp/opf-schema.xml"))

	tree = (
	    opf.package(
		{"unique-identifier": "uuid_id", "version": "2.0"},
		opf.metadata(
		    dc.identifier(
		        {SCHEME: "uuid", "id": "uuid_id"},
		        "d06a2234-67b4-40db-8f4a-136e52057101"),
		    dc.creator({FILE_AS: "Homes, A. M.", ROLE: "aut"}, "A. M. Homes"),
		    dc.title("My Book"),
		    dc.language("en"),
		),
		opf.manifest(
		    opf.item({"id": "foo", "href": "foo.pdf", "media-type": "foo"})
		),
		opf.spine(
		    {"toc": "uuid_id"},
		    opf.itemref({"idref": "uuid_id"}),
		),
		opf.guide(
		    opf.reference(
		        {"href": "cover.jpg", "title": "Cover", "type": "cover"})
		),
	    )
	)
#	validator.assertValid(tree)

	print(ET.tostring(tree, pretty_print=True).decode('utf-8'))


@frappe.whitelist()
def test_xsd():
	from lxml import etree
	from lxml.html import parse
	
	xxml = '/tmp/clientes.xml'
	for event, elem in ET.iterparse(xxml, events=('start','end','start-ns','end-ns')):

		print event
		print elem

@frappe.whitelist()
def validar_xml_xsd(xml_path, xsd_path):
	from lxml import etree

	xmlschema_doc = etree.parse(xsd_path)
	xmlschema = etree.XMLSchema(xmlschema_doc)

	xml_doc = etree.parse(xml_path)
	result = xmlschema.validate(xml_doc)

	print result




import requests
from M2Crypto import BIO, RSA, EVP, X509

@frappe.whitelist()
def verify_message(pem, msg, sig):
    f = open(pem,"r")
    pem1 = f.read()	
    cert = X509.load_cert(pem)	
    cert1 = X509.load_cert_string(pem1)
    pubkey = cert.get_pubkey()
    sig = sig.decode('base64')

    # Write a few files to disk for debugging purposes
    f = open("sig", "wb")
    f.write(sig)
    f.close()

#    f = open("msg", "w")
#    f.write(msg)
#    f.close()

    f = open("mypubkey.pem", "w")
    f.write(pubkey.get_rsa().as_pem())
    f.close()

    pubkey.reset_context(md='sha1')
    pubkey.verify_init()
    pubkey.verify_update(msg)
    return pubkey.verify_final(sig)

'''

PEM = """-----BEGIN CERTIFICATE-----
MIICsDCCAhmgAwIBAgIJAJrZExFauz5pMA0GCSqGSIb3DQEBBQUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIEwpTb21lLVN0YXRlMSEwHwYDVQQKExhJbnRlcm5ldCBX
aWRnaXRzIFB0eSBMdGQwHhcNMTMwMzA3MDkzNjQyWhcNMTgwMzA3MDkzNjQyWjBF
MQswCQYDVQQGEwJBVTETMBEGA1UECBMKU29tZS1TdGF0ZTEhMB8GA1UEChMYSW50
ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKB
gQDRiW70Ea0CIrJmv9nwO0882mZ51ygAqQrQLfaYB2EUE5SRE99GaQbT9TsmcPK1
aG5ZDmazWRGBWe8UCL0W6fFrkg6Cb6VwFGqUSAsFhlT+XhOqAF9p3dfqu3S85zyY
7zJ5YIAMgDbd8/KmaqP8xn2aNY1cUxN/0HxOB4fz2/f/YQIDAQABo4GnMIGkMB0G
A1UdDgQWBBRj2EiZsFFFc4IbLHJa9CupE9ynbzB1BgNVHSMEbjBsgBRj2EiZsFFF
c4IbLHJa9CupE9ynb6FJpEcwRTELMAkGA1UEBhMCQVUxEzARBgNVBAgTClNvbWUt
U3RhdGUxITAfBgNVBAoTGEludGVybmV0IFdpZGdpdHMgUHR5IEx0ZIIJAJrZExFa
uz5pMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQEFBQADgYEAip8XS5JX3hFG8wjZ
0FxqU/FLjSJkGrAscs16y7iq9YnUIfPt0Fha4a36vB5nG42vai10BtLgZEP/mifJ
DQXbDZA46G7gBiV9AvqtJWDNOfn7c34g23G9lxIEuU8ptLoyN+38TFdS+eWQDo/q
a/1IvCESUYYY43s+aOp6nbkDoGw=
-----END CERTIFICATE-----
"""

MSG = """
"""

SIG = """
FFOSR4UhPjheKN3hNAXIh/XL5OByp23+Gk+NRgonsZoI0eQHJn7nCEr/b1NbL/DP7UVL7o
nM6+RC1/yjiSi4J8wj4kqs19PY4ZGQXbnnDxutJoMfo+lhRA/H+jTPL5u8bs/d07ln0eHl
AzyOCxee3DRTxJKbmQewb48xhmou4jQ=
"""

'''