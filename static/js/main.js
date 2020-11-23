let charts;
let refresh_interval;
let error_shown;
let dt;

$(document).ready(function() {
	charts = {}; // charts container

	error_shown = false; // is error currently on screen?
	refresh_interval = 2500; // how often we fetch data
	dt = 2500; // data time interval (the longer, the more accurate some stats are)

	getStats(500);
	getNetwork();

	setInterval(getStats, refresh_interval, dt);

	// handles the "close" button on error page
	$(".closebutton").click(function() {
		$(".errormessage").css({
			"display": "none"
		});
	});

	// handles expansion and shrinking of stats container
	$(".stat").click(function() {
		if ($(this).attr("grow") === "grow") { // time to shrink
			$('div.stat[grow="grow"]').toArray().forEach((d, i) => {
				$(d).attr("grow", "shrink");
				$(d).attr("direction", "");
				$(d).css("top", "auto")
			});
			enableScroll(); // re enable page scrolling
		} else { // time to grow
			$('div.stat[grow="grow"]').toArray().forEach((d, i) => {
				$(d).attr("grow", "shrink");
			});

			let first_in_line = $(this).offset().left < $(".statscontainer").offset().left + $(".stat").width();
			let direction;

			if (first_in_line) {
			//	$(this).attr("direction", "right");
				direction = "right";
			} else {
				//$(this).attr("direction", "left");
				direction = "left";
			}
			$(this).attr("direction", direction);

			$(this).attr("grow", "grow");
			$(this).css("top", 0)

			let top = $(document).scrollTop();
			$(this).css("top", top + "px");
			disableScroll(top); // disable page scrolling
		}
	});
});

function disableScroll(top) {
	window.onscroll = function() {
  	window.scrollTo(0, top);
	};
}

function enableScroll() {
    window.onscroll = function() {};
}

function getNetwork() {
	$.ajax({
		type: 'GET',
		url: '/getnetwork/',
		complete: function(response) {
			if (response.status == 200) {
				for (let property in response.responseJSON) {
					$(`#${property} .statvalue`).text(response.responseJSON[property]);
				}
			}
		}
	});
}

function getStats(dt) {
	$.ajax({
		type: 'GET',
		url: '/getstats/',
		data: {
			"dt": dt
		},
		complete: function(response) {
			if (response.status == 200) {
				let any;
				any = false;
				for (let property in response.responseJSON) {
					if (response.responseJSON[property].value != null) {
						// create new chart
						if (charts[property] === undefined) {
							let chart_container = `#${property} .chart`;
							let chart_max_value = response.responseJSON[property].max
							charts[property] = new Chart(chart_container, chart_max_value);
						}
						charts[property].addData(response.responseJSON[property].value);
						charts[property].updateChart();

						any = true;
						// the value is not null, we proceed to show the div
						$(`#${property} .statvalue`).text(response.responseJSON[property].text);
						$(`#${property}`).css({
							"display": "flex",
							"background-color": response.responseJSON[property].color
						});
					} else {
						// the value is null, we hide the div
						$(`#${property}`).css({
							"display": "none"
						});
					}
				}
				if (any) {
					// we found at least one stat - everything is working!
					let text_color = getCssProperty("--text-color");
					let ok_color = getCssProperty("--ok-color");
					let ok_symbol = getCssProperty("--ok-symbol");
					// reset the text to black
					$(".networkcontainer").css("color", text_color);
					// set the indicator to a green checkmark
					$(".network#symbol").html(ok_symbol);
					$(".network#symbol").css("color", ok_color);
					// hide loading animation
					if ($(".loadingicon").css("opacity") > 0) {
						$(".loadingicon").fadeOut(50, function() {
							$(".loadingicon").css("display", "none");
						});
					}
					// set ok favicon
					$('link[rel="shortcut icon"]').attr('href','/static/ico/favicon-ok.ico');

					if (error_shown) {
						// hide error message (if any)
						$(".errormessage").css({
							"display": "none"
						});
						// hide grey screen (if any)
						$(".greyscreen").css({
							"display": "none"
						});
						error_shown = false;
					}

				}
			}
		},
		error: function(request, status, error) {
			if (!error_shown) {
        // the only way i found to access css variables
        let error_color = getCssProperty("--error-color");
				let error_symbol = getCssProperty("--error-symbol");
				// set the indicator to a red cross
				$(".network#symbol").html(error_symbol);
				$(".network#symbol").css("color", error_color);
				// set the text to deep red
				$(".networkcontainer").css("color", error_color);
				// show error message
				$(".errormessage").css("display", "inline-block");
				// show grey screen
				$(".greyscreen").css("display", "inline-block");
				// show loading animation
				$(".loadingicon").css("display", "block");
				$(".loadingicon").fadeIn(200);
				// set error favicon
				$('link[rel="shortcut icon"]').attr('href','/static/ico/favicon-error.ico');
				error_shown = true;
			}
		}
	});
}
