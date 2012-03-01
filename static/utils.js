function Round(val, places) {
  var pow = Math.pow(10, places);
  return Math.round(val * pow) / pow;
};

var card_list = null;
var keyed_cards = {};

function InitCardGlobber() {
  return $.ajax(
    {url: 'static/card_list.js',
     dataType: 'json',
     success: function(data) {
       // hack, I don't understand this, according to the
       // docs, this should be parsed for me already.
       card_list = eval(data);
       for (var i = 0; i < card_list.length; ++i) {
         keyed_cards[card_list[i].Singular] = card_list[i];
       }
     }});
};

// Requires InitCardGlobber ajax to be finished.
function IsVictory(card_name){
  return keyed_cards[card_name]['Victory'] == '1';
};

function IsReaction(card_name) {
  return keyed_cards[card_name]['Reaction'] == '1';
};

function NumActions(card_name) {
  return parseInt(keyed_cards[card_name]['Actions']) || 1;
};

function ExpandCardGlob(glob) {
  // Glob is either something like "Worker's Village,Smithy" or
  // "actions==2&&cards>=1".
  var ret = [];

  var chunks = glob.split(',');

  var i = 0;
  var matched_chunk_inds = {};

  try {
    for (i = 0; i < card_list.length; ++i) {
      var per_card_attrs = card_list[i];
      var lower_name = per_card_attrs.Singular.toLowerCase();
      for (var j = 0; j < chunks.length; ++j) {
        if (chunks[j].toLowerCase() == lower_name) {
          ret.push(per_card_attrs.Singular);
          matched_chunk_inds[j] = true;
        }
      }
    }
    var remaining_glob = [];
    for (var i = 0; i < chunks.length; ++i) {
      if (!matched_chunk_inds[i]) {
        remaining_glob.push(chunks[i]);
      }
    }
    glob = remaining_glob.join(',');
    for (var i = 0; i < card_list.length; ++i) {
      var per_card_attrs = card_list[i];
      for (k in per_card_attrs) {
	var val = per_card_attrs[k];
	if (isNaN(parseInt(val))) {
	  eval(k + '= "' + val + '"');
	} else {
	  eval(k + '=' + val);
	}
      }
      if (eval(glob)) {
	ret.push(per_card_attrs.Singular);
      }
    }
  } catch (err) {
    console.log(i);
    console.log(card_list[i]);
    console.log(glob);
    console.log(err);
  }
  return ret;
};
