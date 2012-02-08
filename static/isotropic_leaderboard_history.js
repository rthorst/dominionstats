ILH = {};

ILH.process_raw_history_data = function (raw_history_data) {
    var entries = [],
        index,
        row,
        entry;

    for (index in raw_history_data) {
        row = raw_history_data[index];
        entry = {
            date: row[0],
            timestamp: Date.parse(row[0]),
            skill_mean: row[1],
            skill_error: row[2],
            rank: row[3],
            eligible_games_played: row[4]
        };
        entries.push(entry);
    }

    return entries;
};

ILH.plot_level_graph = function (entries, id) {
    var index,
        entry,
        points = [],
        data,
        options;

    for (index in entries) {
        entry = entries[index];
        points.push([entry.timestamp, entry.skill_mean - entry.skill_error]);
    }

    data = [{
        label: 'Level',
        data: points,
        lines: {
            show: true
        },
        points: {
            show: true
        }
    }];
    options = {
        legend: {
            position: 'nw'
        },
        xaxis: {
            mode: 'time',
            timeformat: '%b %d, %y'
        }
    };

    $.plot($('#' + id), data, options);
};

ILH.plot_num_games_graph = function (entries, id) {
    var index,
        entry,
        points = [],
        data,
        options;

    for (index in entries) {
        entry = entries[index];
        points.push([entry.timestamp, entry.eligible_games_played]);
    }

    data = [{
        label: '# Games',
        data: points,
        lines: {
            show: true
        },
        points: {
            show: true
        }
    }];
    options = {
        legend: {
            position: 'nw'
        },
        xaxis: {
            mode: 'time',
            timeformat: '%b %d, %y'
        }
    };

    $.plot($('#' + id), data, options);
};

