function flash(text, type) {
    var flash = jQuery('.flash');
    if (flash.is(':visible')) {
        flash.fadeOut('fast');
    }
    
    if (type) {
        flash.removeClass('alert-error alert-success alert-info');
        flash.addClass('alert-' + type);
    }
    
    if(text) {
        flash.html(text).fadeIn('fast');
        $('html, body').animate({scrollTop:0}, 'fast');
    }
}

function validation_error(text) {
    var error = $("<div class='alert alert-error hide'></div>").html(text);
    $('.error-box').html(error);
    $('html, body').animate({scrollTop:0}, 'fast');
    error.fadeIn();
}

window.ExclusionManager = function() {
    this.exclusions = [];
    
    var self = this;
    $(document).ready(function() {
        self.initialize();
    });
}

window.ExclusionManager.prototype.register = function(groupName, excluderId) {
    this.exclusions.push({
        name: groupName, 
        id: excluderId
    });
}
    
window.ExclusionManager.prototype.initialize = function() {
    $.each(this.exclusions, function(index, excl) {
        var groupName = excl.name;
        var excluderId = excl.id;
        
        var excluder = $('#' + excluderId);
        var restOfGroup = $('[name=' + groupName + ']:not(#' + excluderId + ')');
        
        //Set up the exclusion events
        excluder.change(function() {
            if (this.checked) {
                restOfGroup.attr('checked', false);
            }
        });
        
        restOfGroup.change(function() {
            if (this.checked) {
                excluder.attr('checked', false);
            }
        });
    });
}

window.BlockDialog = function() {
    $(document).ready(function() {
        $(document.activeElement).blur();
        $('#block-dialog').modal({
            keyboard: false,
            backdrop: 'static'
        });
    });
}