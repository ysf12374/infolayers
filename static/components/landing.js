(function(){

    var landing = { data: {}, methods: {}};

    landing.data = function() {
        var data = {};
        return data;
    };

    Q.register_vue_component('landing', 'components/landing.html', function(template) {
            landing.template = template.data;
            return landing;
        });

})();
