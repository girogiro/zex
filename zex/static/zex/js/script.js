$(document).ready(function() {

	/* zistenie poli v URL na predvyplnenie vyhladavacieho formulara */
	pathArray = window.location.pathname.split( '/' );
	zvolene_zasadnutie = (pathArray.length > 2) ? pathArray[2] : '';
	zvoleny_bod = (pathArray.length > 3) ? pathArray[3] : '';
	hladany_text = $.getUrlVar('q');
	
	/* predvypln hladany text, ak je v URL */
	if (hladany_text)
		hladany_text = decodeURIComponent(hladany_text);
		$('#text-input').val(hladany_text);
	
	/* napln vyber zasadnutia */
	options = '\n<option value="">všetky</option>';
	$.each(zasadnutia, function(id, zasadnutie) {
		options += "\n<option value=" + id + (zvolene_zasadnutie == id ? ' selected="selected">' : '>') + zasadnutie.datum + "</option>";
	});
	$('#zasadnutie-select').html(options);
	
	/* napln vyber bodu */
	$('#zasadnutie-select').change(function() {
		options = '\n<option value="">všetky</option>\n';
		if (!this.value) {
			$('#bod-select').html(options);
			$('#bod-select').prop('disabled', 'disabled');
		} else {
			body = zasadnutia[this.value]['body'];
			$.each(body, function(id, bod) {
				options += "\n<option value=" + id + (zvoleny_bod == id ? ' selected="selected">' : '>') + bod + "</option>";
			});
			$('#bod-select').html(options);
			$('#bod-select').prop('disabled', false);
		}
	});
	$('#zasadnutie-select').trigger('change');
	
	/* vytvor peknu URL po odoslani formulara */
	$('#search-form').submit(function() {
		path = '/zex/';
		if ($('#zasadnutie-select').val())
			path += $('#zasadnutie-select').val() + '/';
		if ($('#bod-select').val())
			path += $('#bod-select').val() + '/';
		if ($('#text-input').val()) {
			query = $('#text-input').val().trim();
			query = query.replace(/\W/g, ' ').replace(/ +/g, ' ');
			path += '?q=' + encodeURIComponent(query);
		}
		document.location = path;
		return false;
	});

	if (hladany_text)
		$('#right-panel').highlight(hladany_text.trim().split(/ +/g), true);
});

/* funkcia na pohodlne citanie parametrov v URL */
$.extend({
	getUrlVars: function(){
		var vars = [], hash;
		var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
		for (var i = 0; i < hashes.length; i++) {
			hash = hashes[i].split('=');
			vars.push(hash[0]);
			vars[hash[0]] = hash[1];
		}
		return vars;
	},
	getUrlVar: function(name) {
		return $.getUrlVars()[name];
	}
});
