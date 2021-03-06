// Copyright (c) 2017, Helio de Jesus and contributors
// For license information, please see license.txt



/* globals jscolor */
frappe.provide("frappe.website_theme");
$.extend(frappe.website_theme, {
	color_variables: ["background_color", "top_bar_color", "top_bar_text_color",
		"footer_color", "footer_text_color", "text_color", "link_color"]
});

frappe.ui.form.on("App Theme", "onload_post_render", function(frm) {
	frappe.require('assets/frappe/js/lib/jscolor/jscolor.js', function() {
		$.each(frappe.website_theme.color_variables, function(i, v) {
			$(frm.fields_dict[v].input).addClass('color {required:false,hash:true}');
			console.log('pintou!!!!')
		});
		jscolor.bind();
	});
});

frappe.ui.form.on("App Theme", "onload", function(frm) {
	console.log('Inicio ', frm.doc.username)
	console.log(frappe.session.user)
	cssText = ''
	if (cur_frm.docname.substring(0,3)=="New" || cur_frm.docname.substring(0,3)=="Nov"){
		var dd = document.createElement('link')
		//dd.setAttribute('rel','stylesheet')
		dd.setAttribute('rel','preload')
		dd.setAttribute('as','style')
		dd.setAttribute('onload',"this.rel='stylesheet'")
		dd.setAttribute('type','text/css')
		//dd.setAttribute('href','assets/angola_erp/css/erpnext/bootstrap.css?ver=1509829457.0')
		dd.setAttribute('href','assets/angola_erp/css/erpnext/' + frappe.session.user + '_bootstrap.css')
		document.getElementsByTagName('head')[0].appendChild(dd)
	}


	//Should read the default settings from the APP theme ...
	//css_file='./assets/css/desk.min.css'

	css_file='./assets/angola_erp/css/bootstrap.css'
	if (frm.doc.username){
		css_file_user = './assets/angola_erp/css/erpnext/' + frm.doc.username + '_bootstrap.css'
	}else{
		css_file_user = './assets/angola_erp/css/erpnext/' + frappe.session.user + '_bootstrap.css'
	}





	console.log('filecss ',css_file)
//	if (frm.doc.css ==""){
//		$.get(css_file, function (cssText) {
			//console.log(cssText)

			//frm.doc.css = ".navbar-header {			display: true;		  }"
			//frm.doc.css = '<style />' + cssText;
//			cur_frm.set_value('css',cssText)
//			console.log('css')

//		});
//	}	



});

frappe.ui.form.on("App Theme", "refresh", function(frm) {
	console.log('Refresh')
	console.log('novo ',cur_frm.docname.substring(0,3))
	if (frm.doc.username){
		css_file_user = './assets/angola_erp/css/erpnext/' + frm.doc.username + '_bootstrap.css'
	}else{
		css_file_user = './assets/angola_erp/css/erpnext/' + frappe.session.user + '_bootstrap.css'
	}

	if (cur_frm.docname.substring(0,3)!="New" && cur_frm.docname.substring(0,3)!="Nov"){

		$.ajax({
			cache: false,
			url: css_file_user,
			type: 'HEAD',
			success: function(data){
				console.log('REFRESH ficheiro existe ', css_file_user);
				css_file = css_file_user;
			},
			error: function(date){
				console.log('REFRESH nao existe ...', css_file_user)
			},
		})

		$.ajax({
			cache: false,
			url: css_file_user,
			type: 'HEAD',
			success: function(data){
				console.log(data)
				console.log('ficheiro existe ', css_file_user);
				css_file = css_file_user;
				$.when($.get(css_file_user))
					.done(function(response) {
						//$('<style />').text(response).appendTo($('head'));
						//$('div').html(response);
						console.log (response)

						//background-color
						bbcolor = response.substring(response.search('background-color'),response.search(';}'))
						bbcolor = bbcolor.substring(bbcolor.search('#'),bbcolor.length)
						ffsize = response.substring(response.search('font-size'))
						ffsize = ffsize.substring(ffsize.search(':')+1,ffsize.search(';'))

						//cur_frm.set_value('background_color',$("#body_div").css(bbcolor))
						//cur_frm.set_value('font_size',$("#body_div").css(ffsize))

						$('input[data-fieldname="background_color"]').css("background-color",cur_frm.doc.background_color)
						//frm.refresh_fields()

					});
			},
			error: function(data){
				console.log('nao existe ...', data)
			},
		})


	}
//	frm.set_intro(__('Default theme is set in {0}', ['<a href="#Form/Website Settings">'
//		+ __('Website Settings') + '</a>']));

//	frm.toggle_display(["module", "custom"], !frappe.boot.developer_mode);

//	if (!frm.doc.custom && !frappe.boot.developer_mode) {
//		frm.set_read_only();
//		frm.disable_save();
//	} else {
//		frm.enable_save();
//	}



});


frappe.ui.form.on("App Theme", "theme", function(frm,cdt,cdn){
	console.log('theme')
	
});	


frappe.ui.form.on("App Theme","background_color", function (frm,cdt,cdn) {
	console.log ('Aplica cor no fundo')
	$("#body_div").css("background-color", frm.doc.background_color);
	$("#page_modules").css("background-color", frm.doc.background_color);
	//document.querySelector("<link type="text/css" rel="stylesheet" href="assets/angola_erp/css/bootstrap.css") <link type="text/css" rel="stylesheet" href="assets/angola_erp/css/erpnext/bootstrap.css">)
	

});

frappe.ui.form.on("App Theme","font_size", function (frm,cdt,cdn) {
	console.log ('Aplica tamanho Fonte')
	$("#body_div").css("font-size", frm.doc.font_size);

});
