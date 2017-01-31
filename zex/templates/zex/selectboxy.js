var selectboxy = {{% if obdobia %}{% for obdobie in obdobia %}
	"{{ obdobie.polia.nazov }}": {
		"nazov": "{{ obdobie.polia.nazov }}",
		"zasadnutia": {{% if obdobie.zasadnutia %}{% for zasadnutie in obdobie.zasadnutia %}
			"{{ zasadnutie.polia.datum|date:'j.n.Y' }}": {
				"datum": "{{ zasadnutie.polia.datum }}",
				"body": {{% if zasadnutie.body %}{% for bod in zasadnutie.body %}
					"{{ bod.cislo|floatformat }}": "{{ bod.cislo|floatformat }}. {{ bod.nazov }}",{% endfor %}{% endif %}
				}
			},{% endfor %}{% endif %}
		}
	},{% endfor %}{% endif %}
};
