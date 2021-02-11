(function(){

    var side_menu = { data: {}, methods: {}};

    side_menu.data = function() {
        var self=this;

        var data = {
            page: self.$root.page
        };
        return data;
    };

    // auth.methods.go = function(page, no_history) {
    //     var self=this;
    //     console.log(this);
    //     if (['login','logout','403','404'].indexOf(page)<0 &&
    //         self.allowed_actions.indexOf('all')<0 &&
    //         self.allowed_actions.indexOf(page)<0) {
    //         page = '404';
    //     }
    //     var url_noqs = window.location.href.split('?')[0] ;
    //     var url = url_noqs.substring(0, url_noqs.lastIndexOf('/')) + '/' + page;
    //     if (page == 'login') url += '?next=' + self.next ;
    //     if (!no_history) history.pushState({'page': page}, null, url);
    //     if (page == '403' || page == '404')
    //         self.form = {}
    //     else if (page == 'register') {
    //         self.form = {username: '', email:'', password:'', password2:'', first_name:'', last_name: ''};
    //         self.fields.map(function(f){ if(!(f.name in self.form)) {f._added=true; self.form[f.name]=''; } else f._added=false; });
    //     }
    //     else if (page == 'login')
    //         self.form = {email:'', password:''};
    //     else if (page == 'request_reset_password')
    //         self.form = {email:''};
    //     else if (page == 'reset_password')
    //         self.form = {new_password:'', new_password2:''};
    //     else if (page == 'change_password')
    //         self.form = {old_password:'', new_password:'', new_password2:''};
    //     else if (page == 'change_email')
    //         self.form = {password: '', new_email:'', new_email2:''};
    //     else if (page == 'edit_profile')
    //         self.form = {first_name:'', last_name: ''};
    //     else
    //         self.form = {};
    //     self.errors = {}
    //     for(var key in self.form) self.errors[key] = null;
    //     self.page = page;
    // };

    side_menu.methods.go = function(page, no_history) {
        var self=this;

        if ( page == self.$root.page ) {
            alert("This is your map!");
        } else if ( !(page in self.$root.menu) ) {
            page = 404;
        };

        if ( page != self.$root.page ) {
            self.$root.page = page;
            var url_noqs = window.location.href.split('?')[0] ;
            var url = url_noqs.substring(0, url_noqs.lastIndexOf('/')) + '/' + page;
            if (!no_history) history.pushState({'page': page}, null, url);
        }
        self.$root.$emit('load_map');
    };

    side_menu.created = function() {
        var self = this;
        window.addEventListener('popstate', function (event) {
            self.go(event.state.page, true);
        }, false);
        var parts = window.location.href.split('?')[0].split('/');
        let page = parts[parts.length-1];
        // Just giver the time to load other component
        setTimeout(function() { self.go(page); }, 1000);
    };

    Q.register_vue_component('side_menu', 'components/side_menu.html', function(template) {
        side_menu.template = template.data;
        return side_menu;
    });

})();
