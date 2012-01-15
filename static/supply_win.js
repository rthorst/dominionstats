// Change this if you aren't running a server locally, so you'll make requests
// to councilroom.com.
var have_local_server_instance = true;
// If you are changing this script, please change the developer name to 
// something unique, just for logging/server admin purposes.
var developer_id = "rrenaud";  
var full_path_to_councilroom = "";
var saved_stats = {};
var fetched_cards = {};
var suppressed_cards = {};

if (!have_local_server_instance) {
    full_path_to_councilroom = "http://councilroom.com/"
}

function MergeStats(new_stats, cond1, cond2) {
  for (k in new_stats) {
    var key = k + cond1 + cond2;
    saved_stats[key] = new_stats[k];
    saved_stats[key].name = k;
    saved_stats[key].condition = cond1;
    saved_stats[key].condition2 = cond2;
  }
};

function CardDataUrl(args) {
    if (!args) args = {};

    var url = full_path_to_councilroom + 
        "supply_win_api?dev=" + developer_id;
    if (args.cond1) {
        url += '&cond1=' + encodeURIComponent(args.cond1);
    }
    if (args.cond2) {
        url += "&cond2=" + encodeURIComponent(args.cond2);
    }
    return url;
}

function IsSavedCard(card_name) {
  return fetched_cards[card_name];
}

function IsSuppressedCard(card_name) {
  return suppressed_cards[card_name];
}

function SuppressCard(card_name) {
  card_name = unescape(card_name);
  suppressed_cards[card_name] = true;
  RenderWinStats();
}

function ConditionUpon(card_name) {
    card_name = unescape(card_name);
    if (IsSuppressedCard(card_name)) {
      suppressed_cards[card_name] = false;
      RenderWinStats();
      return;
    }

    fetched_cards[card_name] = true;
    console.log("conditioning on " + card_name);
    var c = $.ajax(
        {url: CardDataUrl({cond1: card_name}),
         dataType: "json",
         success: function(server_stats) { 
             MergeStats(server_stats, card_name); 
             RenderWinStats(); 
         }
        });
};

function SecondCondition(card_name) {
  card_name = unescape(card_name);
  
  var cond1s = [];
  for (k in fetched_cards) {
    if (!IsSuppressedCard(k)) {
      cond1s.push(k);
    }
  }
    
  // Should maybe limit size of cond1s, could end up making lots of requests
  // to councilroom if not.
  var all_results = {}
  var countdown = cond1s.length;
  $(cond1s).each(
    function() {
      var cond1 = this;
      $.ajax(
          {url: CardDataUrl({cond1: cond1, cond2: card_name}),
           dataType: "json",
           success: 
             function(server_stats) { 
               MergeStats(server_stats, cond1, card_name);
               countdown--;
               if (countdown == 0) {
                 RenderWinStats();
               }
             }
           });
    });
}

function RenderWinStats() {
    var output = '<table id="data_table">';
    output += '<thead>';
    output += '  <th>Name</th>';
    output += '  <th>Condition</th>';
    output += '  <th>Condition2</th>';
    output += '  <th>Avail</th>';
    output += '  <th>%+</th>';
    output += '  <th>Per gain</th>';
    output += '  <th>Any gain</th>';
    output += '  <th>Num gained</th>';
    output += '  <th>cond</th>';
    //  output += '  <th>dep</th>';
    output += '</thead>';
    for (k in saved_stats) {
        var stat = saved_stats[k];
        
        if (stat.condition && suppressed_cards[stat.condition]) {
          continue;
        }
        
        var weighted_gain_stat = MeanVarStat(stat.win_weighted_gain);
        var any_gain_stat = MeanVarStat(stat.win_given_any_gain);
        var no_gain_stat = MeanVarStat(stat.win_given_no_gain);
        var avail = any_gain_stat.Freq() + no_gain_stat.Freq();
        var percent_gained = Round(100 * any_gain_stat.Freq() / avail, 1); 
        var num_gain = Round(weighted_gain_stat.Freq() / avail, 2);
        output += "<tr>";
        output += "  <td>" + stat.name + "</td>";
        
        if (stat.condition) {
          output += "  <td>" + stat.condition;
          output += "  <button onclick=SuppressCard('" + 
                escape(stat.condition) + "')>r</button></td>";
        } else {
          output += "  <td></td>";
        }
        
        if (stat.condition2) {
          output += "  <td>" + stat.condition2 + "</td>";
        } else {
          output += "  <td></td>";
        }
        
        output += "  <td>" + avail + "</td>";
        output += "  <td>" + percent_gained + "</td>";
        output += "  <td>" + weighted_gain_stat.RenderMeanVar(2) + "</td>";
        output += "  <td>" + any_gain_stat.RenderMeanVar(2) + "</td>";
        output += "  <td>" + num_gain + "</td>";
        
        output += "  <td>";
        if (!stat.condition) {
          if (!IsSavedCard(stat.name) || IsSuppressedCard(stat.name)) {
            output += "    <button onclick=ConditionUpon('" + 
                  escape(stat.name) + "')>c</button>";
          } 
            output += "    <button onclick=SecondCondition('" + 
                escape(stat.name) + "')>c2</button>";
        }
        output += "  </td>";
        //        output += "  <td><button>d</button></td>";
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
             MergeStats(base_stats, "", "");  
             RenderWinStats(); 
         }
        });
};

jQuery.event.add(window, "load", RefreshData);