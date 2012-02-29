// Change this if you aren't running a server locally, so you'll
// make requests to councilroom.com.
var have_local_server_instance = false;
// If you are changing this script, please change the developer name to
// something unique, just for logging/server admin purposes.
var developer_id = "rrenaud";
var full_path_to_councilroom = "";

if (!have_local_server_instance) {
  full_path_to_councilroom = "http://councilroom.com:8080/";
// Change this if you aren't running a server locally, so you'll
}

var saved_stats = [];

function ScoreStats(card_name, win_given_any_gain, win_given_no_gain) {
  var win_rate_given_gain = win_given_any_gain.Mean();
  var wagf = win_given_any_gain.Freq() + 1;
  var wngf = win_given_no_gain.Freq() + 1;
  var log_odds_any_gained = Math.log(wagf / (wagf + wngf));
  var num_plus_actions = NumActions(card_name);
  var is_vp = IsVictory(card_name);
  var is_reaction = IsReaction(card_name);
  // This function was found by card_ranker/optimize_ranks.py
  return (52.926 * win_rate_given_gain +
          1.358 * log_odds_any_gained +
          -1.161 * num_plus_actions +
          -1.712 * is_vp +
          1.625 * is_reaction);
};

function CardDataUrl() {
  var targets = ExpandCardGlob($('#targets').val());
  var interaction = ExpandCardGlob($('#interaction').val());
  var nested =  $('#nested').is(':checked');
  var unconditional = $('#unconditional').is(':checked');

  var url = full_path_to_councilroom +
    "supply_win_api?dev=" + developer_id;

  if (targets) url += '&targets=' + encodeURIComponent(targets);
  if (interaction) url += '&interaction=' + encodeURIComponent(interaction);
  if (nested) url += '&nested=true';
  if (unconditional) url += '&unconditional=true';
  return url;
}


function RenderWinStats() {
  var output = '<table id="data_table">';
  output += '<thead>';
  output += '  <th>Name</th>';
  output += '  <th>Cond</th>';
  output += '  <th>Cond2</th>';
  output += '  <th>Avail</th>';
  output += '  <th>%+</th>';
  output += '  <th>Per gain</th>';
  output += '  <th>Any gain</th>';
  output += '  <th>Num gained</th>';
  output += '  <th>Quality</th>';
  output += '  <th>&Delta; Qual</th>';
  output += '</thead>';
  function LeastConditionedFirst(a, b) {
    return a.condition.length - b.condition.length;
  }
  saved_stats.sort(LeastConditionedFirst);
  var base_qualities = {};
  for (var i = 0; i < saved_stats.length; ++i) {
    var stat = saved_stats[i].stats;
    var name = saved_stats[i].card_name;

    var condition = saved_stats[i].condition[0] || '';
    var condition2 = saved_stats[i].condition[1] || '';

    var weighted_gain_stat = MeanVarStat(stat.win_weighted_gain);
    var any_gain_stat = MeanVarStat(stat.win_given_any_gain);
    var no_gain_stat = MeanVarStat(stat.win_given_no_gain);
    var avail = any_gain_stat.Freq() + no_gain_stat.Freq();
    var percent_gained = Round(100 * any_gain_stat.Freq() / avail, 1);
    var num_gain = Round(weighted_gain_stat.Freq() / avail, 2);
    var quality = ScoreStats(name, any_gain_stat, no_gain_stat);
    stat.quality = quality;
    var delta_quality = '';
    if (condition.length == 0) {
      base_qualities[name] = quality;
    } else {
      delta_quality = Round(quality - base_qualities[name], 2);
    }

    output += "<tr>";
    output += "  <td>" + name + "</td>";

    output += "  <td>" + condition + '</td>';
    output += "  <td>" + condition2 + "</td>";

    output += "  <td>" + avail + "</td>";
    output += "  <td>" + percent_gained + "</td>";
    output += "  <td>" + weighted_gain_stat.RenderMeanVar(2) + "</td>";
    output += "  <td>" + any_gain_stat.RenderMeanVar(2) + "</td>";
    output += "  <td>" + num_gain + "</td>";

    output += "  <td>" + Round(quality, 2) + "</td>";
    output += "  <td>" + delta_quality + "</td>";

    output += "</tr>\n";
  }
  output += "</table>";
  $("#data_display").html(output);
  $("#data_table").dataTable(
    {"aaSorting": [[ 0, "asc" ]],
     "bPaginate": false});
};

function RefreshData() {
  console.log("calling refresh");
  var c = $.ajax(
    {url: CardDataUrl(),
     dataType: "json",
     success: function(base_stats) {
       saved_stats = base_stats;
       console.log('about to render');
       RenderWinStats();
     }
    });
};

function DisplayUrl() {
  var wl = window.location;
  var new_url = 'http://' + wl.host + wl.pathname + '?';
  if ($('#targets').val())
    new_url += '&targets=' + encodeURIComponent($('#targets').val());
  if ($('#interaction').val())
    new_url += '&interaction=' + encodeURIComponent($('#interaction').val());
  new_url += '&nested=' + $('#nested')[0].checked;
  new_url += '&unconditional=' + $('#unconditional')[0].checked;
  $('#url_display').val(new_url);
  var offset = $('#getlink').offset();
  $('#url_display').css(
    { left:offset.left, top:offset.top,
      height:"25px"}
  ).show().select();
};

$(document).click(
  function (e) {
    if (e.target.id != "getlink") {
      $('#url_display').hide();
    }
  }
);

jQuery.event.add(window, "load",
  function() {
    var q = $.parseQuery();
    console.log(q);
    if (q.targets) $('#targets').val(q.targets);
    if (q.interaction) $('#interaction').val(q.interaction);
    if (q.nested) $('#nested')[0].checked = q.nested != 'false';
    if (q.unconditional)
      $('#unconditional')[0].checked = q.unconditional != 'false';

    InitCardGlobber().then(RefreshData);
  }
);