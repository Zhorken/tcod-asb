<%inherit file='/base.mako'/>\
<%namespace name="h" file="/helpers/helpers.mako"/>\
<%namespace name="t" file="/helpers/tables.mako"/>\
<%block name='title'>Manage items - The Cave of Dragonflies ASB</%block>\
<%! from asb.markup.markdown import render as md %>

<% tickies = iter(take_form.holders) %>
<%def name="take_item_ticky(pokemon)">
<td class="input ticky">${next(tickies)() | n}</td>
</%def>

<p><a href="/items/buy">Buy items →</a></p>

<h1>Bag</h1>
<table class="standard-table effect-table">
<col class="item-icon">
<col class="item">
<col class="stat">
<col class="give">
<col class="summary">

<thead>
    <tr>
        <th colspan="2">Item</th>
        <th><abbr title="Quantity">Qty</abbr></th>
        <th>Give</th>
        <th>Summary</th>
    </tr>
</thead>

<tbody>
    % for (item, quantity) in request.user.bag:
    <tr>
        <td class="icon">
            <img src="/static/images/items/${item.identifier}.png" alt="">
        </td>
        <td>${h.link(item)}</td>
        <td class="stat">${quantity}</td>
        <td class="give focus-column">
            <a href="${request.resource_url(item, 'give')}">
                % if item.identifier in ['ability-capsule', 'rare-candy']:
                Use
                % else:
                Give
                % endif
            </a>
        </td>
        <td>${item.summary | md}</td>
    </tr>
    % endfor
</tbody>
</table>
</form>

% if holders:
<h1>Held</h1>
% if take_form.errors:
<ul class="form-error">
   % for field, errors in take_form.errors.items():
   % for error in errors:
   <li>${error}</li>
   % endfor
   % endfor
</ul>
% endif

<form action="/items/manage" method="POST">
${take_form.csrf_token() | n}

${t.pokemon_table(
    *(group for (header, group) in holders),
    subheaders=(header for (header, group) in holders),
    skip_cols=['item', 'trainer'],
    extra_left_cols=[
        {'col': t.ticky_col, 'th': t.empty_header, 'td': take_item_ticky},
        {'col': t.item_col, 'th': t.item_header, 'td': t.item_cell},
    ]
)}

${take_form.take() | n}
</form>
% endif
