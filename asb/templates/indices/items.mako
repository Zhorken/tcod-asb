<%inherit file='/base.mako'/>\
<%block name='title'>Items - The Cave of Dragonflies ASB</%block>\

<table class="effect-table">
<thead>
<tr>
    <th colspan="2">Item</th>
    <th>Summary</th>
</tr>
</thead>

% for category in item_categories:
<tbody>
    <tr class="subheader-row">
        <td colspan="3">${category.name}</td>
    </tr>

    % for item in category.items:
    <tr>
        <td class="icon"><img src="/static/images/items/${item.identifier}.png" alt=""></td>
        <td class="focus-column"><a href="/items/${item.identifier}">${item.name}</a></td>
        <td>${item.summary}</td>
    </tr>
    % endfor
</tbody>
% endfor
</table>
