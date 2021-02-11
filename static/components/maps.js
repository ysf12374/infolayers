(function(){

    var colors = [
      // "#ffffff",
      "#fcff94",
      "#f1a692",
      // "#fabe8c",
      "#e0769e",
      "#9a5caf",
      "#4b4ba5",
      // "#000000",
    ]

    // var colorScale_ = d3.scaleLinear().domain([0, 1]).range(colors);
    var colorScale2_ = chroma.scale(colors).domain([0, 1]).mode('lab').correctLightness();

    var colorScale = function (value) {
    	const color = colorScale2_(value);
    	return color;
    };

    var mapper = { data: {}, methods: {}, computed: {}};

    // Arithmetic mean
    function getMean (data) {
        return data.reduce(function (a, b) {
            return Number(a) + Number(b);
        }) / data.length;
    };

    function getMedian (data) {
        const mid = Math.floor(data.length / 2);
        const nums = [...data].sort((a, b) => a - b);
        return data.length % 2 !== 0 ? nums[mid] : (nums[mid - 1] + nums[mid]) / 2;
    };

    function getSD (data) {
        let m = getMean(data);
        return Math.sqrt(data.reduce(function (sq, n) {
            return sq + Math.pow(n - m, 2);
        }, 0) / (data.length - 1));
    };

    function formnatThousands(x) {
        return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
    }

    function labelize(definitions) {
        /**
        definitions @array : [{'label': [HTMLElement, ...], 'value': [HTMLElement, ...]}]
        Returns HTMLElement table
        **/
        let ew = document.createElement('p');
        let iw = document.createElement('table');
        iw.className = 'table is-striped is-narrow is-hoverable';
        for ( ii in definitions ) {
            let row = document.createElement('tr');
            let labelColumn = document.createElement('td');
            let valueColumn = document.createElement('td');
            let label = document.createElement('em');
            let value =  document.createElement('strong');
            for ( jj in definitions[ii]['label'] ) {
                label.appendChild(definitions[ii]['label'][jj]);
            };
            for ( jj in definitions[ii]['value'] ) {
                value.appendChild(definitions[ii]['value'][jj]);
            };
            labelColumn.appendChild(label);
            valueColumn.appendChild(value);
            row.appendChild(labelColumn);
            row.appendChild(valueColumn);
            iw.appendChild(row);
        };
        ew.appendChild(iw);
        return ew;
    }

    function allStars(rating) {
        max_stars = 4;
        let wrapper = document.createElement('span')
        const fullStars = Math.floor(rating*max_stars);
        for ( let ii=0; ii < fullStars; ii++ ) {
            star = document.createElement('i');
            star.className = 'fas fa-star';
            wrapper.appendChild(star);
        };
        const halfStars = Math.floor(rating*max_stars*2) - fullStars*2;
        for ( let ii=0; ii < halfStars; ii++ ) {
            star = document.createElement('i');
            star.className = 'fas fa-star-half-alt';
            wrapper.appendChild(star);
        };
        const emptyStars = 4-halfStars-fullStars;
        for ( let ii=0; ii < emptyStars; ii++ ) {
            star = document.createElement('i');
            star.className = 'far fa-star';
            wrapper.appendChild(star);
        };
        return wrapper
    };

    mapper.data = function() {
        var self = this;
        var data = {
            // source_name: 'AGCOM',
            page: self.$root.page,
            map: null,
            mapOptions: {
              center: [45.49118636890595, 9.1571044921875],
              // center: [44.3496, 9.2328],
              zoom: 15,
              maxZoom: 20
            },
            layersOptions: {},
            layers: {},
            sources: {}
        };
        return data;
    };

    mapper.computed.lessIsGood = function () {
        var self = this;
        if ( self.$root.page=='broadband' ) {
            return true;
        } else {
            return false;
        };
    };

    mapper.computed.source_name = function () {
        var self = this;
        if ( self.$root.page=='broadband' ) {
            return 'AGCOM';
        } else if ( self.$root.page=='realestate' ) {
            return 'immobiliare.it'
        } else {
            return null;
        };
    };

    mapper.methods.initLayers = function () {
        var self = this;
        self['{page}Setup'.format({page: self.$root.page})]();
    };

    mapper.methods.initMap = function() {
        var self = this;
        self.map = L.map('map', {maxZoom: self.mapOptions.maxZoom}).setView(self.mapOptions.center, self.mapOptions.zoom);

        // this.tileLayer = L.tileLayer(
        //   'https://cartodb-basemaps-{s}.global.ssl.fastly.net/rastertiles/voyager/{z}/{x}/{y}.png',
        //   {
        //     maxZoom: 18,
        //     attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>, &copy; <a href="https://carto.com/attribution">CARTO</a>',
        //   }
        // );

        // this.tileLayer = L.tileLayer('https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png', {
        // 	maxZoom: self.mapOptions.maxZoom,
        // 	attribution: '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a>, &copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors'
        // });

        self.tileLayer = L.tileLayer('https://{s}.tile.jawg.io/jawg-matrix/{z}/{x}/{y}{r}.png?access-token={accessToken}', {
    		attribution: '<a href="http://jawg.io" title="Tiles Courtesy of Jawg Maps" target="_blank">&copy; <b>Jawg</b>Maps</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    		minZoom: 0,
    		maxZoom: 22,
    		subdomains: 'abcd',
    		accessToken: 'MFf9Ub3EB3193S2mdbCZBbNfePeaQdcqcdnpqDAXF7o79Q3ohYG8OFZODnSJqxAK'
    	});
        self.tileLayer.addTo(this.map);

        self.map.on('moveend', self.initLayers);
        self.initLayers();
    };

    mapper.methods.flyto = function (shortcut) {
        var self = this;
        let shortcuts = {
            'milano': [45.4911, 9.1571],
            'rapallo': [44.3496, 9.2328]
        }
        self.flyTo(shortcuts[shortcut]);
        alert("Welcome to {shortcut}".format({shortcut: shortcut}))
    };

    mapper.methods.call4data = function (url, options, callback) {
        var self = this;
        function wrapper (response) {
            self.map.on('moveend', self.initLayers);
            self.broadbandUpdate(response);
        };
        self.map.off('moveend')
        axios.post(url, options).then(
            wrapper
        ).catch(function (error) {
            // app.map.spin(false);
            console.log(error);
        });
    };

    mapper.methods.broadbandSetup = function () {
        self = this;
        let actualZoom = self.map.getZoom();
        let resolution = actualZoom+3;
        let squared_tiles;
        if ( actualZoom >= 8 & actualZoom <= 11 ) {
            squared_tiles = true;
        } else if ( actualZoom > 11 & actualZoom <= 14 ) {
            squared_tiles = false;
        } else if ( actualZoom > 14 ) {
            squared_tiles = null;
        };

        if ( squared_tiles === undefined ) {
            if ( self.map.hasLayer(self.layers.info) ) {
                self.map.removeLayer(self.layers.info)
            };
        } else {
            let bounds = self.map.getBounds();
            let callOptions = {
                minlon: bounds.getWest(),
                minlat: bounds.getSouth(),
                maxlon: bounds.getEast(),
                maxlat: bounds.getNorth(),
                zoom: resolution,
                source_name: self.source_name
            };
            let url;
            if ( squared_tiles != undefined ) {
                url = '../cluster/{page}.topojson'.format({page: self.$root.page});
                callOptions['classic'] = squared_tiles;
            } else {
                url = '../{page}.topojson'.format({page: self.$root.page});
            };
            axios.post(url, callOptions).then(
                self.broadbandUpdate
            ).catch(function (error) {
                // app.map.spin(false);
                console.log(error);
            });
        }
    };
    mapper.methods.broadbandUpdate = function (response) {
        var self = this;

        if ( this.map.hasLayer(this.layers.info) ) {
            this.map.removeLayer(this.layers.info)
        };

        let data = {};
        if ( response.data.objects && response.data.objects.topology ) {
            data = topojson.feature(response.data, response.data.objects['topology']);
        } else {
            data = response.data;
        };

        self.$set(self.sources, 'info', data);

        self.$set(self.layers, 'info', L.geoJson(self.sources.info, {
            style: self.render,
            onEachFeature: function (feature, layer) {

                let popupElement;
                if ( 'max_download' in feature.properties ) {
                    popupElement = labelize([{
                        'label': [document.createTextNode("Max download: ")],
                        'value': [document.createTextNode(feature.properties.max_download)]
                    }, {
                        'label': [document.createTextNode("Max upload: ")],
                        'value': [document.createTextNode(feature.properties.max_upload)]
                    }, {
                        'label': [document.createTextNode("FTTH: ")],
                        'value': [document.createTextNode(feature.properties.ftth_cover)]
                    }]);
                } else {
                    console.log(feature.properties);
                    popupElement = labelize([{
                        'label': [document.createTextNode("Records in area: ")],
                        'value': [document.createTextNode(feature.properties.count)]
                    }, {
                        'label': [document.createTextNode("Rating: ")],
                        'value': [allStars(feature.properties.mrate)]
                    }]);
                };

                layer.bindPopup(popupElement);
            }
        }));
        self.layers.info.addTo(self.map);
        // self.map.spin(false);

    };

    mapper.methods.realestateSetup = function () {
        self = this;
        let actualZoom = self.map.getZoom();
        let resolution = actualZoom+3;
        let squared_tiles;
        if ( actualZoom >= 8 & actualZoom <= 11 ) {
            squared_tiles = true;
        } else if ( actualZoom > 11 & actualZoom <= 17 ) {
            squared_tiles = false;
        } else if ( actualZoom > 17 ) {
            squared_tiles = null;
        };

        if ( squared_tiles === undefined ) {
            if ( self.map.hasLayer(self.layers.info) ) {
                self.map.removeLayer(self.layers.info)
            };
        } else {
            let bounds = self.map.getBounds();
            let callOptions = {
                minlon: bounds.getWest(),
                minlat: bounds.getSouth(),
                maxlon: bounds.getEast(),
                maxlat: bounds.getNorth(),
                zoom: resolution,
                source_name: self.source_name
            };
            let url;
            if ( squared_tiles != undefined ) {
                url = '../cluster/{page}.topojson'.format({page: self.$root.page});
                callOptions['classic'] = squared_tiles;
            } else {
                url = '../{page}.topojson'.format({page: self.$root.page});
            };
            axios.post(url, callOptions).then(
                self.realestateUpdate
            ).catch(function (error) {
                // app.map.spin(false);
                console.log(error);
            });
        }
    };
    mapper.methods.realestateUpdate = function (response) {
        var self = this;

        if ( this.map.hasLayer(this.layers.info) ) {
            this.map.removeLayer(this.layers.info)
        };

        let data = {}; let mylayer;
        if ( response.data.objects && response.data.objects.topology ) {
            data = topojson.feature(response.data, response.data.objects['topology']);
            self.$set(self.sources, 'info', data);
            mylayer = L.geoJson(self.sources.info, {
                style: self.render,
                onEachFeature: function (feature, layer) {

                    let expText = document.createTextNode("2");
                    let exp = document.createElement('sup');
                    exp.appendChild(expText);

                    let popupElement = labelize([{
                        'label': [document.createTextNode("Records in area:")],
                        'value': [document.createTextNode(feature.properties.count)]
                    }, {
                        'label': [document.createTextNode("Unit price range: ")],
                        'value': [document.createTextNode("{low} ÷ {hi} €/m".format({
                            low: formnatThousands(feature.properties.upricemin),
                            hi: formnatThousands(feature.properties.upricemax)
                        })), exp]
                    }]);

                    layer.bindPopup(popupElement);
                }
            });
        } else {
            data = response.data;
            self.$set(self.sources, 'info', data);
            mylayer = L.markerClusterGroup({
            	iconCreateFunction: function(cluster) {
                    rates = cluster.getAllChildMarkers().map(function (marker) {return marker.feature.properties.rate});
                    icon = document.createElement('span');
                    icon.className = 'tag is-rounded is-light'
                    icon.style['background-color'] = colorScale(getMedian(rates));;
                    icon.style['font-size'] = '2em';
                    text = document.createTextNode("{cnt}".format({cnt: cluster.getChildCount()}));
                    icon.appendChild(text)
                    return L.divIcon({html: icon, className: ''})
            		// return L.divIcon({ html: '<b>' + cluster.getChildCount() + '</b>' });
            	}
            });
            geoJsonLayer = L.geoJson(self.sources.info, {
                pointToLayer: function(feature, latlng) {
                    // return L.marker(latlng);
                    color = colorScale(feature.properties.rate);
                    icon = document.createElement('i');
                    icon.className = 'fas fa-sign fa-4x';
                    // icon.style['font-size'] = '4em';
                    icon.style.color = color;
                    icon_wrappper = document.createElement('span');
                    icon_wrappper.appendChild(icon);
                    return L.marker(latlng, {icon:  L.divIcon({html: icon_wrappper, className: ''})});
                },
                onEachFeature: function (feature, layer) {

                    let expText = document.createTextNode("2");
                    let exp = document.createElement('sup');
                    exp.appendChild(expText);

                    let popupElement = labelize([{
                        'label': [document.createTextNode("Unit price: ")],
                        'value': [document.createTextNode("{price} €/m".format({
                            price: formnatThousands(feature.properties.uprice)
                        })), exp]
                    }]);

                    layer.bindPopup(popupElement);
                }
            });
            mylayer.addLayer(geoJsonLayer);
        };

        self.$set(self.layers, 'info', mylayer);
        self.layers.info.addTo(self.map);
        // self.map.spin(false);

    };

    mapper.methods.render = function (feature, layer) {
        var self = this;
	  	const color = colorScale(feature.properties.mrate);
        let domain;
        let value;
        if ( self.lessIsGood ) {
            domain = [1/20, 1];
            value = 1/feature.properties.count;
        } else {
            domain = [1, 15];
            value = feature.properties.count;
        };
        return {
            "color":  color,
            "weight": 5,
            "fillOpacity": Math.min(d3.scaleLinear().domain(domain).range([.3, .85])(value), .85)
        }
    }

    mapper.methods.load_map = function(page) {
        var self = this;
        console.log("loading new map: {page}".format({page: page}));

        if ( !!(self.$root.menu[page]) & !(self.$root.menu[page].coming_soon) ) {
            if ( self.map === null ) {
                /** Map init **/
                setTimeout(function () {self.initMap();}, 500)
            } else {
                /** Re-init layers **/
                self.initLayers();
            };
        } else { self.map = null; }

    }

    mapper.methods.on_api_error = function (err) {
            var self = this;
            var res = err.response;
            if ( res.data.errors ) self.errors = res.data.errors;
            else alert(res.data.message);
    };

    mapper.created = function() {
        var self = this;
        self.$root.$on('load_map', () => {
            self.load_map(self.$root.page);
        })
        // self.page = self.$root.page;
    };

    Q.register_vue_component('mapper', 'components/maps.html', function(template) {
        mapper.template = template.data;
        return mapper;
    });

})();
