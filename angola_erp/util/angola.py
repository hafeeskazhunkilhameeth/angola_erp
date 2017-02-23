# -*- coding: utf-8 -*-
# Copyright (c) 2016, Helio de Jesus and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

from frappe.model.document import Document
import frappe.model
import frappe
from frappe.utils import nowdate, cstr, flt, cint, now, getdate
from frappe import throw, _
from frappe.utils import formatdate
from frappe.model.naming import make_autoname

@frappe.whitelist()
def check_caixa_aberto():

	if (frappe.db.sql("""select name from `tabCaixa de Registo` WHERE status_caixa ='Aberto' """, as_dict=False)) != ():
		print "AAAAAAAA"
		return frappe.db.sql("""select name from `tabCaixa de Registo` WHERE status_caixa ='Aberto' """, as_dict=False)
	elif (frappe.db.sql("""select name from `tabCaixa de Registo` WHERE status_caixa ='Em Curso' """, as_dict=False)) != ():
		return frappe.db.sql("""select name from `tabCaixa de Registo` WHERE status_caixa ='Em Curso' """, as_dict=False)
		print "BBBBBBBBB"
		print frappe.db.sql("""select name from `tabCaixa de Registo` WHERE status_caixa ='Aberto' """, as_dict=False)	

@frappe.whitelist()
def caixa_movimentos_in(start,caixa,fecho):

		total_tpa = 0
		total_ccorrente = 0
		total_caixa = 0
		recalcula = False
		for d in  frappe.db.sql("""select hora_atendimento, name,total_servicos,pagamento_por, status_atendimento, bar_tender, company from `tabAtendimento Bar` where status_atendimento ='Fechado' and hora_atendimento >= %(start)s and hora_atendimento <= %(end)s """, {"start": start,"end": frappe.utils.now()	}, as_dict=True):
			
			print "MOVIMENTOS BAR RESTAURANTE +++++++++++++++++++++++++++++++"
			ddd = make_autoname('MOV-' + '.#####')
			if len(frappe.db.sql("SELECT name,descricao_movimento from tabMovimentos_Caixa WHERE descricao_movimento=%(mov)s""",{"mov":d.name}, as_dict=True))==0:
				frappe.db.sql("INSERT into tabMovimentos_Caixa (name, docstatus, parent, parenttype, parentfield, tipo_pagamento, descricao_movimento, valor_pago, hora_atendimento, creation, modified, usuario_movimentos, company) values (%s,0,%s,'Caixa de Registo','movimentos_caixa',%s,%s,%s,%s,%s,%s,%s,%s) ",(ddd, caixa, d.pagamento_por ,d.name, d.total_servicos, d.hora_atendimento, frappe.utils.now(), frappe.utils.now(),d.bar_tender,d.company))
				total_caixa = d.total_servicos+total_caixa
				if (d.pagamento_por == "TPA"):
					total_tpa = d.total_servicos+total_tpa
				
				if (d.pagamento_por == "Conta-Corrente"):
					total_ccorrente = d.total_servicos+total_ccorrente
			else:
				#Recalcula o Caixa ....
				recalcula = True
				total_caixa = d.total_servicos+total_caixa
				if (d.pagamento_por == "TPA"):
					total_tpa = d.total_servicos+total_tpa
				
				if (d.pagamento_por == "Conta-Corrente"):
					total_ccorrente = d.total_servicos+total_ccorrente

		print "Abre Caixa"
		print total_caixa
		reser = frappe.get_doc("Caixa de Registo",caixa)
		if (total_caixa > 1) and (reser.amount_caixa == 0):
			if (recalcula == False):
				reser.amount_caixa = total_caixa+reser.amount_caixa
				reser.amount_tpa = total_tpa+reser.amount_tpa
				reser.amount_conta_corrente = total_ccorrente+reser.amount_conta_corrente
			else:
				reser.amount_caixa = total_caixa
				reser.amount_tpa = total_tpa
				reser.amount_conta_corrente = total_ccorrente

			reser.status_caixa='Em Curso'
			reser.save()
		elif (total_caixa > 1) and (reser.amount_caixa >= 0):
			if (recalcula == False):
				reser.amount_caixa = total_caixa+reser.amount_caixa
				reser.amount_tpa = total_tpa+reser.amount_tpa
				reser.amount_conta_corrente = total_ccorrente+reser.amount_conta_corrente
			else:
				reser.amount_caixa = total_caixa
				reser.amount_tpa = total_tpa
				reser.amount_conta_corrente = total_ccorrente

			reser.save()

		print fecho
		print reser.status_caixa
		if (fecho==2):
			reser.status_caixa='Fechado'
			reser.save()

		

		return total_caixa



@frappe.whitelist()
def get_taxa_ipc():
	#locate account 34210000
	j= frappe.db.sql(""" select name, description, account_head, parent  from `tabSales Taxes and Charges` where account_head like '3421%' and parenttype ='Sales Taxes and Charges Template' """,as_dict=True)

	print " LISTA TAXE IPC conta 3421"
	print j	
	return j

@frappe.whitelist()
def get_taxa_retencao():
	#locate account 34120000
	j= frappe.db.sql(""" select name, description, account_head, parent  from `tabSales Taxes and Charges` where account_head like '3413%' and parenttype ='Sales Taxes and Charges Template' """,as_dict=True)

	print " LISTA TAXA RETENCAO conta 3413"
	print j	
	return j

@frappe.whitelist()
def get_lista_retencoes():
	j= frappe.db.sql(""" SELECT name, descricao, percentagem from `tabRetencoes` """,as_dict=True)

	print " LISTA RETENCOES"
	print j	
	return j



@frappe.whitelist()
def get_lista_taxas_vendas():
	j= frappe.db.sql(""" select name, description  from `tabSales Taxes and Charges` """,as_dict=True)

	print " LISTA TAXES e CHARGES"
	print j	
	return j


# 
# convert number to words 
# 
def in_words_pt(integer, in_million=True): 
	""" 
	Returns string in words for the given integer. 
	""" 
	n=int(integer) 
 	known = {0: 'zero', 1: 'um', 2: 'dois', 3: 'três', 4: 'quarto', 5: 'cinco', 6: 'seis', 7: 'sete', 8: 'oito', 9: 'novo', 10: 'dez', 11: 'onze', 12: 'doze', 13: 'treze', 14: 'catorze', 15: 'quinze', 16: 'dezaseis', 17: 'dezasete', 18: 'dezoito',
19: 'dezanove', 20: 'vinte', 30: 'trinta', 40: 'quarenta', 50: 'cinquenta', 60: 'sessenta', 70: 'setenta', 80: 'oitenta', 90: 'noventa'} 


	def psn(n, known, xpsn): 
		import sys; 
		if n in known: return known[n] 
		bestguess, remainder = str(n), 0 

 
		if n<=20: 
			webnotes.errprint(sys.stderr) 
			webnotes.errprint(n) 
			webnotes.errprint("Como isto aconteceu?") 
			assert 0 
		elif n < 100: 
			bestguess= xpsn((n//10)*10, known, xpsn) + '-' + xpsn(n%10, known, xpsn) 
			return bestguess 
		elif n < 1000: 
			bestguess= xpsn(n//100, known, xpsn) + ' ' + 'cem' 
			remainder = n%100 
		else: 
			if in_million: 
				if n < 1000000: 
					bestguess= xpsn(n//1000, known, xpsn) + ' ' + 'mil' 
					remainder = n%1000 
				elif n < 1000000000: 
					bestguess= xpsn(n//1000000, known, xpsn) + ' ' + 'milhões' 
					remainder = n%1000000 
				else: 
					bestguess= xpsn(n//1000000000, known, xpsn) + ' ' + 'bilhões' 
					remainder = n%1000000000 
			else: 
				if n < 100000: 
					bestguess= xpsn(n//1000, known, xpsn) + ' ' + 'mil' 
					remainder = n%1000 
				elif n < 10000000: 
					bestguess= xpsn(n//100000, known, xpsn) + ' ' + 'cem mil' 
					remainder = n%100000 
				else: 
					bestguess= xpsn(n//10000000, known, xpsn) + ' ' + 'dez milhões' 
					remainder = n%10000000 
		if remainder: 
			if remainder >= 100: 
				comma = ',' 
			else: 
				comma = '' 
			return bestguess + comma + ' ' + xpsn(remainder, known, xpsn) 
		else: 
			return bestguess 


	return psn(n, known, psn) 

