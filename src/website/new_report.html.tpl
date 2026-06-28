<head>
<style>
table {
  border-collapse: separate;
  border-spacing: 0 8px;
}

table td {
  background: #f5f5f5;
  padding: 8px 12px;
}

table tr td:first-child {
  border-radius: 6px 0 0 6px;
}

table tr td:last-child {
  border-radius: 0 6px 6px 0;
}
</style>
<meta charset="UTF-8">
</head>
<body>
    <div style="padding-left: 10%; padding-right: 10%;">
	<table>
		<tr>
			<td>____</td>
			<td><b>Type</b></td>
			<td><b>Source</b></td>
			<td><b>Title</b></td>
			<td><b>Published</b></td>
		</tr>
	{% for scrape in scrapes %}
		<tr>
		<td><a href={{scrape[3]}}>link</a></td>
		<td>{{scrape[0]}}</td>
		<td>{{scrape[1]}}</td>
		<td>{{scrape[2]}}</td>
		<td>{{scrape[4]}}</td>
		</tr>
	{% endfor %}
	</table>
    </div>
</body>