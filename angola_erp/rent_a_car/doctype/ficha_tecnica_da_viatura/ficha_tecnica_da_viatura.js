// Copyright (c) 2019, Helio de Jesus and contributors
// For license information, please see license.txt

var contracto_
var contractoS_ = cur_frm.call({method:"angola_erp.util.angola.get_all_contracto_numero",args:{}})
var agora_entrada = false
var botao_checkin = false
var depoisDeSalvar = false

var car_lastMile

//cur_frm.add_fetch('tc_name', 'terms', 'termos');

frappe.ui.form.on('Ficha Tecnica da Viatura', {

	onload: function(frm) {
		console.log('onload')
		cur_frm.fields_dict['matricula_veiculo'].get_query = function(doc){
			return{
				filters:{
					"veiculo_alugado":1,
					"entrada_ou_saida":"Stand-by",
				},
				
			}
		}
		//frm.refresh()
/*
		if (cur_frm.doc.docstatus == 1) {
			botao_checkin = true
			console.log('ATIVA O botao_checkin')
		}	
*/
	},
	refresh: function(frm) {
		console.log('refres')
/*
		if (contracto_ != undefined){
			console.log('para analisar se ainda preicsa...')
			if (contracto_.statusCode == 'Ok'){
				if (contracto_.responseJSON.message != undefined){
					cur_frm.doc.contracto_numero = contracto_.responseJSON.message.contracto_numero
					cur_frm.doc.estacao_viatura = contracto_.responseJSON.message.local_de_saida
					cur_frm.doc.data_entrada_estacao = contracto_.responseJSON.message.devolucao_prevista
					cur_frm.doc.data_saida_estacao = contracto_.responseJSON.message.data_de_saida			
					cur_frm.refresh_fields('contracto_numero')
				}
			}
		}

*/
		cur_frm.toggle_enable('total_dias',false)
		cur_frm.toggle_enable('preco_dia_basico',false)
		cur_frm.toggle_enable("data_estimada_entrada_estacao",false)
		cur_frm.toggle_enable("grupo",false)
		cur_frm.toggle_enable("kms_extra",false)
		cur_frm.toggle_enable("total_kms_extra",false)

		if (cur_frm.doc.docstatus == 0){

			if (cur_frm.doc.entrada_ou_saida_viatura == 'Saida'){
				cur_frm.toggle_enable("kms_entrada",false)
				cur_frm.toggle_enable("combustivel_entrada",false)

				cur_frm.toggle_enable("estacao_viatura",false)

				cur_frm.get_field("kms_entrada").df.reqd = false
				cur_frm.get_field("combustivel_entrada").df.reqd = false

				cur_frm.toggle_enable("data_entrada_estacao",false)
			}else {

				cur_frm.toggle_enable("data_entrada_estacao",true)
				cur_frm.toggle_enable("kms_entrada",true)
				cur_frm.toggle_enable("combustivel_entrada",true)

				cur_frm.toggle_enable("entrada_ou_saida_viatura",false)
				cur_frm.toggle_enable("matricula_veiculo",false)
				cur_frm.toggle_enable("data_saida_estacao",false)
				cur_frm.toggle_enable("kms_saida",false)
				cur_frm.toggle_enable("combustivel_saida",false)
				cur_frm.toggle_enable("data_estimada_entrada_viatura",false)
				cur_frm.fields_dict['matricula_veiculo'].get_query = function(doc){
					return{
						filters:{
							"veiculo_alugado":1,
							"entrada_ou_saida":"Alugado",
						},
				
					}
				}	

				if (cur_frm.doc.grupo != undefined){
					tarifario_("Tarifas",cur_frm.doc.grupo)
				}


			}		

		}


		if (cur_frm.doc.matricula_veiculo) {

			if(frm.doc.docstatus == 1 && cur_frm.doc.status_viatura == "Alugada") {
				console.log('adiciona botao')
				if (cur_frm.doc.entrada_ou_saida_viatura == "Saida"){
					frm.add_custom_button(__('Check In Viatura'), function() {
						agora_entrada = true
						botao_checkin = false
						frappe.model.open_mapped_doc({method:"angola_erp.util.angola.checkin_ficha_tecnica",frm:cur_frm})


					});

				}else{
					frm.clear_custom_buttons()
					//Botao para fazer FACTURA
					if (cur_frm.doc.status_viatura == 'Devolvida') {
						frm.add_custom_button(__('Fazer Factura'), function() {
							//agora_entrada = true
							//botao_checkin = false
							//frappe.model.open_mapped_doc({method:"angola_erp.util.angola.checkin_ficha_tecnica",frm:cur_frm})
							frappe.show_alert('Ainda por automatizar ... Mas sempre pode fazer indo as Facturas.',4)

						});
					}

				}
			}else{
				console.log('limpa botoes')
				frm.clear_custom_buttons()
				//Botao para fazer FACTURA
				if (cur_frm.doc.status_viatura == 'Devolvida') {
					frm.add_custom_button(__('Fazer Factura'), function() {
						//agora_entrada = true
						//botao_checkin = false
						//frappe.model.open_mapped_doc({method:"angola_erp.util.angola.checkin_ficha_tecnica",frm:cur_frm})
						frappe.show_alert('Ainda por automatizar ... Mas sempre pode fazer indo as Facturas.',4)

					});
				}

			}
		}

		if (agora_entrada == true){
			console.log('aqui')
			cur_frm.doc.docstatus = 0 
			cur_frm.set_value("ficha_numero","")
			cur_frm.set_value("entrada_ou_saida_viatura","Entrada")

			cur_frm.toggle_enable("entrada_ou_saida_viatura",false)
			cur_frm.toggle_enable("matricula_veiculo",false)
			cur_frm.toggle_enable("data_saida_estacao",false)
			cur_frm.toggle_enable("kms_saida",false)
			cur_frm.toggle_enable("combustivel_saida",false)

			//cur_frm.toggle_enable("kms_entrada",true)

			cur_frm.toggle_enable('documentos_viatura',true)
			cur_frm.toggle_enable('radio_viatura',true)
			cur_frm.toggle_enable('antena_viatura',true)
			cur_frm.toggle_enable('isqueiro_viatura',true)
			cur_frm.toggle_enable('cinzeiro_viatura',true)
			cur_frm.toggle_enable('vidros_viatura',true)
			cur_frm.toggle_enable('triangulo_viatura',true)
			cur_frm.toggle_enable('penu_suplente',true)
			cur_frm.toggle_enable('tapetes_viatura',true)
			cur_frm.toggle_enable('tampoes_viatura',true)
			cur_frm.toggle_enable('pneus_viatura',true)
			cur_frm.toggle_enable('pintura_viatura',true)
			cur_frm.toggle_enable('chapa_viatura',true)
			cur_frm.toggle_enable('estofo_manchado',true)
			cur_frm.toggle_enable('estofo_queimado',true)

			cur_frm.get_field("kms_entrada").df.reqd = true
			cur_frm.get_field("combustivel_entrada").df.reqd = true

			cur_frm.toggle_enable("kms_entrada",true)
			cur_frm.toggle_enable("combustivel_entrada",true)

			agora_entrada = false

			cur_frm.custom_buttons["Check In Viatura"][0].disabled = true


			console.log('REFRESH')
			console.log('REFRESH')
			console.log('REFRESH')


		}
/*
		if (depoisDeSalvar == true){
			ficha_ = cur_frm.call({method:"angola_erp.util.angola.actualiza_ficha_tecnica",args:{"source_name":cur_frm.doc.matricula_veiculo}})
		}
*/
		if (depoisDeSalvar == true){
			depoisDeSalvar = false
			frm.reload_doc()
		}

	},

	after_save: function(frm) {
		//
		console.log('AFTER SAVE')
		console.log('AFTER SAVE')
		console.log('AFTER SAVE')
		console.log('AFTER SAVE')
		console.log('AFTER SAVE')

		console.log('AFTER SAVE')


		console.log(cur_frm.doc.entrada_ou_saida_viatura)
		console.log(frm.doc.docstatus)

		depoisDeSalvar = true
		botao_checkin = true
	
		if (frm.doc.docstatus == 1 && cur_frm.doc.entrada_ou_saida_viatura == "Entrada"){
			console.log(frm.doc.docstatus)
			cur_frm.refresh()
			console.log('after save')
			console.log('rever ...')


			//ficha_ = cur_frm.call({method:"angola_erp.util.angola.actualiza_ficha_tecnica",args:{"source_name":cur_frm.doc.matricula_veiculo}})

			//cur_frm.reload()


		
		}
	},

	validate: function(frm){
		if (cur_frm.doc.entrada_ou_saida_viatura == "Entrada") {
			if (parseInt(cur_frm.doc.kms_entrada) <= parseInt(cur_frm.doc.kms_saida)){
				frappe.show_alert("Kilometros de Entrada errada!!!",5)
				validated = false
			}
		}
	},

	after_insert: function(frm) {
		console.log('DEPOIS DE INSERIR')
		console.log('DEPOIS DE INSERIR')
		console.log('DEPOIS DE INSERIR')
		console.log('DEPOIS DE INSERIR')

	},
	

});



frappe.ui.form.on('Ficha Tecnica da Viatura','matricula_veiculo',function(frm,cdt,cdn){

	if (cur_frm.doc.matricula_veiculo != undefined) {
		cur_frm.toggle_enable("operador",false)
		frappe.model.set_value(cdt,cdn,'operador',frappe.session.user)

		contracto_ = cur_frm.call({method:"angola_erp.util.angola.get_contracto_numero",args:{"matricula":cur_frm.doc.matricula_veiculo}})
		veiculos_('Vehicle',cur_frm.doc.matricula_veiculo)
	
		if (contractoS_ != undefined){

			for (x in contractoS_.responseJSON.message) {
				if (contractoS_.responseJSON.message[x].matricula == cur_frm.doc.matricula_veiculo) {
					console.log("ENCONTROU A MATRICULA")
					cur_frm.doc.contracto_numero = contractoS_.responseJSON.message[x].contracto_numero
					cur_frm.doc.estacao_viatura = contractoS_.responseJSON.message[x].local_de_saida

					cur_frm.doc.data_estimada_entrada_estacao = contractoS_.responseJSON.message[x].devolucao_prevista
					//cur_frm.doc.grupo = contractoS_.reponseJSON.message[x].grupo
					cur_frm.doc.data_saida_estacao = contractoS_.responseJSON.message[x].data_de_saida
					cur_frm.doc.kms_saida = contractoS_.responseJSON.message[x].kms_out
					cur_frm.doc.combustivel_saida = contractoS_.responseJSON.message[x].deposito_out
					cur_frm.doc.tipo_combustivel = contractoS_.responseJSON.message[x].combustivel
					//cur_frm.refresh_fields('contracto_numero')

				}
			}
		}

		if (cur_frm.doc.entrada_ou_saida_viatura == 'Saida'){
			cur_frm.toggle_enable('documentos_viatura',true)
			cur_frm.toggle_enable('radio_viatura',true)
			cur_frm.toggle_enable('antena_viatura',true)
			cur_frm.toggle_enable('isqueiro_viatura',true)
			cur_frm.toggle_enable('cinzeiro_viatura',true)
			cur_frm.toggle_enable('vidros_viatura',true)
			cur_frm.toggle_enable('triangulo_viatura',true)
			cur_frm.toggle_enable('penu_suplente',true)
			cur_frm.toggle_enable('tapetes_viatura',true)
			cur_frm.toggle_enable('tampoes_viatura',true)
			cur_frm.toggle_enable('pneus_viatura',true)
			cur_frm.toggle_enable('pintura_viatura',true)
			cur_frm.toggle_enable('chapa_viatura',true)
			cur_frm.toggle_enable('estofo_manchado',true)
			cur_frm.toggle_enable('estofo_queimado',true)

		}

		if (cur_frm.doc.grupo != undefined){
			tarifario_("Tarifas",cur_frm.doc.grupo)
		}

		cur_frm.refresh_fields('marca_veiculo');
		cur_frm.trigger('entrada_ou_saida_viatura')
	}
});

frappe.ui.form.on('Ficha Tecnica da Viatura','entrada_ou_saida_viatura',function(frm,cdt,cdn){
	//if saida all checked 1 otherwise 0

	if (cur_frm.doc.entrada_ou_saida_viatura == 'Saida'){
		frappe.model.set_value(cdt,cdn,'documentos_viatura',1)
		frappe.model.set_value(cdt,cdn,'radio_viatura',1)
		frappe.model.set_value(cdt,cdn,'antena_viatura',1)
		frappe.model.set_value(cdt,cdn,'isqueiro_viatura',1)
		frappe.model.set_value(cdt,cdn,'cinzeiro_viatura',1)
		frappe.model.set_value(cdt,cdn,'vidros_viatura',1)
		frappe.model.set_value(cdt,cdn,'triangulo_viatura',1)
		frappe.model.set_value(cdt,cdn,'pneu_suplente',1)
		frappe.model.set_value(cdt,cdn,'tapetes_viatura',1)
		frappe.model.set_value(cdt,cdn,'tampoes_viatura',1)
		frappe.model.set_value(cdt,cdn,'pneus_viatura',1)
		frappe.model.set_value(cdt,cdn,'pintura_viatura',1)
		frappe.model.set_value(cdt,cdn,'chapa_viatura',1)
		frappe.model.set_value(cdt,cdn,'estofo_manchado',0)
		frappe.model.set_value(cdt,cdn,'estofo_queimado',0)

		cur_frm.toggle_enable('documentos_viatura',true)
		cur_frm.toggle_enable('radio_viatura',true)
		cur_frm.toggle_enable('antena_viatura',true)
		cur_frm.toggle_enable('isqueiro_viatura',true)
		cur_frm.toggle_enable('cinzeiro_viatura',true)
		cur_frm.toggle_enable('vidros_viatura',true)
		cur_frm.toggle_enable('triangulo_viatura',true)
		cur_frm.toggle_enable('penu_suplente',true)
		cur_frm.toggle_enable('tapetes_viatura',true)
		cur_frm.toggle_enable('tampoes_viatura',true)
		cur_frm.toggle_enable('pneus_viatura',true)
		cur_frm.toggle_enable('pintura_viatura',true)
		cur_frm.toggle_enable('chapa_viatura',true)
		cur_frm.toggle_enable('estofo_manchado',true)
		cur_frm.toggle_enable('estofo_queimado',true)

		cur_frm.toggle_enable("estacao_viatura",false)

		cur_frm.toggle_enable("kms_entrada",false)
		cur_frm.toggle_enable("combustivel_entrada",false)

		cur_frm.get_field("kms_entrada").df.reqd = false
		cur_frm.get_field("combustivel_entrada").df.reqd = false


	}else {
		frappe.model.set_value(cdt,cdn,'documentos_viatura',1)
		frappe.model.set_value(cdt,cdn,'radio_viatura',1)
		frappe.model.set_value(cdt,cdn,'antena_viatura',1)
		frappe.model.set_value(cdt,cdn,'isqueiro_viatura',1)
		frappe.model.set_value(cdt,cdn,'cinzeiro_viatura',1)
		frappe.model.set_value(cdt,cdn,'vidros_viatura',1)
		frappe.model.set_value(cdt,cdn,'triangulo_viatura',1)
		frappe.model.set_value(cdt,cdn,'pneu_suplente',1)
		frappe.model.set_value(cdt,cdn,'tapetes_viatura',1)
		frappe.model.set_value(cdt,cdn,'tampoes_viatura',1)
		frappe.model.set_value(cdt,cdn,'pneus_viatura',1)
		frappe.model.set_value(cdt,cdn,'pintura_viatura',1)
		frappe.model.set_value(cdt,cdn,'chapa_viatura',1)
		frappe.model.set_value(cdt,cdn,'estofo_manchado',0)
		frappe.model.set_value(cdt,cdn,'estofo_queimado',0)


		cur_frm.toggle_enable("entrada_ou_saida_viatura",false)
		cur_frm.toggle_enable("matricula_veiculo",false)
		cur_frm.toggle_enable("data_saida_estacao",false)
		cur_frm.toggle_enable("kms_saida",false)
		cur_frm.toggle_enable("combustivel_saida",false)

		cur_frm.toggle_enable("data_entrada_estacao",true)
		cur_frm.set_value("data_entrada_estacao",frappe.datetime.now_datetime())
		cur_frm.refresh_fields('data_entrada_estacao')

		cur_frm.fields_dict['matricula_veiculo'].get_query = function(doc){
			return{
				filters:{
					"veiculo_alugado":1,
					"entrada_ou_saida":"Alugado",
				},
				
			}
		}	


	}

	if (cur_frm.doc.grupo != undefined){
		tarifario_("Tarifas",cur_frm.doc.grupo)
	}


});

frappe.ui.form.on('Ficha Tecnica da Viatura','data_entrada_estacao',function(frm,cdt,cdn){

	console.log('DEVOLUCAO NO DIA .....')
	if (cur_frm.doc.data_entrada_estacao && cur_frm.doc.data_saida_estacao) {
		console.log(moment(cur_frm.doc.data_entrada_estacao).format('D') - moment(cur_frm.doc.data_saida_estacao).format('D'))
		cur_frm.doc.total_dias = cur_frm.doc.preco_dia_basico * (frappe.datetime.get_day_diff(cur_frm.doc.data_entrada_estacao,cur_frm.doc.data_saida_estacao) + 1) //(moment(cur_frm.doc.data_entrada_estacao).format('D') - moment(cur_frm.doc.data_saida_estacao).format('D'))

		cur_frm.refresh_field('total_dias')
	}

});


frappe.ui.form.on('Ficha Tecnica da Viatura','combustivel_entrada',function(frm,cdt,cdn){
	if (cur_frm.doc.combustivel_entrada != cur_frm.doc.combustivel_saida) {
		frappe.show_alert('Talvez tenha que cobrar o Combustivel',3)
	}


});



frappe.ui.form.on('Ficha Tecnica da Viatura','kms_entrada',function(frm,cdt,cdn){
	//so pode ser numeros...
	console.log('kms entrada')
	if (isNaN(cur_frm.doc.kms_entrada) == true){
 		frappe.show_alert("Somente numeros",5)
		cur_frm.doc.kms_entrada = ""
	}
	
	if (flt(cur_frm.doc.kms_entrada) <= flt(cur_frm.doc.kms_saida)) {
		frappe.show_alert('KMs de entrada Errados!!! ', 3)	
		cur_frm.doc.kms_entrada = ""
	}else if (frappe.datetime.get_day_diff(cur_frm.doc.data_estimada_entrada_estacao, cur_frm.doc.data_saida_estacao) + 1 <= 3) {  
	//calculate diff of km... if tarifa entre os 3 dias.
		//dentro dos 3 dias...
		if (flt(cur_frm.doc.kms_entrada) - flt(cur_frm.doc.kms_saida) > 100) {
			frappe.show_alert('Passou do 100Km.. ' + flt(cur_frm.doc.kms_entrada) - flt(cur_frm.doc.kms_saida), 3)
			cur_frm.set_value('kms_extra', flt(cur_frm.doc.kms_entrada) - flt(cur_frm.doc.kms_saida))
			cur_frm.set_value('total_kms_extra', flt(cur_frm.doc.por_km) * (flt(cur_frm.doc.kms_entrada) - flt(cur_frm.doc.kms_saida)))
		}else {
			cur_frm.set_value('kms_extra', 0)
			cur_frm.set_value('total_kms_extra', 0)

		}

	}


});


var veiculos_ = function(frm,cdt,cdn){
	frappe.model.with_doc(frm, cdt, function() { 
		var carro = frappe.model.get_doc(frm,cdt)
		if (carro){
			cur_frm.doc.marca_veiculo = carro.make
			cur_frm.doc.modelo_veiculo = carro.model
			cur_frm.doc.cor_veiculo = carro.color
			cur_frm.doc.grupo = carro.grupo
			
			//cur_frm.doc.combustivel = carro.fuel_type
			if (carro.grupo != undefined){
				tarifario_("Tarifas",carro.grupo)
			}

		}
		
		cur_frm.refresh_fields();

	});


}



var tarifario_ = function(frm,cdt,cdn){
	frappe.model.with_doc(frm, cdt, function() { 
		var tarifarios = frappe.model.get_doc(frm,cdt)
		if (tarifarios){
			console.log ('PREcos dos Grupos')
			console.log(moment(cur_frm.doc.data_estimada_entrada_estacao).format('D') - moment(cur_frm.doc.data_saida_estacao).format('D'))

			cur_frm.doc.por_km = tarifarios.preco_por_km
			cur_frm.doc.fim_de_semana = tarifarios.especial_fim_de_semana
			cur_frm.doc.seguro_cdw = tarifarios.seguro_cdw
			cur_frm.doc.seguro_tlw = tarifarios.seguro_tlw
			cur_frm.doc.preco_dia_basico = tarifarios.preco_por_dia


			/*

			Tem muitas validacoes por fazer ...
			1/3 dias e se fizer 100km esta tudo caso ultrapasse tem que calcular a diff de km por p_km 
			Se data entrada - data saida =4 or ate 7 dias ou 8/15 ou +15 nao tem limites de KM

			Se
			
			*/

			//cur_frm.doc.valor_pdia = termos1.basico_dia
			if (cur_frm.doc.entrada_ou_saida_viatura == 'Saida'){
				cur_frm.doc.total_dias = tarifarios.preco_por_dia * (frappe.datetime.get_day_diff(cur_frm.doc.data_estimada_entrada_estacao,cur_frm.doc.data_saida_estacao) + 1) // (moment(cur_frm.doc.data_estimada_entrada_estacao).format('D') - moment(cur_frm.doc.data_saida_estacao).format('D'))

			}else{
				cur_frm.doc.total_dias = tarifarios.preco_por_dia * (frappe.datetime.get_day_diff(frappe.datetime.now_datetime(),cur_frm.doc.data_saida_estacao) + 1) //(moment(frappe.datetime.now_datetime()).format('D') - moment(cur_frm.doc.data_saida_estacao).format('D'))

			}

		}
		
		cur_frm.refresh_fields();

	});


}


