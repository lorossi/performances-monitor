let refresh_interval;
let error_shown;

$(document).ready(function() {
	error_shown = false;
	refresh_interval = 5000;
	dt = 2000;

	getStats(250);
	getNetwork();

	setInterval(getStats, refresh_interval, dt);

	$(".closebutton").click(function() {
		$(".errormessage").css({
			"display": "none"
		});
	});
});

// the only way i found to access css variables
function getCssProperty(property) {
  let css_property = $(":root").css(property)
  return css_property.split(" ").join("").slice(1, -1);
}

function getNetwork() {
	$.ajax({
		type: 'POST',
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
		type: 'POST',
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
					let text_color = getCssProperty("--text-color");
					let ok_color = getCssProperty("--ok-color");
					// reset the text to black
					$(".networkcontainer").css("color", text_color);
					// set the indicator to a green checkmark
					$(".network#symbol").html("✓");
					$(".network#symbol").css("color", ok_color);
					// hide error message (if any)
					if (error_shown) {
						$(".errormessage").css({
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
				// set the indicator to a red cross
				$(".network#symbol").html("✗");
				$(".network#symbol").css("color", error_color);
				// set the text to deep red
				$(".networkcontainer").css("color", error_color);
				// show error message
				$(".errormessage").css("display", "inline-block");
				error_shown = true;
			}
		}
	});
}
