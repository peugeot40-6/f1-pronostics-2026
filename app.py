
<div class="container">
<h2>Historique</h2>
<table>
<tr><th>GP</th><th>Joueur</th><th>Points</th></tr>
{% for r in records %}
<tr>
<td>{{ r["Grand Prix"] }}</td>
<td>{{ r["Participant"] }}</td>
<td>{{ r["Total"] }}</td>
</tr>
{% endfor %}
</table>
</div>
