/* A simple prior for the mean var stats, corresponding to the win points for
 * one 2 player win and one 2 player loss.  This is nice to smooth out
 * the estimates for rare events (if something won twice and never lost, 
 * you don't really expect that thing to always win). */
function SimpleWinPrior() {
    return [2, 2, 4];
};

/* A summary of the distribution of a random variable. 
 * mvs_data is a list of 3 items, containing the frequency, sum, and 
 * sum of squares of some observations.  An optional prior has the same format.
 */
function MeanVarStat(mvs_data, opt_prior_data) {
  mvs_data.freq = mvs_data.freq || mvs_data[0];
  mvs_data.sum = mvs_data.sum || mvs_data[1];
  mvs_data.sum_sq = mvs_data.sum_sq || mvs_data[2];
  if (opt_prior_data) {
    mvs_data.freq += opt_prior_data[0];
    mvs_data.sum += opt_prior_data[1];
    mvs_data.sum_sq += opt_prior_data[2];
  }
  var mvs = {};
  mvs.Mean =  function() { return (mvs_data.sum) / (mvs_data.freq); };
  mvs.Variance = function() {
    if (mvs_data.freq <= 1) {
      return 1e10;
    }
    return ((mvs_data.sum_sq) - ((mvs_data.sum) * (mvs_data.sum)) /
	    (mvs_data.freq - 1)) / (mvs_data.freq - 1);
  };
  mvs.SampleStdDev = function() {
    return Math.sqrt(mvs.Variance() / (mvs_data.freq));
  };
  mvs.Freq = function() {
    return mvs_data.freq;
  };
  mvs.RenderMeanVar = function(digits) {
      if (!digits) digits = 0;
      return Round(mvs.Mean(), digits) + " &plusmn; " + 
          Round(mvs.SampleStdDev(), digits);
  }
  return mvs;
};
