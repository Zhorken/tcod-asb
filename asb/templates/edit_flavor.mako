<%inherit file='/base.mako'/>\
<%namespace name="h" file="/helpers/helpers.mako"/>\
<%block name='title'>Edit ${thing.name} - The Cave of Dragonflies ASB</%block>\
<% from asb.markdown import md, chomp %>

<h1>Edit ${thing.name}</h1>
<form action="${request.path}" method="POST" class="editor">
${form.csrf_token}
${form.edit_time}
${h.form_error_list(*form.errors.values())}

<dl>
    <dt>${form.summary.label}</dt>
    <dd>${form.summary}</dd>

    <dt>${form.description.label}</dt>
    <dd>${form.description(rows=10, cols=100)}</dd>

    <dt>${form.notes.label}</dt>
    <dd>${form.notes(rows=7, cols=100)}</dd>
</dl>

${form.preview}
${form.save}
</form>

% if form.edit_time.errors:
<h1>Current revision</h1>
<p><b>Summary:</b> ${thing.summary | md.convert, chomp, n}</p>

<h2>Description</h2>
${thing.description | md.convert, n}

% if thing.notes:
<h2>Notes</h2>
${thing.notes | md.convert, n}
% endif
% endif

<h1>Preview</h1>
<p><b>Summary:</b> ${form.summary.data | md.convert, chomp, n}</p>

<h2>Description</h2>
${form.description.data | md.convert, n}

% if form.notes.data:
<h2>Notes</h2>
${form.notes.data | md.convert, n}
% endif
