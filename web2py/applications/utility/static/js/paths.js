(function() {
    var PathApp = function(options) {
        this.workerids = [];
        this.workers = [];
        this.timeFormat = "HH:mm:ss, yyyy-MM-dd";
        
        if (options.worker_id) {
            this.workerids.push(options.worker_id);
        }
        
        this.study_id = options.study_id;
    };
    PathApp.prototype.get_worker_data = function(workerid) {
        var self = this;
        self.workers = [];
        
        if (!workerid) {
            for (var i in self.workerids) {
                var workerid = self.workerids[i];                
                self.get_worker_data(workerid);
            }
        } else {
            var worker = new Worker(workerid);
            self.view.append(worker.render());
            
            $.get('/utiliscope/worker_actions.json/' + self.study_id + "?worker_id=" + workerid)
            .done(function(data) {
                self.addWorker(worker);
                worker.setActions(data.actions);
                worker.view.replaceWith(worker.render());
                worker.positionHits();
            })
            .fail(function(jqXHR, textStatus) {
                console.log("Failed to get data for worker " + workerid + ": " + textStatus);
            });
        }
    }
    
    PathApp.prototype.addWorker = function(worker) {
        this.workers.push(worker);
    }
    
    PathApp.prototype.get_workerids = function() {
        var self = this;
        if (self.workerids.length == 0) {
            $.get('/utiliscope/worker_ids.json/' + self.study_id)
            .done(function(data) {
                self.workerids = data.worker_ids;
                self.get_worker_data();
            })
            .fail(function(jqXHR, textStatus) {
                console.log("Failed to get worker ids: " + textStatus);
            });
        } else {
            self.get_worker_data();
        }
    }
    
    PathApp.prototype.render = function() {
        this.view = $('#path-app');
        this.view.html('');
        return this.view;
    }
    
    PathApp.prototype.start = function() {
        this.render();
        this.get_workerids();
    }
    
    
    var Worker = function(id) {
        this.id = id;
        this.hits = [];
    }
    
    Worker.prototype.setActions = function(actions) {
        this.actions = actions;
        this.hits = [];
        this.numFinished = 0;
        this.separate_actions();
    }
    Worker.prototype.separate_actions = function() {
        var self = this;
        
        //Go through the actions, grouping those that occurred at the same time
        var currHit = null;
        var currChunk = null;
        for (var i in self.actions) {
            var action = self.actions[i];
            
            //Turn the json action into a real Action
            action = new Action(action);
            
            //If first hit or new hit, make a new hit
            if (currHit == null || currHit.id != action.hitid) {
                
                //Get variables needed to create the new hit
                var hitid = action.hitid;
                var workerid = action.workerid;
                var time = action.time;
                var study = action.study;
                
                currHit = new Hit(workerid, study, hitid, time);
                self.addHit(currHit);
                currChunk = null;
            }
            
            //If first chunk or separated from last chunk, make a new chunk
            if (currChunk == null ||
                action.time.getTime() - currChunk.time.getTime() > 1000) {
                
                //Get variables needed to create the new chunk
                var separation = 0;
                if (currChunk != null) {
                    var separation = action.time.getTime() - currChunk.time.getTime();
                }
                var time = action.time;
                
                currChunk = new Chunk(time, separation);
                currHit.addChunk(currChunk);
            }
            
            //Add this action to the current chunk
            currChunk.addAction(action);
        }
    }
    Worker.prototype.addHit = function(hit) {
        this.hits.push(hit);
        if (hit.isFinished()) {
            this.numFinished++;
        }
    }
    Worker.prototype.render = function() {
        this.view = $(Worker.template(this));
        this.hitsList = this.view.find('.hits');
        for (var i in this.hits) {
            this.hitsList.append(this.hits[i].render());
        }
        return this.view;
    }
    Worker.prototype.positionIteration = function(columns, basisColumn) {
        var basis = columns[basisColumn];
        
        for (var c = basisColumn + 1; c < columns.length; c++) {
            var col = columns[c];
            
            //////Calculate where the start time should fall relative to the basis
            //1. find what percent col.start is through basis
            var startPercentThrough = (col.startTime.getTime() - basis.startTime.getTime()) / basis.duration;
            
            //1.5 make sure it is not less than 0! this should never happen
            if (startPercentThrough < 0) { console.error("negative start percent through!"); }
            
            //2. don't push it past the end of the basis
            startPercentThrough = Math.min(1.1, startPercentThrough);
            
            //3. convert to position
            var newTop = startPercentThrough * basis.height + basis.top;
            
            //Now move it to that position, but only do positive updates
            if (newTop > col.top) {
                col.setTop(newTop + 10);
            }
        }
    }
    
    Worker.prototype.collapseColumns = function(columns) {
        //each column becomes an array of hits
        columns[0] = [columns[0]];
        for (var c = 1; c < columns.length; c++) {
            var hit = columns[c];
            columns[c] = [hit];
            
            //check the preceding columns to see if there is a spot available
            for (var k = 0; k < c; k++) {
                var overlap = false;
                var column = columns[k];
                for (var i = 0; i < column.length; i++) {
                    var other = column[i];
                    
                    //If my top or my bottom is between his two points,
                    //then there is overlap
                    if ((hit.top > other.top && hit.top < other.bottom) ||
                        (hit.bottom > other.top && hit.bottom < other.bottom)) {
                        overlap = true;
                        break;
                    }
                }
                if (!overlap) {
                    //shift it over. they don't need to be in order in the column
                    column.push(hit);
                    columns.splice(c, 1);
                    c--;
                    break;
                }
            }
        }
        return columns
    }
    
    Worker.prototype.positionHits = function() {
        var columns = _.sortBy(this.hits, function(hit) {
            return hit.startTime.getTime();
        });
        
        var hitWidth = 0;
        for (var i in columns) {
            columns[i].updatePosition();
            hitWidth = columns[i].width;
        }
        
        for (var i = 0; i < columns.length; i++) {
            this.positionIteration(columns, i);
        }
        
        columns = this.collapseColumns(columns);
        
        var bottom = 0;
        for (var c in columns) {
            for (var i in columns[c]) {
                var hit = columns[c][i];
            
                //Position in x
                hit.view.css({
                    left: c * (hitWidth + 5)
                });
                
                if (bottom < hit.bottom) {
                    bottom = hit.bottom;
                }
            }
        }
        this.hitsList.css({
            width: columns.length * (hitWidth + 5) + 5,
            height: bottom + 10
        });
    }
    
    Worker.prototype.positionHits_old = function() {
        //Array containing a number representing the y-position of the bottom of each column
        var columnLastHits = [ null ];
        var columnBottoms = [ 0 ];
        hitWidth = 0;
        for (var i in this.hits) {
            var hit = this.hits[i];
            
            var height = hit.view.outerHeight();
            var width = hit.view.outerWidth();
            hitWidth = width;
            
            //got through each column to find the latest-ending HIT you come after
            //and the earliest-ending HIT you come before
            var comeBefore = null;
            var beforeCol = -1;
            var comeAfter = null;
            var afterCol = -1;
            for (var c in columnLastHits) {
                var lastHit = columnLastHits[c];
                if (lastHit) {
                    //Does it end before I start?
                    if (lastHit.stopTime.getTime() <= hit.startTime.getTime()) {
                        //is it later than the best so far?
                        if (comeAfter == null || lastHit.stopTime.getTime() > comeAfter.stopTime.getTime()) {
                            comeAfter = lastHit;
                            afterCol = c
                        }
                    }
                    //Does it end after I start?
                    else if (lastHit.stopTime.getTime() > hit.startTime.getTime()) {
                        //is it earlier than the best so far
                        if (comeBefore == null || lastHit.stopTime.getTime() < comeBefore.stopTime.getTime()) {
                            comeBefore = lastHit;
                            beforeCol = c;
                        }
                    }
                }
            }
            
            var beforeY = 1000000;
            if (beforeCol >= 0) {
                beforeY = columnBottoms[beforeCol];
            }

            var afterY = 0;
            if (afterCol >= 0) {
                afterY = columnBottoms[afterCol];
            }
            
            //So my coordinate needs to fall above beforeY and below afterY
            //Find the column that satisfies this constraint, or make a new column
            var selectedColumn = -1;
            for (var c in columnLastHits) {
                var columnBot = columnBottoms[c];
                //The prev. hit in this column must end before afterY
                if (columnBot <= afterY && columnBot <= beforeY) {
                    //We got it
                    selectedColumn = c;
                }
            }
            if (selectedColumn == -1) {
                //Make a new column
                selectedColumn = columnBottoms.length;
                columnBottoms.push(0);
                columnLastHits.push(null);
            }
            
            //Position the column
            var top = afterY;
            var left = selectedColumn * width;
            hit.view.css({
                top: top,
                left: left
            });
            
            console.log(i, top, left, selectedColumn, afterY, beforeY);
            
            //Now replace the values in the arrays with the new values
            columnLastHits[selectedColumn] = hit;
            columnBottoms[selectedColumn] = top + height;
        }
        
        this.hitsList.css({
            width: columnBottoms.length * hitWidth + 10,
            height: _.max(columnBottoms) + 10
        });
    }
    
    var Hit = function(workerid, study, hitid, startTime) {
        this.study = study;
        this.workerid = workerid;
        this.id = hitid;
        this.startTime = startTime;
        this.stopTime = startTime;
        this.duration = 0;
        this.chunks = [];
        this.finished = false;
    }
    Hit.prototype.isFinished = function() {
        return this.finished;
    }
    
    Hit.prototype.updatePosition = function() {
        var pos = this.view.position();
        this.left = pos.left;
        this.top = pos.top;
        
        this.width = this.view.outerWidth();
        this.height = this.view.outerHeight();
        
        this.bottom = this.top + this.height;
        this.right = this.left + this.width;
    }
    Hit.prototype.setTop = function(top) {
        this.view.css({
            top: top
        });
        this.top = top;
        this.bottom = top + this.height;
    }
    Hit.prototype.setHeight= function(height) {
        this.height = height;
        this.bottom = this.top + height;
        this.view.height(height);
    }
    
    Hit.prototype.addChunk = function(chunk) {
        chunk.hit = this;
        this.chunks.push(chunk);
        if (chunk.time.getTime() > this.stopTime.getTime()) {
            this.stopTime = chunk.time;
            this.duration = this.stopTime.getTime() - this.startTime.getTime();
        }
        if (chunk.finished) {
            this.finished = true;
        }
    }
    Hit.prototype.render = function() {
        this.view = $(Hit.template(this));
        this.chunksList = this.view.find('.chunks');
        for (var i in this.chunks) {
            this.chunksList.append(this.chunks[i].render());
        }
        
        //Add popover to info
        var hitInfo = this.view.find('.hit-info').first();
        hitInfo.popover({
            title: "HIT Info",
            content: hitInfo.html(),
            trigger: "manual"
        }).addClass('popoverable');
        var self = this;
        hitInfo.on('click', function() {
            $('.popoverable').not(hitInfo).popover('hide');
            hitInfo.popover('toggle');
        });
        
        return this.view;
    }
    
    //separation is the # of milliseconds between this chunk and the prev. chunk
    var Chunk = function(time, separation) {
        this.separation = separation;
        this.time = time;
        this.actions = [];
    }
    
    Chunk.prototype.addAction = function(action) {
        if (!this.hit.study && action.study) {
            this.hit.study = action.study;
        }
        action.chunk = this;
        this.actions.push(action);
        if (action.actionClass == "finished") {
            this.finished = true;
        }
    }
    Chunk.prototype.render = function() {
        this.view = $(Chunk.template(this));
        this.actionsList = this.view.find('.actions');
        for (var i in this.actions) {
            this.actionsList.append(this.actions[i].render());
        }
        return this.view;
    }
    
    var Action = function(json) {
        this.time = Date.parseExact(json.time, "yyyy-MM-dd HH:mm:ss");
        this.action = json.action;
        this.assid = json.assid;
        this.condition = json.condition;
        this.hitid = json.hitid;
        this.id = json.id;
        this.ip = json.ip;
        this.study = json.study;
        this.other = json.other;
        this.workerid = json.workerid;
        
        this.tooltip = this.action;
        this.text = this.action;
        if (this.action == 'display') {
            this.text = this.action + ": " + this.other;
        }
        this.actionClass = this.action.split(/[^\w]/)[0];
    }
    
    Action.prototype.render = function() {
        this.view = $(Action.template(this));
        //this.view.attr("title", this.tooltip);
        this.view.popover({
            title: this.tooltip,
            content: this.getDetails(),
            trigger: "manual"
        }).addClass('popoverable');
        var self = this;
        this.view.on('click', function() {
            $('.popoverable').not(self.view).popover('hide');
            self.view.popover('toggle');
        });
        return this.view;
    }
    Action.prototype.getDetails = function() {
        return Action.detailsTemplate(this);
    }
    
    //Static initializations
    $(document).ready(function() {
        Worker.template = _.template($('#worker-template').html());
        Hit.template = _.template($('#hit-template').html());
        Chunk.template = _.template($('#chunk-template').html());
        Action.template = _.template($('#action-template').html());
        Action.detailsTemplate = _.template($('#action-details-template').html());
    });
    
    //Export PathApp
    window.PathApp = PathApp;
})();