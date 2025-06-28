<head>
<style>
    table, th, td {
	border: 1px solid black;
	border-collapse: collapse;
    }
    td {
	padding-left: 5px;
	padding-right: 10px;
    }
</style>
</head>
<body>
{% for source in sources %}
    <div style="padding-left: 10%; padding-right: 10%;">
    <h2 style="text-decoration: underline;">{{source.name}}</h2>
    {% for group in source.groups %}
	<p><b>{{group.name}}</b> {% if group.desc != "" %}<i>({{group.desc}})</i> {% endif %}</p>
	<table>
	{% for row in group.rows %}
	    <tr>
	    <td><a href="{{row.url}}">link</a></td>
	    <td>{{row.title}}</td>
	    <td>{{row.date}}</td>
	    </tr>
	{% endfor %}
	</table>
    {% endfor %}
    </div>
{% endfor %}
</body>
