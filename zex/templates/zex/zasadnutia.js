var zasadnutia = {{% if zasadnutia %}{% for zasadnutie in zasadnutia %}
	"{{ zasadnutie.polia.datum|date:'j.n.Y' }}": {
		"datum": "{{ zasadnutie.polia.datum }}",
		"body": {{% if zasadnutie.body %}{% for bod in zasadnutie.body %}
			"{{ bod.cislo|floatformat }}": "{{ bod.cislo|floatformat }}. {{ bod.nazov }}",{% endfor %}{% endif %}
		}
	},{% endfor %}{% endif %}
};
