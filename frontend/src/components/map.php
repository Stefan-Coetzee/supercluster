<?php
// Template Name: Fami Mabbox Demo
get_header('new');
while (have_posts()):
    the_post();
?>
    <?php
    function data_format_number($num)
    {
        if ($num >= 1000000) {
            return ['value' => round($num / 1000000, 1), 'suffix' => 'M']; // Format in millions
        } elseif ($num >= 1000) {
            return ['value' => round($num / 1000, 1), 'suffix' => 'K']; // Format in thousands
        }
        return ['value' => number_format($num), 'suffix' => '']; // Show number as is
    }

    // Fetch and calculate get_total_youth_in_work data
    $total_youth_in_work = '';
    if (function_exists('get_youth_in_work_total_by_gender')):
        $total_youth_data =  get_youth_in_work_total_by_gender();
        $total_youth_in_work = calculate_gender_percentages($total_youth_data);
    endif;

    // Fetch and calculate get_youth_in_wage_employment data
    $wage_employment = '';
    if (function_exists('get_youth_in_wage_employment')):
        $wage_employment_data =  get_youth_in_wage_employment();
        $wage_employment = calculate_gender_percentages($wage_employment_data);
    endif;

    // Fetch and calculate Starting Ventures data
    $starting_ventures = '';
    if (function_exists('get_youth_starting_ventures')):
        $starting_ventures_data = get_youth_starting_ventures();
        $starting_ventures = calculate_gender_percentages($starting_ventures_data);
    endif;

    // Fetch and calculate graduate count data
    $graduate_count = '';
    if (function_exists('get_graduate_count')):
        $graduate_count_data = get_graduate_count();
        $graduate_count = calculate_gender_percentages_matric($graduate_count_data);
    endif;

    $job_placement_live = '';
    if (function_exists('get_latest_job_placement_live_feed')) {
        $job_placement_live = get_latest_job_placement_live_feed();
    }

    $six_month_employment = '';
    if (function_exists('get_six_month_employment_rate')) :
        $six_month_employment = get_six_month_employment_rate();
    endif;



    $colors = get_field('colors', 'option');
    // Extract colors from ACF repeater field
    $color_array = [];
    if (!empty($colors) && is_array($colors)) {
        foreach ($colors as $color) {
            if (!empty($color['color'])) { // Ensure 'color' field exists
                $color_array[] = $color['color'];
            }
        }
    }
    $colors_json = json_encode($color_array);

    // Fetch and calculate Job created data
    $jobs_created = '';
    if (function_exists('get_youth_in_jobs_created')):
        $jobs_created_data = get_youth_in_jobs_created();
        $jobs_created = calculate_gender_percentages($jobs_created_data);
    endif;

    // Fetch and calculate currently_enrolled data
    $currently_enrolled_data = '';
    if (function_exists('get_currently_enrolled')):
        $result = get_currently_enrolled();
        $currently_enrolled_data = calculate_gender_percentages_matric($result);
    endif;

    // Fetch and calculate outreach_metrics data
    $outreach_metrics = '';
    if (function_exists('get_outreach_metrics_by_gender')):
        $outreach_metrics_result = get_outreach_metrics_by_gender();
        $outreach_metrics = calculate_gender_percentages_matric($outreach_metrics_result);
    endif;

    // Fetch and calculate funds_raised data
    $funds_raised = '';
    if (function_exists('get_funds_raised_by_ventures')):
        $funds_raised_result = get_funds_raised_by_ventures();
        $funds_raised = calculate_gender_percentages_matric($funds_raised_result);
    endif;

    // Fetch and calculate dignified and fulfilling report data
    $dignified_and_fulfilling = '';
    if (function_exists('get_dignified_and_fulfilling_report_work')) {
        $result = get_dignified_and_fulfilling_report_work();
        if (!is_array($result)) {
            $dignified_and_fulfilling = $result;
        }
    }
    // Fetch and calculate Currently Enrolled data
    $promotion_vs_new_role = '';
    if (function_exists('get_promotion_vs_new_role')) {
        $promotion_vs_new_role = get_promotion_vs_new_role();
    }
    // Prepare data for the JavaScript chart
    $promotion_chartData = [];


    foreach ($promotion_vs_new_role as $data) {
        $promotion_chartData[] = [
            'sector' => strtoupper($data->dimension),
            'size' => $data->metric_value
        ];
    }

    // Fetch and calculate Currently Enrolled data
    $promotion_outcome = '';
    if (function_exists('get_promotion_outcome')) {
        $promotion_outcome = get_promotion_outcome();
    }
    // Prepare data for the JavaScript chart
    $outcome_chartData = [];
    foreach ($promotion_outcome as $data) {
        $outcome_chartData[] = [
            'year' => $data->dimension,
            'income' => $data->percentage
        ];
    }

    // Fetch and calculate Currently Enrolled data
    $promotion_outcome = '';
    if (function_exists('get_distribution_of_jobs_created')) {
        $promotion_outcome = get_distribution_of_jobs_created();
    }
    $total_value = array_sum(array_column($promotion_outcome, 'metric_value'));
    // Prepare data for JavaScript
    $distribution_chartData = [];
    foreach ($promotion_outcome as $data) {
        $percentage = ($total_value > 0) ? round(($data->metric_value / $total_value) * 100, 1) : 0;
        $distribution_chartData[] = [
            'sector' => strtoupper($data->employment_type), // Convert to uppercase
            'size' => $percentage // Store percentage
        ];
    }

    $average_salary = function_exists('get_average_salary_metrics') ? get_average_salary_metrics() : [];

    $salaryData = [
        "Overall" => ["year" => "Overall", "New Role" => 0, "Promotion" => 0],
        "Female" => ["year" => "Female", "New Role" => 0, "Promotion" => 0]
    ];

    // Map the data correctly
    foreach ($average_salary as $data) {
        $gender = $data->gender;
        $dimension = strtolower($data->dimension); // Convert dimension to lowercase for consistency
        $metric_value = (int)$data->metric_value; // Ensure integer values

        if (isset($salaryData[$gender])) {
            if ($dimension === "new role") {
                $salaryData[$gender]["New Role"] = $metric_value;
            } elseif ($dimension === "promotion") {
                $salaryData[$gender]["Promotion"] = $metric_value;
            }
        }
    }

    // Convert structured data to JSON
    $average_salary_chartDataJSON = json_encode(array_values($salaryData));

    $female_icon = get_field('female_icon');
    $male_icon = get_field('male_icon');
    $undisclosed_icon = get_field('undisclosed_icon');

    $youth_in_work_title = get_field('youth_in_work_title');
    $youth_in_wage_employment_title = get_field('youth_in_wage_employment_title');
    $youth_starting_ventures_title = get_field('youth_starting_ventures_title');
    $graduates_title = get_field('graduates_title');
    $currently_enrolled = get_field('currently_enrolled');
    $higher_salary_level = get_field('higher_salary_level');
    $higher_salary_level_title = get_field('higher_salary_level_title');

    $outreach_title = get_field('outreach_title');
    $employment_placement_rate_title = get_field('employment_placement_rate_title');
    $reporting_dignified_and_fulfilling_title = get_field('reporting_dignified_and_fulfilling_title');
    $jobs_created_through_title = get_field('jobs_created_through_title');
    $funds_raised_by_ventures_title = get_field('funds_raised_by_ventures_title');
    $number_of_percentage_promotion = get_field('number_of_percentage_promotion');
    $higher_salary_for_promotion_title = get_field('higher_salary_for_promotion_title');

    $job_placement_live_feed_icon = get_field('job_placement_live_feed_icon');
    $job_placement_live_feed_title = get_field('job_placement_live_feed_title');
    $distribution_of_job_created_title = get_field('distribution_of_job_created_title');
    $average_annual_salary_title = get_field('average_annual_salary_title');
    $promotion_vs_new_roles_title = get_field('promotion_vs_new_roles_title');
    $promotion_outcomes_title = get_field('promotion_outcomes_title');

    $new_role_title = get_field('new_role_title') ? get_field('new_role_title') : 'NEW ROLE';
    $new_role_color = get_field('new_role_color') ? get_field('new_role_color') : '#4895EF';
    $promotion_title = get_field('promotion_title') ? get_field('promotion_title') : 'PROMOTION';
    $promotion_color = get_field('promotion_color') ? get_field('promotion_color') : '#96EFB5';

    $pn_new_role_title = get_field('pn_new_role_title') ? get_field('pn_new_role_title') : 'NEW ROLE';
    $pn_new_role_color = get_field('pn_new_role_color') ? get_field('pn_new_role_color') : '#8571F4';
    $pn_promotion_title = get_field('pn_promotion_title') ? get_field('pn_promotion_title') : 'PROMOTION';
    $pn_promotion_color = get_field('pn_promotion_color') ? get_field('pn_promotion_color') : '#45D0EE';

    $wage_employed_title = get_field('wage_employed_title') ? get_field('wage_employed_title') : 'WAGE EMPLOYED';
    $wage_employed_color = get_field('wage_employed_color') ? get_field('wage_employed_color') : '#F1F4F9';
    $freelancer_title = get_field('freelancer_title') ? get_field('freelancer_title') : 'FREELANCER';
    $freelancer_color = get_field('freelancer_color') ? get_field('freelancer_color') : '#8571F4';
    $emtrepreneurs_title = get_field('emtrepreneurs_title') ? get_field('emtrepreneurs_title') : 'ENTREPRENEURS';
    $emtrepreneurs_color = get_field('emtrepreneurs_color') ? get_field('emtrepreneurs_color') : '#9b8af8';
    $job_created_title = get_field('job_created_title') ? get_field('job_created_title') : 'JOB CREATED';
    $job_created_color = get_field('job_created_color') ? get_field('job_created_color') : '#bcb0fc';
    $rhos_title = get_field('rhos_title') ? get_field('rhos_title') : 'RHOS';
    $rhos_color = get_field('rhos_color') ? get_field('rhos_color') : '#dcd6ff';

    ?>

    <div class="master-data">
    

        <div class="center-panel order-lg-2 order-1">
            <div class="map-area">
                <div class="map-container map-overview map-overview-mapbox " id="map"></div>
                <div class="map-detail-btn">
                    <ul>
                        <li><a href="javascript:void(0);"> <figure>
                            <img src="<?php echo esc_url(THEME_IMG . "marker-video.png"); ?>" alt="video-icon">
                        </figure> Learners video </a></li>
                        <li><a href="javascript:void(0);"> <figure>
                            <img src="<?php echo esc_url(THEME_IMG . "marker.png"); ?>" alt="story-icon">
                        </figure> Learners stories </a></li>
                        <li><a href="javascript:void(0);"> <figure>
                            <img src="<?php echo esc_url(THEME_IMG . "marker-data.png"); ?>" alt="data-icon">
                        </figure> Learners profile </a></li>
                    </ul>
                </div>
            </div>
            
        </div>

    </div>

    <div class="modal-story">
        <div class="modal fade" id="exampleModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable">
                <div class="modal-content">
                    <div class="head-block">
                        <button type="button" class="btn-close pauseButton" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body wrapper scrollbar-dynamic">
                        <!-- Dynamic content will be injected here -->
                        <div id="modal-profile-content"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <style>
        #map {
            width: 100%;
        }
        .cluster-marker {
            font-size: 14px;
            font-weight: bold;
            transition: all 0.2s ease;
            font-family: 'Poppins', sans-serif;
        }

        .custom-marker {
            /* Add any additional styling if needed */
        }

        .mapboxgl-ctrl-group {
            display: flex;
            flex-direction: column;
            align-items: stretch;
        }

        .mapboxgl-ctrl-icon {
            background-size: 20px;
            background-position: center;
            background-repeat: no-repeat;
            width: 25px;
            height: 20px;
            box-sizing: border-box;
            background-color: #fff;
            border: 1px solid #ccc;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* .mapboxgl-ctrl-reset {
            margin: 5px 0;
        } */

        .mapboxgl-ctrl-reset:hover {
            background-color: #f0f0f0;
            border-color: #888;
        }

        .mapboxgl-popup-content {
            background: white;
            padding: 3px;
            font-family: 'Poppins', sans-serif;
        }
    </style>

    <!-- ALX Map Area -->
    <?php
    // API endpoint URLs
    $api_base_url = 'https://supercluster-api.yourdomain.com/api'; // Replace with your actual API base URL
    $countries_endpoint = $api_base_url . '/countries';
    $supercluster_endpoint = $api_base_url . '/getClusters'; // New supercluster endpoint
    
    // Fetch countries data from API
    $country_response = wp_remote_get($countries_endpoint);
    $country_list = [];
    $country_data = [];
    
    if (!is_wp_error($country_response) && wp_remote_retrieve_response_code($country_response) === 200) {
        $api_data = json_decode(wp_remote_retrieve_body($country_response), true);
        
        if (isset($api_data['countries']) && is_array($api_data['countries'])) {
            foreach ($api_data['countries'] as $country) {
                $country_name = $country['name'] ?? '';
                if (!empty($country_name)) {
                    $country_list[] = $country_name;
                    $country_data[$country_name] = [
                        "testimonial" => $country['testimonial'] ?? [],
                        "stats" => $country['stats'] ?? [],
                        "original_name" => $country['original_name'] ?? $country_name,
                        "country_code" => $country['country_code'] ?? null
                    ];
                }
            }
        }
    }

    $country_name_mapping = [
        "Côte d'Ivoire" => "Côte d'Ivoire",
        "United Republic of Tanzania" => "Tanzania",
        "Central African Republic" => "Central African Rep.",
        "Equatorial Guinea" => "Eq. Guinea",
        "South Sudan" => "S. Sudan",
        "Eswatini" => "Swaziland"
    ];

    $custom_country_codes = [
        "Côte d'Ivoire" => "CI",
        "United Republic of Tanzania" => "TZ",
        "Central African Republic" => "CF",
        "Equatorial Guinea" => "GQ",
        "South Sudan" => "SS",
        "Eswatini" => "SZ"
    ];
    ?>

    <!-- Add flag-icons CSS, Google Fonts for Poppins, and required libraries from CDN -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/lipis/flag-icons@7.2.3/css/flag-icons.min.css" />
    <script src="https://cdn.jsdelivr.net/npm/@turf/turf@6/turf.min.js"></script>
    <script src="https://unpkg.com/supercluster@8.0.1/dist/supercluster.min.js"></script>

    <script>
        // API endpoint URLs
        const apiBaseUrl = '<?php echo esc_url($api_base_url); ?>';
        const countryDataEndpoint = `${apiBaseUrl}/country`;
        const profileDataEndpoint = `${apiBaseUrl}/profile`;
        const superclusterEndpoint = `${apiBaseUrl}/getClusters`; // Add supercluster endpoint
        
        mapboxgl.accessToken = 'pk.eyJ1IjoieXV2cmFqa2hhdmFkNSIsImEiOiJjbTh6bDBsYzkwYmJyMmtzaXRsaG1qbGU2In0.VtRlbiTs-REw21A_XcADXQ';

        const map = new mapboxgl.Map({
            container: 'map',
            style: 'mapbox://styles/mapbox/light-v10',
            center: [0, 20],
            zoom: 2,
            minZoom: 2,
            maxZoom: 18,
            maxBounds: [
                [-180, -85],
                [180, 85]
            ]
        });

        // Add zoom & rotation controls
        map.addControl(new mapboxgl.NavigationControl());

        // Add reset button with Google scan-like icon
        const resetButton = document.createElement('button');
        resetButton.className = 'mapboxgl-ctrl-icon mapboxgl-ctrl-reset';
        resetButton.setAttribute('type', 'button');
        resetButton.setAttribute('title', 'Reset Map');
        resetButton.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="15" viewBox="0 0 448 448" fill="none">
            <path d="M160 16C160 20.2435 158.314 24.3131 155.314 27.3137C152.313 30.3143 148.243 32 144 32H80C53.536 32 32 53.536 32 80V144C32 148.243 30.3143 152.313 27.3137 155.314C24.3131 158.314 20.2435 160 16 160C11.7565 160 7.68687 158.314 4.68629 155.314C1.68571 152.313 0 148.243 0 144V80C0 35.888 35.888 0 80 0H144C148.243 0 152.313 1.68571 155.314 4.68629C158.314 7.68687 160 11.7565 160 16ZM368 0H304C299.757 0 295.687 1.68571 292.686 4.68629C289.686 7.68687 288 11.7565 288 16C288 20.2435 289.686 24.3131 292.686 27.3137C295.687 30.3143 299.757 32 304 32H368C394.464 32 416 53.536 416 80V144C416 148.243 417.686 152.313 420.686 155.314C423.687 158.314 427.757 160 432 160C436.243 160 440.313 158.314 443.314 155.314C446.314 152.313 448 148.243 448 144V80C448 35.888 412.112 0 368 0ZM144 416H80C53.536 416 32 394.464 32 368V304C32 299.757 30.3143 295.687 27.3137 292.686C24.3131 289.686 20.2435 288 16 288C11.7565 288 7.68687 289.686 4.68629 292.686C1.68571 295.687 0 299.757 0 304V368C0 412.112 35.888 448 80 448H144C148.243 448 152.313 446.314 155.314 443.314C158.314 440.313 160 436.243 160 432C160 427.757 158.314 423.687 155.314 420.686C152.313 417.686 148.243 416 144 416ZM432 288C427.757 288 423.687 289.686 420.686 292.686C417.686 295.687 416 299.757 416 304V368C416 394.464 394.464 416 368 416H304C299.757 416 295.687 417.686 292.686 420.686C289.686 423.687 288 427.757 288 432C288 436.243 289.686 440.313 292.686 443.314C295.687 446.314 299.757 448 304 448H368C412.112 448 448 412.112 448 368V304C448 299.757 446.314 295.687 443.314 292.686C440.313 289.686 436.243 288 432 288Z" fill="black"/>
            <circle cx="224" cy="224" r="77" fill="black"/>
        </svg>
    `;
        resetButton.style.display = 'none'; // Hidden by default

        resetButton.addEventListener('click', () => {
            map.fitBounds([
                [-27, -37],
                [60, 40]
            ], {
                duration: 1000
            });
            if (currentlySelectedCountry) {
                const previousFeature = map.queryRenderedFeatures({
                        layers: ['country-fills']
                    })
                    .find(f => f.properties.name === currentlySelectedCountry);
                if (previousFeature) {
                    map.setFeatureState({
                        source: 'countries',
                        id: previousFeature.id
                    }, {
                        active: false
                    });
                }
                currentlySelectedCountry = null;
            }
            markers.forEach(marker => marker.remove());
            markers = [];
            isClusterZoomed = false;
            resetButton.style.display = 'none'; // Hide button after reset
        });

        const resetControl = {
            onAdd: function(map) {
                const container = document.createElement('div');
                container.className = 'mapboxgl-ctrl mapboxgl-ctrl-group';
                container.appendChild(resetButton);
                return container;
            },
            onRemove: function() {}
        };
        map.addControl(resetControl, 'top-right');

        // Show reset button on map movement
        map.on('move', () => {
            if (map.getZoom() !== 2 || map.getCenter().lat !== 20 || map.getCenter().lng !== 0) {
                resetButton.style.display = 'block';
            }
        });

        const countries = <?php echo json_encode($country_list); ?>;
        const countryData = <?php echo json_encode($country_data); ?>;
        const customCountryCodes = <?php echo json_encode($custom_country_codes); ?>;

        let markers = [];
        let selectedCountries = new Set();
        let currentlySelectedCountry = null;
        let supercluster;
        let isClusterZoomed = false;

        function getFillColor(overallValue) {
            const value = parseInt(overallValue) || 0;
            if (value >= 10000) return "#002E6C";
            if (value >= 5000) return "#9DB2C5";
            if (value >= 1000) return "#D98D9A";
            if (value >= 200) return "#F1D8DC";
            if (value >= 1) return "#EAEFF5";
            return "#FFFFFF";
        }

        map.on('load', () => {
            const countryFlags = {};
            const geoJsonUrl = 'https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson';

            fetch(geoJsonUrl)
                .then(response => response.json())
                .then(data => {
                    data.features.forEach((feature, index) => {
                        feature.id = index;
                    });

                    const geoJsonCountryCodes = {};
                    data.features.forEach(feature => {
                        const name = feature.properties.name;
                        const isoA2 = feature.properties.iso_a2;
                        if (isoA2 && isoA2 !== "-99") {
                            geoJsonCountryCodes[name] = isoA2.toLowerCase();
                        }
                    });

                    countries.forEach(country => {
                        const originalName = countryData[country]?.original_name || country;
                        const staticCode = countryData[country]?.country_code || customCountryCodes[originalName];
                        const geoJsonCode = geoJsonCountryCodes[country];
                        const countryCode = staticCode || geoJsonCode || "xx";
                        countryFlags[country] = countryCode.toLowerCase();
                        if (!staticCode && !geoJsonCode) {
                            console.warn(`No country code found for ${country} (original: ${originalName}), defaulting to "XX"`);
                        }
                    });

                    // Create a unique GeoJSON with one feature per country using centroids
                    const uniqueCountriesGeoJson = {
                        type: 'FeatureCollection',
                        features: []
                    };

                    const countryCentroids = {};
                    data.features.forEach(feature => {
                        const name = feature.properties.name;
                        if (countries.includes(name) && !countryCentroids[name]) {
                            const centroid = turf.centroid(feature);
                            countryCentroids[name] = centroid;
                            uniqueCountriesGeoJson.features.push({
                                type: 'Feature',
                                geometry: centroid.geometry,
                                properties: {
                                    name: name
                                }
                            });
                        }
                    });

                    map.addSource('countries', {
                        type: 'geojson',
                        data: data
                    });

                    map.addSource('country-labels', {
                        type: 'geojson',
                        data: uniqueCountriesGeoJson
                    });

                    map.addLayer({
                        'id': 'country-background',
                        'type': 'fill',
                        'source': 'countries',
                        'paint': {
                            'fill-color': '#FFFFFF',
                            'fill-opacity': 1
                        }
                    });

                    map.addLayer({
                        'id': 'country-fills',
                        'type': 'fill',
                        'source': 'countries',
                        'paint': {
                            'fill-color': [
                                'match', ['get', 'name'],
                                ...countries.flatMap(country => {
                                    const overall = countryData[country]?.stats?.overall || '0';
                                    const color = getFillColor(overall);
                                    return [country, color];
                                }),
                                'rgba(0,0,0,0)'
                            ],
                            'fill-opacity': [
                                'case',
                                ['boolean', ['feature-state', 'active'], false], 1,
                                ['boolean', ['feature-state', 'hover'], false], 0.8,
                                ['in', ['get', 'name'],
                                    ['literal', countries]
                                ], 1,
                                0
                            ]
                        }
                    });

                    map.addLayer({
                        'id': 'country-borders',
                        'type': 'line',
                        'source': 'countries',
                        'paint': {
                            'line-color': '#A9BBD1',
                            'line-width': 1
                        }
                    });

                    // Add labels using the unique centroids
                    map.addLayer({
                        'id': 'country-labels',
                        'type': 'symbol',
                        'source': 'country-labels',
                        'layout': {
                            'text-field': ['get', 'name'],
                            'text-font': ['Poppins Regular', 'Arial Unicode MS Regular'],
                            'text-size': 12,
                            'text-transform': 'uppercase',
                            'text-anchor': 'center',
                            'text-offset': [0, 0],
                            'text-allow-overlap': false,
                            'text-ignore-placement': false
                        },
                        'paint': {
                            'text-color': '#000000',
                            'text-halo-color': '#FFFFFF',
                            'text-halo-width': 1,
                            'text-opacity': [
                                'case',
                                ['boolean', ['feature-state', 'active'], false], 1,
                                ['boolean', ['feature-state', 'hover'], false], 0.8,
                                1
                            ]
                        }
                    });

                    map.fitBounds([
                        [-27, -37],
                        [60, 40]
                    ]);

                    let hoveredStateId = null;
                    const popup = new mapboxgl.Popup({
                        closeButton: false,
                        closeOnClick: false
                    });

                    map.on('mousemove', 'country-fills', (e) => {
                        map.getCanvas().style.cursor = 'pointer';
                        if (e.features.length > 0) {
                            const feature = e.features[0];
                            const countryName = feature.properties.name;
                            if (!countries.includes(countryName) || countryName === currentlySelectedCountry) return;

                            if (hoveredStateId !== null) {
                                map.setFeatureState({
                                    source: 'countries',
                                    id: hoveredStateId
                                }, {
                                    hover: false
                                });
                            }
                            hoveredStateId = feature.id;
                            map.setFeatureState({
                                source: 'countries',
                                id: hoveredStateId
                            }, {
                                hover: true
                            });

                            const coordinates = e.lngLat;
                            showInfoBox(countryName, coordinates, countryFlags, popup);
                        }
                    });

                    map.on('mouseleave', 'country-fills', () => {
                        map.getCanvas().style.cursor = '';
                        if (hoveredStateId !== null) {
                            map.setFeatureState({
                                source: 'countries',
                                id: hoveredStateId
                            }, {
                                hover: false
                            });
                            hoveredStateId = null;
                        }
                        popup.remove();
                    });

                    map.on('click', 'country-fills', (e) => {
                        if (e.features.length > 0) {
                            const countryName = e.features[0].properties.name;
                            if (!countries.includes(countryName)) return;

                            const clickedId = e.features[0].id;

                            if (currentlySelectedCountry && currentlySelectedCountry !== countryName) {
                                const previousFeature = map.queryRenderedFeatures({
                                        layers: ['country-fills']
                                    })
                                    .find(f => f.properties.name === currentlySelectedCountry);
                                if (previousFeature) {
                                    map.setFeatureState({
                                        source: 'countries',
                                        id: previousFeature.id
                                    }, {
                                        active: false
                                    });
                                }
                            }

                            map.setFeatureState({
                                source: 'countries',
                                id: clickedId
                            }, {
                                active: true
                            });
                            currentlySelectedCountry = countryName;

                            const bbox = turf.bbox(e.features[0].geometry);
                            map.fitBounds(bbox, {
                                padding: 50,
                                duration: 1000
                            });

                            map.once('moveend', () => {
                                sendCountryData(countryName);
                            });

                            popup.remove();
                            isClusterZoomed = false;
                        }
                    });
                })
                .catch(error => console.error("Error loading GeoJSON:", error));

            supercluster = new Supercluster({
                radius: 60,
                maxZoom: 16,
            });

            map.on('zoomend', () => {
                if (isClusterZoomed) {
                    updateClusters();
                }
            });
        });

        function showInfoBox(countryName, coordinates, countryFlags, popup) {
            const data = countryData[countryName] || {};
            const testimonial = data.testimonial || {};
            const stats = data.stats || {};
            const isValid = (value) => value && value.trim() !== "" && value.trim().toLowerCase() !== "n/a";
            const flagCode = countryFlags[countryName] || "xx";

            let statsContent = '';
            if (isValid(stats.overall) || isValid(stats.entrepreneurs) || isValid(stats.jobs_created) || isValid(stats.wage_employed)) {
                statsContent = `
                <ul style="font-family: 'Poppins', sans-serif;">
                    ${isValid(stats.overall) ? `<li>OVERALL <span>${stats.overall}</span></li>` : ""}
                    ${isValid(stats.entrepreneurs) ? `<li>ENTREPRENEURS <span>${stats.entrepreneurs}</span></li>` : ""}
                    ${isValid(stats.jobs_created) ? `<li>JOBS CREATED <span>${stats.jobs_created}</span></li>` : ""}
                    ${isValid(stats.wage_employed) ? `<li>WAGE EMPLOYED <span>${stats.wage_employed}</span></li>` : ""}
                </ul>
            `;
            }

            const content = `
            <div class="main-map-box" style="font-family: 'Poppins', sans-serif;">
                <div class="main-map-box-top">
                    <div class="flag-contain">
                        <span class="fi fi-${flagCode}" style="width: 24px; height: 18px; display: inline-block;"></span>
                        <p style="display: inline; margin-left: 8px;">${countryName}</p>
                    </div>
                    ${statsContent}
                </div>
            </div>
        `;

            popup.setLngLat(coordinates)
                .setHTML(content)
                .addTo(map);
        }

        function sendCountryData(countryName) {
            console.log(`Fetching country data for: ${countryName}`);
            
            // Get current bbox and zoom
            const bounds = map.getBounds();
            const zoom = map.getZoom();
            const bbox = [
                bounds.getWest(),
                bounds.getSouth(),
                bounds.getEast(),
                bounds.getNorth()
            ];
            
            // First, fetch data from original API endpoint (for backward compatibility)
            fetch(`${countryDataEndpoint}?name=${encodeURIComponent(countryName)}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Country API response:', data);
                    
                    // Now fetch cluster data from supercluster API
                    fetchClusterData(countryName, bbox, zoom);
                })
                .catch(error => {
                    console.error(`Country API error for ${countryName}:`, error);
                    // Try fetching cluster data anyway
                    fetchClusterData(countryName, bbox, zoom);
                });
        }
        
        function fetchClusterData(countryName, bbox, zoom) {
            console.log(`Fetching cluster data with bbox: ${bbox} and zoom: ${zoom}`);
            
            // Create request payload for supercluster API
            const payload = {
                bbox: bbox,
                zoom: Math.floor(zoom),
                filters: {
                    country_of_residence: countryName
                }
            };
            
            // Fetch cluster data from supercluster API
            fetch(superclusterEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Supercluster API error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Supercluster API response:', data);
                
                if (data && data.features && Array.isArray(data.features)) {
                    // Directly use the GeoJSON features
                    renderClusters(data.features);
                } else {
                    console.error('Invalid supercluster data structure:', data);
                }
            })
            .catch(error => {
                console.error(`Supercluster API error:`, error);
            });
        }
        
        function renderClusters(features) {
            // Remove existing markers
            markers.forEach(marker => marker.remove());
            markers = [];
            
            features.forEach(feature => {
                const { geometry, properties } = feature;
                const [lng, lat] = geometry.coordinates;
                
                if (properties.cluster) {
                    // Create cluster marker
                    const el = document.createElement('div');
                    el.className = 'cluster-marker';
                    el.innerText = properties.point_count_abbreviated;
                    el.style.backgroundColor = '#007cbf';
                    el.style.borderRadius = '50%';
                    el.style.color = 'white';
                    el.style.width = `${Math.min(30 + (properties.point_count / 10), 60)}px`;
                    el.style.height = `${Math.min(30 + (properties.point_count / 10), 60)}px`;
                    el.style.display = 'flex';
                    el.style.alignItems = 'center';
                    el.style.justifyContent = 'center';
                    el.style.cursor = 'pointer';
                    el.style.fontSize = '14px';
                    el.style.fontWeight = 'bold';
                    el.style.fontFamily = "'Poppins', sans-serif";
                    
                    el.addEventListener('click', (e) => {
                        e.stopPropagation();
                        
                        // Get next zoom level based on expansion_zoom from API
                        const expansionZoom = properties.expansion_zoom || Math.min(zoom + 2, 16);
                        
                        console.log('Cluster clicked, zooming to:', expansionZoom, [lng, lat]);
                        isClusterZoomed = true;
                        
                        map.flyTo({
                            center: [lng, lat],
                            zoom: expansionZoom,
                            duration: 1000,
                            essential: true
                        });
                        
                        // Once zooming is complete, update the clusters
                        map.once('moveend', () => {
                            // Get updated bbox and zoom
                            const newBounds = map.getBounds();
                            const newZoom = map.getZoom();
                            const newBbox = [
                                newBounds.getWest(),
                                newBounds.getSouth(),
                                newBounds.getEast(),
                                newBounds.getNorth()
                            ];
                            
                            // Fetch new clusters
                            fetchClusterData(currentlySelectedCountry, newBbox, newZoom);
                        });
                    });
                    
                    markers.push(new mapboxgl.Marker(el).setLngLat([lng, lat]).addTo(map));
                } else {
                    // Create individual point marker
                    const el = document.createElement('div');
                    el.className = 'custom-marker';
                    
                    let markerType = properties.type || '';
                    let icon = '<?php echo esc_url(THEME_IMG . "marker-video.png"); ?>';
                    
                    if (markerType === 'data' || properties.data == 1) {
                        icon = '<?php echo esc_url(THEME_IMG . "marker-data.png"); ?>';
                    } else if (markerType === 'story' || properties.story == 1) {
                        icon = '<?php echo esc_url(THEME_IMG . "marker.png"); ?>';
                    }
                    
                    el.style.backgroundImage = `url(${icon})`;
                    el.style.backgroundSize = 'contain';
                    el.style.width = '27.43px';
                    el.style.height = '32px';
                    el.style.cursor = 'pointer';
                    
                    const name = properties.name || 'Unknown';
                    const country = properties.country || currentlySelectedCountry || 'Unknown';
                    
                    const popupContent = `
                        <div style="font-size:14px; font-weight:bold; font-family: 'Poppins', sans-serif;">
                            <div class="${properties.data == 1 ? 'data-content' : ''}">${name}</div>
                            <span style="font-size:12px;">${country}</span>
                        </div>
                    `;
                    
                    const popup = new mapboxgl.Popup({
                        offset: 25
                    }).setHTML(popupContent);
                    
                    el.addEventListener('click', (e) => {
                        e.stopPropagation();
                        console.log('Marker clicked:', properties.id);
                        fetchProfileData(properties.id, properties.story, properties.data, properties.is_featured_video);
                    });
                    
                    const marker = new mapboxgl.Marker(el)
                        .setLngLat([lng, lat])
                        .setPopup(popup)
                        .addTo(map);
                    
                    el.addEventListener('mouseenter', () => popup.addTo(map));
                    el.addEventListener('mouseleave', () => popup.remove());
                    
                    markers.push(marker);
                }
            });
        }

        function initMapWithClusters(markerData) {
            if (!markerData || !Array.isArray(markerData)) {
                console.error('Invalid marker data:', markerData);
                return;
            }

            // Instead of using supercluster.js directly, we'll use our API
            // Get current bbox and zoom
            const bounds = map.getBounds();
            const zoom = map.getZoom();
            const bbox = [
                bounds.getWest(),
                bounds.getSouth(),
                bounds.getEast(),
                bounds.getNorth()
            ];
            
            // Fetch clusters from API
            fetchClusterData(currentlySelectedCountry, bbox, zoom);
        }

        // We no longer need the updateClusters function as we're using the API directly
        map.on('zoomend', () => {
            if (isClusterZoomed && currentlySelectedCountry) {
                // Get updated bbox and zoom
                const bounds = map.getBounds();
                const zoom = map.getZoom();
                const bbox = [
                    bounds.getWest(),
                    bounds.getSouth(),
                    bounds.getEast(),
                    bounds.getNorth()
                ];
                
                // Fetch new clusters
                fetchClusterData(currentlySelectedCountry, bbox, zoom);
            }
        });

        function fetchProfileData(profileId, story, data, is_featured_video) {
            if (!profileId) {
                console.error('No profileId provided');
                return;
            }

            console.log(`Fetching profile data for ID: ${profileId}`);
            
            // Fetch profile data from API endpoint
            fetch(`${profileDataEndpoint}/${profileId}?story=${story}&data=${data}&video=${is_featured_video}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(response => {
                    console.log(`Profile API success for ID: ${profileId}`, response);
                    
                    if (response.success) {
                        jQuery('#modal-profile-content').html(response.html);
                        jQuery('.modal-story').removeClass('model-bio model-video model-story-content');
                        
                        if (response.profile_video == 1) {
                            jQuery('.modal-story').addClass('model-video');
                        } else if (response.profile_data == 1) {
                            jQuery('.modal-story').addClass('model-bio');
                        } else {
                            jQuery('.modal-story').addClass('model-story-content');
                        }
                        
                        jQuery('#exampleModal').modal('show');
                    } else {
                        console.error('Profile API response not successful:', response);
                    }
                })
                .catch(error => {
                    console.error(`Profile API error for ID: ${profileId}:`, error);
                });
        }
    </script>

<?php
endwhile;
get_footer();
?>