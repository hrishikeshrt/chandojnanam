var all_occurrences = new Set();
var all_roots = new Set();
var storage = window.localStorage;

const $corpus_table = $("#corpus_viewer");

const $form_prepare_entity = $("#form_prepare_entity");
const $line_id = $("#line_id");
const $entity_occurrence = $("#input_entity_occurrence");
const $entity_root = $("#input_entity_root");
const $entity_type = $("#input_entity_type");

const $add_button = $("#add_entity")

const $confirm_button = $("#confirm_entity_list");
const $entity_list = $("#entity_list");

const $datalist_occurrence = $("#datalist_occurrence");
const $datalist_root = $("#datalist_root");

$corpus_table.on('load-success.bs.table', function (e, data, status, xhr) {
    all_occurrences.clear();
    all_roots.clear();
    for (row of data) {
        for (entity of row.entity) {
            all_occurrences.add("<option>" + entity.occurrence + "</option>");
            all_roots.add("<option>" + entity.root + "</option>");
        }
    }
});

$corpus_table.on('check.bs.table', function (e, row, $element, field) {
    $corpus_table.bootstrapTable('collapseAllRows');
    $corpus_table.bootstrapTable('expandRow', $element.data('index'));
});

$corpus_table.on('expand-row.bs.table', function (e, index, row, $detail) {
    $line_id.val(row.line_id);
    $entity_occurrence.val("");
    $entity_root.val("");

    var row_occurrences = new Set ();
    var row_roots = new Set();
    $.each(row.analysis, function(index, word) {
        if (word.is_noun) {
            row_occurrences.add("<option>" + word.original + "</option>");
            row_roots.add("<option>" + word.root + "</option>");
        }
    });

    var suggest_occurrences = new Set([...row_occurrences, ...all_occurrences]);
    var suggest_roots = new Set([...row_roots, ...all_roots]);

    $datalist_occurrence.html("");
    $datalist_occurrence.append(Array.from(suggest_occurrences).join(""));
    $datalist_root.html("");
    $datalist_root.append(Array.from(suggest_roots).join(""));

    var entity_list_html = [];
    $.each(row.entity, function (index, entity) {
        entity_html = entity_formatter(entity.occurrence, entity.root, entity.type);
        entity_list_html.push(entity_html);
    });
    var unconfirmed = storage.getItem(row.line_id);
    if (unconfirmed !== null) {
        $.each(JSON.parse(unconfirmed), function (index, entity) {
            entity_html = entity_formatter(entity.occurrence, entity.root, entity.type, "list-group-item-warning");
            entity_list_html.push(entity_html);
        });
    }
    $entity_list.html("").append(entity_list_html.join(""));
    $('[name="entity"]').bootstrapToggle();
});

$corpus_table.on('page-change.bs.table', function (e, number, size) {
    $line_id.val("");
    $entity_occurrence.val("");
    $entity_root.val("");
});
